"""
Interviewer Routes Module
Handles all interviewer dashboard endpoints for candidate management
Protected routes requiring JWT authentication with 'interviewer' role
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import logging
from datetime_utils import parse_client_datetime
from db_config import db_connection, get_connection, return_connection
from ai_question_generator import get_ai_question_generator
from candidate_db import (
    get_candidate_by_id,
    get_interviewer_candidates,
)
from code_runner_config import code_runner_enabled as _code_runner_enabled
from assessment_db import (
    AssessmentStateError,
    cancel_schedule_after_invitation_failure,
    get_latest_completed_assessment_by_candidate_id,
    create_scheduled_assessment,
    generate_assessment_token,
    reject_scheduled_candidate,
    record_final_decision,
)
from email_service import (
    send_rejection_email,
    send_assessment_invitation,
    send_final_decision_email
)
from questions_bank import (
    get_coding_problem,
    get_mcq_questions,
    get_psychometric_scenarios,
)
from storage_config import get_upload_root, is_within_upload_root

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint for interviewer routes
interviewer_bp = Blueprint('interviewer', __name__)

_DEVELOPMENT_ENVIRONMENTS = {'dev', 'development', 'local', 'test'}
_HIRING_REVIEW_ROLES = {'interviewer', 'recruiter', 'sector_admin'}
_SECTOR_SCOPED_REVIEW_ROLES = {'recruiter', 'sector_admin'}


def _assessment_frontend_url():
    """Return a trusted base URL for bearer-style candidate links."""
    frontend_url = os.environ.get('FRONTEND_URL', '').strip().rstrip('/')
    if frontend_url:
        parsed = urlsplit(frontend_url)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise RuntimeError('FRONTEND_URL must be a valid HTTP or HTTPS URL')
        return frontend_url
    app_env = os.environ.get('APP_ENV', 'production').strip().lower()
    if app_env in _DEVELOPMENT_ENVIRONMENTS:
        return 'http://localhost:5173'
    raise RuntimeError('FRONTEND_URL must be configured outside development')


def _normalise_skill_values(raw_skills):
    if isinstance(raw_skills, list):
        return [str(skill).strip() for skill in raw_skills if str(skill).strip()]
    if not raw_skills:
        return []
    if isinstance(raw_skills, str):
        try:
            parsed = json.loads(raw_skills)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if isinstance(parsed, list):
            return [str(skill).strip() for skill in parsed if str(skill).strip()]
        return [
            skill.strip()
            for skill in raw_skills.replace('\n', ',').split(',')
            if skill.strip()
        ]
    return []


def _get_schedule_job_context(candidate_id, requested_job_id, reviewer_sector_id):
    """Return only an open job related to this candidate and reviewer scope."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT jd.id, jd.title, jd.required_skills
            FROM candidates c
            JOIN job_descriptions jd
              ON jd.id = COALESCE(%s, c.best_match_job_id)
            WHERE c.id = %s
              AND jd.status = 'active'
              AND (jd.closes_at IS NULL OR jd.closes_at > CURRENT_TIMESTAMP)
              AND (%s IS NULL OR jd.sector_id = %s)
              AND (
                    %s IS NULL
                    OR jd.id = c.best_match_job_id
                    OR EXISTS (
                        SELECT 1
                        FROM candidate_job_matches cjm
                        WHERE cjm.candidate_id = c.id
                          AND cjm.job_id = jd.id
                    )
                  )
            """,
            (
                requested_job_id,
                candidate_id,
                reviewer_sector_id,
                reviewer_sector_id,
                requested_job_id,
            ),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'title': row[1] or '',
            'required_skills': _normalise_skill_values(row[2]),
        }
    finally:
        if conn:
            with suppress(Exception):
                return_connection(conn)


def _generate_assessment_questions(
    candidate_skills,
    job_required_skills,
    applied_job_title,
    is_technical_role,
):
    """Generate independent question types concurrently with local fallbacks."""
    generated = {}
    has_skills = bool(candidate_skills or job_required_skills)

    try:
        ai_generator = get_ai_question_generator()
        futures = {}
        worker_count = 1
        if has_skills:
            worker_count += 1 + int(is_technical_role)

        with ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="assessment-questions",
        ) as executor:
            if has_skills:
                futures['mcq_questions'] = executor.submit(
                    ai_generator.generate_mcq_questions,
                    candidate_skills,
                    count=10,
                    difficulty="mixed",
                    job_title=applied_job_title,
                    job_skills=job_required_skills,
                )
                if is_technical_role:
                    futures['coding_problem'] = executor.submit(
                        ai_generator.generate_coding_problem,
                        candidate_skills,
                        difficulty="medium",
                        job_title=applied_job_title,
                        is_technical=True,
                        job_skills=job_required_skills,
                    )
            futures['psychometric_scenarios'] = executor.submit(
                ai_generator.generate_psychometric_scenarios,
                job_role=applied_job_title or "Professional",
                count=3,
            )

            for question_type, future in futures.items():
                try:
                    generated[question_type] = future.result()
                except Exception as exc:
                    logger.warning(
                        "%s generation failed (%s)",
                        question_type,
                        type(exc).__name__,
                    )
    except Exception as exc:
        logger.warning("Question generation failed (%s)", type(exc).__name__)

    return {
        'mcq_questions': generated.get('mcq_questions') or get_mcq_questions(count=10),
        'coding_problem': (
            generated.get('coding_problem') or get_coding_problem(difficulty="medium")
            if is_technical_role
            else None
        ),
        'psychometric_scenarios': (
            generated.get('psychometric_scenarios')
            or get_psychometric_scenarios(count=3)
        ),
    }


def _reviewer_sector_id(claims):
    if claims.get('role') not in _SECTOR_SCOPED_REVIEW_ROLES:
        return None
    try:
        sector_id = int(claims.get('sector_id'))
    except (TypeError, ValueError) as exc:
        raise ValueError('A sector assignment is required for this role') from exc
    if sector_id <= 0:
        raise ValueError('A sector assignment is required for this role')
    return sector_id


def _candidate_access_scope(candidate_id, interviewer_id, sector_id=None):
    """Return assigned/claimable access without exposing another owner's row."""

    with db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM scheduled_assessments own_assignment
                    WHERE own_assignment.candidate_id = c.id
                      AND own_assignment.interviewer_id = %s
                ) THEN 'assigned'
                WHEN c.status IN ('applied', 'pending', 'absence_of_details')
                     AND NOT EXISTS (
                         SELECT 1
                         FROM scheduled_assessments any_assignment
                         WHERE any_assignment.candidate_id = c.id
                     ) THEN 'claimable'
                ELSE NULL
            END
            FROM candidates c
            WHERE c.id = %s
            """
        params = [interviewer_id, candidate_id]
        if sector_id is not None:
            query += " AND c.sector_id = %s"
            params.append(sector_id)
        cursor.execute(query, tuple(params))
        row = cursor.fetchone()
    return row[0] if row else None


def _assessment_is_assigned(assessment_id, interviewer_id, sector_id=None):
    with db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT 1
            FROM assessments a
            JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
            JOIN candidates c ON c.id = a.candidate_id
            WHERE a.id = %s
              AND sa.interviewer_id = %s
            """
        params = [assessment_id, interviewer_id]
        if sector_id is not None:
            query += " AND c.sector_id = %s"
            params.append(sector_id)
        cursor.execute(query, tuple(params))
        return cursor.fetchone() is not None


