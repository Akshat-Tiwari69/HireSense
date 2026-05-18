"""
Resume upload routes — candidate application entry point.
Handles file upload, AI parsing, and candidate creation.
Registered in app.py at url_prefix='/api'.
"""

import os
import re
import uuid
import logging
import contextlib
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from resume_parser import parse_resume
from resume_analyzer import analyze_resume
from db_helpers import insert_candidate, get_candidate_by_email
from db_config import get_connection, return_connection

logger = logging.getLogger(__name__)

resume_bp = Blueprint('resume', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE_MB = 10
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _is_valid_email(email):
    if not email or not isinstance(email, str) or not email.strip():
        return False
    return bool(re.match(EMAIL_PATTERN, email))


def _name_from_email(email):
    if not email or '@' not in email:
        return None
    local = email.split('@', 1)[0]
    parts = re.split(r'[._-]+', local)
    parts = [p for p in parts if p]
    return " ".join(p.capitalize() for p in parts) if parts else None


def _get_job_description_for_id(job_id):
    try:
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
            job_info = {'id': row[0], 'title': row[1], 'department': row[2]}
            return {'skills': list(skills), 'min_experience': row[5] or 0,
                    'title': row[1], 'department': row[2]}, job_info
    except Exception as e:
        logger.warning(f"[MATCH] Could not load job posting {job_id}: {e}")
    return None, None


@resume_bp.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        "status": "error",
        "message": f"File size exceeds the maximum allowed limit of {MAX_FILE_SIZE_MB}MB"
    }), 413


