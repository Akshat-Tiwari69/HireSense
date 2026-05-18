# IMPORTANT: eventlet monkey_patch MUST be first, before any other imports
import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import socketio
import os
import uuid
import re
import logging
import contextlib
from pathlib import Path

# Load environment variables
# Priority: local.env (for local development) > .env (for production)

# Check if local.env exists and load it first
local_env_path = Path(__file__).parent / 'local.env'
if local_env_path.exists():
    load_dotenv(local_env_path)
    print("[CONFIG] Loaded local.env for local development")
else:
    # Fall back to .env
    load_dotenv()
    print("[CONFIG] Loaded .env")
# Trigger reload for updated SMTP credentials
from request_logger import init_request_logging
from security_headers import add_security_headers
from datetime import timedelta, datetime
from db_helpers import (
    create_assessment, save_mcq_response,
    save_coding_submission, save_psychometric_response,
    update_assessment_scores, get_assessment_by_id,
    get_mcq_score, get_coding_score, get_psychometric_scores,
    get_user_by_email, get_all_candidates, update_candidate_shortlist,
    update_candidate_status,
)
from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp
from admin_routes import admin_bp
from proctor_routes import proctor_bp
from job_routes import jobs_bp
from resume_routes import resume_bp
from werkzeug.security import check_password_hash
import time

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.info("="*80)
logger.info("HireSense Backend Starting...")
logger.info("="*80)

# Configure JWT
def _get_jwt_secret():
    """Load and validate JWT secret to prevent insecure defaults in deployment."""
    secret = os.environ.get('JWT_SECRET_KEY', '').strip()
    allow_insecure_dev_secret = os.environ.get('ALLOW_INSECURE_DEV_SECRET', '').lower() == 'true'

    if not secret:
        if allow_insecure_dev_secret:
            logger.warning("[SECURITY] Using insecure dev JWT secret due to ALLOW_INSECURE_DEV_SECRET=true")
            return 'dev-secret-key-change-in-production'
        raise RuntimeError("JWT_SECRET_KEY must be set. Refusing to start with an insecure default.")

    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY is too short. Use at least 32 characters.")

    return secret


app.config['JWT_SECRET_KEY'] = _get_jwt_secret()
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.warning("[WARNING] JWT token expired")
    return jsonify({
        'status': 'error',
        'message': 'Token has expired. Please login again.'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.error(f"[ERROR] Invalid JWT token: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Invalid token. Please login again.'
    }), 422

@jwt.unauthorized_loader
def unauthorized_callback(error):
    logger.error(f" Missing JWT token: {error}")
    return jsonify({
        'status': 'error',
        'message': 'Authorization token is missing. Please login.'
    }), 401

# Configure CORS properly for frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            "http://10.39.35.52:5173",
            "http://10.39.35.52:5174",
            "http://10.39.150.52:5173",
            "http://10.39.150.52:5174",
            "http://10.9.199.182:5173",
            "http://10.9.199.182:5174",
            "http://10.9.200.2:5173",
            "http://10.9.200.2:5174"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Initialize Socket.IO for live proctoring
from websocket_server import get_socketio_app
sio = get_socketio_app()
# Wrap Flask app with Socket.IO
app_with_socketio = socketio.WSGIApp(sio, app)
logger.info("[PROCTORING] Socket.IO initialized for live video streaming")

# Initialize request logging middleware
app = init_request_logging(app)

# Add security headers
app = add_security_headers(app)

# Register authentication blueprint
app.register_blueprint(auth_bp, url_prefix='/api/auth')

# Register interviewer routes blueprint
app.register_blueprint(interviewer_bp, url_prefix='/api/interviewer')

# Register interviewee routes blueprint
app.register_blueprint(interviewee_bp, url_prefix='/api/interviewee')

# Register admin routes blueprint
app.register_blueprint(admin_bp, url_prefix='/api/admin')

# Register proctor routes blueprint
app.register_blueprint(proctor_bp, url_prefix='/api/proctor')

# Register job postings & sectors routes blueprint
app.register_blueprint(jobs_bp, url_prefix='/api/jobs')

# Register resume upload blueprint
app.register_blueprint(resume_bp, url_prefix='/api')

# Initialize rate limiting after blueprint registration
from rate_limiter import init_rate_limiting
init_rate_limiting(app)

# Ensure uploads folder exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
logger.info(f"[UPLOAD] Folder configured: {UPLOAD_FOLDER}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set maximum file upload size to 10MB for resume uploads
MAX_FILE_SIZE_MB = 10
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

# Allowed file extensions for resume upload (used by errorhandler below)
ALLOWED_EXTENSIONS = {'pdf', 'docx'}


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "status": "error",
        "message": f"File size exceeds the maximum allowed limit of {MAX_FILE_SIZE_MB}MB"
    }), 413






@app.route('/', methods=['GET'])
def root():
    """Root endpoint - API information"""
    return jsonify({
        "status": "success",
        "service": "HireSense API",
        "version": "1.0.0",
        "health": "/api/health"
    }), 200


@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    """Serve uploaded files (resumes, violation screenshots, etc.)"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API is running"""
    return jsonify({"status": "ok"})


