"""
Interviewee answer routes — submitting responses and completing assessments.
"""

import logging
import json as _json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError, as_completed
from flask import Blueprint, request, jsonify

from assessment_db import (
    ASSESSMENT_DURATION_SECONDS,
    AssessmentStateError,
    finalize_assessment,
    get_assessment_by_id,
    get_assessment_questions,
    save_mcq_response,
    save_coding_submission,
    save_psychometric_response,
    verify_assessment_access_token,
    get_assessment_by_token,
)
from code_runner_config import code_runner_enabled, code_runner_endpoint
from questions_bank import get_starter_function_name, normalize_starter_code


def _check_assessment_token(
    assessment_id: int,
    *,
    allow_expired: bool = False,
    allow_completed: bool = False,
):
    """Return a 403 response if the X-Assessment-Token header is missing or invalid, else None."""
    token = request.headers.get('X-Assessment-Token', '')
    if not verify_assessment_access_token(
        token,
        assessment_id,
        allow_expired=allow_expired,
        allow_completed=allow_completed,
    ):
        return jsonify({'status': 'error', 'message': 'Invalid or missing assessment token'}), 403
    return None

logger = logging.getLogger(__name__)

interviewee_answers_bp = Blueprint('interviewee_answers', __name__)


class CodeEvaluationUnavailable(RuntimeError):
    """Raised when a coding answer cannot be scored reliably."""


def _positive_integer(value, field_name):
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return parsed


def _non_negative_integer(value, field_name):
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return parsed


def _find_question(question_id, questions):
    for question in questions or []:
        try:
            stored_id = int(question.get('id'))
        except (AttributeError, TypeError, ValueError):
            continue
        if stored_id == question_id:
            return question
    return None


def _psychometric_option_score(selected_option, optimal_choice):
    """Score categorical options without inventing meaning from their order."""
    try:
        optimal_index = int(optimal_choice)
    except (TypeError, ValueError) as exc:
        raise ValueError("Psychometric scoring data is invalid") from exc
    return 10 if selected_option == optimal_index else 0


