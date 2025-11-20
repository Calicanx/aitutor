# Adam Tutor Service

Backend proxy service for Gemini Live API integration.

## Overview

This service acts as a WebSocket proxy between the frontend and Google's Gemini Live API. It handles:
- Gemini API authentication
- System prompt management
- Real-time audio/video streaming
- Tool calling and responses

## Architecture

```
Frontend (React) <--WebSocket--> Tutor Service (Node.js) <--WebSocket--> Gemini Live API
```

## Setup

1. **Install dependencies:**
   ```bash
   cd services/Tutor
   npm install
   ```

2. **Configure API Key:**
   - Add `GEMINI_API_KEY` to root `.env` file
   - The service automatically loads from root `.env`

3. **Run standalone (for testing):**
   ```bash
   node server.js
   ```

4. **Run with full system:**
   ```bash
   cd ../..
   ./run_tutor.sh
   ```

## Configuration

- **Port:** 8767 (WebSocket)
- **System Prompt:** `system_prompts/adam_tutor.md`
- **Model:** `gemini-2.5-flash-native-audio-preview-09-2025`
- **Log File:** `../../logs/tutor.log`

## API Protocol

The service uses JSON messages over WebSocket:

### Client → Service Messages

**Connect:**
```json
{
  "type": "connect",
  "model": "models/gemini-2.5-flash-native-audio-preview-09-2025",
  "config": {
    "responseModalities": ["AUDIO"],
    "speechConfig": {...}
  }
}
```

**Disconnect:**
```json
{
  "type": "disconnect"
}
```

**Realtime Input (audio/video):**
```json
{
  "type": "realtimeInput",
  "data": {
    "mimeType": "audio/pcm;rate=16000",
    "data": "base64_encoded_data"
  }
}
```

**Send Text:**
```json
{
  "type": "send",
  "parts": [{"text": "Hello"}],
  "turnComplete": true
}
```

**Tool Response:**
```json
{
  "type": "toolResponse",
  "data": {
    "functionResponses": [...]
  }
}
```

### Service → Client Messages

**Connection Opened:**
```json
{
  "type": "open"
}
```

**Gemini Message:**
```json
{
  "type": "message",
  "data": {...}
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
  "reason": "Connection closed"
}
```

## Development

- **Dependencies:** `@google/genai`, `ws`, `dotenv`
- **Node Version:** >= 18.0.0
- **Type:** ES Module

## Logging

All logs are written to `../../logs/tutor.log` with emoji prefixes:
- 🎓 Service start
- ✅ Success events
- 🔗 Connection events
- ❌ Errors
- 🔌 Disconnection events
- 📝 System prompt loaded
- 🎤 Voice configuration

## Security

- API key is stored in root `.env` (not exposed to frontend)
- System prompt is loaded server-side
- All Gemini communication happens through backend

