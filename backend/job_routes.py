"""
Job Postings & Sectors Routes Module
Handles enhanced job postings with required/preferred skills,
sector management, RBAC, candidate-job matching, and audit logging.
"""

import json
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging
import psycopg2

from db_config import db_connection
from storage_config import get_upload_root
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

GLOBAL_JOB_ROLES = {'super_admin', 'admin'}
SECTOR_JOB_ROLES = {'sector_admin', 'recruiter'}
JOB_STATUSES = {'active', 'paused', 'closed', 'draft'}
EMPLOYMENT_TYPES = {'full-time', 'part-time', 'contract', 'internship'}
EXPERIENCE_LEVELS = {'junior', 'mid', 'senior', 'lead', 'principal'}


class ConcurrentJobChangeError(RuntimeError):
    """Raised when matching inputs change while scores are being calculated."""


def get_effective_role(claims):
    """Map legacy 'admin' to 'super_admin' and return the effective role."""
    role = claims.get('role', 'interviewer')
    return 'super_admin' if role == 'admin' else role


def has_permission(claims, min_role='recruiter'):
    """Check if the user's role meets the minimum required level."""
    effective = get_effective_role(claims)
    required_level = ROLE_HIERARCHY.get(min_role)
    return (
        required_level is not None
        and ROLE_HIERARCHY.get(effective, 0) >= required_level
    )


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
    value = claims.get('sector_id')
    if value is None:
        return None
    try:
        sector_id = int(value)
    except (TypeError, ValueError):
        return None
    return sector_id if sector_id > 0 else None


