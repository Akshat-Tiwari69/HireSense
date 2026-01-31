"""
Enhanced Interviewer Routes - Job posting management and AI refinement
Includes: Job creation, AI refinement, job-specific assessments, performance analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import json
from datetime import datetime
from functools import wraps
from db_config import get_connection

interviewer_bp = Blueprint('interviewer', __name__, url_prefix='/api/interviewer')

def get_db():
    conn = get_connection(use_dict_cursor=True)
    # Enable autocommit for PostgreSQL to avoid transaction issues
    if hasattr(conn, 'set_session'):
        conn.set_session(autocommit=True)
    return conn

def get_current_user_id():
    """Get current user ID from JWT token."""
    return int(get_jwt_identity())

def interviewer_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        claims = get_jwt()
        if claims.get('role') != 'interviewer':
            return jsonify({'error': 'Interviewer access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# JOB POSTING MANAGEMENT
# ============================================================================

@interviewer_bp.route('/my-jobs', methods=['GET'])
@interviewer_required
def get_interviewer_jobs():
    """Get all jobs created by this interviewer"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM job_descriptions 
        WHERE created_by_id = ? AND is_archived = FALSE
        ORDER BY created_at DESC
    """, (user_id,))
    
    jobs = [dict(row) for row in cursor.fetchall()]
    
    for job in jobs:
        if job['required_skills']:
            job['required_skills'] = json.loads(job['required_skills'])
        if job['skill_taxonomy']:
            job['skill_taxonomy'] = json.loads(job['skill_taxonomy'])
        
        # Get job analytics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT a.id) as total_assessments,
                COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) as completed_assessments,
                COUNT(DISTINCT CASE WHEN a.decision = 'hired' THEN a.id END) as hired_count,
                AVG(a.overall_score) as avg_score
            FROM assessments a
            WHERE a.job_id = ?
        """, (job['id'],))
        
        analytics = dict(cursor.fetchone())
        job['analytics'] = analytics
    
    conn.close()
    return jsonify(jobs)

