"""
Job Postings & Sectors Routes Module
Handles enhanced job postings with required/preferred skills,
sector management, RBAC, candidate-job matching, and audit logging.
"""

import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import logging
from db_config import get_connection, return_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

jobs_bp = Blueprint('jobs', __name__)


# ============================================================================
#                           RBAC HELPERS
# ============================================================================

ROLE_HIERARCHY = {
    'super_admin': 100,
    'admin': 90,          # Legacy role — treated same as super_admin
    'sector_admin': 70,
    'recruiter': 50,
    'interviewer': 30,
    'proctor': 20,
}


def get_effective_role(claims):
    """Map legacy 'admin' to 'super_admin' and return the effective role."""
    role = claims.get('role', 'interviewer')
    return 'super_admin' if role == 'admin' else role


def has_permission(claims, min_role='recruiter'):
    """Check if the user's role meets the minimum required level."""
    effective = get_effective_role(claims)
    return ROLE_HIERARCHY.get(effective, 0) >= ROLE_HIERARCHY.get(min_role, 0)


def require_role(min_role='recruiter'):
    """Decorator to enforce minimum role."""
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if not has_permission(claims, min_role):
                return jsonify({
                    'status': 'error',
                    'message': f'Access denied. Minimum role required: {min_role}'
                }), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_user_sector_id(claims):
    """Get sector_id from JWT claims (if present)."""
    return claims.get('sector_id')


