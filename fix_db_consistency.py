"""
Script to fix database consistency issues with generated questions
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, Document, Link
from typing import List
from datetime import datetime
from bson import ObjectId

class QuestionDocument(Document):
    question: dict
    source: str = 'khan'
    generated_count: int = 0
    generated: List[Link["GeneratedQuestionDocument"]] = []
    created_at: datetime = datetime.now()

    class Settings:
        name = 'questions'

class GeneratedQuestionDocument(Document):
    question: dict
    source: str = 'aitutor'
    human_approved: bool = False
    created_at: datetime = datetime.now()

    class Settings:
        name = 'questions-generated'

async def fix_database():
    print("Connecting to database...")
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['question_db']
    await init_beanie(database=db, document_models=[QuestionDocument, GeneratedQuestionDocument])

    print("\n" + "="*80)
    print("DATABASE CONSISTENCY CHECK AND FIX")
    print("="*80)

    # Get all source questions with generated_count > 0
    questions_with_generated = await QuestionDocument.find(
        QuestionDocument.generated_count > 0
    ).to_list()

    print(f"\nFound {len(questions_with_generated)} source questions with generated_count > 0")

    # Get all generated questions
    all_generated = await GeneratedQuestionDocument.find().to_list()
    all_generated_ids = {str(g.id) for g in all_generated}
    print(f"Found {len(all_generated)} actual generated questions in database")

    fixed_count = 0
    broken_count = 0

    for question in questions_with_generated:
        # Fetch all links
        await question.fetch_all_links()

        # Check which generated questions actually exist
        valid_generated = []
        for gen_link in question.generated:
            if isinstance(gen_link, Link):
                gen_id = str(gen_link.ref.id)
            else:
                gen_id = str(gen_link.id) if hasattr(gen_link, 'id') else str(gen_link.get('_id', ''))

            if gen_id in all_generated_ids:
                valid_generated.append(gen_link)
            else:
                broken_count += 1
                print(f"  ❌ Broken reference in question {question.id}: generated question {gen_id} doesn't exist")

        # Update if there's a mismatch
        actual_count = len(valid_generated)
        if actual_count != question.generated_count or len(valid_generated) != len(question.generated):
            print(f"  🔧 Fixing question {question.id}:")
            print(f"     Old generated_count: {question.generated_count}, Old array length: {len(question.generated)}")
            print(f"     New generated_count: {actual_count}, New array length: {len(valid_generated)}")

            question.generated = valid_generated
            question.generated_count = actual_count
            await question.save()
            fixed_count += 1

    print(f"\n" + "="*80)
    print(f"SUMMARY:")
    print(f"  - Fixed {fixed_count} source questions")
    print(f"  - Removed {broken_count} broken references")
    print("="*80)

    # Show final state
    print("\nFinal database state:")
    questions_with_generated = await QuestionDocument.find(
        QuestionDocument.generated_count > 0
    ).to_list()
    print(f"  - Source questions with generated_count > 0: {len(questions_with_generated)}")
    print(f"  - Total generated questions: {len(all_generated)}")

    if questions_with_generated:
        print("\nQuestions ready for validation:")
        for q in questions_with_generated[:5]:
            print(f"  - {q.id}: {q.generated_count} pending")

if __name__ == "__main__":
    asyncio.run(fix_database())
