"""
Interviewee monitoring routes — proctoring violations and assessment time sync.
"""

import os
import base64
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

try:
    from db_config import connection_pool
except ImportError:
    def connection_pool(f):
        return f

from db_helpers import (
    record_proctoring_violation, count_violations_for_assessment,
    update_assessment_time_elapsed, get_assessment_by_id,
)

logger = logging.getLogger(__name__)

interviewee_monitoring_bp = Blueprint('interviewee_monitoring', __name__)


@interviewee_monitoring_bp.route('/assessment/<int:assessment_id>/violation', methods=['POST'])
@connection_pool
def report_violation(assessment_id):
    try:
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404
        if assessment.get('status') not in ('started', 'in_progress'):
            return jsonify({'status': 'error', 'message': 'Assessment is not active'}), 400

        data = request.get_json() or {}
        violation_type = data.get('violation_type')
        description = data.get('description', '')
        severity = data.get('severity', 'medium')
        screenshot_data = data.get('screenshot')

        if not violation_type:
            return jsonify({'status': 'error', 'message': 'violation_type is required'}), 400

        screenshot_url = None
        if screenshot_data:
            try:
                screenshots_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'violations')
                os.makedirs(screenshots_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'violation_{assessment_id}_{violation_type}_{timestamp}.jpg'
                filepath = os.path.join(screenshots_dir, filename)
                img_data = screenshot_data.split(',')[1] if ',' in screenshot_data else screenshot_data
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(img_data))
                screenshot_url = f'/uploads/violations/{filename}'
            except Exception as e:
                logger.warning(f"Failed to save violation screenshot: {e}")

        violation_id = record_proctoring_violation(
            assessment_id=assessment_id, violation_type=violation_type,
            description=description, severity=severity, screenshot_url=screenshot_url
        )
        violation_count = count_violations_for_assessment(assessment_id)
        logger.info(f"Violation recorded for assessment {assessment_id}: {violation_type} ({severity}) — Total: {violation_count}")

        return jsonify({'status': 'success', 'message': 'Violation recorded', 'data': {
            'violation_id': violation_id,
            'total_violations': violation_count,
            'screenshot_saved': screenshot_url is not None
        }}), 201

    except Exception as e:
        logger.error(f"Failed to record violation: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to record violation'}), 500


@interviewee_monitoring_bp.route('/assessment/<int:assessment_id>/sync-time', methods=['POST'])
@connection_pool
def sync_assessment_time(assessment_id):
    try:
        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({'status': 'error', 'message': 'Assessment not found'}), 404
        if assessment.get('status') not in ('started', 'in_progress'):
            return jsonify({'status': 'error', 'message': 'Assessment is not active'}), 400

        data = request.get_json() or {}
        time_elapsed = data.get('time_elapsed_seconds')
        if time_elapsed is None:
            return jsonify({'status': 'error', 'message': 'time_elapsed_seconds is required'}), 400
        update_assessment_time_elapsed(assessment_id, int(time_elapsed))
        return jsonify({'status': 'success', 'message': 'Time synced'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Failed to sync time'}), 500
