"""Authenticated proctor dashboard, assignment, and violation reporting routes."""

from __future__ import annotations

import contextlib
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import psycopg2
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from psycopg2.extras import RealDictCursor

from db_config import get_connection, return_connection
from storage_config import get_upload_root, is_within_upload_root


logger = logging.getLogger(__name__)
proctor_bp = Blueprint("proctor", __name__)


class RequestError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_db():
    """Return a transactional database connection (kept for compatibility)."""

    return get_connection()


@contextmanager
def _db_cursor(*, write=False):
    conn = None
    cursor = None
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        if write:
            conn.commit()
    except Exception:
        if conn is not None:
            with contextlib.suppress(Exception):
                conn.rollback()
        raise
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        if conn is not None:
            return_connection(conn)


def get_current_user_id():
    """Return the numeric user ID stored as the JWT identity."""

    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError) as exc:
        raise RequestError("Invalid user identity", 401) from exc
    if user_id <= 0:
        raise RequestError("Invalid user identity", 401)
    return user_id


def proctor_required(function):
    @wraps(function)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        if get_jwt().get("role") != "proctor":
            return jsonify({"status": "error", "message": "Proctor access required"}), 403
        return function(*args, **kwargs)

    return decorated_function


def database_endpoint(function):
    """Translate route failures without leaking SQL or infrastructure details."""

    @wraps(function)
    def decorated_function(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RequestError as exc:
            return jsonify({"status": "error", "message": exc.message}), exc.status_code
        except (psycopg2.Error, RuntimeError):
            logger.exception("Database unavailable in proctor endpoint %s", function.__name__)
            return jsonify({"status": "error", "message": "Proctoring data is temporarily unavailable"}), 503
        except Exception:
            logger.exception("Unexpected failure in proctor endpoint %s", function.__name__)
            return jsonify({"status": "error", "message": "Internal server error"}), 500

    return decorated_function


def _integer_query(name, default, minimum, maximum):
    raw_value = request.args.get(name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise RequestError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise RequestError(f"{name} must be between {minimum} and {maximum}")
    return value


def _rows(cursor):
    return [dict(row) for row in cursor.fetchall()]


def _private_screenshot_routes(rows):
    """Replace storage paths with assignment-checked API URLs."""
    for row in rows:
        if row.get("screenshot_url"):
            row["screenshot_url"] = (
                f"/api/proctor/violations/{row['id']}/screenshot"
            )
    return rows


COMPLETED_ASSESSMENTS_SQL = """
    SELECT
        a.id,
        c.name AS candidate_name,
        c.email AS candidate_email,
        jd.title AS job_title,
        a.technical_score,
        a.psychometric_score,
        a.overall_score,
        COALESCE(mcq.mcq_score, 0) AS mcq_score,
        COALESCE(code.coding_score, 0) AS coding_score,
        COALESCE(violations.violation_count, 0) AS violation_count,
        COALESCE(violations.violation_count, 0) AS proctoring_violations,
        sa.proctor_id,
        a.completed_at
    FROM assessments a
    JOIN candidates c ON a.candidate_id = c.id
    LEFT JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
    LEFT JOIN job_descriptions jd ON jd.id = COALESCE(a.job_id, sa.job_id)
    LEFT JOIN LATERAL (
        SELECT ROUND(AVG(CASE WHEN latest.is_correct THEN 100.0 ELSE 0.0 END), 2) AS mcq_score
        FROM (
            SELECT DISTINCT ON (question_id) question_id, is_correct
            FROM mcq_responses
            WHERE assessment_id = a.id
            ORDER BY question_id, created_at DESC, id DESC
        ) latest
    ) mcq ON TRUE
    LEFT JOIN LATERAL (
        SELECT ROUND(
            100.0 * SUM(latest.test_cases_passed) /
            NULLIF(SUM(latest.total_test_cases), 0), 2
        ) AS coding_score
        FROM (
            SELECT DISTINCT ON (problem_id)
                problem_id, test_cases_passed, total_test_cases
            FROM coding_submissions
            WHERE assessment_id = a.id
            ORDER BY problem_id, submitted_at DESC, id DESC
        ) latest
    ) code ON TRUE
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS violation_count
        FROM proctoring_violations pv
        WHERE pv.assessment_id = a.id
    ) violations ON TRUE
    WHERE a.status = 'completed'
      AND sa.proctor_id = %s
      AND (%s OR a.completed_at >= NOW() - (%s || ' days')::INTERVAL)
    ORDER BY a.completed_at DESC
    LIMIT %s
"""


def _completed_assessments(limit, user_id, days=None):
    with _db_cursor() as cursor:
        cursor.execute(
            COMPLETED_ASSESSMENTS_SQL,
            (user_id, days is None, days or 0, limit),
        )
        return _rows(cursor)


@proctor_bp.route("/dashboard-stats", methods=["GET"])
@proctor_required
@database_endpoint
def get_dashboard_stats():
    """Return a consistent dashboard snapshot from canonical sources."""

    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            SELECT
                (SELECT COUNT(*)
                 FROM assessments a
                 JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
                 WHERE a.status = 'in_progress'
                   AND (sa.proctor_id = %s OR sa.proctor_id IS NULL)) AS active_assessments,
                (SELECT COUNT(*)
                 FROM scheduled_assessments sa
                 WHERE sa.scheduled_time >= CURRENT_DATE
                   AND sa.scheduled_time < CURRENT_DATE + INTERVAL '1 day'
                   AND sa.status = 'scheduled'
                   AND (sa.proctor_id = %s OR sa.proctor_id IS NULL)) AS scheduled_today,
                (SELECT COUNT(*)
                 FROM assessments a
                 JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
                 WHERE a.completed_at >= CURRENT_DATE
                   AND a.completed_at < CURRENT_DATE + INTERVAL '1 day'
                   AND a.status = 'completed'
                   AND sa.proctor_id = %s) AS completed_today,
                (SELECT COUNT(*)
                 FROM proctoring_violations pv
                 JOIN assessments a ON a.id = pv.assessment_id
                 JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
                 WHERE pv.timestamp >= CURRENT_DATE
                   AND pv.timestamp < CURRENT_DATE + INTERVAL '1 day'
                   AND sa.proctor_id = %s) AS violations_today
        """, (user_id, user_id, user_id, user_id))
        return jsonify(dict(cursor.fetchone()))


@proctor_bp.route("/active-assessments", methods=["GET"])
@proctor_required
@database_endpoint
def get_active_assessments():
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            SELECT
                a.id AS assessment_id,
                sa.id AS scheduled_assessment_id,
                c.name AS candidate_name,
                c.email AS candidate_email,
                jd.title AS job_title,
                a.started_at,
                COALESCE(v.violation_count, 0) AS violation_count,
                COALESCE(v.violation_count, 0) AS proctoring_violations,
                sa.proctor_id,
                CASE
                    WHEN EXTRACT(EPOCH FROM (NOW() - a.started_at)) / 60 > 60 THEN 'overdue'
                    WHEN EXTRACT(EPOCH FROM (NOW() - a.started_at)) / 60 > 45 THEN 'near_end'
                    ELSE 'in_progress'
                END AS time_status
            FROM assessments a
            JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN job_descriptions jd ON jd.id = COALESCE(a.job_id, sa.job_id)
            LEFT JOIN LATERAL (
                SELECT COUNT(*) AS violation_count
                FROM proctoring_violations pv
                WHERE pv.assessment_id = a.id
            ) v ON TRUE
            WHERE a.status = 'in_progress'
              AND (sa.proctor_id = %s OR sa.proctor_id IS NULL)
            ORDER BY a.started_at ASC
        """, (user_id,))
        return jsonify(_rows(cursor))


@proctor_bp.route("/scheduled-assessments", methods=["GET"])
@proctor_required
@database_endpoint
def get_scheduled_assessments():
    days_ahead = _integer_query("days", 7, 1, 90)
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            SELECT
                sa.id,
                c.name AS candidate_name,
                c.email AS candidate_email,
                jd.title AS job_title,
                sa.scheduled_time,
                ROUND(EXTRACT(EPOCH FROM (sa.scheduled_time - NOW())) / 60) AS minutes_until_start,
                sa.status,
                sa.proctor_id
            FROM scheduled_assessments sa
            JOIN candidates c ON sa.candidate_id = c.id
            LEFT JOIN job_descriptions jd ON sa.job_id = jd.id
            WHERE sa.status = 'scheduled'
              AND sa.scheduled_time <= NOW() + (%s || ' days')::INTERVAL
              AND sa.scheduled_time > NOW()
              AND (sa.proctor_id = %s OR sa.proctor_id IS NULL)
            ORDER BY sa.scheduled_time ASC
        """, (days_ahead, user_id))
        return jsonify(_rows(cursor))


@proctor_bp.route("/completed-assessments", methods=["GET"])
@proctor_required
@database_endpoint
def get_completed_assessments():
    limit = _integer_query("limit", 50, 1, 200)
    days = _integer_query("days", 7, 1, 365)
    return jsonify(_completed_assessments(limit, get_current_user_id(), days))


@proctor_bp.route("/assessments/<int:assessment_id>/violations", methods=["GET"])
@proctor_required
@database_endpoint
def get_assessment_violations(assessment_id):
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            SELECT 1
            FROM assessments a
            JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
            WHERE a.id = %s AND sa.proctor_id = %s
        """, (assessment_id, user_id))
        if cursor.fetchone() is None:
            raise RequestError("Assessment not found or not assigned to this proctor", 404)
        cursor.execute("""
            SELECT id, assessment_id, violation_type, description, severity,
                   screenshot_path AS screenshot_url, timestamp
            FROM proctoring_violations
            WHERE assessment_id = %s
            ORDER BY timestamp DESC, id DESC
        """, (assessment_id,))
        violations = _private_screenshot_routes(_rows(cursor))
        return jsonify({"status": "success", "data": violations})


