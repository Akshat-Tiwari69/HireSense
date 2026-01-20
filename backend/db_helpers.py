"""
Database Helper Functions Module
Provides reusable functions for all database operations
"""

import json
import sqlite3
from datetime import datetime
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
               VALUES (?, ?, ?, ?)""",
            (email, password_hash, role, name)
        )
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return user_id
    
    except sqlite3.IntegrityError as e:
        raise DatabaseError(f"Email already exists: {str(e)}")
    except Exception as e:
        raise DatabaseError(f"Error creating user: {str(e)}")


def get_user_by_email(email):
    """
    Retrieve user by email address.
    
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
            """SELECT id, email, password_hash, role, name, created_at, updated_at
               FROM users WHERE email = ?""",
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
                'updated_at': row[6]
            }
        return None
    
    except Exception as e:
        raise DatabaseError(f"Error retrieving user by email: {str(e)}")


def get_user_by_id(user_id):
    """
    Retrieve user by user ID.
    
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
               FROM users WHERE id = ?""",
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
        raise DatabaseError(f"Error retrieving user by ID: {str(e)}")


# ============================================================================
#                            CANDIDATE FUNCTIONS
# ============================================================================

def insert_candidate(name, email, phone, resume_path, parsed_data):
    """
    Insert a new candidate into the database.
    
    Args:
        name (str): Candidate's full name
        email (str): Candidate's email address
        phone (str): Candidate's phone number
        resume_path (str): Path to the uploaded resume file
        parsed_data (dict): Parsed resume data with skills, experience, education, match_score
    
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
        
        # Converting skills list to JSON string
        skills_json = json.dumps(skills)
        
        cursor.execute("""
            INSERT INTO candidates 
            (name, email, phone, resume_path, parsed_skills, years_experience, education, match_score, shortlist_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, resume_path, skills_json, experience, education, match_score, shortlist_status))
        
        conn.commit()
        candidate_id = cursor.lastrowid
        conn.close()
        
        return candidate_id
        
    except sqlite3.IntegrityError as e:
        raise DatabaseError(f"Integrity error: {str(e)}")
    except Exception as e:
        raise DatabaseError(f"Error inserting candidate: {str(e)}")


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
            FROM candidates WHERE id = ?
        """, (candidate_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Convert to dictionary and parse JSON skills
        candidate = {
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
            'created_at': row[10],
            'updated_at': row[11]
        }
        
        return candidate
        
    except Exception as e:
        raise DatabaseError(f"Error retrieving candidate: {str(e)}")


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
                   education, match_score, shortlist_status, created_at, updated_at
            FROM candidates ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        candidates = []
        for row in rows:
            candidate = {
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
                'created_at': row[10],
                'updated_at': row[11]
            }
            candidates.append(candidate)
        
        return candidates
        
    except Exception as e:
        raise DatabaseError(f"Error retrieving candidates: {str(e)}")


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
            SET shortlist_status = ?, match_score = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, score, candidate_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error updating candidate shortlist: {str(e)}")


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
        
        cursor.execute("""
            INSERT INTO assessments (candidate_id, job_id, status, started_at)
            VALUES (?, ?, 'in_progress', CURRENT_TIMESTAMP)
        """, (candidate_id, job_id))
        
        conn.commit()
        assessment_id = cursor.lastrowid
        conn.close()
        
        return assessment_id
        
    except Exception as e:
        raise DatabaseError(f"Error creating assessment: {str(e)}")


def update_assessment_scores(assessment_id, technical_score, psychometric_score, decision, rationale):
    """
    Update assessment scores and decision.
    
    Args:
        assessment_id (int): The ID of the assessment
        technical_score (float): Technical score (0-100)
        psychometric_score (float): Psychometric score (0-100)
        decision (str): Hiring decision ("Hire", "No-Hire", "Maybe")
        rationale (str): AI-generated explanation
    
    Raises:
        DatabaseError: If update fails
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Calculate overall score as weighted average
        overall_score = (technical_score * 0.6) + (psychometric_score * 0.4)
        
        cursor.execute("""
            UPDATE assessments 
            SET technical_score = ?, psychometric_score = ?, overall_score = ?, 
                decision = ?, rationale = ?, status = 'completed', 
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (technical_score, psychometric_score, overall_score, decision, rationale, assessment_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error updating assessment scores: {str(e)}")


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
            FROM assessments WHERE id = ?
        """, (assessment_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        assessment = {
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
        
        return assessment
        
    except Exception as e:
        raise DatabaseError(f"Error retrieving assessment: {str(e)}")


# ============================================================================
#                       RESPONSE TRACKING FUNCTIONS
# ============================================================================

def save_mcq_response(assessment_id, question_id, selected_answer, is_correct, time_spent):
    """
    Save an MCQ response.
    
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
        
        cursor.execute("""
            INSERT INTO mcq_responses 
            (assessment_id, question_id, selected_answer, is_correct, time_spent)
            VALUES (?, ?, ?, ?, ?)
        """, (assessment_id, question_id, selected_answer, is_correct, time_spent))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving MCQ response: {str(e)}")


def save_coding_submission(assessment_id, problem_id, language, code, test_cases_passed, total_test_cases):
    """
    Save a coding submission.
    
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
        
        cursor.execute("""
            INSERT INTO coding_submissions 
            (assessment_id, problem_id, language, code, test_cases_passed, total_test_cases)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (assessment_id, problem_id, language, code, test_cases_passed, total_test_cases))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving coding submission: {str(e)}")


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
            VALUES (?, ?, ?, ?)
        """, (assessment_id, event_type, severity, details))
        
        # Increment proctoring violations count in assessments table
        cursor.execute("""
            UPDATE assessments 
            SET proctoring_violations = proctoring_violations + 1
            WHERE id = ?
        """, (assessment_id,))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error logging proctoring event: {str(e)}")


def save_psychometric_response(assessment_id, question_id, trait, score, scenario_response=None):
    """
    Save a psychometric response.
    
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
        
        cursor.execute("""
            INSERT INTO psychometric_responses 
            (assessment_id, question_id, trait, score, scenario_response)
            VALUES (?, ?, ?, ?, ?)
        """, (assessment_id, question_id, trait, score, scenario_response))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        raise DatabaseError(f"Error saving psychometric response: {str(e)}")


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
        
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct
            FROM mcq_responses WHERE assessment_id = ?
        """, (assessment_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        total = result[0]
        correct = result[1] if result[1] else 0
        
        if total == 0:
            return 0.0
        
        score = (correct / total) * 100
        return round(score, 2)
        
    except Exception as e:
        raise DatabaseError(f"Error calculating MCQ score: {str(e)}")


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
            FROM coding_submissions WHERE assessment_id = ?
        """, (assessment_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        total_passed = result[0] if result[0] else 0
        total_tests = result[1] if result[1] else 0
        
        if total_tests == 0:
            return 0.0
        
        score = (total_passed / total_tests) * 100
        return round(score, 2)
        
    except Exception as e:
        raise DatabaseError(f"Error calculating coding score: {str(e)}")


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
            FROM psychometric_responses WHERE assessment_id = ?
            GROUP BY trait
        """, (assessment_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        scores = {}
        for row in rows:
            scores[row[0]] = round(row[1], 2)
        
        return scores
        
    except Exception as e:
        raise DatabaseError(f"Error calculating psychometric scores: {str(e)}")


if __name__ == "__main__":
    print("Database Helper Functions Module")
    print("Import this module to use database functions")