def require_interviewer_role(f):
    """Require a hiring-review role and its mandatory sector scope."""

    @wraps(f)
    def check_interviewer_role(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') not in _HIRING_REVIEW_ROLES:
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Hiring reviewer role required.'
            }), 403
        try:
            _reviewer_sector_id(claims)
        except ValueError as exc:
            return jsonify({'status': 'error', 'message': str(exc)}), 403
        return f(*args, **kwargs)
    return check_interviewer_role


def require_candidate_assignment(f):
    @wraps(f)
    def check_candidate_assignment(*args, **kwargs):
        candidate_id = kwargs.get('candidate_id')
        if _candidate_access_scope(
            candidate_id,
            int(get_jwt_identity()),
            _reviewer_sector_id(get_jwt()),
        ) != 'assigned':
            return jsonify({
                'status': 'error',
                'message': 'Access denied to this candidate',
            }), 403
        return f(*args, **kwargs)
    return check_candidate_assignment


def require_candidate_schedule_access(f):
    @wraps(f)
    def check_candidate_schedule_access(*args, **kwargs):
        candidate_id = kwargs.get('candidate_id')
        if _candidate_access_scope(
            candidate_id,
            int(get_jwt_identity()),
            _reviewer_sector_id(get_jwt()),
        ) not in {
            'assigned',
            'claimable',
        }:
            return jsonify({
                'status': 'error',
                'message': 'Access denied to this candidate',
            }), 403
        return f(*args, **kwargs)
    return check_candidate_schedule_access


