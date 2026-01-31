"""
Enhanced Proctor Routes - Advanced monitoring and violation management
Includes: Real-time monitoring, violation review, anomaly detection, quality metrics
"""

from flask import Blueprint, request, jsonify
import json
from datetime import datetime, timedelta
from functools import wraps
from db_config import get_connection

proctor_bp = Blueprint('proctor', __name__, url_prefix='/api/proctor')

def get_db():
    conn = get_connection()
    # Enable autocommit for PostgreSQL to avoid transaction issues
    if hasattr(conn, 'set_session'):
        conn.set_session(autocommit=True)
    return conn

def proctor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if 'user_id' not in session or session.get('role') != 'proctor':
            return jsonify({'error': 'Proctor access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# REAL-TIME MONITORING DASHBOARD
# ============================================================================

@proctor_bp.route('/dashboard-stats', methods=['GET'])
@proctor_required
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now()
    
    # Active assessments (in progress)
    cursor.execute("""
        SELECT COUNT(*) as count FROM assessments 
        WHERE status = 'in_progress'
    """)
    active_count = cursor.fetchone()['count']
    
    # Scheduled today
    cursor.execute("""
        SELECT COUNT(*) as count FROM scheduled_assessments
        WHERE DATE(scheduled_time) = DATE('now') AND status = 'scheduled'
    """)
    scheduled_today = cursor.fetchone()['count']
    
    # Completed today
    cursor.execute("""
        SELECT COUNT(*) as count FROM assessments
        WHERE DATE(completed_at) = DATE('now') AND status = 'completed'
    """)
    completed_today = cursor.fetchone()['count']
    
    # Total violations today
    cursor.execute("""
        SELECT COUNT(*) as count FROM proctoring_events
        WHERE DATE(timestamp) = DATE('now')
    """)
    violations_today = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'active_assessments': active_count,
        'scheduled_today': scheduled_today,
        'completed_today': completed_today,
        'violations_today': violations_today
    })

@proctor_bp.route('/active-assessments', methods=['GET'])
@proctor_required
def get_active_assessments():
    """Get all currently active assessments with details"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            a.id as assessment_id,
            c.name as candidate_name,
            c.email as candidate_email,
            jd.title as job_title,
            a.started_at,
            COUNT(DISTINCT pe.id) as violation_count,
            a.proctoring_violations,
            CASE 
                WHEN (julianday('now') - julianday(a.started_at)) * 24 * 60 > 60 THEN 'overdue'
                WHEN (julianday('now') - julianday(a.started_at)) * 24 * 60 > 45 THEN 'near_end'
                ELSE 'in_progress'
            END as time_status
        FROM assessments a
        JOIN scheduled_assessments sa ON a.scheduled_assessment_id = sa.id
        JOIN candidates c ON a.candidate_id = c.id
        LEFT JOIN job_descriptions jd ON sa.job_id = jd.id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE a.status = 'in_progress'
        GROUP BY a.id
        ORDER BY a.started_at ASC
    """)
    
    assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(assessments)

@proctor_bp.route('/scheduled-assessments', methods=['GET'])
@proctor_required
def get_scheduled_assessments():
    """Get upcoming scheduled assessments"""
    conn = get_db()
    cursor = conn.cursor()
    
    days_ahead = request.args.get('days', 7, type=int)
    
    cursor.execute("""
        SELECT 
            sa.id,
            c.name as candidate_name,
            c.email as candidate_email,
            jd.title as job_title,
            sa.scheduled_time,
            ROUND((julianday(sa.scheduled_time) - julianday('now')) * 24 * 60) as minutes_until_start,
            sa.status
        FROM scheduled_assessments sa
        JOIN candidates c ON sa.candidate_id = c.id
        LEFT JOIN job_descriptions jd ON sa.job_id = jd.id
        WHERE sa.status = 'scheduled'
            AND sa.scheduled_time <= datetime('now', '+' || ? || ' days')
            AND sa.scheduled_time > datetime('now')
        ORDER BY sa.scheduled_time ASC
    """, (days_ahead,))
    
    assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(assessments)