def audit_log(conn, user_identity, action, entity_type=None, entity_id=None, details=None, ip_address=None):
    """Write an entry to the audit_log table. user_identity is the JWT identity (user_id as string)."""
    cursor = conn.cursor()
    try:
        user_id = int(user_identity) if user_identity else None
    except (TypeError, ValueError) as exc:
        raise ValueError("JWT identity must be a numeric user id") from exc
    user_email = None
    if user_id:
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_email = row[0] if row else None

    cursor.execute("""
        INSERT INTO audit_log (user_id, user_email, action, entity_type, entity_id, details, ip_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        user_id, user_email, action, entity_type, entity_id,
        json.dumps(details) if details is not None else None,
        ip_address
    ))


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def _positive_int(value, field_name):
    if isinstance(value, bool) or (
        isinstance(value, float) and not value.is_integer()
    ):
        raise ValueError(f'{field_name} must be an integer')
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} must be an integer') from exc
    if parsed <= 0:
        raise ValueError(f'{field_name} must be greater than zero')
    return parsed


def _non_negative_int(value, field_name, maximum=80):
    if isinstance(value, bool) or (
        isinstance(value, float) and not value.is_integer()
    ):
        raise ValueError(f'{field_name} must be an integer')
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{field_name} must be an integer') from exc
    if not 0 <= parsed <= maximum:
        raise ValueError(f'{field_name} must be between 0 and {maximum}')
    return parsed


def _clean_text(value, field_name, maximum, required=False):
    if value is None:
        if required:
            raise ValueError(f'{field_name} is required')
        return ''
    if not isinstance(value, str):
        raise ValueError(f'{field_name} must be a string')
    cleaned = value.strip()
    if required and not cleaned:
        raise ValueError(f'{field_name} is required')
    if len(cleaned) > maximum:
        raise ValueError(f'{field_name} cannot exceed {maximum} characters')
    return cleaned


def _normalise_skills(value, field_name, required=False):
    skills = _parse_skills(value)
    cleaned = list(dict.fromkeys(
        str(skill).strip() for skill in skills if str(skill).strip()
    ))
    if required and not cleaned:
        raise ValueError(f'{field_name} must contain at least one skill')
    if len(cleaned) > 100:
        raise ValueError(f'{field_name} cannot contain more than 100 skills')
    if any(len(skill) > 100 for skill in cleaned):
        raise ValueError(f'Each {field_name} entry must be 100 characters or fewer')
    return json.dumps(cleaned)


def _validate_job_data(data, current=None, partial=False):
    if not isinstance(data, dict):
        raise ValueError('A JSON request body is required')
    current = dict(current or {})
    result = {}

    text_fields = {
        'title': (200, True),
        'description': (20_000, False),
        'department': (200, False),
        'location': (300, False),
        'salary_range': (200, False),
        'role_complexity_level': (50, False),
    }
    for field, (maximum, required) in text_fields.items():
        if field in data or (not partial and required):
            field_required = required or field == 'role_complexity_level'
            result[field] = _clean_text(
                data.get(field), field, maximum, required=field_required
            )
            if field == 'role_complexity_level':
                result[field] = result[field].lower()

    if 'required_skills' in data or not partial:
        result['required_skills'] = _normalise_skills(
            data.get('required_skills'), 'required_skills', required=True
        )
    if 'preferred_skills' in data:
        result['preferred_skills'] = _normalise_skills(
            data.get('preferred_skills'), 'preferred_skills'
        )
    elif not partial:
        result['preferred_skills'] = json.dumps([])

    for field in ('min_experience', 'max_experience'):
        if field in data:
            result[field] = (
                None if data[field] is None and field == 'max_experience'
                else _non_negative_int(data[field], field)
            )
        elif not partial and field == 'min_experience':
            result[field] = 0

    merged_min = result.get('min_experience', current.get('min_experience') or 0)
    merged_max = result.get('max_experience', current.get('max_experience'))
    if merged_max is not None and int(merged_max) < int(merged_min):
        raise ValueError('max_experience cannot be less than min_experience')

    enum_fields = {
        'status': (JOB_STATUSES, 'active'),
        'employment_type': (EMPLOYMENT_TYPES, 'full-time'),
        'experience_level': (EXPERIENCE_LEVELS, 'mid'),
    }
    for field, (allowed, default) in enum_fields.items():
        if field in data or not partial:
            value = str(data.get(field, default)).strip().lower()
            if value not in allowed:
                raise ValueError(
                    f'{field} must be one of: {", ".join(sorted(allowed))}'
                )
            result[field] = value

    if 'sector_id' in data:
        result['sector_id'] = (
            None if data['sector_id'] is None
            else _positive_int(data['sector_id'], 'sector_id')
        )
    if 'closes_at' in data:
        value = data['closes_at']
        if value in (None, ''):
            result['closes_at'] = None
        elif not isinstance(value, str):
            raise ValueError('closes_at must be an ISO datetime string')
        else:
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError as exc:
                raise ValueError('closes_at must be an ISO datetime string') from exc
            result['closes_at'] = value

    merged_status = result.get('status', current.get('status', 'active'))
    merged_closes_at = result.get('closes_at', current.get('closes_at'))
    if merged_status == 'active' and merged_closes_at:
        closes_at = _parse_datetime(merged_closes_at, 'closes_at')
        now = datetime.now(closes_at.tzinfo) if closes_at.tzinfo else datetime.now()
        if closes_at <= now:
            raise ValueError('An active job must have a future closes_at value')

    return result


def _parse_datetime(value, field_name):
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValueError(f'{field_name} must be an ISO datetime string')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError(f'{field_name} must be an ISO datetime string') from exc


def _is_job_open(job):
    if job.get('status') != 'active':
        return False
    closes_at = job.get('closes_at')
    if not closes_at:
        return True
    try:
        closes_at = _parse_datetime(closes_at, 'closes_at')
    except ValueError:
        logger.warning("[JOBS] Job %s has invalid closes_at", job.get('id'))
        return False
    now = datetime.now(closes_at.tzinfo) if closes_at.tzinfo else datetime.now()
    return closes_at > now


def _scoped_sector_or_error(claims):
    role = get_effective_role(claims)
    if role in GLOBAL_JOB_ROLES:
        return None
    sector_id = get_user_sector_id(claims)
    if role in SECTOR_JOB_ROLES and sector_id is None:
        raise PermissionError('No sector assigned to your account')
    return sector_id


def _assert_sector_access(entity_sector_id, claims, entity_name):
    sector_id = _scoped_sector_or_error(claims)
    if sector_id is not None and entity_sector_id != sector_id:
        raise PermissionError(f'You can only access {entity_name} in your own sector')


def _extract_resume_text(resume_path, candidate_id):
    """Extract a bounded resume excerpt without allowing arbitrary file reads."""
    if not resume_path:
        return ''
    try:
        path = Path(resume_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
        path = path.resolve(strict=True)
        allowed_roots = {get_upload_root()}
        if not any(path == root or root in path.parents for root in allowed_roots):
            logger.warning(
                "[MATCH] Refusing resume path outside upload roots for candidate %s",
                candidate_id,
            )
            return ''
        if path.stat().st_size > 10 * 1024 * 1024:
            logger.warning("[MATCH] Resume is too large for candidate %s", candidate_id)
            return ''

        extension = path.suffix.lower()
        if extension == '.pdf':
            from PyPDF2 import PdfReader
            with path.open('rb') as file_handle:
                pdf = PdfReader(file_handle)
                text = ' '.join(page.extract_text() or '' for page in pdf.pages)
        elif extension == '.docx':
            from docx import Document
            document = Document(str(path))
            text = ' '.join(paragraph.text for paragraph in document.paragraphs)
        else:
            logger.warning(
                "[MATCH] Unsupported resume extension %s for candidate %s",
                extension,
                candidate_id,
            )
            return ''
        return ' '.join(text.split())[:20_000]
    except Exception:
        logger.exception("[MATCH] Could not read resume for candidate %s", candidate_id)
        return ''


# ============================================================================
#                           SECTORS
# ============================================================================

@jobs_bp.route('/sectors', methods=['GET'])
@jwt_required(optional=True)
def get_sectors():
    """Get all sectors. Public access allowed for job listings filtering."""
    try:
        with db_connection() as conn:
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
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/sectors', methods=['POST'])
@jwt_required()
@require_role('super_admin')
def create_sector():
    """Create a new sector (super admin only)."""
    try:
        data = _json_body()
        if data is None:
            raise ValueError('A JSON request body is required')
        name = _clean_text(data.get('name'), 'name', 200, required=True)
        description = _clean_text(data.get('description'), 'description', 5000)
        email_alias = _clean_text(data.get('email_alias'), 'email_alias', 320) or None

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sectors (name, description, email_alias)
                VALUES (%s, %s, %s) RETURNING id
            """, (name, description, email_alias))
            sector_id = cursor.fetchone()[0]
            audit_log(
                conn, get_jwt_identity(), 'create_sector', 'sector', sector_id,
                {'name': name}, request.remote_addr,
            )
            conn.commit()

        return jsonify({'status': 'success', 'data': {'id': sector_id}, 'message': 'Sector created'}), 201
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except psycopg2.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Sector name or email alias already exists'}), 409
    except Exception:
        logger.exception("[SECTORS] Create failed")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/sectors/<int:sector_id>', methods=['PUT'])
