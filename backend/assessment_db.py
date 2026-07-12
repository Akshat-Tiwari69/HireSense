"""
Assessment database helpers — assessments, responses, scoring, scheduling, and token access.
"""

import json
import secrets

from db_config import db_connection
from user_db import DatabaseError


ACTIVE_ASSESSMENT_STATUSES = ('started', 'in_progress')
ASSESSMENT_DURATION_SECONDS = 60 * 60
TECHNICAL_SCORE_WEIGHT = 0.7
PSYCHOMETRIC_SCORE_WEIGHT = 0.3


class AssessmentStateError(DatabaseError):
    """Raised when an assessment operation is invalid for its current state."""


def _normalise_score(value, field_name):
    """Return a finite score in the inclusive 0-100 range."""
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if not 0 <= score <= 100:
        raise ValueError(f"{field_name} must be between 0 and 100")
    return score


def _lock_active_assessment(cursor, assessment_id):
    """Serialize response writes and reject inactive or expired assessments."""
    cursor.execute(
        """
        SELECT status,
               GREATEST(
                   COALESCE(time_elapsed_seconds, 0),
                   CASE
                       WHEN started_at IS NULL THEN 0
                       ELSE EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER
                   END
               ) >= %s AS deadline_reached
        FROM assessments
        WHERE id = %s
        FOR UPDATE
        """,
        (ASSESSMENT_DURATION_SECONDS, assessment_id),
    )
    row = cursor.fetchone()
    if not row:
        raise AssessmentStateError(f"Assessment {assessment_id} does not exist")
    if row[0] not in ACTIVE_ASSESSMENT_STATUSES:
        raise AssessmentStateError(f"Assessment {assessment_id} is not active")
    if row[1]:
        raise AssessmentStateError(
            f"Assessment {assessment_id} has reached its time limit"
        )


def _recommendation_for_score(overall_score):
    if overall_score >= 70:
        return (
            "Recommend for Hire",
            "Strong technical and soft skills demonstrated.",
            "Proceed to HR discussion",
        )
    if overall_score >= 50:
        return (
            "Consider for Interview",
            "Moderate technical performance with decent soft skills.",
            "Conduct follow-up technical interview",
        )
    return (
        "Not Recommended",
        "Performance below acceptable threshold.",
        "Archive application",
    )


def _fetch_one(query, params=()):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()


def _fetch_all(query, params=()):
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


# ============================================================================
#                            ASSESSMENT CORE
# ============================================================================

