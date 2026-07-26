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
  admin_analytics.py   — GET /analytics, GET /email-logs, GET /db/stats
  admin_content.py     — POST /bulk-upload, POST /ai-enhance,
                         question bank CRUD (/question-bank/*)
"""

from flask import Blueprint
admin_bp = Blueprint('admin', __name__)

# Register domain sub-blueprints (they inherit the /api/admin prefix from app.py)
from admin_users import admin_users_bp
from admin_candidates import admin_candidates_bp
from admin_analytics import admin_analytics_bp
from admin_content import admin_content_bp

admin_bp.register_blueprint(admin_users_bp)
admin_bp.register_blueprint(admin_candidates_bp)
admin_bp.register_blueprint(admin_analytics_bp)
admin_bp.register_blueprint(admin_content_bp)
