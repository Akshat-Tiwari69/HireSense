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

def calculate_match_score(parsed_data, job_description):
    """
    Calculate basic match score based on skills overlap
    """
    if not job_description or not parsed_data.get('skills'):
        return 50  # Default neutral score
    
    required_skills = set(s.lower() for s in job_description.get('skills', []))
    candidate_skills = set(s.lower() for s in parsed_data.get('skills', []))
    
    if not required_skills:
        return 50
    
    match_count = len(required_skills & candidate_skills)
    score = int((match_count / len(required_skills)) * 100)
    
    # Adjust for experience
    min_exp = job_description.get('min_experience', 0)
    candidate_exp = parsed_data.get('experience', 0)
    
    if candidate_exp >= min_exp:
        score = min(100, score + 10)
    
    return score
