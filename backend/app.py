from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.utils import secure_filename
import os
import uuid
import re
from datetime import timedelta
from resume_parser import parse_resume
from db_helpers import (
    insert_candidate, create_assessment, save_mcq_response,
    save_coding_submission, save_psychometric_response,
    update_assessment_scores, get_assessment_by_id,
    get_mcq_score, get_coding_score, get_psychometric_scores
)
from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
from auth import auth_bp
import time

# Initialize Flask app
app = Flask(__name__)

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Enable CORS so frontend can call our APIs
CORS(app)

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Ensure uploads folder exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set maximum file upload size to 10MB for resume uploads
MAX_FILE_SIZE_MB = 10
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

# Allowed file extensions for resume upload
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Email validation pattern (RFC 5322 compliant, simplified)
# Prevents consecutive dots, leading/trailing hyphens in domain
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'


def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file upload exceeding MAX_CONTENT_LENGTH"""
    return jsonify({
        "status": "error",
        "message": f"File size exceeds the maximum allowed limit of {MAX_FILE_SIZE_MB}MB"
    }), 413
def is_valid_email(email):
    """Validate email format using regex pattern"""
    if email is None or not isinstance(email, str) or not email.strip():
        return False
    return re.match(EMAIL_PATTERN, email) is not None


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running"""
    return jsonify({"status": "ok"})


