"""
User database helpers — authentication and user lookup.
"""

import psycopg2
from functools import lru_cache

from db_config import get_connection


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


def create_user(email, password_hash, role, name):
    conn = None
    try:
        conn = get_connection()
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
        raise DatabaseError(f"Email already exists: {str(e)}") from e
    except Exception as e:
        raise DatabaseError(f"Error creating user: {str(e)}") from e
    finally:
        if conn:
            conn.close()


@lru_cache(maxsize=128)
def get_user_by_email(email):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, email, password_hash, role, name, created_at, updated_at, sector_id
               FROM users WHERE email = %s""",
            (email,)
        )

        row = cursor.fetchone()
        conn.close()

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
        raise DatabaseError(f"Error retrieving user by email: {str(e)}") from e


@lru_cache(maxsize=256)
def get_user_by_id(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT id, email, role, name, created_at, updated_at
               FROM users WHERE id = %s""",
            (user_id,)
        )

        row = cursor.fetchone()
        conn.close()

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
        raise DatabaseError(f"Error retrieving user by ID: {str(e)}") from e
