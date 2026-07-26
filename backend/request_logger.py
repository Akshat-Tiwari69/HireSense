"""
Request Logging Middleware for Flask
Logs all API requests with timing, status, and user info
"""

import logging
import time
import contextlib
import re
from flask import request, g
from flask_jwt_extended import get_jwt_identity

logger = logging.getLogger('request_logger')

_ASSESSMENT_TOKEN_PATH = re.compile(
    r"(?P<prefix>/api/interviewee/assessment/(?:verify|start-by-token)/)[^/?#]+",
    re.IGNORECASE,
)


def redact_sensitive_path(path):
    """Remove bearer-like assessment tokens before a path reaches logs."""

    if not isinstance(path, str):
        return "<invalid-path>"
    return _ASSESSMENT_TOKEN_PATH.sub(r"\g<prefix><redacted>", path)


class SensitivePathFilter(logging.Filter):
    """Redact assessment tokens from framework and server access records."""

    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_path(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                redact_sensitive_path(value) if isinstance(value, str) else value
                for value in record.args
            )
        elif isinstance(record.args, dict):
            record.args = {
                key: redact_sensitive_path(value) if isinstance(value, str) else value
                for key, value in record.args.items()
            }
        return True


_SENSITIVE_PATH_FILTER = SensitivePathFilter()


def init_request_logging(app):
    """Initialize request logging for Flask app"""

    # Flask's development server and common production server access loggers can
    # otherwise emit the raw request target independently of our after-request log.
    for logger_name in ("request_logger", "werkzeug", "gunicorn.access"):
        target_logger = logging.getLogger(logger_name)
        if not any(
            isinstance(existing_filter, SensitivePathFilter)
            for existing_filter in target_logger.filters
        ):
            target_logger.addFilter(_SENSITIVE_PATH_FILTER)

    @app.before_request
    def before_request():
        g.start_time = time.perf_counter()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.perf_counter() - g.start_time
            user_id = None
            # Protected routes have already populated the JWT context. Reading it
            # here is cheap; public routes simply remain anonymous.
            with contextlib.suppress(Exception):
                user_id = get_jwt_identity()
            safe_path = redact_sensitive_path(request.path)
            logger.info(
                f"{request.method} {safe_path} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s | "
                f"User: {user_id or 'anonymous'} | "
                f"IP: {request.remote_addr}"
            )
        return response

    logger.info("[OK] Request logging initialized")
    return app
