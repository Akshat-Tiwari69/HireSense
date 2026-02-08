"""
Database Helper Functions Module
Provides reusable functions for all database operations
"""

import json
from datetime import datetime
from functools import lru_cache

import psycopg2
from db_config import get_connection


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


# ============================================================================
#                            USER FUNCTIONS (AUTHENTICATION)
# ============================================================================

def create_user(email, password_hash, role, name):
    """
    Create a new user in the database.
    
    Args:
        email (str): User's email address (unique)
        password_hash (str): Hashed password
        role (str): User role - "interviewer" or "admin"
        name (str): User's full name
    
    Returns:
        int: User ID of the newly created user
    
    Raises:
        DatabaseError: If creation fails
    """
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
        conn.close()
        
        return user_id
    
    except psycopg2.IntegrityError as e:
        raise DatabaseError(f"Email already exists: {str(e)}") from e
    except Exception as e:
        raise DatabaseError(f"Error creating user: {str(e)}") from e


@lru_cache(maxsize=128)
def get_user_by_email(email):
    """
    Retrieve user by email address. Results are cached for performance.
    
    Args:
        email (str): User's email address
    
    Returns:
        dict: User data with keys (id, email, password_hash, role, name, created_at, updated_at)
              or None if user not found
    
    Raises:
        DatabaseError: If query fails
    """
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
    """
    Retrieve user by user ID. Results are cached for performance.
    
    Args:
        user_id (int): User's ID
    
    Returns:
        dict: User data with keys (id, email, role, name, created_at, updated_at)
              or None if user not found (password_hash excluded for security)
    
    Raises:
        DatabaseError: If query fails
    """
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


# ============================================================================
#                            CANDIDATE FUNCTIONS
# ============================================================================

def get_candidate_by_email(email):
    """
    Check if a candidate exists with the given email.
    
    Args:
        email (str): Candidate's email address
    
    Returns:
        dict: Candidate information if found, None otherwise
    
    Raises:
        DatabaseError: If query fails
    """
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
    """
    Insert a new candidate into the database.
    
    Args:
        name (str): Candidate's full name
        email (str): Candidate's email address
        phone (str): Candidate's phone number
        resume_path (str): Path to the uploaded resume file
        parsed_data (dict): Parsed resume data with skills, experience, education, match_score
        status (str, optional): Candidate status - 'pending', 'shortlisted', 'rejected', 'assessment_scheduled', 'assessment_completed'
    
    Returns:
        int: Candidate ID of the newly inserted candidate
    
    Raises:
        DatabaseError: If insertion fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Extract parsed data
        skills = parsed_data.get('skills', [])
        experience = parsed_data.get('experience', 0)
        education = parsed_data.get('education', '')
        match_score = parsed_data.get('match_score', 0)
        shortlist_status = parsed_data.get('shortlist_status', 'Potential')
        
        # Converting lists to JSON strings
        skills_json = json.dumps(skills)
        pros_json = json.dumps(pros) if pros else None
        cons_json = json.dumps(cons) if cons else None
        
        cursor.execute("""
            INSERT INTO candidates 
            (name, email, phone, resume_path, parsed_skills, years_experience, education, match_score, shortlist_status, pros, cons, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (name, email, phone, resume_path, skills_json, experience, education, match_score, shortlist_status, pros_json, cons_json, status))
        
        result = cursor.fetchone()
        candidate_id = result[0] if result else None
        conn.commit()
        conn.close()
        
        return candidate_id
        
    except psycopg2.IntegrityError as e:
        raise DatabaseError(f"Integrity error: {str(e)}") from e
    except Exception as e:
        raise DatabaseError(f"Error inserting candidate: {str(e)}") from e


def get_candidate_by_id(candidate_id):
    """
    Retrieve a candidate by their ID.
    
    Args:
        candidate_id (int): The ID of the candidate
    
    Returns:
        dict: Candidate information including parsed skills as list
    
    Raises:
        DatabaseError: If retrieval fails
    """
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
        
        # Convert to dictionary and parse JSON skills
        raw_skills = row[5]  # parsed_skills column (JSON string or None)
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
            'parsed_skills': raw_skills,  # Raw DB value for schedule-time parsing
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
    """
    Retrieve all candidates from the database.
    
    Returns:
        list: List of all candidates as dictionaries
    
    Raises:
        DatabaseError: If retrieval fails
    """
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
        
        # Use list comprehension for better performance
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
                'pros': json.loads(row[10]) if row[10] else [],
                'cons': json.loads(row[11]) if row[11] else [],
                'status': row[12],
                'created_at': row[13],
                'updated_at': row[14]
            }
            for row in rows
        ]
        
    except Exception as e:
        raise DatabaseError(f"Error retrieving candidates: {str(e)}") from e


