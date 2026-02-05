"""
Enhanced Job Posting Routes
Handles job postings with required/preferred skills and automatic candidate matching
"""

import json
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db_config import get_connection, return_connection
from audit_logger import AuditLogger
from candidate_job_matcher import CandidateJobMatcher
from psycopg2.extras import RealDictCursor
from sector_routes import get_user_sector_access

logger = logging.getLogger(__name__)

# Create blueprint for enhanced job routes
enhanced_job_bp = Blueprint('enhanced_jobs', __name__)
matcher = CandidateJobMatcher()


# ============================================================================
#                           ENHANCED JOB POSTING CRUD
# ============================================================================

@enhanced_job_bp.route('/jobs/enhanced', methods=['GET'])
@jwt_required()
def get_enhanced_jobs():
    """Get all job postings with enhanced details including candidate counts"""
    conn = None
    try:
        user_email = get_jwt_identity()
        user_access = get_user_sector_access(user_email)
        
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Build query based on access level
        if user_access['is_super_admin']:
            # Super admin sees all jobs
            query = "SELECT * FROM jobs_with_candidate_counts ORDER BY created_at DESC"
            cursor.execute(query)
        elif user_access['sector_id']:
            # Sector admin/users see only their sector's jobs
            query = "SELECT * FROM jobs_with_candidate_counts WHERE sector_id = %s ORDER BY created_at DESC"
            cursor.execute(query, (user_access['sector_id'],))
        else:
            # Regular users see all jobs (can be restricted further if needed)
            query = "SELECT * FROM jobs_with_candidate_counts ORDER BY created_at DESC"
            cursor.execute(query)
        
        jobs = cursor.fetchall()
        
        # Format timestamps and parse JSON fields
        for job in jobs:
            if job.get('created_at'):
                job['created_at'] = job['created_at'].isoformat()
            if job.get('updated_at'):
                job['updated_at'] = job['updated_at'].isoformat()
            
            # Parse skills JSON
            for field in ['required_skills_json', 'preferred_skills_json']:
                if job.get(field):
                    try:
                        job[field] = json.loads(job[field]) if isinstance(job[field], str) else job[field]
                    except:
                        job[field] = []
        
        return jsonify({
            'status': 'success',
            'data': jobs
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching enhanced jobs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@enhanced_job_bp.route('/jobs/enhanced', methods=['POST'])
@jwt_required()
def create_enhanced_job():
    """Create a new job posting with required and preferred skills"""
    conn = None
    try:
        data = request.get_json()
        user_email = get_jwt_identity()
        user_access = get_user_sector_access(user_email)
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'status': 'error', 'message': 'Title is required'}), 400
        
        # Check sector access
        sector_id = data.get('sector_id')
        if sector_id and not user_access['is_super_admin']:
            if user_access['sector_id'] and user_access['sector_id'] != sector_id:
                return jsonify({
                    'status': 'error',
                    'message': 'You can only create jobs in your assigned sector'
                }), 403
        
        # Use user's sector if not specified
        if not sector_id and user_access['sector_id']:
            sector_id = user_access['sector_id']
        
        # Parse skills arrays
        required_skills = data.get('required_skills', [])
        preferred_skills = data.get('preferred_skills', [])
        
        if not isinstance(required_skills, list):
            required_skills = [s.strip() for s in str(required_skills).split(',') if s.strip()]
        if not isinstance(preferred_skills, list):
            preferred_skills = [s.strip() for s in str(preferred_skills).split(',') if s.strip()]
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        user_id = user_result[0] if user_result else None
        
        cursor.execute("""
            INSERT INTO job_descriptions (
                title, description, required_skills, required_skills_json,
                preferred_skills_json, min_experience, department, location,
                sector_id, status, created_by
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['title'],
            data.get('description', ''),
            ','.join(required_skills),  # Keep text version for compatibility
            json.dumps(required_skills),
            json.dumps(preferred_skills),
            data.get('min_experience', 0),
            data.get('department', ''),
            data.get('location', ''),
            sector_id,
            data.get('status', 'active'),
            user_id
        ))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        
        # Log the action
        AuditLogger.log_job_created(
            user_id=user_id,
            user_email=user_email,
            job_id=job_id,
            job_title=data['title'],
            sector_id=sector_id
        )
        
        logger.info(f"Enhanced job posting '{data['title']}' created by {user_email}")
        
        # Trigger automatic matching for existing candidates
        try:
            # This can be done asynchronously in production
            matcher.auto_match_all_candidates()
        except Exception as e:
            logger.error(f"Error triggering auto-match: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Job posting created successfully',
            'data': {'id': job_id}
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error creating enhanced job: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@enhanced_job_bp.route('/jobs/enhanced/<int:job_id>', methods=['PUT'])
@jwt_required()
def update_enhanced_job(job_id):
    """Update an existing job posting"""
    conn = None
    try:
        data = request.get_json()
        user_email = get_jwt_identity()
        user_access = get_user_sector_access(user_email)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if user has access to this job
        cursor.execute("SELECT sector_id FROM job_descriptions WHERE id = %s", (job_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404
        
        job_sector_id = result[0]
        
        if not user_access['is_super_admin']:
            if user_access['sector_id'] != job_sector_id:
                return jsonify({
                    'status': 'error',
                    'message': 'You can only update jobs in your sector'
                }), 403
        
        # Build update query
        updates = []
        values = []
        changes = {}
        
        if 'title' in data:
            updates.append("title = %s")
            values.append(data['title'])
            changes['title'] = data['title']
        
        if 'description' in data:
            updates.append("description = %s")
            values.append(data['description'])
            changes['description'] = data['description']
        
        if 'required_skills' in data:
            required_skills = data['required_skills']
            if not isinstance(required_skills, list):
                required_skills = [s.strip() for s in str(required_skills).split(',') if s.strip()]
            updates.append("required_skills_json = %s")
            updates.append("required_skills = %s")
            values.append(json.dumps(required_skills))
            values.append(','.join(required_skills))
            changes['required_skills'] = required_skills
        
        if 'preferred_skills' in data:
            preferred_skills = data['preferred_skills']
            if not isinstance(preferred_skills, list):
                preferred_skills = [s.strip() for s in str(preferred_skills).split(',') if s.strip()]
            updates.append("preferred_skills_json = %s")
            values.append(json.dumps(preferred_skills))
            changes['preferred_skills'] = preferred_skills
        
        if 'min_experience' in data:
            updates.append("min_experience = %s")
            values.append(data['min_experience'])
            changes['min_experience'] = data['min_experience']
        
        if 'department' in data:
            updates.append("department = %s")
            values.append(data['department'])
            changes['department'] = data['department']
        
        if 'location' in data:
            updates.append("location = %s")
            values.append(data['location'])
            changes['location'] = data['location']
        
        if 'status' in data:
            updates.append("status = %s")
            values.append(data['status'])
            changes['status'] = data['status']
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(job_id)
        
        query = f"UPDATE job_descriptions SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, values)
        conn.commit()
        
        # Get user ID
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user_result = cursor.fetchone()
        user_id = user_result[0] if user_result else None
        
        # Log the action
        AuditLogger.log_job_updated(
            user_id=user_id,
            user_email=user_email,
            job_id=job_id,
            changes=changes
        )
        
        # Trigger re-matching if skills changed
        if 'required_skills' in data or 'preferred_skills' in data:
            try:
                matcher.auto_match_all_candidates()
            except Exception as e:
                logger.error(f"Error triggering auto-match: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Job posting updated successfully'
        }), 200
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error updating enhanced job: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


# ============================================================================
#                           CANDIDATE MATCHING
# ============================================================================

@enhanced_job_bp.route('/jobs/<int:job_id>/candidates/matches', methods=['GET'])
@jwt_required()
def get_job_candidate_matches(job_id):
    """Get all candidates matched to a specific job, sorted by match score"""
    conn = None
    try:
        user_email = get_jwt_identity()
        user_access = get_user_sector_access(user_email)
        
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check job access
        cursor.execute("SELECT sector_id FROM job_descriptions WHERE id = %s", (job_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404
        
        job_sector_id = result['sector_id']
        
        if not user_access['is_super_admin'] and user_access['sector_id'] != job_sector_id:
            return jsonify({
                'status': 'error',
                'message': 'Access denied'
            }), 403
        
        # Get candidate matches for this job
        cursor.execute("""
            SELECT 
                c.id, c.name, c.email, c.phone, c.years_experience,
                c.parsed_skills, c.parsed_skills_json, c.status,
                cjm.match_score, cjm.required_skills_matched,
                cjm.required_skills_total, cjm.preferred_skills_matched,
                cjm.preferred_skills_total, cjm.experience_match,
                cjm.matching_details
            FROM candidate_job_matches cjm
            JOIN candidates c ON c.id = cjm.candidate_id
            WHERE cjm.job_id = %s
            ORDER BY cjm.match_score DESC
        """, (job_id,))
        
        matches = cursor.fetchall()
        
        # Parse JSON fields
        for match in matches:
            if match.get('matching_details'):
                try:
                    match['matching_details'] = json.loads(match['matching_details']) if isinstance(match['matching_details'], str) else match['matching_details']
                except:
                    pass
            
            if match.get('parsed_skills_json'):
                try:
                    match['parsed_skills_json'] = json.loads(match['parsed_skills_json']) if isinstance(match['parsed_skills_json'], str) else match['parsed_skills_json']
                except:
                    pass
        
        return jsonify({
            'status': 'success',
            'data': matches,
            'count': len(matches)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching job candidate matches: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@enhanced_job_bp.route('/candidates/<int:candidate_id>/matches', methods=['GET'])
@jwt_required()
def get_candidate_job_matches(candidate_id):
    """Get all jobs matched to a specific candidate, sorted by match score"""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                jd.id, jd.title, jd.description, jd.department, jd.location,
                jd.required_skills_json, jd.preferred_skills_json,
                jd.min_experience, jd.status,
                s.name as sector_name, s.email as sector_email,
                cjm.match_score, cjm.required_skills_matched,
                cjm.required_skills_total, cjm.preferred_skills_matched,
                cjm.preferred_skills_total, cjm.experience_match,
                cjm.matching_details
            FROM candidate_job_matches cjm
            JOIN job_descriptions jd ON jd.id = cjm.job_id
            LEFT JOIN sectors s ON s.id = jd.sector_id
            WHERE cjm.candidate_id = %s
            ORDER BY cjm.match_score DESC
        """, (candidate_id,))
        
        matches = cursor.fetchall()
        
        # Parse JSON fields
        for match in matches:
            for field in ['required_skills_json', 'preferred_skills_json', 'matching_details']:
                if match.get(field):
                    try:
                        match[field] = json.loads(match[field]) if isinstance(match[field], str) else match[field]
                    except:
                        pass
        
        return jsonify({
            'status': 'success',
            'data': matches,
            'count': len(matches)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching candidate job matches: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if conn:
            return_connection(conn)


@enhanced_job_bp.route('/matching/trigger', methods=['POST'])
@jwt_required()
def trigger_matching():
    """Manually trigger re-matching of all candidates to all jobs"""
    try:
        user_email = get_jwt_identity()
        user_access = get_user_sector_access(user_email)
        
        # Only admins can trigger full re-matching
        if not user_access['is_super_admin'] and user_access['role'] != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Access denied. Admin role required.'
            }), 403
        
        logger.info(f"Manual matching triggered by {user_email}")
        
        result = matcher.auto_match_all_candidates()
        
        return jsonify({
            'status': 'success',
            'message': 'Candidate matching completed',
            'data': result
        }), 200
        
    except Exception as e:
        logger.error(f"Error triggering matching: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
