"""
Interviewee answer routes — submitting responses and completing assessments.
"""

import logging
import re
import json as _json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, request, jsonify

try:
    from db_config import connection_pool
except ImportError:
    def connection_pool(f):
        return f

from db_helpers import (
    get_assessment_by_id,
    get_scheduled_assessment,
    get_scheduled_assessment_by_id,
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
    verify_assessment_access_token,
    get_assessment_by_token,
)
from questions_bank import get_mcq_questions


def _check_assessment_token(assessment_id: int):
    """Return a 403 response if the X-Assessment-Token header is missing or invalid, else None."""
    token = request.headers.get('X-Assessment-Token', '')
    if not verify_assessment_access_token(token, assessment_id):
        return jsonify({'status': 'error', 'message': 'Invalid or missing assessment token'}), 403
    return None

logger = logging.getLogger(__name__)

interviewee_answers_bp = Blueprint('interviewee_answers', __name__)


@interviewee_answers_bp.route('/assessment/<int:assessment_id>/submit-answer', methods=['POST'])
@connection_pool
def submit_answer(assessment_id):
    try:
        err = _check_assessment_token(assessment_id)
        if err:
            return err

        # Guard: assessment must exist and be active
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404
        if assessment.get('status') not in ('started', 'in_progress'):
            return jsonify({'status': 'error', 'message': 'Assessment is not active'}), 400

        data = request.json
        answer_type = data.get('type')

        if answer_type == 'mcq':
            question_id = data.get('questionId')
            selected = data.get('answer')
            time_spent = data.get('timeSpent', 0)

            stored_questions = get_assessment_questions(assessment_id)
            questions = (stored_questions.get('mcq_questions', []) if stored_questions else get_mcq_questions(count=20))

            question_id_int = int(question_id) if isinstance(question_id, str) else question_id
            correct_answer = _resolve_correct_answer(question_id_int, questions)
            is_correct = (selected == correct_answer) if correct_answer is not None else None

            save_mcq_response(
                assessment_id=assessment_id, question_id=question_id_int,
                selected_answer=selected, is_correct=is_correct, time_spent=time_spent
            )
            return jsonify({'status': 'success', 'message': 'MCQ answer saved'}), 200

        elif answer_type == 'coding':
            submitted_code = data.get('code', '')
            language = data.get('language', 'python')

            # Look up stored problem to get server-authoritative test cases and
            # starter code (needed to extract the function name for the harness).
            stored_q = get_assessment_questions(assessment_id)
            coding_problem = stored_q.get('coding_problem') if stored_q else None
            test_cases = coding_problem.get('test_cases', []) if coding_problem else []
            starter_map = coding_problem.get('starter_code', {}) if coding_problem else {}

            total_cases = len(test_cases)  # all cases, visible + hidden

            if test_cases and submitted_code:
                try:
                    tests_passed, total_tests = _evaluate_server_side(
                        submitted_code, language, test_cases, starter_map
                    )
                except Exception as eval_err:
                    logger.warning(f"[CODE EVAL] Server evaluation failed: {eval_err}; scoring 0")
                    tests_passed, total_tests = 0, total_cases
            else:
                tests_passed, total_tests = 0, total_cases

            save_coding_submission(
                assessment_id=assessment_id,
                problem_id=data.get('questionId'),
                language=language,
                code=submitted_code,
                test_cases_passed=tests_passed,
                total_test_cases=total_tests
            )
            return jsonify({'status': 'success', 'message': 'Coding solution saved'}), 200

        elif answer_type == 'psychometric':
            selected_option = data.get('selectedOption')
            scenario_response = data.get('scenarioResponse') or (
                str(selected_option) if selected_option is not None else None
            )

            # Calculate score server-side from stored scenarios (never trust client score)
            trait = data.get('trait')
            score = None
            if selected_option is not None:
                stored_q = get_assessment_questions(assessment_id)
                scenarios = (stored_q.get('psychometric_scenarios', []) if stored_q else [])
                q_id = data.get('questionId')
                for sc in scenarios:
                    if sc.get('id') == q_id:
                        trait = sc.get('trait', trait)
                        optimal = sc.get('optimal_choice')
                        if optimal is not None:
                            distance = abs(int(selected_option) - int(optimal))
                            score_map = {0: 10, 1: 6, 2: 3, 3: 1}
                            score = score_map.get(min(distance, 3), 1)
                        break

            save_psychometric_response(
                assessment_id=assessment_id,
                question_id=data.get('questionId'),
                trait=trait,
                score=score,
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
        err = _check_assessment_token(assessment_id)
        if err:
            return err

        logger.info(f"Assessment {assessment_id}: Starting completion process")

        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404

        candidate_id = assessment['candidate_id']
        scheduled_assessment_id = assessment.get('scheduled_assessment_id')

        is_technical_role = True
        scheduled = None
        try:
            if scheduled_assessment_id:
                scheduled = get_scheduled_assessment_by_id(scheduled_assessment_id)
            else:
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

        if scheduled_assessment_id:
            update_scheduled_assessment_status(
                scheduled_assessment_id=scheduled_assessment_id, status='completed', assessment_id=assessment_id
            )
        elif scheduled:
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


@interviewee_answers_bp.route('/run-code', methods=['POST'])
def run_code():
    """
    Proxy code execution through the backend to Piston API.
    Requires a valid X-Assessment-Token so only active candidates can execute code.
    """
    token = request.headers.get('X-Assessment-Token', '')
    if not token:
        return jsonify({'status': 'error', 'message': 'Assessment token required'}), 403
    assessment_record = get_assessment_by_token(token)
    if not assessment_record or assessment_record.get('status') not in ('in_progress',):
        return jsonify({'status': 'error', 'message': 'Invalid or inactive assessment token'}), 403

    data = request.json or {}
    language = data.get('language')
    version = data.get('version', '*')
    code = data.get('code', '')
    filename = data.get('filename', 'main')
    stdin = data.get('stdin', '')

    if not language or not code:
        return jsonify({'status': 'error', 'message': 'language and code are required'}), 400

    try:
        payload = _json.dumps({
            'language': language,
            'version': version,
            'files': [{'name': filename, 'content': code}],
            'stdin': stdin,
        }).encode('utf-8')

        req = urllib.request.Request(
            _PISTON_URL,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode('utf-8'))

        logger.info(f"[CODE EXEC] lang={language} exit={result.get('run', {}).get('code')}")
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        logger.error(f"[CODE EXEC] Piston error: {e}")
        return jsonify({'status': 'error', 'message': 'Code execution service unavailable'}), 503


# ============================================================================
#                     SERVER-SIDE CODE EVALUATION
# ============================================================================

_PISTON_URL = 'https://emkc.org/api/v2/piston/execute'

_LANG_RUNTIME = {
    'python':     ('python',     '3.10.0'),
    'javascript': ('javascript', '18.15.0'),
    'java':       ('java',       '15.0.2'),
    'cpp':        ('c++',        '10.2.0'),
    'c':          ('c',          '10.2.0'),
}


def _extract_func_name(starter_code: str, language: str):
    """Return the first function name defined in the starter code snippet."""
    if not starter_code:
        return None
    if language == 'python':
        m = re.search(r'^def\s+(\w+)\s*\(', starter_code, re.MULTILINE)
    elif language == 'javascript':
        m = re.search(r'function\s+(\w+)\s*\(', starter_code)
    else:
        return None
    return m.group(1) if m else None


def _build_wrapper(code: str, language: str, tc_input: str, func_name: str):
    """Append a call that invokes func_name with tc_input and prints the result."""
    if language == 'python':
        return f"{code}\n\n# __test__\nprint({func_name}({tc_input}))"
    if language == 'javascript':
        return f"{code}\n\n// __test__\nconsole.log(JSON.stringify({func_name}({tc_input})));"
    return None


def _normalise_output(s: str) -> str:
    return s.replace("'", '"').replace('True', 'true').replace('False', 'false').strip()


def _run_one_piston(wrapped_code: str, language: str) -> str | None:
    """Execute wrapped_code via Piston; return stripped stdout or None on error."""
    runtime, version = _LANG_RUNTIME.get(language, (language, '*'))
    payload = _json.dumps({
        'language': runtime, 'version': version,
        'files': [{'name': 'main', 'content': wrapped_code}],
    }).encode()
    req = urllib.request.Request(
        _PISTON_URL, data=payload,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        result = _json.loads(resp.read().decode())
    run = result.get('run', {})
    return run.get('stdout', '').strip() if run.get('code') == 0 else None


def _evaluate_server_side(code: str, language: str, test_cases: list, starter_map: dict):
    """
    Run code against ALL stored test cases (visible + hidden) using Piston.
    Hidden cases are stripped from API responses to the frontend but must be
    included in scoring so candidates cannot hard-code visible examples.
    Returns (tests_passed, total_cases).
    Falls back to (0, total_cases) if the language/problem isn't supported.
    """
    all_cases = test_cases  # score against every case, including is_hidden ones
    if not all_cases:
        return 0, 0

    func_name = _extract_func_name(starter_map.get(language, ''), language)
    if not func_name:
        logger.info(f"[CODE EVAL] Cannot extract function name for {language!r}; defaulting to 0 score")
        return 0, len(all_cases)

    def _eval_one(tc):
        wrapper = _build_wrapper(code, language, tc.get('input', ''), func_name)
        if not wrapper:
            return False
        try:
            stdout = _run_one_piston(wrapper, language)
            if stdout is None:
                return False
            expected = str(tc.get('expected', '')).strip()
            return _normalise_output(stdout) == _normalise_output(expected) or stdout == expected
        except Exception as e:
            logger.debug(f"[CODE EVAL] test case error: {e}")
            return False

    passed = 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_eval_one, tc): tc for tc in all_cases}
        for fut in as_completed(futures, timeout=40):
            try:
                if fut.result():
                    passed += 1
            except Exception:
                pass

    logger.info(f"[CODE EVAL] Server-side result: {passed}/{len(all_cases)}")
    return passed, len(all_cases)


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
