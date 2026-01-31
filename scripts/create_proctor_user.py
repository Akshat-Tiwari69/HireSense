#!/usr/bin/env python3
"""
Create Proctor User Script
Generates a proctor user with bcrypt hashed password
Run this script to create a proctor account
"""

import bcrypt
import sys

def generate_password_hash(password):
    """Generate bcrypt hash for password"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_sql_insert(email, password, name):
    """Generate SQL INSERT statement"""
    password_hash = generate_password_hash(password)
    
    sql = f"""
-- Insert proctor user
INSERT INTO users (email, password_hash, role, name, created_at, updated_at)
VALUES (
    '{email}',
    '{password_hash}',
    'proctor',
    '{name}',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE 
SET 
    role = 'proctor',
    password_hash = EXCLUDED.password_hash,
    name = EXCLUDED.name,
    updated_at = CURRENT_TIMESTAMP;

-- Verify
SELECT id, email, role, name FROM users WHERE email = '{email}';
"""
    return sql

if __name__ == "__main__":
    print("=" * 70)
    print("HireSense - Create Proctor User")
    print("=" * 70)
    
    # Default values
    default_email = "proctor@hiresense.com"
    default_password = "Proctor@123"
    default_name = "Proctoring Admin"
    
    # Interactive mode if no arguments
    if len(sys.argv) == 1:
        print("\nUsing default credentials:")
        print(f"Email: {default_email}")
        print(f"Password: {default_password}")
        print(f"Name: {default_name}")
        print("\nTo use custom credentials, run:")
        print(f"  python {sys.argv[0]} <email> <password> <name>")
        print()
        
        response = input("Continue with defaults? (y/n): ").lower()
        if response != 'y':
            print("Cancelled.")
            sys.exit(0)
        
        email = default_email
        password = default_password
        name = default_name
    
    # Command line arguments
    elif len(sys.argv) == 4:
        email = sys.argv[1]
        password = sys.argv[2]
        name = sys.argv[3]
    else:
        print("Usage:")
        print(f"  {sys.argv[0]}                              # Use defaults")
        print(f"  {sys.argv[0]} <email> <password> <name>    # Custom values")
        print()
        print("Example:")
        print(f"  {sys.argv[0]} proctor@company.com MyPass123 'Senior Proctor'")
        sys.exit(1)
    
    # Generate SQL
    print("\n" + "=" * 70)
    print("Generated SQL:")
    print("=" * 70)
    sql = create_sql_insert(email, password, name)
    print(sql)
    
    print("\n" + "=" * 70)
    print("Login Credentials:")
    print("=" * 70)
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Dashboard: /proctor")
    print("\n⚠️  IMPORTANT: Change the password after first login!")
    print("=" * 70)
    
    # Save to file
    output_file = f"create_proctor_{email.split('@')[0]}.sql"
    with open(output_file, 'w') as f:
        f.write(sql)
    
    print(f"\n✅ SQL saved to: {output_file}")
    print("\nTo execute on PostgreSQL:")
    print(f"  psql -h your-host -U your-user -d your-db -f {output_file}")
    print("  OR copy-paste the SQL into your database client")
