"""
Rate Limiting Configuration for Flask Backend
Prevents API abuse and ensures fair usage
"""

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def _limit_if_present(limiter, app, endpoint_name, limit):
    """Attach a rate limit to endpoint if it exists."""
    endpoint = app.view_functions.get(endpoint_name)
    if endpoint is not None:
        limiter.limit(limit)(endpoint)


def init_rate_limiting(app):
    """Initialize rate limiting for the Flask app"""

    # Use Redis if available so limits persist across restarts and workers.
    # Fall back to in-process memory for single-process dev environments.
    redis_url = os.environ.get('REDIS_URL')
    storage_uri = redis_url if redis_url else "memory://"
    if redis_url:
        app.logger.info(f"[RATE LIMIT] Using Redis storage: {redis_url.split('@')[-1]}")
    else:
        app.logger.warning("[RATE LIMIT] No REDIS_URL set — using in-memory storage (limits reset on restart)")

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=storage_uri,
    )

    # Auth endpoints - stricter limits
    _limit_if_present(limiter, app, 'auth.login', "10 per minute")
    _limit_if_present(limiter, app, 'auth.register', "5 per minute")

    # File upload - limited
    _limit_if_present(limiter, app, 'resume.upload_resume', "10 per hour")

    return limiter
