# API Documentation - AI Tutor Services

## Overview
This document provides API documentation for all AI Tutor backend services.

---

## Authentication Service (Port 8003)

### Base URL
- Development: `http://localhost:8003`
- Production: Set via `AUTH_SERVICE_URL` environment variable

### Endpoints

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "AuthService"
}
```

#### `GET /auth/google`
Initiate Google OAuth flow

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random-state-string"
}
```

#### `GET /auth/callback`
OAuth callback endpoint (handled by backend, redirects to frontend)

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: State parameter for CSRF protection

**Redirects to:**
- Existing user: `/login?token=<jwt_token>&is_new_user=false`
- New user: `/login?setup_token=<setup_token>`

#### `POST /auth/complete-setup`
Complete user setup for new users

**Request Body:**
```json
{
  "setup_token": "string",
  "user_type": "student" | "parent",
  "age": 5-18
}
```

**Response:**
```json
{
  "token": "jwt_token",
  "user": {
    "user_id": "string",
    "email": "string",
    "name": "string",
    "age": number,
    "current_grade": "string",
    "user_type": "student"
  },
  "is_new_user": true
}
```

#### `GET /auth/me`
Get current user information

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Response:**
```json
{
  "user_id": "string",
  "email": "string",
  "name": "string",
  "age": number,
  "current_grade": "string",
  "user_type": "student"
}
```

#### `POST /auth/logout`
Logout endpoint (client clears token)

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

## Teaching Assistant Service (Port 8002)

### Base URL
- Development: `http://localhost:8002`
- Production: Set via `TEACHING_ASSISTANT_PORT` environment variable

### Endpoints

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "TeachingAssistant"
}
```

#### `POST /session/start`
Start a teaching session

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Response:**
```json
{
  "prompt": "Welcome message for Gemini",
  "session_info": {
    "session_active": true,
    "user_id": "string",
    "duration_minutes": 0.0,
    "total_questions": 0
  }
}
```

#### `POST /session/end`
End the current teaching session

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Request Body (optional):**
```json
{
  "interrupt_audio": true
}
```

**Response:**
```json
{
  "prompt": "Session summary message",
  "session_info": {
    "session_active": false,
    "user_id": "string",
    "duration_minutes": 15.5,
    "total_questions": 10
  }
}
```

#### `POST /question/answered`
Record a question attempt

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Request Body:**
```json
{
  "question_id": "string",
  "is_correct": boolean
}
```

**Response:**
```json
{
  "status": "recorded",
  "session_info": { ... }
}
```

#### `GET /session/info`
Get current session information

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Response:**
```json
{
  "session_active": boolean,
  "user_id": "string",
  "duration_minutes": number,
  "total_questions": number
}
```

#### `GET /inactivity/check`
Check for inactivity and get prompt if needed

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Response:**
```json
{
  "prompt": "Inactivity message or empty string",
  "session_info": { ... }
}
```

---

## DASH System Service (Port 8000)

### Base URL
- Development: `http://localhost:8000`
- Production: Set via `PORT` environment variable

### Endpoints

#### `GET /api/questions/{sample_size}`
Get questions using DASH intelligence

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Path Parameters:**
- `sample_size`: Number of questions to return (integer)

**Response:**
```json
[
  {
    "question": { ... },
    "answerArea": { ... },
    "hints": [ ... ],
    "dash_metadata": {
      "dash_question_id": "string",
      "skill_ids": ["string"],
      "difficulty": number,
      "expected_time_seconds": number,
      "slug": "string",
      "skill_names": ["string"]
    }
  }
]
```

#### `POST /api/submit-answer`
Submit an answer and update DASH system

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Request Body:**
```json
{
  "question_id": "string",
  "skill_ids": ["string"],
  "is_correct": boolean,
  "response_time_seconds": number
}
```

**Response:**
```json
{
  "success": true,
  "affected_skills": ["string"],
  "message": "Answer recorded successfully"
}
```

