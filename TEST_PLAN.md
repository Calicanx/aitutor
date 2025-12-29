# DASH System Test Plan - Local MongoDB

## Summary

✅ **MongoDB Setup Complete**
- Local MongoDB is running on port 27017
- Two databases configured:
  - `ai_tutor`: Main app data (users, sessions, generated_skills, scraped_questions)
  - `questions_db`: Khan Academy hierarchy (regions, courses, units, lessons, exercises, questions)

## Current Status

### What's Working ✅
1. MongoDB connections to both databases
2. MongoDB manager updated with dual-database support
3. DASH system loads successfully
4. Skills loading from `generated_skills` (126 skills)
5. Questions indexing from `scraped_questions` (1,623 questions filtered by skills)

### What Needs Implementation 🔨

According to the DASH_INTEGRATION_PLAN.md, we need to:

1. **Switch from scraped_questions to questions_db hierarchy**
   - Current: Uses `scraped_questions` with fabricated IDs
   - Target: Use `questions` collection with proper Khan hierarchy
   
2. **Map Khan Academy hierarchy to DASH concepts**
   - Region → Filter (dropdown)
   - Course → Learning Path (hidden)
   - **Unit → Skill** (primary tracking)
   - **Lesson → Sub-skill** (granular progress)
   - Exercise → Question Pool
   - Question → Practice item

3. **Implement Initial Assessment Flow**
   - Progressive difficulty assessment (10 questions)
   - Calculate actual grade level from performance
   - Initialize mastered skills based on assessment

4. **Update Question Selection Logic**
   - Select from Khan hierarchy instead of exerciseDirName
   - Use exercise_id → lesson_id → unit_id mapping

## Data Comparison

### Questions Available:
- `scraped_questions` (ai_tutor): **38,168** questions
- `questions` (questions_db): **3,942** questions

### Khan Academy Hierarchy (questions_db):
- **Regions**: 3 (US, IN, IN-KA)
- **Courses**: 293
- **Units**: 2,672
- **Lessons**: 13,610  
- **Exercises**: 21,143
- **Questions**: 3,942

## Test Scenarios

### Test 1: Verify Database Connections
```bash
python3 test_dash_system.py
```
**Expected**: ✅ Both databases connect, all collections accessible

**Status**: ✅ PASSED

### Test 2: Load DASH with Current Implementation
```python
from services.DashSystem.dash_system import DASHSystem
dash = DASHSystem(use_mongodb=True)
```
**Expected**: Loads 126 skills, 1,623 questions

**Status**: ✅ PASSED

### Test 3: Explore Khan Hierarchy
**Query regions and their courses**:
```python
from managers.mongodb_manager import mongo_db

# Get all regions
for region in mongo_db.regions.find():
    print(f"Region: {region['region_code']}")
    
    # Count courses in region
    course_count = mongo_db.courses.count_documents({"region": region['region_code']})
    print(f"  Courses: {course_count}")
```

**Status**: ⏳ PENDING

### Test 4: Map Exercise → Lesson → Unit → Course
**Verify hierarchy relationships**:
```python
# Get a question
question = mongo_db.questions.find_one()
exercise_id = question['exercise_id']

# Follow the chain
exercise = mongo_db.exercises.find_one({"exercise_id": exercise_id})
lesson = mongo_db.lessons.find_one({"lesson_id": exercise['lesson_id']})
unit = mongo_db.units.find_one({"unit_id": lesson['unit_id']})
course = mongo_db.courses.find_one({"course_id": unit['course_id']})

print(f"Question → Exercise → Lesson → Unit → Course")
print(f"{question['question_id']} → {exercise['title']} → {lesson['title']} → {unit['title']} → {course['title']}")
```

**Status**: ⏳ PENDING

### Test 5: Grade Level Mapping
**Test course → grade level derivation**:
```python
# Check course slugs for grade level patterns
courses = mongo_db.courses.find({"region": "US"}).limit(20)
for course in courses:
    print(f"{course['slug']}: {course['title']}")
    # Should map to grade levels (K-12)
```

**Status**: ⏳ PENDING

### Test 6: Subject Classification
**Verify subject extraction from course titles**:
```python
from services.DashSystem.dash_api import extract_subject  # If exists

courses = mongo_db.courses.find().limit(20)
for course in courses:
    subject = extract_subject(course['title'])
    print(f"{course['title']} → {subject}")
```

**Status**: ⏳ PENDING

## Implementation Checklist

Based on DASH_INTEGRATION_PLAN.md Phase 2:

- [ ] Create `KhanSkill` model (maps to Units)
- [ ] Create `KhanSubSkill` model (maps to Lessons)
- [ ] Modify `_load_from_mongodb` to load from Khan hierarchy
- [ ] Build question index using exercise → lesson → unit mapping
- [ ] Update `get_recommended_skills` for unit-based skills
- [ ] Update `get_next_question` for Khan hierarchy
- [ ] Test question retrieval with Perseus content

## Next Steps

1. **Run remaining tests** (Tests 3-6) to verify data integrity
2. **Document data mapping** between old and new structures
3. **Decide**: 
   - Keep both question sources? (38K scraped + 3.9K Khan)
   - Migrate fully to Khan hierarchy?
   - Hybrid approach?
4. **Implement Phase 2** from DASH integration plan
5. **Create assessment flow** (Phase 3)

## Running Tests

```bash
# Test MongoDB connections
python3 test_dash_system.py

# Test DASH system initialization  
python3 -c "from services.DashSystem.dash_system import DASHSystem; dash = DASHSystem(); print(f'Skills: {len(dash.skills)}, Questions: {len(dash.question_index)}')"

# Explore Khan hierarchy
python3 -c "from managers.mongodb_manager import mongo_db; print([r['region_code'] for r in mongo_db.regions.find()])"
```

## Questions for Discussion

1. **Question Coverage**: Why only 3.9K questions in questions_db vs 38K in scraped_questions?
   - Are they different subsets?
   - Is questions_db newer/better quality?
   
2. **Migration Strategy**: Should we:
   - Replace scraped_questions entirely?
   - Keep both and prioritize Khan hierarchy?
   - Merge data?

3. **Missing Collections**: Integration plan mentions courses/units/lessons but we have them!
   - Cloud MongoDB didn't have them, but questions_db does
   - Can proceed with full implementation

## Files Modified

- ✅ `managers/mongodb_manager.py` - Added questions_db support
- ✅ `.env` - Added MONGODB_QUESTIONS_DB_NAME
- ✅ `scripts/sync_cloud_to_local.py` - Data sync tool
- ✅ `test_dash_system.py` - Comprehensive test script
