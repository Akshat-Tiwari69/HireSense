from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid

# Initialize Flask app
app = Flask(__name__)

# Enable CORS so frontend can call our APIs
CORS(app)

# Ensure uploads folder exists
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions for resume upload
ALLOWED_EXTENSIONS = {'pdf', 'docx'}


def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    
    # Generate unique filename to prevent conflicts
    original_filename = secure_filename(file.filename)
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
    
    # Return success response
    return jsonify({
        "status": "success",
        "message": "Resume uploaded successfully",
        "data": {
            "file_path": f"uploads/{unique_filename}",
            "original_filename": original_filename,
            "candidate": {
                "name": name,
                "email": email,
                "phone": phone
            }
        }
    }), 201


if __name__ == '__main__':
    app.run(debug=True, port=5000)
