"""
Quick script to verify database data integrity
"""
import os
import sys
from db_config import get_connection

def check_database():
    print("🔍 Checking database connection and data...")
    print("=" * 80)
    
    try:
        conn = get_connection()
        conn.set_session(autocommit=True)  # Enable autocommit for Postgres
        cursor = conn.cursor()
        
        # Check which database we're using
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            print(f"✅ Connected to PostgreSQL")
            print(f"   URL: {database_url[:50]}...")
        else:
            print(f"✅ Connected to SQLite")
            print(f"   Path: {os.path.join(os.path.dirname(__file__), '..', 'database', 'elite_hire.db')}")
        
        print("\n" + "=" * 80)
        print("📊 TABLE COUNTS:")
        print("=" * 80)
        
        # Check users table
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        print(f"👥 Users: {users_count}")
        
        # Check candidates table
        cursor.execute("SELECT COUNT(*) FROM candidates")
        candidates_count = cursor.fetchone()[0]
        print(f"📝 Candidates: {candidates_count}")
        
        # Check assessments table
        cursor.execute("SELECT COUNT(*) FROM assessments")
        assessments_count = cursor.fetchone()[0]
        print(f"📋 Assessments: {assessments_count}")
        
        # Check jobs table
        try:
            cursor.execute("SELECT COUNT(*) FROM jobs")
            jobs_count = cursor.fetchone()[0]
            print(f"💼 Jobs: {jobs_count}")
        except:
            print(f"💼 Jobs: Table not found (skip)")
        
        print("\n" + "=" * 80)
        print("👥 USER DETAILS:")
        print("=" * 80)
        
        # Show user details
        cursor.execute("SELECT id, email, name, role FROM users")
        users = cursor.fetchall()
        
        if users:
            for user in users:
                user_id, email, name, role = user
                print(f"  • ID: {user_id} | Email: {email} | Name: {name} | Role: {role}")
        else:
            print("  ⚠️ No users found in database!")
        
        print("\n" + "=" * 80)
        print("💼 JOBS:")
        print("=" * 80)
        
        try:
            cursor.execute("SELECT id, title, interviewer_id FROM jobs LIMIT 5")
            jobs = cursor.fetchall()
            
            if jobs:
                for job in jobs:
                    print(f"  • Job ID: {job[0]} | Title: {job[1]} | Interviewer: {job[2]}")
            else:
                print("  ℹ️ No jobs found")
        except:
            print("  ⚠️ Jobs table not found (skip)")
        
        print("\n" + "=" * 80)
        print("✅ DATABASE CHECK COMPLETE!")
        print("=" * 80)
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_database()
