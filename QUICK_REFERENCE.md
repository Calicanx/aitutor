# Quick Reference - Local MongoDB Setup

## ✅ Status: READY

Your local MongoDB is configured and tested!

## Connection Info
```
URI: mongodb://localhost:27017/
Main DB: ai_tutor
Questions DB: questions_db
```

## Collections

### ai_tutor database
- `generated_skills` (126) - Current DASH skills
- `scraped_questions` (38,168) - Old question format
- `sessions` (0) - User sessions

### questions_db database  
- `regions` (3) - US, IN, IN-KA
- `courses` (293) - Khan Academy courses
- `units` (2,672) - Skills (DASH mapping)
- `lessons` (13,610) - Sub-skills (DASH mapping)
- `exercises` (21,143) - Question pools
- `questions` (3,942) - Khan questions with Perseus format

## Quick Tests

```bash
# Verify everything works
python3 test_dash_system.py

# Test Khan hierarchy
python3 test_khan_hierarchy.py

# Quick MongoDB check
python3 -c "from managers.mongodb_manager import mongo_db; print('Regions:', [r['region_code'] for r in mongo_db.regions.find()])"
```

## Common Queries

```python
from managers.mongodb_manager import mongo_db

# Get US Math courses
list(mongo_db.courses.find({"region": "US"}).limit(5))

# Count questions per region
for region in mongo_db.regions.find():
    count = mongo_db.courses.count_documents({"region": region['region_code']})
    print(f"{region['region_code']}: {count} courses")

# Trace question hierarchy
q = mongo_db.questions.find_one()
ex = mongo_db.exercises.find_one({"exercise_id": q['exercise_id']})
lesson = mongo_db.lessons.find_one({"lesson_id": ex['lesson_id']})
unit = mongo_db.units.find_one({"unit_id": lesson['unit_id']})
course = mongo_db.courses.find_one({"course_id": unit['course_id']})
```

## Implementation Ready!

Follow [DASH_INTEGRATION_PLAN.md](documentation/DASH_INTEGRATION_PLAN.md) to:
1. Map Units → Skills
2. Map Lessons → Sub-skills
3. Update question loading
4. Implement assessment flow
