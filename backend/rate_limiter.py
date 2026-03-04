"""
Rate Limiting Configuration for Flask Backend
Prevents API abuse and ensures fair usage
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def _limit_if_present(limiter, app, endpoint_name, limit):
    """Attach a rate limit to endpoint if it exists."""
    endpoint = app.view_functions.get(endpoint_name)
    if endpoint is not None:
        limiter.limit(limit)(endpoint)


def init_rate_limiting(app):
    """Initialize rate limiting for the Flask app"""

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )

    # Auth endpoints - stricter limits
    _limit_if_present(limiter, app, 'auth.login', "10 per minute")
    _limit_if_present(limiter, app, 'auth.register', "5 per minute")

    # File upload - limited
    _limit_if_present(limiter, app, 'upload_resume', "10 per hour")

    return limiter
