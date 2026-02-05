#!/usr/bin/env python3
"""
Direct database inspection script
"""
import psycopg2
from urllib.parse import unquote

# Supabase database URL (decoded)
DATABASE_URL = "postgresql://postgres:%3f-Sr%24t6dmhG64%26%2b@db.ezykqdzqholcporflgmq.supabase.co:5432/postgres"

# Decode URL-encoded characters
decoded_url = unquote(DATABASE_URL)
print(f"Connecting to: {decoded_url}\n")

try:
    conn = psycopg2.connect(decoded_url)
    cursor = conn.cursor()
    
    # Get all tables
    print("=" * 80)
    print("TABLES IN DATABASE")
    print("=" * 80)
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n" + "=" * 80)
    print("TABLE STRUCTURES")
    print("=" * 80)
    
    # Get info about each table
    for table in tables:
        table_name = table[0]
        print(f"\n📋 {table_name.upper()}")
        print("-" * 80)
        
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        for col in columns:
            nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col[3]}" if col[3] else ""
            print(f"  {col[0]:25} {col[1]:20} {nullable:10} {default}")
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\n  📊 Rows: {count}")
    
    print("\n" + "=" * 80)
    print("ASSESSMENT DATA CHECK")
    print("=" * 80)
    
    # Check scheduled_assessments
    cursor.execute("""
        SELECT id, candidate_id, scheduled_time, status, access_token, is_streaming
        FROM scheduled_assessments
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print("\n✅ Scheduled Assessments (first 5):")
        for row in rows:
            token_preview = row[4][:20] + '...' if row[4] else 'None'
            print(f"  ID: {row[0]}, Candidate: {row[1]}, Status: {row[3]}, Token: {token_preview}, Streaming: {row[5]}")
    else:
        print("\n⚠️  No scheduled assessments found")
    
    # Check assessments
    cursor.execute("""
        SELECT id, candidate_id, status, technical_score, psychometric_score, overall_score
        FROM assessments
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print("\n✅ Assessments (first 5):")
        for row in rows:
            print(f"  ID: {row[0]}, Candidate: {row[1]}, Status: {row[2]}, Tech: {row[3]}, Psycho: {row[4]}, Overall: {row[5]}")
    else:
        print("\n⚠️  No assessments found")
    
    # Check candidates
    cursor.execute("""
        SELECT id, name, email, status
        FROM candidates
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print("\n✅ Candidates (first 5):")
        for row in rows:
            print(f"  ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Status: {row[3]}")
    else:
        print("\n⚠️  No candidates found")
    
    # Check for tokens and their status
    cursor.execute("""
        SELECT id, candidate_id, status, access_token, is_streaming
        FROM scheduled_assessments
        WHERE access_token IS NOT NULL
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print("\n✅ Assessments with tokens:")
        for row in rows:
            token_preview = row[3][:20] + '...' if row[3] else 'None'
            print(f"  ID: {row[0]}, Candidate ID: {row[1]}, Status: {row[2]}, Token: {token_preview}, Streaming: {row[4]}")
    else:
        print(f"\n❌ Token '{token[:20]}...' NOT found in database")
    
    conn.close()
    print("\n" + "=" * 80)
    print("Database inspection complete!")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
