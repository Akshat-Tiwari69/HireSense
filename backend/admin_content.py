"""
Admin content routes — bulk resume upload, AI text enhancement, and custom question banks.
"""

import os
import re
import uuid
import json as _json
import zipfile
import tempfile
import shutil
import contextlib
import logging
try:
    import rarfile
    RAR_SUPPORTED = True
except ImportError:
    RAR_SUPPORTED = False
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename
from db_config import get_connection, return_connection
from db_helpers import insert_candidate, get_candidate_by_email
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_content_bp = Blueprint('admin_content', __name__)

ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx'}
EMAIL_PATTERN_BULK = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
MAX_BULK_WORKERS = 8


# ============================================================================
#                        BULK UPLOAD HELPERS
# ============================================================================

def _bulk_valid_email(email):
    if email is None or not isinstance(email, str) or not email.strip():
        return False
    return re.match(EMAIL_PATTERN_BULK, email) is not None


def _bulk_name_from_email(email):
    if not email or '@' not in email:
        return None
    local = email.split('@', 1)[0]
    parts = re.split(r'[._-]+', local)
    parts = [p for p in parts if p]
    return " ".join(p.capitalize() for p in parts) if parts else None


def _merge_ai_data_to_parsed(parsed_data, ai_data):
    if ai_data.get('skills'):
        parsed_data['skills'] = ai_data['skills']
    if ai_data.get('experience') and ai_data['experience'] > 0:
        parsed_data['experience'] = ai_data['experience']
    if ai_data.get('education'):
        parsed_data['education'] = ai_data['education']
    if ai_data.get('name'):
        parsed_data['name'] = ai_data['name']
    if ai_data.get('email'):
        parsed_data['email'] = ai_data['email']
    if ai_data.get('phone'):
        parsed_data['phone'] = ai_data['phone']


def _get_db_cursor():
    conn = get_connection()
    return conn, conn.cursor()


def _save_candidate_job_match(candidate_id, job_id, match_score, ai_reasoning):
    match_conn, match_cur = _get_db_cursor()
    try:
        match_cur.execute("""
            INSERT INTO candidate_job_matches
            (candidate_id, job_id, match_score, ai_reasoning)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (candidate_id, job_id)
            DO UPDATE SET match_score = EXCLUDED.match_score,
                         ai_reasoning = EXCLUDED.ai_reasoning,
                         matched_at = NOW()
        """, (candidate_id, int(job_id), match_score, ai_reasoning))
        match_cur.execute("""
            UPDATE candidates SET best_match_job_id = %s, match_score = %s WHERE id = %s
        """, (int(job_id), match_score, candidate_id))
        match_conn.commit()
    except Exception as match_err:
        logger.warning(f"Could not save job match for candidate {candidate_id}: {match_err}")
        with contextlib.suppress(Exception):
            match_conn.rollback()
    finally:
        with contextlib.suppress(Exception):
            return_connection(match_conn)


def _fetch_job_for_bulk(job_id):
    try:
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
        logger.warning(f"[BULK] Could not load job posting {job_id}: {e}")
    return None, None