def audit_log(conn, user_email, action, entity_type=None, entity_id=None, details=None, ip_address=None):
    """Write an entry to the audit_log table."""
    try:
        cursor = conn.cursor()
        # Look up user_id
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        row = cursor.fetchone()
        user_id = row[0] if row else None

        cursor.execute("""
            INSERT INTO audit_log (user_id, user_email, action, entity_type, entity_id, details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, user_email, action, entity_type, entity_id,
            json.dumps(details) if details else None,
            ip_address
        ))
    except Exception as e:
        logger.warning(f"[AUDIT] Failed to write audit log: {e}")


# ============================================================================
#                           SECTORS
# ============================================================================

@jobs_bp.route('/sectors', methods=['GET'])
@jwt_required(optional=True)
def get_sectors():
    """Get all sectors. Public access allowed for job listings filtering."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM sectors ORDER BY name")
        sectors = cursor.fetchall()
        for s in sectors:
            if s.get('created_at'):
                s['created_at'] = s['created_at'].isoformat()
            if s.get('updated_at'):
                s['updated_at'] = s['updated_at'].isoformat()
        return jsonify({'status': 'success', 'data': sectors})
    except Exception as e:
        logger.error(f"[SECTORS] Failed to fetch: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/sectors', methods=['POST'])
@jwt_required()
@require_role('super_admin')
def create_sector():
    """Create a new sector (super admin only)."""
    conn = None
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'status': 'error', 'message': 'Sector name is required'}), 400

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sectors (name, description, email_alias)
            VALUES (%s, %s, %s) RETURNING id
        """, (data['name'], data.get('description', ''), data.get('email_alias', '')))
        sector_id = cursor.fetchone()[0]
        conn.commit()

        admin_email = get_jwt_identity()
        audit_log(conn, admin_email, 'create_sector', 'sector', sector_id,
                  {'name': data['name']}, request.remote_addr)
        conn.commit()

        return jsonify({'status': 'success', 'data': {'id': sector_id}, 'message': 'Sector created'}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[SECTORS] Create failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/sectors/<int:sector_id>', methods=['PUT'])
@jwt_required()
@require_role('super_admin')
def update_sector(sector_id):
    """Update a sector."""
    conn = None
    try:
        data = request.get_json()
        conn = get_connection()
        cursor = conn.cursor()
        from psycopg2 import sql as psql
        update_parts, values = [], []
        allowed_sector_fields = {'name', 'description', 'email_alias'}
        for field in ('name', 'description', 'email_alias'):
            if field in data and field in allowed_sector_fields:
                update_parts.append(psql.SQL("{} = %s").format(psql.Identifier(field)))
                values.append(data[field])
        if not update_parts:
            return jsonify({'status': 'error', 'message': 'Nothing to update'}), 400
        update_parts.append(psql.SQL("updated_at = NOW()"))
        values.append(sector_id)
        query = psql.SQL("UPDATE sectors SET {} WHERE id = %s").format(psql.SQL(', ').join(update_parts))
        cursor.execute(query, values)
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Sector updated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/sectors/<int:sector_id>', methods=['DELETE'])
@jwt_required()
@require_role('super_admin')
def delete_sector(sector_id):
    """Delete a sector."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sectors WHERE id = %s", (sector_id,))
        conn.commit()
        return jsonify({'status': 'success', 'message': 'Sector deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                      ENHANCED JOB POSTINGS
# ============================================================================

@jobs_bp.route('/postings', methods=['GET'])
def get_job_postings():
    """
    Get job postings. Public for candidates (only active), 
    filtered by sector for sector_admins.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if authenticated user with sector restriction
        status_filter = request.args.get('status', 'active')
        sector_filter = request.args.get('sector_id')

        query = "SELECT j.*, s.name as sector_name FROM job_descriptions j LEFT JOIN sectors s ON j.sector_id = s.id WHERE 1=1"
        params = []

        if status_filter and status_filter != 'all':
            query += " AND j.status = %s"
            params.append(status_filter)

        if sector_filter:
            query += " AND j.sector_id = %s"
            params.append(int(sector_filter))

        query += " ORDER BY j.created_at DESC"
        cursor.execute(query, params)
        jobs = cursor.fetchall()

        for job in jobs:
            for ts_field in ('created_at', 'updated_at', 'closes_at'):
                if job.get(ts_field):
                    job[ts_field] = job[ts_field].isoformat()
            # Parse skills into arrays for frontend
            job['required_skills_list'] = _parse_skills(job.get('required_skills', ''))
            job['preferred_skills_list'] = _parse_skills(job.get('preferred_skills', ''))

        return jsonify({'status': 'success', 'data': jobs})
    except Exception as e:
        logger.error(f"[JOBS] Failed to fetch postings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/postings', methods=['POST'])
@jwt_required()
@require_role('recruiter')
def create_job_posting():
    """
    Create a job posting with required + preferred skills.
    Enforces that at least required_skills are provided.
    """
    conn = None
    try:
        data = request.get_json()
        if not data or not data.get('title'):
            return jsonify({'status': 'error', 'message': 'Job title is required'}), 400

        # Enforce skill entry
        required_skills = data.get('required_skills', '')
        if not required_skills or not required_skills.strip():
            return jsonify({
                'status': 'error',
                'message': 'Required skills must be specified for the job posting'
            }), 400

        admin_email = get_jwt_identity()
        conn = get_connection()
        cursor = conn.cursor()

        # Get creator's user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (admin_email,))
        creator_row = cursor.fetchone()
        creator_id = creator_row[0] if creator_row else None

        cursor.execute("""
            INSERT INTO job_descriptions 
            (title, description, required_skills, preferred_skills, min_experience, max_experience,
             department, location, sector_id, status, employment_type, experience_level,
             salary_range, closes_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['title'],
            data.get('description', ''),
            required_skills,
            data.get('preferred_skills', ''),
            data.get('min_experience', 0),
            data.get('max_experience'),
            data.get('department', ''),
            data.get('location', ''),
            data.get('sector_id'),
            data.get('status', 'active'),
            data.get('employment_type', 'full-time'),
            data.get('experience_level', 'mid'),
            data.get('salary_range', ''),
            data.get('closes_at'),
            creator_id
        ))

        job_id = cursor.fetchone()[0]
        conn.commit()

        # Audit
        audit_log(conn, admin_email, 'create_job_posting', 'job_posting', job_id,
                  {'title': data['title'], 'sector_id': data.get('sector_id')},
                  request.remote_addr)
        conn.commit()

        logger.info(f"[JOBS] {admin_email} created job posting #{job_id}: {data['title']}")
        return jsonify({'status': 'success', 'data': {'id': job_id}, 'message': 'Job posting created'}), 201
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[JOBS] Create failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/postings/<int:job_id>', methods=['PUT'])
@jwt_required()
@require_role('recruiter')
def update_job_posting(job_id):
    """Update a job posting."""
    conn = None
    try:
        data = request.get_json()
        conn = get_connection()
        cursor = conn.cursor()

        allowed_fields = [
            'title', 'description', 'required_skills', 'preferred_skills',
            'min_experience', 'max_experience', 'department', 'location',
            'sector_id', 'status', 'employment_type', 'experience_level',
            'salary_range', 'closes_at'
        ]
        allowed_set = set(allowed_fields)
        from psycopg2 import sql as psql
        update_parts, values = [], []
        for field in allowed_fields:
            if field in data and field in allowed_set:
                update_parts.append(psql.SQL("{} = %s").format(psql.Identifier(field)))
                values.append(data[field])
        if not update_parts:
            return jsonify({'status': 'error', 'message': 'Nothing to update'}), 400

        update_parts.append(psql.SQL("updated_at = NOW()"))
        values.append(job_id)
        query = psql.SQL("UPDATE job_descriptions SET {} WHERE id = %s").format(psql.SQL(', ').join(update_parts))
        cursor.execute(query, values)
        conn.commit()

        admin_email = get_jwt_identity()
        audit_log(conn, admin_email, 'update_job_posting', 'job_posting', job_id,
                  {'updated_fields': list(data.keys())}, request.remote_addr)
        conn.commit()

        return jsonify({'status': 'success', 'message': 'Job posting updated'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/postings/<int:job_id>', methods=['DELETE'])
@jwt_required()
@require_role('recruiter')
def delete_job_posting(job_id):
    """Permanently delete a job posting."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Remove related candidate-job matches first
        cursor.execute("DELETE FROM candidate_job_matches WHERE job_id = %s", (job_id,))
        # Permanently delete the job posting
        cursor.execute("DELETE FROM job_descriptions WHERE id = %s", (job_id,))
        conn.commit()

        admin_email = get_jwt_identity()
        audit_log(conn, admin_email, 'delete_job_posting', 'job_posting', job_id,
                  None, request.remote_addr)
        conn.commit()

        return jsonify({'status': 'success', 'message': 'Job posting deleted'})
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/postings/<int:job_id>', methods=['GET'])
def get_job_posting_detail(job_id):
    """Get a single job posting by ID."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT j.*, s.name as sector_name 
            FROM job_descriptions j 
            LEFT JOIN sectors s ON j.sector_id = s.id 
            WHERE j.id = %s
        """, (job_id,))
        job = cursor.fetchone()
        if not job:
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404
        for ts_field in ('created_at', 'updated_at', 'closes_at'):
            if job.get(ts_field):
                job[ts_field] = job[ts_field].isoformat()
        job['required_skills_list'] = _parse_skills(job.get('required_skills', ''))
        job['preferred_skills_list'] = _parse_skills(job.get('preferred_skills', ''))
        return jsonify({'status': 'success', 'data': job})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                  CANDIDATE-JOB MATCHING
# ============================================================================

@jobs_bp.route('/match-candidate', methods=['POST'])
@jwt_required()
@require_role('recruiter')
def match_candidate_to_jobs_endpoint():
    """
    Trigger AI matching for a specific candidate against all active jobs.
    Body: { "candidate_id": 5 }
    """
    conn = None
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        if not candidate_id:
            return jsonify({'status': 'error', 'message': 'candidate_id is required'}), 400

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get candidate
        cursor.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cursor.fetchone()
        if not candidate:
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

        # Get active jobs
        cursor.execute("SELECT * FROM job_descriptions WHERE status = 'active'")
        jobs = cursor.fetchall()
        if not jobs:
            return jsonify({'status': 'error', 'message': 'No active job postings to match against'}), 404

        # Parse candidate skills
        skills = _parse_skills(candidate.get('parsed_skills') or candidate.get('parsed_skills_json') or '[]')
        experience = candidate.get('years_experience') or 0
        education = candidate.get('education') or ''

        # Read resume text
        resume_text = ''
        resume_path = candidate.get('resume_path', '')
        if resume_path:
            try:
                import os
                if os.path.exists(resume_path):
                    if resume_path.endswith('.pdf'):
                        from PyPDF2 import PdfReader
                        with open(resume_path, 'rb') as f:
                            pdf = PdfReader(f)
                            resume_text = " ".join([p.extract_text() for p in pdf.pages])
                    else:
                        from docx import Document
                        doc = Document(resume_path)
                        resume_text = " ".join([p.text for p in doc.paragraphs])
            except Exception as e:
                logger.warning(f"[MATCH] Could not read resume for candidate {candidate_id}: {e}")

        # Run matching
        from job_matcher import match_candidate_to_jobs
        matches = match_candidate_to_jobs(skills, experience, education, resume_text, jobs)

        # Save matches to DB
        for m in matches:
            cursor.execute("""
                INSERT INTO candidate_job_matches 
                (candidate_id, job_id, match_score, skill_match_score, experience_match_score, ai_reasoning)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (candidate_id, job_id) 
                DO UPDATE SET match_score = EXCLUDED.match_score,
                             skill_match_score = EXCLUDED.skill_match_score,
                             experience_match_score = EXCLUDED.experience_match_score,
                             ai_reasoning = EXCLUDED.ai_reasoning,
                             matched_at = NOW()
            """, (
                candidate_id, m['job_id'], m['match_score'],
                m['skill_match_score'], m['experience_match_score'],
                m.get('ai_reasoning', '')
            ))

        # Update best match on candidate
        if matches:
            best = matches[0]
            cursor.execute("""
                UPDATE candidates 
                SET best_match_job_id = %s, match_score = %s 
                WHERE id = %s
            """, (best['job_id'], best['match_score'], candidate_id))

        conn.commit()

        admin_email = get_jwt_identity()
        audit_log(conn, admin_email, 'match_candidate', 'candidate', candidate_id,
                  {'matches_count': len(matches), 'best_job_id': matches[0]['job_id'] if matches else None},
                  request.remote_addr)
        conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Matched candidate to {len(matches)} job(s)',
            'data': {'matches': matches}
        })
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"[MATCH] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/matches/<int:candidate_id>', methods=['GET'])
@jwt_required()
def get_candidate_matches(candidate_id):
    """Get all job matches for a candidate."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT m.*, j.title as job_title, j.department, j.location, j.experience_level,
                   j.required_skills, j.preferred_skills
            FROM candidate_job_matches m
            JOIN job_descriptions j ON m.job_id = j.id
            WHERE m.candidate_id = %s
            ORDER BY m.match_score DESC
        """, (candidate_id,))
        matches = cursor.fetchall()
        for m in matches:
            if m.get('matched_at'):
                m['matched_at'] = m['matched_at'].isoformat()
            if m.get('reviewed_at'):
                m['reviewed_at'] = m['reviewed_at'].isoformat()
        return jsonify({'status': 'success', 'data': matches})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@jobs_bp.route('/postings/<int:job_id>/candidates', methods=['GET'])
@jwt_required()
@require_role('recruiter')
def get_job_candidates(job_id):
    """Get all matched candidates for a job posting, ranked by score."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT m.*, c.name, c.email, c.phone, c.status as candidate_status,
                   c.parsed_skills, c.years_experience, c.education
            FROM candidate_job_matches m
            JOIN candidates c ON m.candidate_id = c.id
            WHERE m.job_id = %s
            ORDER BY m.match_score DESC
        """, (job_id,))
        candidates = cursor.fetchall()
        for c in candidates:
            if c.get('matched_at'):
                c['matched_at'] = c['matched_at'].isoformat()
        return jsonify({'status': 'success', 'data': candidates})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                           AUDIT LOG
# ============================================================================

@jobs_bp.route('/audit-log', methods=['GET'])
@jwt_required()
@require_role('super_admin')
def get_audit_log():
    """Get recent audit log entries."""
    conn = None
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM audit_log 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        logs = cursor.fetchall()
        for log in logs:
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
        return jsonify({'status': 'success', 'data': logs})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                           HELPERS
# ============================================================================

def _parse_skills(skills_value) -> list:
    """Parse skills from JSON string, JSON array, or comma-separated string."""
    if not skills_value:
        return []
    if isinstance(skills_value, list):
        return skills_value
    import contextlib
    with contextlib.suppress(json.JSONDecodeError, TypeError):
        parsed = json.loads(str(skills_value))
        if isinstance(parsed, list):
            return parsed
    return [s.strip() for s in str(skills_value).split(',') if s.strip()]