@interviewee_answers_bp.route('/assessment/<int:assessment_id>/submit-answer', methods=['POST'])
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

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'status': 'error', 'message': 'A JSON request body is required'}), 400
        answer_type = data.get('type')

        if answer_type == 'mcq':
            question_id = _positive_integer(data.get('questionId'), 'questionId')
            selected = str(data.get('answer', '')).strip().upper()
            if selected not in ('A', 'B', 'C', 'D'):
                return jsonify({
                    'status': 'error',
                    'message': 'answer must be one of A, B, C, or D'
                }), 400
            time_spent = _non_negative_integer(data.get('timeSpent', 0), 'timeSpent')

            stored_questions = get_assessment_questions(assessment_id)
            questions = stored_questions.get('mcq_questions', []) if stored_questions else []
            if not questions:
                return jsonify({
                    'status': 'error',
                    'message': 'Assessment questions are unavailable; please reload the assessment'
                }), 409

            correct_answer = _resolve_correct_answer(question_id, questions)
            if correct_answer is None:
                return jsonify({'status': 'error', 'message': 'Unknown MCQ question'}), 400
            is_correct = selected == correct_answer

            save_mcq_response(
                assessment_id=assessment_id, question_id=question_id,
                selected_answer=selected, is_correct=is_correct, time_spent=time_spent
            )
            return jsonify({'status': 'success', 'message': 'MCQ answer saved'}), 200

        elif answer_type == 'coding':
            if not code_runner_enabled():
                return jsonify({
                    'status': 'error',
                    'message': 'Coding assessments are temporarily unavailable.',
                }), 503
            submitted_code = data.get('code', '')
            language = str(data.get('language', 'python')).strip().lower()
            if language not in _LANG_RUNTIME:
                return jsonify({'status': 'error', 'message': 'Unsupported coding language'}), 400
            if not isinstance(submitted_code, str) or not submitted_code.strip():
                return jsonify({'status': 'error', 'message': 'code is required'}), 400
            if len(submitted_code) > 100_000:
                return jsonify({'status': 'error', 'message': 'code exceeds 100,000 characters'}), 413

            # Look up stored problem to get server-authoritative test cases and
            # starter code (needed to extract the function name for the harness).
            stored_q = get_assessment_questions(assessment_id)
            coding_problem = stored_q.get('coding_problem') if stored_q else None
            if not coding_problem:
                return jsonify({'status': 'error', 'message': 'No coding problem is assigned'}), 400
            problem_id = _positive_integer(data.get('questionId'), 'questionId')
            expected_problem_id = _positive_integer(coding_problem.get('id'), 'coding problem id')
            if problem_id != expected_problem_id:
                return jsonify({'status': 'error', 'message': 'Unknown coding problem'}), 400
            test_cases = coding_problem.get('test_cases', []) if coding_problem else []
            starter_map = normalize_starter_code(coding_problem.get('starter_code'))
            if language not in starter_map:
                return jsonify({
                    'status': 'error',
                    'message': 'Language is not available for this coding problem',
                }), 400
            if not isinstance(test_cases, list) or not test_cases:
                return jsonify({
                    'status': 'error',
                    'message': 'Coding test cases are unavailable; please contact support',
                }), 409

            try:
                tests_passed, total_tests = _evaluate_server_side(
                    submitted_code, language, test_cases, starter_map
                )
            except Exception as eval_err:
                logger.warning(
                    "[CODE EVAL] Submission was not scored (%s)",
                    type(eval_err).__name__,
                )
                return jsonify({
                    'status': 'error',
                    'message': (
                        'Coding evaluation is temporarily unavailable. '
                        'Your solution was not saved; please retry.'
                    ),
                }), 503

            save_coding_submission(
                assessment_id=assessment_id,
                problem_id=problem_id,
                language=language,
                code=submitted_code,
                test_cases_passed=tests_passed,
                total_test_cases=total_tests
            )
            return jsonify({'status': 'success', 'message': 'Coding solution saved'}), 200

        elif answer_type == 'psychometric':
            selected_option = _non_negative_integer(
                data.get('selectedOption'), 'selectedOption'
            )
            question_id = _positive_integer(data.get('questionId'), 'questionId')
            scenario_response = str(selected_option)

            # Calculate score server-side from stored scenarios (never trust client score)
            trait = None
            score = None
            stored_q = get_assessment_questions(assessment_id)
            scenarios = stored_q.get('psychometric_scenarios', []) if stored_q else []
            scenario = _find_question(question_id, scenarios)
            if not scenario:
                return jsonify({'status': 'error', 'message': 'Unknown psychometric question'}), 400
            options = scenario.get('options') or []
            if selected_option >= len(options):
                return jsonify({'status': 'error', 'message': 'selectedOption is out of range'}), 400
            trait = str(scenario.get('trait') or 'general').strip()
            optimal = scenario.get('optimal_choice')
            if optimal is None:
                return jsonify({
                    'status': 'error',
                    'message': 'Psychometric scoring data is unavailable'
                }), 409
            score = _psychometric_option_score(selected_option, optimal)

            save_psychometric_response(
                assessment_id=assessment_id,
                question_id=question_id,
                trait=trait,
                score=score,
                scenario_response=scenario_response
            )
            return jsonify({'status': 'success', 'message': 'Psychometric response saved'}), 200

        return jsonify({'status': 'error', 'message': 'Invalid answer type'}), 400

    except AssessmentStateError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 409
    except (TypeError, ValueError) as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception:
        logger.exception("Failed to save answer for assessment %s", assessment_id)
        return jsonify({'status': 'error', 'message': 'Failed to save answer'}), 500


