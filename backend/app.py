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
from resume_parser import parse_resume
from resume_analyzer import analyze_resume
from db_helpers import (
    insert_candidate, create_assessment, save_mcq_response,
    save_coding_submission, save_psychometric_response,
    update_assessment_scores, get_assessment_by_id,
    get_mcq_score, get_coding_score, get_psychometric_scores,
    get_user_by_email, get_all_candidates, update_candidate_shortlist,
    update_candidate_status, get_candidate_by_email
)
from questions_bank import get_mcq_questions, get_coding_problem, get_psychometric_scenarios
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp
from admin_routes import admin_bp
from proctor_routes import proctor_bp
from job_routes import jobs_bp
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


def name_from_email(email):
    """Derive a human-friendly name from the email local part."""
    if not email or '@' not in email:
        return None
    local = email.split('@', 1)[0]
    parts = re.split(r'[._-]+', local)
    parts = [p for p in parts if p]
    return " ".join(p.capitalize() for p in parts) if parts else None


def _get_job_description_for_id(job_id):
    """
    Fetch a specific job posting by ID and return its requirements dict.
    Returns (job_dict, job_row) tuple — job_row includes title/department for response.
    """
    try:
        from db_config import get_connection, return_connection
        import json as _json
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, title, department, required_skills, preferred_skills, min_experience "
            "FROM job_descriptions WHERE id = %s AND status = 'active'",
            (int(job_id),)
        )
        row = cursor.fetchone()
        return_connection(conn)

        if row:
            skills = set()
            for skills_val in (row[3], row[4]):
                if skills_val:
                    with contextlib.suppress(ValueError, TypeError):
                        parsed = _json.loads(skills_val)
                        if isinstance(parsed, list):
                            skills.update(s.strip() for s in parsed if s.strip())
                            continue
                    skills.update(s.strip() for s in str(skills_val).split(',') if s.strip())
            min_exp = row[5] or 0
            job_info = {'id': row[0], 'title': row[1], 'department': row[2]}
            return {'skills': list(skills), 'min_experience': min_exp, 'title': row[1], 'department': row[2]}, job_info
    except Exception as e:
        logger.warning(f"[MATCH] Could not load job posting {job_id}: {e}")
    return None, None






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


