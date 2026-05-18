"""
Admin settings routes — read and update environment variables.
"""

import os
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_settings_bp = Blueprint('admin_settings', __name__)

_TRACKED_ENV_VARS = [
    'DATABASE_URL',
    'JWT_SECRET_KEY',
    'RESEND_API_KEY',
    'RESEND_FROM_EMAIL',
    'SMTP_HOST',
    'SMTP_USER',
    'FRONTEND_URL',
]


@admin_settings_bp.route('/settings/env', methods=['GET'])
@jwt_required()
@require_admin_role
def get_env_status():
    try:
        status = {}
        for var in _TRACKED_ENV_VARS:
            if value := os.environ.get(var):
                status[var] = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***configured***"
            else:
                status[var] = None

        return jsonify({'status': 'success', 'data': status}), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_settings_bp.route('/settings/env', methods=['POST'])
@jwt_required()
@require_admin_role
def set_env_variable():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        var_name = data.get('name')
        var_value = data.get('value')

        if not var_name:
            return jsonify({'status': 'error', 'message': 'Variable name is required'}), 400

        if var_name == 'DATABASE_URL' and var_value and not var_value.startswith(('postgresql://', 'postgres://')):
            return jsonify({'status': 'error', 'message': 'DATABASE_URL must start with postgresql:// or postgres://'}), 400

        if var_value:
            os.environ[var_name] = var_value
        elif var_name in os.environ:
            del os.environ[var_name]

        env_file_path = os.path.join(os.path.dirname(__file__), '.env')
        env_vars = {}

        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        if var_value:
            env_vars[var_name] = var_value
        elif var_name in env_vars:
            del env_vars[var_name]

        with open(env_file_path, 'w') as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        logger.info(f"Environment variable {var_name} {'updated' if var_value else 'removed'} by admin")

        return jsonify({
            'status': 'success',
            'message': f"Environment variable {var_name} {'updated' if var_value else 'removed'} successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error setting environment variable: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