@jwt_required()
@require_role('super_admin')
def update_sector(sector_id):
    """Update a sector."""
    try:
        data = _json_body()
        if data is None:
            raise ValueError('A JSON request body is required')
        from psycopg2 import sql as psql
        update_parts, values = [], []
        for field in ('name', 'description', 'email_alias'):
            if field in data:
                maximum = 320 if field == 'email_alias' else (200 if field == 'name' else 5000)
                value = _clean_text(
                    data[field], field, maximum, required=field == 'name'
                )
                update_parts.append(psql.SQL("{} = %s").format(psql.Identifier(field)))
                values.append(value or None if field == 'email_alias' else value)
        if not update_parts:
            return jsonify({'status': 'error', 'message': 'Nothing to update'}), 400
        update_parts.append(psql.SQL("updated_at = NOW()"))
        values.append(sector_id)
        query = psql.SQL("UPDATE sectors SET {} WHERE id = %s RETURNING id").format(
            psql.SQL(', ').join(update_parts)
        )
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Sector not found'}), 404
            audit_log(
                conn, get_jwt_identity(), 'update_sector', 'sector', sector_id,
                {'updated_fields': sorted(data)}, request.remote_addr,
            )
            conn.commit()
        return jsonify({'status': 'success', 'message': 'Sector updated'})
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except psycopg2.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Sector name or email alias already exists'}), 409
    except Exception:
        logger.exception("[SECTORS] Update failed")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/sectors/<int:sector_id>', methods=['DELETE'])
