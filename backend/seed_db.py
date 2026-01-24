from db_config import get_connection
from werkzeug.security import generate_password_hash
import sqlite3

def seed_users():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        email = "interviewer@company.com"
        password = "password123"
        hashed_pw = generate_password_hash(password)
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"User {email} already exists.")
        else:
            cursor.execute(
                "INSERT INTO users (email, password_hash, role, name) VALUES (?, ?, ?, ?)",
                (email, hashed_pw, 'interviewer', 'Interviewer Name')
            )
            conn.commit()
            print(f"User {email} created successfully.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error seeding users: {e}")

if __name__ == "__main__":
    seed_users()
