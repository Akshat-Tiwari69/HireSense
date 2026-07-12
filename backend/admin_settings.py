"""
Admin settings routes — read and update environment variables.
"""

import os
import logging
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from dotenv import set_key, unset_key
from admin_middleware import require_admin_role, require_super_admin_role

logger = logging.getLogger(__name__)

admin_settings_bp = Blueprint('admin_settings', __name__)

_TRACKED_ENV_VARS = [
    'APP_ENV',
    'ALLOW_RUNTIME_ENV_MUTATION',
    'DATABASE_URL',
    'DB_STATEMENT_TIMEOUT_MS',
    'JWT_SECRET_KEY',
    'ALLOW_INSECURE_DEV_SECRET',
    'OPENAI_API_KEY',
    'OPENAI_MODEL',
    'OPENAI_RESUME_MODEL',
    'OPENAI_TIMEOUT_SECONDS',
    'OPENAI_MAX_RETRIES',
    'EMAIL_PROVIDER',
    'EMAIL_TIMEOUT_SECONDS',
    'RESEND_API_KEY',
    'RESEND_FROM_EMAIL',
    'SMTP_HOST',
    'SMTP_PORT',
    'SMTP_SSL_PORT',
    'SMTP_USER',
    'SMTP_PASS',
    'SMTP_SENDER_EMAIL',
    'SMTP_SENDER_NAME',
    'FRONTEND_URL',
    'CORS_ORIGINS',
    'REDIS_URL',
    'UPLOAD_FOLDER',
    'HTTP_PROXY',
    'HTTPS_PROXY',
]

_DEVELOPMENT_ENVIRONMENTS = {'dev', 'development', 'local', 'test'}
_KNOWN_ENVIRONMENTS = _DEVELOPMENT_ENVIRONMENTS | {'staging', 'production'}


def _valid_http_url(value):
    parsed = urlparse(value)
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def _runtime_env_mutation_enabled():
    """Require two explicit switches so production can never enable this accidentally."""
    app_env = os.environ.get('APP_ENV', 'production').strip().lower()
    opt_in = os.environ.get('ALLOW_RUNTIME_ENV_MUTATION', '').strip().lower()
    return app_env in _DEVELOPMENT_ENVIRONMENTS and opt_in == 'true'


def _validate_env_value(name, value):
    if not value:
        return None
    if len(value) > 4_096:
        return 'Variable value is too long'
    if name == 'APP_ENV' and value.lower() not in _KNOWN_ENVIRONMENTS:
        return 'APP_ENV must be dev, development, local, test, staging, or production'
    if name in {'ALLOW_RUNTIME_ENV_MUTATION', 'ALLOW_INSECURE_DEV_SECRET'}:
        if value.lower() not in {'true', 'false'}:
            return f'{name} must be true or false'
    if name == 'DATABASE_URL' and not value.startswith(('postgresql://', 'postgres://')):
        return 'DATABASE_URL must start with postgresql:// or postgres://'
    if name == 'DB_STATEMENT_TIMEOUT_MS':
        try:
            timeout_ms = int(value)
        except ValueError:
            return 'DB_STATEMENT_TIMEOUT_MS must be an integer'
        if not 1_000 <= timeout_ms <= 600_000:
            return 'DB_STATEMENT_TIMEOUT_MS must be between 1000 and 600000'
    if name == 'JWT_SECRET_KEY' and len(value) < 32:
        return 'JWT_SECRET_KEY must contain at least 32 characters'
    if name == 'FRONTEND_URL' and not _valid_http_url(value):
        return 'FRONTEND_URL must be an HTTP or HTTPS URL'
    if name == 'CORS_ORIGINS':
        origins = [origin.strip() for origin in value.split(',') if origin.strip()]
        if not origins or any(not _valid_http_url(origin) for origin in origins):
            return 'CORS_ORIGINS must be a comma-separated list of HTTP or HTTPS URLs'
    if name == 'REDIS_URL' and not value.startswith(('redis://', 'rediss://')):
        return 'REDIS_URL must start with redis:// or rediss://'
    if name in {'HTTP_PROXY', 'HTTPS_PROXY'} and not _valid_http_url(value):
        return f'{name} must be an HTTP or HTTPS URL'
    if name == 'EMAIL_PROVIDER' and value.lower() not in {'auto', 'smtp', 'resend'}:
        return 'EMAIL_PROVIDER must be auto, smtp, or resend'
    if name in {'SMTP_PORT', 'SMTP_SSL_PORT'}:
        try:
            port = int(value)
        except ValueError:
            return f'{name} must be an integer'
        if not 1 <= port <= 65_535:
            return f'{name} must be between 1 and 65535'
    if name in {'OPENAI_TIMEOUT_SECONDS', 'EMAIL_TIMEOUT_SECONDS'}:
        try:
            timeout = float(value)
        except ValueError:
            return f'{name} must be numeric'
        if not 1 <= timeout <= 120:
            return f'{name} must be between 1 and 120'
    if name == 'OPENAI_MAX_RETRIES':
        try:
            retries = int(value)
        except ValueError:
            return 'OPENAI_MAX_RETRIES must be an integer'
        if not 0 <= retries <= 3:
            return 'OPENAI_MAX_RETRIES must be between 0 and 3'
    return None


@admin_settings_bp.route('/settings/env', methods=['GET'])
@jwt_required()
@require_admin_role
def get_env_status():
    try:
        status = {}
        for var in _TRACKED_ENV_VARS:
            status[var] = "***configured***" if os.environ.get(var) else None

        return jsonify({
            'status': 'success',
            'data': status,
            'runtime_mutation_enabled': _runtime_env_mutation_enabled(),
        }), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_settings_bp.route('/settings/env', methods=['POST'])
@jwt_required()
@require_super_admin_role
def set_env_variable():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        var_name = data.get('name')
        var_value = data.get('value')

        if not var_name:
            return jsonify({'status': 'error', 'message': 'Variable name is required'}), 400

        if var_name not in _TRACKED_ENV_VARS:
            return jsonify({'status': 'error', 'message': 'Variable name not allowed'}), 400

        if var_value is not None and not isinstance(var_value, str):
            return jsonify({'status': 'error', 'message': 'Variable value must be a string'}), 400

        if var_value and any(character in var_value for character in ('\r', '\n', '\x00')):
            return jsonify({'status': 'error', 'message': 'Variable value contains invalid characters'}), 400

        if validation_error := _validate_env_value(var_name, var_value):
            return jsonify({'status': 'error', 'message': validation_error}), 400

        if not _runtime_env_mutation_enabled():
            return jsonify({
                'status': 'error',
                'message': (
                    'Runtime environment changes are disabled. Configure deployment '
                    'variables through the hosting platform. For local development only, '
                    'set APP_ENV=development and ALLOW_RUNTIME_ENV_MUTATION=true.'
                ),
            }), 403

        env_file_path = os.path.join(os.path.dirname(__file__), '.env')
        if var_value:
            set_key(env_file_path, var_name, var_value, quote_mode='always')
            os.environ[var_name] = var_value
        else:
            unset_key(env_file_path, var_name)
            os.environ.pop(var_name, None)

        logger.info(f"Environment variable {var_name} {'updated' if var_value else 'removed'} by admin")

        return jsonify({
            'status': 'success',
            'message': f"Environment variable {var_name} {'updated' if var_value else 'removed'} successfully"
        }), 200
    except Exception as exc:
        logger.error("Error setting environment variable (%s)", type(exc).__name__)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
