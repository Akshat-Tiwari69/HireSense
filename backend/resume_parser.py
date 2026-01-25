"""
Basic resume parsing functions (minimal stubs)
Main parsing now handled by resume_analyzer.py with AI
"""

def parse_resume(filepath, job_description=None):
    """
    Basic fallback parser - returns minimal data structure
    Real parsing done by ResumeAnalyzer in resume_analyzer.py
    """
    return {
        'skills': [],
        'experience': 0,
        'education': '',
        'name': '',
        'email': '',
        'phone': ''
    }

def calculate_match_score(parsed_data_or_skills, job_or_experience=None, required_skills=None, min_experience=0):
    """
    Calculate basic match score based on skills overlap.

    Supports two call styles:
    1) calculate_match_score(parsed_data: dict, job_description: dict)
    2) calculate_match_score(skills: list, experience: int, required_skills: list, min_experience: int)
    """

    # Branch: dict inputs (existing usage)
    if isinstance(parsed_data_or_skills, dict):
        parsed_data = parsed_data_or_skills or {}
        job_description = job_or_experience or {}
        skills = parsed_data.get('skills', []) or []
        experience = parsed_data.get('experience', 0) or 0
        required = job_description.get('skills', []) or []
        min_exp = job_description.get('min_experience', 0) or 0
    else:
        # Branch: positional inputs
        skills = parsed_data_or_skills or []
        experience = job_or_experience or 0
        required = required_skills or []
        min_exp = min_experience or 0

    if not required:
        return 50  # Default neutral when JD unspecified

    required_skills_set = set(s.lower() for s in required)
    candidate_skills_set = set(s.lower() for s in skills)

    if not required_skills_set:
        return 50

    match_count = len(required_skills_set & candidate_skills_set)
    score = int((match_count / len(required_skills_set)) * 100)

    if experience >= min_exp:
        score = min(100, score + 10)

    return score
