"""
Email database helpers — logging sent emails and retrieving email history.
"""

from db_config import get_connection
from user_db import DatabaseError


def log_email(recipient_email, recipient_name, email_type, subject, status='sent', error_message=None):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO email_logs (recipient_email, recipient_name, email_type, subject, status, error_message)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            (recipient_email, recipient_name, email_type, subject, status, error_message)
        )

        result = cursor.fetchone()
        log_id = result[0] if result else None
        conn.commit()

        return log_id

    except Exception as e:
        raise DatabaseError(f"Error logging email: {str(e)}") from e
    finally:
        if conn:
            conn.close()


def get_candidate_emails(candidate_email):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, recipient_email, recipient_name, email_type, subject, status, error_message, sent_at
               FROM email_logs WHERE recipient_email = %s ORDER BY sent_at DESC""",
            (candidate_email,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'id': row[0],
                'recipient_email': row[1],
                'recipient_name': row[2],
                'email_type': row[3],
                'subject': row[4],
                'status': row[5],
                'error_message': row[6],
                'sent_at': row[7]
            }
            for row in rows
        ]

    except Exception as e:
        raise DatabaseError(f"Error retrieving candidate emails: {str(e)}") from e
