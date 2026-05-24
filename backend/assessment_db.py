"""
Assessment database helpers — assessments, responses, scoring, scheduling, and token access.
"""

import json
import secrets
from datetime import datetime, timedelta

from db_config import get_connection
from user_db import DatabaseError


# ============================================================================
#                            ASSESSMENT CORE
# ============================================================================

def create_assessment(candidate_id, job_id=None, scheduled_assessment_id=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO assessments (candidate_id, job_id, scheduled_assessment_id, status, started_at)
            VALUES (%s, %s, %s, 'in_progress', CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (candidate_id, job_id, scheduled_assessment_id)
        )
        assessment_id = cursor.fetchone()[0]

        conn.commit()
        conn.close()

        return assessment_id

    except Exception as e:
        raise DatabaseError(f"Error creating assessment: {str(e)}") from e


def update_assessment_scores(assessment_id, technical_score, psychometric_score, decision, rationale, scheduled_assessment_id=None, hiring_recommendation=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        overall_score = (technical_score * 0.6) + (psychometric_score * 0.4)

        cursor.execute("""
            UPDATE assessments
            SET technical_score = CAST(%s AS NUMERIC), psychometric_score = CAST(%s AS NUMERIC),
                overall_score = CAST(%s AS NUMERIC),
                decision = %s, rationale = %s, status = 'completed',
                completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (technical_score, psychometric_score, overall_score, decision, rationale, assessment_id))

        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()

        if rows_affected == 0:
            raise DatabaseError(f"No assessment found with id {assessment_id}")

    except Exception as e:
        raise DatabaseError(f"Error updating assessment scores: {str(e)}") from e


def get_assessment_by_id(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, candidate_id, job_id, technical_score, psychometric_score,
                   overall_score, decision, rationale, proctoring_violations, status,
                   started_at, completed_at, scheduled_assessment_id
            FROM assessments WHERE id = %s
        """, (assessment_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'id': row[0],
            'candidate_id': row[1],
            'job_id': row[2],
            'technical_score': row[3],
            'psychometric_score': row[4],
            'overall_score': row[5],
            'decision': row[6],
            'rationale': row[7],
            'proctoring_violations': row[8],
            'status': row[9],
            'started_at': row[10],
            'completed_at': row[11],
            'scheduled_assessment_id': row[12],
        }

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment: {str(e)}") from e


def get_assessment_by_candidate_id(candidate_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.id, a.candidate_id, a.job_id, a.technical_score, a.psychometric_score,
                   a.overall_score, a.decision, a.rationale, a.proctoring_violations, a.status,
                   a.started_at, a.completed_at,
                   COALESCE(m.score, 0) as mcq_score,
                   COALESCE(c.score, 0) as coding_score
            FROM assessments a
            LEFT JOIN (
                SELECT assessment_id, ROUND(COUNT(CASE WHEN is_correct = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as score
                FROM mcq_responses GROUP BY assessment_id
            ) m ON a.id = m.assessment_id
            LEFT JOIN (
                SELECT assessment_id, ROUND(SUM(test_cases_passed) * 100.0 / NULLIF(SUM(total_test_cases), 0), 2) as score
                FROM coding_submissions GROUP BY assessment_id
            ) c ON a.id = c.assessment_id
            WHERE a.candidate_id = %s
            ORDER BY a.created_at DESC
            LIMIT 1
        """, (candidate_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            'id': row[0],
            'candidate_id': row[1],
            'job_id': row[2],
            'technical_score': row[3] if row[3] is not None else 0,
            'psychometric_score': row[4] if row[4] is not None else 0,
            'overall_score': row[5] if row[5] is not None else 0,
            'decision': row[6],
            'rationale': row[7],
            'proctoring_violations': row[8],
            'status': row[9],
            'started_at': row[10],
            'completed_at': row[11],
            'mcq_score': row[12],
            'coding_score': row[13]
        }

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment for candidate {candidate_id}: {str(e)}") from e


# ============================================================================
#                           RESPONSE TRACKING — MCQ
# ============================================================================

def save_mcq_response(assessment_id, question_id, selected_answer, is_correct, time_spent):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE mcq_responses
            SET selected_answer = %s, is_correct = %s, time_spent = %s
            WHERE assessment_id = %s AND question_id = %s
            """,
            (selected_answer, is_correct, time_spent, assessment_id, question_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO mcq_responses
                (assessment_id, question_id, selected_answer, is_correct, time_spent)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (assessment_id, question_id, selected_answer, is_correct, time_spent)
            )

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error saving MCQ response: {str(e)}") from e


def get_saved_mcq_answers(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT ON (question_id) question_id, selected_answer
            FROM mcq_responses
            WHERE assessment_id = %s
            ORDER BY question_id, id DESC
            """,
            (assessment_id,)
        )

        rows = cursor.fetchall()
        conn.close()

        return {row[0]: row[1] for row in rows}

    except Exception as e:
        raise DatabaseError(f"Error getting saved MCQ answers: {str(e)}") from e


# ============================================================================
#                       RESPONSE TRACKING — PSYCHOMETRIC
# ============================================================================

def save_psychometric_response(assessment_id, question_id, trait, score, scenario_response=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE psychometric_responses
            SET trait = %s, score = %s, scenario_response = %s
            WHERE assessment_id = %s AND question_id = %s
            """,
            (trait, score, scenario_response, assessment_id, question_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO psychometric_responses
                (assessment_id, question_id, trait, score, scenario_response)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (assessment_id, question_id, trait, score, scenario_response)
            )

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error saving psychometric response: {str(e)}") from e


def get_saved_psychometric_answers(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT ON (question_id) question_id, score, scenario_response
            FROM psychometric_responses
            WHERE assessment_id = %s
            ORDER BY question_id, id DESC
            """,
            (assessment_id,)
        )

        rows = cursor.fetchall()
        conn.close()

        result = {}
        for row in rows:
            q_id = row[0]
            scenario_response = row[2]
            if scenario_response is not None and scenario_response.isdigit():
                result[q_id] = int(scenario_response)
            else:
                result[q_id] = max(0, int(row[1]) - 1) if row[1] else 0
        return result

    except Exception as e:
        raise DatabaseError(f"Error getting saved psychometric answers: {str(e)}") from e


# ============================================================================
#                        RESPONSE TRACKING — CODING
# ============================================================================

def save_coding_submission(assessment_id, problem_id, language, code, test_cases_passed, total_test_cases):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE coding_submissions
            SET language = %s, code = %s, test_cases_passed = %s, total_test_cases = %s, submitted_at = CURRENT_TIMESTAMP
            WHERE assessment_id = %s AND problem_id = %s
            """,
            (language, code, test_cases_passed, total_test_cases, assessment_id, problem_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO coding_submissions
                (assessment_id, problem_id, language, code, test_cases_passed, total_test_cases)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (assessment_id, problem_id, language, code, test_cases_passed, total_test_cases)
            )

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error saving coding submission: {str(e)}") from e


def get_saved_coding_submission(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT problem_id, language, code, test_cases_passed, total_test_cases
            FROM coding_submissions
            WHERE assessment_id = %s
            ORDER BY submitted_at DESC
            LIMIT 1
            """,
            (assessment_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'problem_id': row[0],
                'language': row[1],
                'code': row[2],
                'test_cases_passed': row[3],
                'total_test_cases': row[4]
            }
        return None

    except Exception as e:
        raise DatabaseError(f"Error getting saved coding submission: {str(e)}") from e


# ============================================================================
#                          SCORE CALCULATION
# ============================================================================

def get_mcq_score(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) as correct
            FROM mcq_responses WHERE assessment_id = %s
        """, (assessment_id,))

        result = cursor.fetchone()
        conn.close()

        total = result[0]
        correct = result[1] or 0

        return 0.0 if total == 0 else round((correct / total) * 100, 2)

    except Exception as e:
        raise DatabaseError(f"Error calculating MCQ score: {str(e)}") from e


def get_coding_score(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(test_cases_passed) as total_passed, SUM(total_test_cases) as total_tests
            FROM coding_submissions WHERE assessment_id = %s
        """, (assessment_id,))

        result = cursor.fetchone()
        conn.close()

        total_passed = result[0] or 0
        total_tests = result[1] or 0

        return 0.0 if total_tests == 0 else round((total_passed / total_tests) * 100, 2)

    except Exception as e:
        raise DatabaseError(f"Error calculating coding score: {str(e)}") from e


def get_psychometric_scores(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trait, AVG(score) as avg_score
            FROM psychometric_responses WHERE assessment_id = %s
            GROUP BY trait
        """, (assessment_id,))

        rows = cursor.fetchall()
        conn.close()

        return {row[0]: round(row[1], 2) for row in rows}

    except Exception as e:
        raise DatabaseError(f"Error calculating psychometric scores: {str(e)}") from e


# ============================================================================
#                         ASSESSMENT SCHEDULING
# ============================================================================

def create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time, is_technical_role=True, questions_data=None):
    print(f"[DB] create_scheduled_assessment called: candidate={candidate_id}, interviewer={interviewer_id}, time={scheduled_time}, technical={is_technical_role}", flush=True)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("[DB] Executing INSERT with PostgreSQL...", flush=True)

        cursor.execute(
            """INSERT INTO scheduled_assessments (candidate_id, interviewer_id, scheduled_time, status, is_technical_role, questions_data)
               VALUES (%s, %s, %s, 'scheduled', %s, %s) RETURNING id""",
            (candidate_id, interviewer_id, scheduled_time, is_technical_role, json.dumps(questions_data) if questions_data else None)
        )

        result = cursor.fetchone()
        scheduled_id = result[0] if result else None
        print(f"[DB] INSERT done, scheduled_id={scheduled_id}", flush=True)

        conn.commit()
        conn.close()

        print(f"[DB] Returning scheduled_id={scheduled_id}", flush=True)
        return scheduled_id

    except Exception as e:
        print(f"[DB] ERROR in create_scheduled_assessment: {e}", flush=True)
        raise DatabaseError(f"Error creating scheduled assessment: {str(e)}")


def get_scheduled_assessment_by_id(scheduled_assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, candidate_id, interviewer_id, scheduled_time, status, assessment_id,
                      is_technical_role, questions_data, created_at, updated_at
               FROM scheduled_assessments WHERE id = %s""",
            (scheduled_assessment_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        scheduled_time_raw = row[3]
        scheduled_time = (
            scheduled_time_raw.replace(' ', 'T') if isinstance(scheduled_time_raw, str)
            else (scheduled_time_raw.strftime('%Y-%m-%dT%H:%M:%S') if scheduled_time_raw else None)
        )
        questions_data = row[7]
        if isinstance(questions_data, str):
            try:
                questions_data = json.loads(questions_data)
            except Exception:
                questions_data = None
        return {
            'id': row[0], 'candidate_id': row[1], 'interviewer_id': row[2],
            'scheduled_time': scheduled_time, 'status': row[4], 'assessment_id': row[5],
            'is_technical_role': row[6] if row[6] is not None else True,
            'questions_data': questions_data, 'created_at': row[8], 'updated_at': row[9]
        }
    except Exception as e:
        raise DatabaseError(f"Error retrieving scheduled assessment by id: {str(e)}") from e


def get_scheduled_assessment(candidate_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, candidate_id, interviewer_id, scheduled_time, status, assessment_id,
                      is_technical_role, questions_data, created_at, updated_at
               FROM scheduled_assessments WHERE candidate_id = %s""",
            (candidate_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            scheduled_time_raw = row[3]
            if isinstance(scheduled_time_raw, str):
                scheduled_time = scheduled_time_raw.replace(' ', 'T')
            else:
                scheduled_time = scheduled_time_raw.strftime('%Y-%m-%dT%H:%M:%S') if scheduled_time_raw else None

            questions_data = row[7]
            if isinstance(questions_data, str):
                try:
                    questions_data = json.loads(questions_data)
                except Exception:
                    questions_data = None

            return {
                'id': row[0],
                'candidate_id': row[1],
                'interviewer_id': row[2],
                'scheduled_time': scheduled_time,
                'status': row[4],
                'assessment_id': row[5],
                'is_technical_role': row[6] if row[6] is not None else True,
                'questions_data': questions_data,
                'created_at': row[8],
                'updated_at': row[9]
            }
        return None

    except Exception as e:
        raise DatabaseError(f"Error retrieving scheduled assessment: {str(e)}") from e


def update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        if assessment_id:
            cursor.execute("""
                UPDATE scheduled_assessments
                SET status = %s, assessment_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, assessment_id, scheduled_assessment_id))
        else:
            cursor.execute("""
                UPDATE scheduled_assessments
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, scheduled_assessment_id))

        conn.commit()
        conn.close()

        return True

    except Exception as e:
        raise DatabaseError(f"Error updating scheduled assessment: {str(e)}") from e


def check_assessment_time_valid(candidate_id, current_time, window_minutes=30):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT scheduled_time FROM scheduled_assessments
            WHERE candidate_id = %s AND status = 'scheduled'
            ORDER BY created_at DESC LIMIT 1
        """, (candidate_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return (False, None, "No scheduled assessment found")

        scheduled_time_raw = row[0]

        if isinstance(scheduled_time_raw, str):
            scheduled_time = scheduled_time_raw.replace(' ', 'T')
        else:
            scheduled_time = scheduled_time_raw.strftime('%Y-%m-%dT%H:%M:%S')

        scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', ''))
        current_dt = datetime.now()

        time_diff = abs((current_dt - scheduled_dt).total_seconds() / 60)

        if time_diff <= window_minutes:
            return (True, scheduled_time, f"Assessment is within {window_minutes} minute window")
        else:
            return (False, scheduled_time, f"Assessment is {int(time_diff)} minutes away from scheduled time")

    except Exception as e:
        raise DatabaseError(f"Error checking assessment time: {str(e)}") from e


# ============================================================================
#                       TOKEN-BASED ASSESSMENT ACCESS
# ============================================================================

def generate_assessment_token():
    return secrets.token_urlsafe(32)


def set_assessment_token(scheduled_assessment_id, token):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE scheduled_assessments
               SET access_token = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (token, scheduled_assessment_id)
        )

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    except Exception as e:
        raise DatabaseError(f"Error setting assessment token: {str(e)}") from e


def get_assessment_by_token(token):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT sa.id, sa.candidate_id, sa.interviewer_id, sa.scheduled_time,
                      sa.status, sa.assessment_id, sa.started_at,
                      c.name as candidate_name, c.email as candidate_email
               FROM scheduled_assessments sa
               JOIN candidates c ON sa.candidate_id = c.id
               WHERE sa.access_token = %s""",
            (token,)
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'candidate_id': row[1],
                'interviewer_id': row[2],
                'scheduled_time': row[3],
                'status': row[4],
                'assessment_id': row[5],
                'started_at': row[6],
                'proctoring_enabled': True,
                'candidate_name': row[7],
                'candidate_email': row[8]
            }
        return None

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment by token: {str(e)}") from e


def start_assessment_by_token(token):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE scheduled_assessments
               SET status = 'in_progress', started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
               WHERE access_token = %s AND status = 'scheduled'""",
            (token,)
        )

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    except Exception as e:
        raise DatabaseError(f"Error starting assessment: {str(e)}") from e


def verify_assessment_access_token(token: str, assessment_id: int) -> bool:
    """Return True if token is valid for the given assessment_id."""
    if not token:
        return False
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT 1 FROM scheduled_assessments
               WHERE access_token = %s AND assessment_id = %s
               AND status NOT IN ('cancelled')""",
            (token, assessment_id)
        )
        result = cursor.fetchone()
        conn.close()
        return bool(result)
    except Exception:
        return False


# ============================================================================
#                        ASSESSMENT QUESTIONS & TIME
# ============================================================================

def save_assessment_questions(assessment_id, questions_data):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE assessments
               SET questions_data = %s
               WHERE id = %s""",
            (json.dumps(questions_data), assessment_id)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error saving assessment questions: {str(e)}") from e


def get_assessment_questions(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT questions_data FROM assessments WHERE id = %s""",
            (assessment_id,)
        )

        row = cursor.fetchone()
        conn.close()

        return row[0] if row and row[0] else None

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment questions: {str(e)}") from e


def update_assessment_time_elapsed(assessment_id, time_elapsed_seconds):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE assessments
               SET time_elapsed_seconds = %s
               WHERE id = %s""",
            (time_elapsed_seconds, assessment_id)
        )

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error updating assessment time: {str(e)}") from e


def get_assessment_time_elapsed(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER as elapsed_seconds,
                started_at
            FROM assessments
            WHERE id = %s AND started_at IS NOT NULL
            """,
            (assessment_id,)
        )

        row = cursor.fetchone()
        conn.close()

        return max(0, row[0]) if row and row[0] is not None else 0

    except Exception as e:
        raise DatabaseError(f"Error getting assessment time: {str(e)}") from e
