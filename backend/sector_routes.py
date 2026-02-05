"""
Sector Management Routes
Handles sector-based organization and access control
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from functools import wraps
from db_config import get_connection, return_connection
from audit_logger import AuditLogger
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

# Create blueprint for sector routes
sector_bp = Blueprint('sectors', __name__)


def require_super_admin(f):
    """Decorator to check for super admin role"""
    @wraps(f)
    def check_super_admin(*args, **kwargs):
        claims = get_jwt()
        conn = None
        try:
            # Check if user is super admin
            user_email = get_jwt_identity()
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT is_super_admin, role FROM users WHERE email = %s",
                (user_email,)
            )
            result = cursor.fetchone()
            
            if not result or not (result[0] or result[1] == 'admin'):
                return jsonify({
                    'status': 'error',
                    'message': 'Access denied. Super Admin role required.'
                }), 403
            
            return f(*args, **kwargs)
        finally:
            if conn:
                return_connection(conn)
    
    return check_super_admin


def get_user_sector_access(user_email: str):
    """Get user's sector access information"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, sector_id, is_super_admin
            FROM users
            WHERE email = %s
        """, (user_email,))
        
        result = cursor.fetchone()
        if result:
            return {
                'role': result[0],
                'sector_id': result[1],
                'is_super_admin': result[2]
            }
        return None
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                           SECTOR CRUD OPERATIONS
# ============================================================================

@sector_bp.route('/sectors', methods=['GET'])
@jwt_required()
def get_sectors():
    """Get all sectors (accessible to all authenticated users)"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM sectors ORDER BY name")
        sectors = cursor.fetchall()
        
        # Format timestamps
        for sector in sectors:
            if sector.get('created_at'):
                sector['created_at'] = sector['created_at'].isoformat()
            if sector.get('updated_at'):
                sector['updated_at'] = sector['updated_at'].isoformat()
        
        return jsonify({
            'status': 'success',
            'data': sectors
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sectors: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@sector_bp.route('/sectors', methods=['POST'])
@jwt_required()
@require_super_admin
def create_sector():
    """Create a new sector (super admin only)"""
    conn = None
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        email = data.get('email')
        
        if not name or not email:
            return jsonify({
                'status': 'error',
                'message': 'Name and email are required'
            }), 400
        
        user_email = get_jwt_identity()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sectors (name, description, email)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (name, description, email))
        
        sector_id = cursor.fetchone()[0]
        conn.commit()
        
        # Log the action
        AuditLogger.log_action(
            user_id=None,
            user_email=user_email,
            action='create_sector',
            entity_type='sector',
            entity_id=sector_id,
            details={'sector_name': name}
        )
        
        logger.info(f"Sector '{name}' created by {user_email}")
        
        return jsonify({
            'status': 'success',
            'message': 'Sector created successfully',
            'data': {'id': sector_id}
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating sector: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@sector_bp.route('/sectors/<int:sector_id>', methods=['PUT'])
@jwt_required()
@require_super_admin
def update_sector(sector_id):
    """Update a sector (super admin only)"""
    conn = None
    try:
        data = request.get_json()
        user_email = get_jwt_identity()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("name = %s")
            values.append(data['name'])
        if 'description' in data:
            updates.append("description = %s")
            values.append(data['description'])
        if 'email' in data:
            updates.append("email = %s")
            values.append(data['email'])
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(sector_id)
        
        query = f"UPDATE sectors SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        
        # Log the action
        AuditLogger.log_action(
            user_id=None,
            user_email=user_email,
            action='update_sector',
            entity_type='sector',
            entity_id=sector_id,
            details={'changes': data}
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Sector updated successfully'
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error updating sector: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@sector_bp.route('/sectors/<int:sector_id>', methods=['DELETE'])
@jwt_required()
@require_super_admin
def delete_sector(sector_id):
    """Delete a sector (super admin only)"""
    conn = None
    try:
        user_email = get_jwt_identity()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get sector name before deleting
        cursor.execute("SELECT name FROM sectors WHERE id = %s", (sector_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'status': 'error', 'message': 'Sector not found'}), 404
        
        sector_name = result[0]
        
        cursor.execute("DELETE FROM sectors WHERE id = %s", (sector_id,))
        conn.commit()
        
        # Log the action
        AuditLogger.log_action(
            user_id=None,
            user_email=user_email,
            action='delete_sector',
            entity_type='sector',
            entity_id=sector_id,
            details={'sector_name': sector_name}
        )
        
        logger.info(f"Sector '{sector_name}' deleted by {user_email}")
        
        return jsonify({
            'status': 'success',
            'message': 'Sector deleted successfully'
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error deleting sector: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                           SECTOR STATISTICS
# ============================================================================

@sector_bp.route('/sectors/<int:sector_id>/stats', methods=['GET'])
@jwt_required()
def get_sector_stats(sector_id):
    """Get statistics for a specific sector"""
    conn = None
    try:
        user_email = get_jwt_identity()
        user_access = get_user_sector_access(user_email)
        
        # Check access rights
        if not user_access['is_super_admin'] and user_access['sector_id'] != sector_id:
            return jsonify({
                'status': 'error',
                'message': 'Access denied. You can only view your sector\'s stats.'
            }), 403
        
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get sector statistics
        cursor.execute("""
            SELECT 
                s.name as sector_name,
                s.email as sector_email,
                COUNT(DISTINCT jd.id) as total_jobs,
                COUNT(DISTINCT CASE WHEN jd.status = 'active' THEN jd.id END) as active_jobs,
                COUNT(DISTINCT c.id) as total_candidates,
                COUNT(DISTINCT u.id) as sector_users
            FROM sectors s
            LEFT JOIN job_descriptions jd ON jd.sector_id = s.id
            LEFT JOIN candidates c ON c.job_id IN (
                SELECT id FROM job_descriptions WHERE sector_id = s.id
            )
            LEFT JOIN users u ON u.sector_id = s.id
            WHERE s.id = %s
            GROUP BY s.id, s.name, s.email
        """, (sector_id,))
        
        stats = cursor.fetchone()
        
        if not stats:
            return jsonify({'status': 'error', 'message': 'Sector not found'}), 404
        
        return jsonify({
            'status': 'success',
            'data': dict(stats)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sector stats: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)
