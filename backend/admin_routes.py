"""
Enhanced Admin Routes - Features for complete dashboard control
Includes: Job Management, Question Bank, Email Templates, Assessment Templates, Audit Logs
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
import json
from datetime import datetime
from functools import wraps
import sqlite3

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Database connection helper
def get_db():
    conn = sqlite3.connect('assessment_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# Admin authorization decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if 'user_id' not in session or session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# JOB MANAGEMENT ENDPOINTS
# ============================================================================

@admin_bp.route('/jobs', methods=['GET'])
@admin_required
def list_jobs():
    """Get all job postings with filtering"""
    conn = get_db()
    cursor = conn.cursor()
    
    status = request.args.get('status', 'active')
    search = request.args.get('search', '')
    
    query = "SELECT * FROM job_descriptions WHERE status = ? AND (title LIKE ? OR department LIKE ?)"
    cursor.execute(query, (status, f'%{search}%', f'%{search}%'))
    jobs = [dict(row) for row in cursor.fetchall()]
    
    # Parse JSON fields
    for job in jobs:
        if job['required_skills']:
            job['required_skills'] = json.loads(job['required_skills'])
        if job['skill_taxonomy']:
            job['skill_taxonomy'] = json.loads(job['skill_taxonomy'])
    
    conn.close()
    return jsonify(jobs)

@admin_bp.route('/jobs', methods=['POST'])
@admin_required
def create_job():
    """Create new job posting"""
    from flask import session
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO job_descriptions (
                title, description, required_skills, min_experience, 
                department, location, created_by_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data['description'],
            json.dumps(data.get('required_skills', [])),
            data.get('min_experience', 0),
            data.get('department'),
            data.get('location'),
            session['user_id'],
            'active'
        ))
        
        conn.commit()
        job_id = cursor.lastrowid
        
        # Log action
        log_admin_action(session['user_id'], 'create_job', 'job', job_id, None, data)
        
        conn.close()
        return jsonify({'id': job_id, 'message': 'Job created successfully'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/jobs/<int:job_id>', methods=['PUT'])
@admin_required
def update_job(job_id):
    """Update job posting"""
    from flask import session
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get old values for audit log
        cursor.execute("SELECT * FROM job_descriptions WHERE id = ?", (job_id,))
        old_job = dict(cursor.fetchone())
        
        cursor.execute("""
            UPDATE job_descriptions 
            SET title = ?, description = ?, required_skills = ?, 
                min_experience = ?, department = ?, location = ?,
                skill_taxonomy = ?, role_complexity_level = ?,
                last_modified_by_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('title', old_job['title']),
            data.get('description', old_job['description']),
            json.dumps(data.get('required_skills', json.loads(old_job['required_skills'] or '[]'))),
            data.get('min_experience', old_job['min_experience']),
            data.get('department', old_job['department']),
            data.get('location', old_job['location']),
            json.dumps(data.get('skill_taxonomy', json.loads(old_job['skill_taxonomy'] or '[]'))),
            data.get('role_complexity_level', old_job['role_complexity_level']),
            session['user_id'],
            job_id
        ))
        
        conn.commit()
        
        # Log action
        log_admin_action(session['user_id'], 'update_job', 'job', job_id, old_job, data)
        
        conn.close()
        return jsonify({'message': 'Job updated successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/jobs/<int:job_id>', methods=['DELETE'])
@admin_required
def delete_job(job_id):
    """Delete job posting"""
    from flask import session
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE job_descriptions SET is_archived = TRUE WHERE id = ?", (job_id,))
        conn.commit()
        
        log_admin_action(session['user_id'], 'delete_job', 'job', job_id, None, None)
        
        conn.close()
        return jsonify({'message': 'Job archived successfully'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/jobs/<int:job_id>/scoring-profile', methods=['GET', 'POST', 'PUT'])
@admin_required
def manage_job_scoring_profile(job_id):
    """Get or manage scoring profile for a job"""
    from flask import session
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM job_scoring_profiles WHERE job_id = ?", (job_id,))
        profile = cursor.fetchone()
        conn.close()
        
        if not profile:
            return jsonify({'message': 'No scoring profile found'}), 404
        
        profile_dict = dict(profile)
        if profile_dict['skill_thresholds']:
            profile_dict['skill_thresholds'] = json.loads(profile_dict['skill_thresholds'])
        return jsonify(profile_dict)
    
    elif request.method == 'POST':
        data = request.get_json()
        cursor.execute("""
            INSERT INTO job_scoring_profiles (
                job_id, technical_weight, psychometric_weight, 
                min_passing_score, skill_thresholds
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            job_id,
            data.get('technical_weight', 0.7),
            data.get('psychometric_weight', 0.3),
            data.get('min_passing_score', 70.0),
            json.dumps(data.get('skill_thresholds', {}))
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Scoring profile created'}), 201
    
    elif request.method == 'PUT':
        data = request.get_json()
        cursor.execute("""
            UPDATE job_scoring_profiles 
            SET technical_weight = ?, psychometric_weight = ?,
                min_passing_score = ?, skill_thresholds = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        """, (
            data.get('technical_weight', 0.7),
            data.get('psychometric_weight', 0.3),
            data.get('min_passing_score', 70.0),
            json.dumps(data.get('skill_thresholds', {})),
            job_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Scoring profile updated'})

# ============================================================================
# QUESTION BANK ENDPOINTS
# ============================================================================

@admin_bp.route('/question-bank', methods=['GET'])
@admin_required
def list_questions():
    """Get questions from question bank with filtering"""
    conn = get_db()
    cursor = conn.cursor()
    
    question_type = request.args.get('type')
    category = request.args.get('category')
    difficulty = request.args.get('difficulty')
    
    query = "SELECT * FROM question_bank WHERE is_active = TRUE"
    params = []
    
    if question_type:
        query += " AND question_type = ?"
        params.append(question_type)
    if category:
        query += " AND category = ?"
        params.append(category)
    if difficulty:
        query += " AND difficulty = ?"
        params.append(difficulty)
    
    cursor.execute(query, params)
    questions = [dict(row) for row in cursor.fetchall()]
    
    # Parse JSON fields
    for q in questions:
        if q['options']:
            q['options'] = json.loads(q['options'])
        if q['required_skills']:
            q['required_skills'] = json.loads(q['required_skills'])
        if q['test_cases']:
            q['test_cases'] = json.loads(q['test_cases'])
        if q['job_specific_keywords']:
            q['job_specific_keywords'] = json.loads(q['job_specific_keywords'])
    
    conn.close()
    return jsonify(questions)

@admin_bp.route('/question-bank', methods=['POST'])
@admin_required
def create_question():
    """Add new question to question bank"""
    from flask import session
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO question_bank (
                question_text, question_type, category, difficulty,
                required_skills, options, correct_answer, code_starter,
                test_cases, expected_solution, trait, job_specific_keywords,
                created_by_id, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['question_text'],
            data['question_type'],
            data['category'],
            data.get('difficulty', 'intermediate'),
            json.dumps(data.get('required_skills', [])),
            json.dumps(data.get('options', {})) if data.get('options') else None,
            data.get('correct_answer'),
            data.get('code_starter'),
            json.dumps(data.get('test_cases', [])) if data.get('test_cases') else None,
            data.get('expected_solution'),
            data.get('trait'),
            json.dumps(data.get('job_specific_keywords', [])),
            session['user_id'],
            True
        ))
        
        conn.commit()
        question_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': question_id, 'message': 'Question added to bank'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/question-bank/<int:question_id>', methods=['DELETE'])
@admin_required
def delete_question(question_id):
    """Remove question from question bank"""
    from flask import session
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE question_bank SET is_active = FALSE WHERE id = ?", (question_id,))
        conn.commit()
        
        log_admin_action(session['user_id'], 'delete_question', 'question', question_id, None, None)
        
        conn.close()
        return jsonify({'message': 'Question deactivated'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

# ============================================================================
# EMAIL TEMPLATE ENDPOINTS
# ============================================================================

@admin_bp.route('/email-templates', methods=['GET'])
@admin_required
def list_email_templates():
    """Get all email templates"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM email_templates ORDER BY template_name")
    templates = [dict(row) for row in cursor.fetchall()]
    
    for t in templates:
        if t['variables']:
            t['variables'] = json.loads(t['variables'])
    
    conn.close()
    return jsonify(templates)

@admin_bp.route('/email-templates', methods=['POST'])
@admin_required
def create_email_template():
    """Create new email template"""
    from flask import session
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO email_templates (
                template_name, subject, body, variables, is_default
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            data['template_name'],
            data['subject'],
            data['body'],
            json.dumps(data.get('variables', [])),
            data.get('is_default', False)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Email template created'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/email-templates/<int:template_id>', methods=['PUT'])
@admin_required
def update_email_template(template_id):
    """Update email template"""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE email_templates 
            SET subject = ?, body = ?, variables = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data['subject'],
            data['body'],
            json.dumps(data.get('variables', [])),
            template_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Email template updated'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

# ============================================================================
# ASSESSMENT TEMPLATE ENDPOINTS
# ============================================================================

@admin_bp.route('/assessment-templates', methods=['GET'])
@admin_required
def list_assessment_templates():
    """Get all assessment templates"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM assessment_templates ORDER BY role_type, difficulty_level")
    templates = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return jsonify(templates)

@admin_bp.route('/assessment-templates', methods=['POST'])
@admin_required
def create_assessment_template():
    """Create new assessment template"""
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO assessment_templates (
                template_name, description, role_type, difficulty_level,
                mcq_count, coding_count, psychometric_count, time_limit_minutes,
                tech_weight, psych_weight, is_default
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['template_name'],
            data.get('description'),
            data['role_type'],
            data.get('difficulty_level', 'intermediate'),
            data.get('mcq_count', 10),
            data.get('coding_count', 1),
            data.get('psychometric_count', 3),
            data.get('time_limit_minutes', 60),
            data.get('tech_weight', 0.7),
            data.get('psych_weight', 0.3),
            data.get('is_default', False)
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Assessment template created'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@admin_bp.route('/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Get admin audit logs"""
    conn = get_db()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 100, type=int)
    admin_id = request.args.get('admin_id', type=int)
    action_type = request.args.get('action_type')
    
    query = "SELECT * FROM admin_audit_log WHERE 1=1"
    params = []
    
    if admin_id:
        query += " AND admin_id = ?"
        params.append(admin_id)
    if action_type:
        query += " AND action_type = ?"
        params.append(action_type)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    
    for log in logs:
        if log['old_values']:
            log['old_values'] = json.loads(log['old_values'])
        if log['new_values']:
            log['new_values'] = json.loads(log['new_values'])
    
    conn.close()
    return jsonify(logs)

# ============================================================================
# HELPER FUNCTION
# ============================================================================

def log_admin_action(admin_id, action_type, entity_type, entity_id, old_values, new_values):
    """Log admin action for audit trail"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO admin_audit_log (
                admin_id, action_type, entity_type, entity_id, 
                old_values, new_values
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            admin_id,
            action_type,
            entity_type,
            entity_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None
        ))
        conn.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")
    finally:
        conn.close()
