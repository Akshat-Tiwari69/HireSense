"""
Test script for authentication endpoints
Run this after starting the Flask server to test the auth functionality
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_registration():
    """Test user registration"""
    print("\n=== Testing Registration ===")
    
    # Test successful registration
    data = {
        "email": "interviewer1@example.com",
        "password": "secure123456",
        "role": "interviewer",
        "name": "Jane Doe"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test duplicate email
    print("\n--- Testing Duplicate Email ---")
    response = requests.post(f"{BASE_URL}/auth/register", json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test invalid email
    print("\n--- Testing Invalid Email ---")
    data_invalid = {
        "email": "not-an-email",
        "password": "secure123456",
        "role": "interviewer",
        "name": "Jane Doe"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data_invalid)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test short password
    print("\n--- Testing Short Password ---")
    data_short_pwd = {
        "email": "test2@example.com",
        "password": "short",
        "role": "interviewer",
        "name": "Jane Doe"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=data_short_pwd)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_login():
    """Test user login"""
    print("\n\n=== Testing Login ===")
    
    # Test successful login
    data = {
        "email": "interviewer1@example.com",
        "password": "secure123456"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=data)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if response.status_code == 200:
        token = result['data']['access_token']
        print(f"\nAccess Token (first 50 chars): {token[:50]}...")
        return token
    
    # Test invalid credentials
    print("\n--- Testing Invalid Credentials ---")
    data_wrong = {
        "email": "interviewer1@example.com",
        "password": "wrongpassword"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=data_wrong)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return None


def test_protected_routes(token):
    """Test protected routes with JWT token"""
    print("\n\n=== Testing Protected Routes ===")
    
    if not token:
        print("No token available, skipping protected route tests")
        return
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Test /me endpoint
    print("\n--- Testing GET /auth/me ---")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test /verify endpoint
    print("\n--- Testing GET /auth/verify ---")
    response = requests.get(f"{BASE_URL}/auth/verify", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test without token
    print("\n--- Testing Without Token ---")
    response = requests.get(f"{BASE_URL}/auth/me")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test with invalid token
    print("\n--- Testing With Invalid Token ---")
    invalid_headers = {
        "Authorization": "Bearer invalid.token.here"
    }
    response = requests.get(f"{BASE_URL}/auth/me", headers=invalid_headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Authentication API Test Suite")
    print("=" * 60)
    print("\nMake sure the Flask server is running on http://localhost:5000")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()
    
    try:
        # Test registration
        test_registration()
        
        # Test login and get token
        token = test_login()
        
        # Test protected routes
        test_protected_routes(token)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server.")
        print("Make sure the Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"\nError occurred: {str(e)}")


if __name__ == "__main__":
    main()
