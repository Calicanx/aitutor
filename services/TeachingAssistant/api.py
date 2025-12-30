import sys
import os
import threading
import requests
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from urllib.parse import parse_qs
from sse_starlette.sse import EventSourceResponse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.TeachingAssistant.teaching_assistant import TeachingAssistant
from services.TeachingAssistant.core.context import Event
from shared.auth_middleware import get_current_user, get_user_from_token
from shared.cors_config import ALLOWED_ORIGINS, ALLOW_CREDENTIALS, ALLOWED_METHODS, ALLOWED_HEADERS
from shared.timing_middleware import UnpluggedTimingMiddleware
from shared.cache_middleware import CacheControlMiddleware

from shared.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Observer WebSocket Registry (for real-time feed monitoring)
# ============================================================================
# Maps session_id -> list of observer WebSocket connections
# Used by backend devs to monitor live sessions and feed data to TeachingAssistant
from typing import Dict, List
active_observers: Dict[str, List[WebSocket]] = {}

# Simple API key for observer authentication (backend devs only)
# In production, use a more robust auth mechanism
OBSERVER_API_KEY = os.getenv("OBSERVER_API_KEY", "dev-observer-key-12345")


# ============================================================================
# Lifespan Context Manager (Start/Stop Event Processing Loop)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start and stop event processing loop"""
    global ta, event_processing_task
    
    # Start event processing loop
    ta.running = True
    event_processing_task = asyncio.create_task(ta.ongoing())
    logger.info("[API] Started event processing loop")
    
    yield
    
    # Shutdown
    logger.info("[API] Shutting down event processing loop...")
    ta.running = False
    if event_processing_task:
        event_processing_task.cancel()
        try:
            await event_processing_task
        except asyncio.CancelledError:
            pass
    logger.info("[API] Event processing loop stopped")


app = FastAPI(title="Teaching Assistant API", lifespan=lifespan)

# Add timing middleware for performance monitoring (Phase 1)
app.add_middleware(UnpluggedTimingMiddleware)

# Cache Control (Phase 7)
app.add_middleware(CacheControlMiddleware)

# Add GZip compression middleware (Phase 7)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# Configure CORS with secure origins from environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=ALLOW_CREDENTIALS,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    expose_headers=["*"],
)

# Request timeout middleware (Phase 3)
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    try:
        return await asyncio.wait_for(call_next(request), timeout=30.0)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timeout"}
        )

# Cache control middleware for static responses (Phase 7)
@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/health":
        response.headers["Cache-Control"] = "public, max-age=60"
    elif request.url.path.startswith("/session/info"):
        response.headers["Cache-Control"] = "private, max-age=10"
    else:
        response.headers["Cache-Control"] = "no-cache"
    return response

# Explicit OPTIONS handler for Cloud Run compatibility (backup)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS preflight requests explicitly for Cloud Run"""
    from fastapi.responses import Response
    # Use first allowed origin or * if none configured
    origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "*"
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": ", ".join(ALLOWED_METHODS),
            "Access-Control-Allow-Headers": "*",
        }
    )

# Create TeachingAssistant instance (now stateless - all state in MongoDB)
ta = TeachingAssistant()

# Global task for event processing loop
event_processing_task = None

# DASH API URL for pre-loading questions
DASH_API_URL = os.getenv("DASH_API_URL", "http://localhost:8000")


# ============================================================================
# Feed-to-Event Converter
# ============================================================================

def feed_message_to_event(message: dict, session_id: str, user_id: str) -> Optional[Event]:
    """Convert WebSocket feed message to Event object"""
    msg_type = message.get("type")
    timestamp_str = message.get("timestamp")
    payload = message.get("data", {})
    
    # Parse timestamp
    if timestamp_str:
        try:
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')).timestamp()
        except:
            timestamp = time.time()
    else:
        timestamp = time.time()
    
    # Convert based on message type
    if msg_type == "transcript":
        return Event(
            type="text",
            timestamp=timestamp,
            session_id=session_id,
            user_id=user_id,
            data={
                "speaker": payload.get("speaker", "user"),
                "text": payload.get("transcript", ""),
                "timestamp": timestamp_str
            }
        )
    elif msg_type == "audio":
        return Event(
            type="audio",
            timestamp=timestamp,
            session_id=session_id,
            user_id=user_id,
            data={
                "audio": payload.get("audio", ""),
                "timestamp": timestamp_str
            }
        )
    elif msg_type == "media":
        return Event(
            type="media",
            timestamp=timestamp,
            session_id=session_id,
            user_id=user_id,
            data={
                "media": payload.get("media", ""),
                "timestamp": timestamp_str
            }
        )
    return None


