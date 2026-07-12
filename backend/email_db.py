"""Database helpers for email delivery outcomes and candidate history."""

from contextlib import suppress
import logging
from typing import Optional

from db_config import get_connection, return_connection
from user_db import DatabaseError

logger = logging.getLogger(__name__)
VALID_EMAIL_STATUSES = {"sent", "failed", "bounced"}


def _release_database_resources(conn, cursor) -> None:
    if cursor is not None:
        with suppress(Exception):
            cursor.close()
    if conn is not None:
        with suppress(Exception):
            return_connection(conn)


def log_email(
    recipient_email: str,
    recipient_name: str,
    email_type: str,
    subject: str,
    status: str = "sent",
    error_message: Optional[str] = None,
):
    """Persist one final email outcome and return its database id."""
    if status not in VALID_EMAIL_STATUSES:
        raise ValueError(f"Unsupported email status: {status}")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO email_logs (recipient_email, recipient_name, email_type, subject, status, error_message)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                str(recipient_email)[:254],
                str(recipient_name)[:200],
                str(email_type)[:100],
                str(subject)[:255],
                status,
                str(error_message)[:2_000] if error_message else None,
            ),
        )

        result = cursor.fetchone()
        log_id = result[0] if result else None
        conn.commit()

        return log_id

    except Exception as exc:
        if conn is not None:
            with suppress(Exception):
                conn.rollback()
        logger.error("Email outcome persistence failed (%s)", type(exc).__name__)
        raise DatabaseError("Error logging email") from exc
    finally:
        _release_database_resources(conn, cursor)


def get_candidate_emails(candidate_email: str) -> list[dict]:
    """Return delivery history for one candidate, newest first."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, recipient_email, recipient_name, email_type, subject, status, error_message, sent_at
               FROM email_logs WHERE recipient_email = %s ORDER BY sent_at DESC""",
            (str(candidate_email)[:254],),
        )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "recipient_email": row[1],
                "recipient_name": row[2],
                "email_type": row[3],
                "subject": row[4],
                "status": row[5],
                "error_message": row[6],
                "sent_at": row[7],
            }
            for row in rows
        ]

    except Exception as exc:
        logger.error("Email history query failed (%s)", type(exc).__name__)
        raise DatabaseError("Error retrieving candidate emails") from exc
    finally:
        _release_database_resources(conn, cursor)
