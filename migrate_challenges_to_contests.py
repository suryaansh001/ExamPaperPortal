#!/usr/bin/env python3
"""
Migration script to convert legacy DailyChallenge data to new DailyContest + ContestQuestion format.
This script is idempotent and can be run multiple times safely.
"""

from main import SessionLocal, DailyChallenge, DailyContest, ContestQuestion, Course
from datetime import datetime
from sqlalchemy.exc import IntegrityError

def migrate_challenges_to_contests():
    """
    Migrate all DailyChallenge records to DailyContest + ContestQuestion format.
    Each challenge becomes a contest with a single question.
    Code snippet is converted to JSON format: {"python": code_snippet}
    """
    db = SessionLocal()
    
    try:
        # Get all legacy challenges
        challenges = db.query(DailyChallenge).all()
        
        if not challenges:
            print("✅ No legacy challenges found. Database is already using new format.")
            return
        
        print(f"📊 Found {len(challenges)} legacy challenges to migrate")
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for challenge in challenges:
            try:
                # Check if contest already exists for this date
                existing_contest = db.query(DailyContest).filter(
                    DailyContest.date == challenge.date
                ).first()
                
                if existing_contest:
                    print(f"⏭️  Skipping {challenge.date} - contest already exists")
                    skipped_count += 1
                    continue
                
                # Create new contest
                contest = DailyContest(
                    course_id=challenge.course_id,
                    date=challenge.date,
                    title=f"{challenge.date} Challenge",
                    description=None,
                    created_at=challenge.created_at or datetime.utcnow()
                )
                db.add(contest)
                db.flush()  # Get contest ID
                
                # Create question with Python code in JSON format
                question = ContestQuestion(
                    contest_id=contest.id,
                    order=1,
                    title=challenge.question[:100] if len(challenge.question) > 100 else challenge.question,
                    question=challenge.question,
                    code_snippets={"python": challenge.code_snippet},  # Convert to JSON
                    explanation=challenge.explanation,
                    media_link=challenge.media_link,
                    created_at=challenge.created_at or datetime.utcnow()
                )
                db.add(question)
                
                migrated_count += 1
                print(f"✅ Migrated: {challenge.date} (ID: {challenge.id} → Contest ID: {contest.id})")
                
            except IntegrityError as e:
                db.rollback()
                print(f"❌ Error migrating {challenge.date}: {e}")
                error_count += 1
                continue
            except Exception as e:
                db.rollback()
                print(f"❌ Unexpected error migrating {challenge.date}: {e}")
                error_count += 1
                continue
        
        # Commit all changes
        db.commit()
        
        print("\n" + "="*60)
        print("📈 Migration Summary:")
        print(f"   ✅ Migrated: {migrated_count}")
        print(f"   ⏭️  Skipped: {skipped_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📊 Total: {len(challenges)}")
        print("="*60)
        
        if migrated_count > 0:
            print("\n💡 Note: Legacy DailyChallenge records are preserved for rollback.")
            print("   To remove them, run: DELETE FROM daily_challenges;")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()

def verify_migration():
    """Verify that migration was successful"""
    db = SessionLocal()
    
    try:
        legacy_count = db.query(DailyChallenge).count()
        contest_count = db.query(DailyContest).count()
        question_count = db.query(ContestQuestion).count()
        
        print("\n" + "="*60)
        print("🔍 Database Status:")
        print(f"   Legacy Challenges: {legacy_count}")
        print(f"   New Contests: {contest_count}")
        print(f"   Contest Questions: {question_count}")
        print("="*60)
        
        if contest_count > 0:
            print("\n📋 Sample Contest:")
            sample_contest = db.query(DailyContest).first()
            print(f"   Date: {sample_contest.date}")
            print(f"   Course ID: {sample_contest.course_id}")
            print(f"   Questions: {len(sample_contest.questions)}")
            
            if sample_contest.questions:
                sample_question = sample_contest.questions[0]
                print(f"\n   First Question:")
                print(f"     Title: {sample_question.title}")
                print(f"     Languages: {list(sample_question.code_snippets.keys())}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Starting DailyChallenge → DailyContest migration...\n")
    migrate_challenges_to_contests()
    verify_migration()
    print("\n✅ Migration complete!")
