"""
Proctor Routes Module
Handles proctoring endpoints for live monitoring of assessments
Protected routes requiring JWT authentication with 'proctor' role
"""

import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import logging
from db_config import get_connection
from db_helpers import DatabaseError

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint for proctor routes
proctor_bp = Blueprint('proctor', __name__)


def require_proctor_role(f):
    """Decorator to check for proctor role"""
    from functools import wraps
    @wraps(f)
    def check_proctor_role(*args, **kwargs):
        claims = get_jwt()
        role = claims.get('role')
        # Allow both proctor and admin roles
        if role not in ['proctor', 'admin']:
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Proctor role required.'
            }), 403
        return f(*args, **kwargs)
    return check_proctor_role


# ============================================================================
#                           ASSESSMENT MONITORING
# ============================================================================

@proctor_bp.route('/assessments/scheduled', methods=['GET'])
@jwt_required()
@require_proctor_role
def get_scheduled_assessments():
    """Get all scheduled assessments"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sa.id, sa.candidate_id, sa.scheduled_time, sa.status,
                   c.name as candidate_name, c.email as candidate_email
            FROM scheduled_assessments sa
            JOIN candidates c ON sa.candidate_id = c.id
            WHERE sa.status = 'scheduled'
            ORDER BY sa.scheduled_time ASC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        assessments = [{
            'id': row[0],
            'candidate_id': row[1],
            'scheduled_time': row[2],
            'status': row[3],
            'candidate_name': row[4],
            'candidate_email': row[5]
        } for row in rows]
        
        return jsonify({'status': 'success', 'data': assessments}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@proctor_bp.route('/assessments/active', methods=['GET'])
@jwt_required()
@require_proctor_role
def get_active_assessments():
    """Get all currently active (in-progress) assessments"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.candidate_id, a.started_at, a.status,
                   c.name as candidate_name, c.email as candidate_email,
                   sa.scheduled_time
            FROM assessments a
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN scheduled_assessments sa ON a.candidate_id = sa.candidate_id
            WHERE a.status = 'in_progress'
            ORDER BY a.started_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        assessments = [{
            'id': row[0],
            'candidate_id': row[1],
            'started_at': row[2],
            'status': row[3],
            'candidate_name': row[4],
            'candidate_email': row[5],
            'scheduled_time': row[6]
        } for row in rows]
        
        return jsonify({'status': 'success', 'data': assessments}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@proctor_bp.route('/assessments/completed', methods=['GET'])
@jwt_required()
@require_proctor_role
def get_completed_assessments():
    """Get all completed assessments"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id, a.candidate_id, a.started_at, a.completed_at, a.status,
                   a.proctoring_violations, a.mcq_score, a.coding_score, a.overall_score,
                   c.name as candidate_name, c.email as candidate_email
            FROM assessments a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.status = 'completed'
            ORDER BY a.completed_at DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        conn.close()
        
        assessments = [{
            'id': row[0],
            'candidate_id': row[1],
            'started_at': row[2],
            'completed_at': row[3],
            'status': row[4],
            'proctoring_violations': row[5],
            'mcq_score': row[6],
            'coding_score': row[7],
            'overall_score': row[8],
            'candidate_name': row[9],
            'candidate_email': row[10]
        } for row in rows]
        
        return jsonify({'status': 'success', 'data': assessments}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@proctor_bp.route('/assessments/<int:assessment_id>/violations', methods=['GET'])
@jwt_required()
@require_proctor_role
def get_assessment_violations(assessment_id):
    """Get proctoring violations for a specific assessment"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, assessment_id, violation_type, description, 
                   screenshot_url, timestamp, severity
            FROM proctoring_violations
            WHERE assessment_id = ?
            ORDER BY timestamp DESC
        """, (assessment_id,))
        rows = cursor.fetchall()
        conn.close()
        
        violations = [{
            'id': row[0],
            'assessment_id': row[1],
            'violation_type': row[2],
            'description': row[3],
            'screenshot_url': row[4],
            'timestamp': row[5],
            'severity': row[6]
        } for row in rows]
        
        return jsonify({'status': 'success', 'data': violations}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@proctor_bp.route('/stats', methods=['GET'])
@jwt_required()
@require_proctor_role
def get_proctor_stats():
    """Get proctoring statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Scheduled assessments count
        cursor.execute("SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'scheduled'")
        stats['scheduled_count'] = cursor.fetchone()[0]
        
        # Active assessments count
        cursor.execute("SELECT COUNT(*) FROM assessments WHERE status = 'in_progress'")
        stats['active_count'] = cursor.fetchone()[0]
        
        # Completed today
        cursor.execute("""
            SELECT COUNT(*) FROM assessments 
            WHERE status = 'completed' 
            AND DATE(completed_at) = CURRENT_DATE
        """)
        stats['completed_today'] = cursor.fetchone()[0]
        
        # Total violations today
        cursor.execute("""
            SELECT COUNT(*) FROM proctoring_violations 
            WHERE DATE(timestamp) = CURRENT_DATE
        """)
        stats['violations_today'] = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({'status': 'success', 'data': stats}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
#                           PROCTORING VIOLATION RECORDING
# ============================================================================

@proctor_bp.route('/violations', methods=['POST'])
def record_violation():
    """Record a proctoring violation (called from candidate's browser)"""
    try:
        data = request.get_json()
        
        assessment_id = data.get('assessment_id')
        violation_type = data.get('violation_type')  # 'no_face', 'multiple_faces', 'tab_switch', 'copy_paste'
        description = data.get('description', '')
        screenshot_url = data.get('screenshot_url')
        severity = data.get('severity', 'medium')  # low, medium, high
        
        if not assessment_id or not violation_type:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Insert violation
        cursor.execute("""
            INSERT INTO proctoring_violations 
            (assessment_id, violation_type, description, screenshot_url, severity, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            RETURNING id
        """, (assessment_id, violation_type, description, screenshot_url, severity))
        
        result = cursor.fetchone()
        violation_id = result[0] if result else None
        
        # Update violation count on assessment
        cursor.execute("""
            UPDATE assessments 
            SET proctoring_violations = COALESCE(proctoring_violations, 0) + 1
            WHERE id = ?
        """, (assessment_id,))
        
        conn.commit()
        conn.close()
        
        print(f"[PROCTOR] Violation recorded: {violation_type} for assessment {assessment_id}", flush=True)
        
        return jsonify({
            'status': 'success',
            'message': 'Violation recorded',
            'data': {'violation_id': violation_id}
        }), 201
    except Exception as e:
        print(f"[PROCTOR] Error recording violation: {e}", flush=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500