@proctor_bp.route("/violations/<int:violation_id>/screenshot", methods=["GET"])
@proctor_required
@database_endpoint
def get_violation_screenshot(violation_id):
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute(
            """
            SELECT pv.screenshot_path
            FROM proctoring_violations pv
            JOIN assessments a ON a.id = pv.assessment_id
            JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
            WHERE pv.id = %s AND sa.proctor_id = %s
            """,
            (violation_id, user_id),
        )
        row = cursor.fetchone()

    if not row or not row["screenshot_path"]:
        raise RequestError("Screenshot not found", 404)
    storage_path = row["screenshot_path"]
    if not isinstance(storage_path, str) or not storage_path.startswith("/uploads/"):
        raise RequestError("Screenshot not found", 404)

    relative_path = Path(storage_path.removeprefix("/uploads/"))
    file_path = (get_upload_root() / relative_path).resolve()
    if not is_within_upload_root(file_path) or not file_path.is_file():
        raise RequestError("Screenshot not found", 404)
    return send_file(file_path, conditional=True, max_age=0)


@proctor_bp.route("/violations/flagged", methods=["GET"])
@proctor_required
@database_endpoint
def get_flagged_violations():
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            SELECT
                pv.id,
                pv.assessment_id,
                c.name AS candidate_name,
                c.email AS candidate_email,
                jd.title AS job_title,
                pv.violation_type,
                pv.severity,
                pv.description,
                pv.screenshot_path AS screenshot_url,
                pv.timestamp,
                COUNT(*) OVER (PARTITION BY pv.assessment_id) AS total_violations_in_assessment
            FROM proctoring_violations pv
            JOIN assessments a ON pv.assessment_id = a.id
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
            LEFT JOIN job_descriptions jd ON jd.id = COALESCE(a.job_id, sa.job_id)
            WHERE sa.proctor_id = %s
              AND (
                  pv.severity IN ('high', 'critical')
                  OR pv.assessment_id IN (
                      SELECT assessment_id
                      FROM proctoring_violations
                      GROUP BY assessment_id
                      HAVING COUNT(*) > 3
                  )
              )
            ORDER BY CASE pv.severity
                WHEN 'critical' THEN 4 WHEN 'high' THEN 3
                WHEN 'medium' THEN 2 ELSE 1 END DESC,
                pv.timestamp DESC
        """, (user_id,))
        return jsonify(_private_screenshot_routes(_rows(cursor)))


@proctor_bp.route("/anomaly-detection", methods=["GET"])
@proctor_required
@database_endpoint
def detect_anomalies():
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            SELECT
                a.id,
                c.name AS candidate_name,
                c.email AS candidate_email,
                jd.title AS job_title,
                COUNT(pv.id) AS violation_count,
                STRING_AGG(DISTINCT pv.violation_type, ',') AS violation_types,
                a.overall_score,
                CASE
                    WHEN COUNT(pv.id) > 5 THEN 'critical'
                    WHEN COUNT(pv.id) > 3 THEN 'high'
                    WHEN COUNT(pv.id) > 1 THEN 'medium'
                    ELSE 'low'
                END AS suspicion_level
            FROM assessments a
            JOIN candidates c ON a.candidate_id = c.id
            JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
            LEFT JOIN job_descriptions jd ON jd.id = COALESCE(a.job_id, sa.job_id)
            LEFT JOIN proctoring_violations pv ON a.id = pv.assessment_id
            WHERE a.status = 'completed'
              AND a.completed_at >= NOW() - INTERVAL '7 days'
              AND sa.proctor_id = %s
            GROUP BY a.id, c.name, c.email, jd.title, a.overall_score
            HAVING COUNT(pv.id) > 1
            ORDER BY COUNT(pv.id) DESC
        """, (user_id,))
        suspicious = _rows(cursor)
    return jsonify({
        "suspicious_assessments": suspicious,
        "detection_timestamp": datetime.now(timezone.utc).isoformat(),
    })