@resume_bp.route('/resume/upload', methods=['POST'])
def upload_resume():
    logger.info("[UPLOAD] RESUME UPLOAD REQUEST RECEIVED")

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 400
    if not _allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file type. Only PDF and DOCX allowed"}), 400

    original_filename = secure_filename(file.filename)
    if not original_filename or "." not in original_filename:
        return jsonify({"status": "error", "message": "Invalid filename after sanitization"}), 400

    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, unique_filename)

    try:
        file.save(filepath)
    except OSError as e:
        logger.error(f"[ERROR] OSError saving file: {e}")
        return jsonify({"status": "error", "message": "Failed to save uploaded file."}), 500

    selected_job_id = request.form.get('job_id')
    if not selected_job_id:
        return jsonify({"status": "error", "message": "Please select a job position to apply for."}), 400

    job_description, selected_job_info = _get_job_description_for_id(selected_job_id)
    if not job_description:
        return jsonify({"status": "error",
                        "message": "The selected job position is no longer active."}), 400

    logger.info(f"[MATCH] Scoring against: {selected_job_info['title']} (ID: {selected_job_id})")

    try:
        parsed_data = parse_resume(filepath, job_description)

        with open(filepath, 'rb') as f:
            if filepath.endswith('.pdf'):
                from PyPDF2 import PdfReader
                pdf = PdfReader(f)
                resume_text = " ".join([page.extract_text() or '' for page in pdf.pages])
            else:
                from docx import Document
                doc = Document(f)
                resume_text = " ".join([para.text for para in doc.paragraphs])

        try:
            from resume_analyzer import ResumeAnalyzer
            analyzer = ResumeAnalyzer()
            if ai_extracted_data := analyzer.extract_resume_data(resume_text):
                for field in ('skills', 'education', 'name', 'email', 'phone'):
                    if ai_extracted_data.get(field):
                        parsed_data[field] = ai_extracted_data[field]
                if ai_extracted_data.get('experience', 0) > 0:
                    parsed_data['experience'] = ai_extracted_data['experience']
                from resume_parser import calculate_match_score
                parsed_data['match_score'] = calculate_match_score(
                    parsed_data.get('skills', []), parsed_data.get('experience', 0),
                    job_description.get('skills', []), job_description.get('min_experience', 0)
                )
        except Exception as e:
            logger.warning(f"[WARNING] AI extraction failed: {e}")

        ai_analysis = None
        try:
            ai_analysis = analyze_resume(
                resume_text=resume_text, parsed_data=parsed_data,
                job_requirements=job_description, enhance_score=True
            )
            if 'enhanced_match_score' in ai_analysis:
                parsed_data['match_score'] = ai_analysis['enhanced_match_score']
        except Exception as e:
            logger.warning(f"[WARNING] AI analysis failed: {e}")
            ai_analysis = {
                "pros": ["Resume uploaded successfully"],
                "cons": ["AI analysis unavailable - manual review recommended"],
                "overall_assessment": "AI analysis failed. Manual review required.",
                "recommendation": "Pending Review", "confidence_score": 0
            }

    except Exception as e:
        logger.exception(f"[ERROR] Error parsing resume: {e}")
        parsed_data = {"error": "Failed to parse resume", "skills": [], "experience": 0,
                       "education": "Not Specified", "match_score": 0, "shortlist_status": "Pending Review"}
        ai_analysis = None

    manual_name = request.form.get('name', '').strip()
    manual_email = request.form.get('email', '').strip()
    manual_phone = request.form.get('phone', '').strip()

    name = manual_name or parsed_data.get('name')
    email = manual_email or parsed_data.get('email')
    phone = manual_phone or parsed_data.get('phone') or ""

    if not email or not _is_valid_email(email):
        return jsonify({"status": "error",
                        "message": "Could not detect a valid email in the resume. Please ensure your resume contains a valid email address."}), 400

    if not name:
        name = _name_from_email(email) or "Candidate"

    with contextlib.suppress(Exception):
        if existing := get_candidate_by_email(email):
            return jsonify({
                "status": "error",
                "message": f"You have already registered with this email address ({email}).",
                "existing_candidate": {
                    "name": existing['name'], "status": existing['status'],
                    "registered_at": str(existing['created_at']) if existing['created_at'] else None
                }
            }), 409

    candidate_id = None
    try:
        pros_text = "\n".join(ai_analysis.get('pros', [])) if ai_analysis else None
        cons_text = "\n".join(ai_analysis.get('cons', [])) if ai_analysis else None

        candidate_id = insert_candidate(
            name=name, email=email, phone=phone, resume_path=filepath,
            parsed_data=parsed_data, pros=pros_text, cons=cons_text, status="Applied"
        )

        if candidate_id and selected_job_info:
            match_conn = None
            try:
                match_conn = get_connection()
                match_cur = match_conn.cursor()
                match_score = parsed_data.get('match_score', 0)
                ai_reasoning = ai_analysis.get('overall_assessment', '') if ai_analysis else ''
                match_cur.execute("""
                    INSERT INTO candidate_job_matches (candidate_id, job_id, match_score, ai_reasoning)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (candidate_id, job_id)
                    DO UPDATE SET match_score = EXCLUDED.match_score,
                                 ai_reasoning = EXCLUDED.ai_reasoning, matched_at = NOW()
                """, (candidate_id, int(selected_job_id), match_score, ai_reasoning))
                match_cur.execute(
                    "UPDATE candidates SET best_match_job_id = %s, match_score = %s WHERE id = %s",
                    (int(selected_job_id), match_score, candidate_id)
                )
                match_conn.commit()
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
        logger.exception(f"[ERROR] Error saving candidate: {e}")

    relative_path = os.path.join(os.path.basename(upload_folder), unique_filename)
    response_data = {
        "candidate_id": candidate_id,
        "file_path": relative_path,
        "original_filename": original_filename,
        "candidate": {"name": name, "email": email, "phone": phone},
        "parsed_data": parsed_data
    }
    if ai_analysis:
        response_data["ai_analysis"] = {
            "pros": ai_analysis.get('pros', []), "cons": ai_analysis.get('cons', []),
            "overall_assessment": ai_analysis.get('overall_assessment', ''),
            "recommendation": ai_analysis.get('recommendation', 'Pending Review'),
            "confidence_score": ai_analysis.get('confidence_score', 0),
            "key_highlights": ai_analysis.get('key_highlights', []),
            "areas_for_improvement": ai_analysis.get('areas_for_improvement', [])
        }
        if 'enhanced_match_score' in ai_analysis:
            response_data["ai_analysis"]["enhanced_match_score"] = ai_analysis['enhanced_match_score']
    if selected_job_info:
        response_data["selected_job"] = {
            "id": selected_job_info['id'], "title": selected_job_info['title'],
            "department": selected_job_info.get('department'),
            "required_skills": job_description.get('skills', []),
            "min_experience": job_description.get('min_experience', 0)
        }

    logger.info(f"[SUCCESS] Resume uploaded — Candidate ID: {candidate_id}, Name: {name}, Score: {parsed_data.get('match_score', 0)}")
    return jsonify({"status": "success", "message": "Resume uploaded and analyzed successfully",
                    "data": response_data}), 200