# ============================================================================
# Request/Response Models
# ============================================================================

class StartSessionRequest(BaseModel):
    pass  # user_id now comes from JWT


class EndSessionRequest(BaseModel):
    interrupt_audio: bool = True


class QuestionAnsweredRequest(BaseModel):
    question_id: str
    is_correct: bool


class PromptResponse(BaseModel):
    prompt: str
    session_info: dict


class FeedWebhookRequest(BaseModel):
    type: str  # "media" | "audio" | "transcript" | "combined"
    timestamp: str  # ISO 8601 timestamp
    data: dict  # Contains optional: media, audio, transcript


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "TeachingAssistant"}


# ============================================================================
# Session Management Endpoints
# ============================================================================

@app.post("/session/start", response_model=PromptResponse)
async def start_session(http_request: Request, request: Optional[StartSessionRequest] = None):
    """Start a new tutoring session"""
    user_id = get_current_user(http_request)
    try:
        # Create session in MongoDB (existing method)
        result = ta.start_session(user_id)
        session_id = result["session_info"]["session_id"]
        
        # Initialize memory and context components (new method)
        greeting = await ta.start(user_id, session_id)
        
        # Create session_start event
        start_event = Event(
            type="session_start",
            timestamp=time.time(),
            session_id=session_id,
            user_id=user_id,
            data={"session_id": session_id, "user_id": user_id}
        )
        ta.queue_manager.enqueue(start_event)
        
        # UPDATED: Return greeting in response for immediate delivery
        # Also sent via SSE for systems that listen to instruction queue
        # This ensures backward compatibility with frontends expecting prompt in response
        return PromptResponse(
            prompt=greeting or "",  # Return greeting directly (not empty!)
            session_info=result["session_info"]
        )
    except Exception as e:
        logger.error(f"Error in start_session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _preload_questions_background(user_id: str, token: str):
    """Background function to pre-load questions for next session"""
    try:
        # Call DASH API to get 5 questions for next session
        dash_response = requests.get(
            f"{DASH_API_URL}/api/questions/5",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        if dash_response.status_code == 200:
            preloaded_questions = dash_response.json()
            # Extract question IDs
            question_ids = [
                q.get('dash_metadata', {}).get('dash_question_id', '')
                for q in preloaded_questions
                if q.get('dash_metadata', {}).get('dash_question_id')
            ]

            if question_ids:
                # Store in MongoDB user profile
                from managers.mongodb_manager import mongo_db
                mongo_db.users.update_one(
                    {"user_id": user_id},
                    {"$set": {"preloaded_question_ids": question_ids}}
                )
                logger.info(f"[PRELOAD] Stored {len(question_ids)} question IDs for next session (user: {user_id})")
    except Exception as e:
        # Don't fail session end if pre-loading fails
        logger.error(f"[PRELOAD] Failed to pre-load questions: {e}")


@app.post("/session/end", response_model=PromptResponse)
async def end_session(http_request: Request, request: Optional[EndSessionRequest] = None):
    """End the current tutoring session"""
    user_id = get_current_user(http_request)
    try:
        # Get active session for user
        session = ta.get_active_session(user_id)
        if not session:
            return PromptResponse(
                prompt="",
                session_info={'session_active': False, 'user_id': user_id}
            )

        session_id = session["session_id"]
        
        # End session with memory consolidation (new method)
        closing = await ta.end(user_id, session_id)
        
        # Session end event is NO LONGER needed here because we called ta.end() directly above
        # Queuing it would cause the event loop to call ta.end() a second time!
        # end_event = Event(
        #     type="session_end",
        #     timestamp=time.time(),
        #     session_id=session_id,
        #     user_id=user_id,
        #     data={"session_id": session_id, "user_id": user_id}
        # )
        # ta.queue_manager.enqueue(end_event)
        
        # Get session summary (existing method for stats)
        result = ta.end_session(session_id)

        # Pre-load next session questions in background (non-blocking)
        try:
            auth_header = http_request.headers.get("Authorization", "")
            if not auth_header:
                auth_header = http_request.headers.get("authorization", "")

            token = ""
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "", 1)
            elif auth_header.startswith("bearer "):
                token = auth_header.replace("bearer ", "", 1)

            if token and len(token) > 0:
                preload_thread = threading.Thread(
                    target=_preload_questions_background,
                    args=(user_id, token),
                    daemon=True
                )
                preload_thread.start()
        except Exception as e:
            logger.error(f"[PRELOAD] Failed to start pre-loading thread: {e}")

        
        # Return closing message directly (also sent via SSE)
        return PromptResponse(
            prompt=closing or result["prompt"],  # Use memory-aware closing or fallback
            session_info=result["session_info"]
        )
    except Exception as e:
        logger.error(f"Error in end_session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question/answered")
def record_question(http_request: Request, request: QuestionAnsweredRequest):
    """Record a question answer"""
    user_id = get_current_user(http_request)
    try:
        session = ta.get_active_session(user_id)
        if not session:
            raise HTTPException(status_code=404, detail="No active session")

        ta.record_question_answered(
            session["session_id"],
            request.question_id,
            request.is_correct
        )
        return {"status": "recorded", "session_info": ta.get_session_info(session["session_id"])}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in record_question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/info")
def get_session_info(http_request: Request):
    """Get current session info"""
    user_id = get_current_user(http_request)
    session = ta.get_active_session(user_id)
    if not session:
        return {"session_active": False, "user_id": user_id}
    return ta.get_session_info(session["session_id"])


@app.post("/conversation/turn")
def record_conversation_turn(http_request: Request):
    """Record a conversation turn"""
    user_id = get_current_user(http_request)
    try:
        session = ta.get_active_session(user_id)
        if not session:
            # If session is already closed (race condition with session end), just ignore
            return {"status": "ignored", "reason": "no_active_session"}

        ta.record_conversation_turn(session["session_id"])
        return {"status": "recorded"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in record_conversation_turn: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inactivity/check", response_model=PromptResponse)
def check_inactivity(http_request: Request):
    """Check for inactivity and return prompt if needed"""
    user_id = get_current_user(http_request)
    try:
        session = ta.get_active_session(user_id)
        if not session:
            return PromptResponse(prompt="", session_info={"session_active": False})

        prompt = ta.check_inactivity(session["session_id"])
        session_info = ta.get_session_info(session["session_id"])
        return PromptResponse(prompt=prompt or "", session_info=session_info)
    except Exception as e:
        logger.error(f"Error in check_inactivity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint (Frontend → Backend feed streaming)
# ============================================================================

@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """WebSocket endpoint for streaming audio/video/transcript from frontend"""
    # 1. Extract and validate JWT from query parameter
    query_params = parse_qs(websocket.scope["query_string"].decode())
    token = query_params.get("token", [None])[0]

    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user_info = get_user_from_token(token)
    if not user_info:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = user_info["user_id"]

    # 2. Get active session and check if it's still active
    session = ta.get_active_session(user_id)
    if not session or not session.get("is_active"):
        await websocket.close(code=1008, reason="Session not active or ended")
        logger.info(f"[WS] Rejected connection - no active session for user {user_id}")
        return

    session_id = session["session_id"]

    # 3. Accept connection and update status
    await websocket.accept()
    ta.session_manager.set_connection_status(session_id, websocket=True)
    logger.info(f"[WS] WebSocket connected for session {session_id}")

    try:
        # 4. Message handling loop
        while True:
            data = await websocket.receive_json()

            # Update activity timestamp
            ta.session_manager.update_activity(session_id)

            # Process message based on type
            msg_type = data.get("type")
            timestamp = data.get("timestamp")
            payload = data.get("data", {})

            if msg_type == "audio":
                await process_audio(session_id, payload.get("audio"), timestamp)
            elif msg_type == "media":
                await process_media(session_id, payload.get("media"), timestamp)
            elif msg_type == "transcript":
                speaker = payload.get("speaker", "tutor")
                await process_transcript(session_id, payload.get("transcript"), timestamp, speaker)
                # Record conversation turn for transcripts
                ta.record_conversation_turn(session_id)
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"[WS] WebSocket disconnected for session {session_id}")
        ta.session_manager.set_connection_status(session_id, websocket=False)
    except Exception as e:
        logger.error(f"[WS] WebSocket error for session {session_id}: {e}")
        ta.session_manager.set_connection_status(session_id, websocket=False)


async def broadcast_to_observers(session_id: str, message: dict):
    """Broadcast a message to all observers watching this session"""
    if session_id not in active_observers:
        return

    observers = active_observers[session_id]
    if not observers:
        return

    # Send to all observers concurrently, remove disconnected ones
    disconnected = []
    for ws in observers:
        try:
            await ws.send_json(message)
        except Exception as e:
            logger.debug(f"[OBSERVER] Failed to send to observer: {e}")
            disconnected.append(ws)

    # Clean up disconnected observers
    for ws in disconnected:
        if ws in active_observers[session_id]:
            active_observers[session_id].remove(ws)


async def process_audio(session_id: str, audio_base64: str, timestamp: str):
    """Process incoming audio data and broadcast to observers"""
    # Get user_id from session
    session = ta.session_manager.get_session_by_id(session_id)
    if not session:
        return
    
    user_id = session["user_id"]
    
    # Create event from feed message
    event = feed_message_to_event(
        {
            "type": "audio",
            "timestamp": timestamp,
            "data": {"audio": audio_base64}
        },
        session_id,
        user_id
    )
    
    if event:
        # Enqueue event for processing
        ta.queue_manager.enqueue(event)
    
    # Broadcast to observers (keep existing functionality)
    logger.debug(f"[AUDIO] Session {session_id}: received audio at {timestamp}")

    await broadcast_to_observers(session_id, {
        "type": "audio",
        "timestamp": timestamp,
        "data": {"audio": audio_base64}
    })


async def process_media(session_id: str, media_base64: str, timestamp: str):
    """Process incoming media (video frames) and broadcast to observers"""
    # Get user_id from session
    session = ta.session_manager.get_session_by_id(session_id)
    if not session:
        return
    
    user_id = session["user_id"]
    
    # Create event from feed message
    event = feed_message_to_event(
        {
            "type": "media",
            "timestamp": timestamp,
            "data": {"media": media_base64}
        },
        session_id,
        user_id
    )
    
    if event:
        # Enqueue event for processing
        ta.queue_manager.enqueue(event)
    
    # Broadcast to observers (keep existing functionality)
    logger.debug(f"[MEDIA] Session {session_id}: received frame at {timestamp}")

    await broadcast_to_observers(session_id, {
        "type": "media",
        "timestamp": timestamp,
        "data": {"media": media_base64}
    })


async def process_transcript(session_id: str, transcript: str, timestamp: str, speaker: str = "tutor"):
    """Process incoming transcript and broadcast to observers"""
    # Get user_id from session
    session = ta.session_manager.get_session_by_id(session_id)
    if not session:
        return
    
    user_id = session["user_id"]
    
    # Create event from feed message
    event = feed_message_to_event(
        {
            "type": "transcript",
            "timestamp": timestamp,
            "data": {
                "transcript": transcript,
                "speaker": speaker
            }
        },
        session_id,
        user_id
    )
    
    if event:
        # Enqueue event for processing
        ta.queue_manager.enqueue(event)
    
    # Broadcast to observers (keep existing functionality)
    speaker_label = "USER" if speaker == "user" else "TUTOR"
    logger.debug(f"[TRANSCRIPT] Session {session_id} [{speaker_label}]: {transcript[:100] if transcript else 'empty'}...")

    await broadcast_to_observers(session_id, {
        "type": "transcript",
        "timestamp": timestamp,
        "data": {"transcript": transcript, "speaker": speaker}
    })


# ============================================================================
# SSE Endpoint (Backend → Frontend instruction delivery)
# ============================================================================

@app.get("/sse/instructions")
async def sse_instructions(request: Request, token: str = None):
    """SSE endpoint for pushing instructions to frontend"""
    # Validate token (passed as query param for SSE)
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    user_info = get_user_from_token(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = user_info["user_id"]

    # Get active session
    session = ta.get_active_session(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active session")

    session_id = session["session_id"]
    ta.session_manager.set_connection_status(session_id, sse=True)
    logger.info(f"[SSE] SSE connected for session {session_id}")

    async def event_generator():
        try:
            keepalive_counter = 0
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                # Check for pending instructions in MongoDB
                instructions = ta.session_manager.get_pending_instructions(session_id)

                for instruction in instructions:
                    yield {
                        "event": "instruction",
                        "id": instruction["instruction_id"],
                        "data": instruction["text"]
                    }
                    # Mark as delivered
                    ta.session_manager.mark_instruction_delivered(
                        session_id,
                        instruction["instruction_id"]
                    )

                # Check for inactivity and generate prompt if needed
                # This replaces the background thread approach
                ta.check_inactivity(session_id)

                # Send keepalive every 30 seconds (6 * 5 second intervals)
                keepalive_counter += 1
                if keepalive_counter >= 6:
                    yield {"event": "keepalive", "data": ""}
                    keepalive_counter = 0

                # Poll interval
                await asyncio.sleep(5)

        finally:
            ta.session_manager.set_connection_status(session_id, sse=False)
            logger.info(f"[SSE] SSE disconnected for session {session_id}")

    # Add CORS headers for SSE
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
        "Access-Control-Allow-Credentials": "true"
    }
    
    return EventSourceResponse(event_generator(), headers=headers)


# ============================================================================
# Instruction Push Endpoint (Backend → Frontend via SSE)
# ============================================================================

class InstructionRequest(BaseModel):
    instruction: str
    session_id: Optional[str] = None  # Optional - if not provided, uses user's active session


@app.post("/session/instruction")
def push_instruction(request: InstructionRequest, http_request: Request):
    """
    Push an instruction to the tutor via SSE.

    The instruction will be delivered to the frontend via SSE and sent to Gemini.
    Can be called by:
    - Authenticated user (uses their active session)
    - Backend system with session_id specified
    """
    user_id = get_current_user(http_request)

    try:
        # Get session - either from request or user's active session
        if request.session_id:
            session = ta.session_manager.get_session_by_id(request.session_id)
        else:
            session = ta.get_active_session(user_id)

        if not session:
            raise HTTPException(status_code=404, detail="No active session found")

        session_id = session["session_id"]

        # Add system prompt prefix so tutor knows it's an instruction
        SYSTEM_PROMPT_PREFIX = "[SYSTEM INSTRUCTION]"
        full_instruction = f"{SYSTEM_PROMPT_PREFIX}\n{request.instruction}"

        # Push to session's instruction queue
        instruction_id = ta.session_manager.push_instruction(session_id, full_instruction)

        # Log the instruction content
        truncated_instruction = request.instruction[:150] + "..." if len(request.instruction) > 150 else request.instruction
        logger.info(f"[INSTRUCTION CREATED] {instruction_id}: {truncated_instruction}")

        return {
            "success": True,
            "instruction_id": instruction_id,
            "session_id": session_id,
            "message": "Instruction queued for delivery via SSE"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing instruction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session/instruction/admin")
def push_instruction_admin(request: InstructionRequest, api_key: str = None):
    """
    Admin endpoint to push instruction to any session.
    Requires observer API key authentication.
    session_id is required for this endpoint.
    """
    if api_key != OBSERVER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id is required for admin endpoint")

    try:
        session = ta.session_manager.get_session_by_id(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {request.session_id}")

        # Add system prompt prefix
        SYSTEM_PROMPT_PREFIX = "[SYSTEM INSTRUCTION]"
        full_instruction = f"{SYSTEM_PROMPT_PREFIX}\n{request.instruction}"

        # Push instruction
        instruction_id = ta.session_manager.push_instruction(request.session_id, full_instruction)

        # Log the instruction content
        truncated_instruction = request.instruction[:150] + "..." if len(request.instruction) > 150 else request.instruction
        logger.info(f"[INSTRUCTION CREATED/ADMIN] {instruction_id}: {truncated_instruction}")

        return {
            "success": True,
            "instruction_id": instruction_id,
            "session_id": request.session_id,
            "message": "Instruction queued for delivery via SSE"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pushing admin instruction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Observer WebSocket Endpoint (Backend devs monitoring live sessions)
# ============================================================================

@app.get("/sessions/active")
def list_active_sessions(api_key: str = None):
    """
    List all active sessions (for backend devs to choose which to observe)
    Requires API key authentication
    """
    if api_key != OBSERVER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    sessions = ta.session_manager.list_active_sessions()
    return {
        "sessions": [
            {
                "session_id": s["session_id"],
                "user_id": s["user_id"],
                "started_at": s["started_at"].isoformat() if s.get("started_at") else None,
                "websocket_connected": s.get("websocket_connected", False),
                "sse_connected": s.get("sse_connected", False),
                "questions_answered": s.get("questions_answered_this_session", 0)
            }
            for s in sessions
        ]
    }


@app.websocket("/ws/feed/observe")
async def websocket_observe(websocket: WebSocket):
    """
    Observer WebSocket endpoint for backend devs to monitor live sessions.

    Query params:
        - api_key: Observer API key for authentication
        - session_id: The session to observe (required)

    Receives: audio, media, transcript messages as they flow through the producer
    """
    # 1. Extract query parameters
    query_params = parse_qs(websocket.scope["query_string"].decode())
    api_key = query_params.get("api_key", [None])[0]
    session_id = query_params.get("session_id", [None])[0]

    # 2. Validate API key
    if api_key != OBSERVER_API_KEY:
        await websocket.close(code=4001, reason="Invalid API key")
        return

    # 3. Validate session_id
    if not session_id:
        await websocket.close(code=4002, reason="Missing session_id")
        return

    # 4. Verify session exists
    session = ta.session_manager.get_session_by_id(session_id)
    if not session:
        await websocket.close(code=4003, reason="Session not found")
        return

    # 5. Accept connection and register as observer
    await websocket.accept()

    if session_id not in active_observers:
        active_observers[session_id] = []
    active_observers[session_id].append(websocket)

    observer_count = len(active_observers[session_id])
    logger.info(f"[OBSERVER] Observer connected for session {session_id} (total: {observer_count})")

    # Send initial session info
    await websocket.send_json({
        "type": "session_info",
        "data": {
            "session_id": session_id,
            "user_id": session.get("user_id"),
            "started_at": session.get("started_at").isoformat() if session.get("started_at") else None,
            "websocket_connected": session.get("websocket_connected", False),
            "message": "Observer connected. Waiting for feed data..."
        }
    })

    try:
        # 6. Keep connection alive and handle any observer commands
        while True:
            try:
                # Wait for messages (ping/pong or commands)
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60)

                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "keepalive"})
                except:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"[OBSERVER] Error: {e}")
    finally:
        # Clean up
        if session_id in active_observers and websocket in active_observers[session_id]:
            active_observers[session_id].remove(websocket)
            remaining = len(active_observers[session_id])
            logger.info(f"[OBSERVER] Observer disconnected from session {session_id} (remaining: {remaining})")


# ============================================================================
# Legacy Endpoints (kept for backward compatibility during migration)
# These can be removed after frontend is fully migrated to WebSocket/SSE
# ============================================================================

@app.post("/webhook/feed")
def receive_feed(http_request: Request, request: FeedWebhookRequest):
    """
    LEGACY: POST-based feed webhook
    Will be replaced by WebSocket /ws/feed
    """
    user_id = get_current_user(http_request)
    try:
        logger.debug(f"[FEED] Received {request.type} from user {user_id} at {request.timestamp}")
        return {"status": "received", "type": request.type}
    except Exception as e:
        logger.error(f"Error in receive_feed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_instruction_to_tutor", response_model=PromptResponse)
def send_instruction_to_tutor(http_request: Request):
    """
    LEGACY: POST-based instruction polling
    Will be replaced by SSE /sse/instructions
    """
    user_id = get_current_user(http_request)
    try:
        session = ta.get_active_session(user_id)
        if not session:
            return PromptResponse(prompt="", session_info={"session_active": False})

        session_id = session["session_id"]

        # Check for pending instructions
        instructions = ta.session_manager.get_pending_instructions(session_id)
        if instructions:
            instruction = instructions[0]
            ta.session_manager.mark_instruction_delivered(session_id, instruction["instruction_id"])

            # Log the instruction being sent to tutor
            truncated_instruction = instruction["text"][:150] + "..." if len(instruction["text"]) > 150 else instruction["text"]
            logger.info(f"[INSTRUCTION → TUTOR] {truncated_instruction}")

            return PromptResponse(
                prompt=instruction["text"],
                session_info=ta.get_session_info(session_id)
            )

        return PromptResponse(prompt="", session_info=ta.get_session_info(session_id))
    except Exception as e:
        logger.error(f"Error in send_instruction_to_tutor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("TEACHING_ASSISTANT_PORT", "8002")))
    uvicorn.run(app, host="0.0.0.0", port=port)
