"""
Seed default users into the database
Run this script to create initial interviewer and admin accounts
"""

import sqlite3
import os


def hash_password_simple(password):
    """Simple hash using SHA256 - for development only"""
    import hashlib
    # Note: In production, use bcrypt from auth.py
    # This is a workaround to avoid importing flask dependencies
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_path():
    """Get the database path"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(backend_dir, '..', 'database', 'elite_hire.db')
    return os.path.normpath(db_path)


def seed_default_users():
    """Create default interviewer and admin users"""
    
    print("="*80)
    print("🌱 SEEDING DEFAULT USERS")
    print("="*80)
    
    db_path = get_db_path()
    print(f"📁 Database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        print("   Run init_db.py first to create the database")
        return
    
    # Note: We'll use requests to call the /api/auth/register endpoint instead
    # This ensures we use the proper bcrypt hashing
    print("\n⚠️  To create users properly with bcrypt, use the API endpoint:")
    print()
    print("Option 1: Using curl/PowerShell:")
    print('-' * 80)
    print('Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:5000/api/auth/register" `')
    print('  -ContentType "application/json" `')
    print('  -Body \'{"email": "interviewer@cygnusa.com", "password": "password123", "role": "interviewer", "name": "Demo Interviewer"}\'')
    print()
    print('Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:5000/api/auth/register" `')
    print('  -ContentType "application/json" `')
    print('  -Body \'{"email": "admin@cygnusa.com", "password": "admin123", "role": "admin", "name": "Demo Admin"}\'')
    print('-' * 80)
    print()
    print("Option 2: Direct SQL insert (for emergency only):")
    print("   Run: python -c \"from auth import hash_password; print(hash_password('password123'))\"")
    print("   Then insert manually into database")
    print()
    print("="*80)


if __name__ == "__main__":
    seed_default_users()


if __name__ == "__main__":
    seed_default_users()