def _process_single_resume(filepath, filename, job_description, job_info, job_id, upload_folder):
    from resume_parser import parse_resume, calculate_match_score
    from resume_analyzer import analyze_resume, ResumeAnalyzer

    result = {
        'filename': filename, 'status': 'error',
        'name': None, 'email': None, 'match_score': 0,
        'recommendation': None, 'candidate_id': None,
        'error': None, 'missing': []
    }

    try:
        parsed_data = parse_resume(filepath, job_description)

        with open(filepath, 'rb') as f:
            if filepath.lower().endswith('.pdf'):
                from PyPDF2 import PdfReader
                pdf = PdfReader(f)
                resume_text = " ".join([page.extract_text() or '' for page in pdf.pages])
            else:
                from docx import Document
                doc = Document(f)
                resume_text = " ".join([para.text for para in doc.paragraphs])

        if not resume_text or len(resume_text.strip()) < 50:
            result['missing'] = ['name', 'email']
            name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title() or 'Unknown Candidate'
            email = f'unknown-{uuid.uuid4().hex[:12]}@bulk-upload.local'
            try:
                candidate_id = insert_candidate(
                    name=name, email=email, phone='',
                    resume_path=filepath,
                    parsed_data={'skills': [], 'experience': 0, 'education': '', 'match_score': 0, 'shortlist_status': 'Pending Review'},
                    pros=None, cons=None, status='Absence of Details'
                )
                result.update({'status': 'success', 'name': name, 'email': email, 'candidate_id': candidate_id,
                                'error': 'Could not extract text — saved with Absence of Details'})
            except Exception as save_err:
                result['error'] = f'Could not extract text and save failed: {save_err}'
            return result

        try:
            analyzer = ResumeAnalyzer()
            if ai_data := analyzer.extract_resume_data(resume_text):
                _merge_ai_data_to_parsed(parsed_data, ai_data)
                parsed_data['match_score'] = calculate_match_score(
                    parsed_data.get('skills', []), parsed_data.get('experience', 0),
                    job_description.get('skills', []), job_description.get('min_experience', 0)
                )
        except Exception as ai_err:
            logger.warning(f"[BULK] AI extraction failed for {filename}: {ai_err}")

        ai_analysis = None
        try:
            ai_analysis = analyze_resume(
                resume_text=resume_text, parsed_data=parsed_data,
                job_requirements=job_description, enhance_score=True
            )
            if ai_analysis and 'enhanced_match_score' in ai_analysis:
                parsed_data['match_score'] = ai_analysis['enhanced_match_score']
        except Exception as ai_err:
            logger.warning(f"[BULK] AI analysis failed for {filename}: {ai_err}")
            ai_analysis = {
                "pros": ["Resume uploaded successfully"],
                "cons": ["AI analysis unavailable - manual review recommended"],
                "overall_assessment": "AI analysis failed. Manual review required.",
                "recommendation": "Pending Review", "confidence_score": 0
            }

        name = parsed_data.get('name')
        email = parsed_data.get('email')
        phone = parsed_data.get('phone', '')

        missing_details = []
        if not name:
            missing_details.append('name')
        if not email or not _bulk_valid_email(email):
            missing_details.append('email')

        if not email or not _bulk_valid_email(email):
            email = f'unknown-{uuid.uuid4().hex[:12]}@bulk-upload.local'

        if not name:
            name = _bulk_name_from_email(email)
            if not name or 'unknown' in name.lower():
                name = os.path.splitext(filename)[0].replace('_', ' ').replace('-', ' ').title() or 'Unknown Candidate'

        candidate_status = 'Absence of Details' if missing_details else 'Applied'
        result['name'] = name
        result['email'] = email
        result['match_score'] = parsed_data.get('match_score', 0)
        result['recommendation'] = ai_analysis.get('recommendation', 'Pending Review') if ai_analysis else 'Pending Review'
        result['missing'] = missing_details

        if not email.endswith('@bulk-upload.local'):
            with contextlib.suppress(Exception):
                if existing := get_candidate_by_email(email):
                    result.update({'status': 'duplicate', 'candidate_id': existing['id'],
                                   'error': f'Already registered (ID: {existing["id"]})'})
                    return result

        pros_text = "\n".join(ai_analysis.get('pros', [])) if ai_analysis else None
        cons_text = "\n".join(ai_analysis.get('cons', [])) if ai_analysis else None

        candidate_id = insert_candidate(
            name=name, email=email, phone=phone or '',
            resume_path=filepath, parsed_data=parsed_data,
            pros=pros_text, cons=cons_text, status=candidate_status
        )
        result['candidate_id'] = candidate_id

        if candidate_id:
            _save_candidate_job_match(candidate_id, job_id, parsed_data.get('match_score', 0),
                                      ai_analysis.get('overall_assessment', '') if ai_analysis else '')

        result['status'] = 'success'
        if missing_details:
            result['error'] = f'Saved with Absence of Details (missing: {", ".join(missing_details)})'
        logger.info(f"[BULK] Processed {filename} -> {name} <{email}> score={result['match_score']} status={candidate_status}")

    except Exception as e:
        result['error'] = str(e)
        logger.error(f"[BULK] Error processing {filename}: {e}")

    return result