def update_assessment_scores(
    assessment_id,
    technical_score,
    psychometric_score,
    decision,
    rationale,
    scheduled_assessment_id=None,
    hiring_recommendation=None,
):
    try:
        technical_score = _normalise_score(technical_score, 'technical_score')
        psychometric_score = _normalise_score(psychometric_score, 'psychometric_score')
        overall_score = (
            technical_score * TECHNICAL_SCORE_WEIGHT
            + psychometric_score * PSYCHOMETRIC_SCORE_WEIGHT
        )

        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE assessments
                SET technical_score = CAST(%s AS NUMERIC),
                    psychometric_score = CAST(%s AS NUMERIC),
                    overall_score = CAST(%s AS NUMERIC),
                    decision = %s,
                    rationale = %s,
                    hiring_recommendation = COALESCE(%s, hiring_recommendation),
                    status = 'completed',
                    completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                WHERE id = %s
                  AND status IN ('started', 'in_progress', 'completed')
                RETURNING scheduled_assessment_id
                """,
                (
                    technical_score,
                    psychometric_score,
                    overall_score,
                    decision,
                    rationale,
                    hiring_recommendation,
                    assessment_id,
                ),
            )
            row = cursor.fetchone()
            if not row:
                raise AssessmentStateError(
                    f"Assessment {assessment_id} does not exist or cannot be completed"
                )

            linked_schedule_id = row[0]
            if (
                scheduled_assessment_id is not None
                and linked_schedule_id is not None
                and linked_schedule_id != scheduled_assessment_id
            ):
                raise AssessmentStateError(
                    f"Assessment {assessment_id} is linked to schedule {linked_schedule_id}, "
                    f"not {scheduled_assessment_id}"
                )

            schedule_id = linked_schedule_id or scheduled_assessment_id
            if schedule_id is not None:
                cursor.execute(
                    """
                    UPDATE scheduled_assessments
                    SET status = 'completed', assessment_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND status IN ('scheduled', 'in_progress', 'completed')
                      AND (assessment_id IS NULL OR assessment_id = %s)
                    """,
                    (assessment_id, schedule_id, assessment_id),
                )
                if cursor.rowcount == 0:
                    raise AssessmentStateError(
                        f"Schedule {schedule_id} cannot be linked to assessment {assessment_id}"
                    )

            conn.commit()
            return overall_score

    except Exception as e:
        if isinstance(e, (AssessmentStateError, ValueError)):
            raise
        raise DatabaseError(f"Error updating assessment scores: {str(e)}") from e


def record_final_decision(assessment_id, decision, rationale=None):
    """Atomically persist a human decision and the matching candidate status.

    The assessment and candidate rows are locked together so a retry or a failure
    cannot leave a completed assessment saying "Hire" while the candidate still
    has a non-final status (or the inverse).
    """
    decision_label = "Hire" if decision == "hire" else "No-Hire"
    candidate_status = "hired" if decision == "hire" else "rejected"

    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.candidate_id, a.technical_score, a.psychometric_score,
                       a.rationale, a.status, a.decision,
                       c.name, c.email, c.status
                FROM assessments a
                JOIN candidates c ON c.id = a.candidate_id
                WHERE a.id = %s
                FOR UPDATE OF a, c
                """,
                (assessment_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            if row[4] != "completed":
                raise AssessmentStateError(
                    "The assessment must be completed before a final decision"
                )

            technical_score = _normalise_score(row[1] or 0, "technical_score")
            psychometric_score = _normalise_score(
                row[2] or 0, "psychometric_score"
            )
            overall_score = (
                technical_score * TECHNICAL_SCORE_WEIGHT
                + psychometric_score * PSYCHOMETRIC_SCORE_WEIGHT
            )
            final_rationale = (
                rationale
                or row[3]
                or "Decision made after assessment review"
            )
            should_notify = (
                row[5] != decision_label or row[8] != candidate_status
            )

            cursor.execute(
                """
                UPDATE assessments
                SET overall_score = CAST(%s AS NUMERIC),
                    decision = %s,
                    rationale = %s
                WHERE id = %s AND status = 'completed'
                """,
                (overall_score, decision_label, final_rationale, assessment_id),
            )
            if cursor.rowcount != 1:
                raise AssessmentStateError(
                    f"Assessment {assessment_id} cannot accept a final decision"
                )

            cursor.execute(
                """
                UPDATE candidates
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (candidate_status, row[0]),
            )
            if cursor.rowcount != 1:
                raise AssessmentStateError(
                    f"Candidate {row[0]} could not be updated"
                )

            conn.commit()
            return {
                "assessment_id": assessment_id,
                "candidate_id": row[0],
                "candidate_name": row[6],
                "candidate_email": row[7],
                "decision": decision_label,
                "status": candidate_status,
                "technical_score": technical_score,
                "psychometric_score": psychometric_score,
                "overall_score": overall_score,
                "rationale": final_rationale,
                "should_notify": should_notify,
            }
    except Exception as e:
        if isinstance(e, (AssessmentStateError, ValueError)):
            raise
        raise DatabaseError(f"Error recording final decision: {str(e)}") from e


def get_assessment_by_id(assessment_id):
    try:
        row = _fetch_one("""
            SELECT id, candidate_id, job_id, technical_score, psychometric_score,
                   overall_score, decision, rationale, proctoring_violations, status,
                   started_at, completed_at, scheduled_assessment_id,
                   hiring_recommendation
            FROM assessments WHERE id = %s
        """, (assessment_id,))

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
            'hiring_recommendation': row[13],
        }

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment: {str(e)}") from e


def get_assessment_by_candidate_id(candidate_id):
    try:
        row = _fetch_one("""
            SELECT a.id, a.candidate_id, a.job_id, a.technical_score, a.psychometric_score,
                   a.overall_score, a.decision, a.rationale, a.proctoring_violations, a.status,
                   a.started_at, a.completed_at,
                   COALESCE(m.score, 0) as mcq_score,
                   COALESCE(c.score, 0) as coding_score,
                   a.scheduled_assessment_id, a.hiring_recommendation
            FROM assessments a
            LEFT JOIN (
                SELECT assessment_id,
                       ROUND(
                           COUNT(CASE WHEN is_correct = TRUE THEN 1 END) * 100.0
                           / NULLIF(COUNT(*), 0),
                           2
                       ) AS score
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
            'coding_score': row[13],
            'scheduled_assessment_id': row[14],
            'hiring_recommendation': row[15],
        }

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment for candidate {candidate_id}: {str(e)}") from e


# ============================================================================
#                           RESPONSE TRACKING — MCQ
# ============================================================================

def save_mcq_response(assessment_id, question_id, selected_answer, is_correct, time_spent):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            _lock_active_assessment(cursor, assessment_id)
            cursor.execute(
                """
                INSERT INTO mcq_responses (
                    assessment_id, question_id, selected_answer, is_correct, time_spent
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (assessment_id, question_id) DO UPDATE
                SET selected_answer = EXCLUDED.selected_answer,
                    is_correct = EXCLUDED.is_correct,
                    time_spent = EXCLUDED.time_spent
                """,
                (assessment_id, question_id, selected_answer, is_correct, time_spent),
            )
            conn.commit()

    except Exception as e:
        if isinstance(e, AssessmentStateError):
            raise
        raise DatabaseError(f"Error saving MCQ response: {str(e)}") from e


def get_saved_mcq_answers(assessment_id):
    try:
        rows = _fetch_all(
            """
            SELECT DISTINCT ON (question_id) question_id, selected_answer
            FROM mcq_responses
            WHERE assessment_id = %s
            ORDER BY question_id, id DESC
            """,
            (assessment_id,)
        )

        return {row[0]: row[1] for row in rows}

    except Exception as e:
        raise DatabaseError(f"Error getting saved MCQ answers: {str(e)}") from e


# ============================================================================
#                       RESPONSE TRACKING — PSYCHOMETRIC
# ============================================================================

def save_psychometric_response(assessment_id, question_id, trait, score, scenario_response=None):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            _lock_active_assessment(cursor, assessment_id)
            cursor.execute(
                """
                INSERT INTO psychometric_responses (
                    assessment_id, question_id, trait, score, scenario_response
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (assessment_id, question_id) DO UPDATE
                SET trait = EXCLUDED.trait,
                    score = EXCLUDED.score,
                    scenario_response = EXCLUDED.scenario_response
                """,
                (assessment_id, question_id, trait, score, scenario_response),
            )
            conn.commit()

    except Exception as e:
        if isinstance(e, AssessmentStateError):
            raise
        raise DatabaseError(f"Error saving psychometric response: {str(e)}") from e


def get_saved_psychometric_answers(assessment_id):
    try:
        rows = _fetch_all(
            """
            SELECT DISTINCT ON (question_id) question_id, score, scenario_response
            FROM psychometric_responses
            WHERE assessment_id = %s
            ORDER BY question_id, id DESC
            """,
            (assessment_id,)
        )

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
        with db_connection() as conn:
            cursor = conn.cursor()
            _lock_active_assessment(cursor, assessment_id)
            cursor.execute(
                """
                INSERT INTO coding_submissions (
                    assessment_id, problem_id, language, code,
                    test_cases_passed, total_test_cases
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (assessment_id, problem_id) DO UPDATE
                SET language = EXCLUDED.language,
                    code = EXCLUDED.code,
                    test_cases_passed = EXCLUDED.test_cases_passed,
                    total_test_cases = EXCLUDED.total_test_cases,
                    submitted_at = CURRENT_TIMESTAMP
                """,
                (
                    assessment_id,
                    problem_id,
                    language,
                    code,
                    test_cases_passed,
                    total_test_cases,
                ),
            )
            conn.commit()

    except Exception as e:
        if isinstance(e, AssessmentStateError):
            raise
        raise DatabaseError(f"Error saving coding submission: {str(e)}") from e


def get_saved_coding_submission(assessment_id):
    try:
        row = _fetch_one(
            """
            SELECT problem_id, language, code, test_cases_passed, total_test_cases
            FROM coding_submissions
            WHERE assessment_id = %s
            ORDER BY submitted_at DESC
            LIMIT 1
            """,
            (assessment_id,)
        )

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
        result = _fetch_one("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) as correct
            FROM mcq_responses WHERE assessment_id = %s
        """, (assessment_id,))

        total = result[0]
        correct = result[1] or 0

        return 0.0 if total == 0 else round((correct / total) * 100, 2)

    except Exception as e:
        raise DatabaseError(f"Error calculating MCQ score: {str(e)}") from e


def get_coding_score(assessment_id):
    try:
        result = _fetch_one("""
            SELECT SUM(test_cases_passed) as total_passed, SUM(total_test_cases) as total_tests
            FROM coding_submissions WHERE assessment_id = %s
        """, (assessment_id,))

        total_passed = result[0] or 0
        total_tests = result[1] or 0

        return 0.0 if total_tests == 0 else round((total_passed / total_tests) * 100, 2)

    except Exception as e:
        raise DatabaseError(f"Error calculating coding score: {str(e)}") from e


def get_psychometric_scores(assessment_id):
    try:
        rows = _fetch_all("""
            SELECT trait, AVG(score) as avg_score
            FROM psychometric_responses WHERE assessment_id = %s
            GROUP BY trait
        """, (assessment_id,))

        return {row[0]: round(row[1], 2) for row in rows}

    except Exception as e:
        raise DatabaseError(f"Error calculating psychometric scores: {str(e)}") from e


def finalize_assessment(assessment_id):
    """Score and complete an assessment as one serialized transaction.

    Answer writes lock the same assessment row, so completion cannot race a final
    autosave. Repeated completion requests are idempotent and return the persisted
    result while repairing schedule/candidate status links if necessary.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT a.candidate_id, a.scheduled_assessment_id, a.status,
                       a.technical_score, a.psychometric_score, a.overall_score,
                       a.decision, a.rationale, a.hiring_recommendation,
                       COALESCE(sa.is_technical_role, TRUE), a.job_id,
                       GREATEST(
                           COALESCE(a.time_elapsed_seconds, 0),
                           CASE
                               WHEN a.started_at IS NULL THEN 0
                               ELSE EXTRACT(
                                   EPOCH FROM (CURRENT_TIMESTAMP - a.started_at)
                               )::INTEGER
                           END
                       ) AS elapsed_seconds
                FROM assessments a
                LEFT JOIN scheduled_assessments sa
                  ON sa.id = a.scheduled_assessment_id
                WHERE a.id = %s
                FOR UPDATE OF a
                """,
                (assessment_id,),
            )
            assessment = cursor.fetchone()
            if not assessment:
                raise AssessmentStateError(f"Assessment {assessment_id} does not exist")

            (
                candidate_id,
                scheduled_assessment_id,
                assessment_status,
                persisted_technical,
                persisted_psychometric,
                persisted_overall,
                persisted_decision,
                persisted_rationale,
                persisted_recommendation,
                is_technical_role,
                assessment_job_id,
                elapsed_seconds,
            ) = assessment

            finalized_elapsed_seconds = min(
                ASSESSMENT_DURATION_SECONDS,
                max(0, int(elapsed_seconds or 0)),
            )

            if assessment_status not in (*ACTIVE_ASSESSMENT_STATUSES, 'completed'):
                raise AssessmentStateError(
                    f"Assessment {assessment_id} cannot be completed from {assessment_status}"
                )

            # Repair legacy rows where only scheduled_assessments.assessment_id was set.
            if scheduled_assessment_id is None:
                cursor.execute(
                    """
                    SELECT id, is_technical_role, job_id
                    FROM scheduled_assessments
                    WHERE assessment_id = %s
                       OR (candidate_id = %s AND status = 'in_progress')
                    ORDER BY CASE WHEN assessment_id = %s THEN 0 ELSE 1 END, created_at DESC
                    LIMIT 1
                    FOR UPDATE
                    """,
                    (assessment_id, candidate_id, assessment_id),
                )
                schedule = cursor.fetchone()
                if schedule:
                    scheduled_assessment_id = schedule[0]
                    is_technical_role = (
                        schedule[1] if schedule[1] is not None else is_technical_role
                    )
                    assessment_job_id = assessment_job_id or schedule[2]
                    cursor.execute(
                        """
                        UPDATE assessments
                        SET scheduled_assessment_id = %s,
                            job_id = COALESCE(job_id, %s)
                        WHERE id = %s
                        """,
                        (scheduled_assessment_id, assessment_job_id, assessment_id),
                    )

            cursor.execute(
                """
                SELECT COUNT(*),
                       COALESCE(SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END), 0)
                FROM mcq_responses
                WHERE assessment_id = %s
                """,
                (assessment_id,),
            )
            mcq_total, mcq_correct = cursor.fetchone()
            mcq_score = 0.0 if not mcq_total else (mcq_correct / mcq_total) * 100

            cursor.execute(
                """
                SELECT COALESCE(SUM(test_cases_passed), 0),
                       COALESCE(SUM(total_test_cases), 0)
                FROM coding_submissions
                WHERE assessment_id = %s
                """,
                (assessment_id,),
            )
            code_passed, code_total = cursor.fetchone()
            coding_score = 0.0 if not code_total else (code_passed / code_total) * 100

            cursor.execute(
                """
                SELECT trait, AVG(score)
                FROM psychometric_responses
                WHERE assessment_id = %s
                GROUP BY trait
                """,
                (assessment_id,),
            )
            psychometric_breakdown = {
                row[0]: round(float(row[1]), 2) for row in cursor.fetchall()
            }
            average_trait_score = (
                sum(psychometric_breakdown.values()) / len(psychometric_breakdown)
                if psychometric_breakdown
                else 0.0
            )

            if assessment_status == 'completed' and all(
                value is not None
                for value in (persisted_technical, persisted_psychometric, persisted_overall)
            ):
                technical_score = float(persisted_technical)
                psychometric_score = float(persisted_psychometric)
                overall_score = float(persisted_overall)
                decision = persisted_decision
                rationale = persisted_rationale
                recommendation = persisted_recommendation
                if not all((decision, rationale, recommendation)):
                    defaults = _recommendation_for_score(overall_score)
                    decision = decision or defaults[0]
                    rationale = rationale or defaults[1]
                    recommendation = recommendation or defaults[2]
                    cursor.execute(
                        """
                        UPDATE assessments
                        SET decision = COALESCE(decision, %s),
                            rationale = COALESCE(rationale, %s),
                            hiring_recommendation = COALESCE(hiring_recommendation, %s)
                        WHERE id = %s
                        """,
                        (decision, rationale, recommendation, assessment_id),
                    )
            else:
                technical_score = (
                    mcq_score * 0.6 + coding_score * 0.4
                    if is_technical_role
                    else mcq_score
                )
                psychometric_score = average_trait_score * 10
                overall_score = (
                    technical_score * TECHNICAL_SCORE_WEIGHT
                    + psychometric_score * PSYCHOMETRIC_SCORE_WEIGHT
                )

                decision, rationale, recommendation = _recommendation_for_score(
                    overall_score
                )

                cursor.execute(
                    """
                    UPDATE assessments
                    SET technical_score = %s, psychometric_score = %s,
                        overall_score = %s, decision = %s, rationale = %s,
                        hiring_recommendation = %s, status = 'completed',
                        time_elapsed_seconds = GREATEST(
                            COALESCE(time_elapsed_seconds, 0), %s
                        ),
                        completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                    WHERE id = %s
                    """,
                    (
                        technical_score,
                        psychometric_score,
                        overall_score,
                        decision,
                        rationale,
                        recommendation,
                        finalized_elapsed_seconds,
                        assessment_id,
                    ),
                )

            if scheduled_assessment_id is not None:
                cursor.execute(
                    """
                    UPDATE scheduled_assessments
                    SET status = 'completed', assessment_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                      AND status IN ('scheduled', 'in_progress', 'completed')
                      AND (assessment_id IS NULL OR assessment_id = %s)
                    """,
                    (assessment_id, scheduled_assessment_id, assessment_id),
                )
                if cursor.rowcount == 0:
                    raise AssessmentStateError(
                        f"Schedule {scheduled_assessment_id} is inconsistent with "
                        f"assessment {assessment_id}"
                    )

            cursor.execute(
                """
                UPDATE candidates
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (candidate_id,),
            )
            if cursor.rowcount == 0:
                raise AssessmentStateError(
                    f"Candidate {candidate_id} for assessment {assessment_id} does not exist"
                )

            conn.commit()
            return {
                'assessment_id': assessment_id,
                'candidate_id': candidate_id,
                'scheduled_assessment_id': scheduled_assessment_id,
                'job_id': assessment_job_id,
                'scores': {
                    'mcq': round(mcq_score, 2),
                    'coding': round(coding_score if is_technical_role else 0.0, 2),
                    'technical': round(technical_score, 2),
                    'psychometric': round(psychometric_score, 2),
                    'overall': round(overall_score, 2),
                },
                'psychometric_breakdown': psychometric_breakdown,
                'decision': decision,
                'rationale': rationale,
                'ai_recommendation': recommendation,
                'is_technical_role': bool(is_technical_role),
                'time_elapsed_seconds': finalized_elapsed_seconds,
            }
    except Exception as e:
        if isinstance(e, AssessmentStateError):
            raise
        raise DatabaseError(f"Error finalizing assessment: {str(e)}") from e


# ============================================================================
#                         ASSESSMENT SCHEDULING
# ============================================================================

def create_scheduled_assessment(
    candidate_id,
    interviewer_id,
    scheduled_time,
    is_technical_role=True,
    questions_data=None,
    job_id=None,
    access_token=None,
):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scheduled_assessments (
                    candidate_id, interviewer_id, job_id, scheduled_time, status,
                    is_technical_role, questions_data, access_token
                )
                VALUES (%s, %s, %s, %s, 'scheduled', %s, %s, %s)
                RETURNING id
                """,
                (
                    candidate_id,
                    interviewer_id,
                    job_id,
                    scheduled_time,
                    is_technical_role,
                    json.dumps(questions_data) if questions_data else None,
                    access_token,
                ),
            )
            result = cursor.fetchone()
            if not result:
                raise DatabaseError("Scheduled assessment insert returned no id")
            cursor.execute(
                """
                UPDATE candidates
                SET status = 'under_review', updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (candidate_id,),
            )
            if cursor.rowcount == 0:
                raise AssessmentStateError(
                    f"Candidate {candidate_id} does not exist"
                )
            conn.commit()
            return result[0]

    except Exception as e:
        if isinstance(e, DatabaseError):
            raise
        raise DatabaseError(f"Error creating scheduled assessment: {str(e)}") from e


