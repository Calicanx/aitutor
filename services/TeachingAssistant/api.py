import sys
import os
import threading
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.TeachingAssistant.teaching_assistant import TeachingAssistant
from shared.auth_middleware import get_current_user

app = FastAPI(title="Teaching Assistant API")

# Configure CORS - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
)

# Explicit OPTIONS handler for Cloud Run compatibility (backup)
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle OPTIONS preflight requests explicitly for Cloud Run"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

ta = TeachingAssistant()

# DASH API URL for pre-loading questions
DASH_API_URL = os.getenv("DASH_API_URL", "http://localhost:8000")


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


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "TeachingAssistant"}


@app.post("/session/start", response_model=PromptResponse)
def start_session(http_request: Request, request: Optional[StartSessionRequest] = None):
    # Get user_id from JWT token (will raise 401 if invalid)
    user_id = get_current_user(http_request)
    try:
        prompt = ta.start_session(user_id)
        session_info = ta.get_session_info()
        return PromptResponse(prompt=prompt, session_info=session_info)
    except Exception as e:
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
                print(f"[PRELOAD] Stored {len(question_ids)} question IDs for next session (user: {user_id})")
    except Exception as e:
        # Don't fail session end if pre-loading fails
        print(f"[PRELOAD] Failed to pre-load questions: {e}")

@app.post("/session/end", response_model=PromptResponse)
def end_session(http_request: Request, request: Optional[EndSessionRequest] = None):
    # Get user_id from JWT token (will raise 401 if invalid)
    user_id = get_current_user(http_request)
    try:
        prompt = ta.end_session()
        
        # Pre-load next session questions in background (non-blocking)
        try:
            auth_header = http_request.headers.get("Authorization", "")
            if not auth_header:
                # Try alternative header name (some clients use different casing)
                auth_header = http_request.headers.get("authorization", "")
            
            token = ""
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "", 1)
            elif auth_header.startswith("bearer "):
                token = auth_header.replace("bearer ", "", 1)
            
            if token and len(token) > 0:
                # Start background thread to pre-load questions
                preload_thread = threading.Thread(
                    target=_preload_questions_background,
                    args=(user_id, token),
                    daemon=True
                )
                preload_thread.start()
            else:
                print(f"[PRELOAD] No valid token found in Authorization header, skipping pre-load")
        except Exception as e:
            # Don't fail session end if pre-loading setup fails
            print(f"[PRELOAD] Failed to start pre-loading thread: {e}")
        
        if not prompt:
            # Return a proper response for no active session instead of raising 400
            session_info = {
                'session_active': False,
                'user_id': None,
                'duration_minutes': 0.0,
                'total_questions': 0
            }
            return PromptResponse(prompt="", session_info=session_info)

        session_info = ta.get_session_info()
        return PromptResponse(prompt=prompt, session_info=session_info)
    except Exception as e:
        # Log the actual error for debugging
        print(f"Error in end_session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question/answered")
def record_question(http_request: Request, request: QuestionAnsweredRequest):
    # Verify JWT token (will raise 401 if invalid)
    user_id = get_current_user(http_request)
    try:
        # For now, just ensure user is authenticated - session state is managed separately
        ta.record_question_answered(request.question_id, request.is_correct)
        return {"status": "recorded", "session_info": ta.get_session_info()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/info")
def get_session_info(http_request: Request):
    # Verify JWT token
    user_id = get_current_user(http_request)
    return ta.get_session_info()


@app.post("/conversation/turn")
def record_conversation_turn(http_request: Request):
    # Verify JWT token (will raise 401 if invalid)
    user_id = get_current_user(http_request)
    try:
        ta.record_conversation_turn()
        return {"status": "recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/inactivity/check", response_model=PromptResponse)
def check_inactivity(http_request: Request):
    try:
        # Verify JWT token
        user_id = get_current_user(http_request)
        prompt = ta.get_inactivity_prompt()
        if prompt:
            session_info = ta.get_session_info()
            return PromptResponse(prompt=prompt, session_info=session_info)
        return PromptResponse(prompt="", session_info=ta.get_session_info())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/feed")
def receive_feed(http_request: Request, request: FeedWebhookRequest):
    # Get user_id from JWT token (will raise 401 if invalid)
    user_id = get_current_user(http_request)
    try:
        # For now: just log and acknowledge the feed (no analysis yet)
        # Later: analyze feed and generate instructions
        print(f"[FEED] Received {request.type} from user {user_id} at {request.timestamp}")
        # TODO: Store feed data for future analysis
        return {"status": "received", "type": request.type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send_instruction_to_tutor", response_model=PromptResponse)
def send_instruction_to_tutor(http_request: Request):
    # Get user_id from JWT token (will raise 401 if invalid)
    user_id = get_current_user(http_request)
    try:
        # For now: return empty prompt (no analysis yet)
        # Later: analyze stored feed and generate instruction
        instruction = ""  # TODO: Generate instruction based on feed analysis
        session_info = ta.get_session_info()
        return PromptResponse(prompt=instruction, session_info=session_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", os.getenv("TEACHING_ASSISTANT_PORT", "8002")))
    uvicorn.run(app, host="0.0.0.0", port=port)