@proctor_bp.route('/completed-assessments', methods=['GET'])
@proctor_required
def get_completed_assessments():
    """Get recently completed assessments with scores"""
    conn = get_db()
    cursor = conn.cursor()
    
    limit = request.args.get('limit', 50, type=int)
    days = request.args.get('days', 7, type=int)
    
    cursor.execute("""
        SELECT 
            a.id,
            c.name as candidate_name,
            c.email as candidate_email,
            jd.title as job_title,
            a.technical_score,
            a.psychometric_score,
            a.overall_score,
            a.proctoring_violations,
            a.completed_at,
            COUNT(DISTINCT pe.id) as violation_count
        FROM assessments a
        JOIN candidates c ON a.candidate_id = c.id
        LEFT JOIN job_descriptions jd ON a.job_id = jd.id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE a.status = 'completed'
            AND DATE(a.completed_at) >= DATE('now', '-' || ? || ' days')
        GROUP BY a.id
        ORDER BY a.completed_at DESC
        LIMIT ?
    """, (days, limit))
    
    assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(assessments)

# ============================================================================
# VIOLATION MANAGEMENT
# ============================================================================

@proctor_bp.route('/assessments/<int:assessment_id>/violations', methods=['GET'])
@proctor_required
def get_assessment_violations(assessment_id):
    """Get all violations for an assessment"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM proctoring_events
        WHERE assessment_id = ?
        ORDER BY timestamp DESC
    """, (assessment_id,))
    
    violations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(violations)

@proctor_bp.route('/violations/<int:violation_id>/review', methods=['POST'])
@proctor_required
def review_violation(violation_id):
    """Mark violation as reviewed and add proctor notes"""
    from flask import session
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE proctoring_events
            SET is_reviewed = TRUE,
                violation_acknowledged = ?,
                reviewer_id = ?,
                reviewer_notes = ?,
                timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('violation_acknowledged', False),
            session['user_id'],
            data.get('notes', ''),
            violation_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Violation reviewed'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@proctor_bp.route('/violations/flagged', methods=['GET'])
@proctor_required
def get_flagged_violations():
    """Get high-severity violations that need review"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            pe.id,
            pe.assessment_id,
            c.name as candidate_name,
            c.email as candidate_email,
            jd.title as job_title,
            pe.event_type,
            pe.severity,
            pe.details,
            pe.timestamp,
            pe.is_reviewed,
            COUNT(*) OVER (PARTITION BY pe.assessment_id) as total_violations_in_assessment
        FROM proctoring_events pe
        JOIN assessments a ON pe.assessment_id = a.id
        JOIN candidates c ON a.candidate_id = c.id
        LEFT JOIN job_descriptions jd ON a.job_id = jd.id
        WHERE (pe.severity IN ('high', 'critical') OR pe.assessment_id IN (
            SELECT assessment_id FROM proctoring_events 
            WHERE is_reviewed = FALSE 
            GROUP BY assessment_id 
            HAVING COUNT(*) > 3
        ))
        AND pe.is_reviewed = FALSE
        ORDER BY pe.severity DESC, pe.timestamp DESC
    """)
    
    violations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(violations)

# ============================================================================
# ANOMALY DETECTION & QUALITY METRICS
# ============================================================================

@proctor_bp.route('/anomaly-detection', methods=['GET'])
@proctor_required
def detect_anomalies():
    """Detect suspicious assessment patterns"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Assessments with unusually high violation counts
    cursor.execute("""
        SELECT 
            a.id,
            c.name as candidate_name,
            c.email as candidate_email,
            jd.title as job_title,
            COUNT(pe.id) as violation_count,
            GROUP_CONCAT(DISTINCT pe.event_type) as violation_types,
            a.overall_score,
            CASE 
                WHEN COUNT(pe.id) > 5 THEN 'critical'
                WHEN COUNT(pe.id) > 3 THEN 'high'
                WHEN COUNT(pe.id) > 1 THEN 'medium'
                ELSE 'low'
            END as suspicion_level
        FROM assessments a
        JOIN candidates c ON a.candidate_id = c.id
        LEFT JOIN job_descriptions jd ON a.job_id = jd.id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE a.status = 'completed' AND a.completed_at >= datetime('now', '-7 days')
        GROUP BY a.id
        HAVING COUNT(pe.id) > 1
        ORDER BY COUNT(pe.id) DESC
    """)
    
    suspicious_assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'suspicious_assessments': suspicious_assessments,
        'detection_timestamp': datetime.now().isoformat()
    })

@proctor_bp.route('/quality-metrics', methods=['GET'])
@proctor_required
def get_quality_metrics():
    """Get proctoring quality metrics"""
    from flask import session
    conn = get_db()
    cursor = conn.cursor()
    
    # Get this proctor's metrics if assigned
    proctor_id = request.args.get('proctor_id', session['user_id'], type=int)
    
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT a.id) as total_proctored,
            COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) as completed,
            COUNT(DISTINCT CASE WHEN a.proctoring_violations > 0 THEN a.id END) as flagged_assessments,
            AVG(a.proctoring_violations) as avg_violations_per_assessment,
            COUNT(DISTINCT pe.id) as total_violations,
            COUNT(DISTINCT CASE WHEN pe.severity = 'critical' THEN pe.id END) as critical_violations,
            COUNT(DISTINCT CASE WHEN pe.is_reviewed THEN pe.id END) as reviewed_violations
        FROM scheduled_assessments sa
        LEFT JOIN assessments a ON sa.id = a.scheduled_assessment_id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE sa.proctor_id = ? OR (? IS NULL)
    """, (proctor_id if proctor_id != session['user_id'] else session['user_id'], 
          None if proctor_id == session['user_id'] else None))
    
    metrics = dict(cursor.fetchone())
    
    conn.close()
    return jsonify(metrics)

