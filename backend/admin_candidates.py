"""
Admin candidate management routes — view, update, delete, and reset candidates.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db_config import get_connection, return_connection
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_candidates_bp = Blueprint('admin_candidates', __name__)


@admin_candidates_bp.route('/absence-of-details', methods=['GET'])
@jwt_required()
@require_admin_role
def get_absence_of_details():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.email, c.phone, c.resume_path,
                   c.match_score, c.status, c.created_at,
                   cjm.job_id,
                   (SELECT jp.title FROM job_postings jp WHERE jp.id = cjm.job_id LIMIT 1) AS job_title
            FROM candidates c
            LEFT JOIN candidate_job_matches cjm ON cjm.candidate_id = c.id
            WHERE c.status = 'Absence of Details'
            ORDER BY c.created_at DESC
        """)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            cid, name, email, phone, resume_path, match_score, status, created_at, job_id, job_title = row
            missing = []
            if not name or name.strip().lower() in ('unknown candidate', 'candidate') or name.strip() == '':
                missing.append('name')
            if not email or email.endswith('@bulk-upload.local'):
                missing.append('email')
            if not phone or phone.strip() == '':
                missing.append('phone')

            results.append({
                'id': cid,
                'name': name,
                'email': email,
                'phone': phone or '',
                'resume_path': resume_path,
                'match_score': match_score or 0,
                'status': status,
                'created_at': str(created_at) if created_at else None,
                'job_id': job_id,
                'job_title': job_title or 'N/A',
                'missing_fields': missing,
            })

        return jsonify({'status': 'success', 'data': results, 'total': len(results)}), 200
    except Exception as e:
        logger.error(f"[ADMIN] absence-of-details error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_candidates_bp.route('/candidates', methods=['GET'])
@jwt_required()
@require_admin_role
def get_all_candidates():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, email, phone, resume_path, match_score,
                   shortlist_status, pros, cons, created_at, status
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
            'status': row[10] or row[6] or 'Applied'
        } for row in rows]

        return jsonify({'status': 'success', 'data': candidates}), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_candidates_bp.route('/candidates/<int:candidate_id>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_candidate(candidate_id):
    conn = None
    try:
        admin_email = get_jwt_identity()
        data = request.get_json()

        logger.info(f"[ADMIN ACTION] {admin_email} updating candidate ID: {candidate_id} with data: {list(data.keys())}")

        from psycopg2 import sql as psql
        field_names = []
        values = []

        if 'name' in data:
            field_names.append('name')
            values.append(data['name'])
        if 'email' in data:
            field_names.append('email')
            values.append(data['email'])
        if 'phone' in data:
            field_names.append('phone')
            values.append(data['phone'])
        if 'status' in data:
            field_names.append('status')
            values.append(data['status'])
            field_names.append('shortlist_status')
            values.append(data['status'])
        if 'match_score' in data:
            field_names.append('match_score')
            values.append(data['match_score'])

        if not field_names:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        conn = get_connection()
        cursor = conn.cursor()
        values.append(candidate_id)
        set_clause = psql.SQL(', ').join(
            [psql.SQL("{} = %s").format(psql.Identifier(f)) for f in field_names]
        )
        query = psql.SQL("UPDATE candidates SET {} WHERE id = %s").format(set_clause)
        cursor.execute(query, values)
        conn.commit()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully updated candidate ID: {candidate_id}")

        return jsonify({'status': 'success', 'message': 'Candidate updated successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to update candidate ID {candidate_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_candidates_bp.route('/candidates/<int:candidate_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_candidate(candidate_id):
    try:
        admin_email = get_jwt_identity()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name, email FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()

        if not candidate:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

        candidate_name, candidate_email = candidate[0], candidate[1]
        logger.warning(f"[ADMIN ACTION] {admin_email} deleting candidate ID: {candidate_id} ({candidate_name}, {candidate_email})")

        cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = %s", (candidate_id,))
        cursor.execute("DELETE FROM assessments WHERE candidate_id = %s", (candidate_id,))
        cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
        conn.commit()
        conn.close()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully deleted candidate ID: {candidate_id}")

        return jsonify({'status': 'success', 'message': 'Candidate deleted successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to delete candidate ID {candidate_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_candidates_bp.route('/reset-candidate-status/<int:candidate_id>', methods=['POST'])
@jwt_required()
@require_admin_role
def reset_candidate_status(candidate_id):
    try:
        admin_email = get_jwt_identity()
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name, email FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()

        if not candidate:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

        candidate_name = candidate[0]
        logger.info(f"[ADMIN ACTION] {admin_email} resetting status to 'Applied' for candidate ID: {candidate_id} ({candidate_name})")

        cursor.execute("""
            UPDATE candidates
            SET status = 'Applied', shortlist_status = 'Applied'
            WHERE id = %s
        """, (candidate_id,))
        cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = %s", (candidate_id,))
        conn.commit()
        conn.close()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully reset candidate ID: {candidate_id} to 'Applied'")

        return jsonify({'status': 'success', 'message': 'Candidate status reset to Applied'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to reset candidate ID {candidate_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