@interviewee_answers_bp.route('/assessment/<int:assessment_id>/complete', methods=['POST'])
def complete_assessment(assessment_id):
    try:
        err = _check_assessment_token(
            assessment_id,
            allow_expired=True,
            allow_completed=True,
        )
        if err:
            return err

        result = finalize_assessment(assessment_id)
        logger.info(
            "Assessment %s completed with overall score %.2f",
            assessment_id,
            result['scores']['overall'],
        )

        return jsonify({
            'status': 'success',
            'message': 'Assessment completed successfully',
            'data': {
                'assessment_id': result['assessment_id'],
                'status': 'completed',
            },
        }), 200

    except AssessmentStateError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 409
    except Exception as e:
        logger.error(f"Assessment {assessment_id}: FAILED to complete — {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to complete assessment'}), 500


@interviewee_answers_bp.route('/run-code', methods=['POST'])
def run_code():
    """
    Run one visible example from the candidate's assigned coding problem.

    The server supplies the test input and wrapper. This prevents the endpoint
    from becoming an unrelated general-purpose execution proxy and ensures a
    hidden test can never be selected by index.
    """
    token = request.headers.get('X-Assessment-Token', '')
    if not token:
        return jsonify({'status': 'error', 'message': 'Assessment token required'}), 403
    assessment_record = get_assessment_by_token(token)
    if not assessment_record or assessment_record.get('status') not in ('in_progress',):
        return jsonify({'status': 'error', 'message': 'Invalid or inactive assessment token'}), 403
    if assessment_record.get('deadline_reached'):
        return jsonify({
            'status': 'error',
            'message': (
                'Assessment time limit has expired after '
                f'{ASSESSMENT_DURATION_SECONDS // 60} minutes'
            ),
        }), 409
    if not code_runner_enabled():
        return jsonify({
            'status': 'error',
            'message': 'Coding assessments are temporarily unavailable.',
        }), 503

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'status': 'error', 'message': 'A JSON object is required'}), 400
    language = data.get('language')
    code = data.get('code', '')

    if not isinstance(language, str) or language not in _LANG_RUNTIME:
        return jsonify({'status': 'error', 'message': 'Unsupported language'}), 400
    if not isinstance(code, str) or not code.strip():
        return jsonify({'status': 'error', 'message': 'language and code are required'}), 400
    if len(code) > 100_000:
        return jsonify({'status': 'error', 'message': 'Code exceeds the 100 KB limit'}), 400

    try:
        problem_id = _positive_integer(data.get('problem_id'), 'problem_id')
        test_case_index = _non_negative_integer(
            data.get('test_case_index'), 'test_case_index'
        )
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400

    assessment_id = assessment_record.get('assessment_id')
    stored_questions = get_assessment_questions(assessment_id) if assessment_id else None
    coding_problem = stored_questions.get('coding_problem') if stored_questions else None
    if not coding_problem:
        return jsonify({'status': 'error', 'message': 'No coding problem is assigned'}), 400
    try:
        assigned_problem_id = _positive_integer(
            coding_problem.get('id'), 'assigned coding problem id'
        )
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Assigned coding problem is invalid'}), 409
    if problem_id != assigned_problem_id:
        return jsonify({'status': 'error', 'message': 'Unknown coding problem'}), 400

    visible_cases = [
        test_case for test_case in coding_problem.get('test_cases', [])
        if isinstance(test_case, dict) and not test_case.get('is_hidden', False)
    ]
    if test_case_index >= len(visible_cases):
        return jsonify({'status': 'error', 'message': 'Unknown visible test case'}), 400
    test_case = visible_cases[test_case_index]
    starter_map = normalize_starter_code(coding_problem.get('starter_code'))
    func_name = get_starter_function_name(starter_map.get(language, ''), language)
    if not func_name:
        return jsonify({
            'status': 'error',
            'message': 'This problem cannot be previewed in the selected language',
        }), 400
    wrapped_code = _build_wrapper(
        code,
        language,
        str(test_case.get('input', '')),
        func_name,
    )
    if not wrapped_code or len(wrapped_code) > 120_000:
        return jsonify({'status': 'error', 'message': 'Unable to prepare code preview'}), 400

    runtime, version = _LANG_RUNTIME[language]
    filename = f'main.{_LANG_FILE_EXTENSIONS[language]}'

    try:
        payload = _json.dumps({
            'language': runtime,
            'version': version,
            'files': [{'name': filename, 'content': wrapped_code}],
            'compile_timeout': 10_000,
            'run_timeout': 3_000,
            'compile_cpu_time': 10_000,
            'run_cpu_time': 3_000,
            'compile_memory_limit': 256 * 1024 * 1024,
            'run_memory_limit': 256 * 1024 * 1024,
        }).encode('utf-8')

        req = urllib.request.Request(
            _PISTON_URL,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            response_body = resp.read(1_000_001)
        if len(response_body) > 1_000_000:
            raise ValueError('Code execution response exceeded the size limit')
        result = _json.loads(response_body.decode('utf-8'))
        if not isinstance(result, dict):
            raise ValueError('Code execution service returned an invalid response')

        run = result.get('run')
        if not isinstance(run, dict):
            raise ValueError('Code execution service omitted its run result')
        stdout = str(run.get('stdout') or '').strip()
        stderr = str(run.get('stderr') or '').strip()
        exit_code = run.get('code')
        expected = str(test_case.get('expected', '')).strip()
        passed = (
            exit_code == 0
            and _normalise_output(stdout) == _normalise_output(expected)
        )
        logger.info("[CODE EXEC] assessment=%s lang=%s exit=%s", assessment_id, language, exit_code)
        return jsonify({
            'status': 'success',
            'data': {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code,
                'expected': expected,
                'passed': passed,
            },
        }), 200
    except Exception:
        logger.warning("[CODE EXEC] Piston request failed", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Code execution service unavailable'}), 503


# ============================================================================
#                     SERVER-SIDE CODE EVALUATION
# ============================================================================

_PISTON_URL = code_runner_endpoint()

_LANG_RUNTIME = {
    'python': ('python', '*'),
    'javascript': ('javascript', '*'),
}

_LANG_FILE_EXTENSIONS = {
    'python': 'py',
    'javascript': 'js',
}


def _build_wrapper(code: str, language: str, tc_input: str, func_name: str):
    """Append a harness call that invokes func_name with tc_input and prints the result."""
    if language == 'python':
        return f"{code}\n\n# __test__\nprint({func_name}({tc_input}))"
    if language == 'javascript':
        return f"{code}\n\n// __test__\nconsole.log(JSON.stringify({func_name}({tc_input})));"
    return None


def _normalise_output(s: str) -> str:
    return s.replace("'", '"').replace('True', 'true').replace('False', 'false').strip()


def _run_one_piston(wrapped_code: str, language: str) -> str | None:
    """Execute code via Piston, distinguishing outages from candidate failures."""
    if not isinstance(wrapped_code, str) or len(wrapped_code) > 120_000:
        return None
    runtime, version = _LANG_RUNTIME.get(language, (language, '*'))
    payload = _json.dumps({
        'language': runtime, 'version': version,
        'files': [{'name': 'main', 'content': wrapped_code}],
        'compile_timeout': 10_000,
        'run_timeout': 3_000,
        'compile_cpu_time': 10_000,
        'run_cpu_time': 3_000,
        'compile_memory_limit': 256 * 1024 * 1024,
        'run_memory_limit': 256 * 1024 * 1024,
    }).encode()
    req = urllib.request.Request(
        _PISTON_URL, data=payload,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            response_body = resp.read(1_000_001)
        result = _json.loads(response_body.decode())
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        raise CodeEvaluationUnavailable(
            'Coding evaluation service is unavailable'
        ) from exc
    if len(response_body) > 1_000_000:
        return None
    if not isinstance(result, dict):
        raise CodeEvaluationUnavailable('Coding evaluation service is unavailable')
    run = result.get('run')
    if not isinstance(run, dict) or not isinstance(run.get('code'), int):
        raise CodeEvaluationUnavailable('Coding evaluation service is unavailable')
    if run['code'] != 0:
        return None
    stdout = run.get('stdout')
    if not isinstance(stdout, str):
        raise CodeEvaluationUnavailable('Coding evaluation service is unavailable')
    return stdout.strip()


def _evaluate_server_side(code: str, language: str, test_cases: list, starter_map: dict):
    """
    Run code against ALL stored test cases (visible + hidden) using Piston.
    Hidden cases are stripped from API responses to the frontend but must be
    included in scoring so candidates cannot hard-code visible examples.
    Returns (tests_passed, total_cases).
    Raises when evaluation infrastructure cannot produce a trustworthy score.
    """
    all_cases = test_cases[:10] if isinstance(test_cases, list) else []
    if not all_cases:
        return 0, 0

    normalized_starters = normalize_starter_code(starter_map)
    func_name = get_starter_function_name(normalized_starters.get(language, ''), language)
    if not func_name:
        raise CodeEvaluationUnavailable(
            f'Coding evaluation configuration is unavailable for {language!r}'
        )

    def _eval_one(tc):
        wrapper = _build_wrapper(code, language, tc.get('input', ''), func_name)
        if not wrapper:
            return False
        stdout = _run_one_piston(wrapper, language)
        if stdout is None:
            return False
        expected = str(tc.get('expected', '')).strip()
        return _normalise_output(stdout) == _normalise_output(expected) or stdout == expected

    passed = 0
    futures = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_eval_one, tc): tc for tc in all_cases}
        try:
            for fut in as_completed(futures, timeout=30):
                if fut.result():
                    passed += 1
        except FuturesTimeoutError as exc:
            logger.warning("[CODE EVAL] Timed out before every test case completed")
            for future in futures:
                future.cancel()
            raise CodeEvaluationUnavailable(
                'Coding evaluation service timed out'
            ) from exc
        except Exception:
            for future in futures:
                future.cancel()
            raise

    logger.info(f"[CODE EVAL] Server-side result: {passed}/{len(all_cases)}")
    return passed, len(all_cases)


def _resolve_correct_answer(question_id_int, questions):
    """Try 5 matching strategies to find the correct answer letter (A/B/C/D)."""
    question = _find_question(question_id_int, questions)
    if not question:
        return None
    correct = question.get('correct_answer')
    if not isinstance(correct, str) or not correct.strip():
        return None
    correct_upper = correct.strip().upper()
    if correct_upper in ('A', 'B', 'C', 'D'):
        return correct_upper
    if correct.strip() in ('0', '1', '2', '3'):
        return ('A', 'B', 'C', 'D')[int(correct.strip())]

    correct_lower = correct.strip().lower()
    letters = ('A', 'B', 'C', 'D')
    options = question.get('options') or []
    for idx, option in enumerate(options[:4]):
        if str(option).strip().lower() == correct_lower:
            return letters[idx]
    for idx, option in enumerate(options[:4]):
        option_lower = str(option).strip().lower()
        if correct_lower in option_lower or option_lower in correct_lower:
            return letters[idx]
    for idx, option in enumerate(options[:4]):
        option_lower = str(option).strip().lower()
        if (
            option_lower.startswith(correct_lower[:20])
            or correct_lower.startswith(option_lower[:20])
        ):
            return letters[idx]
    return None
