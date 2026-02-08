"""
Request Logging Middleware for Flask
Logs all API requests with timing, status, and user info
"""

import logging
import time
from datetime import datetime
from functools import wraps
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/requests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('request_logger')


def log_request(f):
    """Decorator to log API requests with timing and user info"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Start timing
        start_time = time.time()
        
        # Get user info if authenticated
        user_id = None
        import contextlib
        with contextlib.suppress(Exception):
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        
        # Execute the route function
        response = f(*args, **kwargs)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Get status code
        status_code = response[1] if isinstance(response, tuple) else 200
        
        # Log the request
        logger.info(
            f"{request.method} {request.path} | "
            f"Status: {status_code} | "
            f"Duration: {duration:.3f}s | "
            f"User: {user_id or 'anonymous'} | "
            f"IP: {request.remote_addr}"
        )
        
        return response
    
    return decorated_function


def init_request_logging(app):
    """Initialize request logging for Flask app"""
    
    @app.before_request
    def before_request():
        """Store request start time"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Log all requests after completion"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Get user info if available
            user_id = None
            import contextlib
            with contextlib.suppress(Exception):
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
            
            # Log the request
            logger.info(
                f"{request.method} {request.path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s | "
                f"User: {user_id or 'anonymous'} | "
                f"IP: {request.remote_addr}"
            )
        
        return response
    
    logger.info("[OK] Request logging initialized")
    return app
