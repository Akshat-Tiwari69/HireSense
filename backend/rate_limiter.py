"""
Rate Limiting Configuration for Flask Backend
Prevents API abuse and ensures fair usage
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def init_rate_limiting(app):
    """Initialize rate limiting for the Flask app"""
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    
    # Auth endpoints - stricter limits
    limiter.limit("10 per minute")(app.view_functions.get('auth.login'))
    limiter.limit("5 per minute")(app.view_functions.get('auth.register'))
    
    # File upload - limited
    limiter.limit("10 per hour")(app.view_functions.get('upload_resume'))
    
    return limiter
