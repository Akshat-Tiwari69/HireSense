"""
Admin routes — thin orchestrator.

All admin endpoints now live in focused sub-modules. This file
creates the main admin_bp and registers sub-blueprints on it so
all routes remain at /api/admin/... with no changes needed in app.py
or any frontend API calls.

Sub-module responsibilities:
  admin_users.py       — GET/POST/PUT/DELETE /users
  admin_candidates.py  — GET/PUT/DELETE /candidates, GET /absence-of-details,
                         POST /reset-candidate-status/<id>
  admin_analytics.py   — GET /analytics, GET /email-logs,
                         GET /db/tables, GET /db/tables/<name>, GET /db/stats
  admin_settings.py    — GET/POST /settings/env
  admin_content.py     — POST /bulk-upload, POST /ai-enhance,
                         question bank CRUD (/question-bank/*)
"""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

admin_bp = Blueprint('admin', __name__)

# Register domain sub-blueprints (they inherit the /api/admin prefix from app.py)
from admin_users import admin_users_bp
from admin_candidates import admin_candidates_bp
from admin_analytics import admin_analytics_bp
from admin_settings import admin_settings_bp
from admin_content import admin_content_bp

admin_bp.register_blueprint(admin_users_bp)
admin_bp.register_blueprint(admin_candidates_bp)
admin_bp.register_blueprint(admin_analytics_bp)
admin_bp.register_blueprint(admin_settings_bp)
admin_bp.register_blueprint(admin_content_bp)


# ============================================================================
#  Legacy job posting redirects — kept here since they're 3 lines each.
#  New code should use /api/jobs/postings (job_routes.py).
# ============================================================================

@admin_bp.route('/job-postings', methods=['GET'])
@jwt_required()
def get_job_postings():
    from flask import redirect
    return redirect('/api/jobs/postings?status=all', code=307)


@admin_bp.route('/job-postings', methods=['POST'])
@jwt_required()
def create_job_posting():
    from flask import redirect
    return redirect('/api/jobs/postings', code=307)


@admin_bp.route('/job-postings/<int:job_id>', methods=['DELETE'])
@jwt_required()
def delete_job_posting(job_id):
    from flask import redirect
    return redirect(f'/api/jobs/postings/{job_id}', code=307)
