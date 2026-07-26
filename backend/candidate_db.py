"""
Candidate database helpers — CRUD for candidate records.
"""

import json

import psycopg2

from db_config import db_connection
from user_db import DatabaseError, DuplicateEmailError


def _parse_json_list(raw):
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _serialize_lines(value):
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "\n".join(str(item).strip() for item in value if str(item).strip()) or None
    return str(value)


def _normalize_candidate_email(email):
    if not isinstance(email, str) or not email.strip():
        raise ValueError("Candidate email must be a non-empty string")
    return email.strip().lower()


def _candidate_values(name, email, phone, resume_path, parsed_data, pros, cons, status):
    skills = parsed_data.get('skills', [])
    return (
        name,
        _normalize_candidate_email(email),
        phone,
        resume_path,
        json.dumps(skills),
        parsed_data.get('experience', 0),
        parsed_data.get('education', ''),
        parsed_data.get('match_score', 0),
        parsed_data.get('shortlist_status', 'Potential'),
        _serialize_lines(pros),
        _serialize_lines(cons),
        status,
    )


def get_candidate_by_email(email):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, email, status, created_at
                FROM candidates
                WHERE LOWER(email) = LOWER(%s)
            """, (email,))
            row = cursor.fetchone()

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
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO candidates
                (name, email, phone, resume_path, parsed_skills, years_experience,
                 education, match_score, shortlist_status, pros, cons, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, _candidate_values(
                name, email, phone, resume_path, parsed_data, pros, cons, status
            ))
            result = cursor.fetchone()
            candidate_id = result[0] if result else None
            conn.commit()

        return candidate_id

    except psycopg2.errors.UniqueViolation as e:
        raise DuplicateEmailError("Email already exists") from e
    except psycopg2.IntegrityError as e:
        raise DatabaseError(f"Integrity error: {str(e)}") from e
    except Exception as e:
        raise DatabaseError(f"Error inserting candidate: {str(e)}") from e


def insert_candidate_application(
    name, email, phone, resume_path, parsed_data, job_id,
    ai_reasoning='', pros=None, cons=None, status='applied'
):
    """Create a candidate and their selected-job match in one transaction."""
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            values = _candidate_values(
                name, email, phone, resume_path, parsed_data, pros, cons, status
            )
            cursor.execute("""
                INSERT INTO candidates
                (name, email, phone, resume_path, parsed_skills, years_experience,
                 education, match_score, shortlist_status, pros, cons, status,
                 best_match_job_id, sector_id)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                       %s, j.sector_id
                FROM job_descriptions j
                WHERE j.id = %s
                RETURNING id
            """, (*values, job_id, job_id))
            inserted = cursor.fetchone()
            if not inserted:
                raise DatabaseError("Selected job does not exist")
            candidate_id = inserted[0]
            match_score = parsed_data.get('match_score', 0)
            cursor.execute("""
                INSERT INTO candidate_job_matches
                    (candidate_id, job_id, match_score, ai_reasoning)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (candidate_id, job_id) DO UPDATE
                SET match_score = EXCLUDED.match_score,
                    ai_reasoning = EXCLUDED.ai_reasoning,
                    matched_at = CURRENT_TIMESTAMP
            """, (candidate_id, job_id, match_score, ai_reasoning))
            conn.commit()
            return candidate_id
    except psycopg2.errors.UniqueViolation as e:
        raise DuplicateEmailError("Email already exists") from e
    except DatabaseError:
        raise
    except psycopg2.IntegrityError as e:
        raise DatabaseError(f"Integrity error: {str(e)}") from e
    except Exception as e:
        raise DatabaseError(f"Error inserting candidate application: {str(e)}") from e


def get_candidate_by_id(candidate_id):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, email, phone, resume_path, parsed_skills, years_experience,
                       education, match_score, shortlist_status, created_at, updated_at,
                       pros, cons, status, best_match_job_id, sector_id
                FROM candidates WHERE id = %s
            """, (candidate_id,))
            row = cursor.fetchone()

        if not row:
            return None

        raw_skills = row[5]

        return {
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'resume_path': row[4],
            'skills': _parse_json_list(raw_skills),
            'parsed_skills': raw_skills,
            'years_experience': row[6],
            'education': row[7],
            'match_score': row[8],
            'shortlist_status': row[9],
            'created_at': row[10],
            'updated_at': row[11],
            'pros': _serialize_lines(row[12]),
            'cons': _serialize_lines(row[13]),
            'status': row[14],
            'best_match_job_id': row[15],
            'sector_id': row[16],
        }

    except Exception as e:
        raise DatabaseError(f"Error retrieving candidate: {str(e)}") from e


def get_interviewer_candidates(interviewer_id, sector_id=None):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            sector_clause = " AND c.sector_id = %s" if sector_id is not None else ""
            params = [interviewer_id, interviewer_id]
            if sector_id is not None:
                params.append(sector_id)
            cursor.execute(
                f"""
                SELECT c.id, c.name, c.email, c.phone, c.resume_path,
                       c.parsed_skills, c.years_experience, c.education,
                       c.match_score, c.shortlist_status, c.pros, c.cons,
                       c.status, c.created_at, c.updated_at,
                       assignment.assessment_id, assignment.scheduled_time,
                       assignment.assessment_status
                FROM candidates c
                LEFT JOIN LATERAL (
                    SELECT a.id AS assessment_id, sa.scheduled_time,
                           sa.status AS assessment_status
                    FROM scheduled_assessments sa
                    LEFT JOIN assessments a
                      ON a.scheduled_assessment_id = sa.id
                    WHERE sa.candidate_id = c.id
                      AND sa.interviewer_id = %s
                    ORDER BY sa.created_at DESC, a.created_at DESC NULLS LAST
                    LIMIT 1
                ) assignment ON TRUE
                WHERE (
                    EXISTS (
                        SELECT 1
                        FROM scheduled_assessments own_assignment
                        WHERE own_assignment.candidate_id = c.id
                          AND own_assignment.interviewer_id = %s
                    )
                    OR (
                        c.status IN ('applied', 'pending', 'absence_of_details')
                        AND NOT EXISTS (
                            SELECT 1
                            FROM scheduled_assessments any_assignment
                            WHERE any_assignment.candidate_id = c.id
                        )
                   )
                ){sector_clause}
                ORDER BY c.created_at DESC
                """,
                tuple(params),
            )
            rows = cursor.fetchall()

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
                'skills': _parse_json_list(row[5]),
                'years_experience': row[6],
                'education': row[7],
                'match_score': row[8],
                'shortlist_status': row[9],
                'pros': _parse_pros_cons(row[10]),
                'cons': _parse_pros_cons(row[11]),
                'status': row[12],
                'created_at': row[13],
                'updated_at': row[14],
                'assessment_id': row[15],
                'assessment_date': row[16],
                'assessment_status': row[17],
            }
            for row in rows
        ]

    except Exception as e:
        raise DatabaseError(f"Error retrieving candidates: {str(e)}") from e


def update_candidate_shortlist(candidate_id, status, score):
    try:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE candidates
                SET shortlist_status = %s, match_score = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, score, candidate_id))
            conn.commit()

    except Exception as e:
        raise DatabaseError(f"Error updating candidate shortlist: {str(e)}") from e
