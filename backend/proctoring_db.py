"""Database operations for the canonical proctoring violation log.

``proctoring_violations`` is the source of truth for candidate-side monitoring
violations.  The denormalized counter on ``assessments`` is maintained in the
same transaction so dashboards cannot drift after a successful write.
"""

from __future__ import annotations

import contextlib
import json

from db_config import get_connection, return_connection
from user_db import DatabaseError


VALID_SEVERITIES = frozenset({"low", "medium", "high", "critical"})


def _normalise_violation(
    assessment_id, violation_type, description, severity, screenshot_path
):
    if isinstance(assessment_id, bool) or not isinstance(assessment_id, int) or assessment_id <= 0:
        raise ValueError("assessment_id must be a positive integer")

    if not isinstance(violation_type, str):
        raise ValueError("violation_type must be a string")
    violation_type = violation_type.strip().lower()
    if not violation_type or len(violation_type) > 64:
        raise ValueError("violation_type must contain between 1 and 64 characters")

    if description is None:
        description = ""
    elif not isinstance(description, str):
        description = json.dumps(description, separators=(",", ":"), default=str)
    description = description.strip()
    if len(description) > 2_000:
        raise ValueError("description must not exceed 2000 characters")

    if not isinstance(severity, str) or severity.strip().lower() not in VALID_SEVERITIES:
        raise ValueError(f"severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}")
    severity = severity.strip().lower()

    if screenshot_path is not None:
        if not isinstance(screenshot_path, str) or len(screenshot_path) > 500:
            raise ValueError("screenshot_path must be a string of at most 500 characters")

    return assessment_id, violation_type, description, severity, screenshot_path


def _record_proctoring_violation(
    assessment_id,
    violation_type,
    description,
    severity="medium",
    screenshot_path=None,
):
    values = _normalise_violation(
        assessment_id, violation_type, description, severity, screenshot_path
    )
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Serialize all violation writes for one assessment. Without this lock,
        # concurrent inserts can each recalculate from a different snapshot and
        # leave the denormalized aggregate one write behind.
        cursor.execute(
            "SELECT id FROM assessments WHERE id = %s FOR UPDATE",
            (assessment_id,),
        )
        if cursor.fetchone() is None:
            raise DatabaseError("Assessment not found while recording violation")

        cursor.execute(
            """INSERT INTO proctoring_violations
               (assessment_id, violation_type, description, severity, screenshot_path)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            values,
        )
        result = cursor.fetchone()
        if not result:
            raise DatabaseError("Database did not return the created violation")
        violation_id = result[0]

        # Recalculate instead of incrementing so this write also repairs a stale
        # aggregate left by older application versions.
        cursor.execute(
            """UPDATE assessments
               SET proctoring_violations = (
                   SELECT COUNT(*)
                   FROM proctoring_violations
                   WHERE assessment_id = %s
               )
               WHERE id = %s
               RETURNING proctoring_violations""",
            (assessment_id, assessment_id),
        )
        count_row = cursor.fetchone()
        if not count_row:
            raise DatabaseError("Assessment disappeared while recording violation")

        conn.commit()
        return violation_id, int(count_row[0])
    except (ValueError, DatabaseError):
        if conn is not None:
            with contextlib.suppress(Exception):
                conn.rollback()
        raise
    except Exception as exc:
        if conn is not None:
            with contextlib.suppress(Exception):
                conn.rollback()
        raise DatabaseError(f"Error recording proctoring violation: {exc}") from exc
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        if conn is not None:
            return_connection(conn)


def record_proctoring_violation(
    assessment_id,
    violation_type,
    description,
    severity="medium",
    screenshot_path=None,
):
    """Record one canonical violation and return its database ID."""

    violation_id, _ = _record_proctoring_violation(
        assessment_id, violation_type, description, severity, screenshot_path
    )
    return violation_id


def record_proctoring_violation_with_count(
    assessment_id,
    violation_type,
    description,
    severity="medium",
    screenshot_path=None,
):
    """Record a violation and return ``(id, aggregate_count)`` atomically."""

    return _record_proctoring_violation(
        assessment_id, violation_type, description, severity, screenshot_path
    )


def get_violations_for_assessment(assessment_id):
    if isinstance(assessment_id, bool) or not isinstance(assessment_id, int) or assessment_id <= 0:
        raise ValueError("assessment_id must be a positive integer")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, assessment_id, violation_type, description, severity,
                      screenshot_path, timestamp
               FROM proctoring_violations
               WHERE assessment_id = %s
               ORDER BY timestamp DESC, id DESC""",
            (assessment_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row[0],
                "assessment_id": row[1],
                "violation_type": row[2],
                "description": row[3],
                "severity": row[4],
                "screenshot_url": row[5],
                "timestamp": row[6],
            }
            for row in rows
        ]
    except ValueError:
        raise
    except Exception as exc:
        raise DatabaseError(f"Error retrieving violations: {exc}") from exc
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        if conn is not None:
            return_connection(conn)


def count_violations_for_assessment(assessment_id):
    if isinstance(assessment_id, bool) or not isinstance(assessment_id, int) or assessment_id <= 0:
        raise ValueError("assessment_id must be a positive integer")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM proctoring_violations WHERE assessment_id = %s",
            (assessment_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except ValueError:
        raise
    except Exception as exc:
        raise DatabaseError(f"Error counting violations: {exc}") from exc
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        if conn is not None:
            return_connection(conn)
