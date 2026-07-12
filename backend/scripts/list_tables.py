"""
Operational script to list all PostgreSQL tables.
"""
import os
from _bootstrap import add_backend_to_path

add_backend_to_path()
from db_config import get_connection

conn = get_connection()
conn.set_session(autocommit=True)
cursor = conn.cursor()

# Get all tables
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

tables = cursor.fetchall()
print("📋 TABLES IN DATABASE:")
print("=" * 50)
for table in tables:
    print(f"  • {table[0]}")

if not tables:
    print("  ⚠️ NO TABLES FOUND - Database needs initialization!")

conn.close()
