"""
Admin candidate management routes — view, update, delete, and reset candidates.
"""

import logging
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db_config import db_connection, get_connection, return_connection
from admin_middleware import require_admin_role
from auth import validate_email
from storage_config import get_upload_root

logger = logging.getLogger(__name__)

admin_candidates_bp = Blueprint('admin_candidates', __name__)

_CANDIDATE_STATUSES = {
    'applied', 'absence_of_details', 'pending', 'under_review',
    'rejected', 'completed', 'hired',
}
_SHORTLIST_STATUSES = {'High Match', 'Potential', 'Reject'}


def _remove_resume_file(resume_path):
    if not resume_path:
        return
    upload_root = os.path.realpath(get_upload_root())
    candidate_path = os.path.realpath(resume_path)
    try:
        within_uploads = os.path.commonpath([upload_root, candidate_path]) == upload_root
    except ValueError:
        within_uploads = False
    if within_uploads and os.path.isfile(candidate_path):
        try:
            os.remove(candidate_path)
        except OSError:
            logger.warning("Failed to remove candidate resume %s", candidate_path, exc_info=True)


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
                   c.best_match_job_id AS job_id,
                   jd.title AS job_title
            FROM candidates c
            LEFT JOIN job_descriptions jd ON jd.id = c.best_match_job_id
            WHERE c.status IN ('absence_of_details', 'Absence of Details')
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
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'status': 'error', 'message': 'A JSON object is required'}), 400

        unknown_fields = set(data) - {
            'name', 'email', 'phone', 'status', 'shortlist_status', 'match_score'
        }
        if unknown_fields:
            return jsonify({'status': 'error', 'message': 'Unsupported candidate fields'}), 400

        logger.info(f"[ADMIN ACTION] {admin_email} updating candidate ID: {candidate_id} with data: {list(data.keys())}")

        from psycopg2 import sql as psql
        field_names = []
        values = []

        if 'name' in data:
            if not isinstance(data['name'], str) or not data['name'].strip():
                return jsonify({'status': 'error', 'message': 'Name must be a non-empty string'}), 400
            if len(data['name'].strip()) > 120:
                return jsonify({'status': 'error', 'message': 'Name is too long'}), 400
            field_names.append('name')
            values.append(data['name'].strip())
        if 'email' in data:
            if not isinstance(data['email'], str) or not validate_email(data['email'].strip().lower()):
                return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
            if len(data['email'].strip()) > 254:
                return jsonify({'status': 'error', 'message': 'Email is too long'}), 400
            field_names.append('email')
            values.append(data['email'].strip().lower())
        if 'phone' in data:
            if not isinstance(data['phone'], str):
                return jsonify({'status': 'error', 'message': 'Phone must be a string'}), 400
            if len(data['phone'].strip()) > 50:
                return jsonify({'status': 'error', 'message': 'Phone is too long'}), 400
            field_names.append('phone')
            values.append(data['phone'].strip())
        if 'status' in data:
            if not isinstance(data['status'], str):
                return jsonify({'status': 'error', 'message': 'Status must be a string'}), 400
            normalized_status = data['status'].strip().lower().replace(' ', '_')
            if normalized_status not in _CANDIDATE_STATUSES:
                return jsonify({'status': 'error', 'message': 'Invalid candidate status'}), 400
            field_names.append('status')
            values.append(normalized_status)
        if 'shortlist_status' in data:
            if data['shortlist_status'] not in _SHORTLIST_STATUSES:
                return jsonify({'status': 'error', 'message': 'Invalid shortlist status'}), 400
            field_names.append('shortlist_status')
            values.append(data['shortlist_status'])
        if 'match_score' in data:
            if isinstance(data['match_score'], bool) or not isinstance(data['match_score'], (int, float)):
                return jsonify({'status': 'error', 'message': 'Match score must be a number'}), 400
            if not 0 <= data['match_score'] <= 100:
                return jsonify({'status': 'error', 'message': 'Match score must be between 0 and 100'}), 400
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
        query = psql.SQL(
            "UPDATE candidates SET {}, updated_at = CURRENT_TIMESTAMP WHERE id = %s"
        ).format(set_clause)
        cursor.execute(query, values)
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404
        conn.commit()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully updated candidate ID: {candidate_id}")

        return jsonify({'status': 'success', 'message': 'Candidate updated successfully'}), 200
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("[ADMIN ERROR] Failed to update candidate %s", candidate_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_candidates_bp.route('/candidates/<int:candidate_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_candidate(candidate_id):
    try:
        admin_id = get_jwt_identity()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, email, resume_path FROM candidates WHERE id = %s FOR UPDATE",
                (candidate_id,),
            )
            candidate = cursor.fetchone()
            if not candidate:
                return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

            candidate_name, candidate_email, resume_path = candidate
            logger.warning(
                "[ADMIN ACTION] %s deleting candidate ID %s (%s, %s)",
                admin_id, candidate_id, candidate_name, candidate_email,
            )
            cursor.execute("DELETE FROM candidates WHERE id = %s", (candidate_id,))
            conn.commit()

        _remove_resume_file(resume_path)

        logger.info("[ADMIN ACTION] %s deleted candidate ID %s", admin_id, candidate_id)

        return jsonify({'status': 'success', 'message': 'Candidate deleted successfully'}), 200
    except Exception:
        logger.exception("[ADMIN ERROR] Failed to delete candidate ID %s", candidate_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_candidates_bp.route('/reset-candidate-status/<int:candidate_id>', methods=['POST'])
@jwt_required()
@require_admin_role
def reset_candidate_status(candidate_id):
    try:
        admin_id = get_jwt_identity()
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM candidates WHERE id = %s FOR UPDATE",
                (candidate_id,),
            )
            candidate = cursor.fetchone()
            if not candidate:
                return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

            logger.info(
                "[ADMIN ACTION] %s resetting candidate ID %s (%s)",
                admin_id, candidate_id, candidate[0],
            )
            cursor.execute("DELETE FROM assessments WHERE candidate_id = %s", (candidate_id,))
            cursor.execute("DELETE FROM scheduled_assessments WHERE candidate_id = %s", (candidate_id,))
            cursor.execute("""
                UPDATE candidates
                SET status = 'applied', shortlist_status = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (candidate_id,))
            conn.commit()

        logger.info("[ADMIN ACTION] %s reset candidate ID %s to applied", admin_id, candidate_id)

        return jsonify({'status': 'success', 'message': 'Candidate status reset to Applied'}), 200
    except Exception:
        logger.exception("[ADMIN ERROR] Failed to reset candidate ID %s", candidate_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
