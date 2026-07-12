from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, jwt_required
from dotenv import load_dotenv
import socketio
import os
import logging
from pathlib import Path
from werkzeug.exceptions import HTTPException
from storage_config import get_upload_root

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
from datetime import timedelta
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp
from admin_routes import admin_bp
from proctor_routes import proctor_bp
from job_routes import jobs_bp
from resume_routes import resume_bp
from db_config import get_connection, return_connection
from user_db import get_user_by_id, user_auth_version

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
# The frontend uses Authorization: Bearer. Keeping a second cookie-based JWT
# path would require CSRF tokens on every mutation and creates inconsistent auth.
app.config['JWT_TOKEN_LOCATION'] = ['headers']
jwt = JWTManager(app)
app.config.setdefault('JWT_SKIP_USER_VERSION_CHECK', False)


def _is_staff_token_revoked(jwt_payload):
    """Fail closed when a staff account changed or disappeared after login."""
    try:
        user = get_user_by_id(jwt_payload.get('sub'))
        if not user:
            return True
        if user.get('role') != jwt_payload.get('role'):
            return True
        issued_version = jwt_payload.get('user_auth_version')
        return not issued_version or issued_version != user_auth_version(user)
    except Exception:
        logger.exception("Unable to validate the current JWT user state")
        return True


@jwt.token_in_blocklist_loader
def staff_token_revocation_callback(_jwt_header, jwt_payload):
    if app.config.get('JWT_SKIP_USER_VERSION_CHECK'):
        return False
    return _is_staff_token_revoked(jwt_payload)


@jwt.revoked_token_loader
def revoked_token_callback(_jwt_header, _jwt_payload):
    return jsonify({
        'status': 'error',
        'message': 'Your account or permissions changed. Please login again.'
    }), 401

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

# Configure CORS from one environment variable instead of machine-specific IPs.
cors_origins = [
    origin.strip()
    for origin in os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:5173,http://localhost:5174,http://localhost:3000'
    ).split(',')
    if origin.strip()
]
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": ["Content-Type", "Authorization", "X-Assessment-Token"],
        "supports_credentials": False
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

# Ensure the shared upload root exists. Production deployments should point
# UPLOAD_FOLDER at a persistent mounted volume or durable storage adapter.
UPLOAD_FOLDER = str(get_upload_root(create=True))
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


@app.errorhandler(HTTPException)
def handle_http_error(error):
    """Keep framework-level failures on the same JSON contract as API routes."""
    return jsonify({
        'status': 'error',
        'message': error.description,
    }), error.code


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Return a safe response while retaining the full exception in server logs."""
    logger.exception("Unhandled request error", exc_info=error)
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
    }), 500






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
    """Serve uploaded PII only to recruiting roles."""
    if get_jwt().get('role') not in {
        'interviewer', 'recruiter', 'sector_admin', 'admin', 'super_admin'
    }:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "File not found"}), 404


@app.route('/api/health', methods=['GET'])
def health_check():
    """Liveness check: verifies that the API process can serve requests."""
    return jsonify({"status": "ok"})


@app.route('/api/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check: verifies that the required PostgreSQL dependency is reachable."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        return jsonify({'status': 'ready', 'database': 'ok'}), 200
    except Exception:
        logger.warning("Readiness check failed: database unavailable", exc_info=True)
        return jsonify({'status': 'not_ready', 'database': 'unavailable'}), 503
    finally:
        if conn:
            return_connection(conn)
