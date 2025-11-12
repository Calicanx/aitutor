import math
import time
import json
import os
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from user_manager import UserManager, UserProfile, SkillState
from QuestionGeneratorAgent.question_generator_agent import QuestionGeneratorAgent

# Helper function to ensure logs are flushed immediately
def log_print(message: str):
    """Print with immediate flush to ensure logs appear in redirected output"""
    print(message, flush=True)

class GradeLevel(Enum):
    K = 0
    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3
    GRADE_4 = 4
    GRADE_5 = 5
    GRADE_6 = 6
    GRADE_7 = 7
    GRADE_8 = 8
    GRADE_9 = 9
    GRADE_10 = 10
    GRADE_11 = 11
    GRADE_12 = 12

@dataclass
class Skill:
    skill_id: str
    name: str
    grade_level: GradeLevel
    prerequisites: List[str] = field(default_factory=list)
    forgetting_rate: float = 0.1
    difficulty: float = 0.0
    order: int = 0  # Order within grade level for learning journey

@dataclass
class StudentSkillState:
    memory_strength: float = 0.0
    last_practice_time: Optional[float] = None
    practice_count: int = 0
    correct_count: int = 0

@dataclass
class Question:
    question_id: str
    skill_ids: List[str]
    content: str
    difficulty: float = 0.0
    expected_time_seconds: float = 60.0  # Default expected time for answering

