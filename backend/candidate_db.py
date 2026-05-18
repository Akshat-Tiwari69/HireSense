"""
Candidate database helpers — CRUD for candidate records.
"""

import json

import psycopg2

from db_config import get_connection
from user_db import DatabaseError


def get_candidate_by_email(email):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email, status, created_at
            FROM candidates
            WHERE LOWER(email) = LOWER(%s)
        """, (email,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'status': row[3],
                'created_at': row[4]
            }
        return None

    except Exception as e:
        raise DatabaseError(f"Error checking candidate email: {str(e)}") from e


def insert_candidate(name, email, phone, resume_path, parsed_data, pros=None, cons=None, status='pending'):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        skills = parsed_data.get('skills', [])
        experience = parsed_data.get('experience', 0)
        education = parsed_data.get('education', '')
        match_score = parsed_data.get('match_score', 0)
        shortlist_status = parsed_data.get('shortlist_status', 'Potential')

        skills_json = json.dumps(skills)
        # pros/cons are plain newline-separated strings — store as-is, not JSON-encoded
        pros_text = pros if pros else None
        cons_text = cons if cons else None

        cursor.execute("""
            INSERT INTO candidates
            (name, email, phone, resume_path, parsed_skills, years_experience, education, match_score, shortlist_status, pros, cons, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (name, email, phone, resume_path, skills_json, experience, education, match_score, shortlist_status, pros_text, cons_text, status))

        result = cursor.fetchone()
        candidate_id = result[0] if result else None
        conn.commit()

        return candidate_id

    except psycopg2.IntegrityError as e:
        raise DatabaseError(f"Integrity error: {str(e)}") from e
    except Exception as e:
        raise DatabaseError(f"Error inserting candidate: {str(e)}") from e
    finally:
        if conn:
            conn.close()


def get_candidate_by_id(candidate_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email, phone, resume_path, parsed_skills, years_experience,
                   education, match_score, shortlist_status, created_at, updated_at
            FROM candidates WHERE id = %s
        """, (candidate_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        raw_skills = row[5]
        skills_list = []
        if raw_skills:
            try:
                skills_list = json.loads(raw_skills) if isinstance(raw_skills, str) else raw_skills
            except (json.JSONDecodeError, TypeError):
                skills_list = []

        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'resume_path': row[4],
            'skills': skills_list,
            'parsed_skills': raw_skills,
            'years_experience': row[6],
            'education': row[7],
            'match_score': row[8],
            'shortlist_status': row[9],
            'created_at': row[10],
            'updated_at': row[11]
        }

    except Exception as e:
        raise DatabaseError(f"Error retrieving candidate: {str(e)}") from e


def get_all_candidates():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email, phone, resume_path, parsed_skills, years_experience,
                   education, match_score, shortlist_status, pros, cons, status, created_at, updated_at
            FROM candidates ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        def _parse_pros_cons(raw):
            """Handle pros/cons as plain newline-text (new) or legacy JSON-encoded string."""
            if not raw:
                return []
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, str):
                    return [p.strip() for p in parsed.split('\n') if p.strip()]
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            return [p.strip() for p in raw.split('\n') if p.strip()]

        return [
            {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'resume_path': row[4],
                'skills': json.loads(row[5]) if row[5] else [],
                'years_experience': row[6],
                'education': row[7],
                'match_score': row[8],
                'shortlist_status': row[9],
                'pros': _parse_pros_cons(row[10]),
                'cons': _parse_pros_cons(row[11]),
                'status': row[12],
                'created_at': row[13],
                'updated_at': row[14]
            }
            for row in rows
        ]

    except Exception as e:
        raise DatabaseError(f"Error retrieving candidates: {str(e)}") from e


def update_candidate_shortlist(candidate_id, status, score):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE candidates
            SET shortlist_status = %s, match_score = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (status, score, candidate_id))

        conn.commit()
        conn.close()

    except Exception as e:
        raise DatabaseError(f"Error updating candidate shortlist: {str(e)}") from e


def update_candidate_status(candidate_id, status, pros=None, cons=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        pros_json = json.dumps(pros) if pros else None
        cons_json = json.dumps(cons) if cons else None

        if pros_json or cons_json:
            cursor.execute("""
                UPDATE candidates
                SET status = %s, pros = COALESCE(%s, pros), cons = COALESCE(%s, cons), updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, pros_json, cons_json, candidate_id))
        else:
            cursor.execute("""
                UPDATE candidates
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, candidate_id))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()

        return success

    except Exception as e:
        raise DatabaseError(f"Error updating candidate status: {str(e)}") from e
