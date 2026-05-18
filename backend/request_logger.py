"""
Request Logging Middleware for Flask
Logs all API requests with timing, status, and user info
"""

import logging
import time
import contextlib
from flask import request, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
import os

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/requests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('request_logger')


def init_request_logging(app):
    """Initialize request logging for Flask app"""

    @app.before_request
    def before_request():
        g.start_time = time.time()
        # Capture identity once, before the route runs, so after_request doesn't
        # need to re-parse the JWT (avoids double overhead and suppressed exceptions).
        g.request_user_id = None
        with contextlib.suppress(Exception):
            verify_jwt_in_request(optional=True)
            g.request_user_id = get_jwt_identity()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            user_id = getattr(g, 'request_user_id', None)
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
