"""
Interviewer Routes Module
Handles all interviewer dashboard endpoints for candidate management
Protected routes requiring JWT authentication with 'interviewer' role
"""

import os
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import logging
from functools import lru_cache
from db_config import get_connection, return_connection
from db_helpers import (
    get_all_candidates,
    get_candidate_by_id,
    update_candidate_status,
    get_assessment_by_candidate_id,
    update_assessment_scores,
    get_assessment_by_id,
    create_scheduled_assessment,
    get_scheduled_assessment,
    update_scheduled_assessment_status,
    check_assessment_time_valid,
    generate_assessment_token,
    set_assessment_token
)
from email_service import (
    send_rejection_email,
    send_assessment_invitation,
    send_final_decision_email
)

# Setup logger
logger = logging.getLogger(__name__)

# Create blueprint for interviewer routes
interviewer_bp = Blueprint('interviewer', __name__)


def require_interviewer_role(f):
    """Decorator to check for interviewer role"""
    from functools import wraps
    @wraps(f)
    def check_interviewer_role(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'interviewer':
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Interviewer role required.'
            }), 403
        return f(*args, **kwargs)
    return check_interviewer_role


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
        candidates = get_all_candidates()
        
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
        # (get_all_candidates already returns them as lists after the db_helpers fix)
        for candidate in candidates:
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
            'message': f'Failed to fetch candidates: {str(e)}'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>', methods=['GET'])