# ============================================================================
#                        QUESTION BANK HELPERS
# ============================================================================

def _extract_text_from_file(filepath):
    text = ""
    if filepath.lower().endswith('.pdf'):
        from PyPDF2 import PdfReader
        with open(filepath, 'rb') as f:
            pdf = PdfReader(f)
            for page in pdf.pages:
                if page_text := page.extract_text():
                    text += page_text + "\n"
    elif filepath.lower().endswith('.docx'):
        from docx import Document
        doc = Document(filepath)
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text += cell.text + "\n"
    return text.strip()


def _parse_questions_from_text(text):
    questions = []

    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY not configured')

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except TypeError:
            import httpx
            proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            http_client = httpx.Client(proxies=proxy) if proxy else httpx.Client()
            from openai import OpenAI
            client = OpenAI(api_key=api_key, http_client=http_client)

        truncated = text[:12000] if len(text) > 12000 else text

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are an expert at parsing assessment questions from documents.
Extract ALL questions from the given text. For each question, identify:
- The question text
- The options (if multiple-choice)
- The correct answer (if indicated, otherwise null)
- A category/topic tag
- Difficulty level (easy/medium/hard)

Return a JSON array. Each element:
{
  "question": "...",
  "options": ["A", "B", "C", "D"] or null if not MCQ,
  "correct_answer": "..." or null,
  "category": "topic",
  "difficulty": "medium"
}