class DASHSystem:
    def __init__(self, skills_file: Optional[str] = None, curriculum_file: Optional[str] = None):
        
        # Default file paths relative to the project root
        self.skills_file_path = skills_file if skills_file else "QuestionsBank/skills.json"
        self.curriculum_file_path = curriculum_file if curriculum_file else "QuestionsBank/curriculum.json"

        self.skills: Dict[str, Skill] = {}
        self.student_states: Dict[str, Dict[str, StudentSkillState]] = {}
        self.questions: Dict[str, Question] = {}
        self.curriculum: Dict = {}
        self.user_manager = UserManager(users_folder="Users")
        
        # Initialize the Question Generator Agent
        try:
            # Convert relative path to absolute path
            qg_curriculum_path = os.path.abspath("QuestionsBank/curriculum.json")
            self.question_generator = QuestionGeneratorAgent(curriculum_file=qg_curriculum_path)
            log_print("[OK] Question Generator Agent initialized.")
        except Exception as e:
            self.question_generator = None
            log_print(f"[WARNING] Could not initialize Question Generator Agent: {e}")

        self._load_from_files(self.skills_file_path, self.curriculum_file_path)
    
    def _reload_questions(self):
        """Reload only the questions from the curriculum file."""
        try:
            with open(self.curriculum_file_path, 'r') as f:
                self.curriculum = json.load(f)
            
            self.questions.clear()
            for grade_key, grade_data in self.curriculum['grades'].items():
                for skill_data in grade_data['skills']:
                    for question_data in skill_data['questions']:
                        question = Question(
                            question_id=question_data['question_id'],
                            skill_ids=[skill_data['skill_id']],
                            content=question_data['content'],
                            difficulty=question_data['difficulty'],
                            expected_time_seconds=question_data.get('expected_time_seconds', 60.0)
                        )
                        self.questions[question.question_id] = question
            log_print(f"[OK] Reloaded {len(self.questions)} questions from curriculum.")
        except Exception as e:
            log_print(f"[ERROR] Error reloading questions: {e}")

    def _load_from_files(self, skills_file: str, curriculum_file: str):
        """Load skills and curriculum from JSON files"""
        try:
            # Load skills
            with open(skills_file, 'r') as f:
                skills_data = json.load(f)
            
            # Track order within each grade level for learning journey
            grade_order_map = {}
            for skill_id, skill_data in skills_data.items():
                grade_level = GradeLevel[skill_data['grade_level']]
                # Use order from JSON if present, otherwise infer from position
                order = skill_data.get('order', 0)
                if order == 0:
                    # Infer order from position in file (for backward compatibility)
                    if grade_level not in grade_order_map:
                        grade_order_map[grade_level] = 0
                    grade_order_map[grade_level] += 1
                    order = grade_order_map[grade_level]
                
                skill = Skill(
                    skill_id=skill_data['skill_id'],
                    name=skill_data['name'],
                    grade_level=grade_level,
                    prerequisites=skill_data['prerequisites'],
                    forgetting_rate=skill_data['forgetting_rate'],
                    difficulty=skill_data['difficulty'],
                    order=order
                )
                self.skills[skill_id] = skill
            
            # Load curriculum and questions
            self._reload_questions()
            
            log_print(f"[OK] Loaded {len(self.skills)} skills from JSON files")
            
        except FileNotFoundError as e:
            log_print(f"[ERROR] Error: Could not find file {e.filename}")
            log_print("[INFO] Falling back to hardcoded curriculum...")
            self._initialize_k12_math_curriculum_fallback()
        except json.JSONDecodeError as e:
            log_print(f"[ERROR] Error: Invalid JSON format - {e}")
            log_print("[INFO] Falling back to hardcoded curriculum...")
            self._initialize_k12_math_curriculum_fallback()
        except Exception as e:
            log_print(f"[ERROR] Unexpected error loading curriculum: {e}")
            log_print("[INFO] Falling back to hardcoded curriculum...")
            self._initialize_k12_math_curriculum_fallback()
    
    def _initialize_k12_math_curriculum_fallback(self):
        """Fallback: Initialize K-12 Math curriculum with hardcoded skills (original implementation)"""
        
        # Kindergarten skills (order: 1, 2, 3)
        self.skills["counting_1_10"] = Skill("counting_1_10", "Counting 1-10", GradeLevel.K, [], 0.05, 0.0, 1)
        self.skills["number_recognition"] = Skill("number_recognition", "Number Recognition", GradeLevel.K, [], 0.05, 0.0, 2)
        self.skills["basic_shapes"] = Skill("basic_shapes", "Basic Shapes", GradeLevel.K, [], 0.08, 0.0, 3)
        
        # Grade 1 skills (order: 1, 2, 3)
        self.skills["addition_basic"] = Skill("addition_basic", "Basic Addition", GradeLevel.GRADE_1, ["counting_1_10"], 0.07, 0.0, 1)
        self.skills["subtraction_basic"] = Skill("subtraction_basic", "Basic Subtraction", GradeLevel.GRADE_1, ["counting_1_10"], 0.07, 0.0, 2)
        self.skills["counting_100"] = Skill("counting_100", "Counting to 100", GradeLevel.GRADE_1, ["counting_1_10"], 0.06, 0.0, 3)
        
        # Grade 2 skills (order: 1, 2, 3)
        self.skills["addition_2digit"] = Skill("addition_2digit", "2-Digit Addition", GradeLevel.GRADE_2, ["addition_basic"], 0.08, 0.0, 1)
        self.skills["subtraction_2digit"] = Skill("subtraction_2digit", "2-Digit Subtraction", GradeLevel.GRADE_2, ["subtraction_basic"], 0.08, 0.0, 2)
        self.skills["multiplication_intro"] = Skill("multiplication_intro", "Introduction to Multiplication", GradeLevel.GRADE_2, ["addition_basic"], 0.09, 0.0, 3)
        
        # Grade 3 skills (order: 1, 2, 3)
        self.skills["multiplication_tables"] = Skill("multiplication_tables", "Multiplication Tables", GradeLevel.GRADE_3, ["multiplication_intro"], 0.08, 0.0, 1)
        self.skills["division_basic"] = Skill("division_basic", "Basic Division", GradeLevel.GRADE_3, ["multiplication_tables"], 0.09, 0.0, 2)
        self.skills["fractions_intro"] = Skill("fractions_intro", "Introduction to Fractions", GradeLevel.GRADE_3, ["division_basic"], 0.10, 0.0, 3)
        
        # Grade 4 skills (order: 1, 2)
        self.skills["fractions_operations"] = Skill("fractions_operations", "Fraction Operations", GradeLevel.GRADE_4, ["fractions_intro"], 0.11, 0.0, 1)
        self.skills["decimals_intro"] = Skill("decimals_intro", "Introduction to Decimals", GradeLevel.GRADE_4, ["fractions_intro"], 0.10, 0.0, 2)
        
        # Grade 5 skills (order: 1, 2)
        self.skills["decimals_operations"] = Skill("decimals_operations", "Decimal Operations", GradeLevel.GRADE_5, ["decimals_intro"], 0.10, 0.0, 1)
        self.skills["percentages"] = Skill("percentages", "Percentages", GradeLevel.GRADE_5, ["decimals_operations"], 0.11, 0.0, 2)
        
        # Grade 6 skills (order: 1, 2)
        self.skills["integers"] = Skill("integers", "Integers", GradeLevel.GRADE_6, ["subtraction_2digit"], 0.09, 0.0, 1)
        self.skills["ratios_proportions"] = Skill("ratios_proportions", "Ratios and Proportions", GradeLevel.GRADE_6, ["fractions_operations"], 0.12, 0.0, 2)
        
        # Grade 7 skills (order: 1, 2)
        self.skills["algebraic_expressions"] = Skill("algebraic_expressions", "Algebraic Expressions", GradeLevel.GRADE_7, ["integers"], 0.13, 0.0, 1)
        self.skills["linear_equations_1var"] = Skill("linear_equations_1var", "Linear Equations (1 Variable)", GradeLevel.GRADE_7, ["algebraic_expressions"], 0.14, 0.0, 2)
        
        # Grade 8 skills (order: 1, 2)
        self.skills["linear_equations_2var"] = Skill("linear_equations_2var", "Linear Equations (2 Variables)", GradeLevel.GRADE_8, ["linear_equations_1var"], 0.15, 0.0, 1)
        self.skills["quadratic_intro"] = Skill("quadratic_intro", "Introduction to Quadratics", GradeLevel.GRADE_8, ["linear_equations_1var"], 0.16, 0.0, 2)
        
        # Grade 9 skills (Algebra 1) (order: 1, 2)
        self.skills["quadratic_equations"] = Skill("quadratic_equations", "Quadratic Equations", GradeLevel.GRADE_9, ["quadratic_intro"], 0.15, 0.0, 1)
        self.skills["polynomial_operations"] = Skill("polynomial_operations", "Polynomial Operations", GradeLevel.GRADE_9, ["algebraic_expressions"], 0.14, 0.0, 2)
        
        # Grade 10 skills (Geometry) (order: 1, 2)
        self.skills["geometric_proofs"] = Skill("geometric_proofs", "Geometric Proofs", GradeLevel.GRADE_10, ["basic_shapes"], 0.17, 0.0, 1)
        self.skills["trigonometry_basic"] = Skill("trigonometry_basic", "Basic Trigonometry", GradeLevel.GRADE_10, ["geometric_proofs"], 0.16, 0.0, 2)
        
        # Grade 11 skills (Algebra 2) (order: 1, 2)
        self.skills["exponentials_logs"] = Skill("exponentials_logs", "Exponentials and Logarithms", GradeLevel.GRADE_11, ["polynomial_operations"], 0.18, 0.0, 1)
        self.skills["trigonometry_advanced"] = Skill("trigonometry_advanced", "Advanced Trigonometry", GradeLevel.GRADE_11, ["trigonometry_basic"], 0.17, 0.0, 2)
        
        # Grade 12 skills (Pre-Calculus/Calculus) (order: 1, 2)
        self.skills["limits"] = Skill("limits", "Limits", GradeLevel.GRADE_12, ["exponentials_logs"], 0.19, 0.0, 1)
        self.skills["derivatives"] = Skill("derivatives", "Derivatives", GradeLevel.GRADE_12, ["limits"], 0.20, 0.0, 2)
    
    def get_student_state(self, student_id: str, skill_id: str) -> StudentSkillState:
        """Get or create student state for a specific skill"""
        if student_id not in self.student_states:
            self.student_states[student_id] = {}
        
        if skill_id not in self.student_states[student_id]:
            self.student_states[student_id][skill_id] = StudentSkillState()
        
        return self.student_states[student_id][skill_id]
    
    def calculate_memory_strength(self, student_id: str, skill_id: str, current_time: float) -> float:
        """Calculate current memory strength with decay"""
        state = self.get_student_state(student_id, skill_id)
        skill = self.skills[skill_id]
        
        if state.last_practice_time is None:
            return state.memory_strength
        
        time_elapsed = current_time - state.last_practice_time
        decay_factor = math.exp(-skill.forgetting_rate * time_elapsed)
        
        return state.memory_strength * decay_factor
    
    def get_all_prerequisites(self, skill_id: str) -> List[str]:
        """Get all prerequisite skills recursively"""
        prerequisites = []
        skill = self.skills.get(skill_id)
        if not skill:
            return prerequisites
        
        for prereq_id in skill.prerequisites:
            prerequisites.append(prereq_id)
            # Recursively get prerequisites of prerequisites
            prerequisites.extend(self.get_all_prerequisites(prereq_id))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_prerequisites = []
        for prereq in prerequisites:
            if prereq not in seen:
                seen.add(prereq)
                unique_prerequisites.append(prereq)
        
        return unique_prerequisites
    
    def calculate_time_penalty(self, response_time_seconds: float) -> float:
        """Calculate time penalty multiplier for response time"""
        if response_time_seconds > 180:  # 3 minutes
            return 0.5
        return 1.0
    
    def predict_correctness(self, student_id: str, skill_id: str, current_time: float) -> float:
        """Predict probability of correct answer using sigmoid function"""
        memory_strength = self.calculate_memory_strength(student_id, skill_id, current_time)
        skill = self.skills[skill_id]
        
        # Sigmoid function: P(correct) = 1 / (1 + exp(-(memory_strength - difficulty)))
        logit = memory_strength - skill.difficulty
        return 1 / (1 + math.exp(-logit))
    
    def update_student_state(self, student_id: str, skill_id: str, is_correct: bool, current_time: float, response_time_seconds: float = 0.0):
        """Update student state after practice"""
        state = self.get_student_state(student_id, skill_id)
        skill = self.skills.get(skill_id)
        skill_name = skill.name if skill else skill_id
        
        # Store previous values for logging
        prev_strength = state.memory_strength
        prev_practice_count = state.practice_count
        prev_correct_count = state.correct_count
        
        # Update practice counts
        state.practice_count += 1
        if is_correct:
            state.correct_count += 1
        
        # Calculate current memory strength with decay
        current_strength = self.calculate_memory_strength(student_id, skill_id, current_time)
        time_since_last = current_time - state.last_practice_time if state.last_practice_time else 0
        
        # Update memory strength based on performance
        if is_correct:
            # Base strength increment with diminishing returns
            strength_increment = 1.0 / (1 + 0.1 * state.correct_count)
            
            # Apply time penalty using separate function
            time_penalty = self.calculate_time_penalty(response_time_seconds)
            strength_increment *= time_penalty
            
            new_strength = min(5.0, current_strength + strength_increment)
            state.memory_strength = new_strength
            
            # Log memory strength update
            log_print(f"[MEMORY_UPDATE] Student {student_id}, Skill {skill_name} ({skill_id}): CORRECT answer")
            log_print(f"  - Previous strength: {prev_strength:.3f} (decayed from {prev_strength:.3f} over {time_since_last:.1f}s)")
            log_print(f"  - Strength increment: {strength_increment:.3f} (time penalty: {time_penalty:.2f})")
            log_print(f"  - New strength: {new_strength:.3f} (practice: {prev_practice_count}->{state.practice_count}, "
                  f"correct: {prev_correct_count}->{state.correct_count})")
        else:
            # Slight decrease for incorrect answers
            new_strength = max(-2.0, current_strength - 0.2)
            state.memory_strength = new_strength
            
            # Log memory strength update
            log_print(f"[MEMORY_UPDATE] Student {student_id}, Skill {skill_name} ({skill_id}): INCORRECT answer")
            log_print(f"  - Previous strength: {prev_strength:.3f} (decayed from {prev_strength:.3f} over {time_since_last:.1f}s)")
            log_print(f"  - Strength decrement: -0.2")
            log_print(f"  - New strength: {new_strength:.3f} (practice: {prev_practice_count}->{state.practice_count}, "
                  f"correct: {prev_correct_count}->{state.correct_count})")
        
        # Update last practice time
        state.last_practice_time = current_time
    
    def update_with_prerequisites(self, student_id: str, skill_ids: List[str], is_correct: bool, current_time: float, response_time_seconds: float = 0.0) -> List[str]:
        """Update student state including prerequisites on wrong answers"""
        all_affected_skills = []
        
        for skill_id in skill_ids:
            # Always update the direct skill
            self.update_student_state(student_id, skill_id, is_correct, current_time, response_time_seconds)
            all_affected_skills.append(skill_id)
            
            # If answer is wrong, also penalize prerequisites
            if not is_correct:
                prerequisites = self.get_all_prerequisites(skill_id)
                for prereq_id in prerequisites:
                    # Apply penalty to prerequisite (but don't count as practice attempt)
                    state = self.get_student_state(student_id, prereq_id)
                    current_strength = self.calculate_memory_strength(student_id, prereq_id, current_time)
                    
                    # Apply smaller penalty to prerequisites
                    state.memory_strength = max(-2.0, current_strength - 0.1)
                    state.last_practice_time = current_time
                    
                    all_affected_skills.append(prereq_id)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_affected_skills = []
        for skill_id in all_affected_skills:
            if skill_id not in seen:
                seen.add(skill_id)
                unique_affected_skills.append(skill_id)
        
        return unique_affected_skills
    
    def load_user_or_create(self, user_id: str) -> UserProfile:
        """Load existing user or create new one with all skills initialized"""
        all_skill_ids = list(self.skills.keys())
        user_profile = self.user_manager.get_or_create_user(user_id, all_skill_ids)
        
        # Sync user profile with current student_states for backward compatibility
        self.student_states[user_id] = {}
        for skill_id, skill_state in user_profile.skill_states.items():
            self.student_states[user_id][skill_id] = StudentSkillState(
                memory_strength=skill_state.memory_strength,
                last_practice_time=skill_state.last_practice_time,
                practice_count=skill_state.practice_count,
                correct_count=skill_state.correct_count
            )
        
        return user_profile
    
    def save_user_state(self, user_id: str, user_profile: UserProfile):
        """Save current student states back to user profile"""
        if user_id in self.student_states:
            for skill_id, student_state in self.student_states[user_id].items():
                if skill_id in user_profile.skill_states:
                    user_profile.skill_states[skill_id] = SkillState(
                        memory_strength=student_state.memory_strength,
                        last_practice_time=student_state.last_practice_time,
                        practice_count=student_state.practice_count,
                        correct_count=student_state.correct_count
                    )
        
        self.user_manager.save_user(user_profile)
    
    def record_question_attempt(self, user_profile: UserProfile, question_id: str, 
                              skill_ids: List[str], is_correct: bool, 
                              response_time_seconds: float):
        """Record a question attempt and update both memory and persistent storage"""
        current_time = time.time()
        time_penalty_applied = self.calculate_time_penalty(response_time_seconds) < 1.0
        
        # Get question details for logging
        question = self.questions.get(question_id)
        question_difficulty = question.difficulty if question else "unknown"
        expected_time = question.expected_time_seconds if question else 0.0
        time_ratio = response_time_seconds / expected_time if expected_time > 0 else 0.0
        
        skill_names = [self.skills.get(sid).name if self.skills.get(sid) else sid for sid in skill_ids]
        
        log_print(f"[QUESTION_ATTEMPT] Student {user_profile.user_id}: Recording attempt for question {question_id}")
        log_print(f"  - Result: {'CORRECT' if is_correct else 'INCORRECT'}")
        log_print(f"  - Skills: {', '.join(skill_names)} ({', '.join(skill_ids)})")
        log_print(f"  - Difficulty: {question_difficulty}, Response time: {response_time_seconds:.1f}s "
              f"(expected: {expected_time:.1f}s, ratio: {time_ratio:.2f}x)")
        if time_penalty_applied:
            log_print(f"  - Time penalty applied (response time > 180s)")
        
        # Update memory states
        affected_skills = self.update_with_prerequisites(
            user_profile.user_id, skill_ids, is_correct, current_time, response_time_seconds
        )
        
        log_print(f"  - Updated {len(affected_skills)} skill(s): {', '.join(affected_skills)}")
        
        # Save to persistent storage
        self.save_user_state(user_profile.user_id, user_profile)
        
        # Add to question history
        self.user_manager.add_question_attempt(
            user_profile, question_id, skill_ids, is_correct, 
            response_time_seconds, time_penalty_applied
        )
        
        total_attempts = len(user_profile.question_history)
        log_print(f"  - Total question attempts: {total_attempts}")
        
        return affected_skills
    
    def get_skill_scores(self, student_id: str, current_time: float) -> Dict[str, Dict[str, float]]:
        """Get all skill scores for a student"""
        scores = {}
        
        for skill_id, skill in self.skills.items():
            state = self.get_student_state(student_id, skill_id)
            memory_strength = self.calculate_memory_strength(student_id, skill_id, current_time)
            probability = self.predict_correctness(student_id, skill_id, current_time)
            
            scores[skill_id] = {
                'name': skill.name,
                'grade_level': skill.grade_level.name,
                'memory_strength': round(memory_strength, 3),
                'probability': round(probability, 3),
                'practice_count': state.practice_count,
                'correct_count': state.correct_count,
                'accuracy': round(state.correct_count / state.practice_count, 3) if state.practice_count > 0 else 0.0
            }
        
        return scores
    
    def get_recommended_skills(self, student_id: str, current_time: float, threshold: float = 0.7) -> List[str]:
        """
        Get skills that need practice based on memory strength decay.
        Returns skills sorted by learning journey: grade level -> order -> probability.
        """
        recommendations = []
        skipped_prerequisites = []
        skipped_above_threshold = []
        
        for skill_id, skill in self.skills.items():
            probability = self.predict_correctness(student_id, skill_id, current_time)
            
            # Check if prerequisites are met
            prerequisites_met = True
            missing_prereqs = []
            for prereq_id in skill.prerequisites:
                prereq_prob = self.predict_correctness(student_id, prereq_id, current_time)
                if prereq_prob < threshold:
                    prerequisites_met = False
                    missing_prereqs.append((prereq_id, prereq_prob))
            
            # Recommend if probability is below threshold and prerequisites are met
            if probability < threshold and prerequisites_met:
                recommendations.append((skill_id, skill, probability))
            elif not prerequisites_met:
                skipped_prerequisites.append((skill_id, skill.name, missing_prereqs))
            elif probability >= threshold:
                skipped_above_threshold.append((skill_id, skill.name, probability))
        
        # Sort by learning journey: grade level (ascending) -> order (ascending) -> probability (ascending)
        # This ensures students follow a structured learning path
        recommendations.sort(key=lambda x: (
            x[1].grade_level.value,  # Grade level (K=0, Grade 1=1, etc.)
            x[1].order,                # Order within grade
            x[2]                       # Probability (lower = needs more practice)
        ))
        
        # Log detailed information about skill recommendations
        log_print(f"[LEARNING_JOURNEY] Student {student_id}: Analyzing skills for recommendations (threshold={threshold:.2f})")
        log_print(f"[LEARNING_JOURNEY] Found {len(recommendations)} skills needing practice")
        
        if recommendations:
            log_print(f"[LEARNING_JOURNEY] Recommended skills (sorted by learning journey):")
            for idx, (skill_id, skill, prob) in enumerate(recommendations[:10], 1):  # Log top 10
                log_print(f"  {idx}. {skill.name} (Grade {skill.grade_level.value}, Order {skill.order}, "
                      f"Probability: {prob:.3f}, Skill ID: {skill_id})")
            if len(recommendations) > 10:
                log_print(f"  ... and {len(recommendations) - 10} more skills")
        
        if skipped_prerequisites:
            log_print(f"[LEARNING_JOURNEY] Skipped {len(skipped_prerequisites)} skills due to unmet prerequisites:")
            for skill_id, skill_name, missing in skipped_prerequisites[:5]:  # Log first 5
                prereq_str = ", ".join([f"{p[0]}({p[1]:.2f})" for p in missing])
                log_print(f"  - {skill_name} ({skill_id}): Missing prerequisites: {prereq_str}")
        
        if skipped_above_threshold:
            log_print(f"[LEARNING_JOURNEY] Skipped {len(skipped_above_threshold)} skills (already above threshold)")
        
        result = [skill_id for skill_id, _, _ in recommendations]
        log_print(f"[LEARNING_JOURNEY] Returning {len(result)} recommended skills in learning journey order")
        return result
    
    def analyze_recent_performance(self, user_profile: UserProfile, lookback_count: int = 5) -> Dict[str, float]:
        """
        Analyze recent performance to determine difficulty adjustment.
        Returns a dict with:
        - 'performance_score': -1.0 (struggling) to 1.0 (excelling)
        - 'difficulty_adjustment': negative = easier, positive = harder
        - 'correctness_rate': 0.0 to 1.0
        - 'avg_time_ratio': average response time / expected time
        """
        if not user_profile.question_history or len(user_profile.question_history) == 0:
            # No history: start with medium difficulty
            log_print(f"[ADAPTIVE_DIFFICULTY] Student {user_profile.user_id}: No question history, using default difficulty (no adjustment)")
            return {
                'performance_score': 0.0,
                'difficulty_adjustment': 0.0,
                'correctness_rate': 0.5,
                'avg_time_ratio': 1.0
            }
        
        # Get recent attempts (last N questions)
        recent_attempts = user_profile.question_history[-lookback_count:]
        total_history = len(user_profile.question_history)
        
        log_print(f"[ADAPTIVE_DIFFICULTY] Student {user_profile.user_id}: Analyzing recent performance "
              f"(looking at last {len(recent_attempts)} of {total_history} total attempts)")
        
        # Calculate correctness rate
        correct_count = sum(1 for attempt in recent_attempts if attempt.is_correct)
        correctness_rate = correct_count / len(recent_attempts)
        
        # Calculate average response time ratio
        # Get expected time from questions
        time_ratios = []
        time_details = []
        for attempt in recent_attempts:
            question = self.questions.get(attempt.question_id)
            if question and attempt.response_time_seconds > 0:
                expected_time = question.expected_time_seconds
                if expected_time > 0:
                    time_ratio = attempt.response_time_seconds / expected_time
                    time_ratios.append(time_ratio)
                    time_details.append((attempt.question_id, attempt.response_time_seconds, expected_time, time_ratio))
        
        avg_time_ratio = sum(time_ratios) / len(time_ratios) if time_ratios else 1.0
        
        # Calculate performance score
        # - Correctness contributes 60% weight
        # - Time efficiency contributes 40% weight
        correctness_score = (correctness_rate - 0.5) * 2.0  # -1.0 to 1.0
        time_score = (1.0 - min(avg_time_ratio, 2.0) / 2.0) * 2.0 - 1.0  # -1.0 to 1.0 (faster = better)
        
        performance_score = correctness_score * 0.6 + time_score * 0.4
        
        # Determine difficulty adjustment
        # If struggling (low correctness, slow): make easier (negative adjustment)
        # If excelling (high correctness, fast): make harder (positive adjustment)
        if performance_score < -0.3:
            # Struggling: easier questions (reduce difficulty by 0.2-0.4)
            difficulty_adjustment = -0.3
            performance_level = "STRUGGLING"
        elif performance_score < -0.1:
            # Slightly struggling: slightly easier (reduce by 0.1-0.2)
            difficulty_adjustment = -0.15
            performance_level = "SLIGHTLY_STRUGGLING"
        elif performance_score > 0.3:
            # Excelling: harder questions (increase difficulty by 0.2-0.4)
            difficulty_adjustment = 0.3
            performance_level = "EXCELLING"
        elif performance_score > 0.1:
            # Slightly excelling: slightly harder (increase by 0.1-0.2)
            difficulty_adjustment = 0.15
            performance_level = "SLIGHTLY_EXCELLING"
        else:
            # Balanced performance: maintain current difficulty
            difficulty_adjustment = 0.0
            performance_level = "BALANCED"
        
        # Detailed logging
        log_print(f"[ADAPTIVE_DIFFICULTY] Performance Metrics:")
        log_print(f"  - Correctness: {correct_count}/{len(recent_attempts)} = {correctness_rate:.2%} "
              f"(score: {correctness_score:+.2f}, weight: 60%)")
        log_print(f"  - Time Efficiency: avg ratio = {avg_time_ratio:.2f}x expected time "
              f"(score: {time_score:+.2f}, weight: 40%)")
        if time_details:
            log_print(f"  - Time Details (last {min(3, len(time_details))} questions):")
            for qid, actual, expected, ratio in time_details[-3:]:
                log_print(f"    * Q{qid}: {actual:.1f}s / {expected:.1f}s = {ratio:.2f}x")
        log_print(f"  - Combined Performance Score: {performance_score:+.3f} ({performance_level})")
        log_print(f"  - Difficulty Adjustment: {difficulty_adjustment:+.2f} "
              f"({'EASIER' if difficulty_adjustment < 0 else 'HARDER' if difficulty_adjustment > 0 else 'SAME'})")
        
        return {
            'performance_score': performance_score,
            'difficulty_adjustment': difficulty_adjustment,
            'correctness_rate': correctness_rate,
            'avg_time_ratio': avg_time_ratio
        }

    def get_next_question(self, student_id: str, current_time: float, is_retry: bool = False, exclude_question_ids: Optional[List[str]] = None) -> Optional[Question]:
        """
        Get the next best question for the student, avoiding repeats.
        Intelligently selects question difficulty based on recent performance.
        If no questions are available, try to generate one.
        """
        recommended_skills = self.get_recommended_skills(student_id, current_time)
        
        if not recommended_skills:
            return None

        user_profile = self.user_manager.load_user(student_id)
        if not user_profile:
            return None
        
        answered_question_ids = {attempt.question_id for attempt in user_profile.question_history}
        
        # Also exclude questions that are already selected in the current batch
        if exclude_question_ids:
            answered_question_ids.update(exclude_question_ids)
        
        # Analyze recent performance to determine difficulty adjustment
        performance_analysis = self.analyze_recent_performance(user_profile)
        difficulty_adjustment = performance_analysis['difficulty_adjustment']
        
        log_print(f"[QUESTION_SELECTION] Student {student_id}: Selecting next question with adaptive difficulty")
        log_print(f"[QUESTION_SELECTION] Answered questions: {len(answered_question_ids)}, "
              f"Available questions: {len(self.questions)}")
        
        # Try to find an unanswered question from the recommended skills with adaptive difficulty
        for skill_idx, skill_id in enumerate(recommended_skills, 1):
            skill = self.skills.get(skill_id)
            if not skill:
                continue
            
            # Calculate target difficulty range based on skill difficulty and performance
            base_difficulty = skill.difficulty
            target_difficulty = base_difficulty + difficulty_adjustment
            
            # Allow some flexibility: ±0.2 around target difficulty
            min_difficulty = max(0.0, target_difficulty - 0.2)
            max_difficulty = target_difficulty + 0.2
            
            log_print(f"[QUESTION_SELECTION] Trying skill {skill_idx}/{len(recommended_skills)}: "
                  f"{skill.name} (ID: {skill_id})")
            log_print(f"  - Base difficulty: {base_difficulty:.2f}, "
                  f"Target after adjustment: {target_difficulty:.2f} (range: {min_difficulty:.2f}-{max_difficulty:.2f})")
            
            # Get all candidate questions for this skill
            all_candidates = [
                q for q in self.questions.values() 
                if skill_id in q.skill_ids and q.question_id not in answered_question_ids
            ]
            
            if not all_candidates:
                log_print(f"  - No unanswered questions available for this skill")
                continue
            
            log_print(f"  - Found {len(all_candidates)} unanswered candidate question(s)")
            
            # Filter by difficulty range (adaptive selection)
            filtered_candidates = [
                q for q in all_candidates
                if min_difficulty <= q.difficulty <= max_difficulty
            ]
            
            # If we have questions in the target difficulty range, use them
            if filtered_candidates:
                # Sort by how close they are to target difficulty, then return the best match
                filtered_candidates.sort(key=lambda q: abs(q.difficulty - target_difficulty))
                selected = filtered_candidates[0]
                log_print(f"[QUESTION_SELECTION] [SUCCESS] Selected question {selected.question_id} "
                      f"(difficulty: {selected.difficulty:.2f}, target: {target_difficulty:.2f}, "
                      f"adjustment: {difficulty_adjustment:+.2f}, skill: {skill.name})")
                log_print(f"[QUESTION_SELECTION] Question selected from {len(filtered_candidates)} questions "
                      f"in target difficulty range")
                return selected
            
            # If no questions in target range, use closest match from all candidates
            # This ensures we always return a question if available
            log_print(f"  - No questions in target range ({min_difficulty:.2f}-{max_difficulty:.2f}), "
                  f"using closest match from {len(all_candidates)} candidates")
            all_candidates.sort(key=lambda q: abs(q.difficulty - target_difficulty))
            selected = all_candidates[0]
            difficulty_diff = abs(selected.difficulty - target_difficulty)
            log_print(f"[QUESTION_SELECTION] [FALLBACK] Selected question {selected.question_id} "
                  f"(difficulty: {selected.difficulty:.2f}, target: {target_difficulty:.2f}, "
                  f"difference: {difficulty_diff:.2f}, skill: {skill.name})")
            return selected

        # If we're here, no unanswered questions were found. Time to generate one.
        if is_retry or self.question_generator is None:
            log_print("No unanswered questions found and cannot generate new ones.")
            return None

        log_print("[INFO] No unanswered questions available. Attempting to generate a new one...")
        
        top_skill_id = recommended_skills[0]
        
        source_question_id = None
        # Find the most recently answered question for this skill to use as a template
        for attempt in reversed(user_profile.question_history):
            if top_skill_id in attempt.skill_ids:
                source_question_id = attempt.question_id
                break
        
        if not source_question_id:
            # Fallback: find any question for the skill
            all_skill_questions = [q.question_id for q in self.questions.values() if top_skill_id in q.skill_ids]
            if all_skill_questions:
                source_question_id = all_skill_questions[0]

        if not source_question_id:
            log_print(f"Could not find any source question for skill {top_skill_id} to generate a variation.")
            return None

        try:
            log_print(f"[INFO] Generating variation based on question {source_question_id} for skill {top_skill_id}...")
            generated_ids = self.question_generator.generate_variations(source_question_id, num_variations=1)
            
            if generated_ids:
                log_print(f"[OK] Successfully generated {len(generated_ids)} new question(s).")
                self._reload_questions()
                # Retry finding a question
                return self.get_next_question(student_id, current_time, is_retry=True)
            else:
                log_print("[WARNING] Question generation did not produce any new questions.")
                return None
        except Exception as e:
            log_print(f"[ERROR] Error during question generation: {e}")
            return None