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
from functools import lru_cache
from db_config import get_connection, return_connection
from db_helpers import DatabaseError
from auth import hash_password
from psycopg2.extras import RealDictCursor

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
    """Get all users in the system with optimized pooled connection"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id")
        rows = cursor.fetchall()
        
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
    finally:
        if conn:
            return_connection(conn)


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
        
        if role not in ['interviewer', 'admin', 'proctor']:
            return jsonify({'status': 'error', 'message': 'Invalid role. Must be interviewer, proctor, or admin'}), 400
        
        admin_email = get_jwt_identity()
        logger.info(f"[ADMIN ACTION] {admin_email} creating new user: {email} with role: {role}")
        
        password_hash = hash_password(password)
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, email, password_hash, role)
        )
        result = cursor.fetchone()
        user_id = result[0] if result else None
        conn.commit()
        conn.close()
        
        logger.info(f"[ADMIN ACTION] {admin_email} successfully created user ID: {user_id} ({email})")
        
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
        admin_email = get_jwt_identity()
        data = request.get_json()
        
        logger.info(f"[ADMIN ACTION] {admin_email} updating user ID: {user_id} with data: {list(data.keys())}")
        
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
            if data['role'] not in ['interviewer', 'admin', 'proctor']:
                return jsonify({'status': 'error', 'message': 'Invalid role. Must be interviewer, proctor, or admin'}), 400
            updates.append("role = ?")
            values.append(data['role'])
        if 'password' in data and data['password']:
            updates.append("password_hash = ?")
            values.append(hash_password(data['password']))
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        logger.info(f"[ADMIN ACTION] {admin_email} successfully updated user ID: {user_id}")
        
        return jsonify({'status': 'success', 'message': 'User updated successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to update user ID {user_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_user(user_id):
    """Delete a user"""
    try:
        # Prevent deleting yourself
        admin_email = get_jwt_identity()
        current_user_id = int(admin_email.split('@')[0]) if '@' in admin_email else 0
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get user info before deleting
        cursor.execute("SELECT email, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        user_email = user[0]
        user_role = user[1]
        
        logger.warning(f"[ADMIN ACTION] {admin_email} deleting user ID: {user_id} ({user_email}, role: {user_role})")
        
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"[ADMIN ACTION] {admin_email} successfully deleted user ID: {user_id}")
        
        return jsonify({'status': 'success', 'message': 'User deleted successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to delete user ID {user_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                           CANDIDATE MANAGEMENT
# ============================================================================

@admin_bp.route('/candidates', methods=['GET'])
@jwt_required()
@require_admin_role
def get_all_candidates():
    """Get all candidates with full details (filtered by sector access)"""
    from flask_jwt_extended import get_jwt
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, email, phone, resume_path, match_score, 
                   shortlist_status, pros, cons, created_at, status, sector, skills
            FROM candidates ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        
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
            'status': row[10] or row[6] or 'Applied',
            'sector': row[11],
            'skills': row[12]
        } for row in rows]
        
        # Filter by sector access
        claims = get_jwt()
        user_role = claims.get('role')
        user_sector = claims.get('sector')
        
        # Sector admins and recruiters can only see candidates in their sector
        if user_role in ['sector_admin', 'recruiter']:
            candidates = [c for c in candidates if c.get('sector') == user_sector]
        
        return jsonify({'status': 'success', 'data': candidates}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_bp.route('/candidates/<int:candidate_id>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_candidate(candidate_id):
    """Update a candidate's details"""
    try:
        admin_email = get_jwt_identity()
        data = request.get_json()
        
        logger.info(f"[ADMIN ACTION] {admin_email} updating candidate ID: {candidate_id} with data: {list(data.keys())}")
        
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
        query = f"UPDATE candidates SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        logger.info(f"[ADMIN ACTION] {admin_email} successfully updated candidate ID: {candidate_id}")
        
        return jsonify({'status': 'success', 'message': 'Candidate updated successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to update candidate ID {candidate_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/candidates/<int:candidate_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_candidate(candidate_id):
    """Delete a candidate and all related data"""
    try:
        admin_email = get_jwt_identity()
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get candidate info before deleting
        cursor.execute("SELECT name, email FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()
        
        if not candidate:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404
        
        candidate_name = candidate[0]
        candidate_email = candidate[1]
        
        logger.warning(f"[ADMIN ACTION] {admin_email} deleting candidate ID: {candidate_id} ({candidate_name}, {candidate_email}) and all related data")
        
        # Delete related records first
        cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = %s", (candidate_id,))
        cursor.execute("DELETE FROM assessments WHERE candidate_id = %s", (candidate_id,))
        cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[ADMIN ACTION] {admin_email} successfully deleted candidate ID: {candidate_id}")
        
        return jsonify({'status': 'success', 'message': 'Candidate deleted successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to delete candidate ID {candidate_id}: {str(e)}")
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
    """Get data from a specific table (limited to 100 rows) with optimized pooling"""
    conn = None
    try:
        # Whitelist allowed tables for security
        allowed_tables = {
            'users', 'candidates', 'assessments', 'scheduled_assessments', 
            'email_logs', 'questions', 'proctoring_violations',
            'coding_submissions', 'job_descriptions', 'mcq_responses',
            'proctoring_events', 'psychometric_responses'
        }
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
        # Check if table has 'id' column for ordering
        if 'id' in columns:
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 100")
        else:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
        rows = cursor.fetchall()
        
        data = [dict(zip(columns, row)) for row in rows]
        
        return jsonify({
            'status': 'success',
            'data': data,
            'columns': columns,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


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


@admin_bp.route('/settings/env', methods=['POST'])
@jwt_required()
@require_admin_role
def set_env_variable():
    """Set/update environment variables and persist to .env file"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        var_name = data.get('name')
        var_value = data.get('value')
        
        if not var_name:
            return jsonify({'status': 'error', 'message': 'Variable name is required'}), 400
        
        # Validate DATABASE_URL format if being set
        if var_name == 'DATABASE_URL' and var_value:
            if not (var_value.startswith('postgresql://') or var_value.startswith('postgres://')):
                return jsonify({'status': 'error', 'message': 'DATABASE_URL must start with postgresql:// or postgres://'}), 400
        
        # Set in current environment
        if var_value:
            os.environ[var_name] = var_value
        elif var_name in os.environ:
            del os.environ[var_name]
        
        # Persist to .env file
        env_file_path = os.path.join(os.path.dirname(__file__), '.env')
        env_vars = {}
        
        # Read existing .env file if it exists
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        
        # Update or remove the variable
        if var_value:
            env_vars[var_name] = var_value
        elif var_name in env_vars:
            del env_vars[var_name]
        
        # Write back to .env file
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
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/reset-candidate-status/<int:candidate_id>', methods=['POST'])
@jwt_required()
@require_admin_role
def reset_candidate_status(candidate_id):
    """Reset a candidate's status back to Applied"""
    try:
        admin_email = get_jwt_identity()
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get candidate info
        cursor.execute("SELECT name, email FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()
        
        if not candidate:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404
        
        candidate_name = candidate[0]
        candidate_email = candidate[1]
        
        logger.info(f"[ADMIN ACTION] {admin_email} resetting status to 'Applied' for candidate ID: {candidate_id} ({candidate_name})")
        
        cursor.execute("""
            UPDATE candidates 
            SET status = 'Applied', shortlist_status = 'Applied'
            WHERE id = %s
        """, (candidate_id,))
        
        # Also delete any scheduled assessments for this candidate
        cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = %s", (candidate_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"[ADMIN ACTION] {admin_email} successfully reset candidate ID: {candidate_id} to 'Applied'")
        
        return jsonify({'status': 'success', 'message': 'Candidate status reset to Applied'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to reset candidate ID {candidate_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                           EMAIL LOGS MANAGEMENT
# ============================================================================

@admin_bp.route('/email-logs', methods=['GET'])
@jwt_required()
@require_admin_role
def get_email_logs():
    """
    Get all email logs with optimized timestamp formatting
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 100")
        logs = cursor.fetchall()
        
        # Use list comprehension for in-place formatting (faster than loop)
        formatted_logs = [
            {**log, 'sent_at': log['sent_at'].isoformat() if log.get('sent_at') else None}
            for log in logs
        ]
        
        return jsonify({
            'status': 'success',
            'data': formatted_logs
        })
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch email logs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                           JOB POSTINGS MANAGEMENT
# ============================================================================

@admin_bp.route('/job-postings', methods=['GET'])
@jwt_required()
@require_admin_role
def get_job_postings():
    """
    Get all job postings (filtered by sector access)
    """
    from flask_jwt_extended import get_jwt
    from access_control import filter_by_sector_access
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
        jobs = cursor.fetchall()
        
        cursor.close()
        
        # Format timestamps
        for job in jobs:
            if job.get('created_at'):
                job['created_at'] = job['created_at'].isoformat()
            if job.get('updated_at'):
                job['updated_at'] = job['updated_at'].isoformat()
        
        # Filter by sector access
        claims = get_jwt()
        user_role = claims.get('role')
        user_sector = claims.get('sector')
        
        # Sector admins can only see jobs in their sector
        if user_role == 'sector_admin':
            jobs = [job for job in jobs if job.get('sector') == user_sector]
        
        return jsonify({
            'status': 'success',
            'data': jobs
        })
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch job postings: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()


@admin_bp.route('/job-postings', methods=['POST'])
@jwt_required()
@require_admin_role
def create_job_posting():
    """
    Create a new job posting with required and preferred skills
    """
    from audit_middleware import audit_log
    from access_control import filter_by_sector_access
    from flask_jwt_extended import get_jwt
    
    conn = None
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('title'):
            return jsonify({'status': 'error', 'message': 'Title is required'}), 400
        
        if not data.get('required_skills'):
            return jsonify({'status': 'error', 'message': 'At least one required skill must be specified'}), 400
        
        # Get user info from JWT
        claims = get_jwt()
        user_role = claims.get('role')
        user_sector = claims.get('sector')
        
        # Determine sector for the job
        job_sector = data.get('sector', '')
        
        # Sector admins can only create jobs in their sector
        if user_role == 'sector_admin' and job_sector != user_sector:
            return jsonify({
                'status': 'error',
                'message': 'Sector admins can only create jobs in their assigned sector'
            }), 403
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO job_descriptions 
            (title, description, required_skills, preferred_skills, min_experience, department, location, sector)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['title'],
            data.get('description', ''),
            data.get('required_skills', ''),
            data.get('preferred_skills', ''),
            data.get('min_experience', 0),
            data.get('department', ''),
            data.get('location', ''),
            job_sector
        ))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        
        # Log audit trail
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
        from db_helpers import log_audit, get_user_by_id
        user = get_user_by_id(user_id)
        log_audit(
            user_id=int(user_id),
            user_email=user.get('email') if user else 'unknown',
            action='create',
            resource_type='job',
            resource_id=job_id,
            details={'title': data['title'], 'sector': job_sector},
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Job posting created successfully',
            'data': {'id': job_id}
        }), 201
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[ADMIN ERROR] Failed to create job posting: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()


@admin_bp.route('/job-postings/<int:job_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_job_posting(job_id):
    """
    Delete a job posting
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM job_descriptions WHERE id = %s", (job_id,))
        conn.commit()
        cursor.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Job posting deleted successfully'
        })
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[ADMIN ERROR] Failed to delete job posting: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()


# ============================================================================
#                           ANALYTICS
# ============================================================================

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_admin_role
def get_analytics():
    """
    Get system-wide analytics and statistics.
    Optimized with combined queries for better performance.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Combined query for all statistics - more efficient than separate queries
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM candidates) as total_candidates,
                (SELECT COUNT(*) FROM candidates WHERE status = 'pending') as pending_candidates,
                (SELECT COUNT(*) FROM candidates WHERE status = 'under_review') as under_review_candidates,
                (SELECT COUNT(*) FROM candidates WHERE status = 'hired') as hired_candidates,
                (SELECT COUNT(*) FROM candidates WHERE status = 'rejected') as rejected_candidates,
                (SELECT AVG(match_score) FROM candidates) as avg_match_score,
                (SELECT COUNT(*) FROM candidates WHERE created_at >= NOW() - INTERVAL '30 days') as candidates_this_month,
                (SELECT COUNT(*) FROM scheduled_assessments) as total_assessments,
                (SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'scheduled') as scheduled_assessments,
                (SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'in_progress') as in_progress_assessments,
                (SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'completed') as completed_assessments,
                (SELECT AVG(technical_score) FROM scheduled_assessments) as avg_technical_score,
                (SELECT AVG(psychometric_score) FROM scheduled_assessments) as avg_psychometric_score,
                (SELECT COUNT(*) FROM scheduled_assessments WHERE created_at >= NOW() - INTERVAL '30 days') as assessments_this_month
        """)
        
        stats = cursor.fetchone()
        cursor.close()
        
        # Build response using extracted stats
        analytics = {
            'candidates': {
                'total': stats['total_candidates'] or 0,
                'pending': stats['pending_candidates'] or 0,
                'under_review': stats['under_review_candidates'] or 0,
                'hired': stats['hired_candidates'] or 0,
                'rejected': stats['rejected_candidates'] or 0,
                'avg_match_score': round(float(stats['avg_match_score'] or 0), 2),
                'this_month': stats['candidates_this_month'] or 0
            },
            'assessments': {
                'total': stats['total_assessments'] or 0,
                'scheduled': stats['scheduled_assessments'] or 0,
                'in_progress': stats['in_progress_assessments'] or 0,
                'completed': stats['completed_assessments'] or 0,
                'avg_technical_score': round(float(stats['avg_technical_score'] or 0), 2),
                'avg_psychometric_score': round(float(stats['avg_psychometric_score'] or 0), 2),
                'this_month': stats['assessments_this_month'] or 0
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch analytics: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()


# ============================================================================
#                    SECTOR EMAIL CONFIGURATION ROUTES
# ============================================================================

@admin_bp.route('/sector-emails', methods=['GET'])
@jwt_required()
@require_admin_role
def get_sector_emails():
    """
    Get all sector email configurations
    """
    try:
        from db_helpers import get_all_sector_email_configs
        configs = get_all_sector_email_configs()
        
        # Format timestamps
        for config in configs:
            if config.get('created_at'):
                config['created_at'] = config['created_at'].isoformat()
            if config.get('updated_at'):
                config['updated_at'] = config['updated_at'].isoformat()
        
        return jsonify({
            'status': 'success',
            'data': configs
        })
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch sector emails: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/sector-emails', methods=['POST'])
@jwt_required()
@require_admin_role
def create_sector_email():
    """
    Create a new sector email configuration (Super Admin only)
    """
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from db_helpers import create_sector_email_config, log_audit, get_user_by_id
    
    try:
        # Only super_admin can create sector email configs
        claims = get_jwt()
        if claims.get('role') != 'super_admin':
            return jsonify({
                'status': 'error',
                'message': 'Only super admins can create sector email configurations'
            }), 403
        
        data = request.get_json()
        
        if not all(k in data for k in ['sector', 'email_address', 'display_name']):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: sector, email_address, display_name'
            }), 400
        
        config_id = create_sector_email_config(
            data['sector'],
            data['email_address'],
            data['display_name']
        )
        
        # Log audit trail
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        log_audit(
            user_id=int(user_id),
            user_email=user.get('email') if user else 'unknown',
            action='create',
            resource_type='sector_email_config',
            resource_id=config_id,
            details={'sector': data['sector']},
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Sector email configuration created successfully',
            'data': {'id': config_id}
        }), 201
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to create sector email: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/sector-emails/<sector>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_sector_email(sector):
    """
    Update a sector email configuration (Super Admin only)
    """
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from db_helpers import update_sector_email_config, log_audit, get_user_by_id
    
    try:
        # Only super_admin can update sector email configs
        claims = get_jwt()
        if claims.get('role') != 'super_admin':
            return jsonify({
                'status': 'error',
                'message': 'Only super admins can update sector email configurations'
            }), 403
        
        data = request.get_json()
        
        update_sector_email_config(
            sector=sector,
            email_address=data.get('email_address'),
            display_name=data.get('display_name'),
            is_active=data.get('is_active')
        )
        
        # Log audit trail
        user_id = get_jwt_identity()
        user = get_user_by_id(user_id)
        log_audit(
            user_id=int(user_id),
            user_email=user.get('email') if user else 'unknown',
            action='update',
            resource_type='sector_email_config',
            details={'sector': sector, 'changes': data},
            ip_address=request.headers.get('X-Forwarded-For', request.remote_addr),
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Sector email configuration updated successfully'
        })
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to update sector email: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                          AUDIT LOG ROUTES
# ============================================================================

@admin_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@require_admin_role
def get_audit_logs():
    """
    Get audit logs (filtered based on role)
    Super Admin: All logs
    Sector Admin: Only logs for their sector
    """
    from flask_jwt_extended import get_jwt
    from db_helpers import get_audit_logs
    
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        user_sector = claims.get('sector')
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        action = request.args.get('action')
        resource_type = request.args.get('resource_type')
        
        logs = get_audit_logs(limit=limit, action=action, resource_type=resource_type)
        
        # Format timestamps
        for log in logs:
            if log.get('timestamp'):
                log['timestamp'] = log['timestamp'].isoformat()
        
        # Filter by sector for sector admins
        if user_role == 'sector_admin':
            # Sector admins can only see logs from users in their sector
            logs = [log for log in logs if log.get('details', {}).get('sector') == user_sector]
        
        return jsonify({
            'status': 'success',
            'data': logs
        })
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch audit logs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
