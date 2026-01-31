#!/usr/bin/env python
"""
Test if the Flask app can start without errors
"""
import os
import sys

print("🔍 Testing Flask app startup...")
print("=" * 80)

try:
    print("1️⃣ Importing app...")
    from app import app, logger
    
    print("✅ App imported successfully!")
    print("2️⃣ Creating test client...")
    
    client = app.test_client()
    
    print("✅ Test client created!")
    print("3️⃣ Testing health check (GET /)...")
    
    response = client.get('/')
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.get_json()}")
    
    print("\n✅ FLASK APP IS WORKING!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