@jwt_required()
@require_role('super_admin')
def delete_sector(sector_id):
    """Delete a sector."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sectors WHERE id = %s RETURNING name", (sector_id,))
            deleted = cursor.fetchone()
            if not deleted:
                return jsonify({'status': 'error', 'message': 'Sector not found'}), 404
            audit_log(
                conn, get_jwt_identity(), 'delete_sector', 'sector', sector_id,
                {'name': deleted[0]}, request.remote_addr,
            )
            conn.commit()
        return jsonify({'status': 'success', 'message': 'Sector deleted'})
    except Exception:
        logger.exception("[SECTORS] Delete failed")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
#                      ENHANCED JOB POSTINGS
# ============================================================================

@jobs_bp.route('/postings', methods=['GET'])
@jwt_required(optional=True)
def get_job_postings():
    """
    Get job postings. Public for candidates (only active), 
    filtered by sector for sector_admins.
    """
    try:
        caller_claims = get_jwt() or {}
        caller_role = get_effective_role(caller_claims) if caller_claims else None
        is_job_staff = caller_role in GLOBAL_JOB_ROLES | SECTOR_JOB_ROLES

        status_filter = request.args.get('status', 'active')
        sector_filter = request.args.get('sector_id')

        if not is_job_staff:
            status_filter = 'active'
        elif status_filter != 'all' and status_filter not in JOB_STATUSES:
            raise ValueError(
                f'status must be one of: all, {", ".join(sorted(JOB_STATUSES))}'
            )

        if caller_role in SECTOR_JOB_ROLES:
            scoped_sector = _scoped_sector_or_error(caller_claims)
            if sector_filter is not None and _positive_int(sector_filter, 'sector_id') != scoped_sector:
                raise PermissionError('You can only view jobs in your own sector')
            sector_filter = scoped_sector
        elif sector_filter is not None:
            sector_filter = _positive_int(sector_filter, 'sector_id')

        query = "SELECT j.*, s.name as sector_name FROM job_descriptions j LEFT JOIN sectors s ON j.sector_id = s.id WHERE 1=1"
        params = []

        if status_filter and status_filter != 'all':
            query += " AND j.status = %s"
            params.append(status_filter)
        if not is_job_staff:
            query += " AND (j.closes_at IS NULL OR j.closes_at > CURRENT_TIMESTAMP)"

        if sector_filter:
            query += " AND j.sector_id = %s"
            params.append(sector_filter)

        query += " ORDER BY j.created_at DESC"
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            jobs = cursor.fetchall()

        for job in jobs:
            for ts_field in ('created_at', 'updated_at', 'closes_at'):
                if job.get(ts_field):
                    job[ts_field] = job[ts_field].isoformat()
            # Parse skills into arrays for frontend
            job['required_skills_list'] = _parse_skills(job.get('required_skills', ''))
            job['preferred_skills_list'] = _parse_skills(job.get('preferred_skills', ''))
            job['required_skills'] = ', '.join(job['required_skills_list'])
            job['preferred_skills'] = ', '.join(job['preferred_skills_list'])

        return jsonify({'status': 'success', 'data': jobs})
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except Exception:
        logger.exception("[JOBS] Failed to fetch postings")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/postings', methods=['POST'])
@jwt_required()
@require_role('recruiter')
def create_job_posting():
    """
    Create a job posting with required + preferred skills.
    Enforces that at least required_skills are provided.
    """
    try:
        data = _validate_job_data(_json_body(), partial=False)
        claims = get_jwt()
        user_identity = get_jwt_identity()
        creator_id = _positive_int(user_identity, 'JWT identity')
        scoped_sector = _scoped_sector_or_error(claims)
        if scoped_sector is not None:
            requested_sector = data.get('sector_id')
            if requested_sector is not None and requested_sector != scoped_sector:
                raise PermissionError('You can only create jobs in your own sector')
            data['sector_id'] = scoped_sector

        with db_connection() as conn:
            cursor = conn.cursor()
            if data.get('sector_id') is not None:
                cursor.execute("SELECT 1 FROM sectors WHERE id = %s", (data['sector_id'],))
                if not cursor.fetchone():
                    raise ValueError('sector_id does not reference an existing sector')

            cursor.execute("""
                INSERT INTO job_descriptions
                (title, description, required_skills, preferred_skills, min_experience, max_experience,
                 department, location, sector_id, status, employment_type, experience_level,
                 salary_range, closes_at, created_by, role_complexity_level)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['title'], data.get('description', ''), data['required_skills'],
                data.get('preferred_skills', json.dumps([])), data.get('min_experience', 0),
                data.get('max_experience'), data.get('department', ''), data.get('location', ''),
                data.get('sector_id'), data.get('status', 'active'),
                data.get('employment_type', 'full-time'), data.get('experience_level', 'mid'),
                data.get('salary_range', ''), data.get('closes_at'), creator_id,
                data.get('role_complexity_level', 'intermediate'),
            ))
            job_id = cursor.fetchone()[0]
            audit_log(
                conn, user_identity, 'create_job_posting', 'job_posting', job_id,
                {'title': data['title'], 'sector_id': data.get('sector_id')},
                request.remote_addr,
            )
            conn.commit()

        logger.info(
            "[JOBS] user:%s created job posting #%s: %s",
            creator_id,
            job_id,
            data['title'],
        )
        return jsonify({'status': 'success', 'data': {'id': job_id}, 'message': 'Job posting created'}), 201
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except psycopg2.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Job posting conflicts with existing data'}), 409
    except Exception:
        logger.exception("[JOBS] Create failed")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/postings/<int:job_id>', methods=['PUT'])
