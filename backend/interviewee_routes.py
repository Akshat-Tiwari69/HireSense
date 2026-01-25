"""
Interviewee Routes Module
Handles assessment endpoints for candidates
Includes assessment time validation (±30 minute window)
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import pytz
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from db_helpers import (
    get_candidate_by_id,
    get_scheduled_assessment,
    get_assessment_by_id,
    check_assessment_time_valid,
    update_scheduled_assessment_status,
    create_assessment,
    update_assessment_scores,
    get_mcq_score,
    get_coding_score,
    get_psychometric_scores,
    get_assessment_by_token,
    start_assessment_by_token,
    record_proctoring_violation,
    count_violations_for_assessment,
    save_mcq_response,
    save_coding_submission,
    save_psychometric_response
)
from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios


# Create blueprint for interviewee routes
interviewee_bp = Blueprint('interviewee', __name__)


@interviewee_bp.route('/my-assessment/<int:candidate_id>', methods=['GET'])
def get_my_assessment(candidate_id):
    """
    Get assessment information for a candidate
    
    Returns:
        - Scheduled time (if assessment is scheduled)
        - Assessment status
        - Assessment link
        - Window information
    """
    try:
        # Get candidate
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        # Get scheduled assessment
        scheduled = get_scheduled_assessment(candidate_id)
        if not scheduled:
            return jsonify({
                'status': 'error',
                'message': 'No assessment scheduled yet'
            }), 404
        
        # Get current time
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Check if time is valid
        is_valid, scheduled_time, message = check_assessment_time_valid(
            candidate_id=candidate_id,
            current_time=current_time,
            window_minutes=30
        )
        
        # Parse scheduled time to datetime for calculations
        scheduled_dt = datetime.fromisoformat(scheduled['scheduled_time'].replace('Z', '+00:00'))
        current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        minutes_until = int(((scheduled_dt - current_dt).total_seconds()) / 60)
        
        return jsonify({
            'status': 'success',
            'data': {
                'candidate_id': candidate_id,
                'candidate_name': candidate['name'],
                'scheduled_time': scheduled['scheduled_time'],
                'window_minutes': 30,
                'current_time': current_time,
                'minutes_until_start': minutes_until,
                'can_start': is_valid,
                'message': message,
                'status': scheduled['status'],
                'assessment_id': scheduled.get('assessment_id')
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to fetch assessment info: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/start/<int:candidate_id>', methods=['POST'])
def start_assessment(candidate_id):
    """
    Start assessment for a candidate with time validation
    
    Validates:
        - Candidate exists
        - Assessment is scheduled
        - Current time is within ±30 minute window of scheduled time
    
    Returns:
        - assessment_id
        - MCQ questions (without answers)
        - Coding problem (without test cases)
        - Psychometric scenarios
    """
    try:
        # Get candidate
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({
                'status': 'error',
                'message': 'Candidate not found'
            }), 404
        
        # Get scheduled assessment
        scheduled = get_scheduled_assessment(candidate_id)
        if not scheduled:
            return jsonify({
                'status': 'error',
                'message': 'No assessment scheduled. Please contact your recruiter.'
            }), 404
        
        # Get current time
        current_time = datetime.utcnow().isoformat() + 'Z'
        
        # Check if assessment time is valid
        is_valid, scheduled_time, time_message = check_assessment_time_valid(
            candidate_id=candidate_id,
            current_time=current_time,
            window_minutes=30
        )
        
        if not is_valid:
            # Calculate how far off the time is
            scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            minutes_diff = int(abs((current_dt - scheduled_dt).total_seconds()) / 60)
            
            return jsonify({
                'status': 'error',
                'message': f'Assessment not available yet. {time_message}',
                'data': {
                    'scheduled_time': scheduled_time,
                    'current_time': current_time,
                    'minutes_away': minutes_diff,
                    'allowed_window': 30
                }
            }), 403
        
        # If assessment already exists and is in progress, return it
        if scheduled.get('assessment_id'):
            existing = get_assessment_by_id(scheduled['assessment_id'])
            if existing and existing['status'] in ['started', 'in_progress']:
                # Assessment already started - load and return it
                assessment_id = existing['id']
                
                # Get questions
                mcq_questions = get_mcq_questions(count=10)
                coding_problem = get_coding_problem(difficulty="easy")
                psychometric_scenarios = get_psychometric_scenarios(count=3)
                
                # Remove answers from questions
                mcq_for_frontend = []
                for q in mcq_questions:
                    mcq_for_frontend.append({
                        "id": q["id"],
                        "question": q["question"],
                        "options": q["options"],
                        "time_limit": q["time_limit"],
                        "category": q["category"],
                        "difficulty": q["difficulty"]
                    })
                
                return jsonify({
                    'status': 'success',
                    'message': 'Assessment resumed',
                    'data': {
                        'assessment_id': assessment_id,
                        'candidate_id': candidate_id,
                        'mcq_questions': mcq_for_frontend,
                        'coding_problem': {
                            'id': coding_problem['id'],
                            'title': coding_problem['title'],
                            'description': coding_problem['description'],
                            'example': coding_problem['example'],
                            'difficulty': coding_problem['difficulty']
                        },
                        'psychometric_scenarios': psychometric_scenarios,
                        'resumed': True
                    }
                }), 200
        
        # Create new assessment
        assessment_id = create_assessment(candidate_id)
        
        # Update scheduled assessment status to in_progress
        update_scheduled_assessment_status(
            scheduled_assessment_id=scheduled['id'],
            status='in_progress',
            assessment_id=assessment_id
        )
        
        # Get questions
        mcq_questions = get_mcq_questions(count=10)
        coding_problem = get_coding_problem(difficulty="easy")
        psychometric_scenarios = get_psychometric_scenarios(count=3)
        
        # Remove answers from questions for frontend
        mcq_for_frontend = []
        for q in mcq_questions:
            mcq_for_frontend.append({
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
                "time_limit": q["time_limit"],
                "category": q["category"],
                "difficulty": q["difficulty"]
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Assessment started successfully',
            'data': {
                'assessment_id': assessment_id,
                'candidate_id': candidate_id,
                'scheduled_time': scheduled_time,
                'mcq_questions': mcq_for_frontend,
                'coding_problem': {
                    'id': coding_problem['id'],
                    'title': coding_problem['title'],
                    'description': coding_problem['description'],
                    'example': coding_problem['example'],
                    'difficulty': coding_problem['difficulty']
                },
                'psychometric_scenarios': psychometric_scenarios
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start assessment: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/<int:assessment_id>/submit-answer', methods=['POST'])
def submit_answer(assessment_id):
    """
    Submit an answer for MCQ, coding, or psychometric question.
    
    Expects:
        {
            "type": "mcq" | "coding" | "psychometric",
            "questionId": int,
            "answer": str (for MCQ: "A"/"B"/"C"/"D"),
            "code": str (for coding),
            "language": str (for coding: "python"/"javascript"/"java"/"cpp"),
            "testsPassed": int (for coding),
            "totalTests": int (for coding),
            "trait": str (for psychometric),
            "score": int (for psychometric: 1-10),
            "timeSpent": int (optional, in seconds)
        }
    """
    try:
        data = request.json
        answer_type = data.get('type')
        
        if answer_type == 'mcq':
            # Get the correct answer for this question
            question_id = data.get('questionId')
            selected = data.get('answer')  # "A", "B", "C", or "D"
            time_spent = data.get('timeSpent', 0)
            
            # Get assessment to verify it exists
            assessment = get_assessment_by_id(assessment_id)
            if not assessment:
                return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404
            
            # Get question bank (static questions)
            questions = get_mcq_questions(count=20)
            correct_answer = None
            correct_option_text = None
            
            # Find the correct answer for this question
            for q in questions:
                if q['id'] == question_id:
                    correct_option_text = q['correct_answer']
                    # Find which option letter matches the correct answer text
                    for idx, option in enumerate(q['options']):
                        if option == correct_option_text:
                            correct_answer = ['A', 'B', 'C', 'D'][idx]
                            break
                    break
            
            if not correct_answer:
                return jsonify({'status': 'error', 'message': 'Question not found'}), 404
            
            is_correct = (selected == correct_answer)
            
            save_mcq_response(
                assessment_id=assessment_id,
                question_id=question_id,
                selected_answer=selected,
                is_correct=is_correct,
                time_spent=time_spent
            )
            
            return jsonify({
                'status': 'success',
                'message': 'MCQ answer saved',
                'is_correct': is_correct
            }), 200
            correct_answer = None
            
            # Find the correct answer for this question
            for q in questions:
                if q['id'] == question_id:
                    correct_answer = q['correct_answer']
                    break
            
            if not correct_answer:
                return jsonify({'status': 'error', 'message': 'Question not found'}), 404
            
            is_correct = (selected == correct_answer)
            
            save_mcq_response(
                assessment_id=assessment_id,
                question_id=question_id,
                selected_answer=selected,
                is_correct=is_correct,
                time_spent=time_spent
            )
            
            return jsonify({
                'status': 'success',
                'message': 'MCQ answer saved',
                'is_correct': is_correct
            }), 200
            
        elif answer_type == 'coding':
            problem_id = data.get('questionId')
            language = data.get('language')
            code = data.get('code')
            tests_passed = data.get('testsPassed', 0)
            total_tests = data.get('totalTests', 0)
            
            save_coding_submission(
                assessment_id=assessment_id,
                problem_id=problem_id,
                language=language,
                code=code,
                test_cases_passed=tests_passed,
                total_test_cases=total_tests
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Coding solution saved'
            }), 200
            
        elif answer_type == 'psychometric':
            question_id = data.get('questionId')
            trait = data.get('trait')
            score = data.get('score')
            scenario_response = data.get('scenarioResponse', None)
            
            save_psychometric_response(
                assessment_id=assessment_id,
                question_id=question_id,
                trait=trait,
                score=score,
                scenario_response=scenario_response
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Psychometric response saved'
            }), 200
            
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid answer type'
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to save answer: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/<int:assessment_id>/complete', methods=['POST'])
def complete_assessment(assessment_id):
    """
    Complete assessment and calculate final scores
    
    Calculates:
        - Technical score (60% MCQ, 40% Coding)
        - Psychometric score (average of traits)
        - Overall score (70% technical, 30% psychometric)
        - Preliminary hiring decision
    
    Returns:
        - All scores
        - AI hiring recommendation
        - Decision status
    """
    try:
        logger.info(f"Assessment {assessment_id}: Starting completion process")
        
        # Get assessment
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            logger.error(f"Assessment {assessment_id}: Not found")
            return jsonify({
                'status': 'error',
                'message': 'Assessment not found'
            }), 404
        
        candidate_id = assessment['candidate_id']
        logger.info(f"Assessment {assessment_id}: Candidate ID {candidate_id}")
        
        # Calculate scores
        mcq_score = get_mcq_score(assessment_id)
        logger.info(f"Assessment {assessment_id}: MCQ Score = {mcq_score}")
        
        coding_score = get_coding_score(assessment_id)
        logger.info(f"Assessment {assessment_id}: Coding Score = {coding_score}")
        
        psychometric_scores = get_psychometric_scores(assessment_id)
        logger.info(f"Assessment {assessment_id}: Psychometric Scores = {psychometric_scores}")
        
        # Calculate technical score (60% MCQ, 40% Coding)
        technical_score = (mcq_score * 0.6) + (coding_score * 0.4)
        logger.info(f"Assessment {assessment_id}: Technical Score = {technical_score} (MCQ: {mcq_score}, Coding: {coding_score})")
        
        # Calculate average psychometric score
        if psychometric_scores:
            avg_psychometric = sum(psychometric_scores.values()) / len(psychometric_scores)
        else:
            avg_psychometric = 0
        logger.info(f"Assessment {assessment_id}: Avg Psychometric = {avg_psychometric}")
        
        # Calculate overall score (70% technical, 30% psychometric)
        overall_score = (technical_score * 0.7) + (avg_psychometric * 10 * 0.3)
        logger.info(f"Assessment {assessment_id}: Overall Score = {overall_score}")
        
        # Determine preliminary decision and AI recommendation
        if overall_score >= 70:
            decision = "Recommend for Hire"
            rationale = "Strong technical and soft skills demonstrated. Candidate shows excellent problem-solving ability and communication."
            recommendation = "Proceed to HR discussion"
        elif overall_score >= 50:
            decision = "Consider for Interview"
            rationale = "Moderate technical performance with decent soft skills. Candidate shows potential but needs further evaluation."
            recommendation = "Conduct follow-up technical interview"
        else:
            decision = "Not Recommended"
            rationale = "Performance below acceptable threshold. Skills not aligned with role requirements."
            recommendation = "Archive application"
        
        logger.info(f"Assessment {assessment_id}: Decision = {decision}")
        
        # Update assessment in database with completed status
        logger.info(f"Assessment {assessment_id}: Updating database with scores")
        update_assessment_scores(
            assessment_id=assessment_id,
            technical_score=technical_score,
            psychometric_score=avg_psychometric * 10,
            decision=decision,
            rationale=rationale
        )
        logger.info(f"Assessment {assessment_id}: Scores updated successfully")
        
        # Update scheduled assessment to completed
        scheduled = get_scheduled_assessment(candidate_id)
        if scheduled:
            logger.info(f"Assessment {assessment_id}: Updating scheduled assessment {scheduled['id']} to completed")
            update_scheduled_assessment_status(
                scheduled_assessment_id=scheduled['id'],
                status='completed',
                assessment_id=assessment_id
            )
        
        logger.info(f"Assessment {assessment_id}: COMPLETED SUCCESSFULLY - Overall: {overall_score}, Decision: {decision}")
        
        return jsonify({
            'status': 'success',
            'message': 'Assessment completed successfully',
            'data': {
                'assessment_id': assessment_id,
                'candidate_id': candidate_id,
                'scores': {
                    'mcq': round(mcq_score, 2),
                    'coding': round(coding_score, 2),
                    'technical': round(technical_score, 2),
                    'psychometric': round(avg_psychometric * 10, 2),
                    'overall': round(overall_score, 2)
                },
                'psychometric_breakdown': {k: round(v, 2) for k, v in psychometric_scores.items()} if psychometric_scores else {},
                'decision': decision,
                'rationale': rationale,
                'ai_recommendation': recommendation
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Assessment {assessment_id}: FAILED to complete - Error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to complete assessment: {str(e)}'
        }), 500


# ============================================================================
#                    TOKEN-BASED ASSESSMENT ACCESS
# ============================================================================

@interviewee_bp.route('/assessment/verify/<token>', methods=['GET'])
def verify_assessment_token(token):
    """
    Verify an assessment token and return assessment details.
    This is used when a candidate clicks their assessment link.
    
    Returns:
        - Assessment status
        - Candidate info
        - Whether proctoring is enabled
        - Time remaining until/since scheduled time
    """
    try:
        # Get assessment by token
        assessment = get_assessment_by_token(token)
        if not assessment:
            return jsonify({
                'status': 'error',
                'message': 'Invalid assessment link. Please check your email for the correct link.'
            }), 404
        
        # Check status
        if assessment['status'] == 'completed':
            return jsonify({
                'status': 'error',
                'message': 'This assessment has already been completed.'
            }), 400
        
        if assessment['status'] == 'cancelled':
            return jsonify({
                'status': 'error',
                'message': 'This assessment has been cancelled. Please contact your recruiter.'
            }), 400
        
        # Calculate time until scheduled (using IST)
        ist = pytz.timezone('Asia/Kolkata')
        scheduled_dt = datetime.fromisoformat(str(assessment['scheduled_time']).replace('Z', ''))
        # If scheduled_dt is naive, assume it's IST
        if scheduled_dt.tzinfo is None:
            scheduled_dt = ist.localize(scheduled_dt)
        current_dt = datetime.now(ist)
        minutes_until = int((scheduled_dt - current_dt).total_seconds() / 60)
        
        # Check if within window (±30 minutes)
        can_start = abs(minutes_until) <= 30
        
        return jsonify({
            'status': 'success',
            'data': {
                'candidate_name': assessment['candidate_name'],
                'candidate_email': assessment['candidate_email'],
                'scheduled_time': str(assessment['scheduled_time']),
                'minutes_until_start': minutes_until,
                'can_start': can_start,
                'proctoring_enabled': assessment['proctoring_enabled'],
                'assessment_status': assessment['status'],
                'already_started': assessment['status'] == 'in_progress'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to verify assessment: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/start-by-token/<token>', methods=['POST'])
def start_assessment_with_token(token):
    """
    Start assessment using access token.
    This endpoint validates the token and returns assessment questions.
    
    Returns:
        - MCQ questions (without answers)
        - Coding problem
        - Psychometric scenarios
        - Assessment ID for tracking
    """
    try:
        logger.info(f"Token verification requested: {token[:10]}...")
        
        # Get assessment by token
        assessment = get_assessment_by_token(token)
        if not assessment:
            logger.warning(f"Token not found or invalid: {token[:10]}...")
            return jsonify({
                'status': 'error',
                'message': 'Invalid assessment link.'
            }), 404
        
        # Check status
        if assessment['status'] == 'completed':
            return jsonify({
                'status': 'error',
                'message': 'This assessment has already been completed.'
            }), 400
        
        # Check time window (using IST)
        ist = pytz.timezone('Asia/Kolkata')
        scheduled_dt = datetime.fromisoformat(str(assessment['scheduled_time']).replace('Z', ''))
        # If scheduled_dt is naive, assume it's IST
        if scheduled_dt.tzinfo is None:
            scheduled_dt = ist.localize(scheduled_dt)
        current_dt = datetime.now(ist)
        minutes_diff = int((current_dt - scheduled_dt).total_seconds() / 60)
        
        if abs(minutes_diff) > 30 and assessment['status'] != 'in_progress':
            return jsonify({
                'status': 'error',
                'message': f'Assessment can only be started within ±30 minutes of scheduled time. Currently {abs(minutes_diff)} minutes away.',
                'data': {
                    'scheduled_time': str(assessment['scheduled_time']),
                    'minutes_away': abs(minutes_diff)
                }
            }), 403
        
        # If already in progress, resume
        if assessment['status'] == 'in_progress' and assessment['assessment_id']:
            assessment_id = assessment['assessment_id']
        else:
            # Start the assessment
            start_assessment_by_token(token)
            
            # Create assessment record
            assessment_id = create_assessment(assessment['candidate_id'])
            
            # Update scheduled assessment with assessment_id
            update_scheduled_assessment_status(
                scheduled_assessment_id=assessment['id'],
                status='in_progress',
                assessment_id=assessment_id
            )
        
        # Get questions
        mcq_questions = get_mcq_questions(count=10)
        coding_problem = get_coding_problem(difficulty="easy")
        psychometric_scenarios = get_psychometric_scenarios(count=3)
        
        # Remove answers from MCQ questions
        mcq_for_frontend = []
        for q in mcq_questions:
            mcq_for_frontend.append({
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
                "time_limit": q.get("time_limit", 60),
                "category": q.get("category", "general"),
                "difficulty": q.get("difficulty", "medium")
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Assessment started successfully',
            'data': {
                'assessment_id': assessment_id,
                'candidate_id': assessment['candidate_id'],
                'candidate_name': assessment['candidate_name'],
                'proctoring_enabled': assessment['proctoring_enabled'],
                'mcq_questions': mcq_for_frontend,
                'coding_problem': {
                    'id': coding_problem['id'],
                    'title': coding_problem['title'],
                    'description': coding_problem['description'],
                    'example': coding_problem.get('example', ''),
                    'difficulty': coding_problem['difficulty']
                },
                'psychometric_scenarios': psychometric_scenarios,
                'duration_minutes': 60
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start assessment: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/<int:assessment_id>/violation', methods=['POST'])
def report_violation(assessment_id):
    """
    Report a proctoring violation during assessment.
    Called by frontend when face detection or other monitoring detects issues.
    
    Expected JSON body:
        - violation_type: Type of violation (no_face, multiple_faces, tab_switch, etc.)
        - description: Description of the violation
        - severity: low, medium, high, critical (optional, defaults to medium)
        - screenshot_url: URL to screenshot evidence (optional)
    """
    try:
        data = request.get_json() or {}
        
        violation_type = data.get('violation_type')
        description = data.get('description', '')
        severity = data.get('severity', 'medium')
        screenshot_url = data.get('screenshot_url')
        
        if not violation_type:
            return jsonify({
                'status': 'error',
                'message': 'violation_type is required'
            }), 400
        
        # Record the violation
        violation_id = record_proctoring_violation(
            assessment_id=assessment_id,
            violation_type=violation_type,
            description=description,
            severity=severity,
            screenshot_url=screenshot_url
        )
        
        # Get current violation count
        violation_count = count_violations_for_assessment(assessment_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Violation recorded',
            'data': {
                'violation_id': violation_id,
                'total_violations': violation_count
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to record violation: {str(e)}'
        }), 500


# Export blueprint
__all__ = ['interviewee_bp']
