"""
Authentication Module
Handles user registration, login, and JWT token management
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity,
    get_jwt
)
import re
import logging
import time
from werkzeug.security import generate_password_hash, check_password_hash
from db_helpers import create_user, get_user_by_email, get_user_by_id

# Setup logger
logger = logging.getLogger(__name__)

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Email validation pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'

# Valid roles
VALID_ROLES = ['interviewer', 'admin', 'proctor']


def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    return re.match(EMAIL_PATTERN, email) is not None


def hash_password(password):
    """Hash a password using bcrypt"""
    logger.info(f"🔐 Hashing password (length: {len(password)} chars)")
    hashed = generate_password_hash(password)
    logger.info(f"✅ Password hashed successfully")
    return hashed


def verify_password(password, password_hash):
    """Verify a password against its hash"""
    logger.info("🔓 Verifying password...")
    try:
        result = check_password_hash(password_hash, password)
        if result:
            logger.info("✅ Password verified successfully")
        else:
            logger.warning("❌ Password verification failed")
        return result
    except Exception as e:
        logger.warning("❌ Password verification error (invalid/legacy hash): %s", e)
        return False


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user (interviewer or admin)
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword",
        "role": "interviewer",
        "name": "John Doe"
    }
    
    Returns:
        201: User created successfully with user_id
        400: Validation error or missing fields
        409: Email already exists
        500: Server error
    """
    try:
        logger.info("="*80)
        logger.info("📝 USER REGISTRATION REQUEST")
        logger.info("="*80)
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'role', 'name']
        for field in required_fields:
            if field not in data or not data[field]:
                logger.error(f"❌ Missing required field: {field}")
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        role = data['role'].strip().lower()
        name = data['name'].strip()
        
        logger.info(f"👤 Registration attempt - Email: {email}, Role: {role}, Name: {name}")
        
        # Validate email format
        if not validate_email(email):
            logger.error(f"❌ Invalid email format: {email}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid email format'
            }), 400
        
        # Validate password length
        if len(password) < 8:
            logger.error("❌ Password too short")
            return jsonify({
                'status': 'error',
                'message': 'Password must be at least 8 characters long'
            }), 400
        
        # Validate role
        if role not in VALID_ROLES:
            logger.error(f"❌ Invalid role: {role}")
            return jsonify({
                'status': 'error',
                'message': f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}'
            }), 400
        
        # Validate name
        if len(name) < 2:
            logger.error("❌ Name too short")
            return jsonify({
                'status': 'error',
                'message': 'Name must be at least 2 characters long'
            }), 400
        
        # Check if user already exists
        logger.info(f"🔍 Checking if user already exists: {email}")
        existing_user = get_user_by_email(email)
        if existing_user:
            logger.warning(f"⚠️ User already exists: {email}")
            return jsonify({
                'status': 'error',
                'message': 'User with this email already exists'
            }), 409
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        logger.info(f"💾 Creating user in database...")
        user_id = create_user(email, password_hash, role, name)
        
        logger.info(f"✅ User registered successfully - ID: {user_id}")
        logger.info("="*80)
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user_id': user_id,
                'email': email,
                'role': role,
                'name': name
            }
        }), 201
        
    except Exception as e:
        logger.exception(f"❌ Registration failed: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Registration failed: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    
    Request body:
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    
    Returns:
        200: Login successful with JWT token
        400: Missing fields
        401: Invalid credentials
        500: Server error
    """
    try:
        logger.info("="*80)
        logger.info("🔑 USER LOGIN REQUEST")
        logger.info("="*80)
        
        # Get request data
        data = request.get_json()
        
        # Validate required fields
        if not data or 'email' not in data or 'password' not in data:
            logger.error("❌ Missing email or password")
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        email = data['email'].strip().lower()
        password = data['password']
        
        logger.info(f"👤 Login attempt for: {email}")
        
        # Get user from database
        logger.info(f"🔍 Looking up user in database...")
        user_lookup_start = time.perf_counter()
        user = get_user_by_email(email)
        logger.info("🔍 User lookup finished in %.3fs (found=%s)", time.perf_counter() - user_lookup_start, bool(user))
        
        if not user:
            logger.warning(f"⚠️ User not found: {email}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
        
        logger.info(f"✅ User found - Role: {user.get('role')}")
        
        # Verify password
        try:
            verify_start = time.perf_counter()
            is_valid = verify_password(password, user['password_hash'])
            logger.info("🔒 Password verification finished in %.3fs (ok=%s)", time.perf_counter() - verify_start, is_valid)
        except Exception:
            logger.exception("❌ Password verification error")
            return jsonify({'status': 'error', 'message': 'Authentication failed'}), 500

        if not is_valid:
            logger.warning(f"⚠️ Invalid password for: {email}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
        
        # Create JWT token with user info
        logger.info("🎫 Creating JWT access token...")
        additional_claims = {
            'role': user['role'],
            'name': user['name']
        }
        
        access_token = create_access_token(
            identity=str(user['id']),  # Convert to string - JWT requires string identity
            additional_claims=additional_claims
        )
        
        logger.info(f"✅ JWT token created successfully")
        logger.info(f"✅ LOGIN SUCCESSFUL - User: {email}, Role: {user['role']}")
        logger.info("="*80)
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'role': user['role'],
                    'name': user['name']
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Login failed: {str(e)}'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user information
    Protected route - requires valid JWT token
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns:
        200: User information
        401: Invalid or missing token
        404: User not found
        500: Server error
    """
    try:
        # Get user ID from JWT
        user_id = get_jwt_identity()
        
        # Get additional claims
        claims = get_jwt()
        
        # Get user from database
        user = get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'name': user['name'],
                'created_at': user['created_at']
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get user info: {str(e)}'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify JWT token validity
    Protected route - requires valid JWT token
    
    Headers:
        Authorization: Bearer <jwt_token>
    
    Returns:
        200: Token is valid
        401: Invalid or expired token
    """
    try:
        user_id = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            'status': 'success',
            'message': 'Token is valid',
            'data': {
                'user_id': user_id,
                'role': claims.get('role'),
                'name': claims.get('name')
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Token verification failed: {str(e)}'
        }), 401
