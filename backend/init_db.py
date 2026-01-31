"""
Database Initialization Module
Creation of all database tables for PostgreSQL (Render production)
"""

import os
from werkzeug.security import generate_password_hash
from db_config import get_connection


def drop_all_tables():
    """
    Drop all tables from the PostgreSQL database.
    Useful for resetting/clearing the database completely.
    """
    try:
        conn = get_connection()
        if conn is None:
            print("[ERROR] Failed to connect to database")
            return False
        
        cursor = conn.cursor()
        
        print("\n[INFO] Dropping all existing tables...")
        
        # Get all table names from PostgreSQL
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        # Drop all tables
        for table in tables:
            print(f"   Dropping table: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        
        conn.commit()
        conn.close()
        
        if tables:
            print(f"[SUCCESS] Dropped {len(tables)} tables")
        else:
            print("[INFO] No tables found to drop")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error dropping tables: {e}")
        import traceback
        traceback.print_exc()
        return False


def init_database():
    """
    Initialize the PostgreSQL database by reading and executing schema_postgres.sql.
    Creates all tables defined in the schema.
    """
    try:
        # Get the database connection
        conn = get_connection()
        if conn is None:
            print("[ERROR] Failed to connect to database")
            return False
        
        print("[INFO] Connected to PostgreSQL database")
        
        cursor = conn.cursor()
        
        # Use PostgreSQL schema file
        schema_file = 'schema_postgres.sql'
        schema_path = os.path.join(os.path.dirname(__file__), schema_file)
        
        if not os.path.exists(schema_path):
            print(f"[ERROR] Schema file not found at {schema_path}")
            return False
        
        print(f"[INFO] Loading schema from: {schema_file}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # PostgreSQL: execute statements one by one
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
        for stmt in statements:
            try:
                cursor.execute(stmt)
            except Exception as stmt_error:
                print(f"[WARNING] Statement failed: {stmt[:50]}... Error: {stmt_error}")
        conn.commit()
        
        # Verify tables were created
        cursor.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        print("[SUCCESS] Database initialized successfully!")
        print(f"\n[INFO] Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   - {table}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def seed_default_users():
    """
    Seed default users (interviewer, admin, proctor) into the database.
    Skips if users already exist.
    """
    try:
        conn = get_connection()
        if conn is None:
            print("[ERROR] Failed to connect to database for seeding")
            return False
        
        cursor = conn.cursor()
        
        # Default users to create
        default_users = [
            {
                'email': 'interviewer@company.com',
                'password': 'password123',
                'role': 'interviewer',
                'name': 'Demo Interviewer'
            },
            {
                'email': 'admin@company.com',
                'password': 'admin123',
                'role': 'admin',
                'name': 'Demo Admin'
            },
            {
                'email': 'proctor@company.com',
                'password': 'proctor123',
                'role': 'proctor',
                'name': 'Demo Proctor'
            }
        ]
        
        print("\n[INFO] Seeding default users...")
        
        for user in default_users:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (user['email'],))
            
            if cursor.fetchone():
                print(f"   ⚠️  User {user['email']} already exists, skipping")
            else:
                hashed_pw = generate_password_hash(user['password'])
                cursor.execute(
                    "INSERT INTO users (email, password_hash, role, name) VALUES (%s, %s, %s, %s)",
                    (user['email'], hashed_pw, user['role'], user['name'])
                )
                conn.commit()
                print(f"   ✅ User {user['email']} ({user['role']}) created")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Error seeding users: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    db_url = os.environ.get('DATABASE_URL')
    print(f"🔄 Database Initialization (PostgreSQL)")
    
    if not db_url:
        print("[ERROR] DATABASE_URL environment variable is not set!")
        print("Set it with: export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
        exit(1)
    
    print(f"[INFO] Connecting to PostgreSQL...")
    
    # Step 1: Drop all existing tables
    print("\n" + "="*60)
    print("STEP 1: Clearing database")
    print("="*60)
    drop_success = drop_all_tables()
    
    if not drop_success:
        print("\n[WARNING] Drop operation had issues, continuing anyway...")
    
    # Step 2: Create new schema
    print("\n" + "="*60)
    print("STEP 2: Creating schema")
    print("="*60)
    schema_success = init_database()
    
    if schema_success:
        # Step 3: Seed default users
        print("\n" + "="*60)
        print("STEP 3: Seeding default users")
        print("="*60)
        seed_success = seed_default_users()
        
        if seed_success:
            print("\n" + "="*60)
            print("✅ [SUCCESS] Database fully reset and initialized!")
            print("="*60)
            print("\nDefault users created:")
            print("  - interviewer@company.com / password123 (interviewer)")
            print("  - admin@company.com / admin123 (admin)")
            print("  - proctor@company.com / proctor123 (proctor)")
        else:
            print("\n[WARNING] Database schema created but user seeding failed.")
    else:
        print("\n[ERROR] Database initialization failed.")
