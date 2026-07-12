"""
User database helpers — authentication and user lookup.
"""

import psycopg2

from db_config import db_connection


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class DuplicateEmailError(DatabaseError):
    """Raised when a user email violates the unique constraint."""


def user_auth_version(user):
    """Return the stable JWT revocation version for a user record."""
    updated_at = user.get("updated_at") if user else None
    if updated_at is None:
        return None
    if hasattr(updated_at, "isoformat"):
        return updated_at.isoformat()
    return str(updated_at)


def create_user(email, password_hash, role, name):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO users (email, password_hash, role, name)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (email, password_hash, role, name)
            )
            result = cursor.fetchone()
            user_id = result[0] if result else None
            conn.commit()

        return user_id

    except psycopg2.IntegrityError as e:
        raise DuplicateEmailError("Email already exists") from e
    except DatabaseError:
        raise
    except Exception as e:
        raise DatabaseError("Error creating user") from e


def get_user_by_email(email):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, email, password_hash, role, name, created_at, updated_at, sector_id
                   FROM users WHERE email = %s""",
                (email,)
            )
            row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'email': row[1],
                'password_hash': row[2],
                'role': row[3],
                'name': row[4],
                'created_at': row[5],
                'updated_at': row[6],
                'sector_id': row[7]
            }
        return None

    except Exception as e:
        raise DatabaseError("Error retrieving user by email") from e


def get_user_by_id(user_id):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, email, role, name, created_at, updated_at
                   FROM users WHERE id = %s""",
                (user_id,)
            )
            row = cursor.fetchone()

        if row:
            return {
                'id': row[0],
                'email': row[1],
                'role': row[2],
                'name': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            }
        return None

    except Exception as e:
        raise DatabaseError("Error retrieving user by ID") from e
