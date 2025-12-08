#!/usr/bin/env bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Load environment variables from .env file if it exists
if [[ -f ".env" ]]; then
    echo "Loading environment variables from .env file..."
    # Read .env file and export variables (works on Windows/Git Bash)
    while IFS='=' read -r key value; do
        # Skip comments, empty lines, and lines that start with #
        [[ $key =~ ^[[:space:]]*#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        [[ $key =~ ^# ]] && continue
        
        # Remove leading/trailing whitespace
        key=$(echo "$key" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
        
        # Skip if key starts with # or is empty after trimming
        [[ -z "$key" ]] && continue
        [[ $key =~ ^# ]] && continue
        
        # Remove quotes from value if present
        value=$(echo "$value" | sed 's/^"//' | sed 's/"$//' | sed "s/^'//" | sed "s/'$//")
        
        # Only export if key is valid (contains only alphanumeric and underscore)
        if [[ $key =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
            export "$key=$value"
            echo "  Loaded: $key"
        fi
    done < .env
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  No .env file found. Using default values."
    echo "   Create a .env file with your MongoDB Atlas URI and other config."
fi

# Clean up old logs and create a fresh logs directory
rm -rf "$SCRIPT_DIR/logs"
mkdir -p "$SCRIPT_DIR/logs"

# Detect Python environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    # Not already in a virtual environment
    if [[ -d "$SCRIPT_DIR/env" ]]; then
        echo "Activating local env..."
        # shellcheck source=/dev/null
        source "$SCRIPT_DIR/env/bin/activate"
    elif [[ -d "$SCRIPT_DIR/.env" ]]; then
        echo "Activating local .env..."
        # shellcheck source=/dev/null
        source "$SCRIPT_DIR/.env/bin/activate"
    else
        echo "❌ No virtual environment found."
        echo "👉 Please create one with:"
        echo "    python -m venv env"
        echo "    source env/bin/activate"
        echo "👉 Next, install the required packages with:"
        echo "    pip install -r requirements.txt"
        echo "👉 If you plan to use the frontend, also run:"
        echo "    cd frontend"
        echo "    npm install --force"
        echo "    cd .."
        echo "👉 Finally, run this script again."
        exit 1
    fi
else
    echo "Using already active virtual environment: $VIRTUAL_ENV"
fi

# Get the python executable (now guaranteed to be from venv)
# On Windows, explicitly use the venv's Python to avoid finding system Python
if [[ -n "$VIRTUAL_ENV" ]]; then
    # Use the venv's Python explicitly
    if [[ -f "$VIRTUAL_ENV/Scripts/python.exe" ]]; then
        # Windows native path
        PYTHON_BIN="$VIRTUAL_ENV/Scripts/python.exe"
    elif [[ -f "$VIRTUAL_ENV/bin/python3" ]]; then
        # Unix-style path (Git Bash/Linux/Mac)
        PYTHON_BIN="$VIRTUAL_ENV/bin/python3"
    elif [[ -f "$VIRTUAL_ENV/bin/python" ]]; then
        PYTHON_BIN="$VIRTUAL_ENV/bin/python"
    else
        # Fallback to PATH search if venv Python not found
        PYTHON_BIN="$(command -v python3 || command -v python)"
        echo "⚠️  Warning: Could not find venv Python, using: $PYTHON_BIN"
    fi
else
    # No venv active, search PATH
    PYTHON_BIN="$(command -v python3 || command -v python)"
fi
echo "Using Python: $PYTHON_BIN"

# Array to hold the PIDs of background processes
pids=()

# Function to clean up background processes
cleanup() {
    echo "Shutting down tutor..."
    for pid in "${pids[@]}"; do
        echo "Killing process $pid"
        kill "$pid"
    done
    echo "All processes terminated."
}

# Trap the INT signal (sent by Ctrl+C) to run the cleanup function
trap cleanup INT

# Function to check if a port is in use and kill the process
check_and_free_port() {
    local port=$1
    local service_name=$2
    if lsof -ti:$port > /dev/null 2>&1 || fuser $port/tcp > /dev/null 2>&1; then
        echo "⚠️  Port $port is already in use. Freeing it for $service_name..."
        lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null || true
        fuser -k $port/tcp 2>/dev/null || true
        sleep 1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service_name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "⚠️  $service_name may not be ready yet (checked $max_attempts times)"
    return 1
}

# Free up ports before starting services
echo "Checking and freeing ports..."
check_and_free_port 8000 "DASH API"
check_and_free_port 8001 "SherlockED API"
check_and_free_port 8002 "TeachingAssistant"
check_and_free_port 8003 "Auth Service"
check_and_free_port 8767 "Tutor Service"
check_and_free_port 3000 "Frontend"

# Start the FastAPI server in the background
echo "Starting DASH API server... Logs -> logs/dash_api.log"
(cd "$SCRIPT_DIR" && "$PYTHON_BIN" services/DashSystem/dash_api.py) > "$SCRIPT_DIR/logs/dash_api.log" 2>&1 &
pids+=($!)

# Start the SherlockEDExam FastAPI server in the background
echo "Starting SherlockED Exam API server... Logs -> logs/sherlocked_exam.log"
(cd "$SCRIPT_DIR" && "$PYTHON_BIN" services/SherlockEDApi/run_backend.py) > "$SCRIPT_DIR/logs/sherlocked_exam.log" 2>&1 &
pids+=($!)

# Start the Tutor service (Node.js backend for Gemini Live API)
echo "Starting Tutor service (Adam)... Logs -> logs/tutor.log"
(cd "$SCRIPT_DIR/services/Tutor" && node server.js) > "$SCRIPT_DIR/logs/tutor.log" 2>&1 &
pids+=($!)

# Start the TeachingAssistant API server in the background
echo "Starting TeachingAssistant API server... Logs -> logs/teaching_assistant.log"
(cd "$SCRIPT_DIR" && "$PYTHON_BIN" services/TeachingAssistant/api.py) > "$SCRIPT_DIR/logs/teaching_assistant.log" 2>&1 &
pids+=($!)

# Start the Auth Service API server in the background
echo "Starting Auth Service API server... Logs -> logs/auth_service.log"
(cd "$SCRIPT_DIR" && "$PYTHON_BIN" services/AuthService/auth_api.py) > "$SCRIPT_DIR/logs/auth_service.log" 2>&1 &
pids+=($!)

# Give the backend servers a moment to start
echo "Waiting for backend services to initialize..."
sleep 5

# Wait for critical services to be ready (with timeout)
echo "Verifying services are ready..."
wait_for_service "http://localhost:8000/health" "DASH API" || echo "⚠️  DASH API health check failed, but continuing..."
wait_for_service "http://localhost:8002/health" "TeachingAssistant" || echo "⚠️  TeachingAssistant health check failed, but continuing..."
wait_for_service "http://localhost:8003/health" "Auth Service" || echo "⚠️  Auth Service health check failed, but continuing..."
wait_for_service "http://localhost:8001/health" "SherlockED API" || echo "⚠️  SherlockED API health check failed, but continuing..."

# Extract ports dynamically from configuration files
FRONTEND_PORT=$(grep -o '"port":[[:space:]]*[0-9]*' "$SCRIPT_DIR/frontend/vite.config.ts" 2>/dev/null | grep -o '[0-9]*' || echo "3000")
DASH_API_PORT=$(grep -o 'PORT", [0-9]*' "$SCRIPT_DIR/services/DashSystem/dash_api.py" 2>/dev/null | grep -o '[0-9]*' || echo "8000")
SHERLOCKED_API_PORT=$(grep -o 'PORT", [0-9]*' "$SCRIPT_DIR/services/SherlockEDApi/run_backend.py" 2>/dev/null | grep -o '[0-9]*' || echo "8001")
TEACHING_ASSISTANT_PORT=$(grep -o '"8002"' "$SCRIPT_DIR/services/TeachingAssistant/api.py" 2>/dev/null | grep -o '[0-9]*' || echo "8002")
AUTH_SERVICE_PORT=$(grep -o 'PORT", [0-9]*' "$SCRIPT_DIR/services/AuthService/auth_api.py" 2>/dev/null | grep -o '[0-9]*' || echo "8003")

# Ensure all port variables are properly set (fallback to defaults if extraction failed)
FRONTEND_PORT=${FRONTEND_PORT:-3000}
DASH_API_PORT=${DASH_API_PORT:-8000}
SHERLOCKED_API_PORT=${SHERLOCKED_API_PORT:-8001}
TEACHING_ASSISTANT_PORT=${TEACHING_ASSISTANT_PORT:-8002}
AUTH_SERVICE_PORT=${AUTH_SERVICE_PORT:-8003}

# Start the Node.js frontend in the background (after backend services are ready)
echo "Starting Node.js frontend... Logs -> logs/frontend.log"
(cd "$SCRIPT_DIR/frontend" && npm run dev) > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
pids+=($!)

# Give frontend a moment to start
sleep 2

echo "Tutor is running with the following PIDs: ${pids[*]}"
echo ""
echo "📡 Service URLs:"
echo "  🌐 Frontend:           http://localhost:$FRONTEND_PORT"
echo "  🔐 Auth Service:       http://localhost:$AUTH_SERVICE_PORT"
echo "  🔧 DASH API:           http://localhost:$DASH_API_PORT"
echo "  🕵️  SherlockED API:     http://localhost:$SHERLOCKED_API_PORT"
echo "  👨‍🏫 TeachingAssistant:  http://localhost:$TEACHING_ASSISTANT_PORT"
echo "  🎓 Tutor Service:      ws://localhost:8767"
echo ""
echo "Press Ctrl+C to stop."
echo "You can view the logs for each service in the 'logs' directory."

# Wait indefinitely until the script is interrupted
wait
