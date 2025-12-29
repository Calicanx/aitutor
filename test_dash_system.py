#!/usr/bin/env python3
"""
Test script for DASH System with questions_db
"""

import sys
from managers.mongodb_manager import mongo_db

print("=" * 70)
print("DASH System Test - Loading from questions_db")
print("=" * 70)

print("\n1. Testing MongoDB connections...")
result = mongo_db.test_connection()
if not result:
    print("❌ MongoDB connection failed!")
    sys.exit(1)

print("\n2. Checking available data...")
print(f"  ✓ Regions: {mongo_db.regions.count_documents({})}")
print(f"  ✓ Courses: {mongo_db.courses.count_documents({})}")
print(f"  ✓ Units: {mongo_db.units.count_documents({})}")
print(f"  ✓ Lessons: {mongo_db.lessons.count_documents({})}")
print(f"  ✓ Exercises: {mongo_db.exercises.count_documents({})}")
print(f"  ✓ Questions: {mongo_db.questions.count_documents({})}")
print(f"  ✓ Generated Skills: {mongo_db.generated_skills.count_documents({})}")

print("\n3. Exploring data structure...")

# Check regions
print("\n📍 Available Regions:")
for region in mongo_db.regions.find():
    print(f"  - {region.get('region_code', 'N/A')}: {region.get('name', 'N/A')}")

# Sample course
print("\n📚 Sample Course:")
course = mongo_db.courses.find_one()
if course:
    print(f"  Course ID: {course.get('course_id', 'N/A')}")
    print(f"  Title: {course.get('title', 'N/A')}")
    print(f"  Region: {course.get('region', 'N/A')}")
    for key in course.keys():
        if key not in ['_id', 'course_id', 'title', 'region']:
            print(f"  {key}: {course[key]}")

# Sample unit
print("\n📖 Sample Unit:")
unit = mongo_db.units.find_one()
if unit:
    print(f"  Unit ID: {unit.get('unit_id', 'N/A')}")
    print(f"  Title: {unit.get('title', 'N/A')}")
    print(f"  Course ID: {unit.get('course_id', 'N/A')}")
    for key in unit.keys():
        if key not in ['_id', 'unit_id', 'title', 'course_id']:
            print(f"  {key}: {unit[key]}")

# Sample lesson
print("\n📝 Sample Lesson:")
lesson = mongo_db.lessons.find_one()
if lesson:
    print(f"  Lesson ID: {lesson.get('lesson_id', 'N/A')}")
    print(f"  Title: {lesson.get('title', 'N/A')}")
    print(f"  Unit ID: {lesson.get('unit_id', 'N/A')}")
    for key in lesson.keys():
        if key not in ['_id', 'lesson_id', 'title', 'unit_id']:
            print(f"  {key}: {lesson[key]}")

# Sample exercise
print("\n🏋️ Sample Exercise:")
exercise = mongo_db.exercises.find_one()
if exercise:
    print(f"  Exercise ID: {exercise.get('exercise_id', 'N/A')}")
    print(f"  Title: {exercise.get('title', 'N/A')}")
    print(f"  Lesson ID: {exercise.get('lesson_id', 'N/A')}")
    for key in exercise.keys():
        if key not in ['_id', 'exercise_id', 'title', 'lesson_id']:
            value = exercise[key]
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")

# Sample question
print("\n❓ Sample Question:")
question = mongo_db.questions.find_one()
if question:
    print(f"  Question ID: {question.get('question_id', 'N/A')}")
    print(f"  Exercise ID: {question.get('exercise_id', 'N/A')}")
    for key in question.keys():
        if key not in ['_id', 'question_id', 'exercise_id']:
            value = question[key]
            if isinstance(value, (dict, list)):
                print(f"  {key}: <{type(value).__name__}>")
            elif isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")

print("\n4. Testing DASH System initialization...")
try:
    from services.DashSystem.dash_system import DASHSystem
    
    print("  Creating DASH System instance...")
    dash = DASHSystem(use_mongodb=True)
    
    print(f"  ✓ Loaded {len(dash.skills)} skills")
    print(f"  ✓ Loaded {len(dash.question_index)} questions into index")
    print(f"  ✓ Cache size: {len(dash.question_cache)}")
    
    # Show sample skills
    if dash.skills:
        print("\n  Sample skills:")
        for i, (skill_id, skill) in enumerate(list(dash.skills.items())[:5]):
            print(f"    - {skill_id}: {skill.name} (Grade {skill.grade_level.name})")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error initializing DASH System: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
