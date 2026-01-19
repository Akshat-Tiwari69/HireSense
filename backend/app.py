from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import re
from resume_parser import parse_resume

# Initialize Flask app
app = Flask(__name__)

# Enable CORS so frontend can call our APIs
CORS(app)

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
    
    # Return success response
    # Use the configured upload folder name for consistency
    relative_path = os.path.join(os.path.basename(app.config['UPLOAD_FOLDER']), unique_filename)
    return jsonify({
        "status": "success",
        "message": "Resume uploaded and parsed successfully",
        "data": {
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
