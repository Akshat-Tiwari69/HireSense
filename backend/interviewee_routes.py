"""
Interviewee routes — thin orchestrator.

All candidate-facing assessment endpoints now live in focused sub-modules.
This file creates interviewee_bp and registers sub-blueprints so all routes
remain at /api/interviewee/... with no changes to app.py or the frontend.

Sub-module responsibilities:
  interviewee_session.py     — GET /my-assessment/<id>
                               POST /assessment/start/<id>
                               GET  /assessment/verify/<token>
                               POST /assessment/start-by-token/<token>
  interviewee_answers.py     — POST /assessment/<id>/submit-answer
                               POST /assessment/<id>/complete
  interviewee_monitoring.py  — POST /assessment/<id>/violation
                               POST /assessment/<id>/sync-time
"""

from flask import Blueprint

interviewee_bp = Blueprint('interviewee', __name__)

from interviewee_session import interviewee_session_bp
from interviewee_answers import interviewee_answers_bp
from interviewee_monitoring import interviewee_monitoring_bp

interviewee_bp.register_blueprint(interviewee_session_bp)
interviewee_bp.register_blueprint(interviewee_answers_bp)
interviewee_bp.register_blueprint(interviewee_monitoring_bp)