def get_scheduled_assessment_by_id(scheduled_assessment_id):
    try:
        row = _fetch_one(
            """SELECT id, candidate_id, interviewer_id, scheduled_time, status, assessment_id,
                      is_technical_role, questions_data, created_at, updated_at, job_id
               FROM scheduled_assessments WHERE id = %s""",
            (scheduled_assessment_id,)
        )
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
            'questions_data': questions_data, 'created_at': row[8], 'updated_at': row[9],
            'job_id': row[10],
        }
    except Exception as e:
        raise DatabaseError(f"Error retrieving scheduled assessment by id: {str(e)}") from e


# ============================================================================
#                       TOKEN-BASED ASSESSMENT ACCESS
# ============================================================================

def generate_assessment_token():
    return secrets.token_urlsafe(32)


def get_assessment_by_token(token):
    try:
        row = _fetch_one(
            """SELECT sa.id, sa.candidate_id, sa.interviewer_id, sa.scheduled_time,
                      sa.status, COALESCE(sa.assessment_id, a.id), sa.started_at,
                      c.name as candidate_name, c.email as candidate_email,
                      sa.job_id,
                      CASE
                          WHEN a.id IS NULL THEN FALSE
                          ELSE GREATEST(
                              COALESCE(a.time_elapsed_seconds, 0),
                              CASE
                                  WHEN a.started_at IS NULL THEN 0
                                  ELSE EXTRACT(
                                      EPOCH FROM (CURRENT_TIMESTAMP - a.started_at)
                                  )::INTEGER
                              END
                          ) >= %s
                      END AS deadline_reached
               FROM scheduled_assessments sa
               JOIN candidates c ON sa.candidate_id = c.id
               LEFT JOIN assessments a
                 ON a.id = sa.assessment_id
                 OR (
                     sa.assessment_id IS NULL
                     AND a.scheduled_assessment_id = sa.id
                 )
               WHERE sa.access_token = %s""",
            (ASSESSMENT_DURATION_SECONDS, token)
        )

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
                'candidate_email': row[8],
                'job_id': row[9],
                'deadline_reached': bool(row[10]),
            }
        return None

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment by token: {str(e)}") from e


