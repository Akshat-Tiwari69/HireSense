"""
Rate Limiting Configuration for Flask Backend
Prevents API abuse and ensures fair usage
"""

import hashlib
import os

from flask import jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _limit_if_present(limiter, app, endpoint_name, limit, **limit_options):
    """Attach a rate limit to endpoint if it exists."""
    endpoint = app.view_functions.get(endpoint_name)
    if endpoint is not None:
        app.view_functions[endpoint_name] = limiter.limit(
            limit,
            **limit_options,
        )(endpoint)
        return True
    app.logger.warning("[RATE LIMIT] Endpoint not found: %s", endpoint_name)
    return False


def _assessment_submission_key():
    """Scope expensive submissions without storing bearer tokens in limiter keys."""
    assessment_id = (request.view_args or {}).get('assessment_id', 'unknown')
    token = request.headers.get('X-Assessment-Token', '').strip()
    if token:
        token_key = hashlib.sha256(token.encode('utf-8')).hexdigest()
    else:
        token_key = f"ip:{get_remote_address()}"
    return f"assessment:{assessment_id}:{token_key}"


def _not_a_coding_submission():
    """Keep ordinary assessment autosaves outside the expensive-code quota."""
    payload = request.get_json(silent=True)
    return not (isinstance(payload, dict) and payload.get('type') == 'coding')


def _not_screenshot_evidence():
    """Keep lightweight telemetry outside the screenshot-storage quota."""
    payload = request.get_json(silent=True)
    return not (isinstance(payload, dict) and payload.get('screenshot') is not None)


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
        default_limits=["5000 per day", "1000 per hour"],
        storage_uri=storage_uri,
    )

    # Auth endpoints - stricter limits
    _limit_if_present(limiter, app, 'auth.login', "10 per minute")

    # File upload - limited
    _limit_if_present(limiter, app, 'resume.upload_resume', "10 per hour")
    _limit_if_present(limiter, app, 'admin.admin_content.bulk_upload_resumes', "5 per hour")
    _limit_if_present(limiter, app, 'admin.admin_content.ai_enhance_text', "30 per hour")
    _limit_if_present(limiter, app, 'admin.admin_content.upload_question_bank', "10 per hour")
    _limit_if_present(limiter, app, 'interviewee.interviewee_answers.run_code', "30 per minute")
    _limit_if_present(
        limiter,
        app,
        'interviewee.interviewee_answers.submit_answer',
        "6 per minute; 30 per hour",
        key_func=_assessment_submission_key,
        exempt_when=_not_a_coding_submission,
        override_defaults=False,
    )
    _limit_if_present(
        limiter,
        app,
        'interviewee.interviewee_monitoring.report_violation',
        "120 per minute",
    )
    _limit_if_present(
        limiter,
        app,
        'interviewee.interviewee_monitoring.report_violation',
        "6 per minute; 20 per hour",
        key_func=_assessment_submission_key,
        exempt_when=_not_screenshot_evidence,
        override_defaults=False,
    )

    @app.errorhandler(429)
    def rate_limit_exceeded(_error):
        return jsonify({
            'status': 'error',
            'message': 'Too many requests. Please try again later.'
        }), 429

    return limiter
