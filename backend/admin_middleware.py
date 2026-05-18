"""
Shared admin middleware — role-checking decorator used by all admin sub-modules.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt


def require_admin_role(f):
    """Decorator: rejects non-admin JWT tokens with 403."""
    @wraps(f)
    def check_admin_role(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Admin role required.'
            }), 403
        return f(*args, **kwargs)
    return check_admin_role
