"""
Check which skill_prefix values exist in MongoDB perseus_questions collection
"""

import sys
import os
from collections import Counter

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mongodb_manager import mongo_db

def check_perseus_prefixes():
    """Check all unique skill_prefix values in Perseus collection"""
    
    print("\n" + "="*80)
    print("CHECKING PERSEUS QUESTION PREFIXES IN MONGODB")
    print("="*80)
    
    # Get all unique skill prefixes
    prefixes = mongo_db.perseus_questions.distinct("skill_prefix")
    prefixes_sorted = sorted(prefixes)
    
    print(f"\n📊 Total unique skill prefixes: {len(prefixes_sorted)}")
    print("\n🔍 All Skill Prefixes Available:")
    print("-" * 80)
    
    # Group by grade level (first digit)
    by_grade = {}
    for prefix in prefixes_sorted:
        first_digit = prefix.split('.')[0]
        if first_digit not in by_grade:
            by_grade[first_digit] = []
        by_grade[first_digit].append(prefix)
    
    # Display by grade
    for grade in sorted(by_grade.keys()):
        prefixes_list = by_grade[grade]
        count = mongo_db.perseus_questions.count_documents(
            {"skill_prefix": {"$regex": f"^{grade}\."}}
        )
        print(f"\nGrade Level {grade}:")
        print(f"  Prefixes: {', '.join(prefixes_list[:10])}")
        if len(prefixes_list) > 10:
            print(f"  ... and {len(prefixes_list) - 10} more")
        print(f"  Total questions: {count}")
    
    # Check specific prefixes DASH is trying to use
    print("\n" + "="*80)
    print("CHECKING DASH-REQUESTED PREFIXES")
    print("="*80)
    
    dash_mappings = {
        "fractions_intro": "3.1.1.1",
        "fractions_operations": "4.1.1.1",
        "decimals_intro": "4.1.2.1",
        "multiplication_tables": "2.1.6.1",
        "division_basic": "2.1.8.1",
    }
    
    for skill_name, prefix in dash_mappings.items():
        count = mongo_db.perseus_questions.count_documents({"skill_prefix": prefix})
        status = "✅" if count > 0 else "❌"
        print(f"{status} {skill_name:25} → {prefix:10} ({count} questions)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    check_perseus_prefixes()