@proctor_bp.route('/job-performance', methods=['GET'])
@proctor_required
def get_job_performance_metrics():
    """Get proctoring metrics by job type"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            jd.id,
            jd.title as job_title,
            COUNT(DISTINCT a.id) as total_assessments,
            AVG(a.overall_score) as avg_score,
            AVG(a.proctoring_violations) as avg_violations,
            COUNT(DISTINCT CASE WHEN COUNT(pe.id) > 3 THEN a.id END) as highly_flagged,
            jd.role_complexity_level as complexity
        FROM job_descriptions jd
        LEFT JOIN assessments a ON jd.id = a.job_id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE a.completed_at >= datetime('now', '-30 days')
        GROUP BY jd.id
        ORDER BY avg_violations DESC
    """)
    
    metrics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(metrics)

# ============================================================================
# ASSESSMENT ASSIGNMENT
# ============================================================================

@proctor_bp.route('/assign-assessment', methods=['POST'])
@proctor_required
def assign_assessment():
    """Assign assessment to this proctor"""
    from flask import session
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE scheduled_assessments
            SET proctor_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], data['assessment_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Assessment assigned'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

# ============================================================================
# VIOLATION STATISTICS & REPORTING
# ============================================================================

@proctor_bp.route('/violation-statistics', methods=['GET'])
@proctor_required
def get_violation_statistics():
    """Get violation type statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    period_days = request.args.get('days', 30, type=int)
    
    cursor.execute("""
        SELECT 
            event_type,
            severity,
            COUNT(*) as count,
            COUNT(DISTINCT assessment_id) as affected_assessments,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM proctoring_events 
                WHERE timestamp >= datetime('now', '-' || ? || ' days')), 2) as percentage
        FROM proctoring_events
        WHERE timestamp >= datetime('now', '-' || ? || ' days')
        GROUP BY event_type, severity
        ORDER BY count DESC
    """, (period_days, period_days))
    
    stats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'period_days': period_days,
        'statistics': stats
    })

@proctor_bp.route('/shift-summary', methods=['GET'])
@proctor_required
def get_shift_summary():
    """Get summary of assessments proctored in current shift"""
    from flask import session
    conn = get_db()
    cursor = conn.cursor()
    
    # Today's assessments
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT a.id) as total_assessments,
            COUNT(DISTINCT CASE WHEN a.status = 'completed' THEN a.id END) as completed,
            COUNT(DISTINCT CASE WHEN a.status = 'in_progress' THEN a.id END) as in_progress,
            COUNT(DISTINCT CASE WHEN pe.id IS NOT NULL THEN a.id END) as flagged,
            COUNT(DISTINCT pe.id) as total_violations,
            AVG(a.overall_score) as avg_candidate_score
        FROM scheduled_assessments sa
        LEFT JOIN assessments a ON sa.id = a.scheduled_assessment_id
        LEFT JOIN proctoring_events pe ON a.id = pe.assessment_id
        WHERE sa.proctor_id = ? AND DATE(sa.scheduled_time) = DATE('now')
    """, (session['user_id'],))
    
    summary = dict(cursor.fetchone())
    conn.close()
    
    return jsonify(summary)
