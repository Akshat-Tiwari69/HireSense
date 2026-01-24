import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'elite_hire.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Update pending to Applied
c.execute("UPDATE candidates SET status='Applied' WHERE status='pending'")
conn.commit()

# Show all candidates
c.execute("SELECT id, name, email, status FROM candidates")
rows = c.fetchall()
print("Updated candidates:")
for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Status: {row[3]}")

conn.close()
