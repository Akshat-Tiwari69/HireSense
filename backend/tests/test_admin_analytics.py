"""Admin observability is bounded to product-level aggregates and logs."""

from contextlib import contextmanager

import admin_analytics
from flask_jwt_extended import create_access_token

from app import app


CANONICAL_CANDIDATE_STATUSES = {
    "applied",
    "absence_of_details",
    "pending",
    "under_review",
    "completed",
    "rejected",
    "hired",
}


def _admin_headers():
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "admin", "name": "Admin"},
        )
    return {"Authorization": f"Bearer {token}"}


def _registered_routes():
    return {rule.rule for rule in app.url_map.iter_rules()}


def test_raw_database_and_environment_admin_routes_are_not_registered():
    assert _registered_routes().isdisjoint(
        {
            "/api/admin/db/tables",
            "/api/admin/db/tables/<table_name>",
            "/api/admin/settings/env",
            "/api/admin/job-postings",
            "/api/admin/job-postings/<int:job_id>",
        }
    )


def test_bounded_admin_observability_routes_remain_registered():
    assert {
        "/api/admin/db/stats",
        "/api/admin/analytics",
        "/api/admin/email-logs",
        "/api/jobs/audit-log",
    }.issubset(_registered_routes())


def test_candidate_status_breakdown_includes_every_canonical_status(monkeypatch):
    class AnalyticsCursor:
        def execute(self, _query):
            pass

        def fetchone(self):
            return {
                "total_candidates": 7,
                "applied_candidates": 1,
                "absence_of_details_candidates": 1,
                "pending_candidates": 1,
                "under_review_candidates": 1,
                "completed_candidates": 1,
                "rejected_candidates": 1,
                "hired_candidates": 1,
                "avg_match_score": 80,
                "candidates_this_month": 2,
                "total_assessments": 3,
                "scheduled_assessments": 1,
                "in_progress_assessments": 1,
                "completed_assessments": 1,
                "avg_technical_score": 75,
                "avg_psychometric_score": 70,
                "assessments_this_month": 2,
            }

    class AnalyticsConnection:
        def cursor(self, **_kwargs):
            return AnalyticsCursor()

    @contextmanager
    def connection_factory():
        yield AnalyticsConnection()

    monkeypatch.setattr(admin_analytics, "db_connection", connection_factory)

    response = app.test_client().get("/api/admin/analytics", headers=_admin_headers())

    assert response.status_code == 200
    candidates = response.get_json()["data"]["candidates"]
    assert CANONICAL_CANDIDATE_STATUSES <= candidates.keys()
    assert sum(candidates[status] for status in CANONICAL_CANDIDATE_STATUSES) == candidates["total"]
