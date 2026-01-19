"""
Database Initialization Module
Creation of all database tables
"""

import os
import sqlite3
from db_config import get_connection, DB_PATH


def init_database():
    """
    Initializing the database by reading and executing schema.sql
    Creates all tables defined in the schema.
    """
    try:
        # Getting the database connection
        conn = get_connection()
        if conn is None:
            print("❌ Failed to connect to database")
            return False
        
        cursor = conn.cursor()
        
        # Read schema.sql file (located in database directory)
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
        
        if not os.path.exists(schema_path):
            print(f"❌ Schema file not found at {schema_path}")
            return False
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema SQL
        cursor.executescript(schema_sql)
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        conn.close()
        
        print("✅ Database initialized successfully!")
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print(f"Initializing database at: {DB_PATH}")
    success = init_database()
    
    if success:
        print("\n✨ Database is ready to use!")
    else:
        print("\n⚠️  Database initialization failed.")
