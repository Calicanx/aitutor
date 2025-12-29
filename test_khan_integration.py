#!/usr/bin/env python3
"""
Test DASH System with Khan Academy Hierarchy Integration
"""

import sys

print("=" * 70)
print("Testing DASH System with Khan Academy Hierarchy")
print("=" * 70)

# Test 1: Import Khan models
print("\n1. Testing Khan models import...")
try:
    from services.DashSystem.khan_models import (
        KhanSkill, KhanSubSkill, derive_grade_from_course, extract_subject, GradeLevel
    )
    print("  ✓ Khan models imported successfully")
except Exception as e:
    print(f"  ✗ Failed to import Khan models: {e}")
    sys.exit(1)

# Test 2: Test subject extraction
print("\n2. Testing subject extraction...")
test_courses = [
    "2nd grade math",
    "High school biology",
    "Financial Literacy",
    "Algebra 1",
    "Computer programming"
]
for course in test_courses:
    subject = extract_subject(course)
    print(f"  '{course}' → {subject}")

# Test 3: Test grade level derivation
print("\n3. Testing grade level derivation...")
test_courses_grades = [
    ("Kindergarten math", "early-math", 0),
    ("2nd grade math", "cc-2nd-grade-math", 2),
    ("Algebra 1", "algebra", 9),
    ("High school geometry", "geometry", 10),
]
for title, slug, order in test_courses_grades:
    grade = derive_grade_from_course(title, slug, order)
    print(f"  '{title}' → {grade.name}")

# Test 4: Initialize DASH with Khan hierarchy (US Math)
print("\n4. Testing DASH initialization with Khan hierarchy (US Math)...")
try:
    from services.DashSystem.dash_system import DASHSystem
    
    dash = DASHSystem(
        use_mongodb=True,
        use_khan_hierarchy=True,
        region="US",
        subject="Math"
    )
    
    print(f"  ✓ DASH initialized successfully")
    print(f"  ✓ Khan Skills (Units): {len(dash.khan_skills)}")
    print(f"  ✓ Khan Sub-skills (Lessons): {len(dash.khan_sub_skills)}")
    print(f"  ✓ Questions indexed: {len(dash.question_index)}")
    print(f"  ✓ Skills with questions: {len(dash.skill_question_index)}")
    
    # Show sample skills
    if dash.khan_skills:
        print("\n  Sample Khan Skills (Units):")
        for i, (skill_id, skill) in enumerate(list(dash.khan_skills.items())[:5]):
            sub_skill_count = len(skill.sub_skills)
            question_count = len(dash.skill_question_index.get(skill_id, []))
            print(f"    [{i+1}] {skill.name}")
            print(f"        Grade: {skill.grade_level.name}, Sub-skills: {sub_skill_count}, Questions: {question_count}")
    
    # Show sample sub-skills
    if dash.khan_sub_skills:
        print("\n  Sample Khan Sub-skills (Lessons):")
        for i, (sub_skill_id, sub_skill) in enumerate(list(dash.khan_sub_skills.items())[:5]):
            print(f"    [{i+1}] {sub_skill.name}")
            print(f"        Parent skill: {dash.khan_skills[sub_skill.skill_id].name}")
            print(f"        Exercises: {len(sub_skill.exercise_ids)}")
    
    print("\n✅ Khan hierarchy integration working!")
    
except Exception as e:
    print(f"  ✗ Failed to initialize DASH: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test with different region (India)
print("\n5. Testing DASH with India region...")
try:
    dash_india = DASHSystem(
        use_mongodb=True,
        use_khan_hierarchy=True,
        region="IN",
        subject="Math"
    )
    
    print(f"  ✓ DASH India initialized")
    print(f"  ✓ Khan Skills: {len(dash_india.khan_skills)}")
    print(f"  ✓ Questions: {len(dash_india.question_index)}")
    
    if dash_india.khan_skills:
        sample_skill = list(dash_india.khan_skills.values())[0]
        print(f"  ✓ Sample: {sample_skill.name} (Region: {sample_skill.region})")
    
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Test 6: Compare with legacy mode
print("\n6. Testing legacy mode (generated_skills)...")
try:
    dash_legacy = DASHSystem(
        use_mongodb=True,
        use_khan_hierarchy=False
    )
    
    print(f"  ✓ Legacy mode initialized")
    print(f"  ✓ Skills: {len(dash_legacy.skills)}")
    print(f"  ✓ Questions: {len(dash_legacy.question_index)}")
    
except Exception as e:
    print(f"  ✗ Failed: {e}")

print("\n" + "=" * 70)
print("All Tests Complete!")
print("=" * 70)

print("\n📊 Summary:")
print(f"  Khan Hierarchy Mode:")
print(f"    - Skills (US Math): {len(dash.khan_skills)}")
print(f"    - Sub-skills: {len(dash.khan_sub_skills)}")
print(f"    - Questions: {len(dash.question_index)}")
print(f"  Legacy Mode:")
print(f"    - Skills: {len(dash_legacy.skills)}")
print(f"    - Questions: {len(dash_legacy.question_index)}")
