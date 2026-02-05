"""
Database Reset Script
Resets all candidates to 'applied' status and clears all assessment data
"""

import psycopg2
from db_config import get_connection

def reset_database():
    """
    Reset database to clean slate:
    - Set all candidates to 'applied' status
    - Delete all assessments
    - Delete all answers (MCQ, coding, psychometric)
    - Delete all scheduled assessments
    - Delete all proctoring data
    - Reset sequences
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("🔄 Starting database reset...")
        
        # 1. Delete proctoring violations
        print("   Deleting proctoring violations...")
        cursor.execute("DELETE FROM proctoring_violations")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} proctoring violations")
        
        # 2. Delete proctoring events
        print("   Deleting proctoring events...")
        cursor.execute("DELETE FROM proctoring_events")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} proctoring events")
        
        # 3. Delete psychometric responses
        print("   Deleting psychometric responses...")
        cursor.execute("DELETE FROM psychometric_responses")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} psychometric responses")
        
        # 4. Delete coding submissions
        print("   Deleting coding submissions...")
        cursor.execute("DELETE FROM coding_submissions")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} coding submissions")
        
        # 5. Delete MCQ responses
        print("   Deleting MCQ responses...")
        cursor.execute("DELETE FROM mcq_responses")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} MCQ responses")
        
        # 6. Delete assessment questions (stored AI-generated questions)
        print("   Deleting assessment questions...")
        try:
            cursor.execute("DELETE FROM assessment_questions")
            deleted = cursor.rowcount
            print(f"   ✓ Deleted {deleted} assessment question sets")
        except Exception as e:
            print(f"   ⚠ Table assessment_questions does not exist, skipping...")
            conn.rollback()  # Rollback the failed transaction
            cursor = conn.cursor()  # Get a new cursor
        
        # 7. Delete assessments
        print("   Deleting assessments...")
        cursor.execute("DELETE FROM assessments")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} assessments")
        
        # 8. Delete scheduled assessments
        print("   Deleting scheduled assessments...")
        cursor.execute("DELETE FROM scheduled_assessments")
        deleted = cursor.rowcount
        print(f"   ✓ Deleted {deleted} scheduled assessments")
        
        # 9. Update all candidates to 'applied' status
        print("   Resetting candidate statuses to 'applied'...")
        cursor.execute("""
            UPDATE candidates 
            SET status = 'applied',
                updated_at = CURRENT_TIMESTAMP
        """)
        updated = cursor.rowcount
        print(f"   ✓ Reset {updated} candidates to 'applied' status")
        
        # 10. Reset auto-increment sequences
        print("   Resetting sequences...")
        sequences = [
            'assessments_id_seq',
            'scheduled_assessments_id_seq',
            'mcq_responses_id_seq',
            'coding_submissions_id_seq',
            'psychometric_responses_id_seq',
            'proctoring_events_id_seq',
            'proctoring_violations_id_seq',
            'assessment_questions_id_seq'
        ]
        
        for seq in sequences:
            try:
                cursor.execute(f"ALTER SEQUENCE IF EXISTS {seq} RESTART WITH 1")
                print(f"   ✓ Reset {seq}")
            except Exception as e:
                print(f"   ⚠ Could not reset {seq}: {e}")
        
        # Commit all changes
        conn.commit()
        print("\n✅ Database reset complete!")
        print("   All candidates are now 'applied' status")
        print("   All assessments and answers have been cleared")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM candidates")
        candidate_count = cursor.fetchone()[0]
        print(f"\n📊 Database Summary:")
        print(f"   Candidates: {candidate_count}")
        print(f"   Assessments: 0")
        print(f"   Scheduled Assessments: 0")
        print(f"   Answers: 0")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error during database reset: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE RESET SCRIPT")
    print("=" * 60)
    print("⚠️  WARNING: This will:")
    print("   - Reset ALL candidates to 'applied' status")
    print("   - DELETE all assessments")
    print("   - DELETE all answers (MCQ, coding, psychometric)")
    print("   - DELETE all scheduled assessments")
    print("   - DELETE all proctoring data")
    print("=" * 60)
    
    confirm = input("\nType 'RESET' to confirm: ")
    
    if confirm == "RESET":
        reset_database()
    else:
        print("\n❌ Reset cancelled")
