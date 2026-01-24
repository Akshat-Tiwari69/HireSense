"""
Resume Parser Module
Extracts and analyzes data from resume files (PDF/DOCX)
"""

import re
import PyPDF2
from docx import Document


# Common skills list for matching (expandable)
COMMON_SKILLS = [
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 
    'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab', 'sql',
    
    # Web Technologies
    'html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django',
    'flask', 'spring', 'spring boot', 'asp.net', 'laravel', 'jquery',
    
    # Databases
    'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sql server', 
    'cassandra', 'dynamodb', 'elasticsearch', 'firebase',
    
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'gitlab',
    'terraform', 'ansible', 'ci/cd', 'devops',
    
    # Data Science & ML
    'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
    'pandas', 'numpy', 'data analysis', 'data science', 'nlp', 'computer vision',
    
    # Tools & Frameworks
    'git', 'github', 'jira', 'agile', 'scrum', 'rest api', 'graphql',
    'microservices', 'linux', 'unix', 'bash', 'power bi', 'tableau',
    
    # Soft Skills
    'leadership', 'communication', 'problem solving', 'team work', 'management'
]

# Basic patterns for contact details
EMAIL_REGEX = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
PHONE_REGEX = r'(?:\+?\d[\s-]*){10,15}'

# Education keywords
EDUCATION_KEYWORDS = {
    'bachelor': ['bachelor', 'b.tech', 'b.e', 'b.sc', 'bs', 'btech', 'bca'],
    'master': ['master', 'm.tech', 'm.e', 'm.sc', 'ms', 'mtech', 'mca', 'mba'],
    'phd': ['phd', 'ph.d', 'doctorate'],
    'diploma': ['diploma', 'associate']
}


def extract_text_from_pdf(filepath):
    """
    Extract text from PDF file
    
    Args:
        filepath (str): Path to PDF file
        
    Returns:
        str: Extracted text
    """
    try:
        text = ""
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_docx(filepath):
    """
    Extract text from DOCX file
    
    Args:
        filepath (str): Path to DOCX file
        
    Returns:
        str: Extracted text
    """
    try:
        doc = Document(filepath)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return ""


def extract_skills(text):
    """
    Extract skills from resume text by matching against known skills
    
    Args:
        text (str): Resume text
        
    Returns:
        list: List of found skills
    """
    text_lower = text.lower()
    found_skills = []
    
    for skill in COMMON_SKILLS:
        # Use word boundary regex to avoid partial matches
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title())
    
    # Remove duplicates and sort
    found_skills = sorted(list(set(found_skills)))
    return found_skills


def extract_experience(text):
    """
    Extract years of experience from resume text
    
    Args:
        text (str): Resume text
        
    Returns:
        int: Years of experience (0 if not found)
    """
    # Patterns to match experience mentions
    patterns = [
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)',
        r'experience\s*[:–-]\s*(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:in|of|with)',
    ]
    
    text_lower = text.lower()
    max_experience = 0
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            try:
                years = int(match)
                max_experience = max(max_experience, years)
            except ValueError:
                continue
    
    return max_experience


def extract_education(text):
    """
    Extract highest education level from resume text
    
    Args:
        text (str): Resume text
        
    Returns:
        str: Education level (e.g., "Bachelor's", "Master's", "PhD", "Diploma", "Not Specified")
    """
    text_lower = text.lower()
    
    # Check in order of highest to lowest
    if any(keyword in text_lower for keyword in EDUCATION_KEYWORDS['phd']):
        return "PhD"
    elif any(keyword in text_lower for keyword in EDUCATION_KEYWORDS['master']):
        return "Master's"
    elif any(keyword in text_lower for keyword in EDUCATION_KEYWORDS['bachelor']):
        return "Bachelor's"
    elif any(keyword in text_lower for keyword in EDUCATION_KEYWORDS['diploma']):
        return "Diploma"
    
    return "Not Specified"


def extract_email(text):
    """Pull the first email-like string from the resume text."""
    matches = re.findall(EMAIL_REGEX, text)
    return matches[0].strip() if matches else None


def extract_phone(text):
    """Find a likely phone number (10-15 digits with optional separators)."""
    matches = re.findall(PHONE_REGEX, text)
    if not matches:
        return None
    # Keep digits and leading plus
    raw = matches[0]
    digits = re.sub(r'[^\d+]', '', raw)
    # Normalize simple cases like +1XXXXXXXXXX or XXXXXXXXXX
    return digits


def derive_name_from_email(email):
    """Derive a readable name from the local-part of an email address."""
    if not email or '@' not in email:
        return None
    local = email.split('@', 1)[0]
    parts = re.split(r'[._-]+', local)
    parts = [p for p in parts if p]
    if not parts:
        return None
    return " ".join([p.capitalize() for p in parts])