@jwt_required()
@require_role('recruiter')
def update_job_posting(job_id):
    """Update a job posting."""
    try:
        raw_data = _json_body()
        if raw_data is None:
            raise ValueError('A JSON request body is required')
        claims = get_jwt()
        from psycopg2 import sql as psql
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT * FROM job_descriptions WHERE id = %s FOR UPDATE",
                (job_id,),
            )
            current = cursor.fetchone()
            if not current:
                return jsonify({'status': 'error', 'message': 'Job not found'}), 404
            _assert_sector_access(current.get('sector_id'), claims, 'jobs')

            data = _validate_job_data(raw_data, current=current, partial=True)
            scoped_sector = _scoped_sector_or_error(claims)
            if scoped_sector is not None and data.get('sector_id', scoped_sector) != scoped_sector:
                raise PermissionError('You cannot move a job outside your sector')
            if not data:
                return jsonify({'status': 'error', 'message': 'Nothing to update'}), 400
            if data.get('sector_id') is not None:
                cursor.execute("SELECT 1 FROM sectors WHERE id = %s", (data['sector_id'],))
                if not cursor.fetchone():
                    raise ValueError('sector_id does not reference an existing sector')

            update_parts = [
                psql.SQL("{} = %s").format(psql.Identifier(field)) for field in data
            ]
            values = list(data.values())
            update_parts.append(psql.SQL("updated_at = NOW()"))
            values.append(job_id)
            query = psql.SQL(
                "UPDATE job_descriptions SET {} WHERE id = %s RETURNING id"
            ).format(psql.SQL(', ').join(update_parts))
            cursor.execute(query, values)
            if not cursor.fetchone():
                return jsonify({'status': 'error', 'message': 'Job not found'}), 404
            audit_log(
                conn, get_jwt_identity(), 'update_job_posting', 'job_posting', job_id,
                {'updated_fields': sorted(data)}, request.remote_addr,
            )
            conn.commit()

        return jsonify({'status': 'success', 'message': 'Job posting updated'})
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except psycopg2.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Job update conflicts with existing data'}), 409
    except Exception:
        logger.exception("[JOBS] Update failed for job %s", job_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/postings/<int:job_id>', methods=['DELETE'])
@jwt_required()
@require_role('recruiter')
def delete_job_posting(job_id):
    """Permanently delete a job posting."""
    try:
        claims = get_jwt()
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT id, title, sector_id FROM job_descriptions WHERE id = %s FOR UPDATE",
                (job_id,),
            )
            job = cursor.fetchone()
            if not job:
                return jsonify({'status': 'error', 'message': 'Job not found'}), 404
            _assert_sector_access(job.get('sector_id'), claims, 'jobs')
            cursor.execute("DELETE FROM job_descriptions WHERE id = %s", (job_id,))
            audit_log(
                conn, get_jwt_identity(), 'delete_job_posting', 'job_posting', job_id,
                {'title': job.get('title')}, request.remote_addr,
            )
            conn.commit()

        return jsonify({'status': 'success', 'message': 'Job posting deleted'})
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except Exception:
        logger.exception("[JOBS] Delete failed for job %s", job_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/postings/<int:job_id>', methods=['GET'])
@jwt_required(optional=True)
def get_job_posting_detail(job_id):
    """Get a single job posting by ID."""
    try:
        with db_connection() as conn:
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

        claims = get_jwt() or {}
        role = get_effective_role(claims) if claims else None
        if role in SECTOR_JOB_ROLES:
            _assert_sector_access(job.get('sector_id'), claims, 'jobs')
        elif role not in GLOBAL_JOB_ROLES and not _is_job_open(job):
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404

        for ts_field in ('created_at', 'updated_at', 'closes_at'):
            if job.get(ts_field):
                job[ts_field] = job[ts_field].isoformat()
        job['required_skills_list'] = _parse_skills(job.get('required_skills', ''))
        job['preferred_skills_list'] = _parse_skills(job.get('preferred_skills', ''))
        job['required_skills'] = ', '.join(job['required_skills_list'])
        job['preferred_skills'] = ', '.join(job['preferred_skills_list'])
        return jsonify({'status': 'success', 'data': job})
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except Exception:
        logger.exception("[JOBS] Failed to fetch posting %s", job_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


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
    try:
        data = _json_body()
        if data is None:
            raise ValueError('A JSON request body is required')
        candidate_id = _positive_int(data.get('candidate_id'), 'candidate_id')
        claims = get_jwt()
        scoped_sector = _scoped_sector_or_error(claims)

        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT id, parsed_skills, parsed_skills_json, years_experience,
                       education, resume_path, sector_id, updated_at
                FROM candidates WHERE id = %s
                """,
                (candidate_id,),
            )
            candidate = cursor.fetchone()
            if candidate:
                _assert_sector_access(candidate.get('sector_id'), claims, 'candidates')

            jobs_query = (
                "SELECT * FROM job_descriptions WHERE status = 'active' "
                "AND (closes_at IS NULL OR closes_at > CURRENT_TIMESTAMP)"
            )
            jobs_params = []
            if scoped_sector is not None:
                jobs_query += " AND sector_id = %s"
                jobs_params.append(scoped_sector)
            jobs_query += " ORDER BY id"
            cursor.execute(jobs_query, jobs_params)
            jobs = cursor.fetchall()

        if not candidate:
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404
        if not jobs:
            return jsonify({'status': 'error', 'message': 'No active job postings to match against'}), 404

        # Parse candidate skills
        skills = _parse_skills(candidate.get('parsed_skills') or candidate.get('parsed_skills_json') or '[]')
        experience = candidate.get('years_experience') or 0
        education = candidate.get('education') or ''

        resume_text = _extract_resume_text(candidate.get('resume_path'), candidate_id)

        # Run matching
        from job_matcher import match_candidate_to_jobs
        matches = match_candidate_to_jobs(skills, experience, education, resume_text, jobs)

        allowed_job_ids = {int(job['id']) for job in jobs}
        job_versions = {int(job['id']): job.get('updated_at') for job in jobs}
        if any(match.get('job_id') not in allowed_job_ids for match in matches):
            raise ValueError('Matcher returned a job outside the authorized active-job set')

        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT sector_id, updated_at FROM candidates WHERE id = %s FOR UPDATE",
                (candidate_id,),
            )
            current_candidate = cursor.fetchone()
            if not current_candidate:
                return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404
            _assert_sector_access(
                current_candidate.get('sector_id'), claims, 'candidates'
            )
            if current_candidate.get('updated_at') != candidate.get('updated_at'):
                raise ConcurrentJobChangeError(
                    'Candidate data changed during matching; please retry'
                )
            cursor.execute(
                """
                SELECT id, updated_at FROM job_descriptions
                WHERE id = ANY(%s) AND status = 'active'
                  AND (closes_at IS NULL OR closes_at > CURRENT_TIMESTAMP)
                FOR SHARE
                """,
                (list(allowed_job_ids),),
            )
            current_job_versions = {
                int(row['id']): row.get('updated_at') for row in cursor.fetchall()
            }
            if current_job_versions != job_versions:
                raise ConcurrentJobChangeError(
                    'Active jobs changed during matching; please retry'
                )

            # Remove stale automatic suggestions, while preserving recruiter
            # confirmations/rejections as hiring history.
            cursor.execute(
                """
                DELETE FROM candidate_job_matches
                WHERE candidate_id = %s AND status = 'auto_matched'
                  AND NOT (job_id = ANY(%s))
                """,
                (candidate_id, list(allowed_job_ids)),
            )
            for match in matches:
                cursor.execute("""
                    INSERT INTO candidate_job_matches
                    (candidate_id, job_id, match_score, skill_match_score,
                     experience_match_score, ai_reasoning)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (candidate_id, job_id) DO UPDATE
                    SET match_score = EXCLUDED.match_score,
                        skill_match_score = EXCLUDED.skill_match_score,
                        experience_match_score = EXCLUDED.experience_match_score,
                        ai_reasoning = EXCLUDED.ai_reasoning,
                        matched_at = CURRENT_TIMESTAMP
                """, (
                    candidate_id, match['job_id'], match['match_score'],
                    match['skill_match_score'], match['experience_match_score'],
                    match.get('ai_reasoning', ''),
                ))

            cursor.execute(
                """
                SELECT job_id, match_score
                FROM candidate_job_matches
                WHERE candidate_id = %s AND status <> 'rejected'
                  AND job_id = ANY(%s)
                ORDER BY match_score DESC, job_id
                LIMIT 1
                """,
                (candidate_id, list(allowed_job_ids)),
            )
            best = cursor.fetchone()
            cursor.execute("""
                UPDATE candidates
                SET best_match_job_id = %s, match_score = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                best.get('job_id') if best else None,
                best.get('match_score') if best else 0,
                candidate_id,
            ))
            audit_log(
                conn, get_jwt_identity(), 'match_candidate', 'candidate', candidate_id,
                {
                    'matches_count': len(matches),
                    'best_job_id': best.get('job_id') if best else None,
                },
                request.remote_addr,
            )
            conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Matched candidate to {len(matches)} job(s)',
            'data': {'matches': matches}
        })
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except ConcurrentJobChangeError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 409
    except Exception:
        logger.exception("[MATCH] Error for candidate")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/matches/<int:candidate_id>', methods=['GET'])
