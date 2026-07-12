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
import stat
import zipfile
from pathlib import PurePosixPath
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from resume_parser import parse_resume
from resume_analyzer import analyze_resume
from candidate_db import get_candidate_by_email, insert_candidate_application
from db_config import db_connection

logger = logging.getLogger(__name__)

resume_bp = Blueprint('resume', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_FILE_SIZE_MB = 10
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_DOCX_ENTRY_BYTES = 20 * 1024 * 1024
MAX_DOCX_FILES = 2_000
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'


class UploadValidationError(ValueError):
    """Raised when uploaded resume bytes do not match a safe PDF/DOCX file."""


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _validate_pdf_file(filepath):
    file_size = os.path.getsize(filepath)
    if file_size < 10:
        raise UploadValidationError("Uploaded PDF is empty or incomplete")
    with open(filepath, 'rb') as pdf_file:
        header = pdf_file.read(8)
        if not header.startswith(b'%PDF-'):
            raise UploadValidationError("Uploaded file does not have a valid PDF signature")
        pdf_file.seek(max(0, file_size - 4096))
        if b'%%EOF' not in pdf_file.read(4096):
            raise UploadValidationError("Uploaded PDF is incomplete")


def _validate_docx_file(filepath):
    if not zipfile.is_zipfile(filepath):
        raise UploadValidationError("Uploaded file is not a valid DOCX container")

    required_parts = {'[Content_Types].xml', '_rels/.rels', 'word/document.xml'}
    try:
        with zipfile.ZipFile(filepath) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_DOCX_FILES:
                raise UploadValidationError("DOCX contains too many files")

            names = set()
            uncompressed_total = 0
            for info in infos:
                normalized_name = info.filename.replace('\\', '/')
                path = PurePosixPath(normalized_name)
                if (
                    not normalized_name
                    or normalized_name.startswith('/')
                    or '..' in path.parts
                ):
                    raise UploadValidationError("DOCX contains an unsafe file path")
                if normalized_name in names:
                    raise UploadValidationError("DOCX contains duplicate file entries")
                names.add(normalized_name)

                if info.flag_bits & 0x1:
                    raise UploadValidationError("Encrypted DOCX files are not supported")
                mode = (info.external_attr >> 16) & 0xFFFF
                if mode and stat.S_ISLNK(mode):
                    raise UploadValidationError("DOCX must not contain symbolic links")
                if info.is_dir():
                    continue
                if info.file_size > MAX_DOCX_ENTRY_BYTES:
                    raise UploadValidationError("DOCX contains an oversized file entry")
                uncompressed_total += info.file_size
                if uncompressed_total > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise UploadValidationError("DOCX expands beyond the allowed size")

            if not required_parts.issubset(names):
                raise UploadValidationError("DOCX is missing required document parts")
            if corrupt_name := archive.testzip():
                raise UploadValidationError(
                    f"DOCX contains a corrupt file entry: {corrupt_name}"
                )
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise UploadValidationError("Uploaded file is not a valid DOCX container") from exc


def _validate_resume_file(filepath, extension):
    if extension == 'pdf':
        _validate_pdf_file(filepath)
    elif extension == 'docx':
        _validate_docx_file(filepath)
    else:
        raise UploadValidationError("Unsupported resume file type")


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


def _delete_file(filepath):
    """Silently delete a file — used for cleanup when request fails after upload."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError:
        pass


def _get_job_description_for_id(job_id):
    try:
        import json as _json
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, title, department, required_skills, preferred_skills, min_experience "
                "FROM job_descriptions WHERE id = %s AND status = 'active' "
                "AND (closes_at IS NULL OR closes_at > CURRENT_TIMESTAMP)",
                (int(job_id),)
            )
            row = cursor.fetchone()
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

    extension = original_filename.rsplit('.', 1)[1].lower()
    filename_stem = original_filename.rsplit('.', 1)[0]
    unique_filename = f"{uuid.uuid4()}_{filename_stem}.{extension}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, unique_filename)

    selected_job_id = request.form.get('job_id')
    if not selected_job_id:
        return jsonify({"status": "error", "message": "Please select a job position to apply for."}), 400

    job_description, selected_job_info = _get_job_description_for_id(selected_job_id)
    if not job_description:
        return jsonify({"status": "error",
                        "message": "The selected job position is no longer active."}), 400

    try:
        file.save(filepath)
    except OSError as e:
        logger.error(f"[ERROR] OSError saving file: {e}")
        return jsonify({"status": "error", "message": "Failed to save uploaded file."}), 500

    try:
        _validate_resume_file(filepath, extension)
    except UploadValidationError as exc:
        _delete_file(filepath)
        return jsonify({"status": "error", "message": str(exc)}), 400

    logger.info(f"[MATCH] Scoring against: {selected_job_info['title']} (ID: {selected_job_id})")

    try:
        parsed_data = parse_resume(filepath, job_description)

        with open(filepath, 'rb') as f:
            if extension == 'pdf':
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
        _delete_file(filepath)
        return jsonify({
            "status": "error",
            "message": "The resume could not be parsed as a valid PDF or DOCX file.",
        }), 400

    manual_name = request.form.get('name', '').strip()
    manual_email = request.form.get('email', '').strip()
    manual_phone = request.form.get('phone', '').strip()

    name = manual_name or parsed_data.get('name')
    email = manual_email or parsed_data.get('email')
    if isinstance(email, str):
        email = email.strip().lower()
    phone = manual_phone or parsed_data.get('phone') or ""

    if not email or not _is_valid_email(email):
        _delete_file(filepath)
        return jsonify({"status": "error",
                        "message": "Could not detect a valid email in the resume. Please ensure your resume contains a valid email address."}), 400

    if not name:
        name = _name_from_email(email) or "Candidate"

    with contextlib.suppress(Exception):
        if existing := get_candidate_by_email(email):
            _delete_file(filepath)
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
        ai_reasoning = ai_analysis.get('overall_assessment', '') if ai_analysis else ''
        candidate_id = insert_candidate_application(
            name=name, email=email, phone=phone, resume_path=filepath,
            parsed_data=parsed_data, job_id=int(selected_job_id), ai_reasoning=ai_reasoning,
            pros=pros_text, cons=cons_text, status="applied"
        )
    except Exception as e:
        logger.exception(f"[ERROR] Error saving candidate: {e}")
        _delete_file(filepath)
        return jsonify({"status": "error", "message": "Failed to save application. Please try again."}), 500

    if not candidate_id:
        _delete_file(filepath)
        return jsonify({"status": "error", "message": "Failed to save application. Please try again."}), 500

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