def extract_name(text, email=None):
    """Guess the candidate's name from the top of the resume or email."""
    # Check first few non-empty lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:5]:
        # Skip lines that look like contact lines
        if '@' in line or re.search(PHONE_REGEX, line):
            continue
        # Require at least two words and mostly letters
        words = line.split()
        if len(words) >= 2 and all(re.match(r'^[A-Za-z\-\.]+$', w) for w in words):
            return " ".join([w.strip('.').capitalize() for w in words])
    # Fallback to email-derived name
    return derive_name_from_email(email)


def calculate_match_score(candidate_skills, candidate_exp, jd_skills=None, jd_min_exp=0):
    """
    Calculate match score between candidate and job description
    
    Args:
        candidate_skills (list): List of candidate's skills
        candidate_exp (int): Candidate's years of experience
        jd_skills (list): Required skills from job description (optional)
        jd_min_exp (int): Minimum required experience (default: 0)
        
    Returns:
        int: Match score (0-100)
    """
    # If no JD provided, use basic scoring
    if not jd_skills:
        # Base score on number of skills and experience
        skill_score = min(len(candidate_skills) * 5, 70)  # Max 70 for skills
        exp_score = min(candidate_exp * 3, 30)  # Max 30 for experience
        return min(skill_score + exp_score, 100)
    
    # Calculate skill match percentage
    jd_skills_lower = [skill.lower() for skill in jd_skills]
    candidate_skills_lower = [skill.lower() for skill in candidate_skills]
    
    matched_skills = [skill for skill in candidate_skills_lower if skill in jd_skills_lower]
    
    if len(jd_skills) > 0:
        skill_match = (len(matched_skills) / len(jd_skills)) * 100
    else:
        skill_match = 0
    
    # Calculate experience match
    if jd_min_exp > 0:
        exp_match = min((candidate_exp / jd_min_exp) * 100, 100)
    else:
        exp_match = 100  # No experience requirement
    
    # Weighted score: 70% skills, 30% experience
    final_score = (skill_match * 0.7) + (exp_match * 0.3)
    
    return round(final_score)


def get_shortlist_status(score):
    """
    Determine shortlist status based on match score
    
    Args:
        score (int): Match score (0-100)
        
    Returns:
        str: Shortlist status
    """
    if score >= 70:
        return "High Match"
    elif score >= 40:
        return "Potential"
    else:
        return "Reject"


def parse_resume(filepath, job_description=None):
    """
    Main function to parse resume and extract all relevant information
    
    Args:
        filepath (str): Path to resume file
        job_description (dict): Optional JD with 'skills' and 'min_experience' keys
        
    Returns:
        dict: Parsed resume data including skills, experience, education, match score, and status
    """
    # Determine file type and extract text
    if filepath.lower().endswith('.pdf'):
        text = extract_text_from_pdf(filepath)
    elif filepath.lower().endswith('.docx'):
        text = extract_text_from_docx(filepath)
    else:
        return {
            "error": "Unsupported file format",
            "text": "",
            "skills": [],
            "experience": 0,
            "education": "Not Specified",
            "match_score": 0,
            "shortlist_status": "Reject"
        }
    
    # Extract data
    email = extract_email(text)
    phone = extract_phone(text)
    name = extract_name(text, email)
    skills = extract_skills(text)
    experience = extract_experience(text)
    education = extract_education(text)
    
    # Calculate match score
    jd_skills = job_description.get('skills', []) if job_description else []
    jd_min_exp = job_description.get('min_experience', 0) if job_description else 0
    
    match_score = calculate_match_score(skills, experience, jd_skills, jd_min_exp)
    shortlist_status = get_shortlist_status(match_score)
    
    return {
        "text": text[:500] + "..." if len(text) > 500 else text,  # First 500 chars for preview
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "experience": experience,
        "education": education,
        "match_score": match_score,
        "shortlist_status": shortlist_status
    }


# For testing
if __name__ == "__main__":
    # Test with sample data
    sample_text = """
    John Doe
    Senior Software Engineer
    
    Experience: 5 years in software development
    
    Skills: Python, Java, JavaScript, React, Node.js, MySQL, AWS, Docker, Git
    
    Education: B.Tech in Computer Science
    """
    
    print("Skills found:", extract_skills(sample_text))
    print("Experience:", extract_experience(sample_text))
    print("Education:", extract_education(sample_text))
    
    # Test match score
    jd = {
        'skills': ['Python', 'React', 'AWS', 'Docker'],
        'min_experience': 3
    }
    
    score = calculate_match_score(
        extract_skills(sample_text),
        extract_experience(sample_text),
        jd['skills'],
        jd['min_experience']
    )
    
    print(f"Match Score: {score}")
    print(f"Status: {get_shortlist_status(score)}")