#### `GET /api/skill-scores`
Get all skill scores for current user

**Headers:**
- `Authorization`: `Bearer <jwt_token>`

**Response:**
```json
{
  "skill_states": {
    "skill_id": {
      "name": "string",
      "memory_strength": number,
      "last_practice_time": number | null,
      "practice_count": number,
      "correct_count": number
    }
  }
}
```

---

## Tutor Service (WebSocket - Port 8767)

### Base URL
- Development: `ws://localhost:8767`
- Production: Set via `PORT` environment variable

### WebSocket Connection

**Connection URL:**
```
ws://localhost:8767?token=<jwt_token>
```

**Query Parameters:**
- `token`: JWT authentication token (required)

### Message Types

#### Client → Server

**Connect to Gemini:**
```json
{
  "type": "connect",
  "config": {
    "model": "models/gemini-2.5-flash-native-audio-preview-09-2025",
    "systemInstruction": "...",
    "generationConfig": { ... },
    "speechConfig": { ... }
  }
}
```

**Send Realtime Input (Audio/Video):**
```json
{
  "type": "realtimeInput",
  "data": {
    "mimeType": "audio/pcm",
    "data": "base64-encoded-data"
  }
}
```

**Send Text Message:**
```json
{
  "type": "send",
  "parts": [ ... ],
  "turnComplete": true
}
```

**Send Tool Response:**
```json
{
  "type": "toolResponse",
  "data": { ... }
}
```

**Disconnect:**
```json
{
  "type": "disconnect"
}
```

#### Server → Client

**Connection Opened:**
```json
{
  "type": "open"
}
```

**Message from Gemini:**
```json
{
  "type": "message",
  "data": { ... }
}
```

**Error:**
```json
{
  "type": "error",
  "error": "Error message"
}
```

**Connection Closed:**
```json
{
  "type": "close",
  "reason": "Reason for closure"
}
```

---

## Error Responses

All services return consistent error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common HTTP Status Codes

- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (missing or invalid JWT)
- `404`: Not Found
- `500`: Internal Server Error
- `504`: Request Timeout

---

## Authentication

All endpoints except `/health`, `/auth/google`, and `/auth/callback` require JWT authentication.

**Header Format:**
```
Authorization: Bearer <jwt_token>
```

**JWT Claims:**
- `sub`: User ID
- `email`: User email
- `name`: User name
- `aud`: "teachr-api" (audience)
- `iss`: "teachr-auth-service" (issuer)
- `exp`: Expiration timestamp

---

## Rate Limiting

Currently no rate limiting is implemented. This should be added for production.

---

## CORS

CORS is configured via the `ALLOWED_ORIGINS` environment variable.

**Development defaults:**
- `http://localhost:3000`
- `http://localhost:4173`
- `http://localhost:5173`

**Production:**
Set `ALLOWED_ORIGINS` to comma-separated list of allowed domains.

---

## Environment Variables

### Required for All Services:
- `JWT_SECRET`: Strong secret for JWT signing (32+ characters)
- `JWT_AUDIENCE`: "teachr-api"
- `JWT_ISSUER`: "teachr-auth-service"
- `MONGODB_URI`: MongoDB connection string

### Service-Specific:
- `AUTH_SERVICE_URL`: Auth service URL
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `FRONTEND_URL`: Frontend URL for OAuth redirects
- `GEMINI_API_KEY`: Google Gemini API key
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

---

## Testing

Use tools like:
- **Postman** for HTTP endpoints
- **wscat** for WebSocket testing

**Example wscat command:**
```bash
wscat -c "ws://localhost:8767?token=YOUR_JWT_TOKEN"
```

---

## Support

For issues or questions, refer to:
- `COMPLETE_IMPLEMENTATION_PLAN.md` - Full roadmap
- `SESSION_SUMMARY.md` - Latest updates
- `SECURITY_FIXES_COMPLETE.md` - Security details
