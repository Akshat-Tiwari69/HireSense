"""
Interviewee answer routes — submitting responses and completing assessments.
"""

import logging
from flask import Blueprint, request, jsonify

try:
    from db_config import connection_pool
except ImportError:
    def connection_pool(f):
        return f

from db_helpers import (
    get_assessment_by_id,
    get_scheduled_assessment,
    get_assessment_questions,
    save_mcq_response,
    save_coding_submission,
    save_psychometric_response,
    update_assessment_scores,
    update_scheduled_assessment_status,
    update_candidate_status,
    get_mcq_score,
    get_coding_score,
    get_psychometric_scores,
)
from questions_bank import get_mcq_questions

logger = logging.getLogger(__name__)

interviewee_answers_bp = Blueprint('interviewee_answers', __name__)


@interviewee_answers_bp.route('/assessment/<int:assessment_id>/submit-answer', methods=['POST'])
@connection_pool
def submit_answer(assessment_id):
    try:
        data = request.json
        answer_type = data.get('type')

        if answer_type == 'mcq':
            question_id = data.get('questionId')
            selected = data.get('answer')
            time_spent = data.get('timeSpent', 0)

            assessment = get_assessment_by_id(assessment_id)
            if not assessment:
                return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404

            stored_questions = get_assessment_questions(assessment_id)
            questions = (stored_questions.get('mcq_questions', [])
                         if stored_questions else get_mcq_questions(count=20))

            question_id_int = int(question_id) if isinstance(question_id, str) else question_id
            correct_answer = _resolve_correct_answer(question_id_int, questions)
            is_correct = (selected == correct_answer) if correct_answer is not None else None

            save_mcq_response(
                assessment_id=assessment_id, question_id=question_id_int,
                selected_answer=selected, is_correct=is_correct, time_spent=time_spent
            )
            return jsonify({'status': 'success', 'message': 'MCQ answer saved'}), 200

        elif answer_type == 'coding':
            save_coding_submission(
                assessment_id=assessment_id,
                problem_id=data.get('questionId'),
                language=data.get('language'),
                code=data.get('code'),
                test_cases_passed=data.get('testsPassed', 0),
                total_test_cases=data.get('totalTests', 0)
            )
            return jsonify({
                'status': 'success', 'message': 'Coding solution saved',
                'tests_passed': data.get('testsPassed', 0), 'total_tests': data.get('totalTests', 0)
            }), 200

        elif answer_type == 'psychometric':
            selected_option = data.get('selectedOption')
            scenario_response = data.get('scenarioResponse') or (
                str(selected_option) if selected_option is not None else None
            )
            save_psychometric_response(
                assessment_id=assessment_id,
                question_id=data.get('questionId'),
                trait=data.get('trait'),
                score=data.get('score'),
                scenario_response=scenario_response
            )
            return jsonify({'status': 'success', 'message': 'Psychometric response saved'}), 200

        return jsonify({'status': 'error', 'message': 'Invalid answer type'}), 400

    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to save answer'}), 500


@interviewee_answers_bp.route('/assessment/<int:assessment_id>/complete', methods=['POST'])
@connection_pool
def complete_assessment(assessment_id):
    try:
        logger.info(f"Assessment {assessment_id}: Starting completion process")

        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404

        candidate_id = assessment['candidate_id']

        is_technical_role = True
        try:
            scheduled = get_scheduled_assessment(candidate_id)
            if scheduled:
                val = scheduled.get('is_technical_role')
                if val is not None:
                    is_technical_role = bool(val)
        except Exception as e:
            logger.warning(f"Could not determine is_technical_role: {e}")

        mcq_score = get_mcq_score(assessment_id)
        coding_score = get_coding_score(assessment_id) if is_technical_role else 0
        psychometric_scores = get_psychometric_scores(assessment_id)

        if is_technical_role:
            technical_score = (float(mcq_score) * 0.6) + (float(coding_score) * 0.4)
        else:
            technical_score = float(mcq_score)

        avg_psychometric = (
            sum(float(v) for v in psychometric_scores.values()) / len(psychometric_scores)
            if psychometric_scores else 0
        )

        overall_score = (float(technical_score) * 0.7) + (float(avg_psychometric) * 10 * 0.3)

        if overall_score >= 70:
            decision = "Recommend for Hire"
            rationale = "Strong technical and soft skills demonstrated."
            recommendation = "Proceed to HR discussion"
        elif overall_score >= 50:
            decision = "Consider for Interview"
            rationale = "Moderate technical performance with decent soft skills."
            recommendation = "Conduct follow-up technical interview"
        else:
            decision = "Not Recommended"
            rationale = "Performance below acceptable threshold."
            recommendation = "Archive application"

        update_assessment_scores(
            assessment_id=assessment_id,
            technical_score=technical_score,
            psychometric_score=avg_psychometric * 10,
            decision=decision,
            rationale=rationale
        )

        scheduled = get_scheduled_assessment(candidate_id)
        if scheduled:
            update_scheduled_assessment_status(
                scheduled_assessment_id=scheduled['id'], status='completed', assessment_id=assessment_id
            )

        update_candidate_status(candidate_id, 'completed')

        logger.info(f"Assessment {assessment_id}: COMPLETED — Overall: {overall_score}, Decision: {decision}")

        return jsonify({'status': 'success', 'message': 'Assessment completed successfully', 'data': {
            'assessment_id': assessment_id, 'candidate_id': candidate_id,
            'scores': {
                'mcq': round(mcq_score, 2), 'coding': round(coding_score, 2),
                'technical': round(technical_score, 2),
                'psychometric': round(avg_psychometric * 10, 2),
                'overall': round(overall_score, 2)
            },
            'psychometric_breakdown': {k: round(v, 2) for k, v in psychometric_scores.items()} if psychometric_scores else {},
            'decision': decision, 'rationale': rationale, 'ai_recommendation': recommendation
        }}), 200

    except Exception as e:
        logger.error(f"Assessment {assessment_id}: FAILED to complete — {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to complete assessment'}), 500


def _resolve_correct_answer(question_id_int, questions):
    """Try 5 matching strategies to find the correct answer letter (A/B/C/D)."""
    for q in questions:
        q_id = int(q['id']) if isinstance(q['id'], str) else q['id']
        if q_id != question_id_int:
            continue
        ct = q.get('correct_answer')
        if not ct:
            return None
        ct_upper = ct.strip().upper()
        if ct_upper in ('A', 'B', 'C', 'D'):
            return ct_upper
        if ct.strip() in ('0', '1', '2', '3'):
            return ('A', 'B', 'C', 'D')[int(ct.strip())]
        ct_lower = ct.strip().lower()
        letters = ('A', 'B', 'C', 'D')
        for idx, option in enumerate(q['options']):
            if option.strip().lower() == ct_lower:
                return letters[idx]
        for idx, option in enumerate(q['options']):
            opt = option.strip().lower()
            if ct_lower in opt or opt in ct_lower:
                return letters[idx]
        for idx, option in enumerate(q['options']):
            opt = option.strip().lower()
            if opt.startswith(ct_lower[:20]) or ct_lower.startswith(opt[:20]):
                return letters[idx]
        return None
    return None