def update_candidate_shortlist(candidate_id, status, score):
    """
    Update candidate's shortlist status and match score.
    
    Args:
        candidate_id (int): The ID of the candidate
        status (str): Shortlist status ("High Match", "Potential", "Reject")
        score (int): Match score (0-100)
    
    Raises:
        DatabaseError: If update fails
    """
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
    """
    
    Args:
        candidate_id (int): The ID of the candidate
        status (str): Candidate status - 'pending', 'shortlisted', 'rejected', 'assessment_scheduled', 'assessment_completed'
    
    Returns:
        bool: True if update successful, False if candidate not found
    
    Raises:
        DatabaseError: If update fails
    """
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


# ============================================================================
#                           ASSESSMENT FUNCTIONS
# ============================================================================

def create_assessment(candidate_id, job_id=None):
    """
    Create a new assessment for a candidate.
    
    Args:
        candidate_id (int): The ID of the candidate
        job_id (int, optional): The ID of the job posting
    
    Returns:
        int: Assessment ID of the newly created assessment
    
    Raises:
        DatabaseError: If creation fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO assessments (candidate_id, job_id, status, started_at)
            VALUES (%s, %s, 'in_progress', CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (candidate_id, job_id)
        )
        assessment_id = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        return assessment_id
        
    except Exception as e:
        raise DatabaseError(f"Error creating assessment: {str(e)}") from e


def update_assessment_scores(assessment_id, technical_score, psychometric_score, decision, rationale, scheduled_assessment_id=None, hiring_recommendation=None):
    """
    Update assessment scores, decision, and hiring recommendation.
    
    Args:
        assessment_id (int): The ID of the assessment
        technical_score (float): Technical score (0-100)
        psychometric_score (float): Psychometric score (0-100)
        decision (str): Hiring decision ("Hire", "No-Hire", "Maybe")
        scheduled_assessment_id (int, optional): Link to scheduled assessment
    
    Raises:
        DatabaseError: If update fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Calculate overall score as weighted average
        overall_score = (technical_score * 0.6) + (psychometric_score * 0.4)
        
        # PostgreSQL: explicit CAST for numeric types
        cursor.execute("""
            UPDATE assessments 
            SET technical_score = CAST(%s AS NUMERIC), psychometric_score = CAST(%s AS NUMERIC), 
                overall_score = CAST(%s AS NUMERIC), 
                decision = %s, rationale = %s, status = 'completed', 
                completed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (technical_score, psychometric_score, overall_score, decision, rationale, assessment_id))
        
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        
        if rows_affected == 0:
            raise DatabaseError(f"No assessment found with id {assessment_id}")
        
    except Exception as e:
        raise DatabaseError(f"Error updating assessment scores: {str(e)}") from e


def get_assessment_by_id(assessment_id):
    """
    Retrieve an assessment by ID.
    
    Args:
        assessment_id (int): The ID of the assessment
    
    Returns:
        dict: Assessment details
    
    Raises:
        DatabaseError: If retrieval fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, candidate_id, job_id, technical_score, psychometric_score, 
                   overall_score, decision, rationale, proctoring_violations, status, 
                   started_at, completed_at
            FROM assessments WHERE id = %s
        """, (assessment_id,))
        
        row = cursor.fetchone()
        conn.close()
        
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
            'completed_at': row[11]
        }
        
    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment: {str(e)}") from e


# ============================================================================
#                       RESPONSE TRACKING FUNCTIONS
# ============================================================================

def save_mcq_response(assessment_id, question_id, selected_answer, is_correct, time_spent):
    """
    Save an MCQ response (upsert - update if exists, insert if not).
    
    Args:
        assessment_id (int): The ID of the assessment
        question_id (int): The question number/ID
        selected_answer (str): Selected answer (A, B, C, D)
        is_correct (bool): Whether the answer is correct
        time_spent (int): Time spent on this question in seconds
    
    Raises:
        DatabaseError: If save fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First, try to update existing response
        cursor.execute(
            """
            UPDATE mcq_responses 
            SET selected_answer = %s, is_correct = %s, time_spent = %s
            WHERE assessment_id = %s AND question_id = %s
            """,
            (selected_answer, is_correct, time_spent, assessment_id, question_id)
        )
        
        # If no row was updated, insert new one
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO mcq_responses 
                (assessment_id, question_id, selected_answer, is_correct, time_spent)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (assessment_id, question_id, selected_answer, is_correct, time_spent)
            )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving MCQ response: {str(e)}") from e


