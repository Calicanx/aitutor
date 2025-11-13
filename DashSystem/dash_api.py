import time
import sys
import os
import json
import glob
import random
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s|%(message)s|file:%(filename)s:line No.%(lineno)d',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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
            logger.warning(f"Warning: Failed to load {file_path}: {e}")
    
    if limit and len(all_items) > limit:
        return random.sample(all_items, limit)
    return all_items

@app.get("/api/questions/{sample_size}", response_model=List[PerseusQuestion])
def get_questions_with_dash_intelligence(sample_size: int, user_id: str = "default_user"):
    """
    Gets questions using DASH intelligence but returns full Perseus items.
    Uses DASH to intelligently select questions based on learning journey and adaptive difficulty.
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"[NEW_SESSION] Requesting {sample_size} questions for user: {user_id}")
    logger.info(f"{'='*80}\n")
    
    # Ensure the user exists and is loaded
    dash_system.load_user_or_create(user_id)
    
    # Use DASH intelligence to get recommended questions
    current_time = time.time()
    selected_questions = []
    selected_question_ids = []  # Track selected question IDs to avoid duplicates
    
    # Get multiple questions using DASH intelligence
    for i in range(sample_size):
        next_question = dash_system.get_next_question(user_id, current_time, exclude_question_ids=selected_question_ids)
        if next_question:
            selected_questions.append(next_question)
            selected_question_ids.append(next_question.question_id)  # Track to avoid duplicates
        else:
            logger.info(f"[SESSION_END] Selected {len(selected_questions)}/{sample_size} questions")
            break
    
    # Load Perseus items from CurriculumBuilder
    perseus_items = load_perseus_items_from_dir(CURRICULUM_BUILDER_PATH, limit=sample_size)
    
    if not perseus_items:
        logger.error(f"[ERROR] No Perseus questions found in CurriculumBuilder")
        raise HTTPException(status_code=404, detail="No Perseus questions found in CurriculumBuilder")
    
    # If we have fewer items than requested, repeat some (or return what we have)
    while len(perseus_items) < sample_size and selected_questions:
        additional = load_perseus_items_from_dir(CURRICULUM_BUILDER_PATH, limit=sample_size - len(perseus_items))
        perseus_items.extend(additional)
        if not additional:
            break
    
    logger.info(f"[SESSION_READY] Loaded {len(perseus_items[:sample_size])} Perseus questions\n")
    
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
    logger.info(f"\n{'-'*80}")
    
    user_profile = dash_system.user_manager.load_user(user_id)
    if not user_profile:
        logger.error(f"[ERROR] User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Record the attempt using DASH system
    affected_skills = dash_system.record_question_attempt(
        user_profile, answer.question_id, answer.skill_ids, 
        answer.is_correct, answer.response_time_seconds
    )
    
    # Show performance summary after this question
    total_attempts = len(user_profile.question_history)
    correct_count = sum(1 for attempt in user_profile.question_history if attempt.is_correct)
    accuracy = (correct_count / total_attempts * 100) if total_attempts > 0 else 0
    
    logger.info(f"[PROGRESS] Total:{total_attempts} questions | Accuracy:{accuracy:.1f}% ({correct_count}/{total_attempts})")
    logger.info(f"{'-'*80}\n")
    
    return {
        "success": True,
        "affected_skills": affected_skills,
        "message": "Answer recorded successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