@proctor_bp.route("/quality-metrics", methods=["GET"])
@proctor_required
@database_endpoint
def get_quality_metrics():
    user_id = get_current_user_id()
    requested_id = _integer_query("proctor_id", user_id, 1, 2_147_483_647)
    if requested_id != user_id:
        raise RequestError("Proctors may only view their own quality metrics", 403)

    with _db_cursor() as cursor:
        cursor.execute("""
            WITH scoped AS (
                SELECT a.id, a.status
                FROM scheduled_assessments sa
                JOIN assessments a ON sa.id = a.scheduled_assessment_id
                WHERE sa.proctor_id = %s
            ), violation_counts AS (
                SELECT pv.assessment_id,
                       COUNT(*) AS total,
                       COUNT(*) FILTER (WHERE pv.severity = 'critical') AS critical
                FROM proctoring_violations pv
                JOIN scoped s ON s.id = pv.assessment_id
                GROUP BY pv.assessment_id
            )
            SELECT
                COUNT(s.id) AS total_proctored,
                COUNT(*) FILTER (WHERE s.status = 'completed') AS completed,
                COUNT(*) FILTER (WHERE COALESCE(v.total, 0) > 0) AS flagged_assessments,
                COALESCE(AVG(COALESCE(v.total, 0)), 0) AS avg_violations_per_assessment,
                COALESCE(SUM(v.total), 0) AS total_violations,
                COALESCE(SUM(v.critical), 0) AS critical_violations
            FROM scoped s
            LEFT JOIN violation_counts v ON v.assessment_id = s.id
        """, (user_id,))
        return jsonify(dict(cursor.fetchone()))


