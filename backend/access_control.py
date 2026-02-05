"""
Access Control Module
Provides decorators for role-based and sector-based access control
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
import logging

logger = logging.getLogger(__name__)


def require_role(*allowed_roles):
    """
    Decorator to enforce role-based access control
    
    Usage:
        @require_role('admin', 'super_admin')
        def admin_only_route():
            pass
    
    Args:
        *allowed_roles: Variable number of role strings that are allowed
    
    Returns:
        Decorator function
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role not in allowed_roles:
                logger.warning(f"[ACCESS DENIED] User role '{user_role}' not in {allowed_roles}")
                return jsonify({
                    'status': 'error',
                    'message': 'Insufficient permissions'
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_sector_access(allow_super_admin=True):
    """
    Decorator to enforce sector-based access control
    
    This decorator ensures that:
    - Super admins can access all sectors (if allow_super_admin=True)
    - Sector admins and recruiters can only access their assigned sector
    - Other roles are denied unless they have super_admin privilege
    
    The sector is obtained from:
    1. Request query parameter 'sector'
    2. Request JSON body 'sector' field
    3. URL path parameter (if present)
    
    Usage:
        @require_sector_access()
        def sector_specific_route():
            pass
    
    Args:
        allow_super_admin (bool): If True, super_admin can access all sectors
    
    Returns:
        Decorator function
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request
            
            claims = get_jwt()
            user_role = claims.get('role')
            user_sector = claims.get('sector')
            
            # Super admin has access to all sectors
            if allow_super_admin and user_role == 'super_admin':
                return fn(*args, **kwargs)
            
            # Get requested sector from various sources
            requested_sector = None
            
            # Check query parameters
            if request.args.get('sector'):
                requested_sector = request.args.get('sector')
            
            # Check JSON body
            elif request.is_json and request.get_json(silent=True):
                data = request.get_json()
                requested_sector = data.get('sector')
            
            # Check URL path parameters
            elif 'sector' in kwargs:
                requested_sector = kwargs['sector']
            
            # If no sector is requested, use user's assigned sector
            if not requested_sector:
                requested_sector = user_sector
            
            # Sector-specific roles must match sectors
            if user_role in ['sector_admin', 'recruiter']:
                if not user_sector:
                    logger.error(f"[ACCESS DENIED] User has sector role but no sector assigned")
                    return jsonify({
                        'status': 'error',
                        'message': 'User sector not configured'
                    }), 403
                
                if requested_sector and requested_sector != user_sector:
                    logger.warning(f"[ACCESS DENIED] Sector mismatch: user={user_sector}, requested={requested_sector}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Access denied: sector mismatch'
                    }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_any_admin():
    """
    Decorator to allow access to any admin role (super_admin, sector_admin, admin)
    
    Usage:
        @require_any_admin()
        def admin_route():
            pass
    """
    return require_role('super_admin', 'sector_admin', 'admin')


def require_super_admin():
    """
    Decorator to allow access only to super_admin
    
    Usage:
        @require_super_admin()
        def super_admin_route():
            pass
    """
    return require_role('super_admin')


def can_access_sector(user_sector, user_role, target_sector):
    """
    Helper function to check if a user can access a specific sector
    
    Args:
        user_sector (str): User's assigned sector
        user_role (str): User's role
        target_sector (str): Target sector to access
    
    Returns:
        bool: True if user can access the sector
    """
    # Super admin can access all sectors
    if user_role == 'super_admin':
        return True
    
    # Sector-specific roles can only access their sector
    if user_role in ['sector_admin', 'recruiter']:
        return user_sector == target_sector
    
    # Other roles (admin, interviewer, proctor) have global access
    if user_role in ['admin', 'interviewer', 'proctor']:
        return True
    
    return False


def filter_by_sector_access(items, sector_field='sector'):
    """
    Filter a list of items based on user's sector access
    
    Args:
        items (list): List of dictionaries to filter
        sector_field (str): Name of the sector field in each item
    
    Returns:
        list: Filtered list based on user's sector access
    """
    claims = get_jwt()
    user_role = claims.get('role')
    user_sector = claims.get('sector')
    
    # Super admin and global roles can see all
    if user_role in ['super_admin', 'admin', 'interviewer', 'proctor']:
        return items
    
    # Sector-specific roles can only see their sector
    if user_role in ['sector_admin', 'recruiter']:
        return [item for item in items if item.get(sector_field) == user_sector]
    
    return []
