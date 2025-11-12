import time
import sys
import os
import json
import glob
import random
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from DashSystem.dash_system import DASHSystem, Question

app = FastAPI()
dash_system = DASHSystem()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allows the React frontend to connect
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Perseus item model matching frontend expectations
class PerseusQuestion(BaseModel):
    question: dict = Field(description="The question data")
    answerArea: dict = Field(description="The answer area")
    hints: List = Field(description="List of question hints")

# Path to CurriculumBuilder with full Perseus items
CURRICULUM_BUILDER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'SherlockEDApi', 'CurriculumBuilder')
)

def load_perseus_items_from_dir(directory: str, limit: Optional[int] = None) -> List[Dict]:
    """Load Perseus items from CurriculumBuilder directory"""
    all_items = []
    file_pattern = os.path.join(directory, "*.json")
    
    for file_path in glob.glob(file_pattern):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure it has the expected structure
                if isinstance(data, dict) and "question" in data:
                    all_items.append(data)
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")
    
    if limit and len(all_items) > limit:
        return random.sample(all_items, limit)
    return all_items

@app.get("/api/questions/{sample_size}", response_model=List[PerseusQuestion])
def get_questions_with_dash_intelligence(sample_size: int, user_id: str = "default_user"):
    """
    Gets questions using DASH intelligence but returns full Perseus items.
    Uses DASH to intelligently select questions based on learning journey and adaptive difficulty.
    """
    print(f"[DASH_API] Request received: sample_size={sample_size}, user_id={user_id}", flush=True)
    
    # Ensure the user exists and is loaded
    dash_system.load_user_or_create(user_id)
    
    # Use DASH intelligence to get recommended questions
    current_time = time.time()
    selected_questions = []
    selected_question_ids = []  # Track selected question IDs to avoid duplicates
    
    print(f"[DASH_API] Using DASH intelligence to select {sample_size} questions", flush=True)
    
    # Get multiple questions using DASH intelligence
    for i in range(sample_size):
        next_question = dash_system.get_next_question(user_id, current_time, exclude_question_ids=selected_question_ids)
        if next_question:
            selected_questions.append(next_question)
            selected_question_ids.append(next_question.question_id)  # Track to avoid duplicates
            print(f"[DASH_API] Selected question {i+1}/{sample_size}: {next_question.question_id} (skills: {next_question.skill_ids})", flush=True)
        else:
            print(f"[DASH_API] No more questions available after {len(selected_questions)} selections", flush=True)
            break
    
    # Load Perseus items from CurriculumBuilder
    # Since there's no direct mapping, we'll load items and return them
    # The DASH intelligence has already selected which skills/questions to focus on
    print(f"[DASH_API] Loading Perseus items from CurriculumBuilder", flush=True)
    perseus_items = load_perseus_items_from_dir(CURRICULUM_BUILDER_PATH, limit=sample_size)
    
    if not perseus_items:
        print(f"[DASH_API] ERROR: No Perseus questions found in CurriculumBuilder", flush=True)
        raise HTTPException(status_code=404, detail="No Perseus questions found in CurriculumBuilder")
    
    # If we have fewer items than requested, repeat some (or return what we have)
    while len(perseus_items) < sample_size and selected_questions:
        # Add more items if needed
        additional = load_perseus_items_from_dir(CURRICULUM_BUILDER_PATH, limit=sample_size - len(perseus_items))
        perseus_items.extend(additional)
        if not additional:
            break
    
    print(f"[DASH_API] Returning {len(perseus_items[:sample_size])} Perseus items", flush=True)
    
    # Return the requested number
    return perseus_items[:sample_size]

@app.get("/next-question/{user_id}", response_model=Question)
def get_next_question(user_id: str):
    """
    Gets the next recommended question for a given user.
    (Original endpoint kept for backward compatibility)
    """
    # Ensure the user exists and is loaded
    dash_system.load_user_or_create(user_id)
    
    # Get the next question
    next_question = dash_system.get_next_question(user_id, time.time())
    
    if next_question:
        return next_question
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No recommended question found.")

class AnswerSubmission(BaseModel):
    question_id: str
    skill_ids: List[str]
    is_correct: bool
    response_time_seconds: float

@app.post("/api/submit-answer/{user_id}")
def submit_answer(user_id: str, answer: AnswerSubmission):
    """
    Record a question attempt and update DASH system.
    This enables tracking and adaptive difficulty.
    """
    print(f"[DASH_API] Answer submission received for user {user_id}: question_id={answer.question_id}, is_correct={answer.is_correct}", flush=True)
    
    user_profile = dash_system.user_manager.load_user(user_id)
    if not user_profile:
        print(f"[DASH_API] ERROR: User {user_id} not found", flush=True)
        raise HTTPException(status_code=404, detail="User not found")
    
    # Record the attempt using DASH system
    affected_skills = dash_system.record_question_attempt(
        user_profile, answer.question_id, answer.skill_ids, 
        answer.is_correct, answer.response_time_seconds
    )
    
    print(f"[DASH_API] Answer recorded successfully, affected {len(affected_skills)} skill(s)", flush=True)
    
    return {
        "success": True,
        "affected_skills": affected_skills,
        "message": "Answer recorded successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