@interviewer_bp.route('/jobs', methods=['POST'])
@interviewer_required
def create_job():
    """Create new job posting"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Create job
        cursor.execute("""
            INSERT INTO job_descriptions (
                title, description, required_skills, min_experience,
                department, location, created_by_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data.get('description', ''),
            json.dumps(data.get('required_skills', [])),
            data.get('min_experience', 0),
            data.get('department'),
            data.get('location'),
            user_id,
            'active'
        ))
        
        job_id = cursor.lastrowid
        
        # Create default scoring profile
        cursor.execute("""
            INSERT INTO job_scoring_profiles (
                job_id, technical_weight, psychometric_weight, min_passing_score
            ) VALUES (?, ?, ?, ?)
        """, (job_id, 0.7, 0.3, 70.0))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': job_id,
            'message': 'Job created successfully'
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@interviewer_bp.route('/jobs/<int:job_id>/ai-refine', methods=['POST'])
@interviewer_required
def ai_refine_job(job_id):
    """Use AI to refine and enhance job description"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get job details
        cursor.execute("SELECT * FROM job_descriptions WHERE id = ? AND created_by_id = ?",
                      (job_id, user_id))
        job_row = cursor.fetchone()
        
        if not job_row:
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        job = dict(job_row)
        
        # Parse required skills safely
        try:
            required_skills = json.loads(job.get('required_skills') or '[]')
        except:
            required_skills = []
        
        # Create refined data from request or use defaults
        refined = {
            "refined_description": data.get('refined_description', job.get('description', '')),
            "ideal_candidate_profile": data.get('ideal_candidate_profile', 'Experienced professional'),
            "skill_taxonomy": data.get('skill_taxonomy', required_skills),
            "role_complexity_level": data.get('role_complexity_level', 'intermediate')
        }
        
        # Update job with refined information
        cursor.execute("""
            UPDATE job_descriptions
            SET ai_refined_description = ?,
                ideal_candidate_profile = ?,
                skill_taxonomy = ?,
                role_complexity_level = ?
            WHERE id = ?
        """, (
            refined['refined_description'],
            refined['ideal_candidate_profile'],
            json.dumps(refined['skill_taxonomy']),
            refined['role_complexity_level'],
            job_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Job refined successfully',
            'refined_data': refined
        }), 200
    except Exception as e:
        import traceback
        print(f"Error in ai_refine_job: {str(e)}")
        print(traceback.format_exc())
        try:
            conn.close()
        except:
            pass
        return jsonify({'error': str(e), 'type': type(e).__name__}), 400

# ============================================================================
# ASSESSMENT SCHEDULING WITH JOB CONTEXT
# ============================================================================

@interviewer_bp.route('/schedule-assessment', methods=['POST'])
@interviewer_required
def schedule_assessment_with_job():
    """Schedule assessment linked to specific job posting"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Create scheduled assessment
        cursor.execute("""
            INSERT INTO scheduled_assessments (
                candidate_id, interviewer_id, scheduled_time,
                job_id, status, proctoring_enabled
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['candidate_id'],
            user_id,
            data['scheduled_time'],
            data.get('job_id'),
            'scheduled',
            data.get('proctoring_enabled', True)
        ))
        
        conn.commit()
        scheduled_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'id': scheduled_id,
            'message': 'Assessment scheduled successfully'
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

# ============================================================================
# JOB-SPECIFIC ASSESSMENT RESULTS
# ============================================================================

@interviewer_bp.route('/jobs/<int:job_id>/assessment-results', methods=['GET'])
@interviewer_required
def get_job_assessment_results(job_id):
    """Get all assessment results for a specific job"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify job belongs to interviewer
    cursor.execute("SELECT * FROM job_descriptions WHERE id = ? AND created_by_id = ?",
                  (job_id, user_id))
    if not cursor.fetchone():
        return jsonify({'error': 'Job not found'}), 404
    
    # Get assessments for this job
    cursor.execute("""
        SELECT 
            a.id, a.candidate_id, a.job_id, a.technical_score, a.psychometric_score,
            a.overall_score, a.status, a.decision, a.proctoring_violations,
            a.ai_recommendation, a.skill_gap_analysis, a.started_at, a.completed_at,
            c.name as candidate_name,
            c.email as candidate_email,
            COUNT(DISTINCT CASE WHEN pe.event_type = 'violation' THEN pe.id END) as violation_count
        FROM assessments a
        JOIN candidates c ON a.candidate_id = c.id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE a.job_id = ?
        GROUP BY a.id, a.candidate_id, a.job_id, a.technical_score, a.psychometric_score,
                 a.overall_score, a.status, a.decision, a.proctoring_violations,
                 a.ai_recommendation, a.skill_gap_analysis, a.started_at, a.completed_at,
                 c.name, c.email
        ORDER BY a.completed_at DESC
    """, (job_id,))
    
    results = [dict(row) for row in cursor.fetchall()]
    
    for result in results:
        if result['ai_recommendation']:
            result['ai_recommendation'] = json.loads(result['ai_recommendation'])
        if result['skill_gap_analysis']:
            result['skill_gap_analysis'] = json.loads(result['skill_gap_analysis'])
    
    conn.close()
    return jsonify(results)

# ============================================================================
# JOB PERFORMANCE ANALYTICS
# ============================================================================

@interviewer_bp.route('/jobs/<int:job_id>/analytics', methods=['GET'])
@interviewer_required
def get_job_analytics(job_id):
    """Get detailed analytics for a job posting"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("SELECT * FROM job_descriptions WHERE id = ? AND created_by_id = ?",
                  (job_id, user_id))
    if not cursor.fetchone():
        return jsonify({'error': 'Job not found'}), 404
    
    # Get various metrics
    cursor.execute("""
        SELECT 
            COUNT(*) as total_candidates_for_job,
            COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) as completed_assessments,
            COUNT(DISTINCT CASE WHEN a.decision = 'hired' THEN a.id END) as hired,
            COUNT(DISTINCT CASE WHEN a.decision = 'rejected' THEN a.id END) as rejected,
            AVG(a.technical_score) as avg_technical_score,
            AVG(a.psychometric_score) as avg_psychometric_score,
            AVG(a.overall_score) as avg_overall_score,
            AVG(a.proctoring_violations) as avg_violations
        FROM scheduled_assessments sa
        LEFT JOIN assessments a ON sa.id = a.scheduled_assessment_id
        WHERE sa.job_id = ?
    """, (job_id,))
    
    stats = dict(cursor.fetchone())
    
    # Get assessment analytics over time
    cursor.execute("""
        SELECT 
            DATE(assessment_date) as date,
            total_assessments_completed,
            average_overall_score,
            pass_rate,
            hired_count
        FROM assessment_analytics
        WHERE job_id = ?
        ORDER BY assessment_date DESC
        LIMIT 30
    """, (job_id,))
    
    daily_analytics = [dict(row) for row in cursor.fetchall()]
    stats['daily_analytics'] = daily_analytics
    
    conn.close()
    return jsonify(stats)

# ============================================================================
# INTERVIEWER PREFERENCES
# ============================================================================

@interviewer_bp.route('/preferences', methods=['GET', 'POST'])
@interviewer_required
def manage_preferences():
    """Get or update interviewer preferences"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute("SELECT * FROM interviewer_preferences WHERE interviewer_id = ?",
                      (user_id,))
        prefs = cursor.fetchone()
        conn.close()
        
        if not prefs:
            return jsonify({
                'default_assessment_template_id': None,
                'email_notifications': True,
                'assessment_time_window_minutes': 30
            })
        
        return jsonify(dict(prefs))
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Check if preferences exist
        cursor.execute("SELECT id FROM interviewer_preferences WHERE interviewer_id = ?",
                      (user_id,))
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute("""
                UPDATE interviewer_preferences
                SET default_assessment_template_id = ?,
                    email_notifications = ?,
                    assessment_time_window_minutes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE interviewer_id = ?
            """, (
                data.get('default_assessment_template_id'),
                data.get('email_notifications', True),
                data.get('assessment_time_window_minutes', 30),
                user_id
            ))
        else:
            cursor.execute("""
                INSERT INTO interviewer_preferences (
                    interviewer_id, default_assessment_template_id,
                    email_notifications, assessment_time_window_minutes
                ) VALUES (?, ?, ?, ?)
            """, (
                user_id,
                data.get('default_assessment_template_id'),
                data.get('email_notifications', True),
                data.get('assessment_time_window_minutes', 30)
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Preferences updated'})

# ============================================================================
# ACTIVE ASSESSMENTS
# ============================================================================

@interviewer_bp.route('/active-assessments', methods=['GET'])
@interviewer_required
def get_active_assessments():
    """Get currently active assessments for interviewer"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.id,
            a.status,
            c.name as candidate_name,
            c.email as candidate_email,
            jd.title as job_title,
            a.started_at,
            a.proctoring_violations,
            sa.scheduled_time
        FROM assessments a
        JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
        JOIN candidates c ON a.candidate_id = c.id
        JOIN job_descriptions jd ON sa.job_id = jd.id
        WHERE sa.interviewer_id = ? AND a.status IN ('in_progress', 'pending')
        ORDER BY a.started_at DESC
    """, (user_id,))
    
    assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(assessments)

# ============================================================================
# CANDIDATE MANAGEMENT (For Legacy UI)
# ============================================================================

@interviewer_bp.route('/candidates', methods=['GET'])
@interviewer_required
def get_candidates():
    """Get all candidates for this interviewer's jobs"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    status = request.args.get('status', None)
    
    query = """
        SELECT DISTINCT 
            c.*,
            jd.title as job_title,
            sa.scheduled_time,
            a.overall_score,
            a.status as assessment_status
        FROM candidates c
        LEFT JOIN scheduled_assessments sa ON c.id = sa.candidate_id
        LEFT JOIN job_descriptions jd ON sa.job_id = jd.id
        LEFT JOIN assessments a ON c.id = a.candidate_id
        WHERE sa.interviewer_id = ?
    """
    params = [user_id]
    
    if status:
        query += " AND c.status = ?"
        params.append(status)
    
    query += " ORDER BY c.created_at DESC"
    
    cursor.execute(query, params)
    candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(candidates)

@interviewer_bp.route('/candidates/<int:candidate_id>', methods=['GET'])
@interviewer_required
def get_candidate_details(candidate_id):
    """Get detailed candidate information"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, 
            jd.title as job_title,
            a.technical_score, a.psychometric_score, a.overall_score,
            a.decision, a.rationale, a.proctoring_violations
        FROM candidates c
        LEFT JOIN scheduled_assessments sa ON c.id = sa.candidate_id
        LEFT JOIN job_descriptions jd ON sa.job_id = jd.id
        LEFT JOIN assessments a ON c.id = a.candidate_id
        WHERE c.id = ? AND sa.interviewer_id = ?
    """, (candidate_id, user_id))
    
    candidate = cursor.fetchone()
    conn.close()
    
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404
    
    return jsonify(dict(candidate))

@interviewer_bp.route('/candidates/<int:candidate_id>/reject', methods=['POST'])
@interviewer_required
def reject_candidate(candidate_id):
    """Reject a candidate"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Verify interviewer has access to this candidate
        cursor.execute("""
            SELECT 1 FROM scheduled_assessments sa
            WHERE sa.candidate_id = ? AND sa.interviewer_id = ?
        """, (candidate_id, user_id))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Update candidate status
        cursor.execute("""
            UPDATE candidates SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (candidate_id,))
        
        # Update assessment decision if exists
        cursor.execute("""
            UPDATE assessments SET decision = 'rejected', rationale = ?
            WHERE candidate_id = ?
        """, (data.get('reason', ''), candidate_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Candidate rejected'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@interviewer_bp.route('/candidates/<int:candidate_id>/schedule', methods=['POST'])
@interviewer_required
def schedule_candidate_assessment(candidate_id):
    """Schedule an assessment for a candidate"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO scheduled_assessments (
                candidate_id, interviewer_id, scheduled_time, job_id, status, proctoring_enabled
            ) VALUES (?, ?, ?, ?, 'scheduled', ?)
        """, (
            candidate_id,
            user_id,
            data['scheduled_time'],
            data.get('job_id'),
            data.get('proctoring_enabled', True)
        ))
        
        conn.commit()
        scheduled_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'id': scheduled_id, 'message': 'Assessment scheduled'}), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
