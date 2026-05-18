"""
Interviewee session routes — verifying access, starting, and resuming assessments.
"""

import logging
import contextlib
from datetime import datetime
import pytz
from flask import Blueprint, request, jsonify

try:
    from db_config import connection_pool, get_connection, return_connection
except ImportError:
    from db_config import get_connection, return_connection
    def connection_pool(f):
        return f

from db_helpers import (
    get_candidate_by_id,
    get_scheduled_assessment,
    check_assessment_time_valid,
    get_assessment_by_id,
    get_assessment_by_token,
    start_assessment_by_token,
    create_assessment,
    update_scheduled_assessment_status,
    save_assessment_questions,
    get_assessment_questions,
    get_assessment_time_elapsed,
    get_saved_mcq_answers,
    get_saved_psychometric_answers,
    get_saved_coding_submission,
)
from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
from ai_question_generator import get_ai_question_generator

logger = logging.getLogger(__name__)

interviewee_session_bp = Blueprint('interviewee_session', __name__)


@interviewee_session_bp.route('/my-assessment/<int:candidate_id>', methods=['GET'])
@connection_pool
def get_my_assessment(candidate_id):
    try:
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

        scheduled = get_scheduled_assessment(candidate_id)
        if not scheduled:
            return jsonify({'status': 'error', 'message': 'No assessment scheduled yet'}), 404

        current_time = f"{datetime.utcnow().isoformat()}Z"
        is_valid, scheduled_time, message = check_assessment_time_valid(
            candidate_id=candidate_id, current_time=current_time, window_minutes=30
        )

        scheduled_dt = datetime.fromisoformat(scheduled['scheduled_time'].replace('Z', '+00:00'))
        current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        minutes_until = int(((scheduled_dt - current_dt).total_seconds()) / 60)

        return jsonify({'status': 'success', 'data': {
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
        }}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to fetch assessment info'}), 500


@interviewee_session_bp.route('/assessment/start/<int:candidate_id>', methods=['POST'])
@connection_pool
def start_assessment(candidate_id):
    try:
        candidate = get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({'status': 'error', 'message': 'Candidate not found'}), 404

        scheduled = get_scheduled_assessment(candidate_id)
        if not scheduled:
            return jsonify({'status': 'error', 'message': 'No assessment scheduled. Please contact your recruiter.'}), 404

        current_time = f"{datetime.utcnow().isoformat()}Z"
        is_valid, scheduled_time, time_message = check_assessment_time_valid(
            candidate_id=candidate_id, current_time=current_time, window_minutes=30
        )

        if not is_valid:
            scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            minutes_diff = int(abs((current_dt - scheduled_dt).total_seconds()) / 60)
            return jsonify({
                'status': 'error',
                'message': f'Assessment not available yet. {time_message}',
                'data': {'scheduled_time': scheduled_time, 'current_time': current_time,
                         'minutes_away': minutes_diff, 'allowed_window': 30}
            }), 403

        if scheduled.get('assessment_id'):
            existing = get_assessment_by_id(scheduled['assessment_id'])
            if existing and existing['status'] in ['started', 'in_progress']:
                assessment_id = existing['id']
                mcq_questions = get_mcq_questions(count=10)
                mcq_for_frontend = [{"id": q["id"], "question": q["question"], "options": q["options"],
                                      "time_limit": q["time_limit"], "category": q["category"],
                                      "difficulty": q["difficulty"]} for q in mcq_questions]
                coding_problem = get_coding_problem(difficulty="easy")
                psychometric_scenarios = get_psychometric_scenarios(count=3)
                return jsonify({'status': 'success', 'message': 'Assessment resumed', 'data': {
                    'assessment_id': assessment_id, 'candidate_id': candidate_id,
                    'mcq_questions': mcq_for_frontend,
                    'coding_problem': {'id': coding_problem['id'], 'title': coding_problem['title'],
                                       'description': coding_problem['description'],
                                       'example': coding_problem['example'],
                                       'difficulty': coding_problem['difficulty']},
                    'psychometric_scenarios': psychometric_scenarios, 'resumed': True
                }}), 200

        assessment_id = create_assessment(candidate_id)
        update_scheduled_assessment_status(
            scheduled_assessment_id=scheduled['id'], status='in_progress', assessment_id=assessment_id
        )

        candidate = get_candidate_by_id(candidate_id)
        candidate_skills = _extract_candidate_skills(candidate)

        applied_job_title, job_required_skills = _fetch_job_for_candidate(candidate_id)
        logger.info(f"Generating AI questions for candidate {candidate_id} (role: {applied_job_title or 'unknown'})")

        mcq_questions, coding_problem, psychometric_scenarios = _generate_questions(
            candidate_skills, job_required_skills, applied_job_title, is_technical=True
        )

        mcq_for_frontend = _strip_answers(mcq_questions)

        return jsonify({'status': 'success', 'message': 'Assessment started successfully', 'data': {
            'assessment_id': assessment_id, 'candidate_id': candidate_id,
            'scheduled_time': scheduled_time, 'mcq_questions': mcq_for_frontend,
            'coding_problem': _format_coding_problem(coding_problem),
            'psychometric_scenarios': psychometric_scenarios,
            'ai_generated': bool(candidate_skills)
        }}), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to start assessment'}), 500


@interviewee_session_bp.route('/assessment/verify/<token>', methods=['GET'])
@connection_pool
def verify_assessment_token(token):
    try:
        assessment = get_assessment_by_token(token)
        if not assessment:
            return jsonify({'status': 'error',
                            'message': 'Invalid assessment link. Please check your email for the correct link.'}), 404

        if assessment['status'] == 'completed':
            return jsonify({'status': 'error', 'message': 'This assessment has already been completed.'}), 400
        if assessment['status'] == 'cancelled':
            return jsonify({'status': 'error',
                            'message': 'This assessment has been cancelled. Please contact your recruiter.'}), 400

        ist = pytz.timezone('Asia/Kolkata')
        scheduled_dt = datetime.fromisoformat(str(assessment['scheduled_time']).replace('Z', ''))
        if scheduled_dt.tzinfo is None:
            scheduled_dt = ist.localize(scheduled_dt)
        current_dt = datetime.now(ist)
        minutes_until = int((scheduled_dt - current_dt).total_seconds() / 60)
        can_start = abs(minutes_until) <= 30

        return jsonify({'status': 'success', 'data': {
            'candidate_name': assessment['candidate_name'],
            'candidate_email': assessment['candidate_email'],
            'scheduled_time': str(assessment['scheduled_time']),
            'minutes_until_start': minutes_until,
            'can_start': can_start,
            'proctoring_enabled': assessment['proctoring_enabled'],
            'assessment_status': assessment['status'],
            'already_started': assessment['status'] == 'in_progress'
        }}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to verify assessment'}), 500


@interviewee_session_bp.route('/assessment/start-by-token/<token>', methods=['POST'])
@connection_pool
def start_assessment_with_token(token):
    try:
        logger.info(f"Token verification requested: {token[:10]}...")
        assessment = get_assessment_by_token(token)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Invalid assessment link.'}), 404

        if assessment['status'] == 'completed':
            return jsonify({'status': 'error', 'message': 'This assessment has already been completed.'}), 400

        ist = pytz.timezone('Asia/Kolkata')
        scheduled_dt = datetime.fromisoformat(str(assessment['scheduled_time']).replace('Z', ''))
        if scheduled_dt.tzinfo is None:
            scheduled_dt = ist.localize(scheduled_dt)
        current_dt = datetime.now(ist)
        minutes_diff = int((current_dt - scheduled_dt).total_seconds() / 60)

        if abs(minutes_diff) > 30 and assessment['status'] != 'in_progress':
            return jsonify({
                'status': 'error',
                'message': f'Assessment can only be started within ±30 minutes of scheduled time. Currently {abs(minutes_diff)} minutes away.',
                'data': {'scheduled_time': str(assessment['scheduled_time']), 'minutes_away': abs(minutes_diff)}
            }), 403

        is_resume = False
        time_elapsed = 0
        stored_questions = None
        is_technical_role = True

        if assessment['status'] == 'in_progress' and assessment['assessment_id']:
            assessment_id = assessment['assessment_id']
            is_resume = True
            time_elapsed = get_assessment_time_elapsed(assessment_id)
            stored_questions = get_assessment_questions(assessment_id)
            if stored_questions:
                mcq_questions = stored_questions.get('mcq_questions', [])
                coding_problem = stored_questions.get('coding_problem', {})
                psychometric_scenarios = stored_questions.get('psychometric_scenarios', [])
        else:
            start_assessment_by_token(token)
            assessment_id = create_assessment(assessment['candidate_id'])
            update_scheduled_assessment_status(
                scheduled_assessment_id=assessment['id'], status='in_progress', assessment_id=assessment_id
            )

        if not stored_questions:
            pconn = None
            try:
                pconn = get_connection()
                pcur = pconn.cursor()
                pcur.execute(
                    "SELECT questions_data, is_technical_role FROM scheduled_assessments WHERE id = %s",
                    (assessment['id'],)
                )
                prow = pcur.fetchone()
                if prow and prow[0]:
                    import json
                    pre_generated = json.loads(prow[0]) if isinstance(prow[0], str) else prow[0]
                    if pre_generated:
                        mcq_questions = pre_generated.get('mcq_questions', [])
                        coding_problem = pre_generated.get('coding_problem')
                        psychometric_scenarios = pre_generated.get('psychometric_scenarios', [])
                        is_technical_role = pre_generated.get('is_technical_role', True)
                        stored_questions = pre_generated
                if prow:
                    is_technical_role = prow[1] if prow[1] is not None else True
            except Exception as pre_err:
                logger.warning(f"Could not load pre-generated questions: {pre_err}")
            finally:
                if pconn:
                    with contextlib.suppress(Exception):
                        return_connection(pconn)

        if not stored_questions:
            candidate = get_candidate_by_id(assessment['candidate_id'])
            candidate_skills = _extract_candidate_skills(candidate)
            applied_job_title, job_required_skills = _fetch_job_for_candidate(assessment['candidate_id'])
            mcq_questions, coding_problem, psychometric_scenarios = _generate_questions(
                candidate_skills, job_required_skills, applied_job_title, is_technical=is_technical_role
            )
            save_assessment_questions(assessment_id, {
                'mcq_questions': mcq_questions, 'coding_problem': coding_problem,
                'psychometric_scenarios': psychometric_scenarios, 'is_technical_role': is_technical_role
            })
            logger.info(f"Stored questions for assessment {assessment_id}")

        mcq_for_frontend = _strip_answers(mcq_questions)
        total_duration_seconds = 60 * 60
        remaining_seconds = max(0, total_duration_seconds - time_elapsed)

        saved_mcq_answers, saved_psychometric_answers, saved_coding = {}, {}, None
        if is_resume:
            try:
                saved_mcq_answers = get_saved_mcq_answers(assessment_id)
                saved_psychometric_answers = get_saved_psychometric_answers(assessment_id)
                saved_coding = get_saved_coding_submission(assessment_id)
            except Exception as e:
                logger.warning(f"Failed to load saved answers: {str(e)}")

        return jsonify({'status': 'success',
                        'message': 'Assessment resumed successfully' if is_resume else 'Assessment started successfully',
                        'data': {
                            'assessment_id': assessment_id,
                            'candidate_id': assessment['candidate_id'],
                            'candidate_name': assessment['candidate_name'],
                            'proctoring_enabled': assessment['proctoring_enabled'],
                            'mcq_questions': mcq_for_frontend,
                            'coding_problem': _format_coding_problem(coding_problem),
                            'psychometric_scenarios': psychometric_scenarios,
                            'is_technical_role': is_technical_role,
                            'duration_minutes': 60,
                            'remaining_seconds': remaining_seconds,
                            'is_resume': is_resume,
                            'ai_generated': bool(not is_resume or not stored_questions),
                            'saved_mcq_answers': saved_mcq_answers,
                            'saved_psychometric_answers': saved_psychometric_answers,
                            'saved_coding': saved_coding
                        }}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to start assessment'}), 500


# ============================================================================
#                             SHARED HELPERS
# ============================================================================

def _extract_candidate_skills(candidate):
    if not candidate:
        return []
    if candidate.get('skills') and isinstance(candidate['skills'], list):
        return [s.strip() for s in candidate['skills'] if isinstance(s, str) and s.strip()]
    skills_raw = candidate.get('parsed_skills')
    if not skills_raw:
        return []
    if isinstance(skills_raw, str):
        try:
            import json as _json
            parsed = _json.loads(skills_raw)
            if isinstance(parsed, list):
                return [s.strip() for s in parsed if isinstance(s, str) and s.strip()]
            return [s.strip() for s in skills_raw.replace('\n', ',').split(',') if s.strip()]
        except Exception:
            return [s.strip() for s in skills_raw.replace('\n', ',').split(',') if s.strip()]
    if isinstance(skills_raw, list):
        return [s.strip() for s in skills_raw if isinstance(s, str) and s.strip()]
    return []


def _fetch_job_for_candidate(candidate_id):
    applied_job_title, job_required_skills = "", []
    jconn = None
    try:
        jconn = get_connection()
        jcur = jconn.cursor()
        jcur.execute(
            """SELECT jd.title, jd.required_skills
               FROM job_descriptions jd
               JOIN candidates c ON c.best_match_job_id = jd.id
               WHERE c.id = %s""",
            (candidate_id,)
        )
        jrow = jcur.fetchone()
        if jrow:
            applied_job_title = jrow[0] or ""
            if jrow[1]:
                job_required_skills = [s.strip() for s in jrow[1].replace('\n', ',').split(',') if s.strip()]
    except Exception as e:
        logger.warning(f"Could not fetch applied job details: {e}")
    finally:
        if jconn:
            with contextlib.suppress(Exception):
                return_connection(jconn)
    return applied_job_title, job_required_skills


def _generate_questions(candidate_skills, job_required_skills, job_title, is_technical=True):
    try:
        ai_generator = get_ai_question_generator()
        if candidate_skills or job_required_skills:
            mcq_questions = ai_generator.generate_mcq_questions(
                candidate_skills, count=10, difficulty="mixed",
                job_title=job_title, job_skills=job_required_skills
            )
            coding_problem = (
                ai_generator.generate_coding_problem(
                    candidate_skills, difficulty="medium", job_title=job_title,
                    is_technical=True, job_skills=job_required_skills
                ) if is_technical else None
            )
        else:
            mcq_questions = ai_generator._get_fallback_mcq_questions(10)
            coding_problem = ai_generator._get_fallback_coding_problem("medium") if is_technical else None
        psychometric_scenarios = ai_generator.generate_psychometric_scenarios(
            job_role=job_title or "Professional", count=3
        )
        return mcq_questions, coding_problem, psychometric_scenarios
    except Exception as e:
        logger.warning(f"AI question generation failed, using fallback: {str(e)}")
        return (
            get_mcq_questions(count=10),
            get_coding_problem(difficulty="easy") if is_technical else None,
            get_psychometric_scenarios(count=3)
        )


def _strip_answers(mcq_questions):
    return [{
        "id": q["id"], "question": q["question"], "options": q["options"],
        "time_limit": q.get("time_limit", 60),
        "category": q.get("category", "general"),
        "difficulty": q.get("difficulty", "medium")
    } for q in mcq_questions]


def _format_coding_problem(coding_problem):
    if not coding_problem:
        return None
    return {
        'id': coding_problem['id'], 'title': coding_problem['title'],
        'description': coding_problem['description'],
        'example': coding_problem.get('example', ''),
        'difficulty': coding_problem['difficulty'],
        'constraints': coding_problem.get('constraints', []),
        'hints': coding_problem.get('hints', []),
        'starter_code': coding_problem.get('starter_code', {}),
        'test_cases': [tc for tc in coding_problem.get('test_cases', []) if not tc.get('is_hidden', False)]
    }