@proctor_bp.route("/job-performance", methods=["GET"])
@proctor_required
@database_endpoint
def get_job_performance_metrics():
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            WITH recent AS (
                SELECT a.id, COALESCE(a.job_id, sa.job_id) AS job_id, a.overall_score
                FROM assessments a
                JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
                WHERE a.completed_at >= NOW() - INTERVAL '30 days'
                  AND sa.proctor_id = %s
            ), violation_counts AS (
                SELECT assessment_id, COUNT(*) AS total
                FROM proctoring_violations
                GROUP BY assessment_id
            )
            SELECT
                jd.id,
                jd.title AS job_title,
                COUNT(r.id) AS total_assessments,
                AVG(r.overall_score) AS avg_score,
                COALESCE(AVG(COALESCE(v.total, 0)), 0) AS avg_violations,
                COUNT(*) FILTER (WHERE COALESCE(v.total, 0) > 3) AS highly_flagged,
                jd.role_complexity_level AS complexity
            FROM job_descriptions jd
            JOIN recent r ON jd.id = r.job_id
            LEFT JOIN violation_counts v ON v.assessment_id = r.id
            GROUP BY jd.id, jd.title, jd.role_complexity_level
            ORDER BY avg_violations DESC
        """, (user_id,))
        return jsonify(_rows(cursor))


@proctor_bp.route("/assign-assessment", methods=["POST"])
@proctor_required
@database_endpoint
def assign_assessment():
    user_id = get_current_user_id()
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RequestError("A JSON object is required")
    scheduled_assessment_id = data.get("scheduled_assessment_id")
    if isinstance(scheduled_assessment_id, bool):
        raise RequestError("scheduled_assessment_id must be a positive integer")
    try:
        scheduled_assessment_id = int(scheduled_assessment_id)
    except (TypeError, ValueError) as exc:
        raise RequestError(
            "scheduled_assessment_id must be a positive integer"
        ) from exc
    if scheduled_assessment_id <= 0:
        raise RequestError("scheduled_assessment_id must be a positive integer")

    with _db_cursor(write=True) as cursor:
        cursor.execute("""
            SELECT id, status, proctor_id
            FROM scheduled_assessments
            WHERE id = %s
            FOR UPDATE
        """, (scheduled_assessment_id,))
        scheduled = cursor.fetchone()
        if scheduled is None:
            raise RequestError("Scheduled assessment not found", 404)
        if scheduled["status"] not in {"scheduled", "in_progress"}:
            raise RequestError("Only scheduled or active assessments can be assigned", 409)
        if scheduled["proctor_id"] not in {None, user_id}:
            raise RequestError("Assessment is already assigned to another proctor", 409)

        cursor.execute("""
            UPDATE scheduled_assessments
            SET proctor_id = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, proctor_id
        """, (user_id, scheduled_assessment_id))
        assigned = dict(cursor.fetchone())
    return jsonify({"status": "success", "message": "Assessment assigned", "data": assigned})


@proctor_bp.route("/violation-statistics", methods=["GET"])
@proctor_required
@database_endpoint
def get_violation_statistics():
    period_days = _integer_query("days", 30, 1, 365)
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            WITH scoped AS (
                SELECT pv.assessment_id, pv.violation_type, pv.severity
                FROM proctoring_violations pv
                JOIN assessments a ON a.id = pv.assessment_id
                JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
                WHERE sa.proctor_id = %s
                  AND pv.timestamp >= NOW() - (%s || ' days')::INTERVAL
            )
            SELECT
                violation_type,
                severity,
                COUNT(*) AS count,
                COUNT(DISTINCT assessment_id) AS affected_assessments,
                ROUND(COUNT(*) * 100.0 / NULLIF(
                    (SELECT COUNT(*) FROM scoped), 0
                ), 2) AS percentage
            FROM scoped
            GROUP BY violation_type, severity
            ORDER BY count DESC
        """, (user_id, period_days))
        statistics = _rows(cursor)
    return jsonify({"period_days": period_days, "statistics": statistics})