@jwt_required()
@require_role('recruiter')
def get_candidate_matches(candidate_id):
    """Get all job matches for a candidate."""
    try:
        claims = get_jwt()
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT sector_id FROM candidates WHERE id = %s", (candidate_id,))
            candidate = cursor.fetchone()
            if not candidate:
                return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404
            _assert_sector_access(candidate.get('sector_id'), claims, 'candidates')
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
            m['required_skills_list'] = _parse_skills(m.get('required_skills'))
            m['preferred_skills_list'] = _parse_skills(m.get('preferred_skills'))
        return jsonify({'status': 'success', 'data': matches})
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except Exception:
        logger.exception("[MATCH] Failed to fetch candidate matches")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/matches/<int:candidate_id>/<int:job_id>', methods=['PATCH'])
@jwt_required()
@require_role('recruiter')
def review_candidate_match(candidate_id, job_id):
    """Confirm or reject an automatic candidate-to-job recommendation."""
    try:
        data = _json_body()
        if data is None:
            raise ValueError('A JSON request body is required')
        status = str(data.get('status') or '').strip().lower()
        if status not in {'confirmed', 'rejected'}:
            raise ValueError('status must be confirmed or rejected')

        claims = get_jwt()
        reviewer_id = _positive_int(get_jwt_identity(), 'JWT identity')
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                """
                SELECT m.match_score, m.status, c.sector_id,
                       c.best_match_job_id, j.status AS job_status,
                       j.closes_at, j.sector_id AS job_sector_id
                FROM candidate_job_matches m
                JOIN candidates c ON c.id = m.candidate_id
                JOIN job_descriptions j ON j.id = m.job_id
                WHERE m.candidate_id = %s AND m.job_id = %s
                FOR UPDATE OF m, c
                """,
                (candidate_id, job_id),
            )
            match = cursor.fetchone()
            if not match:
                return jsonify({'status': 'error', 'message': 'Match not found'}), 404
            _assert_sector_access(match.get('sector_id'), claims, 'candidate matches')
            _assert_sector_access(match.get('job_sector_id'), claims, 'jobs')
            if status == 'confirmed' and not _is_job_open({
                'status': match.get('job_status'),
                'closes_at': match.get('closes_at'),
                'id': job_id,
            }):
                raise ConcurrentJobChangeError(
                    'Cannot confirm a match for a closed or expired job'
                )

            cursor.execute(
                """
                UPDATE candidate_job_matches
                SET status = %s, reviewed_by = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE candidate_id = %s AND job_id = %s
                """,
                (status, reviewer_id, candidate_id, job_id),
            )

            if status == 'confirmed':
                cursor.execute(
                    """
                    UPDATE candidates
                    SET best_match_job_id = %s, match_score = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (job_id, match.get('match_score') or 0, candidate_id),
                )
            elif match.get('best_match_job_id') == job_id:
                cursor.execute(
                    """
                    SELECT m.job_id, m.match_score
                    FROM candidate_job_matches m
                    JOIN job_descriptions j ON j.id = m.job_id
                    WHERE m.candidate_id = %s AND m.status <> 'rejected'
                      AND j.status = 'active'
                      AND (j.closes_at IS NULL OR j.closes_at > CURRENT_TIMESTAMP)
                    ORDER BY m.match_score DESC, m.job_id
                    LIMIT 1
                    """,
                    (candidate_id,),
                )
                replacement = cursor.fetchone()
                cursor.execute(
                    """
                    UPDATE candidates
                    SET best_match_job_id = %s, match_score = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        replacement.get('job_id') if replacement else None,
                        replacement.get('match_score') if replacement else 0,
                        candidate_id,
                    ),
                )

            audit_log(
                conn, get_jwt_identity(), 'review_candidate_match',
                'candidate_job_match', None,
                {
                    'candidate_id': candidate_id,
                    'job_id': job_id,
                    'status': status,
                },
                request.remote_addr,
            )
            conn.commit()

        return jsonify({
            'status': 'success',
            'message': f'Match {status}',
            'data': {
                'candidate_id': candidate_id,
                'job_id': job_id,
                'match_status': status,
            },
        })
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except ConcurrentJobChangeError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 409
    except Exception:
        logger.exception("[MATCH] Failed to review candidate match")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@jobs_bp.route('/postings/<int:job_id>/candidates', methods=['GET'])
