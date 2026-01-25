"""
Admin Routes Module
Handles all admin dashboard endpoints for system management
Protected routes requiring JWT authentication with 'admin' role
"""

import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import logging
from db_config import get_connection
from db_helpers import DatabaseError
from auth import hash_password

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint for admin routes
admin_bp = Blueprint('admin', __name__)


def require_admin_role(f):
    """Decorator to check for admin role"""
    from functools import wraps
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


# ============================================================================
#                           USER MANAGEMENT
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin_role
def get_all_users():
    """Get all users in the system"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id")
        rows = cursor.fetchall()
        conn.close()
        
        users = [{
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'role': row[3],
            'created_at': row[4]
        } for row in rows]
        
        return jsonify({'status': 'success', 'data': users}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@require_admin_role
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'interviewer')
        
        if not all([name, email, password]):
            return jsonify({'status': 'error', 'message': 'Name, email, and password are required'}), 400
        
        if role not in ['interviewer', 'admin']:
            return jsonify({'status': 'error', 'message': 'Invalid role'}), 400
        
        password_hash = hash_password(password)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?) RETURNING id",
            (name, email, password_hash, role)
        )
        result = cursor.fetchone()
        user_id = result[0] if result else None
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'User created successfully',
            'data': {'id': user_id, 'name': name, 'email': email, 'role': role}
        }), 201
    except Exception as e:
        if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 409
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_user(user_id):
    """Update a user's details"""
    try:
        data = request.get_json()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("name = ?")
            values.append(data['name'])
        if 'email' in data:
            updates.append("email = ?")
            values.append(data['email'])
        if 'role' in data:
            if data['role'] not in ['interviewer', 'admin']:
                return jsonify({'status': 'error', 'message': 'Invalid role'}), 400
            updates.append("role = ?")
            values.append(data['role'])
        if 'password' in data and data['password']:
            updates.append("password_hash = ?")
            values.append(hash_password(data['password']))
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_user(user_id):
    """Delete a user"""
    try:
        # Prevent deleting yourself
        current_user_id = int(get_jwt_identity())
        if user_id == current_user_id:
            return jsonify({'status': 'error', 'message': 'Cannot delete your own account'}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                           CANDIDATE MANAGEMENT
# ============================================================================

@admin_bp.route('/candidates', methods=['GET'])
@jwt_required()
@require_admin_role
def get_all_candidates():
    """Get all candidates with full details"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, email, phone, resume_path, match_score, 
                   shortlist_status, pros, cons, created_at, status
            FROM candidates ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        candidates = [{
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'resume_path': row[4],
            'match_score': row[5],
            'shortlist_status': row[6],
            'pros': row[7],
            'cons': row[8],
            'created_at': row[9],
            'status': row[10] or row[6] or 'Applied'
        } for row in rows]
        
        return jsonify({'status': 'success', 'data': candidates}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/candidates/<int:candidate_id>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_candidate(candidate_id):
    """Update a candidate's details"""
    try:
        data = request.get_json()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("name = ?")
            values.append(data['name'])
        if 'email' in data:
            updates.append("email = ?")
            values.append(data['email'])
        if 'phone' in data:
            updates.append("phone = ?")
            values.append(data['phone'])
        if 'status' in data:
            updates.append("status = ?")
            values.append(data['status'])
            updates.append("shortlist_status = ?")
            values.append(data['status'])
        if 'match_score' in data:
            updates.append("match_score = ?")
            values.append(data['match_score'])
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        values.append(candidate_id)
        query = f"UPDATE candidates SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Candidate updated successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/candidates/<int:candidate_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_candidate(candidate_id):
    """Delete a candidate and all related data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Delete related records first
        cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = ?", (candidate_id,))
        cursor.execute("DELETE FROM assessments WHERE candidate_id = ?", (candidate_id,))
        cursor.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Candidate deleted successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                           DATABASE MANAGEMENT
# ============================================================================

@admin_bp.route('/db/tables', methods=['GET'])
@jwt_required()
@require_admin_role
def get_db_tables():
    """Get list of all tables in the database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # PostgreSQL query for tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        rows = cursor.fetchall()
        conn.close()
        
        tables = [row[0] for row in rows]
        return jsonify({'status': 'success', 'data': tables}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/db/tables/<table_name>', methods=['GET'])
@jwt_required()
@require_admin_role
def get_table_data(table_name):
    """Get data from a specific table (limited to 100 rows)"""
    try:
        # Whitelist allowed tables for security
        allowed_tables = ['users', 'candidates', 'assessments', 'scheduled_assessments', 'email_logs', 'questions', 'proctoring_violations']
        if table_name not in allowed_tables:
            return jsonify({'status': 'error', 'message': 'Table not allowed'}), 403
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Get data (limit 100 rows)
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        data = [dict(zip(columns, row)) for row in rows]
        
        return jsonify({
            'status': 'success',
            'data': data,
            'columns': columns,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/db/stats', methods=['GET'])
@jwt_required()
@require_admin_role
def get_db_stats():
    """Get database statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Count users by role
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        stats['users_by_role'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Count candidates by status
        cursor.execute("SELECT COALESCE(status, shortlist_status, 'Applied') as s, COUNT(*) FROM candidates GROUP BY s")
        stats['candidates_by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Count scheduled assessments
        cursor.execute("SELECT status, COUNT(*) FROM scheduled_assessments GROUP BY status")
        stats['assessments_by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total counts
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM candidates")
        stats['total_candidates'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM assessments")
        stats['total_assessments'] = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({'status': 'success', 'data': stats}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                           SYSTEM SETTINGS
# ============================================================================

@admin_bp.route('/settings/env', methods=['GET'])
@jwt_required()
@require_admin_role
def get_env_status():
    """Get status of required environment variables (not values)"""
    try:
        env_vars = [
            'DATABASE_URL',
            'JWT_SECRET_KEY',
            'OPENAI_API_KEY',
            'RESEND_API_KEY',
            'RESEND_FROM_EMAIL',
            'SMTP_HOST',
            'SMTP_USER',
            'FRONTEND_URL'
        ]
        
        status = {}
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                # Mask the value for security
                if len(value) > 8:
                    status[var] = f"{value[:4]}...{value[-4:]}"
                else:
                    status[var] = "***configured***"
            else:
                status[var] = None
        
        return jsonify({'status': 'success', 'data': status}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/reset-candidate-status/<int:candidate_id>', methods=['POST'])
@jwt_required()
@require_admin_role
def reset_candidate_status(candidate_id):
    """Reset a candidate's status back to Applied"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE candidates 
            SET status = 'Applied', shortlist_status = 'Applied'
            WHERE id = ?
        """, (candidate_id,))
        
        # Also delete any scheduled assessments for this candidate
        cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = ?", (candidate_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Candidate status reset to Applied'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