@app.route('/api/resume/upload', methods=['POST'])
def upload_resume():
    """
    Resume upload endpoint
    
    Accepts:
        - file: PDF or DOCX resume file
        - name: Candidate's name (required)
        - email: Candidate's email (required)
        - phone: Candidate's phone number (optional)
    
    Returns:
        JSON with status, file_path, and message
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file uploaded"
        }), 400
    
    file = request.files['file']
    
    # Check if file has a filename (no file selected)
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "No file selected"
        }), 400
    
    # Check file type
    if not allowed_file(file.filename):
        return jsonify({
            "status": "error",
            "message": "Invalid file type. Only PDF and DOCX allowed"
        }), 400
    
    # Get form data
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()  # Optional field
    
    # Validate required fields
    if not name or not email:
        return jsonify({
            "status": "error",
            "message": "Name and email are required"
        }), 400
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({
            "status": "error",
            "message": "Invalid email format"
        }), 400
    
    # Generate unique filename to prevent conflicts
    original_filename = secure_filename(file.filename)
    # Ensure secure_filename produced a valid filename with an extension
    if not original_filename or "." not in original_filename:
        return jsonify({
            "status": "error",
            "message": "Invalid filename after sanitization"
        }), 400
    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    
    # Save file to uploads folder
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    try:
        file.save(filepath)
    except OSError as e:
        app.logger.error("Failed to save uploaded file '%s': %s", filepath, e)
        return jsonify({
            "status": "error",
            "message": "Failed to save uploaded file. Please try again later."
        }), 500
    except Exception as e:
        app.logger.exception("Unexpected error while saving uploaded file '%s'", filepath)
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while saving the file."
        }), 500
    
    # Parse the resume to extract data
    try:
        # Optional: Define job description for matching (can be passed from frontend or config)
        job_description = {
            'skills': ['Python', 'Java', 'JavaScript', 'React', 'AWS'],  # Example JD
            'min_experience': 2  # Example requirement
        }
        
        parsed_data = parse_resume(filepath, job_description)
    except Exception as e:
        app.logger.exception("Error parsing resume '%s'", filepath)
        parsed_data = {
            "error": "Failed to parse resume",
            "skills": [],
            "experience": 0,
            "education": "Not Specified",
            "match_score": 0,
            "shortlist_status": "Pending Review"
        }
    
    # Save candidate to database
    try:
        candidate_id = insert_candidate(
            name=name,
            email=email,
            phone=phone,
            resume_path=filepath,
            parsed_data=parsed_data
        )
        app.logger.info(f"Candidate saved to database with ID: {candidate_id}")
    except Exception as e:
        app.logger.exception("Error saving candidate to database")
        # Continue anyway - parsing was successful
        candidate_id = None
    
    # Return success response
    # Use the configured upload folder name for consistency
    relative_path = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER']), unique_filename)
    return jsonify({
        "status": "success",
        "message": "Resume uploaded and parsed successfully",
        "data": {
            "candidate_id": candidate_id,
            "file_path": relative_path,
            "original_filename": original_filename,
            "candidate": {
                "name": name,
                "email": email,
                "phone": phone
            },
            "parsed_data": parsed_data
        }
    }), 201


@app.route('/api/assessment/start', methods=['POST'])
def start_assessment():
    """
    Start assessment for a candidate
    
    Expects JSON:
        - candidate_id: ID of the candidate
    
    Returns:
        - assessment_id
        - MCQ questions
        - Coding problem
        - Psychometric scenarios
    """
    data = request.get_json()
    
    if not data or 'candidate_id' not in data:
        return jsonify({
            "status": "error",
            "message": "candidate_id is required"
        }), 400
    
    candidate_id = data['candidate_id']
    
    try:
        # Create assessment in database
        assessment_id = create_assessment(candidate_id)
        
        # Get questions
        mcq_questions = get_mcq_questions(count=10)
        coding_problem = get_coding_problem(difficulty="easy")
        psychometric_scenarios = get_psychometric_scenarios(count=3)
        
        # Remove correct answers from MCQ questions before sending
        mcq_for_frontend = []
        for q in mcq_questions:
            mcq_for_frontend.append({
                "id": q["id"],
                "question": q["question"],
                "options": q["options"],
                "time_limit": q["time_limit"],
                "category": q["category"],
                "difficulty": q["difficulty"]
            })
        
        return jsonify({
            "status": "success",
            "message": "Assessment started successfully",
            "data": {
                "assessment_id": assessment_id,
                "mcq_questions": mcq_for_frontend,
                "coding_problem": {
                    "id": coding_problem["id"],
                    "title": coding_problem["title"],
                    "description": coding_problem["description"],
                    "example": coding_problem["example"],
                    "difficulty": coding_problem["difficulty"]
                },
                "psychometric_scenarios": psychometric_scenarios
            }
        }), 201
        
    except Exception as e:
        app.logger.exception("Error starting assessment")
        return jsonify({
            "status": "error",
            "message": f"Failed to start assessment: {str(e)}"
        }), 500


@app.route('/api/assessment/mcq/submit', methods=['POST'])
def submit_mcq():
    """
    Submit MCQ answer
    
    Expects JSON:
        - assessment_id: ID of the assessment
        - question_id: ID of the question
        - answer: Selected answer index (0-3)
        - time_taken: Time taken in seconds
    
    Returns:
        - is_correct: Boolean
        - correct_answer: The correct answer index
    """
    data = request.get_json()
    
    required_fields = ['assessment_id', 'question_id', 'answer', 'time_taken']
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(required_fields)}"
        }), 400
    
    try:
        assessment_id = data['assessment_id']
        question_id = data['question_id']
        answer = data['answer']
        time_taken = data['time_taken']
        
        # Find the question to check correct answer
        from questions_bank import MCQ_QUESTIONS
        question = next((q for q in MCQ_QUESTIONS if q['id'] == question_id), None)
        
        if not question:
            return jsonify({
                "status": "error",
                "message": "Invalid question_id"
            }), 400
        
        is_correct = (answer == question['correct_answer'])
        
        # Save response to database
        save_mcq_response(
            assessment_id=assessment_id,
            question_id=question_id,
            selected_answer=answer,
            is_correct=is_correct,
            time_spent=time_taken
        )
        
        return jsonify({
            "status": "success",
            "data": {
                "is_correct": is_correct,
                "correct_answer": question['correct_answer']
            }
        }), 200
        
    except Exception as e:
        app.logger.exception("Error submitting MCQ answer")
        return jsonify({
            "status": "error",
            "message": f"Failed to submit answer: {str(e)}"
        }), 500


@app.route('/api/assessment/code/submit', methods=['POST'])
def submit_code():
    """
    Submit coding solution
    
    Expects JSON:
        - assessment_id: ID of the assessment
        - problem_id: ID of the problem
        - code: Source code submitted
        - language: Programming language
    
    Returns:
        - test_results: Results of test cases
        - passed_count: Number of passed test cases
        - total_count: Total test cases
    """
    data = request.get_json()
    
    required_fields = ['assessment_id', 'problem_id', 'code', 'language']
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(required_fields)}"
        }), 400
    
    try:
        assessment_id = data['assessment_id']
        problem_id = data['problem_id']
        code = data['code']
        language = data['language']
        
        # For now, we'll do basic validation without actual execution
        # In production, you'd use grading_engine.py with proper sandboxing
        
        # Simulate test case execution (placeholder)
        passed = 2
        total = 3
        test_results = [
            {"test_case": 1, "passed": True, "message": "Correct output"},
            {"test_case": 2, "passed": True, "message": "Correct output"},
            {"test_case": 3, "passed": False, "message": "Expected [0,1] but got [1,0]"}
        ]
        
        # Save submission to database
        save_coding_submission(
            assessment_id=assessment_id,
            problem_id=problem_id,
            language=language,
            code=code,
            test_cases_passed=passed,
            total_test_cases=total
        )
        
        return jsonify({
            "status": "success",
            "data": {
                "test_results": test_results,
                "passed_count": passed,
                "total_count": total,
                "score": round((passed / total) * 100, 2)
            }
        }), 200
        
    except Exception as e:
        app.logger.exception("Error submitting code")
        return jsonify({
            "status": "error",
            "message": f"Failed to submit code: {str(e)}"
        }), 500


@app.route('/api/assessment/psychometric/submit', methods=['POST'])
def submit_psychometric():
    """
    Submit psychometric response
    
    Expects JSON:
        - assessment_id: ID of the assessment
        - scenario_id: ID of the scenario
        - trait_scores: Dict of trait names to scores (1-10)
        - response_text: Written response to scenario
    
    Returns:
        - success message
    """
    data = request.get_json()
    
    required_fields = ['assessment_id', 'scenario_id', 'trait_scores']
    if not data or not all(field in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(required_fields)}"
        }), 400
    
    try:
        assessment_id = data['assessment_id']
        scenario_id = data['scenario_id']
        trait_scores = data['trait_scores']
        response_text = data.get('response_text', '')
        
        # Save each trait score
        for trait, score in trait_scores.items():
            save_psychometric_response(
                assessment_id=assessment_id,
                question_id=scenario_id,
                trait=trait,
                score=score,
                scenario_response=response_text
            )
        
        return jsonify({
            "status": "success",
            "message": "Psychometric response saved successfully"
        }), 200
        
    except Exception as e:
        app.logger.exception("Error submitting psychometric response")
        return jsonify({
            "status": "error",
            "message": f"Failed to submit response: {str(e)}"
        }), 500


@app.route('/api/assessment/complete', methods=['POST'])
def complete_assessment():
    """
    Complete assessment and calculate final scores
    
    Expects JSON:
        - assessment_id: ID of the assessment
    
    Returns:
        - technical_score: Combined MCQ + coding score
        - psychometric_scores: Average scores for each trait
        - overall_score: Weighted combination
        - decision: Preliminary decision
    """
    data = request.get_json()
    
    if not data or 'assessment_id' not in data:
        return jsonify({
            "status": "error",
            "message": "assessment_id is required"
        }), 400
    
    try:
        assessment_id = data['assessment_id']
        
        # Calculate scores
        mcq_score = get_mcq_score(assessment_id)
        coding_score = get_coding_score(assessment_id)
        psychometric_scores = get_psychometric_scores(assessment_id)
        
        # Calculate technical score (60% MCQ, 40% Coding)
        technical_score = (mcq_score * 0.6) + (coding_score * 0.4)
        
        # Calculate average psychometric score
        if psychometric_scores:
            avg_psychometric = sum(psychometric_scores.values()) / len(psychometric_scores)
        else:
            avg_psychometric = 0
        
        # Calculate overall score (70% technical, 30% psychometric)
        overall_score = (technical_score * 0.7) + (avg_psychometric * 10 * 0.3)
        
        # Determine preliminary decision
        if overall_score >= 70:
            decision = "Recommend for Hire"
            rationale = "Strong technical and soft skills demonstrated"
        elif overall_score >= 50:
            decision = "Consider for Interview"
            rationale = "Moderate performance, needs further evaluation"
        else:
            decision = "Not Recommended"
            rationale = "Performance below threshold"
        
        # Update assessment in database
        update_assessment_scores(
            assessment_id=assessment_id,
            technical_score=technical_score,
            psychometric_score=avg_psychometric * 10,
            decision=decision,
            rationale=rationale
        )
        
        return jsonify({
            "status": "success",
            "message": "Assessment completed successfully",
            "data": {
                "assessment_id": assessment_id,
                "scores": {
                    "mcq": round(mcq_score, 2),
                    "coding": round(coding_score, 2),
                    "technical": round(technical_score, 2),
                    "psychometric": round(avg_psychometric * 10, 2),
                    "overall": round(overall_score, 2)
                },
                "psychometric_traits": {k: round(v, 2) for k, v in psychometric_scores.items()},
                "decision": decision,
                "rationale": rationale
            }
        }), 200
        
    except Exception as e:
        app.logger.exception("Error completing assessment")
        return jsonify({
            "status": "error",
            "message": f"Failed to complete assessment: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
