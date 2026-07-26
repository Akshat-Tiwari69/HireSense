"""Admin analytics routes — system-wide stats and email logs."""

import logging
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from psycopg2.extras import RealDictCursor
from db_config import db_connection
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_analytics_bp = Blueprint('admin_analytics', __name__)

def _fetch_database_stats():
    with db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        users_by_role = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COALESCE(status, 'applied') as s, COUNT(*) FROM candidates GROUP BY s")
        candidates_by_status = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT status, COUNT(*) FROM scheduled_assessments GROUP BY status")
        assessments_by_status = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM candidates")
        total_candidates = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM assessments")
        total_assessments = cursor.fetchone()[0]

    return {
        'users_by_role': users_by_role,
        'candidates_by_status': candidates_by_status,
        'assessments_by_status': assessments_by_status,
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_assessments': total_assessments
    }


@admin_analytics_bp.route('/db/stats', methods=['GET'])
@jwt_required()
@require_admin_role
def get_db_stats():
    try:
        stats = _fetch_database_stats()
        return jsonify({'status': 'success', 'data': stats}), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_analytics_bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_admin_role
def get_analytics():
    try:
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM candidates) as total_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'applied') as applied_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'absence_of_details') as absence_of_details_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'pending') as pending_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'under_review') as under_review_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'completed') as completed_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'hired') as hired_candidates,
                    (SELECT COUNT(*) FROM candidates WHERE status = 'rejected') as rejected_candidates,
                    (SELECT AVG(match_score) FROM candidates) as avg_match_score,
                    (SELECT COUNT(*) FROM candidates WHERE created_at >= NOW() - INTERVAL '30 days') as candidates_this_month,
                    (SELECT COUNT(*) FROM scheduled_assessments) as total_assessments,
                    (SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'scheduled') as scheduled_assessments,
                    (SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'in_progress') as in_progress_assessments,
                    (SELECT COUNT(*) FROM scheduled_assessments WHERE status = 'completed') as completed_assessments,
                    (SELECT AVG(technical_score) FROM assessments) as avg_technical_score,
                    (SELECT AVG(psychometric_score) FROM assessments) as avg_psychometric_score,
                    (SELECT COUNT(*) FROM scheduled_assessments WHERE created_at >= NOW() - INTERVAL '30 days') as assessments_this_month
            """)

            stats = cursor.fetchone()

        analytics = {
            'candidates': {
                'total': stats['total_candidates'] or 0,
                'applied': stats['applied_candidates'] or 0,
                'absence_of_details': stats['absence_of_details_candidates'] or 0,
                'pending': stats['pending_candidates'] or 0,
                'under_review': stats['under_review_candidates'] or 0,
                'completed': stats['completed_candidates'] or 0,
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

        return jsonify({'status': 'success', 'data': analytics})
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch analytics: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_analytics_bp.route('/email-logs', methods=['GET'])
@jwt_required()
@require_admin_role
def get_email_logs():
    try:
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 100")
            logs = cursor.fetchall()

        formatted_logs = [
            {**log, 'sent_at': log['sent_at'].isoformat() if log.get('sent_at') else None}
            for log in logs
        ]

        return jsonify({'status': 'success', 'data': formatted_logs})
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch email logs: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