def get_saved_mcq_answers(assessment_id):
    """
    Get all saved MCQ answers for an assessment.
    Gets the most recent answer for each question.
    
    Args:
        assessment_id (int): The ID of the assessment
    
    Returns:
        dict: Dictionary mapping question_id to selected_answer
    
    Raises:
        DatabaseError: If retrieval fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Use DISTINCT ON to get only the latest answer per question (by id)
        cursor.execute(
            """
            SELECT DISTINCT ON (question_id) question_id, selected_answer
            FROM mcq_responses 
            WHERE assessment_id = %s
            ORDER BY question_id, id DESC
            """,
            (assessment_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        # Return as dict: {question_id: selected_answer}
        return {row[0]: row[1] for row in rows}
        
    except Exception as e:
        raise DatabaseError(f"Error getting saved MCQ answers: {str(e)}") from e


def get_saved_psychometric_answers(assessment_id):
    """
    Get all saved psychometric answers for an assessment.
    Gets the most recent answer for each question.
    
    Args:
        assessment_id (int): The ID of the assessment
    
    Returns:
        dict: Dictionary mapping question_id to selected option index (from scenario_response)
    
    Raises:
        DatabaseError: If retrieval fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Use DISTINCT ON to get only the latest answer per question (by id)
        cursor.execute(
            """
            SELECT DISTINCT ON (question_id) question_id, score, scenario_response
            FROM psychometric_responses 
            WHERE assessment_id = %s
            ORDER BY question_id, id DESC
            """,
            (assessment_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        # Return as dict: {question_id: selected_option_index}
        # scenario_response stores the selected option index as a string
        result = {}
        for row in rows:
            q_id = row[0]
            scenario_response = row[2]
            if scenario_response is not None and scenario_response.isdigit():
                result[q_id] = int(scenario_response)
            else:
                # Fallback: use score to estimate index (legacy data)
                result[q_id] = max(0, int(row[1]) - 1) if row[1] else 0
        return result
        
    except Exception as e:
        raise DatabaseError(f"Error getting saved psychometric answers: {str(e)}") from e


def get_saved_coding_submission(assessment_id):
    """
    Get the saved coding submission for an assessment.
    
    Args:
        assessment_id (int): The ID of the assessment
    
    Returns:
        dict: Dictionary with code, language, and test results or None if no submission
    
    Raises:
        DatabaseError: If retrieval fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT problem_id, language, code, test_cases_passed, total_test_cases
            FROM coding_submissions 
            WHERE assessment_id = %s
            ORDER BY submitted_at DESC
            LIMIT 1
            """,
            (assessment_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
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


def save_coding_submission(assessment_id, problem_id, language, code, test_cases_passed, total_test_cases):
    """
    Save a coding submission (upsert - update if exists, insert if not).
    
    Args:
        assessment_id (int): The ID of the assessment
        problem_id (int): The problem ID
        language (str): Programming language (Python, JavaScript, Java)
        code (str): Submitted code
        test_cases_passed (int): Number of test cases passed
        total_test_cases (int): Total number of test cases
    
    Raises:
        DatabaseError: If save fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First, try to update existing submission
        cursor.execute(
            """
            UPDATE coding_submissions 
            SET language = %s, code = %s, test_cases_passed = %s, total_test_cases = %s, submitted_at = CURRENT_TIMESTAMP
            WHERE assessment_id = %s AND problem_id = %s
            """,
            (language, code, test_cases_passed, total_test_cases, assessment_id, problem_id)
        )
        
        # If no row was updated, insert new one
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO coding_submissions 
                (assessment_id, problem_id, language, code, test_cases_passed, total_test_cases)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (assessment_id, problem_id, language, code, test_cases_passed, total_test_cases)
            )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving coding submission: {str(e)}") from e


def log_proctoring_event(assessment_id, event_type, severity, details):
    """
    Log a proctoring event.
    
    Args:
        assessment_id (int): The ID of the assessment
        event_type (str): Type of event (multiple_faces, no_face, tab_switch, copy_paste, keyboard_shortcut)
        severity (str): Severity level (low, medium, high)
        details (str): Additional event details
    
    Raises:
        DatabaseError: If logging fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO proctoring_events 
            (assessment_id, event_type, severity, details)
            VALUES (%s, %s, %s, %s)
        """, (assessment_id, event_type, severity, details))
        
        # Increment proctoring violations count in assessments table
        cursor.execute("""
            UPDATE assessments 
            SET proctoring_violations = proctoring_violations + 1
            WHERE id = %s
        """, (assessment_id,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error logging proctoring event: {str(e)}") from e


def save_psychometric_response(assessment_id, question_id, trait, score, scenario_response=None):
    """
    Save a psychometric response (upsert - update if exists, insert if not).
    
    Args:
        assessment_id (int): The ID of the assessment
        question_id (int): The question ID
        trait (str): Trait being measured (leadership, resilience, teamwork, etc.)
        score (int): Score on scale of 1-10
        scenario_response (str, optional): Text response to scenario
    
    Raises:
        DatabaseError: If save fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # First, try to update existing response
        cursor.execute(
            """
            UPDATE psychometric_responses 
            SET trait = %s, score = %s, scenario_response = %s
            WHERE assessment_id = %s AND question_id = %s
            """,
            (trait, score, scenario_response, assessment_id, question_id)
        )
        
        # If no row was updated, insert new one
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO psychometric_responses 
                (assessment_id, question_id, trait, score, scenario_response)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (assessment_id, question_id, trait, score, scenario_response)
            )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving psychometric response: {str(e)}") from e


# ============================================================================
#                      SCORE CALCULATION FUNCTIONS
# ============================================================================

def get_mcq_score(assessment_id):
    """
    Calculate MCQ score for an assessment.
    
    Returns:
        float: Percentage score (0-100)
    
    Raises:
        DatabaseError: If calculation fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # PostgreSQL: explicit cast for boolean
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_correct = TRUE THEN 1 ELSE 0 END) as correct
            FROM mcq_responses WHERE assessment_id = %s
        """, (assessment_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        total = result[0]
        correct = result[1] or 0
        
        return 0.0 if total == 0 else round((correct / total) * 100, 2)
        
    except Exception as e:
        raise DatabaseError(f"Error calculating MCQ score: {str(e)}") from e


def get_coding_score(assessment_id):
    """
    Calculate coding score for an assessment.
    
    Returns:
        float: Percentage score (0-100)
    
    Raises:
        DatabaseError: If calculation fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(test_cases_passed) as total_passed, SUM(total_test_cases) as total_tests
            FROM coding_submissions WHERE assessment_id = %s
        """, (assessment_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        total_passed = result[0] or 0
        total_tests = result[1] or 0
        
        return 0.0 if total_tests == 0 else round((total_passed / total_tests) * 100, 2)
        
    except Exception as e:
        raise DatabaseError(f"Error calculating coding score: {str(e)}") from e


def get_psychometric_scores(assessment_id):
    """
    Calculate psychometric trait scores for an assessment.
    
    Returns:
        dict: Dictionary of traits and their average scores
    
    Raises:
        DatabaseError: If calculation fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trait, AVG(score) as avg_score
            FROM psychometric_responses WHERE assessment_id = %s
            GROUP BY trait
        """, (assessment_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: round(row[1], 2) for row in rows}
        
    except Exception as e:
        raise DatabaseError(f"Error calculating psychometric scores: {str(e)}") from e


# ============================================================================
#                    ASSESSMENT SCHEDULING FUNCTIONS
# ============================================================================

def create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time, is_technical_role=True, questions_data=None):
    """
    Create a new scheduled assessment session.
    
    Args:
        candidate_id (int): ID of the candidate
        interviewer_id (int): ID of the interviewer (user)
        scheduled_time (str): ISO format datetime string (e.g., '2026-01-25T10:30:00')
        is_technical_role (bool): Whether this is a technical role requiring coding questions
        questions_data (dict): Pre-generated questions to store
    
    Returns:
        int: Scheduled assessment ID
    
    Raises:
        DatabaseError: If creation fails
    """
    print(f"[DB] create_scheduled_assessment called: candidate={candidate_id}, interviewer={interviewer_id}, time={scheduled_time}, technical={is_technical_role}", flush=True)
    try:
        import json
        conn = get_connection()
        cursor = conn.cursor()
        print("[DB] Executing INSERT with PostgreSQL...", flush=True)
        
        # PostgreSQL INSERT with is_technical_role and questions_data
        cursor.execute(
            """INSERT INTO scheduled_assessments (candidate_id, interviewer_id, scheduled_time, status, is_technical_role, questions_data)
               VALUES (%s, %s, %s, 'scheduled', %s, %s) RETURNING id""",
            (candidate_id, interviewer_id, scheduled_time, is_technical_role, json.dumps(questions_data) if questions_data else None)
        )
        
        result = cursor.fetchone()
        scheduled_id = result[0] if result else None
        print(f"[DB] INSERT done, scheduled_id={scheduled_id}", flush=True)
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Returning scheduled_id={scheduled_id}", flush=True)
        return scheduled_id
    
    except Exception as e:
        print(f"[DB] ERROR in create_scheduled_assessment: {e}", flush=True)
        raise DatabaseError(f"Error creating scheduled assessment: {str(e)}")


def get_scheduled_assessment(candidate_id):
    """
    Retrieve scheduled assessment for a candidate.
    
    Args:
        candidate_id (int): ID of the candidate
    
    Returns:
        dict: Scheduled assessment data with keys (id, candidate_id, interviewer_id, scheduled_time, status, assessment_id, is_technical_role, questions_data, created_at, updated_at)
              or None if not found
    
    Raises:
        DatabaseError: If query fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, candidate_id, interviewer_id, scheduled_time, status, assessment_id, 
                      is_technical_role, questions_data, created_at, updated_at
               FROM scheduled_assessments WHERE candidate_id = %s""",
            (candidate_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Format scheduled_time as ISO string (stored as local time)
            scheduled_time_raw = row[3]
            if isinstance(scheduled_time_raw, str):
                scheduled_time = scheduled_time_raw.replace(' ', 'T')
            else:
                # datetime object from database
                scheduled_time = scheduled_time_raw.strftime('%Y-%m-%dT%H:%M:%S') if scheduled_time_raw else None
            
            # Parse questions_data if present
            questions_data = row[7]
            if isinstance(questions_data, str):
                import json
                try:
                    questions_data = json.loads(questions_data)
                except Exception:
                    questions_data = None
            
            return {
                'id': row[0],
                'candidate_id': row[1],
                'interviewer_id': row[2],
                'scheduled_time': scheduled_time,
                'status': row[4],
                'assessment_id': row[5],
                'is_technical_role': row[6] if row[6] is not None else True,
                'questions_data': questions_data,
                'created_at': row[8],
                'updated_at': row[9]
            }
        return None
    
    except Exception as e:
        raise DatabaseError(f"Error retrieving scheduled assessment: {str(e)}") from e


def update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id=None):
    """
    Update the status of a scheduled assessment.
    
    Args:
        scheduled_assessment_id (int): ID of the scheduled assessment
        status (str): New status - 'scheduled', 'in_progress', 'completed', 'cancelled'
        assessment_id (int, optional): Assessment ID to link when marking as in_progress
    
    Returns:
        bool: True if update successful, False if assessment not found
    
    Raises:
        DatabaseError: If update fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if assessment_id:
            cursor.execute(
                """UPDATE scheduled_assessments 
                   SET status = %s, assessment_id = %s, updated_at = CURRENT_TIMESTAMP
                   WHERE id = %s""",
                (status, assessment_id, scheduled_assessment_id)
            )
        else:
            cursor.execute(
                """UPDATE scheduled_assessments 
                   SET status = %s, updated_at = CURRENT_TIMESTAMP
                   WHERE id = %s""",
                (status, scheduled_assessment_id)
            )
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success
    
    except Exception as e:
        raise DatabaseError(f"Error updating scheduled assessment status: {str(e)}") from e


def check_assessment_time_valid(candidate_id, current_time):
    """
    Check if current time is within ±30 minutes of scheduled assessment time.
    
    Args:
        candidate_id (int): ID of the candidate
        current_time (str): ISO format datetime string (e.g., '2026-01-25T10:30:00')
    
    Returns:
        dict: {'valid': bool, 'scheduled_assessment_id': int or None, 'message': str}
              If valid: {'valid': True, 'scheduled_assessment_id': id, 'message': 'Assessment can proceed'}
              If invalid: {'valid': False, 'scheduled_assessment_id': None, 'message': 'error reason'}
    
    Raises:
        DatabaseError: If query fails
    """
    try:
        from datetime import datetime, timedelta
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, scheduled_time, status 
               FROM scheduled_assessments WHERE candidate_id = %s AND status = 'scheduled'""",
            (candidate_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {
                'valid': False,
                'scheduled_assessment_id': None,
                'message': 'No scheduled assessment found for this candidate'
            }
        
        scheduled_id, scheduled_time_str, status = row
        
        # Parse times
        current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
        scheduled_dt = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
        
        # Check if within ±30 minutes
        time_diff = abs((current_dt - scheduled_dt).total_seconds() / 60)
        
        if time_diff <= 30:
            return {
                'valid': True,
                'scheduled_assessment_id': scheduled_id,
                'message': 'Assessment can proceed'
            }
        
        minutes_until = int((scheduled_dt - current_dt).total_seconds() / 60)
        return (
            {
                'valid': False,
                'scheduled_assessment_id': None,
                'message': f'Assessment starts in {minutes_until} minutes. Come back at scheduled time.'
            } if minutes_until > 0 else {
                'valid': False,
                'scheduled_assessment_id': None,
                'message': 'Assessment time has passed. Please contact the interviewer.'
            }
        )
    
    except Exception as e:
        raise DatabaseError(f"Error checking assessment time validity: {str(e)}") from e


# ============================================================================
#                          EMAIL LOGGING FUNCTIONS
# ============================================================================

def log_email(recipient_email, recipient_name, email_type, subject, status='sent', error_message=None):
    """
    Log an email sent to a candidate.
    
    Args:
        recipient_email (str): Email address of recipient
        recipient_name (str): Name of recipient
        email_type (str): Type of email - 'rejection', 'assessment_invitation', 'final_decision', etc.
        subject (str): Email subject line
        status (str, optional): Email status - 'sent', 'failed', 'bounced' (defaults to 'sent')
        error_message (str, optional): Error message if status is 'failed'
    
    Returns:
        int: Email log entry ID
    
    Raises:
        DatabaseError: If logging fails
    """
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
        conn.close()
        
        return log_id
    
    except Exception as e:
        raise DatabaseError(f"Error logging email: {str(e)}") from e


def get_candidate_emails(candidate_email):
    """
    Retrieve all emails sent to a candidate.
    
    Args:
        candidate_email (str): Email address of the candidate
    
    Returns:
        list: List of email logs as dictionaries with keys (id, recipient_email, recipient_name, email_type, subject, status, error_message, sent_at)
              Empty list if no emails found
    
    Raises:
        DatabaseError: If query fails
    """
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


def get_assessment_by_candidate_id(candidate_id):
    """
    Retrieve the most recent assessment for a candidate.
    
    Args:
        candidate_id (int): The ID of the candidate
    
    Returns:
        dict: Assessment details (most recent), or None if no assessment exists
    
    Raises:
        DatabaseError: If retrieval fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.candidate_id, a.job_id, a.technical_score, a.psychometric_score, 
                   a.overall_score, a.decision, a.rationale, a.proctoring_violations, a.status, 
                   a.started_at, a.completed_at,
                   COALESCE(m.score, 0) as mcq_score,
                   COALESCE(c.score, 0) as coding_score
            FROM assessments a
            LEFT JOIN (
                SELECT assessment_id, ROUND(COUNT(CASE WHEN is_correct = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as score
                FROM mcq_responses GROUP BY assessment_id
            ) m ON a.id = m.assessment_id
            LEFT JOIN (
                SELECT assessment_id, ROUND(test_cases_passed * 100.0 / test_cases_total, 2) as score
                FROM coding_submissions GROUP BY assessment_id
            ) c ON a.id = c.assessment_id
            WHERE a.candidate_id = %s
            ORDER BY a.created_at DESC
            LIMIT 1
        """, (candidate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
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
            'coding_score': row[13]
        }
    
    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment for candidate {candidate_id}: {str(e)}") from e


# NOTE: create_scheduled_assessment is defined earlier in this file (line ~761)
# Do not duplicate it here


def update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id=None):
    """
    Update the status of a scheduled assessment.
    
    Args:
        scheduled_assessment_id (int): The ID of the scheduled assessment
        status (str): New status (e.g., 'in_progress', 'completed', 'cancelled')
        assessment_id (int): Optional assessment ID to link
    
    Returns:
        bool: True if successful
    
    Raises:
        DatabaseError: If update fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if assessment_id:
            cursor.execute("""
                UPDATE scheduled_assessments 
                SET status = %s, assessment_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, assessment_id, scheduled_assessment_id))
        else:
            cursor.execute("""
                UPDATE scheduled_assessments 
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (status, scheduled_assessment_id))
        
        conn.commit()
        conn.close()
        
        return True
    
    except Exception as e:
        raise DatabaseError(f"Error updating scheduled assessment: {str(e)}") from e


def check_assessment_time_valid(candidate_id, current_time, window_minutes=30):
    """
    Check if current time is within valid assessment window (±30 minutes from scheduled time).
    
    Args:
        candidate_id (int): The ID of the candidate
        current_time (str): Current time in ISO format
        window_minutes (int): Allowed window in minutes (default 30)
    
    Returns:
        tuple: (is_valid, scheduled_time, message)
    
    Raises:
        DatabaseError: If check fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT scheduled_time FROM scheduled_assessments 
            WHERE candidate_id = %s AND status = 'scheduled'
            ORDER BY created_at DESC LIMIT 1
        """, (candidate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return (False, None, "No scheduled assessment found")
        
        scheduled_time_raw = row[0]
        
        # Format scheduled_time as ISO string (stored as local time, no Z suffix)
        if isinstance(scheduled_time_raw, str):
            scheduled_time = scheduled_time_raw.replace(' ', 'T')
        else:
            # datetime object from database
            scheduled_time = scheduled_time_raw.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Parse times and check window - compare as naive datetimes (local time)
        from datetime import datetime, timedelta
        scheduled_dt = datetime.fromisoformat(scheduled_time.replace('Z', ''))
        current_dt = datetime.now()  # Use local time for comparison
        
        time_diff = abs((current_dt - scheduled_dt).total_seconds() / 60)
        
        if time_diff <= window_minutes:
            return (True, scheduled_time, f"Assessment is within {window_minutes} minute window")
        else:
            return (False, scheduled_time, f"Assessment is {int(time_diff)} minutes away from scheduled time")
    
    except Exception as e:
        raise DatabaseError(f"Error checking assessment time: {str(e)}") from e


# ============================================================================
#                    TOKEN-BASED ASSESSMENT ACCESS
# ============================================================================

def generate_assessment_token():
    """Generate a secure random token for assessment access."""
    import secrets
    return secrets.token_urlsafe(32)


def set_assessment_token(scheduled_assessment_id, token):
    """
    Set the access token for a scheduled assessment.
    
    Args:
        scheduled_assessment_id (int): ID of the scheduled assessment
        token (str): Access token for the assessment
    
    Returns:
        bool: True if successful
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE scheduled_assessments 
               SET access_token = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s""",
            (token, scheduled_assessment_id)
        )
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success
    
    except Exception as e:
        raise DatabaseError(f"Error setting assessment token: {str(e)}") from e


def get_assessment_by_token(token):
    """
    Retrieve scheduled assessment by access token.
    
    Args:
        token (str): Access token
    
    Returns:
        dict: Assessment data with candidate info, or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT sa.id, sa.candidate_id, sa.interviewer_id, sa.scheduled_time, 
                      sa.status, sa.assessment_id, sa.started_at,
                      c.name as candidate_name, c.email as candidate_email
               FROM scheduled_assessments sa
               JOIN candidates c ON sa.candidate_id = c.id
               WHERE sa.access_token = %s""",
            (token,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'candidate_id': row[1],
                'interviewer_id': row[2],
                'scheduled_time': row[3],
                'status': row[4],
                'assessment_id': row[5],
                'started_at': row[6],
                'proctoring_enabled': True,  # Default to True
                'candidate_name': row[7],
                'candidate_email': row[8]
            }
        return None
    
    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment by token: {str(e)}") from e


def start_assessment_by_token(token):
    """
    Mark assessment as started and record the start time.
    
    Args:
        token (str): Access token
    
    Returns:
        bool: True if successful
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE scheduled_assessments 
               SET status = 'in_progress', started_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
               WHERE access_token = %s AND status = 'scheduled'""",
            (token,)
        )
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        return success
    
    except Exception as e:
        raise DatabaseError(f"Error starting assessment: {str(e)}") from e


# ============================================================================
#                    PROCTORING VIOLATIONS
# ============================================================================

def record_proctoring_violation(assessment_id, violation_type, description, severity='medium', screenshot_url=None):
    """
    Record a proctoring violation during an assessment.
    
    Args:
        assessment_id (int): ID of the assessment
        violation_type (str): Type of violation (no_face, multiple_faces, tab_switch, etc.)
        description (str): Description of the violation
        severity (str): Severity level (low, medium, high, critical)
        screenshot_url (str, optional): URL to screenshot evidence
    
    Returns:
        int: Violation ID
    """
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
    """
    Get all proctoring violations for an assessment.
    
    Args:
        assessment_id (int): ID of the assessment
    
    Returns:
        list: List of violation records
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, assessment_id, violation_type, description, severity, 
                      screenshot_url, timestamp, resolved
               FROM proctoring_violations 
               WHERE assessment_id = %s
               ORDER BY timestamp DESC""",
            (assessment_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'assessment_id': row[1],
                'violation_type': row[2],
                'description': row[3],
                'severity': row[4],
                'screenshot_url': row[5],
                'timestamp': row[6],
                'resolved': row[7]
            }
            for row in rows
        ]
    
    except Exception as e:
        raise DatabaseError(f"Error retrieving violations: {str(e)}") from e


def count_violations_for_assessment(assessment_id):
    """
    Count proctoring violations for an assessment.
    
    Args:
        assessment_id (int): ID of the assessment
    
    Returns:
        int: Number of violations
    """
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


def save_assessment_questions(assessment_id, questions_data):
    """
    Save generated questions to the assessment record.
    
    Args:
        assessment_id: The assessment ID
        questions_data: Dict containing mcq_questions, coding_problem, psychometric_scenarios
    """
    try:
        import json
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE assessments 
               SET questions_data = %s
               WHERE id = %s""",
            (json.dumps(questions_data), assessment_id)
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving assessment questions: {str(e)}") from e


def get_assessment_questions(assessment_id):
    """
    Retrieve stored questions for an assessment.
    
    Args:
        assessment_id: The assessment ID
        
    Returns:
        dict: Questions data or None if not found
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT questions_data FROM assessments WHERE id = %s""",
            (assessment_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row and row[0] else None
    
    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment questions: {str(e)}") from e


def update_assessment_time_elapsed(assessment_id, time_elapsed_seconds):
    """
    Update the elapsed time for an assessment (for resume functionality).
    
    Args:
        assessment_id: The assessment ID
        time_elapsed_seconds: Total seconds elapsed
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """UPDATE assessments 
               SET time_elapsed_seconds = %s
               WHERE id = %s""",
            (time_elapsed_seconds, assessment_id)
        )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error updating assessment time: {str(e)}") from e


def get_assessment_time_elapsed(assessment_id):
    """
    Get the elapsed time for an assessment by calculating from started_at.
    
    Args:
        assessment_id: The assessment ID
        
    Returns:
        int: Seconds elapsed since assessment started, or 0 if not started
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Calculate elapsed time from started_at timestamp
        cursor.execute(
            """
            SELECT 
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER as elapsed_seconds,
                started_at
            FROM assessments 
            WHERE id = %s AND started_at IS NOT NULL
            """,
            (assessment_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        return max(0, row[0]) if row and row[0] is not None else 0
    
    except Exception as e:
        raise DatabaseError(f"Error getting assessment time: {str(e)}") from e


if __name__ == "__main__":
    print("Database Helper Functions Module")
    print("Import this module to use database functions")
