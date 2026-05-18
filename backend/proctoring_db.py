"""
Proctoring database helpers — violation recording and event logging.
"""

from db_config import get_connection
from user_db import DatabaseError


def log_proctoring_event(assessment_id, event_type, severity, details):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO proctoring_events
            (assessment_id, event_type, severity, details)
            VALUES (%s, %s, %s, %s)
        """, (assessment_id, event_type, severity, details))

        cursor.execute("""
            UPDATE assessments
            SET proctoring_violations = proctoring_violations + 1
            WHERE id = %s
        """, (assessment_id,))

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error logging proctoring event: {str(e)}") from e


def record_proctoring_violation(assessment_id, violation_type, description, severity='medium', screenshot_url=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO proctoring_violations
               (assessment_id, violation_type, description, severity, screenshot_url)
               VALUES (%s, %s, %s, %s, %s) RETURNING id""",
            (assessment_id, violation_type, description, severity, screenshot_url)
        )

        result = cursor.fetchone()
        violation_id = result[0] if result else None

        conn.commit()
        conn.close()

        return violation_id

    except Exception as e:
        raise DatabaseError(f"Error recording proctoring violation: {str(e)}") from e


def get_violations_for_assessment(assessment_id):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, assessment_id, violation_type, description, severity,
                      screenshot_url, timestamp
               FROM proctoring_violations
               WHERE assessment_id = %s
               ORDER BY timestamp DESC""",
            (assessment_id,)
        )

        rows = cursor.fetchall()

        return [
            {
                'id': row[0],
                'assessment_id': row[1],
                'violation_type': row[2],
                'description': row[3],
                'severity': row[4],
                'screenshot_url': row[5],
                'timestamp': row[6]
            }
            for row in rows
        ]

    except Exception as e:
        raise DatabaseError(f"Error retrieving violations: {str(e)}") from e
    finally:
        if conn:
            conn.close()


def count_violations_for_assessment(assessment_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM proctoring_violations WHERE assessment_id = %s",
            (assessment_id,)
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count

    except Exception as e:
        raise DatabaseError(f"Error counting violations: {str(e)}") from e
