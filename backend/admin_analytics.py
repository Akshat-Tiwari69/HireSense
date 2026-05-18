"""
Admin analytics routes — system-wide stats, email logs, and DB inspection.
"""

import logging
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from psycopg2.extras import RealDictCursor
from db_config import get_connection, return_connection
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_analytics_bp = Blueprint('admin_analytics', __name__)


def _fetch_database_stats():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
    users_by_role = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT COALESCE(status, shortlist_status, 'Applied') as s, COUNT(*) FROM candidates GROUP BY s")
    candidates_by_status = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT status, COUNT(*) FROM scheduled_assessments GROUP BY status")
    assessments_by_status = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM assessments")
    total_assessments = cursor.fetchone()[0]

    conn.close()

    return {
        'users_by_role': users_by_role,
        'candidates_by_status': candidates_by_status,
        'assessments_by_status': assessments_by_status,
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_assessments': total_assessments
    }


@admin_analytics_bp.route('/db/tables', methods=['GET'])
@jwt_required()
@require_admin_role
def get_db_tables():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'data': [row[0] for row in rows]}), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_analytics_bp.route('/db/tables/<table_name>', methods=['GET'])
@jwt_required()
@require_admin_role
def get_table_data(table_name):
    conn = None
    try:
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

        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s ORDER BY ordinal_position",
            (table_name,)
        )
        columns = [row[0] for row in cursor.fetchall()]

        from psycopg2 import sql
        if 'id' in columns:
            cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY id DESC LIMIT 100").format(sql.Identifier(table_name)))
        else:
            cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 100").format(sql.Identifier(table_name)))
        rows = cursor.fetchall()

        data = [dict(zip(columns, row)) for row in rows]

        return jsonify({
            'status': 'success',
            'data': data,
            'columns': columns,
            'count': len(data)
        }), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


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
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

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

        return jsonify({'status': 'success', 'data': analytics})
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to fetch analytics: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()


@admin_analytics_bp.route('/email-logs', methods=['GET'])
@jwt_required()
@require_admin_role
def get_email_logs():
    conn = None
    try:
        conn = get_connection()
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
    finally:
        if conn:
            return_connection(conn)
