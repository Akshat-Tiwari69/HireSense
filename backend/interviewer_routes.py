"""
Interviewer Routes Module
Handles all interviewer dashboard endpoints for candidate management
Protected routes requiring JWT authentication with 'interviewer' role
"""

import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import logging
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
    check_assessment_time_valid
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
        logger.info("📊 DASHBOARD: FETCHING CANDIDATES")
        logger.info("="*80)
        
        # Get filter and sort parameters
        status_filter = request.args.get('status', None)
        sort_by = request.args.get('sort', 'date')
        order = request.args.get('order', 'desc').lower()
        
        logger.info(f"   Filters - Status: {status_filter or 'All'}, Sort: {sort_by}, Order: {order}")
        
        if order not in ['asc', 'desc']:
            order = 'desc'
        
        # Get all candidates
        logger.info("🔍 Querying database for candidates...")
        candidates = get_all_candidates()
        
        if not candidates:
            logger.info("ℹ️ No candidates found")
            return jsonify({
                'status': 'success',
                'data': [],
                'total': 0
            }), 200
        
        logger.info(f"✅ Found {len(candidates)} candidates")
        
        # Filter by status if provided
        if status_filter:
            candidates = [c for c in candidates if c.get('status') == status_filter]
        
        # Parse pros and cons from database text
        for candidate in candidates:
            if candidate.get('pros'):
                candidate['pros'] = candidate['pros'].split('\n') if isinstance(candidate['pros'], str) else []
            else:
                candidate['pros'] = []
            
            if candidate.get('cons'):
                candidate['cons'] = candidate['cons'].split('\n') if isinstance(candidate['cons'], str) else []
            else:
                candidate['cons'] = []
        
        # Sort candidates
        if sort_by == 'name':
            candidates.sort(key=lambda x: x.get('name', ''), reverse=(order == 'desc'))
        elif sort_by == 'match_score':
            candidates.sort(key=lambda x: x.get('match_score', 0), reverse=(order == 'desc'))
        else:  # date
            candidates.sort(key=lambda x: x.get('created_at', ''), reverse=(order == 'desc'))
        
        logger.info(f"✅ Returning {len(candidates)} candidates to dashboard")
        logger.info("="*80)
        
        return jsonify({
            'status': 'success',
            'data': candidates,
            'total': len(candidates)
        }), 200
        
    except Exception as e:
        logger.exception(f"❌ Failed to fetch candidates: {e}")
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
        
        # Parse pros and cons
        if candidate.get('pros'):
            candidate['pros'] = candidate['pros'].split('\n') if isinstance(candidate['pros'], str) else []
        else:
            candidate['pros'] = []
        
        if candidate.get('cons'):
            candidate['cons'] = candidate['cons'].split('\n') if isinstance(candidate['cons'], str) else []
        else:
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
        print(f"[REJECT] Getting candidate info...", flush=True)
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            print(f"[REJECT] Candidate {candidate_id} not found", flush=True)
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        print(f"[REJECT] Found candidate: {candidate['name']}", flush=True)
        
        # Update status to rejected
        print(f"[REJECT] Updating status to rejected...", flush=True)
        update_candidate_status(candidate_id, 'rejected', candidate.get('pros'), candidate.get('cons'))
        
        # Send rejection email
        print(f"[REJECT] Sending rejection email to {candidate['email']}...", flush=True)
        email_sent = send_rejection_email(
            candidate_email=candidate['email'],
            candidate_name=candidate['name'],
            reason=reason if reason else None
        )
        print(f"[REJECT] Email result: {email_sent}", flush=True)
        
        print(f"[REJECT] Done! Returning success.", flush=True)
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
    Schedule assessment for a candidate
    
    Request Body:
        - scheduled_time: ISO datetime string or formatted time
        - additional_info: Optional custom instructions
    
    Returns:
        Success with scheduled assessment info
    """
    print(f"[SCHEDULE] Starting schedule for candidate {candidate_id}", flush=True)
    try:
        data = request.get_json()
        print(f"[SCHEDULE] Data received: {data}", flush=True)
        
        if not data or 'scheduled_time' not in data:
            print(f"[SCHEDULE] Missing scheduled_time", flush=True)
            return jsonify({
                'status': 'error',
                'message': 'scheduled_time is required'
            }), 400
        
        scheduled_time = data['scheduled_time']
        additional_info = data.get('additional_info', None)
        
        # Get candidate info
        print(f"[SCHEDULE] Getting candidate info...", flush=True)
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            print(f"[SCHEDULE] Candidate {candidate_id} not found", flush=True)
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        print(f"[SCHEDULE] Found candidate: {candidate['name']}", flush=True)
        
        # Get interviewer ID from JWT
        interviewer_id = get_jwt_identity()
        
        # Create scheduled assessment
        print(f"[SCHEDULE] Creating scheduled assessment...", flush=True)
        scheduled_assessment_id = create_scheduled_assessment(
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            scheduled_time=scheduled_time
        )
        print(f"[SCHEDULE] Assessment ID: {scheduled_assessment_id}", flush=True)
        
        # Generate assessment link - use FRONTEND_URL from env or default
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        assessment_link = f"{frontend_url}/assessment"
        print(f"[SCHEDULE] Assessment link: {assessment_link}", flush=True)
        
        # Get interviewer name from JWT claims
        claims = get_jwt()
        interviewer_name = claims.get('name', 'The Hiring Team')
        
        # Send invitation email
        print(f"[SCHEDULE] Sending invitation email to {candidate['email']}...", flush=True)
        email_sent = send_assessment_invitation(
            candidate_email=candidate['email'],
            candidate_name=candidate['name'],
            assessment_link=assessment_link,
            scheduled_time=scheduled_time,
            interviewer_name=interviewer_name,
            additional_info=additional_info
        )
        print(f"[SCHEDULE] Email result: {email_sent}", flush=True)
        
        # Update candidate status
        print(f"[SCHEDULE] Updating candidate status...", flush=True)
        update_candidate_status(candidate_id, 'under_review', candidate.get('pros'), candidate.get('cons'))
        
        print(f"[SCHEDULE] Done! Returning success.", flush=True)
        return jsonify({
            'status': 'success',
            'message': 'Assessment scheduled successfully',
            'data': {
                'candidate_id': candidate_id,
                'candidate_name': candidate['name'],
                'scheduled_assessment_id': scheduled_assessment_id,
                'scheduled_time': scheduled_time,
                'assessment_link': assessment_link,
                'status': 'under_review',
                'email_sent': email_sent
            }
        }), 201
        
    except Exception as e:
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
            decision=f"Hire" if decision in ['hire', 'hired', 'selected'] else "No-Hire",
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