@jwt_required()
@require_role('recruiter')
def get_job_candidates(job_id):
    """Get all matched candidates for a job posting, ranked by score."""
    try:
        claims = get_jwt()
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT sector_id FROM job_descriptions WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            if not job:
                return jsonify({'status': 'error', 'message': 'Job not found'}), 404
            _assert_sector_access(job.get('sector_id'), claims, 'jobs')
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
            if c.get('reviewed_at'):
                c['reviewed_at'] = c['reviewed_at'].isoformat()
            c['parsed_skills_list'] = _parse_skills(c.get('parsed_skills'))
        return jsonify({'status': 'success', 'data': candidates})
    except PermissionError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 403
    except Exception:
        logger.exception("[MATCH] Failed to fetch candidates for job %s", job_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
#                           AUDIT LOG
# ============================================================================

@jobs_bp.route('/audit-log', methods=['GET'])
@jwt_required()
@require_role('super_admin')
def get_audit_log():
    """Get recent audit log entries."""
    try:
        requested_limit = request.args.get('limit', 100, type=int)
        if requested_limit is None or not 1 <= requested_limit <= 500:
            raise ValueError('limit must be between 1 and 500')
        with db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM audit_log
                ORDER BY created_at DESC
                LIMIT %s
            """, (requested_limit,))
            logs = cursor.fetchall()
        for log in logs:
            if log.get('created_at'):
                log['created_at'] = log['created_at'].isoformat()
        return jsonify({'status': 'success', 'data': logs})
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception:
        logger.exception("[AUDIT] Failed to fetch audit log")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
#                           HELPERS
# ============================================================================

def _parse_skills(skills_value) -> list:
    """Parse skills from JSON string, JSON array, or comma-separated string."""
    if not skills_value:
        return []
    if isinstance(skills_value, (list, tuple, set)):
        return list(dict.fromkeys(
            str(value).strip() for value in skills_value if str(value).strip()
        ))
    try:
        parsed = json.loads(str(skills_value))
    except (json.JSONDecodeError, TypeError):
        parsed = None
    if parsed is not None:
        if isinstance(parsed, list):
            return list(dict.fromkeys(
                str(value).strip() for value in parsed if str(value).strip()
            ))
        if isinstance(parsed, str):
            skills_value = parsed
        else:
            return []
    normalised = str(skills_value).replace(';', ',').replace('\n', ',')
    return list(dict.fromkeys(
        value.strip() for value in normalised.split(',') if value.strip()
    ))
