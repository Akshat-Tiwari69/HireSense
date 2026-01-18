"""
Database Configuration Module
Handles SQLite database connection setup and testing
"""

import sqlite3
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'elite_hire.db')

# Ensure database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection():
    """
    Get a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        # Enable foreign key support
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def test_connection():
    """
    Test the database connection.
    Prints success or failure message.
    """
    try:
        conn = get_connection()
        if conn is None:
            print("❌ Database connection failed!")
            return False
        
        # Try to execute a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        conn.close()
        print("✅ Database connected!")
        return True
    except sqlite3.Error as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run test when file is executed directly
    print(f"Database path: {DB_PATH}")
    test_connection()