@proctor_bp.route("/shift-summary", methods=["GET"])
@proctor_required
@database_endpoint
def get_shift_summary():
    user_id = get_current_user_id()
    with _db_cursor() as cursor:
        cursor.execute("""
            WITH todays_assessments AS (
                SELECT a.id, a.status, a.overall_score
                FROM scheduled_assessments sa
                LEFT JOIN assessments a ON sa.id = a.scheduled_assessment_id
                WHERE sa.proctor_id = %s
                  AND sa.scheduled_time >= CURRENT_DATE
                  AND sa.scheduled_time < CURRENT_DATE + INTERVAL '1 day'
            ), violation_counts AS (
                SELECT pv.assessment_id, COUNT(*) AS total
                FROM proctoring_violations pv
                JOIN todays_assessments ta ON ta.id = pv.assessment_id
                GROUP BY pv.assessment_id
            )
            SELECT
                COUNT(ta.id) AS total_assessments,
                COUNT(*) FILTER (WHERE ta.status = 'completed') AS completed,
                COUNT(*) FILTER (WHERE ta.status = 'in_progress') AS in_progress,
                COUNT(*) FILTER (WHERE COALESCE(v.total, 0) > 0) AS flagged,
                COALESCE(SUM(v.total), 0) AS total_violations,
                AVG(ta.overall_score) AS avg_candidate_score
            FROM todays_assessments ta
            LEFT JOIN violation_counts v ON v.assessment_id = ta.id
        """, (user_id,))
        return jsonify(dict(cursor.fetchone()))
