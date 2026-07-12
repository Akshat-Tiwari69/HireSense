"""
Shared admin middleware — role-checking decorator used by all admin sub-modules.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt


_ADMIN_ROLES = {'admin', 'super_admin'}


def require_admin_role(f):
    """Decorator: rejects tokens that do not have an admin-level role."""
    @wraps(f)
    def check_admin_role(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') not in _ADMIN_ROLES:
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Admin role required.'
            }), 403
        return f(*args, **kwargs)
    return check_admin_role


def require_super_admin_role(f):
    """Decorator: restricts infrastructure-level operations to super admins."""
    @wraps(f)
    def check_super_admin_role(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'super_admin':
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Super admin role required.'
            }), 403
        return f(*args, **kwargs)
    return check_super_admin_role
