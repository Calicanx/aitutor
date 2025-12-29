#!/usr/bin/env python3
"""
Comprehensive tests for Khan Academy hierarchy in questions_db
"""

from managers.mongodb_manager import mongo_db

print("=" * 70)
print("Khan Academy Hierarchy Tests")
print("=" * 70)

print("\n✅ TEST 1: Database Connections")
print("-" * 70)
result = mongo_db.test_connection()
print(f"Result: {'PASSED' if result else 'FAILED'}")

print("\n✅ TEST 2: Explore Khan Hierarchy by Region")
print("-" * 70)
for region in mongo_db.regions.find():
    region_code = region.get('region_code', 'N/A')
    print(f"\n📍 Region: {region_code}")
    
    # Count courses in region
    courses = list(mongo_db.courses.find({"region": region_code}).limit(5))
    total_courses = mongo_db.courses.count_documents({"region": region_code})
    print(f"  Total Courses: {total_courses}")
    print(f"  Sample courses:")
    for course in courses:
        print(f"    - {course['title']} (slug: {course['slug']})")

print("\n✅ TEST 3: Verify Hierarchy Relationships")
print("-" * 70)
# Get a question and trace it back through hierarchy
question = mongo_db.questions.find_one()
if question:
    print(f"Starting with question: {question['question_id']}")
    
    # Follow the chain
    exercise = mongo_db.exercises.find_one({"exercise_id": question['exercise_id']})
    if exercise:
        print(f"  ↑ Exercise: {exercise.get('title', 'N/A')} (ID: {exercise['exercise_id']})")
        
        lesson = mongo_db.lessons.find_one({"lesson_id": exercise['lesson_id']})
        if lesson:
            print(f"  ↑ Lesson: {lesson.get('title', 'N/A')} (ID: {lesson['lesson_id']})")
            
            unit = mongo_db.units.find_one({"unit_id": lesson['unit_id']})
            if unit:
                print(f"  ↑ Unit: {unit.get('title', 'N/A')} (ID: {unit['unit_id']})")
                
                course = mongo_db.courses.find_one({"course_id": unit['course_id']})
                if course:
                    print(f"  ↑ Course: {course.get('title', 'N/A')} (Region: {course.get('region', 'N/A')})")
                    print(f"\n  ✓ Full chain verified!")

print("\n✅ TEST 4: Grade Level Mapping")
print("-" * 70)
print("Checking US Math courses for grade level patterns:\n")

us_courses = mongo_db.courses.find({"region": "US"}).limit(15)
for course in us_courses:
    title = course['title']
    slug = course['slug']
    order = course.get('order_in_region', 0)
    
    # Try to detect grade level from title
    grade_hint = "?"
    title_lower = title.lower()
    if 'kindergarten' in title_lower or title_lower.startswith('k '):
        grade_hint = "K"
    elif '1st' in title_lower or 'grade 1' in title_lower:
        grade_hint = "1"
    elif '2nd' in title_lower or 'grade 2' in title_lower:
        grade_hint = "2"
    elif '3rd' in title_lower or 'grade 3' in title_lower:
        grade_hint = "3"
    elif any(f'{i}th' in title_lower or f'grade {i}' in title_lower for i in range(4, 13)):
        for i in range(4, 13):
            if f'{i}th' in title_lower or f'grade {i}' in title_lower:
                grade_hint = str(i)
                break
    elif 'algebra' in title_lower and 'algebra 2' not in title_lower:
        grade_hint = "9"
    elif 'geometry' in title_lower:
        grade_hint = "10"
    elif 'algebra 2' in title_lower or 'algebra ii' in title_lower:
        grade_hint = "11"
    elif 'precalculus' in title_lower or 'pre-calculus' in title_lower:
        grade_hint = "12"
    
    print(f"  [{order:2}] Grade {grade_hint:>2}: {title}")

print("\n✅ TEST 5: Subject Classification")
print("-" * 70)

def extract_subject(course_title):
    """Extract subject from course title"""
    title_lower = course_title.lower()
    
    if any(word in title_lower for word in ['math', 'algebra', 'geometry', 'calculus', 'trigonometry', 'statistics', 'arithmetic']):
        return 'Math'
    elif any(word in title_lower for word in ['science', 'physics', 'chemistry', 'biology']):
        return 'Science'
    elif 'history' in title_lower:
        return 'History'
    elif any(word in title_lower for word in ['english', 'grammar', 'reading']):
        return 'English'
    elif 'economics' in title_lower:
        return 'Economics'
    elif any(word in title_lower for word in ['computer', 'programming', 'coding']):
        return 'Computer Science'
    elif 'art' in title_lower:
        return 'Arts'
    elif 'music' in title_lower:
        return 'Music'
    else:
        return 'Other'

print("Sample subject classification:\n")
all_courses = list(mongo_db.courses.find().limit(20))
subjects_found = {}
for course in all_courses:
    subject = extract_subject(course['title'])
    if subject not in subjects_found:
        subjects_found[subject] = []
    subjects_found[subject].append(course['title'])

for subject, titles in sorted(subjects_found.items()):
    print(f"\n  {subject}:")
    for title in titles[:3]:  # Show max 3 examples
        print(f"    - {title}")

print("\n✅ TEST 6: Exercise → Questions Mapping")
print("-" * 70)
# Sample some exercises and their questions
exercises_with_questions = list(mongo_db.exercises.aggregate([
    {"$match": {"question_count": {"$gt": 0}}},
    {"$limit": 5}
]))

for exercise in exercises_with_questions:
    exercise_id = exercise['exercise_id']
    question_count_in_db = mongo_db.questions.count_documents({"exercise_id": exercise_id})
    
    print(f"\n  Exercise: {exercise['title']}")
    print(f"    Reported question_count: {exercise.get('question_count', 0)}")
    print(f"    Actual questions in DB: {question_count_in_db}")
    print(f"    Lesson: {exercise.get('lesson_id', 'N/A')}")

print("\n✅ TEST 7: Skills Coverage")
print("-" * 70)
print("Checking which units could map to generated_skills:\n")

# Get all generated skills
gen_skills = list(mongo_db.generated_skills.find().limit(10))
print(f"Total generated_skills: {mongo_db.generated_skills.count_documents({})}")
print(f"Total units (potential skills): {mongo_db.units.count_documents({})}")

print(f"\nSample generated skills:")
for skill in gen_skills[:5]:
    print(f"  - {skill.get('name', 'N/A')} (Grade: {skill.get('grade_level', 'N/A')})")

print("\n" + "=" * 70)
print("All Tests Complete!")
print("=" * 70)

print("\n📊 Summary:")
print(f"  ✓ Regions: {mongo_db.regions.count_documents({})}")
print(f"  ✓ Courses: {mongo_db.courses.count_documents({})}")
print(f"  ✓ Units: {mongo_db.units.count_documents({})}")
print(f"  ✓ Lessons: {mongo_db.lessons.count_documents({})}")
print(f"  ✓ Exercises: {mongo_db.exercises.count_documents({})}")
print(f"  ✓ Questions: {mongo_db.questions.count_documents({})}")
print(f"  ✓ Generated Skills: {mongo_db.generated_skills.count_documents({})}")
