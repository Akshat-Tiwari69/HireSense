# Authentication System Usage Guide

## Overview
The authentication system uses JWT (JSON Web Tokens) with bcrypt password hashing for secure user authentication.

## Installation

First, install the new dependencies:

```bash
cd backend
pip install -r requirements.txt
```

The following packages are now required:
- `flask-jwt-extended` - JWT token management
- `bcrypt` - Password hashing

## Configuration

### Environment Variables

The JWT secret key can be configured via environment variable:

```bash
# .env file (create in backend directory)
JWT_SECRET_KEY=your_super_secret_key_change_in_production
```

**Important:** 
- In development, it defaults to `dev-secret-key-change-in-production`
- **ALWAYS** change this to a strong random secret in production
- Token expiration is set to 24 hours

## API Endpoints

All authentication endpoints are prefixed with `/api/auth`:

### 1. Register User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "interviewer@example.com",
  "password": "secure123456",
  "role": "interviewer",
  "name": "Jane Doe"
}
```

**Roles:**
- `interviewer` - For recruiters/hiring managers
- `admin` - For system administrators

**Password Requirements:**
- Minimum 8 characters
- Automatically hashed with bcrypt before storage

### 2. Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "interviewer@example.com",
  "password": "secure123456"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "interviewer@example.com",
      "role": "interviewer",
      "name": "Jane Doe"
    }
  }
}
```

### 3. Get Current User (Protected)
```bash
GET /api/auth/me
Authorization: Bearer <your_jwt_token>
```

### 4. Verify Token (Protected)
```bash
GET /api/auth/verify
Authorization: Bearer <your_jwt_token>
```

## Testing

A comprehensive test script is provided:

```bash
# Make sure the Flask server is running first
python app.py

# In another terminal:
python test_auth.py
```

The test script will:
1. Test user registration (valid and invalid cases)
2. Test login (valid and invalid credentials)
3. Test protected routes (with and without tokens)

## Frontend Integration

### Storing the Token

After successful login, store the JWT token:

```javascript
// After successful login
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();

if (data.status === 'success') {
  // Store token in localStorage
  localStorage.setItem('token', data.data.access_token);
  localStorage.setItem('user', JSON.stringify(data.data.user));
}
```

### Using the Token

Include the token in subsequent API requests:

```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:5000/api/auth/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Logout

```javascript
// Simply remove the token
localStorage.removeItem('token');
localStorage.removeItem('user');
```

## Security Features

1. **Password Hashing:** Passwords are hashed using bcrypt with automatic salt generation
2. **JWT Claims:** Tokens include user role and name for authorization
3. **Token Expiration:** Tokens expire after 24 hours
4. **Email Validation:** Server-side email format validation
5. **Role Validation:** Only specific roles are allowed
6. **Protected Routes:** Use `@jwt_required()` decorator for protected endpoints

## Creating Protected Endpoints

To create a new protected endpoint in other modules:

```python
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

@app.route('/api/interviewer/dashboard', methods=['GET'])
@jwt_required()
def interviewer_dashboard():
    # Get user ID from token
    user_id = get_jwt_identity()
    
    # Get additional claims (role, name)
    claims = get_jwt()
    user_role = claims.get('role')
    
    # Check if user has the right role
    if user_role != 'interviewer':
        return jsonify({
            'status': 'error',
            'message': 'Access denied'
        }), 403
    
    # Your endpoint logic here
    return jsonify({
        'status': 'success',
        'data': {...}
    })
```

## Database Schema

The authentication system uses the `users` table created by Prashanth:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Helper functions used:
- `create_user(email, password_hash, role, name)`
- `get_user_by_email(email)`
- `get_user_by_id(user_id)`

## Error Handling

The API returns standard error responses:

```json
{
  "status": "error",
  "message": "Error description here"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created (successful registration)
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid credentials or token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `409` - Conflict (email already exists)
- `500` - Server error

## Next Steps for Frontend (Shaivi)

1. **Create Login Page** (Task S4)
   - Use the `/api/auth/login` endpoint
   - Store JWT token in localStorage
   - Redirect to dashboard on success

2. **Create Auth Context** (Task S5)
   - Manage authentication state globally
   - Provide login/logout functions
   - Check token validity on app load

3. **Create Protected Routes** (Task S5)
   - Wrap protected pages with authentication check
   - Redirect to login if not authenticated
   - Check user role for role-based pages

4. **Update API Service** 
   - Add JWT token to all API requests automatically
   - Handle 401 errors (token expired) → redirect to login

## Troubleshooting

### "Module not found" errors
```bash
pip install flask-jwt-extended bcrypt
```

### Token expired errors
- Tokens expire after 24 hours
- User needs to login again
- Consider implementing refresh tokens for production

### CORS errors from frontend
- CORS is already enabled in app.py
- Make sure to include credentials in fetch requests if needed

## Production Considerations

Before deploying to production:

1. **Change JWT Secret:**
   ```bash
   JWT_SECRET_KEY=$(openssl rand -base64 32)
   ```

2. **Use HTTPS:** JWT tokens should only be transmitted over HTTPS

3. **Implement Refresh Tokens:** For better UX, implement token refresh mechanism

4. **Add Rate Limiting:** Prevent brute force attacks on login endpoint

5. **Consider Token Blacklist:** For logout functionality, implement token blacklist

6. **Database:** Use PostgreSQL or MySQL instead of SQLite

7. **Password Policy:** Enforce stronger password requirements if needed

---

**Created:** January 21, 2026  
**Task:** A5 - JWT Authentication  
**Author:** Akshat
