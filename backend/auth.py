"""
Authentication Module
Handles staff login and JWT token management. Staff accounts are created only
through the admin API.
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
from time import perf_counter
from functools import lru_cache
from werkzeug.security import generate_password_hash, check_password_hash
from user_db import (
    get_user_by_email,
    get_user_by_id,
    user_auth_version,
)

# Setup logger
logger = logging.getLogger(__name__)

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__)

# Email validation pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'

# Valid roles (expanded for RBAC)
VALID_ROLES = ['interviewer', 'admin', 'proctor', 'super_admin', 'sector_admin', 'recruiter']

# Cache compiled regex pattern for validation (avoids recompiling on each request)
_EMAIL_PATTERN_COMPILED = re.compile(EMAIL_PATTERN)
_DUMMY_PASSWORD_HASH = generate_password_hash("timing-only-nonexistent-account")
SLOW_LOGIN_SECONDS = 2.0


@lru_cache(maxsize=128)
def validate_email(email):
    """Validate email format with cached regex pattern"""
    if not email:
        return False
    return _EMAIL_PATTERN_COMPILED.match(email) is not None


def hash_password(password):
    """Hash a password using bcrypt"""
    hashed = generate_password_hash(password)
    return hashed


def verify_password(password, password_hash):
    """Verify a password hash and fail closed for malformed legacy values."""
    try:
        return check_password_hash(password_hash, password)
    except Exception as exc:
        logger.warning(
            "Password hash could not be verified (%s)",
            type(exc).__name__,
        )
        return False


def _record_login_timing(request_started, lookup_seconds, verify_seconds):
    total_seconds = perf_counter() - request_started
    if total_seconds >= SLOW_LOGIN_SECONDS:
        logger.warning(
            "[AUTH] Slow login request: total=%.3fs lookup=%.3fs verify=%.3fs",
            total_seconds,
            lookup_seconds,
            verify_seconds,
        )


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
    request_started = perf_counter()
    try:
        # Get request data
        data = request.get_json(silent=True)
        
        # Validate required fields
        if not isinstance(data, dict) or 'email' not in data or 'password' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
        
        if not isinstance(data['email'], str) or not isinstance(data['password'], str):
            return jsonify({
                'status': 'error',
                'message': 'Email and password must be strings'
            }), 400

        email = data['email'].strip().lower()
        password = data['password']
        if not email or not password or len(email) > 254 or len(password) > 128:
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 400
        
        # Get user from the user-domain data module.
        user_lookup_start = perf_counter()
        user = get_user_by_email(email)
        lookup_seconds = perf_counter() - user_lookup_start
        logger.debug("[AUTH] User lookup completed in %.3fs", lookup_seconds)
        
        # Always perform one password-hash check so unknown accounts and wrong
        # passwords have the same expensive code path and generic response.
        verify_start = perf_counter()
        password_hash = user.get('password_hash') if user else _DUMMY_PASSWORD_HASH
        is_valid = verify_password(password, password_hash)
        verify_seconds = perf_counter() - verify_start
        logger.debug("[AUTH] Password verification completed in %.3fs", verify_seconds)

        if not user or not is_valid:
            _record_login_timing(request_started, lookup_seconds, verify_seconds)
            logger.warning("[AUTH] Login rejected")
            return jsonify({
                'status': 'error',
                'message': 'Invalid email or password'
            }), 401
        
        # Create JWT token with user info (includes sector for RBAC)
        additional_claims = {
            'role': user['role'],
            'name': user['name'],
            'sector_id': user.get('sector_id'),
            'user_auth_version': user_auth_version(user),
        }
        
        access_token = create_access_token(
            identity=str(user['id']),  # Convert to string - JWT requires string identity
            additional_claims=additional_claims
        )

        _record_login_timing(request_started, lookup_seconds, verify_seconds)
        
        logger.info("[AUTH] Login succeeded for user %s with role %s", user['id'], user['role'])
        
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'access_token': access_token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'role': user['role'],
                    'name': user['name'],
                    'sector_id': user.get('sector_id')
                }
            }
        }), 200

    except Exception:
        logger.exception("[ERROR] Login failed")
        return jsonify({
            'status': 'error',
            'message': 'Login failed. Please try again later.'
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
                'sector_id': user.get('sector_id'),
                'created_at': user['created_at']
            }
        }), 200
        
    except Exception:
        logger.exception("[ERROR] Failed to get current user")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get user info'
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
        
    except Exception:
        logger.exception("[ERROR] Token verification failed")
        return jsonify({
            'status': 'error',
            'message': 'Token verification failed'
        }), 401
