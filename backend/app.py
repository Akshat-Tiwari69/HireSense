# IMPORTANT: eventlet monkey_patch MUST be first, before any other imports
import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import socketio
import os
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
from db_helpers import update_candidate_status
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp
from admin_routes import admin_bp
from proctor_routes import proctor_bp
from job_routes import jobs_bp
from resume_routes import resume_bp
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
# Accept JWT from both HttpOnly cookie AND Authorization header so the browser
# gets the cookie automatically while API clients can still use Bearer tokens.
app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
app.config['JWT_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # CORS + SameSite=Lax is sufficient for non-state-changing GETs; enable CSRF protection for mutations once frontend is ready
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
        "allow_headers": ["Content-Type", "Authorization", "X-Assessment-Token"],
        "supports_credentials": True
    }
})

# Initialize Socket.IO for live proctoring
from websocket_server import get_socketio_app, init_websocket_server
sio = get_socketio_app()
init_websocket_server(app)  # give websocket server access to app context for JWT decode
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
@jwt_required()
def serve_uploaded_file(filename):
    """Serve uploaded files — requires a valid JWT to prevent unauthenticated PII access."""
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
    """REMOVED: Use /api/interviewee/assessment/start-by-token/<token> instead."""
    return jsonify({
        "status": "error",
        "message": "This endpoint has been removed. Use /api/interviewee/assessment/start-by-token/<token>"
    }), 410


@app.route('/api/assessment/mcq/submit', methods=['POST'])
def submit_mcq():
    """REMOVED: Use /api/interviewee/assessment/<id>/submit-answer instead."""
    return jsonify({
        "status": "error",
        "message": "This endpoint has been removed. Use /api/interviewee/assessment/<id>/submit-answer"
    }), 410


@app.route('/api/assessment/code/submit', methods=['POST'])
def submit_code():
    """REMOVED: Use /api/interviewee/assessment/<id>/submit-answer instead."""
    return jsonify({
        "status": "error",
        "message": "This endpoint has been removed. Use /api/interviewee/assessment/<id>/submit-answer"
    }), 410


@app.route('/api/assessment/psychometric/submit', methods=['POST'])
def submit_psychometric():
    """REMOVED: Use /api/interviewee/assessment/<id>/submit-answer instead."""
    return jsonify({
        "status": "error",
        "message": "This endpoint has been removed. Use /api/interviewee/assessment/<id>/submit-answer"
    }), 410


@app.route('/api/assessment/complete', methods=['POST'])
def complete_assessment():
    """REMOVED: Use /api/interviewee/assessment/<id>/complete instead."""
    return jsonify({
        "status": "error",
        "message": "This endpoint has been removed. Use /api/interviewee/assessment/<id>/complete"
    }), 410


if __name__ == '__main__':
    # Run with Socket.IO WSGI app
    import eventlet.wsgi
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app_with_socketio)
