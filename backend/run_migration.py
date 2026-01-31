"""
Migration Runner - Execute SQL migration files
"""
import os
import sys
from db_config import get_connection

def run_migration(migration_file):
    """Execute a migration SQL file"""
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    print(f"📁 Reading migration: {migration_file}")
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"🔌 Connecting to database...")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        print(f"🚀 Executing {len(statements)} SQL statements...")
        for i, statement in enumerate(statements, 1):
            print(f"   [{i}/{len(statements)}] {statement[:60]}...")
            cursor.execute(statement)
        
        conn.commit()
        print(f"✅ Migration completed successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        print("\nExample:")
        print("  python run_migration.py ../database/migrations/add_job_id_to_candidates.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    success = run_migration(migration_file)
    sys.exit(0 if success else 1)
