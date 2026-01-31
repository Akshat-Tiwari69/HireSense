"""
Enhanced Interviewer Routes - Job posting management and AI refinement
Includes: Job creation, AI refinement, job-specific assessments, performance analytics
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import json
import os
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
        
        # Generate AI-enhanced content
        title = job.get('title', 'Position')
        department = job.get('department', 'Department')
        description = job.get('description', '')
        min_exp = job.get('min_experience', 0)
        
        # Enhanced description with responsibilities and requirements
        refined_description = f"""**Position Overview:**
{title} role in the {department} team. {description}

**Key Responsibilities:**
• Lead technical initiatives and drive innovation within the team
• Collaborate with cross-functional teams to deliver high-quality solutions
• Mentor junior team members and contribute to knowledge sharing
• Participate in code reviews and maintain best practices
• Design and implement scalable, maintainable solutions

**Requirements:**
• Minimum {min_exp} years of relevant industry experience
• Strong problem-solving and analytical skills
• Excellent communication and teamwork abilities
• Proven track record of delivering complex projects
• Self-motivated with ability to work independently"""

        # Ideal candidate profile
        if min_exp < 2:
            ideal_profile = "Entry-level professional eager to learn and grow. Strong foundational knowledge with enthusiasm for technology. Quick learner who thrives in collaborative environments."
            complexity = "junior"
        elif min_exp < 5:
            ideal_profile = "Mid-level professional with solid technical foundation and growing leadership skills. Proven ability to work independently while collaborating effectively with team members. Demonstrates ownership and accountability."
            complexity = "intermediate"
        elif min_exp < 8:
            ideal_profile = "Senior professional with deep technical expertise and strong leadership capabilities. Strategic thinker who can architect complex solutions. Mentors others and drives technical excellence across the organization."
            complexity = "senior"
        else:
            ideal_profile = "Expert-level professional with extensive industry experience and thought leadership. Drives technical vision and strategy. Recognized authority in their domain with ability to influence at organizational level."
            complexity = "expert"
        
        # Enhanced skill taxonomy - expand on required skills
        enhanced_skills = list(set(required_skills))
        if 'Python' in enhanced_skills or 'python' in enhanced_skills:
            enhanced_skills.extend(['Django', 'Flask', 'FastAPI', 'pytest'])
        if 'JavaScript' in enhanced_skills or 'javascript' in enhanced_skills:
            enhanced_skills.extend(['React', 'Node.js', 'TypeScript', 'Jest'])
        if 'Java' in enhanced_skills or 'java' in enhanced_skills:
            enhanced_skills.extend(['Spring Boot', 'Maven', 'JUnit', 'Hibernate'])
        
        # Add common professional skills
        enhanced_skills.extend(['Problem Solving', 'Communication', 'Teamwork', 'Agile/Scrum'])
        enhanced_skills = list(set(enhanced_skills))[:15]  # Limit to 15 skills
        
        # Create refined data
        refined = {
            "refined_description": data.get('refined_description', refined_description),
            "ideal_candidate_profile": data.get('ideal_candidate_profile', ideal_profile),
            "skill_taxonomy": data.get('skill_taxonomy', enhanced_skills),
            "role_complexity_level": data.get('role_complexity_level', complexity)
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
    """Get all candidates with their auto-matched jobs"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    status = request.args.get('status', None)
    
    # Get all candidates with their matched job info
    query = """
        SELECT DISTINCT 
            c.*,
            jd.title as job_title,
            jd.id as matched_job_id,
            sa.scheduled_time,
            a.overall_score,
            a.status as assessment_status
        FROM candidates c
        LEFT JOIN job_descriptions jd ON c.job_id = jd.id
        LEFT JOIN scheduled_assessments sa ON c.id = sa.candidate_id AND sa.interviewer_id = ?
        LEFT JOIN assessments a ON c.id = a.candidate_id
    """
    params = [user_id]
    
    if status:
        query += " WHERE c.status = ?"
        params.append(status)
    
    query += " ORDER BY c.created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    candidates = []
    for row in rows:
        candidate = dict(row)
        
        # Parse JSON fields
        try:
            candidate['parsed_skills'] = json.loads(candidate.get('parsed_skills') or '[]')
        except:
            candidate['parsed_skills'] = []
        
        try:
            pros_data = candidate.get('pros')
            if pros_data:
                # Handle both JSON array and newline-separated string
                if pros_data.startswith('['):
                    candidate['pros'] = json.loads(pros_data)
                else:
                    candidate['pros'] = pros_data.split('\n')
            else:
                candidate['pros'] = []
        except:
            candidate['pros'] = []
        
        try:
            cons_data = candidate.get('cons')
            if cons_data:
                # Handle both JSON array and newline-separated string
                if cons_data.startswith('['):
                    candidate['cons'] = json.loads(cons_data)
                else:
                    candidate['cons'] = cons_data.split('\n')
            else:
                candidate['cons'] = []
        except:
            candidate['cons'] = []
        
        # Build parsed_data object for frontend
        candidate['parsed_data'] = {
            'skills': candidate.get('parsed_skills', []),
            'experience': candidate.get('years_experience', 0),
            'education': candidate.get('education', ''),
            'match_score': candidate.get('match_score', 0),
            'pros': candidate['pros'],
            'cons': candidate['cons']
        }
        
        candidates.append(candidate)
    
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
    """Reject a candidate and send rejection email"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get candidate details
        cursor.execute("""
            SELECT c.name, c.email, c.status
            FROM candidates c
            WHERE c.id = ?
        """, (candidate_id,))
        
        candidate_row = cursor.fetchone()
        if not candidate_row:
            conn.close()
            return jsonify({'error': 'Candidate not found'}), 404
        
        candidate = dict(candidate_row)
        
        # Update candidate status
        cursor.execute("""
            UPDATE candidates SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (candidate_id,))
        
        # Update assessment decision if exists
        cursor.execute("""
            UPDATE assessments SET decision = 'rejected', rationale = ?
            WHERE candidate_id = ?
        """, (data.get('reason', 'After careful consideration'), candidate_id))
        
        conn.commit()
        conn.close()
        
        # Send rejection email
        email_sent = False
        try:
            from email_service import EmailService
            email_service = EmailService()
            email_sent = email_service.send_rejection_email(
                candidate_email=candidate['email'],
                candidate_name=candidate['name'],
                reason=data.get('reason', 'After careful consideration, we have decided to move forward with other candidates.')
            )
            print(f"✅ Rejection email sent to {candidate['email']}")
        except Exception as email_error:
            print(f"⚠️ Failed to send rejection email: {email_error}")
        
        return jsonify({
            'message': 'Candidate rejected successfully',
            'candidate_name': candidate['name'],
            'email_sent': email_sent
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@interviewer_bp.route('/candidates/<int:candidate_id>/schedule', methods=['POST'])
@interviewer_required
def schedule_candidate_assessment(candidate_id):
    """Schedule an assessment for a candidate and send invitation email"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get candidate details
        cursor.execute("""
            SELECT c.name, c.email, c.job_id, jd.title as job_title
            FROM candidates c
            LEFT JOIN job_descriptions jd ON c.job_id = jd.id
            WHERE c.id = ?
        """, (candidate_id,))
        
        candidate_row = cursor.fetchone()
        if not candidate_row:
            conn.close()
            return jsonify({'error': 'Candidate not found'}), 404
        
        candidate = dict(candidate_row)
        
        # Get interviewer details
        cursor.execute("""
            SELECT name, email FROM users WHERE id = ?
        """, (user_id,))
        
        interviewer_row = cursor.fetchone()
        interviewer = dict(interviewer_row) if interviewer_row else {'name': 'CYGNUSA Team', 'email': ''}
        
        # Generate assessment token
        from db_helpers import generate_assessment_token
        import secrets
        access_token = secrets.token_urlsafe(32)
        
        # Insert scheduled assessment
        cursor.execute("""
            INSERT INTO scheduled_assessments (
                candidate_id, interviewer_id, scheduled_time, job_id, 
                status, proctoring_enabled, access_token
            ) VALUES (?, ?, ?, ?, 'scheduled', ?, ?)
        """, (
            candidate_id,
            user_id,
            data.get('scheduled_time', data.get('scheduled_at')),
            candidate.get('job_id') or data.get('job_id'),
            data.get('proctoring_enabled', True),
            access_token
        ))
        
        # Update candidate status
        cursor.execute("""
            UPDATE candidates SET status = 'assessment_scheduled', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (candidate_id,))
        
        conn.commit()
        scheduled_id = cursor.lastrowid
        conn.close()
        
        # Generate assessment link
        frontend_url = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
        assessment_link = f"{frontend_url}/assessment/{access_token}"
        
        # Send invitation email
        email_sent = False
        try:
            from email_service import EmailService
            from datetime import datetime
            email_service = EmailService()
            
            scheduled_time = data.get('scheduled_time', data.get('scheduled_at', 'Soon'))
            try:
                # Format datetime nicely if it's ISO format
                dt = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%B %d, %Y at %I:%M %p')
            except:
                formatted_time = str(scheduled_time)
            
            email_sent = email_service.send_assessment_invitation(
                candidate_email=candidate['email'],
                candidate_name=candidate['name'],
                assessment_link=assessment_link,
                scheduled_time=formatted_time,
                interviewer_name=interviewer['name'],
                additional_info=data.get('additional_info')
            )
            print(f"✅ Assessment invitation sent to {candidate['email']}")
        except Exception as email_error:
            print(f"⚠️ Failed to send assessment invitation: {email_error}")
        
        return jsonify({
            'id': scheduled_id,
            'message': 'Assessment scheduled successfully',
            'candidate_name': candidate['name'],
            'assessment_link': assessment_link,
            'access_token': access_token,
            'email_sent': email_sent
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@interviewer_bp.route('/completed-assessments', methods=['GET'])
@interviewer_required
def get_completed_assessments():
    """Get all completed assessments for interviewer's jobs"""
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                a.id,
                a.candidate_id,
                c.name as candidate_name,
                c.email as candidate_email,
                jd.title as job_title,
                a.technical_score,
                a.psychometric_score,
                a.overall_score,
                a.decision,
                a.rationale,
                a.proctoring_violations,
                a.hiring_recommendation,
                a.completed_at,
                a.started_at
            FROM assessments a
            JOIN candidates c ON a.candidate_id = c.id
            LEFT JOIN job_descriptions jd ON a.job_id = jd.id
            LEFT JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
            WHERE a.status = 'completed' 
                AND (sa.interviewer_id = ? OR jd.created_by_id = ?)
            ORDER BY a.completed_at DESC
        """, (user_id, user_id))
        
        assessments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(assessments)
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@interviewer_bp.route('/assessments/<int:assessment_id>/final-decision', methods=['POST'])
@interviewer_required
def make_final_decision(assessment_id):
    """Make final hiring decision (hire or no-hire) and send notification email"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    decision = data.get('decision')  # 'hire' or 'no-hire'
    rationale = data.get('rationale', '')
    next_steps = data.get('next_steps', '')
    
    if decision not in ['hire', 'no-hire']:
        return jsonify({'error': 'Decision must be "hire" or "no-hire"'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get assessment and candidate details
        cursor.execute("""
            SELECT 
                a.id,
                a.candidate_id,
                c.name as candidate_name,
                c.email as candidate_email,
                a.technical_score,
                a.psychometric_score,
                a.overall_score
            FROM assessments a
            JOIN candidates c ON a.candidate_id = c.id
            WHERE a.id = ?
        """, (assessment_id,))
        
        assessment_row = cursor.fetchone()
        if not assessment_row:
            conn.close()
            return jsonify({'error': 'Assessment not found'}), 404
        
        assessment = dict(assessment_row)
        
        # Update assessment decision
        cursor.execute("""
            UPDATE assessments 
            SET decision = ?, rationale = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (decision, rationale, assessment_id))
        
        # Update candidate status
        new_status = 'hired' if decision == 'hire' else 'rejected'
        cursor.execute("""
            UPDATE candidates 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, assessment['candidate_id']))
        
        conn.commit()
        conn.close()
        
        # Send decision email
        email_sent = False
        try:
            from email_service import EmailService
            email_service = EmailService()
            
            scores = {
                'technical': assessment.get('technical_score'),
                'psychometric': assessment.get('psychometric_score'),
                'overall': assessment.get('overall_score')
            }
            
            email_sent = email_service.send_final_decision_email(
                candidate_email=assessment['candidate_email'],
                candidate_name=assessment['candidate_name'],
                decision=decision,
                rationale=rationale,
                next_steps=next_steps,
                scores=scores
            )
            print(f"✅ Final decision email sent to {assessment['candidate_email']}")
        except Exception as email_error:
            print(f"⚠️ Failed to send decision email: {email_error}")
        
        return jsonify({
            'message': f'Decision recorded: {decision}',
            'candidate_name': assessment['candidate_name'],
            'decision': decision,
            'email_sent': email_sent
        })
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400