@app.route('/api/resume/upload-legacy', methods=['POST'])
def upload_resume_legacy():
    """Deprecated: resume upload now handled by resume_routes.py at /api/resume/upload."""
    return jsonify({"status": "error", "message": "Use /api/resume/upload instead"}), 410

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
        mcq_for_frontend = [{
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "time_limit": q["time_limit"],
            "category": q["category"],
            "difficulty": q["difficulty"]
        } for q in mcq_questions]
        
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
    DEPRECATED: Use /api/interviewee/assessment/<id>/submit-answer instead.
    This endpoint is kept for backward compatibility but redirects to the proper handler.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400
    
    assessment_id = data.get('assessment_id')
    if not assessment_id:
        return jsonify({"status": "error", "message": "assessment_id is required"}), 400
    
    # Forward to the proper interviewee route handler
    question_id = data.get('question_id')
    answer = data.get('answer')
    time_taken = data.get('time_taken', 0)
    
    # Convert numeric answer index to letter if needed
    if isinstance(answer, int) and 0 <= answer <= 3:
        answer = ['A', 'B', 'C', 'D'][answer]
    
    try:
        from interviewee_routes import interviewee_bp
        # Use the proper submit-answer logic
        from db_helpers import get_assessment_questions, get_assessment_by_id, save_mcq_response
        from questions_bank import get_mcq_questions
        
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404
        
        stored_questions = get_assessment_questions(assessment_id)
        questions = stored_questions.get('mcq_questions', []) if stored_questions else get_mcq_questions(count=20)
        
        correct_answer = None
        for q in questions:
            q_id = int(q['id']) if isinstance(q['id'], str) else q['id']
            if q_id == question_id:
                correct_text = q.get('correct_answer', '')
                for idx, option in enumerate(q['options']):
                    if option.strip().lower() == correct_text.strip().lower():
                        correct_answer = ['A', 'B', 'C', 'D'][idx]
                        break
                break
        
        is_correct = (answer == correct_answer) if correct_answer else None
        
        save_mcq_response(
            assessment_id=assessment_id,
            question_id=question_id,
            selected_answer=answer,
            is_correct=is_correct,
            time_spent=time_taken
        )
        
        return jsonify({
            "status": "success",
            "data": {"is_correct": is_correct}
        }), 200
        
    except Exception as e:
        app.logger.exception("Error submitting MCQ answer")
        return jsonify({"status": "error", "message": f"Failed to submit answer: {str(e)}"}), 500


@app.route('/api/assessment/code/submit', methods=['POST'])
def submit_code():
    """
    DEPRECATED: Use /api/interviewee/assessment/<id>/submit-answer instead.
    Kept for backward compatibility.
    """
    data = request.get_json()
    
    required_fields = ['assessment_id', 'problem_id', 'code', 'language']
    if not data or any(field not in data for field in required_fields):
        return jsonify({
            "status": "error",
            "message": f"Missing required fields: {', '.join(required_fields)}"
        }), 400
    
    try:
        assessment_id = data['assessment_id']
        problem_id = data['problem_id']
        code = data['code']
        language = data['language']
        tests_passed = data.get('testsPassed', 0)
        total_tests = data.get('totalTests', 0)
        
        # Save submission to database with actual test results from client
        save_coding_submission(
            assessment_id=assessment_id,
            problem_id=problem_id,
            language=language,
            code=code,
            test_cases_passed=tests_passed,
            total_test_cases=total_tests
        )
        
        return jsonify({
            "status": "success",
            "data": {
                "passed_count": tests_passed,
                "total_count": total_tests,
                "score": round((tests_passed / max(total_tests, 1)) * 100, 2)
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
    if not data or any(field not in data for field in required_fields):
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


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Accepts:
        - email
        - password
    
    Returns:
        - token (mock)
        - user details
    """
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({
            "status": "error",
            "message": "Email and password are required"
        }), 400
    
    email = data['email']
    password = data['password']
    
    try:
        user = get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            # In production, generate a real JWT here
            return jsonify({
                "status": "success",
                "message": "Login successful",
                "data": {
                    "token": f"mock_token_{uuid.uuid4()}",
                    "user": {
                        "id": user['id'],
                        "name": user['name'],
                        "email": user['email'],
                        "role": user['role']
                    }
                }
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid email or password"
            }), 401
            
    except Exception as e:
        app.logger.exception("Login error")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred during login"
        }), 500


@app.route('/api/dashboard/candidates', methods=['GET'])
def get_candidates():
    """
    Get all candidates for dashboard
    """
    try:
        candidates = get_all_candidates()
        
        # Enrich candidate data if needed (e.g. status badge colors)
        # For now return as is
        
        return jsonify({
            "status": "success",
            "data": candidates
        }), 200
    except Exception as e:
        app.logger.exception("Error fetching candidates")
        return jsonify({
            "status": "error",
            "message": "Failed to fetch candidates"
        }), 500

@app.route('/api/dashboard/candidates/<int:candidate_id>/shortlist', methods=['POST'])
def update_shortlist(candidate_id):
    """Update candidate shortlist status"""
    data = request.get_json()
    try:
        status = data.get('status')
        score = data.get('score')
        update_candidate_shortlist(candidate_id, status, score)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run with Socket.IO WSGI app
    import eventlet.wsgi
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app_with_socketio)