@app.route('/api/resume/upload', methods=['POST'])
def upload_resume():
    """
    Resume upload endpoint
    
    Accepts:
        - file: PDF or DOCX resume file (required)
        - name/email/phone: Optional overrides; normally extracted from resume
    
    Returns:
        JSON with status, file_path, and message
    """
    logger.info("="*80)
    logger.info("[UPLOAD] RESUME UPLOAD REQUEST RECEIVED")
    logger.info("="*80)
    
    # Check if file was uploaded
    if 'file' not in request.files:
        logger.error("[ERROR] No file in request")
        return jsonify({
            "status": "error",
            "message": "No file uploaded"
        }), 400
    
    file = request.files['file']
    logger.info(f"[FILE] File detected: {file.filename}")
    
    # Check if file has a filename (no file selected)
    if file.filename == '':
        logger.error("[ERROR] Empty filename")
        return jsonify({
            "status": "error",
            "message": "No file selected"
        }), 400
    
    # Check file type
    if not allowed_file(file.filename):
        logger.error(f"[ERROR] Invalid file type: {file.filename}")
        return jsonify({
            "status": "error",
            "message": "Invalid file type. Only PDF and DOCX allowed"
        }), 400
    
    logger.info(f"[OK] File type validated: {file.filename}")
    
    # Generate unique filename to prevent conflicts
    original_filename = secure_filename(file.filename)
    # Ensure secure_filename produced a valid filename with an extension
    if not original_filename or "." not in original_filename:
        logger.error(f"[ERROR] Invalid filename after sanitization: {original_filename}")
        return jsonify({
            "status": "error",
            "message": "Invalid filename after sanitization"
        }), 400
    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    
    logger.info(f"[SECURE] Generated unique filename: {unique_filename}")
    
    # Save file to uploads folder
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    try:
        logger.info(f"[SAVE] Saving file to: {filepath}")
        file.save(filepath)
        logger.info("[OK] File saved successfully")
    except OSError as e:
        logger.error(f"[ERROR] OSError saving file: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to save uploaded file. Please try again later."
        }), 500
    except Exception as e:
        logger.exception(f"[ERROR] Unexpected error saving file: {e}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while saving the file."
        }), 500
    
    # Candidate must select a specific job — AI scores only against that role
    selected_job_id = request.form.get('job_id')
    selected_job_info = None
    job_description = None

    if not selected_job_id:
        return jsonify({
            "status": "error",
            "message": "Please select a job position to apply for."
        }), 400

    job_description, selected_job_info = _get_job_description_for_id(selected_job_id)
    if not job_description:
        return jsonify({
            "status": "error",
            "message": "The selected job position is no longer active. Please choose another."
        }), 400

    logger.info(f"[MATCH] Scoring against selected job: {selected_job_info['title']} (ID: {selected_job_id})")
    logger.info(f"[MATCH] Job skills: {job_description.get('skills', [])}, Min exp: {job_description.get('min_experience', 0)}")

    # Parse the resume to extract data
    try:
        logger.info("[PARSE] Starting resume parsing...")
        
        # First try basic parsing as fallback data
        parsed_data = parse_resume(filepath, job_description)
        logger.info(f"[OK] Basic parsing completed - Skills: {len(parsed_data.get('skills', []))}, Experience: {parsed_data.get('experience', 0)} years")
        
        # Extract resume text for AI analysis
        logger.info("[AI] Extracting resume text for AI analysis...")
        with open(filepath, 'rb') as f:
            # Get raw text (simplified - you may want to use the same extraction as in resume_parser)
            if filepath.endswith('.pdf'):
                from PyPDF2 import PdfReader
                pdf = PdfReader(f)
                resume_text = " ".join([page.extract_text() for page in pdf.pages])
                logger.info(f"[OK] Extracted {len(resume_text)} characters from PDF")
            else:
                from docx import Document
                doc = Document(f)
                resume_text = " ".join([para.text for para in doc.paragraphs])
                logger.info(f"[OK] Extracted {len(resume_text)} characters from DOCX")
        
        # Try AI extraction for better accuracy
        ai_extracted_data = None
        try:
            from resume_analyzer import ResumeAnalyzer
            logger.info("[AI] Using AI to extract contact info and resume data...")
            analyzer = ResumeAnalyzer()
            
            if ai_extracted_data := analyzer.extract_resume_data(resume_text):
                logger.info("[OK] AI extraction successful")
                logger.info(f"   Name: {ai_extracted_data.get('name')}")
                logger.info(f"   Email: {ai_extracted_data.get('email')}")
                logger.info(f"   Phone: {ai_extracted_data.get('phone')}")
                logger.info(f"   Skills: {len(ai_extracted_data.get('skills', []))}")
                logger.info(f"   Experience: {ai_extracted_data.get('experience', 0)} years")
                
                # Merge AI data with parsed data (AI takes precedence)
                if ai_extracted_data.get('skills'):
                    parsed_data['skills'] = ai_extracted_data['skills']
                if ai_extracted_data.get('experience') is not None and ai_extracted_data['experience'] > 0:
                    parsed_data['experience'] = ai_extracted_data['experience']
                if ai_extracted_data.get('education'):
                    parsed_data['education'] = ai_extracted_data['education']
                if ai_extracted_data.get('name'):
                    parsed_data['name'] = ai_extracted_data['name']
                if ai_extracted_data.get('email'):
                    parsed_data['email'] = ai_extracted_data['email']
                if ai_extracted_data.get('phone'):
                    parsed_data['phone'] = ai_extracted_data['phone']
                
                # Recalculate match score with AI-extracted data
                from resume_parser import calculate_match_score
                parsed_data['match_score'] = calculate_match_score(
                    parsed_data.get('skills', []),
                    parsed_data.get('experience', 0),
                    job_description.get('skills', []),
                    job_description.get('min_experience', 0)
                )
                logger.info(f"[SCORE] Recalculated match score: {parsed_data['match_score']}%")
        except Exception as ai_extract_error:
            logger.warning(f"[WARNING] AI extraction failed: {ai_extract_error}. Using basic parsing.")
        
        # Generate AI-powered pros/cons analysis
        ai_analysis = None
        try:
            logger.info("[AI] Sending resume to AI for pros/cons analysis...")
            logger.info(f"[INFO] Resume text length: {len(resume_text)} chars, Parsed skills: {len(parsed_data.get('skills', []))}")
            
            ai_analysis = analyze_resume(
                resume_text=resume_text,
                parsed_data=parsed_data,
                job_requirements=job_description,
                enhance_score=True
            )
            logger.info(" AI analysis completed")
            logger.info(f"   Recommendation: {ai_analysis['recommendation']}")
            logger.info(f"   Confidence: {ai_analysis.get('confidence_score', 0)}")
            logger.info(f"   Pros: {len(ai_analysis.get('pros', []))} points")
            logger.info(f"   Cons: {len(ai_analysis.get('cons', []))} points")
            
            # Use enhanced match score if available
            if 'enhanced_match_score' in ai_analysis:
                parsed_data['match_score'] = ai_analysis['enhanced_match_score']
                parsed_data['original_match_score'] = parsed_data.get('match_score', 0)
                logger.info(f"[SCORE] Match score updated: {parsed_data['match_score']}")
            
        except Exception as ai_error:
            logger.warning(f"[WARNING] AI analysis failed: {ai_error}. Proceeding with basic analysis.")
            # Continue without AI - we'll still have parsed data
            ai_analysis = {
                "pros": ["Resume uploaded successfully"],
                "cons": ["AI analysis unavailable - manual review recommended"],
                "overall_assessment": "AI analysis failed. Manual review required.",
                "recommendation": "Pending Review",
                "confidence_score": 0
            }
    
    except Exception as e:
        logger.exception(f"[ERROR] Error parsing resume: {e}")
        parsed_data = {
            "error": "Failed to parse resume",
            "skills": [],
            "experience": 0,
            "education": "Not Specified",
            "match_score": 0,
            "shortlist_status": "Pending Review"
        }
        ai_analysis = None
    
    # Resolve candidate identity from parsed data with optional manual overrides
    manual_name = request.form.get('name', '').strip()
    manual_email = request.form.get('email', '').strip()
    manual_phone = request.form.get('phone', '').strip()

    name = manual_name or parsed_data.get('name')
    email = manual_email or parsed_data.get('email')
    phone = manual_phone or parsed_data.get('phone') or ""
    
    # Debug logging for name/email detection with source identification
    logger.info(f"[DEBUG] Email detection - manual: '{manual_email}', parsed: '{parsed_data.get('email')}', final: '{email}'")
    logger.info(f"[DEBUG] Name detection - manual: '{manual_name}', AI/parsed: '{parsed_data.get('name')}', final: '{name}'")

    if not email or not is_valid_email(email):
        logger.error("[ERROR] Unable to detect a valid email from resume or overrides")
        logger.error(f"[ERROR] Failed email value: '{email}', is_valid: {is_valid_email(email) if email else 'N/A'}")
        logger.error(f"[ERROR] Parsed data keys: {list(parsed_data.keys())}")
        return jsonify({
            "status": "error",
            "message": "Could not detect a valid email in the resume. Please add an email field or ensure your resume contains a valid email address."
        }), 400

    if not name:
        derived_name = name_from_email(email)
        name = derived_name or "Candidate"
        logger.info(f"[DEBUG] Name was empty, derived from email: '{derived_name}' -> final: '{name}'")

    logger.info(f"[CANDIDATE] Candidate Info - Name: {name}, Email: {email}, Phone: {phone or 'N/A'}")

    # Check if candidate already exists with this email
    with contextlib.suppress(Exception):
        if existing_candidate := get_candidate_by_email(email):
            logger.info(f"[DUPLICATE] Candidate with email {email} already registered (ID: {existing_candidate['id']})")
            return jsonify({
                "status": "error",
                "message": f"You have already registered with this email address ({email}). Please check your email for assessment instructions or contact the recruiter if you need assistance.",
                "existing_candidate": {
                    "name": existing_candidate['name'],
                    "status": existing_candidate['status'],
                    "registered_at": str(existing_candidate['created_at']) if existing_candidate['created_at'] else None
                }
            }), 409  # 409 Conflict

    # Save candidate to database with AI insights
    try:
        logger.info("[DB] Saving candidate to database...")
        # Prepare pros and cons for database
        pros_text = None
        cons_text = None
        status = "Applied"
        
        if ai_analysis:
            # Convert lists to newline-separated strings for database storage
            pros_text = "\n".join(ai_analysis.get('pros', []))
            cons_text = "\n".join(ai_analysis.get('cons', []))
            logger.info(f"   Pros: {len(ai_analysis.get('pros', []))} items")
            logger.info(f"   Cons: {len(ai_analysis.get('cons', []))} items")
            
            # Set initial status based on recommendation
            status = "Applied"
            logger.info(f"   Status set to: {status}")
        
        candidate_id = insert_candidate(
            name=name,
            email=email,
            phone=phone,
            resume_path=filepath,
            parsed_data=parsed_data,
            pros=pros_text,
            cons=cons_text,
            status=status
        )
        logger.info(f"[OK] Candidate saved with ID: {candidate_id}")

        # Save match for the selected job
        if candidate_id and selected_job_info:
            match_conn = None
            try:
                from db_config import get_connection, return_connection
                match_conn = get_connection()
                match_cur = match_conn.cursor()
                match_score = parsed_data.get('match_score', 0)
                ai_reasoning = ai_analysis.get('overall_assessment', '') if ai_analysis else ''
                match_cur.execute("""
                    INSERT INTO candidate_job_matches
                    (candidate_id, job_id, match_score, ai_reasoning)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (candidate_id, job_id)
                    DO UPDATE SET match_score = EXCLUDED.match_score,
                                 ai_reasoning = EXCLUDED.ai_reasoning,
                                 matched_at = NOW()
                """, (candidate_id, int(selected_job_id), match_score, ai_reasoning))
                match_cur.execute("""
                    UPDATE candidates SET best_match_job_id = %s, match_score = %s WHERE id = %s
                """, (int(selected_job_id), match_score, candidate_id))
                match_conn.commit()
                logger.info(f"[MATCH] Saved candidate {candidate_id} -> Job #{selected_job_id} ({selected_job_info['title']}) score={match_score}")
            except Exception as match_err:
                logger.warning(f"[MATCH] Could not save job match: {match_err}")
                if match_conn:
                    with contextlib.suppress(Exception):
                        match_conn.rollback()
            finally:
                if match_conn:
                    with contextlib.suppress(Exception):
                        return_connection(match_conn)
    except Exception as e:
        logger.exception(f"[ERROR] Error saving candidate to database: {e}")
        # Continue anyway - parsing was successful
        candidate_id = None
    
    # Return success response
    # Use the configured upload folder name for consistency
    relative_path = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER']), unique_filename)
    
    logger.info("[RESPONSE] Preparing response data...")
    # Prepare response data
    response_data = {
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
    
    # Add AI analysis if available
    if ai_analysis:
        response_data["ai_analysis"] = {
            "pros": ai_analysis.get('pros', []),
            "cons": ai_analysis.get('cons', []),
            "overall_assessment": ai_analysis.get('overall_assessment', ''),
            "recommendation": ai_analysis.get('recommendation', 'Pending Review'),
            "confidence_score": ai_analysis.get('confidence_score', 0),
            "key_highlights": ai_analysis.get('key_highlights', []),
            "areas_for_improvement": ai_analysis.get('areas_for_improvement', [])
        }
        if 'enhanced_match_score' in ai_analysis:
            response_data["ai_analysis"]["enhanced_match_score"] = ai_analysis['enhanced_match_score']

    # Include selected job info so frontend knows which job was scored against
    if selected_job_info:
        response_data["selected_job"] = {
            "id": selected_job_info['id'],
            "title": selected_job_info['title'],
            "department": selected_job_info.get('department'),
            "required_skills": job_description.get('skills', []),
            "min_experience": job_description.get('min_experience', 0)
        }
    
    logger.info("="*80)
    logger.info("[SUCCESS] RESUME UPLOAD COMPLETED SUCCESSFULLY")
    logger.info(f"   Candidate ID: {candidate_id}")
    logger.info(f"   Name: {name}")
    logger.info(f"   Email: {email}")
    logger.info(f"   Match Score: {parsed_data.get('match_score', 0)}")
    logger.info("="*80)
    
    return jsonify({
        "status": "success",
        "message": "Resume uploaded and analyzed successfully",
        "data": response_data
    }), 200


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