def start_assessment_by_token(token):
    """Atomically create/link an assessment for a schedule, or resume its existing one.

    Locking the scheduled row prevents two concurrent start requests from creating
    separate assessments. The schedule job is copied to the assessment in the same
    transaction, so downstream analytics always retain the job selected at schedule
    time even if the candidate's best match changes later.
    """
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, candidate_id, job_id, status, assessment_id
                FROM scheduled_assessments
                WHERE access_token = %s
                FOR UPDATE
                """,
                (token,),
            )
            schedule = cursor.fetchone()
            if not schedule:
                return None

            schedule_id, candidate_id, job_id, schedule_status, linked_assessment_id = schedule
            if schedule_status not in ('scheduled', 'in_progress'):
                return None

            cursor.execute(
                """
                SELECT id, status,
                       GREATEST(
                           COALESCE(time_elapsed_seconds, 0),
                           CASE
                               WHEN started_at IS NULL THEN 0
                               ELSE EXTRACT(
                                   EPOCH FROM (CURRENT_TIMESTAMP - started_at)
                               )::INTEGER
                           END
                       ) >= %s AS deadline_reached
                FROM assessments
                WHERE scheduled_assessment_id = %s
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
                """,
                (ASSESSMENT_DURATION_SECONDS, schedule_id),
            )
            existing = cursor.fetchone()
            was_resume = schedule_status == 'in_progress' or existing is not None

            if existing:
                assessment_id, assessment_status, deadline_reached = existing
                if assessment_status not in ACTIVE_ASSESSMENT_STATUSES:
                    raise AssessmentStateError(
                        f"Assessment {assessment_id} is already {assessment_status}"
                    )
                if deadline_reached:
                    raise AssessmentStateError(
                        f"Assessment {assessment_id} has reached its time limit"
                    )
                cursor.execute(
                    """
                    UPDATE assessments
                    SET job_id = COALESCE(job_id, %s)
                    WHERE id = %s
                    """,
                    (job_id, assessment_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO assessments (
                        candidate_id, job_id, scheduled_assessment_id,
                        status, started_at
                    )
                    VALUES (%s, %s, %s, 'in_progress', CURRENT_TIMESTAMP)
                    RETURNING id
                    """,
                    (candidate_id, job_id, schedule_id),
                )
                assessment_id = cursor.fetchone()[0]

            if linked_assessment_id not in (None, assessment_id):
                raise AssessmentStateError(
                    f"Schedule {schedule_id} is already linked to assessment "
                    f"{linked_assessment_id}"
                )

            cursor.execute(
                """
                UPDATE scheduled_assessments
                SET status = 'in_progress', assessment_id = %s,
                    started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (assessment_id, schedule_id),
            )
            conn.commit()
            return {
                'assessment_id': assessment_id,
                'scheduled_assessment_id': schedule_id,
                'candidate_id': candidate_id,
                'job_id': job_id,
                'is_resume': was_resume,
            }

    except Exception as e:
        if isinstance(e, AssessmentStateError):
            raise
        raise DatabaseError(f"Error starting assessment: {str(e)}") from e


def verify_assessment_access_token(
    token: str,
    assessment_id: int,
    *,
    allow_expired: bool = False,
    allow_completed: bool = False,
) -> bool:
    """Return whether a token may access an assessment in its current state."""
    if not token:
        return False
    try:
        result = _fetch_one(
            """SELECT sa.status, a.status,
                      GREATEST(
                          COALESCE(a.time_elapsed_seconds, 0),
                          CASE
                              WHEN a.started_at IS NULL THEN 0
                              ELSE EXTRACT(
                                  EPOCH FROM (CURRENT_TIMESTAMP - a.started_at)
                              )::INTEGER
                          END
                      ) >= %s AS deadline_reached
               FROM scheduled_assessments sa
               JOIN assessments a ON a.id = sa.assessment_id
               WHERE sa.access_token = %s AND sa.assessment_id = %s
                  AND sa.status IN ('in_progress', 'completed')
                  AND a.status IN ('started', 'in_progress', 'completed')""",
            (ASSESSMENT_DURATION_SECONDS, token, assessment_id)
        )
        if not result:
            return False
        schedule_status, assessment_status, deadline_reached = result
        if schedule_status == 'completed' or assessment_status == 'completed':
            return allow_completed
        return allow_expired or not deadline_reached
    except Exception:
        return False


# ============================================================================
#                        ASSESSMENT QUESTIONS & TIME
# ============================================================================

def save_assessment_questions(assessment_id, questions_data):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            _lock_active_assessment(cursor, assessment_id)
            cursor.execute(
                """UPDATE assessments
                   SET questions_data = %s
                   WHERE id = %s""",
                (json.dumps(questions_data), assessment_id),
            )
            conn.commit()

    except Exception as e:
        if isinstance(e, AssessmentStateError):
            raise
        raise DatabaseError(f"Error saving assessment questions: {str(e)}") from e


def get_assessment_questions(assessment_id):
    try:
        row = _fetch_one(
            """SELECT questions_data FROM assessments WHERE id = %s""",
            (assessment_id,)
        )

        questions_data = row[0] if row and row[0] else None
        if isinstance(questions_data, str):
            try:
                return json.loads(questions_data)
            except json.JSONDecodeError as exc:
                raise DatabaseError(
                    f"Assessment {assessment_id} has invalid questions JSON"
                ) from exc
        return questions_data

    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment questions: {str(e)}") from e


def update_assessment_time_elapsed(assessment_id, time_elapsed_seconds):
    try:
        time_elapsed_seconds = int(time_elapsed_seconds)
        if not 0 <= time_elapsed_seconds <= ASSESSMENT_DURATION_SECONDS:
            raise ValueError(
                "time_elapsed_seconds must be between 0 and "
                f"{ASSESSMENT_DURATION_SECONDS}"
            )
        with db_connection() as conn:
            cursor = conn.cursor()
            _lock_active_assessment(cursor, assessment_id)
            cursor.execute(
                """UPDATE assessments
                   SET time_elapsed_seconds = GREATEST(time_elapsed_seconds, %s)
                   WHERE id = %s""",
                (time_elapsed_seconds, assessment_id),
            )
            conn.commit()

    except Exception as e:
        if isinstance(e, (AssessmentStateError, ValueError)):
            raise
        raise DatabaseError(f"Error updating assessment time: {str(e)}") from e


def get_assessment_time_elapsed(assessment_id):
    try:
        row = _fetch_one(
            """
            SELECT
                GREATEST(
                    COALESCE(time_elapsed_seconds, 0),
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER
                ) AS elapsed_seconds
            FROM assessments
            WHERE id = %s AND started_at IS NOT NULL
            """,
            (assessment_id,)
        )
        return max(0, row[0]) if row and row[0] is not None else 0

    except Exception as e:
        raise DatabaseError(f"Error getting assessment time: {str(e)}") from e