If the document contains free-form questions (not MCQ), still include them with options=null.
Return ONLY valid JSON, no markdown."""},
                {"role": "user", "content": f"Parse all questions from this document:\n\n{truncated}"}
            ],
            temperature=0.2,
            max_tokens=4000
        )
        import json
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        questions = json.loads(content)
        logger.info(f"[CUSTOM QB] AI parsed {len(questions)} questions from uploaded document")
        return questions
    except Exception as ai_err:
        logger.warning(f"[CUSTOM QB] AI parsing failed: {ai_err}, falling back to regex")

    q_pattern = re.compile(r'(?:^|\n)\s*(\d+)\s*[.)]\s*(.+?)(?=\n\s*\d+\s*[.)]|\n*$)', re.DOTALL)
    matches = q_pattern.findall(text)
    for num, q_text in matches:
        q_text = q_text.strip()
        if len(q_text) > 15:
            questions.append({'question': q_text, 'options': None, 'correct_answer': None,
                              'category': 'custom', 'difficulty': 'medium'})

    if not questions:
        for line in text.split('\n'):
            line = line.strip()
            if line.endswith('?') and len(line) > 20:
                questions.append({'question': line, 'options': None, 'correct_answer': None,
                                  'category': 'custom', 'difficulty': 'medium'})

    logger.info(f"[CUSTOM QB] Regex parsed {len(questions)} questions from uploaded document")
    return questions


# ============================================================================
#                        ROUTES
# ============================================================================

@admin_content_bp.route('/bulk-upload', methods=['POST'])
@jwt_required()
@require_admin_role
def bulk_upload_resumes():
    logger.info("[BULK] BULK RESUME UPLOAD REQUEST RECEIVED")

    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    archive_file = request.files['file']
    fname = (archive_file.filename or '').lower()
    if not fname.endswith('.zip') and not fname.endswith('.rar'):
        return jsonify({'status': 'error', 'message': 'Please upload a .zip or .rar file'}), 400
    if fname.endswith('.rar') and not RAR_SUPPORTED:
        return jsonify({'status': 'error', 'message': 'RAR support not available. Please upload a .zip file.'}), 400
    is_rar = fname.endswith('.rar')

    job_id = request.form.get('job_id')
    if not job_id:
        return jsonify({'status': 'error', 'message': 'Please select a job position'}), 400

    job_description, job_info = _fetch_job_for_bulk(job_id)
    if not job_description:
        return jsonify({'status': 'error', 'message': 'Selected job is no longer active'}), 400

    logger.info(f"[BULK] Target job: {job_info['title']} (ID: {job_id})")

    temp_dir = tempfile.mkdtemp(prefix='bulk_upload_')
    extract_dir = os.path.join(temp_dir, 'resumes')
    os.makedirs(extract_dir, exist_ok=True)
    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    try:
        archive_path = os.path.join(temp_dir, 'upload.rar' if is_rar else 'upload.zip')
        archive_file.save(archive_path)
        resume_files = []

        def _collect_resume_files(base_dir):
            for root, _dirs, files in os.walk(base_dir):
                for fname in files:
                    if '__MACOSX' in root or fname.startswith('.'):
                        continue
                    ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
                    if ext not in ALLOWED_RESUME_EXTENSIONS:
                        continue
                    rel_path = os.path.relpath(os.path.join(root, fname), base_dir)
                    parent_dir = os.path.basename(os.path.dirname(rel_path))
                    display_name = f"{parent_dir}/{fname}" if parent_dir and parent_dir != '.' else fname
                    safe_name = secure_filename(fname)
                    unique_name = f"{uuid.uuid4()}_{safe_name}"
                    perm_path = os.path.join(upload_folder, unique_name)
                    shutil.copy2(os.path.join(root, fname), perm_path)
                    resume_files.append((perm_path, display_name))

        if is_rar:
            import subprocess as _sp
            _unrar_candidates = [
                r'C:\Program Files\WinRAR\UnRAR.exe',
                r'C:\Program Files (x86)\WinRAR\UnRAR.exe',
                'unrar', 'UnRAR',
            ]
            if RAR_SUPPORTED and getattr(rarfile, 'UNRAR_TOOL', None):
                _unrar_candidates.insert(0, rarfile.UNRAR_TOOL)

            rar_extract_dir = os.path.join(temp_dir, 'rar_extracted')
            os.makedirs(rar_extract_dir, exist_ok=True)
            proc = None
            for _tool in _unrar_candidates:
                try:
                    proc = _sp.run(
                        [_tool, 'x', '-o+', '-y', archive_path, rar_extract_dir + os.sep],
                        capture_output=True, timeout=120
                    )
                    if proc.returncode == 0:
                        break
                except OSError:
                    continue
            if proc is None or proc.returncode != 0:
                err_msg = proc.stderr.decode(errors='replace') if proc else 'unrar not found'
                logger.error(f"[BULK] unrar failed: {err_msg}")
                return jsonify({'status': 'error',
                                'message': 'Failed to extract RAR file. Please use a .zip file instead.'}), 400
            _collect_resume_files(rar_extract_dir)
        else:
            zip_extract_dir = os.path.join(temp_dir, 'zip_extracted')
            os.makedirs(zip_extract_dir, exist_ok=True)
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(zip_extract_dir)
            _collect_resume_files(zip_extract_dir)

        if not resume_files:
            return jsonify({'status': 'error', 'message': 'No PDF or DOCX files found in the archive'}), 400

        total = len(resume_files)
        logger.info(f"[BULK] Found {total} resume files. Starting parallel processing with {MAX_BULK_WORKERS} workers...")

        results = []
        with ThreadPoolExecutor(max_workers=MAX_BULK_WORKERS) as executor:
            future_map = {
                executor.submit(_process_single_resume, filepath, original_name,
                                job_description, job_info, job_id, upload_folder): original_name
                for filepath, original_name in resume_files
            }
            for future in as_completed(future_map):
                try:
                    results.append(future.result(timeout=120))
                except Exception as exc:
                    results.append({
                        'filename': future_map[future], 'status': 'error', 'error': str(exc),
                        'name': None, 'email': None, 'match_score': 0,
                        'recommendation': None, 'candidate_id': None
                    })

        success = [r for r in results if r['status'] == 'success']
        duplicates = [r for r in results if r['status'] == 'duplicate']
        errors = [r for r in results if r['status'] == 'error']

        logger.info(f"[BULK] COMPLETE: {len(success)} success, {len(duplicates)} duplicates, {len(errors)} errors out of {total}")

        return jsonify({
            'status': 'success',
            'message': f'Processed {total} resumes: {len(success)} added, {len(duplicates)} duplicates, {len(errors)} failed',
            'summary': {
                'total': total, 'success': len(success), 'duplicates': len(duplicates), 'errors': len(errors),
                'job': {'id': job_info['id'], 'title': job_info['title'], 'department': job_info.get('department')}
            },
            'results': sorted(results, key=lambda r: r.get('match_score', 0), reverse=True)
        })

    except zipfile.BadZipFile:
        return jsonify({'status': 'error', 'message': 'Invalid or corrupted archive file'}), 400
    except Exception as e:
        logger.exception(f"[BULK] Unexpected error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        with contextlib.suppress(Exception):
            shutil.rmtree(temp_dir, ignore_errors=True)


@admin_content_bp.route('/ai-enhance', methods=['POST'])
@jwt_required()
@require_admin_role
def ai_enhance_text():
    data = request.get_json(force=True)
    text_type = data.get('type', 'job')
    title = data.get('title') or ''
    description = data.get('description') or ''

    if isinstance(title, dict):
        title = ' '.join(str(v) for v in title.values())
    if isinstance(description, dict):
        parts = []
        for key, val in description.items():
            heading = key.replace('_', ' ').title()
            if isinstance(val, list):
                val = '\n'.join(f'- {item}' for item in val)
            parts.append(f"{heading}:\n{val}")
        description = '\n\n'.join(parts)
    elif isinstance(description, list):
        description = '\n'.join(str(item) for item in description)

    title = str(title).strip()
    description = str(description).strip()

    if not title and not description:
        return jsonify({'status': 'error', 'message': 'Provide at least a title or description to enhance'}), 400

    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'status': 'error', 'message': 'OpenAI API key not configured'}), 500

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except TypeError:
            import httpx
            proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
            http_client = httpx.Client(proxies=proxy) if proxy else httpx.Client()
            from openai import OpenAI
            client = OpenAI(api_key=api_key, http_client=http_client)

        if text_type == 'sector':
            system_msg = (
                "You are a corporate branding specialist. The user will give you a sector/department name and description. "
                "Polish them to sound professional and clear. Keep it concise. "
                "Return JSON with keys: enhanced_title (string), enhanced_description (single plain-text string, not nested). No markdown fences."
            )
            user_msg = f"Sector name: {title}\nDescription: {description}"
        else:
            system_msg = (
                "You are a senior HR copywriter at a leading company based in India. "
                "The user will give you a job title and description draft. "
                "Polish the title to be industry-standard (concise, clear seniority). "
                "Rewrite the description to focus ONLY on: a brief overview of the role, key responsibilities, and what is expected day-to-day. "
                "Use bullet points for responsibilities. Make it compelling and professional. "
                "Do NOT include qualifications, experience requirements, education/degree requirements, or salary in the description — the recruiter fills those separately. "
                "From the description, extract ONLY concrete, domain-specific skills relevant to the job title. "
                "For tech roles these would be tools/frameworks/languages (e.g. React, Python, AWS, Docker, PostgreSQL). "
                "For non-tech roles these would be domain expertise areas (e.g. Contract Law, Corporate Governance, Financial Modelling, Supply Chain Management, Talent Acquisition). "
                "Do NOT list soft skills or vague abilities like 'communication', 'problem solving', 'team management', 'leadership' as skills — those belong in the description. "
                "Every skill must be in Title Case. "
                "Split them into required_skills and preferred_skills (comma-separated strings). "
                "Return JSON with keys: enhanced_title (string), enhanced_description (plain-text string, responsibilities only), "
                "required_skills (comma-separated string of must-have domain skills), preferred_skills (comma-separated string of nice-to-have domain skills). "
                "No markdown fences."
            )
            user_msg = f"Job title: {title}\nDescription draft: {description}"

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': user_msg}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[-1].rsplit('```', 1)[0].strip()

        import json as _j
        result = _j.loads(raw)

        enhanced_title = result.get('enhanced_title', title)
        enhanced_desc = result.get('enhanced_description', description)

        if isinstance(enhanced_title, dict):
            enhanced_title = str(enhanced_title)
        if isinstance(enhanced_desc, dict):
            parts = []
            for key, val in enhanced_desc.items():
                heading = key.replace('_', ' ').title()
                if isinstance(val, list):
                    val = '\n'.join(f'- {item}' for item in val)
                parts.append(f"{heading}:\n{val}")
            enhanced_desc = '\n\n'.join(parts)
        elif isinstance(enhanced_desc, list):
            enhanced_desc = '\n'.join(str(item) for item in enhanced_desc)

        required_skills = result.get('required_skills', '')
        preferred_skills = result.get('preferred_skills', '')
        if isinstance(required_skills, list):
            required_skills = ', '.join(str(s) for s in required_skills)
        if isinstance(preferred_skills, list):
            preferred_skills = ', '.join(str(s) for s in preferred_skills)

        def _title_case_skills(skills_str):
            if not skills_str:
                return ''
            return ', '.join(s.strip().title() for s in str(skills_str).split(',') if s.strip())

        resp = {
            'status': 'success',
            'enhanced_title': str(enhanced_title),
            'enhanced_description': str(enhanced_desc)
        }
        if text_type == 'job':
            resp['required_skills'] = _title_case_skills(required_skills)
            resp['preferred_skills'] = _title_case_skills(preferred_skills)

        return jsonify(resp)

    except Exception as e:
        logger.error(f"[AI ENHANCE] Failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_content_bp.route('/question-bank/upload', methods=['POST'])
@jwt_required()
def upload_question_bank():
    try:
        claims = get_jwt()
        if claims.get('role', '') not in ('admin', 'super_admin', 'interviewer'):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ('pdf', 'docx'):
            return jsonify({'status': 'error', 'message': 'Only PDF and DOCX files allowed'}), 400

        description = request.form.get('description', '')
        tags = request.form.get('tags', '')

        upload_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'question_banks')
        os.makedirs(upload_dir, exist_ok=True)
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)

        questions_text = _extract_text_from_file(filepath)
        if not questions_text or len(questions_text.strip()) < 30:
            os.remove(filepath)
            return jsonify({'status': 'error', 'message': 'Could not extract any text from the file.'}), 400

        parsed_questions = _parse_questions_from_text(questions_text)

        user_id = int(get_jwt_identity())
        conn = get_connection()
        cur = conn.cursor()
        import json
        cur.execute("""
            INSERT INTO custom_question_bank
            (filename, original_filename, file_path, questions_text, parsed_questions, uploaded_by, description, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (unique_filename, file.filename, filepath,
              questions_text, json.dumps(parsed_questions),
              user_id, description, tags))
        qb_id = cur.fetchone()[0]
        conn.commit()
        return_connection(conn)

        logger.info(f"[CUSTOM QB] Uploaded question bank #{qb_id}: {file.filename} ({len(parsed_questions)} questions parsed)")

        return jsonify({
            'status': 'success',
            'message': f'Uploaded successfully — {len(parsed_questions)} questions parsed',
            'data': {
                'id': qb_id, 'filename': file.filename,
                'questions_count': len(parsed_questions),
                'parsed_questions': parsed_questions[:3],
                'raw_text_length': len(questions_text)
            }
        }), 201

    except Exception as e:
        logger.error(f"[CUSTOM QB] Upload failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_content_bp.route('/question-bank', methods=['GET'])
@jwt_required()
def list_question_banks():
    try:
        claims = get_jwt()
        if claims.get('role', '') not in ('admin', 'super_admin', 'interviewer'):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT qb.id, qb.original_filename, qb.description, qb.tags,
                   qb.is_active, qb.created_at, u.name as uploaded_by_name,
                   jsonb_array_length(COALESCE(qb.parsed_questions, '[]'::jsonb)) as questions_count
            FROM custom_question_bank qb
            LEFT JOIN users u ON qb.uploaded_by = u.id
            ORDER BY qb.created_at DESC
        """)
        rows = cur.fetchall()
        return_connection(conn)

        items = [{
            'id': row[0], 'filename': row[1], 'description': row[2],
            'tags': row[3], 'is_active': row[4],
            'created_at': str(row[5]) if row[5] else None,
            'uploaded_by': row[6], 'questions_count': row[7] or 0
        } for row in rows]

        return jsonify({'status': 'success', 'data': items})

    except Exception as e:
        logger.error(f"[CUSTOM QB] List failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_content_bp.route('/question-bank/<int:qb_id>', methods=['GET'])
@jwt_required()
def get_question_bank(qb_id):
    try:
        claims = get_jwt()
        if claims.get('role', '') not in ('admin', 'super_admin', 'interviewer'):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT qb.id, qb.original_filename, qb.description, qb.tags,
                   qb.is_active, qb.created_at, qb.parsed_questions, qb.questions_text,
                   u.name as uploaded_by_name
            FROM custom_question_bank qb
            LEFT JOIN users u ON qb.uploaded_by = u.id
            WHERE qb.id = %s
        """, (qb_id,))
        row = cur.fetchone()
        return_connection(conn)

        if not row:
            return jsonify({'status': 'error', 'message': 'Not found'}), 404

        import json
        parsed = json.loads(row[6]) if isinstance(row[6], str) else (row[6] or [])

        return jsonify({'status': 'success', 'data': {
            'id': row[0], 'filename': row[1], 'description': row[2], 'tags': row[3],
            'is_active': row[4], 'created_at': str(row[5]) if row[5] else None,
            'parsed_questions': parsed, 'raw_text_preview': (row[7] or '')[:500],
            'uploaded_by': row[8], 'questions_count': len(parsed)
        }})

    except Exception as e:
        logger.error(f"[CUSTOM QB] Get failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_content_bp.route('/question-bank/<int:qb_id>', methods=['DELETE'])
@jwt_required()
def delete_question_bank(qb_id):
    try:
        claims = get_jwt()
        if claims.get('role', '') not in ('admin', 'super_admin'):
            return jsonify({'status': 'error', 'message': 'Only admins can delete'}), 403

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT file_path FROM custom_question_bank WHERE id = %s", (qb_id,))
        row = cur.fetchone()
        if not row:
            return_connection(conn)
            return jsonify({'status': 'error', 'message': 'Not found'}), 404

        filepath = row[0]
        cur.execute("DELETE FROM custom_question_bank WHERE id = %s", (qb_id,))
        conn.commit()
        return_connection(conn)

        if filepath and os.path.exists(filepath):
            with contextlib.suppress(Exception):
                os.remove(filepath)

        return jsonify({'status': 'success', 'message': 'Question bank deleted'})

    except Exception as e:
        logger.error(f"[CUSTOM QB] Delete failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_content_bp.route('/question-bank/<int:qb_id>/toggle', methods=['PATCH'])
@jwt_required()
def toggle_question_bank(qb_id):
    try:
        claims = get_jwt()
        if claims.get('role', '') not in ('admin', 'super_admin'):
            return jsonify({'status': 'error', 'message': 'Only admins can toggle status'}), 403

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE custom_question_bank
            SET is_active = NOT is_active, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING is_active
        """, (qb_id,))
        row = cur.fetchone()
        if not row:
            return_connection(conn)
            return jsonify({'status': 'error', 'message': 'Not found'}), 404
        conn.commit()
        return_connection(conn)

        return jsonify({'status': 'success', 'is_active': row[0]})

    except Exception as e:
        logger.error(f"[CUSTOM QB] Toggle failed: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