@jwt_required()
@require_interviewer_role
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
        assessment = get_assessment_by_candidate_id(candidate_id)
        if assessment:
            candidate['assessment'] = assessment
        
        return jsonify({
            'status': 'success',
            'data': candidate
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to fetch candidate details: {str(e)}'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/resume', methods=['GET'])
@jwt_required()
@require_interviewer_role
def download_resume(candidate_id):
    """
    Download resume file for a candidate
    
    Returns:
        Resume file as attachment
    """
    from flask import send_file
    import os
    
    try:
        candidate = get_candidate_by_id(candidate_id)
        
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        resume_path = candidate.get('resume_path')
        if not resume_path or not os.path.exists(resume_path):
            return jsonify({
                'status': 'error',
                'message': 'Resume file not found'
            }), 404
        
        # Send file with original filename
        filename = os.path.basename(resume_path)
        return send_file(resume_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to download resume: {str(e)}'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/reject', methods=['POST'])
@jwt_required()
@require_interviewer_role
def reject_candidate(candidate_id):
    """
    Reject a candidate after resume review
    
    Request Body:
        - reason: Optional rejection reason/feedback
    
    Returns:
        Success confirmation with candidate info
    """
    print(f"[REJECT] Starting rejection for candidate {candidate_id}", flush=True)
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # Get candidate info
        print("[REJECT] Getting candidate info...", flush=True)
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            print(f"[REJECT] Candidate {candidate_id} not found", flush=True)
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        print(f"[REJECT] Found candidate: {candidate['name']}", flush=True)
        
        # Update status to rejected
        print("[REJECT] Updating status to rejected...", flush=True)
        update_candidate_status(candidate_id, 'rejected', candidate.get('pros'), candidate.get('cons'))
        
        # Send rejection email
        print(f"[REJECT] Sending rejection email to {candidate['email']}...", flush=True)
        email_sent = send_rejection_email(
            candidate_email=candidate['email'],
            candidate_name=candidate['name'],
            reason=reason or None
        )
        print(f"[REJECT] Email result: {email_sent}", flush=True)
        
        print("[REJECT] Done! Returning success.", flush=True)
        return jsonify({
            'status': 'success',
            'message': 'Candidate rejected successfully',
            'data': {
                'candidate_id': candidate_id,
                'candidate_name': candidate['name'],
                'status': 'rejected',
                'email_sent': email_sent
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to reject candidate: {str(e)}'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/schedule', methods=['POST'])
@jwt_required()
@require_interviewer_role
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
    print(f"[SCHEDULE] Starting schedule for candidate {candidate_id}", flush=True)
    try:
        data = request.get_json()
        print(f"[SCHEDULE] Data received: {data}", flush=True)
        
        if not data or 'scheduled_time' not in data:
            print("[SCHEDULE] Missing scheduled_time", flush=True)
            return jsonify({
                'status': 'error',
                'message': 'scheduled_time is required'
            }), 400
        
        scheduled_time_input = data['scheduled_time']
        additional_info = data.get('additional_info', None)
        is_technical_role = data.get('is_technical_role', True)  # Default to technical
        
        # Store the time as-is (local time) - no timezone conversion
        scheduled_time = scheduled_time_input
        print(f"[SCHEDULE] Using time as entered: {scheduled_time}, is_technical: {is_technical_role}", flush=True)
        
        # Get candidate info
        print("[SCHEDULE] Getting candidate info...", flush=True)
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            print(f"[SCHEDULE] Candidate {candidate_id} not found", flush=True)
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        print(f"[SCHEDULE] Found candidate: {candidate['name']}", flush=True)
        
        # Parse candidate skills (handle both 'skills' list and 'parsed_skills' JSON string)
        candidate_skills = []
        # Try 'skills' key first (already-parsed list from get_candidate_by_id)
        if candidate.get('skills') and isinstance(candidate['skills'], list):
            candidate_skills = [s.strip() for s in candidate['skills'] if isinstance(s, str) and s.strip()]
        # Fallback: try 'parsed_skills' raw JSON string
        elif candidate.get('parsed_skills'):
            skills_raw = candidate['parsed_skills']
            if isinstance(skills_raw, str):
                try:
                    parsed = json.loads(skills_raw)
                    if isinstance(parsed, list):
                        candidate_skills = [s.strip() for s in parsed if isinstance(s, str) and s.strip()]
                    else:
                        candidate_skills = [s.strip() for s in skills_raw.replace('\n', ',').split(',') if s.strip()]
                except (json.JSONDecodeError, TypeError):
                    candidate_skills = [s.strip() for s in skills_raw.replace('\n', ',').split(',') if s.strip()]
            elif isinstance(skills_raw, list):
                candidate_skills = [s.strip() for s in skills_raw if isinstance(s, str) and s.strip()]
        print(f"[SCHEDULE] Parsed candidate_skills: {candidate_skills[:5]} (total: {len(candidate_skills)})", flush=True)
        
        # Fetch job details for better question generation
        applied_job_title = ""
        job_required_skills = []
        jconn = None
        try:
            jconn = get_connection()
            cursor = jconn.cursor()
            cursor.execute(
                """SELECT jd.title, jd.required_skills 
                FROM job_descriptions jd 
                JOIN candidates c ON c.best_match_job_id = jd.id 
                WHERE c.id = %s""",
                (candidate_id,)
            )
            jrow = cursor.fetchone()
            if jrow:
                applied_job_title = jrow[0] or ""
                if jrow[1]:
                    job_required_skills = [s.strip() for s in jrow[1].replace('\n', ',').split(',') if s.strip()]
        except Exception as e:
            logger.warning(f"Could not fetch job details: {e}")
        finally:
            if jconn:
                import contextlib
                with contextlib.suppress(Exception):
                    return_connection(jconn)
        
        # Generate UNIQUE AI questions at schedule time (pre-cached for fast assessment start)
        print("[SCHEDULE] Generating unique AI questions for candidate...", flush=True)
        print(f"[SCHEDULE] candidate_skills ({len(candidate_skills)}): {candidate_skills[:5]}", flush=True)
        print(f"[SCHEDULE] job_required_skills ({len(job_required_skills)}): {job_required_skills[:5]}", flush=True)
        print(f"[SCHEDULE] applied_job_title: {applied_job_title}", flush=True)
        questions_data = None
        try:
            from ai_question_generator import get_ai_question_generator
            from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
            
            ai_generator = get_ai_question_generator()
            
            # Generate each question type independently so one failure doesn't kill the rest
            mcq_questions = None
            coding_problem = None
            psychometric_scenarios = None
            
            has_skills = candidate_skills or job_required_skills
            
            # 1. MCQ Questions
            try:
                if has_skills:
                    mcq_questions = ai_generator.generate_mcq_questions(
                        candidate_skills,
                        count=10,
                        difficulty="mixed",
                        job_title=applied_job_title,
                        job_skills=job_required_skills
                    )
            except Exception as mcq_err:
                print(f"[SCHEDULE] MCQ AI failed: {mcq_err}", flush=True)
            if not mcq_questions:
                mcq_questions = get_mcq_questions(count=10)
                print("[SCHEDULE] MCQ: Using fallback questions", flush=True)
            
            # 2. Coding Problem (technical roles only)
            try:
                if is_technical_role and has_skills:
                    coding_problem = ai_generator.generate_coding_problem(
                        candidate_skills,
                        difficulty="medium",
                        job_title=applied_job_title,
                        is_technical=True,
                        job_skills=job_required_skills
                    )
            except Exception as code_err:
                print(f"[SCHEDULE] Coding AI failed: {code_err}", flush=True)
            if is_technical_role and not coding_problem:
                coding_problem = get_coding_problem(difficulty="medium")
                print("[SCHEDULE] Coding: Using fallback problem", flush=True)
            
            # 3. Psychometric Scenarios
            try:
                psychometric_scenarios = ai_generator.generate_psychometric_scenarios(
                    job_role=applied_job_title or "Professional",
                    count=3
                )
            except Exception as psych_err:
                print(f"[SCHEDULE] Psychometric AI failed: {psych_err}", flush=True)
            if not psychometric_scenarios:
                psychometric_scenarios = get_psychometric_scenarios(count=3)
                print("[SCHEDULE] Psychometric: Using fallback scenarios", flush=True)
            
            questions_data = {
                'mcq_questions': mcq_questions,
                'coding_problem': coding_problem,
                'psychometric_scenarios': psychometric_scenarios,
                'is_technical_role': is_technical_role
            }
            print(f"[SCHEDULE] Final: {len(mcq_questions)} MCQ, coding={'Yes' if coding_problem else 'No'}, {len(psychometric_scenarios)} psychometric", flush=True)
            
        except Exception as e:
            logger.warning(f"AI question generation failed at schedule time: {str(e)}")
            print(f"[SCHEDULE] TOTAL FAILURE: {e}", flush=True)
            from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
            questions_data = {
                'mcq_questions': get_mcq_questions(count=10),
                'coding_problem': get_coding_problem(difficulty="medium") if is_technical_role else None,
                'psychometric_scenarios': get_psychometric_scenarios(count=3),
                'is_technical_role': is_technical_role
            }
        
        # Get interviewer ID from JWT
        interviewer_id = int(get_jwt_identity())
        print(f"[SCHEDULE] Interviewer ID: {interviewer_id}", flush=True)
        
        # Create scheduled assessment with pre-generated questions
        print("[SCHEDULE] Creating scheduled assessment with unique questions...", flush=True)
        scheduled_assessment_id = create_scheduled_assessment(
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            scheduled_time=scheduled_time,
            is_technical_role=is_technical_role,
            questions_data=questions_data
        )
        print(f"[SCHEDULE] Assessment ID: {scheduled_assessment_id}", flush=True)
        
        # Generate secure access token for this assessment
        access_token = generate_assessment_token()
        set_assessment_token(scheduled_assessment_id, access_token)
        print("[SCHEDULE] Access token generated", flush=True)
        
        # Generate assessment link with token
        # Priority: 1) FRONTEND_URL env var, 2) Origin header from request, 3) Referer header, 4) localhost fallback
        frontend_url = os.environ.get('FRONTEND_URL')
        if not frontend_url:
            # Try to get from request origin
            if origin := request.headers.get('Origin'):
                frontend_url = origin.rstrip('/')
            elif referer := request.headers.get('Referer'):
                # Extract base URL from referer (e.g., http://10.39.35.52:5173/some/path -> http://10.39.35.52:5173)
                from urllib.parse import urlparse
                parsed = urlparse(referer)
                frontend_url = f"{parsed.scheme}://{parsed.netloc}"
            else:
                # Final fallback to localhost
                frontend_url = 'http://localhost:5173'
        
        assessment_link = f"{frontend_url}/assessment/{access_token}"
        print(f"[SCHEDULE] Frontend URL: {frontend_url}", flush=True)
        print(f"[SCHEDULE] Assessment link: {assessment_link}", flush=True)
        
        # Get interviewer name from JWT claims
        claims = get_jwt()
        interviewer_name = claims.get('name', 'The Hiring Team')
        
        # Send invitation email (use original IST time for display)
        print(f"[SCHEDULE] Sending invitation email to {candidate['email']}...", flush=True)
        email_sent = send_assessment_invitation(
            candidate_email=candidate['email'],
            candidate_name=candidate['name'],
            assessment_link=assessment_link,
            scheduled_time=scheduled_time_input,  # Use original IST time for email
            interviewer_name=interviewer_name,
            additional_info=additional_info
        )
        print(f"[SCHEDULE] Email result: {email_sent}", flush=True)
        
        # Update candidate status
        print("[SCHEDULE] Updating candidate status...", flush=True)
        update_candidate_status(candidate_id, 'under_review', candidate.get('pros'), candidate.get('cons'))
        
        print("[SCHEDULE] Done! Returning success.", flush=True)
        return jsonify({
            'status': 'success',
            'message': 'Assessment scheduled successfully',
            'data': {
                'candidate_id': candidate_id,
                'candidate_name': candidate['name'],
                'scheduled_assessment_id': scheduled_assessment_id,
                'scheduled_time': scheduled_time_input,  # Return original IST time for frontend display
                'scheduled_time_utc': scheduled_time,    # Also provide UTC time
                'assessment_link': assessment_link,
                'status': 'under_review',
                'email_sent': email_sent
            }
        }), 201
        
    except Exception as e:
        print(f"[SCHEDULE] ERROR: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Failed to schedule assessment: {str(e)}'
        }), 500


@interviewer_bp.route('/assessments/<int:candidate_id>', methods=['GET'])
@jwt_required()
@require_interviewer_role
def get_assessment_results(candidate_id):
    """
    Get assessment results for a candidate
    
    Returns:
        Assessment scores, decision, and AI recommendation
    """
    try:
        assessment = get_assessment_by_candidate_id(candidate_id)
        
        if not assessment:
            return jsonify({
                'status': 'error',
                'message': 'No assessment found for this candidate'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': assessment
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to fetch assessment results: {str(e)}'
        }), 500


@interviewer_bp.route('/assessments/<int:assessment_id>/final-decision', methods=['POST'])
@jwt_required()
@require_interviewer_role
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
        
        decision = data['decision'].lower()
        if decision not in ['hire', 'no-hire', 'hired', 'selected']:
            return jsonify({
                'status': 'error',
                'message': 'decision must be "hire" or "no-hire"'
            }), 400
        
        rationale = data.get('rationale', None)
        next_steps = data.get('next_steps', None)
        
        # Get assessment
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({
                'status': 'error',
                'message': 'Assessment not found'
            }), 404
        
        # Get candidate info
        candidate_id = assessment.get('candidate_id')
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        # Update assessment with decision
        final_status = 'hired' if decision in ['hire', 'hired', 'selected'] else 'rejected'
        update_assessment_scores(
            assessment_id=assessment_id,
            technical_score=assessment.get('technical_score'),
            psychometric_score=assessment.get('psychometric_score'),
            decision="Hire" if decision in ['hire', 'hired', 'selected'] else "No-Hire",
            rationale=rationale or assessment.get('rationale', 'Decision made after assessment review')
        )
        
        # Update candidate status
        update_candidate_status(candidate_id, final_status, candidate.get('pros'), candidate.get('cons'))
        
        # Prepare scores for email
        scores = {
            'technical': round(assessment.get('technical_score', 0), 2),
            'psychometric': round(assessment.get('psychometric_score', 0), 2),
            'overall': round(
                (assessment.get('technical_score', 0) * 0.7) + 
                (assessment.get('psychometric_score', 0) * 0.3),
                2
            )
        }
        
        # Send final decision email
        email_sent = send_final_decision_email(
            candidate_email=candidate['email'],
            candidate_name=candidate['name'],
            decision=decision,
            rationale=rationale,
            next_steps=next_steps,
            scores=scores
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Final decision recorded successfully',
            'data': {
                'assessment_id': assessment_id,
                'candidate_id': candidate_id,
                'candidate_name': candidate['name'],
                'decision': 'Hire' if decision in ['hire', 'hired', 'selected'] else 'No-Hire',
                'status': final_status,
                'scores': scores,
                'email_sent': email_sent
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to record final decision: {str(e)}'
        }), 500


@interviewer_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@require_interviewer_role
def get_dashboard_stats():
    """
    Get dashboard statistics for the interviewer
    
    Returns:
        Total candidates, by status, average scores, etc.
    """
    try:
        candidates = get_all_candidates()
        
        stats = {
            'total_candidates': len(candidates),
            'pending': len([c for c in candidates if c.get('status') == 'pending']),
            'under_review': len([c for c in candidates if c.get('status') == 'under_review']),
            'hired': len([c for c in candidates if c.get('status') == 'hired']),
            'rejected': len([c for c in candidates if c.get('status') == 'rejected']),
            'average_match_score': round(
                sum(c.get('match_score', 0) for c in candidates) / max(len(candidates), 1),
                2
            )
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to fetch dashboard stats: {str(e)}'
        }), 500


@interviewer_bp.route('/candidates/<int:candidate_id>/notes', methods=['POST', 'GET'])
@jwt_required()
@require_interviewer_role
def manage_candidate_notes(candidate_id):
    """
    Get or add notes for a candidate (for future implementation)
    
    Currently returns placeholder response
    """
    try:
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'data': {
                    'candidate_id': candidate_id,
                    'notes': []
                }
            }), 200
        else:  # POST
            return jsonify({
                'status': 'success',
                'message': 'Note saved successfully'
            }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to manage notes: {str(e)}'
        }), 500


# Export blueprint
__all__ = ['interviewer_bp']