def require_assessment_assignment(f):
    @wraps(f)
    def check_assessment_assignment(*args, **kwargs):
        assessment_id = kwargs.get('assessment_id')
        if not _assessment_is_assigned(
            assessment_id,
            int(get_jwt_identity()),
            _reviewer_sector_id(get_jwt()),
        ):
            return jsonify({
                'status': 'error',
                'message': 'Access denied to this assessment',
            }), 403
        return f(*args, **kwargs)
    return check_assessment_assignment


@interviewer_bp.route('/candidates', methods=['GET'])
@jwt_required()
@require_interviewer_role
def get_candidates():
    """
    Get all candidates with their resume analysis
    
    Query Parameters:
        - status: Filter by status (pending, under_review, rejected, hired)
        - sort: Sort by (name, date, match_score)
        - order: asc or desc
    
    Returns:
        List of candidates with all data
    """
    try:
        logger.info("="*80)
        logger.info("[DASHBOARD] DASHBOARD: FETCHING CANDIDATES")
        logger.info("="*80)
        
        # Get filter and sort parameters
        status_filter = request.args.get('status', None)
        sort_by = request.args.get('sort', 'date')
        order = request.args.get('order', 'desc').lower()
        
        logger.info(f"   Filters - Status: {status_filter or 'All'}, Sort: {sort_by}, Order: {order}")
        
        if order not in ['asc', 'desc']:
            order = 'desc'
        
        # Get all candidates
        logger.info("[QUERY] Querying database for candidates...")
        candidates = get_interviewer_candidates(
            int(get_jwt_identity()),
            sector_id=_reviewer_sector_id(get_jwt()),
        )
        
        if not candidates:
            logger.info("[INFO] No candidates found")
            return jsonify({
                'status': 'success',
                'data': [],
                'total': 0
            }), 200
        
        logger.info(f"[OK] Found {len(candidates)} candidates")
        
        # Filter by status if provided
        if status_filter:
            candidates = [c for c in candidates if c.get('status') == status_filter]
        
        # Ensure pros/cons are always lists
        # The repository already returns JSON-compatible lists.
        for candidate in candidates:
            candidate.pop('resume_path', None)
            if not isinstance(candidate.get('pros'), list):
                candidate['pros'] = []
            if not isinstance(candidate.get('cons'), list):
                candidate['cons'] = []
        
        # Sort candidates
        if sort_by == 'name':
            candidates.sort(key=lambda x: x.get('name', ''), reverse=(order == 'desc'))
        elif sort_by == 'match_score':
            candidates.sort(key=lambda x: x.get('match_score', 0), reverse=(order == 'desc'))
        else:  # date
            candidates.sort(key=lambda x: x.get('created_at', ''), reverse=(order == 'desc'))
        
        logger.info(f"[OK] Returning {len(candidates)} candidates to dashboard")
        logger.info("="*80)
        
        return jsonify({
            'status': 'success',
            'data': candidates,
            'total': len(candidates)
        }), 200
        
    except Exception as e:
        logger.exception(f" Failed to fetch candidates: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>', methods=['GET'])
@jwt_required()
@require_interviewer_role
@require_candidate_assignment
def get_candidate_details(candidate_id):
    """
    Get detailed information for a specific candidate
    
    Includes:
        - Resume data
        - AI analysis (pros, cons)
        - Assessment status (if any)
        - Hiring history
    
    Returns:
        Detailed candidate information
    """
    try:
        candidate = get_candidate_by_id(candidate_id)
        
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        candidate.pop('resume_path', None)

        # Ensure pros/cons are always lists
        # (get_candidate_by_id may return raw strings for these fields)
        if isinstance(candidate.get('pros'), str):
            candidate['pros'] = [p.strip() for p in candidate['pros'].split('\n') if p.strip()]
        elif not isinstance(candidate.get('pros'), list):
            candidate['pros'] = []
        
        if isinstance(candidate.get('cons'), str):
            candidate['cons'] = [c.strip() for c in candidate['cons'].split('\n') if c.strip()]
        elif not isinstance(candidate.get('cons'), list):
            candidate['cons'] = []
        
        # Get assessment if any
        assessment = get_latest_completed_assessment_by_candidate_id(candidate_id)
        if assessment:
            candidate['assessment'] = assessment
        
        return jsonify({
            'status': 'success',
            'data': candidate
        }), 200
        
    except Exception:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/resume', methods=['GET'])
@jwt_required()
@require_interviewer_role
@require_candidate_assignment
def download_resume(candidate_id):
    """
    Download resume file for a candidate
    
    Returns:
        Resume file as attachment
    """
    try:
        candidate = get_candidate_by_id(candidate_id)
        
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        resume_path = candidate.get('resume_path')
        try:
            path = Path(resume_path)
            if not path.is_absolute():
                path = get_upload_root() / path
            path = path.resolve(strict=True)
        except (OSError, TypeError, ValueError):
            path = None
        if (
            path is None
            or not path.is_file()
            or path.suffix.lower() not in {'.pdf', '.docx'}
            or not is_within_upload_root(path)
        ):
            return jsonify({
                'status': 'error',
                'message': 'Resume file not found'
            }), 404

        return send_file(path, as_attachment=True, download_name=path.name)
        
    except Exception:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/reject', methods=['POST'])
@jwt_required()
@require_interviewer_role
@require_candidate_assignment
def reject_candidate(candidate_id):
    """
    Reject a candidate after resume review
    
    Request Body:
        - reason: Optional rejection reason/feedback
    
    Returns:
        Success confirmation with candidate info
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        if not isinstance(reason, str) or len(reason) > 4000:
            return jsonify({
                'status': 'error',
                'message': 'reason must be text up to 4000 characters',
            }), 400

        result = reject_scheduled_candidate(candidate_id, int(get_jwt_identity()))
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'Access denied to this candidate',
            }), 403

        email_sent = False
        if result['should_notify']:
            email_sent = send_rejection_email(
                candidate_email=result['candidate_email'],
                candidate_name=result['candidate_name'],
                reason=reason.strip() or None,
            )
        return jsonify({
            'status': 'success',
            'message': 'Candidate rejected successfully',
            'data': {
                'candidate_id': candidate_id,
                'candidate_name': result['candidate_name'],
                'status': 'rejected',
                'email_sent': email_sent
            }
        }), 200
    except AssessmentStateError as error:
        return jsonify({
            'status': 'error',
            'message': str(error),
        }), 409
    except Exception:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/schedule', methods=['POST'])
@jwt_required()
@require_interviewer_role
@require_candidate_schedule_access
def schedule_assessment(candidate_id):
    """
    Schedule assessment for a candidate and generate questions immediately.
    
    Request Body:
        - scheduled_time: ISO datetime string or formatted time
        - is_technical_role: Boolean (default True) - if False, no coding questions
        - additional_info: Optional custom instructions
    
    Returns:
        Success with scheduled assessment info
    """
    try:
        data = request.get_json()
        
        if not data or 'scheduled_time' not in data:
            return jsonify({
                'status': 'error',
                'message': 'scheduled_time is required'
            }), 400
        
        scheduled_time_input = data['scheduled_time']
        if not isinstance(scheduled_time_input, str) or not scheduled_time_input.strip():
            return jsonify({
                'status': 'error',
                'message': 'scheduled_time must be a valid ISO datetime string'
            }), 400
        try:
            scheduled_time = parse_client_datetime(scheduled_time_input)
        except ValueError:
            return jsonify({
                'status': 'error',
                'message': 'scheduled_time must be a valid ISO datetime string'
            }), 400
        if scheduled_time <= datetime.now(timezone.utc):
            return jsonify({
                'status': 'error',
                'message': 'scheduled_time must be in the future'
            }), 400

        try:
            frontend_url = _assessment_frontend_url()
        except RuntimeError:
            logger.error("Assessment invitations require a valid FRONTEND_URL")
            return jsonify({
                'status': 'error',
                'message': 'Assessment invitations are not configured.'
            }), 503

        additional_info = data.get('additional_info', None)
        is_technical_role = data.get('is_technical_role', True)  # Default to technical
        if not isinstance(is_technical_role, bool):
            return jsonify({
                'status': 'error',
                'message': 'is_technical_role must be a boolean'
            }), 400
        if is_technical_role and not _code_runner_enabled():
            return jsonify({
                'status': 'error',
                'message': 'Technical assessments are temporarily unavailable.'
            }), 503

        requested_job_id = data.get('job_id')
        if requested_job_id is not None:
            try:
                requested_job_id = int(requested_job_id)
            except (TypeError, ValueError):
                return jsonify({'status': 'error', 'message': 'job_id must be an integer'}), 400
        
        # Get candidate info
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        candidate_skills = _normalise_skill_values(
            candidate.get('skills') or candidate.get('parsed_skills')
        )
        reviewer_sector_id = _reviewer_sector_id(get_jwt())
        job_context = _get_schedule_job_context(
            candidate_id,
            requested_job_id,
            reviewer_sector_id,
        )
        applied_job_title = ""
        job_required_skills = []
        selected_job_id = None
        if job_context:
            selected_job_id = job_context['id']
            applied_job_title = job_context['title']
            job_required_skills = job_context['required_skills']
        elif requested_job_id is not None:
            return jsonify({
                'status': 'error',
                'message': 'Selected job is not open or authorized for this candidate',
            }), 400

        # Pre-cache independent question types before creating the schedule.
        questions_data = _generate_assessment_questions(
            candidate_skills=candidate_skills,
            job_required_skills=job_required_skills,
            applied_job_title=applied_job_title,
            is_technical_role=is_technical_role,
        )
        
        # Get interviewer ID from JWT
        interviewer_id = int(get_jwt_identity())
        
        # Create the schedule and token together so an invitation can never point
        # at a partially-created schedule.
        access_token = generate_assessment_token()
        scheduled_assessment_id = create_scheduled_assessment(
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            scheduled_time=scheduled_time,
            is_technical_role=is_technical_role,
            questions_data=questions_data,
            job_id=selected_job_id,
            reviewer_sector_id=reviewer_sector_id,
            access_token=access_token,
        )
        # FRONTEND_URL was validated before any schedule state was created.
        # Keep the bearer token in the URL fragment so browsers and reverse
        # proxies never send it in HTTP request paths or access logs.
        assessment_link = f"{frontend_url}/assessment#token={access_token}"
        # The link contains the candidate's bearer-style assessment token and
        # must never be written to application or platform logs.
        
        # Get interviewer name from JWT claims
        claims = get_jwt()
        interviewer_name = claims.get('name', 'The Hiring Team')
        
        # Send invitation email (use original IST time for display)
        try:
            email_sent = send_assessment_invitation(
                candidate_email=candidate['email'],
                candidate_name=candidate['name'],
                assessment_link=assessment_link,
                scheduled_time=scheduled_time_input,
                interviewer_name=interviewer_name,
                additional_info=additional_info
            )
        except Exception as exc:
            logger.error(
                "Assessment %s invitation delivery failed (%s)",
                scheduled_assessment_id,
                type(exc).__name__,
            )
            email_sent = False
        if not email_sent:
            cancelled = cancel_schedule_after_invitation_failure(
                scheduled_assessment_id,
                interviewer_id,
            )
            if not cancelled:
                logger.error(
                    "Assessment %s invitation failed after its state advanced",
                    scheduled_assessment_id,
                )
                return jsonify({
                    'status': 'error',
                    'message': (
                        'Invitation delivery could not be confirmed. '
                        'Refresh the candidate before retrying.'
                    ),
                }), 409
            return jsonify({
                'status': 'error',
                'message': (
                    'Assessment invitation could not be delivered. '
                    'The schedule was cancelled; please try again.'
                ),
            }), 503
        return jsonify({
            'status': 'success',
            'message': 'Assessment scheduled successfully',
            'data': {
                'candidate_id': candidate_id,
                'candidate_name': candidate['name'],
                'scheduled_assessment_id': scheduled_assessment_id,
                'job_id': selected_job_id,
                'scheduled_time': scheduled_time_input,  # Return original IST time for frontend display
                'scheduled_time_utc': scheduled_time.isoformat(),
                'assessment_link': assessment_link,
                'status': 'under_review',
                'email_sent': email_sent
            }
        }), 201
        
    except AssessmentStateError as error:
        return jsonify({
            'status': 'error',
            'message': str(error),
        }), 409
    except Exception as e:
        logger.error(
            "Scheduling failed for candidate id=%s (%s)",
            candidate_id,
            type(e).__name__,
        )
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@interviewer_bp.route('/assessments/<int:candidate_id>', methods=['GET'])
@jwt_required()
@require_interviewer_role
@require_candidate_assignment
def get_assessment_results(candidate_id):
    """
    Get assessment results for a candidate
    
    Returns:
        Assessment scores, decision, and AI recommendation
    """
    try:
        assessment = get_latest_completed_assessment_by_candidate_id(candidate_id)
        
        if not assessment:
            return jsonify({
                'status': 'error',
                'message': 'No assessment found for this candidate'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': assessment
        }), 200
        
    except Exception:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@interviewer_bp.route('/assessments/<int:assessment_id>/final-decision', methods=['POST'])
@jwt_required()
@require_interviewer_role
@require_assessment_assignment
def make_final_decision(assessment_id):
    """
    Make final hiring decision after assessment completion
    
    Request Body:
        - decision: "hire" or "no-hire"
        - rationale: Optional explanation for the decision
        - next_steps: Optional custom next steps message
    
    Returns:
        Success confirmation and email sent status
    """
    try:
        data = request.get_json()
        
        if not data or 'decision' not in data:
            return jsonify({
                'status': 'error',
                'message': 'decision is required (hire or no-hire)'
            }), 400
        
        raw_decision = data['decision']
        if not isinstance(raw_decision, str):
            return jsonify({
                'status': 'error',
                'message': 'decision must be "hire" or "no-hire"'
            }), 400
        decision = raw_decision.strip().lower()
        if decision not in ['hire', 'no-hire', 'hired', 'selected']:
            return jsonify({
                'status': 'error',
                'message': 'decision must be "hire" or "no-hire"'
            }), 400

        rationale = data.get('rationale', None)
        next_steps = data.get('next_steps', None)
        if rationale is not None and (
            not isinstance(rationale, str) or len(rationale) > 4000
        ):
            return jsonify({
                'status': 'error',
                'message': 'rationale must be text up to 4000 characters'
            }), 400
        if next_steps is not None and (
            not isinstance(next_steps, str) or len(next_steps) > 4000
        ):
            return jsonify({
                'status': 'error',
                'message': 'next_steps must be text up to 4000 characters'
            }), 400

        normalized_decision = (
            'hire' if decision in ['hire', 'hired', 'selected'] else 'no-hire'
        )
        result = record_final_decision(
            assessment_id,
            normalized_decision,
            rationale.strip() if rationale else None,
        )
        if not result:
            return jsonify({
                'status': 'error',
                'message': 'Assessment not found'
            }), 404

        # Prepare scores for email
        scores = {
            'technical': round(result['technical_score'], 2),
            'psychometric': round(result['psychometric_score'], 2),
            'overall': round(result['overall_score'], 2),
        }
        
        # Send final decision email
        email_sent = False
        if result['should_notify']:
            email_sent = send_final_decision_email(
                candidate_email=result['candidate_email'],
                candidate_name=result['candidate_name'],
                decision=normalized_decision,
                rationale=result['final_rationale'],
                next_steps=next_steps.strip() if next_steps else None,
                scores=scores
            )
        
        return jsonify({
            'status': 'success',
            'message': 'Final decision recorded successfully',
            'data': {
                'assessment_id': assessment_id,
                'candidate_id': result['candidate_id'],
                'candidate_name': result['candidate_name'],
                'final_decision': result['final_decision'],
                'status': result['status'],
                'scores': scores,
                'email_sent': email_sent
            }
        }), 200
        
    except AssessmentStateError as error:
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 409
    except Exception:
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
# Export blueprint
__all__ = ['interviewer_bp']
