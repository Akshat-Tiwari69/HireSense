"""
Interviewee Routes Module
Handles assessment endpoints for candidates
Includes assessment time validation (±30 minute window)
Optimized with connection pooling and query efficiency
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import pytz
import logging
from functools import wraps

# Import connection pool decorator
try:
    from db_config import connection_pool
except ImportError:
    # Fallback decorator if not available
    def connection_pool(f):
        return f

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
    update_candidate_status,
    get_mcq_score,
    get_coding_score,
    get_psychometric_scores,
    get_assessment_by_token,
    start_assessment_by_token,
    record_proctoring_violation,
    count_violations_for_assessment,
    save_mcq_response,
    save_coding_submission,
    save_psychometric_response,
    save_assessment_questions,
    get_assessment_questions,
    update_assessment_time_elapsed,
    get_assessment_time_elapsed,
    get_saved_mcq_answers,
    get_saved_psychometric_answers,
    get_saved_coding_submission
)
from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
from ai_question_generator import get_ai_question_generator


# Create blueprint for interviewee routes
interviewee_bp = Blueprint('interviewee', __name__)


@interviewee_bp.route('/my-assessment/<int:candidate_id>', methods=['GET'])
@connection_pool
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
        
        # Get current time in UTC ISO format
        current_time = f"{datetime.utcnow().isoformat()}Z"
        
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
@connection_pool
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
        
        # Get current time in UTC ISO format
        current_time = f"{datetime.utcnow().isoformat()}Z"
        
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
                mcq_for_frontend = [{
                    "id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                    "time_limit": q["time_limit"],
                    "category": q["category"],
                    "difficulty": q["difficulty"]
                } for q in mcq_questions]
                
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
        
        # Get candidate skills for AI-generated questions
        candidate = get_candidate_by_id(candidate_id)
        candidate_skills = []
        if candidate and candidate.get('parsed_skills'):
            skills_str = candidate['parsed_skills']
            if isinstance(skills_str, str):
                candidate_skills = [s.strip() for s in skills_str.replace('\n', ',').split(',') if s.strip()]
        
        logger.info(f"Generating AI questions for candidate {candidate_id} with skills: {candidate_skills[:10]}")
        
        # Generate AI-powered questions based on candidate's resume
        try:
            ai_generator = get_ai_question_generator()
            
            if candidate_skills:
                mcq_questions = ai_generator.generate_mcq_questions(candidate_skills, count=10, difficulty="mixed")
                coding_problem = ai_generator.generate_coding_problem(candidate_skills, difficulty="medium")
            else:
                mcq_questions = ai_generator._get_fallback_mcq_questions(10)
                coding_problem = ai_generator._get_fallback_coding_problem("medium")
            
            psychometric_scenarios = ai_generator.generate_psychometric_scenarios(count=3)
        except Exception as e:
            logger.warning(f"AI question generation failed: {str(e)}")
            mcq_questions = get_mcq_questions(count=10)
            coding_problem = get_coding_problem(difficulty="easy")
            psychometric_scenarios = get_psychometric_scenarios(count=3)
        
        # Remove answers from questions for frontend
        mcq_for_frontend = [{
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "time_limit": q.get("time_limit", 60),
            "category": q.get("category", "general"),
            "difficulty": q.get("difficulty", "medium")
        } for q in mcq_questions]
        
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
                    'example': coding_problem.get('example', ''),
                    'difficulty': coding_problem['difficulty'],
                    'constraints': coding_problem.get('constraints', []),
                    'hints': coding_problem.get('hints', []),
                    'starter_code': coding_problem.get('starter_code', {}),
                    'test_cases': [tc for tc in coding_problem.get('test_cases', []) if not tc.get('is_hidden', False)]
                },
                'psychometric_scenarios': psychometric_scenarios,
                'ai_generated': bool(candidate_skills)
            }
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start assessment: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/<int:assessment_id>/submit-answer', methods=['POST'])
@connection_pool
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
            
            # First try to get questions from stored assessment questions (AI-generated)
            stored_questions = get_assessment_questions(assessment_id)
            questions = []
            if stored_questions and stored_questions.get('mcq_questions'):
                questions = stored_questions['mcq_questions']
                logger.info(f"Using stored questions for assessment {assessment_id}, {len(questions)} questions found")
            else:
                # Fallback to static question bank
                questions = get_mcq_questions(count=20)
                logger.info(f"Using static question bank, {len(questions)} questions")
            
            correct_answer = None
            correct_option_text = None
            
            # Find the correct answer for this question (handle both int and string IDs)
            question_id_int = int(question_id) if isinstance(question_id, str) else question_id
            logger.info(f"Looking for question ID {question_id_int} in {len(questions)} questions")
            
            for q in questions:
                q_id = int(q['id']) if isinstance(q['id'], str) else q['id']
                if q_id == question_id_int:
                    correct_option_text = q.get('correct_answer')
                    logger.info(f"Found question {q_id}, correct_answer field: '{correct_option_text}'")
                    if correct_option_text:
                        # Find which option letter matches the correct answer text (with normalization)
                        correct_text_normalized = correct_option_text.strip().lower()
                        for idx, option in enumerate(q['options']):
                            option_normalized = option.strip().lower()
                            if option_normalized == correct_text_normalized:
                                correct_answer = ['A', 'B', 'C', 'D'][idx]
                                logger.info(f"[OK] Correct answer is option {correct_answer} (index {idx}): '{option}'")
                                break
                        
                        # If still not found after normalization, log all options for debugging
                        if not correct_answer:
                            logger.error(f"[ERROR] Could not match correct_answer '{correct_option_text}' with any option. Options: {q['options']}")
                    break
            
            # If correct answer not found, still save the response but mark is_correct as None
            if not correct_answer:
                logger.warning(f"Could not find correct answer for question {question_id}, saving response anyway. Questions have IDs: {[q.get('id') for q in questions[:5]]}")
                is_correct = None
            else:
                is_correct = (selected == correct_answer)
                logger.info(f"Answer for Q{question_id_int}: selected={selected}, correct={correct_answer}, is_correct={is_correct}")
            
            save_mcq_response(
                assessment_id=assessment_id,
                question_id=question_id_int,
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
            
            logger.info(f"Saving coding submission for assessment {assessment_id}: {tests_passed}/{total_tests} tests passed, language={language}")
            
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
                'message': 'Coding solution saved',
                'tests_passed': tests_passed,
                'total_tests': total_tests
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
@connection_pool
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
        
        # Check if coding problem was assigned
        questions = get_assessment_questions(assessment_id)
        has_coding = False
        if questions and questions.get('coding_problem'):
            has_coding = True
            
        # Calculate technical score
        if has_coding:
            # 60% MCQ, 40% Coding
            technical_score = (float(mcq_score) * 0.6) + (float(coding_score) * 0.4)
            logger.info(f"Assessment {assessment_id}: Technical Score = {technical_score} (MCQ: {mcq_score}, Coding: {coding_score})")
        else:
            # 100% MCQ if no coding problem assigned (non-technical roles)
            technical_score = float(mcq_score)
            logger.info(f"Assessment {assessment_id}: Technical Score = {technical_score} (MCQ ONLY, no coding assigned)")
        
        # Calculate average psychometric score (convert Decimal to float for Postgres compatibility)
        if psychometric_scores:
            psycho_values = [float(v) for v in psychometric_scores.values()]
            avg_psychometric = sum(psycho_values) / len(psycho_values)
        else:
            avg_psychometric = 0
        logger.info(f"Assessment {assessment_id}: Avg Psychometric = {avg_psychometric}")
        
        # Calculate overall score (70% technical, 30% psychometric)
        overall_score = (float(technical_score) * 0.7) + (float(avg_psychometric) * 10 * 0.3)
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
        try:
            update_assessment_scores(
                assessment_id=assessment_id,
                technical_score=technical_score,
                psychometric_score=avg_psychometric * 10,
                decision=decision,
                rationale=rationale
            )
            logger.info(f"Assessment {assessment_id}: Scores updated successfully")
        except Exception as e:
            logger.error(f"Assessment {assessment_id}: Failed to update scores - {str(e)}", exc_info=True)
            raise
        
        # Update scheduled assessment to completed
        scheduled = get_scheduled_assessment(candidate_id)
        if scheduled:
            logger.info(f"Assessment {assessment_id}: Updating scheduled assessment {scheduled['id']} to completed")
            update_scheduled_assessment_status(
                scheduled_assessment_id=scheduled['id'],
                status='completed',
                assessment_id=assessment_id
            )
        
        # Update candidate status to 'completed'
        logger.info(f"Assessment {assessment_id}: Updating candidate {candidate_id} status to 'completed'")
        update_candidate_status(candidate_id, 'completed')
        
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
@connection_pool
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
        print(f"[VERIFY] ERROR: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Failed to verify assessment: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/start-by-token/<token>', methods=['POST'])
@connection_pool
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
        
        is_resume = False
        time_elapsed = 0
        
        # Check if assessment already exists (created at schedule time)
        if assessment['assessment_id']:
            assessment_id = assessment['assessment_id']
            
            # Check if this is a resume (already started) or first start
            if assessment['status'] == 'in_progress':
                is_resume = True
                time_elapsed = get_assessment_time_elapsed(assessment_id)
                logger.info(f"Resuming assessment {assessment_id}, elapsed time: {time_elapsed}s")
            else:
                # First time starting - update status to in_progress
                start_assessment_by_token(token)
                update_scheduled_assessment_status(
                    scheduled_assessment_id=assessment['id'],
                    status='in_progress',
                    assessment_id=assessment_id
                )
                logger.info(f"First start of assessment {assessment_id}")
            
            # Try to load stored questions (should exist from schedule time)
            stored_questions = get_assessment_questions(assessment_id)
            if stored_questions:
                logger.info(f"Loaded pre-generated questions for assessment {assessment_id}")
                mcq_questions = stored_questions.get('mcq_questions', [])
                coding_problem = stored_questions.get('coding_problem')
                psychometric_scenarios = stored_questions.get('psychometric_scenarios', [])
            else:
                # Questions not stored (legacy or edge case), will generate below
                logger.warning(f"No stored questions for assessment {assessment_id}, will generate")
                stored_questions = None
        else:
            # Legacy case: assessment not created at schedule time
            start_assessment_by_token(token)
            
            # Create assessment record
            assessment_id = create_assessment(assessment['candidate_id'])
            
            # Update scheduled assessment with assessment_id
            update_scheduled_assessment_status(
                scheduled_assessment_id=assessment['id'],
                status='in_progress',
                assessment_id=assessment_id
            )
            stored_questions = None
            logger.info(f"Created new assessment {assessment_id} (legacy path)")
        
        # Generate questions only if not already loaded from storage
        if not stored_questions:
            # Get candidate skills for AI-generated questions
            candidate = get_candidate_by_id(assessment['candidate_id'])
            candidate_skills = []
            if candidate and candidate.get('parsed_skills'):
                skills_str = candidate['parsed_skills']
                if isinstance(skills_str, str):
                    # Parse skills from comma-separated or newline-separated string
                    candidate_skills = [s.strip() for s in skills_str.replace('\n', ',').split(',') if s.strip()]
            
            logger.info(f"Generating AI questions for candidate skills: {candidate_skills[:10]}")
            
            # Check if this is a technical role (includes coding exam)
            is_technical_role = assessment.get('is_technical_role', True)
            logger.info(f"Assessment is_technical_role: {is_technical_role}")
            
            # Generate AI-powered questions based on candidate's resume
            try:
                ai_generator = get_ai_question_generator()
                logger.info(f"AI Generator initialized, client exists: {ai_generator.client is not None}")
                
                if candidate_skills:
                    # Generate personalized questions based on skills
                    logger.info(f"Generating personalized questions for skills: {candidate_skills[:5]}")
                    mcq_questions = ai_generator.generate_mcq_questions(candidate_skills, count=10, difficulty="mixed")
                    logger.info(f"Generated {len(mcq_questions)} MCQ questions")
                    
                    # Only generate coding problem for technical roles
                    if is_technical_role:
                        coding_problem = ai_generator.generate_coding_problem(candidate_skills, difficulty="medium")
                        logger.info(f"Generated coding problem: {coding_problem.get('title', 'Unknown')}")
                    else:
                        coding_problem = None
                        logger.info("Skipping coding problem for non-technical role")
                else:
                    # Fallback to default questions
                    logger.info("No skills found, using fallback questions")
                    mcq_questions = ai_generator._get_fallback_mcq_questions(10)
                    if is_technical_role:
                        coding_problem = ai_generator._get_fallback_coding_problem("medium")
                    else:
                        coding_problem = None
                        logger.info("Skipping coding problem for non-technical role")
                
                psychometric_scenarios = ai_generator.generate_psychometric_scenarios(count=3)
                logger.info(f"Generated {len(psychometric_scenarios)} psychometric scenarios")
                
                logger.info(f"Successfully generated AI questions for assessment {assessment_id}")
            except Exception as e:
                logger.warning(f"AI question generation failed, using fallback: {str(e)}")
                # Fallback to static questions
                mcq_questions = get_mcq_questions(count=10)
                if is_technical_role:
                    coding_problem = get_coding_problem(difficulty="easy")
                else:
                    coding_problem = None
                psychometric_scenarios = get_psychometric_scenarios(count=3)
            
            # Store questions for future resume
            save_assessment_questions(assessment_id, {
                'mcq_questions': mcq_questions,
                'coding_problem': coding_problem,
                'psychometric_scenarios': psychometric_scenarios
            })
            logger.info(f"Stored questions for assessment {assessment_id}")
        
        # Remove answers from MCQ questions for frontend
        mcq_for_frontend = [
            {
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
                "time_limit": q.get("time_limit", 60),
                "category": q.get("category", "general"),
                "difficulty": q.get("difficulty", "medium")
            }
            for q in mcq_questions
        ]
        
        # Calculate remaining time
        total_duration_seconds = 60 * 60  # 60 minutes
        remaining_seconds = max(0, total_duration_seconds - time_elapsed)
        
        # Get saved answers if resuming
        saved_mcq_answers = {}
        saved_psychometric_answers = {}
        saved_coding = None
        if is_resume:
            try:
                saved_mcq_answers = get_saved_mcq_answers(assessment_id)
                saved_psychometric_answers = get_saved_psychometric_answers(assessment_id)
                saved_coding = get_saved_coding_submission(assessment_id)
                logger.info(f"Loaded saved answers for assessment {assessment_id}: MCQ={len(saved_mcq_answers)}, Psychometric={len(saved_psychometric_answers)}, Coding={'yes' if saved_coding else 'no'}")
            except Exception as e:
                logger.warning(f"Failed to load saved answers for assessment {assessment_id}: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Assessment resumed successfully' if is_resume else 'Assessment started successfully',
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
                    'difficulty': coding_problem['difficulty'],
                    'constraints': coding_problem.get('constraints', []),
                    'hints': coding_problem.get('hints', []),
                    'starter_code': coding_problem.get('starter_code', {}),
                    'test_cases': [tc for tc in coding_problem.get('test_cases', []) if not tc.get('is_hidden', False)]
                } if coding_problem else None,
                'is_technical_role': assessment.get('is_technical_role', True),
                'psychometric_scenarios': psychometric_scenarios,
                'duration_minutes': 60,
                'remaining_seconds': remaining_seconds,
                'is_resume': is_resume,
                'ai_generated': bool(not is_resume or not stored_questions),
                'saved_mcq_answers': saved_mcq_answers,
                'saved_psychometric_answers': saved_psychometric_answers,
                'saved_coding': saved_coding
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to start assessment: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/<int:assessment_id>/violation', methods=['POST'])
@connection_pool
def report_violation(assessment_id):
    """
    Report a proctoring violation during assessment.
    Called by frontend when face detection or other monitoring detects issues.
    
    Expected JSON body:
        - violation_type: Type of violation (no_face, multiple_faces, tab_switch, etc.)
        - description: Description of the violation
        - severity: low, medium, high, critical (optional, defaults to medium)
        - screenshot: Base64 encoded screenshot image (optional)
    """
    try:
        data = request.get_json() or {}
        
        violation_type = data.get('violation_type')
        description = data.get('description', '')
        severity = data.get('severity', 'medium')
        screenshot_data = data.get('screenshot')  # Base64 encoded image
        
        if not violation_type:
            return jsonify({
                'status': 'error',
                'message': 'violation_type is required'
            }), 400
        
        # Save screenshot to file if provided
        screenshot_url = None
        if screenshot_data:
            try:
                import base64
                import os
                from datetime import datetime
                
                # Create screenshots directory if it doesn't exist
                screenshots_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'violations')
                os.makedirs(screenshots_dir, exist_ok=True)
                
                # Generate unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'violation_{assessment_id}_{violation_type}_{timestamp}.jpg'
                filepath = os.path.join(screenshots_dir, filename)
                
                # Decode and save the image
                # Remove data URL prefix if present
                if ',' in screenshot_data:
                    screenshot_data = screenshot_data.split(',')[1]
                
                image_bytes = base64.b64decode(screenshot_data)
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                screenshot_url = f'/uploads/violations/{filename}'
                logger.info(f"Saved violation screenshot: {screenshot_url}")
            except Exception as e:
                logger.warning(f"Failed to save violation screenshot: {e}")
        
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
        
        logger.info(f"Violation recorded for assessment {assessment_id}: {violation_type} ({severity}) - Total: {violation_count}")
        
        return jsonify({
            'status': 'success',
            'message': 'Violation recorded',
            'data': {
                'violation_id': violation_id,
                'total_violations': violation_count,
                'screenshot_saved': screenshot_url is not None
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to record violation: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to record violation: {str(e)}'
        }), 500


@interviewee_bp.route('/assessment/<int:assessment_id>/sync-time', methods=['POST'])
@connection_pool
def sync_assessment_time(assessment_id):
    """
    Sync the elapsed time for an assessment.
    Called periodically by frontend to save progress.
    
    Expected JSON body:
        - time_elapsed_seconds: Total seconds elapsed since assessment started
    """
    try:
        data = request.get_json() or {}
        
        time_elapsed = data.get('time_elapsed_seconds')
        if time_elapsed is None:
            return jsonify({
                'status': 'error',
                'message': 'time_elapsed_seconds is required'
            }), 400
        
        update_assessment_time_elapsed(assessment_id, int(time_elapsed))
        
        return jsonify({
            'status': 'success',
            'message': 'Time synced'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to sync time: {str(e)}'
        }), 500


# Export blueprint
__all__ = ['interviewee_bp']
