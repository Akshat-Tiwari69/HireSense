"""Regression tests for proctoring persistence, routes, and socket authorization."""

import base64

import psycopg2
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

import interviewee_monitoring
import proctor_routes
import proctoring_db
import websocket_server


class FakeCursor:
    def __init__(self, fetchone_values=(), fetchall_value=(), fail_on_execute=None):
        self.fetchone_values = list(fetchone_values)
        self.fetchall_value = list(fetchall_value)
        self.fail_on_execute = fail_on_execute
        self.executions = []
        self.closed = False

    def execute(self, query, params=None):
        self.executions.append((query, params))
        if self.fail_on_execute == len(self.executions):
            raise RuntimeError("database write failed")

    def fetchone(self):
        return self.fetchone_values.pop(0) if self.fetchone_values else None

    def fetchall(self):
        return self.fetchall_value

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, *args, **kwargs):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _close_connection(connection):
    connection.close()


def _jwt_app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY="test-proctor-secret-that-is-long-enough-for-sha256",
    )
    JWTManager(app)
    app.register_blueprint(proctor_routes.proctor_bp, url_prefix="/api/proctor")
    return app


def _token(app, role="proctor", user_id="7"):
    with app.app_context():
        return create_access_token(identity=user_id, additional_claims={"role": role})


def test_violation_write_and_aggregate_are_one_transaction(monkeypatch):
    cursor = FakeCursor(fetchone_values=[(9,), (41,), (3,)])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctoring_db, "get_connection", lambda: connection)
    monkeypatch.setattr(proctoring_db, "return_connection", _close_connection)

    violation_id, count = proctoring_db.record_proctoring_violation_with_count(
        9, "tab_switch", "Candidate changed tabs", "high"
    )

    assert (violation_id, count) == (41, 3)
    assert connection.committed is True
    assert connection.rolled_back is False
    assert connection.closed is True
    assert "FOR UPDATE" in cursor.executions[0][0]
    assert "INSERT INTO proctoring_violations" in cursor.executions[1][0]
    assert "UPDATE assessments" in cursor.executions[2][0]
    assert "SELECT COUNT(*)" in cursor.executions[2][0]


def test_violation_write_rolls_back_when_counter_update_fails(monkeypatch):
    cursor = FakeCursor(fetchone_values=[(9,), (41,)], fail_on_execute=3)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctoring_db, "get_connection", lambda: connection)
    monkeypatch.setattr(proctoring_db, "return_connection", _close_connection)

    with pytest.raises(proctoring_db.DatabaseError):
        proctoring_db.record_proctoring_violation(9, "tab_switch", "Changed tabs")

    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True


def test_candidate_violation_endpoint_returns_atomic_count(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(interviewee_monitoring.interviewee_monitoring_bp, url_prefix="/api")
    monkeypatch.setattr(interviewee_monitoring, "verify_assessment_access_token", lambda token, aid: True)
    monkeypatch.setattr(
        interviewee_monitoring,
        "get_assessment_by_id",
        lambda aid: {"id": aid, "status": "in_progress"},
    )
    monkeypatch.setattr(
        interviewee_monitoring,
        "record_proctoring_violation_with_count",
        lambda **kwargs: (52, 6),
    )

    response = app.test_client().post(
        "/api/assessment/11/violation",
        headers={"X-Assessment-Token": "candidate-token"},
        json={"violation_type": "tab_switch", "severity": "high"},
    )

    assert response.status_code == 201
    assert response.get_json()["data"] == {
        "violation_id": 52,
        "total_violations": 6,
        "screenshot_saved": False,
    }


def test_candidate_violation_rejects_malformed_screenshot(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(interviewee_monitoring.interviewee_monitoring_bp, url_prefix="/api")
    monkeypatch.setattr(interviewee_monitoring, "verify_assessment_access_token", lambda token, aid: True)
    monkeypatch.setattr(
        interviewee_monitoring,
        "get_assessment_by_id",
        lambda aid: {"id": aid, "status": "in_progress"},
    )

    response = app.test_client().post(
        "/api/assessment/11/violation",
        headers={"X-Assessment-Token": "candidate-token"},
        json={"violation_type": "tab_switch", "screenshot": "not-base64!"},
    )

    assert response.status_code == 400
    assert "base64" in response.get_json()["message"]


def test_candidate_violation_rejects_base64_that_is_not_an_image():
    encoded = base64.b64encode(b"this is not an image").decode("ascii")

    with pytest.raises(ValueError, match="supported image"):
        interviewee_monitoring._decode_screenshot(encoded)


def test_screenshot_storage_enforces_per_assessment_count_quota(tmp_path, monkeypatch):
    violations = tmp_path / "violations"
    violations.mkdir()
    monkeypatch.setattr(
        interviewee_monitoring,
        "get_upload_subdirectory",
        lambda *_args, **_kwargs: violations,
    )
    for index in range(interviewee_monitoring.MAX_SCREENSHOTS_PER_ASSESSMENT):
        (violations / f"violation_11_{index}.jpg").write_bytes(b"existing")

    with pytest.raises(
        interviewee_monitoring.ScreenshotQuotaExceeded,
        match="quota",
    ):
        interviewee_monitoring._save_screenshot(11, b"\xff\xd8\xffimage", "jpg")


def test_time_sync_never_rewinds_server_elapsed_time(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(interviewee_monitoring.interviewee_monitoring_bp, url_prefix="/api")
    updates = []
    monkeypatch.setattr(interviewee_monitoring, "verify_assessment_access_token", lambda token, aid: True)
    monkeypatch.setattr(
        interviewee_monitoring,
        "get_assessment_by_id",
        lambda aid: {"id": aid, "status": "in_progress"},
    )
    monkeypatch.setattr(interviewee_monitoring, "get_assessment_time_elapsed", lambda aid: 120)
    monkeypatch.setattr(
        interviewee_monitoring,
        "update_assessment_time_elapsed",
        lambda aid, elapsed: updates.append((aid, elapsed)),
    )

    response = app.test_client().post(
        "/api/assessment/11/sync-time",
        headers={"X-Assessment-Token": "candidate-token"},
        json={"time_elapsed_seconds": 60},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["server_elapsed_seconds"] == 120
    assert updates == []


def test_completed_assessments_exposes_real_section_scores(monkeypatch):
    app = _jwt_app()
    row = {
        "id": 4,
        "technical_score": 72,
        "psychometric_score": 81,
        "mcq_score": 75,
        "coding_score": 60,
        "violation_count": 2,
        "proctoring_violations": 2,
    }
    cursor = FakeCursor(fetchall_value=[row])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        "/api/proctor/completed-assessments",
        headers={"Authorization": f"Bearer {_token(app)}"},
    )

    assert response.status_code == 200
    assert response.get_json()[0]["mcq_score"] == 75
    assert response.get_json()[0]["coding_score"] == 60
    query = cursor.executions[0][0]
    assert "DISTINCT ON (question_id)" in query
    assert "DISTINCT ON (problem_id)" in query
    assert "FROM proctoring_violations" in query


@pytest.mark.parametrize(
    "path",
    [
        "/api/proctor/active-assessments",
        "/api/proctor/scheduled-assessments",
    ],
)
def test_claim_queues_only_show_own_or_unassigned_assessments(monkeypatch, path):
    app = _jwt_app()
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        path,
        headers={"Authorization": f"Bearer {_token(app, user_id='29')}"},
    )

    assert response.status_code == 200
    query, params = cursor.executions[0]
    assert "sa.proctor_id = %s OR sa.proctor_id IS NULL" in query
    assert 29 in params


def test_completed_assessments_only_show_current_proctors_history(monkeypatch):
    app = _jwt_app()
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        "/api/proctor/completed-assessments",
        headers={"Authorization": f"Bearer {_token(app, user_id='29')}"},
    )

    assert response.status_code == 200
    query, params = cursor.executions[0]
    assert "sa.proctor_id = %s" in query
    assert params[0] == 29


def test_dashboard_counts_only_assigned_work_and_claimable_queue(monkeypatch):
    app = _jwt_app()
    cursor = FakeCursor(fetchone_values=[{}])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        "/api/proctor/dashboard-stats",
        headers={"Authorization": f"Bearer {_token(app, user_id='29')}"},
    )

    assert response.status_code == 200
    query, params = cursor.executions[0]
    assert query.count("sa.proctor_id = %s OR sa.proctor_id IS NULL") == 2
    assert query.count("sa.proctor_id = %s") == 4
    assert params == (29, 29, 29, 29)


@pytest.mark.parametrize(
    "path",
    [
        "/api/proctor/anomaly-detection",
        "/api/proctor/job-performance",
        "/api/proctor/violation-statistics",
    ],
)
def test_proctor_analytics_only_use_assigned_assessments(monkeypatch, path):
    app = _jwt_app()
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        path,
        headers={"Authorization": f"Bearer {_token(app, user_id='29')}"},
    )

    assert response.status_code == 200
    query, params = cursor.executions[0]
    assert "sa.proctor_id = %s" in query
    assert 29 in params


def test_quality_metrics_cannot_query_another_proctor(monkeypatch):
    app = _jwt_app()
    response = app.test_client().get(
        "/api/proctor/quality-metrics?proctor_id=8",
        headers={"Authorization": f"Bearer {_token(app, user_id='7')}"},
    )

    assert response.status_code == 403
    assert "own quality metrics" in response.get_json()["message"]


def test_quality_metrics_only_reads_canonical_violation_log(monkeypatch):
    app = _jwt_app()
    cursor = FakeCursor(fetchone_values=[{}])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        "/api/proctor/quality-metrics",
        headers={"Authorization": f"Bearer {_token(app)}"},
    )

    assert response.status_code == 200
    query = cursor.executions[0][0]
    assert "proctoring_violations" in query
    assert "proctoring_events" not in query


def test_shift_summary_uses_sargable_today_range(monkeypatch):
    app = _jwt_app()
    cursor = FakeCursor(fetchone_values=[{}])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        "/api/proctor/shift-summary",
        headers={"Authorization": f"Bearer {_token(app)}"},
    )

    assert response.status_code == 200
    query = cursor.executions[0][0]
    assert "DATE(" not in query
    assert "sa.scheduled_time >= CURRENT_DATE" in query
    assert "sa.scheduled_time < CURRENT_DATE + INTERVAL '1 day'" in query


def test_violation_screenshot_requires_assignment_and_serves_private_file(
    monkeypatch, tmp_path
):
    app = _jwt_app()
    screenshot = tmp_path / "violations" / "proof.png"
    screenshot.parent.mkdir()
    screenshot.write_bytes(b"private-image")
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path))

    cursor = FakeCursor(
        fetchone_values=[{"screenshot_path": "/uploads/violations/proof.png"}]
    )
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().get(
        "/api/proctor/violations/12/screenshot",
        headers={"Authorization": f"Bearer {_token(app, user_id='7')}"},
    )

    assert response.status_code == 200
    assert response.data == b"private-image"
    assert cursor.executions[0][1] == (12, 7)
    assert "sa.proctor_id = %s" in cursor.executions[0][0]


def test_private_screenshot_routes_hide_storage_paths():
    rows = [{"id": 12, "screenshot_url": "/uploads/violations/proof.png"}]

    assert proctor_routes._private_screenshot_routes(rows) == [{
        "id": 12,
        "screenshot_url": "/api/proctor/violations/12/screenshot",
    }]


def test_assignment_conflict_rolls_back(monkeypatch):
    app = _jwt_app()
    cursor = FakeCursor(fetchone_values=[{"id": 13, "status": "scheduled", "proctor_id": 99}])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().post(
        "/api/proctor/assign-assessment",
        headers={"Authorization": f"Bearer {_token(app)}"},
        json={"scheduled_assessment_id": 13},
    )

    assert response.status_code == 409
    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True


def test_assignment_rejects_misnamed_assessment_identifier(monkeypatch):
    app = _jwt_app()
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(proctor_routes, "get_db", lambda: connection)
    monkeypatch.setattr(proctor_routes, "return_connection", _close_connection)

    response = app.test_client().post(
        "/api/proctor/assign-assessment",
        headers={"Authorization": f"Bearer {_token(app)}"},
        json={"assessment_id": 13},
    )

    assert response.status_code == 400
    assert "scheduled_assessment_id" in response.get_json()["message"]
    assert cursor.executions == []


def test_database_errors_are_sanitized(monkeypatch):
    app = _jwt_app()
    monkeypatch.setattr(
        proctor_routes,
        "get_db",
        lambda: (_ for _ in ()).throw(psycopg2.OperationalError("secret hostname")),
    )

    response = app.test_client().get(
        "/api/proctor/dashboard-stats",
        headers={"Authorization": f"Bearer {_token(app)}"},
    )

    assert response.status_code == 503
    assert response.get_json()["message"] == "Proctoring data is temporarily unavailable"
    assert "secret hostname" not in response.get_data(as_text=True)


@pytest.mark.parametrize(
    ("user_id", "role", "expected"),
    [
        (7, "interviewer", True),
        (8, "interviewer", False),
        (9, "proctor", True),
        (10, "proctor", False),
        (99, "admin", True),
        (99, "super_admin", True),
        (7, "sector_admin", True),
        (7, "recruiter", True),
    ],
)
def test_websocket_staff_access_respects_assignment_and_explicit_admin_roles(
    monkeypatch, user_id, role, expected
):
    cursor = FakeCursor(fetchone_values=[(7, 9, 12, 12)])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(websocket_server, "get_connection", lambda: connection)
    monkeypatch.setattr(websocket_server, "return_connection", _close_connection)

    assert websocket_server._verify_staff_assessment_access(user_id, role, 21) is expected

    query, params = cursor.executions[0]
    compact_query = " ".join(query.split())
    assert "sa.id = a.scheduled_assessment_id" in compact_query
    assert "sa.assessment_id" not in compact_query
    assert params == (user_id, 21)
    assert connection.closed is True


@pytest.mark.parametrize("role", ["recruiter", "sector_admin"])
def test_websocket_sector_reviewers_cannot_cross_sector(monkeypatch, role):
    cursor = FakeCursor(fetchone_values=[(7, 9, 13, 12)])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(websocket_server, "get_connection", lambda: connection)
    monkeypatch.setattr(websocket_server, "return_connection", _close_connection)

    assert websocket_server._verify_staff_assessment_access(7, role, 21) is False


def test_websocket_rejects_staff_not_assigned_to_assessment(monkeypatch):
    websocket_server.active_rooms.clear()
    websocket_server.connections.clear()
    websocket_server.authenticated_sockets.clear()
    monkeypatch.setattr(websocket_server, "_verify_interviewer_jwt", lambda token: (7, "proctor"))
    monkeypatch.setattr(
        websocket_server,
        "_verify_staff_assessment_access",
        lambda user_id, role, assessment_id: False,
    )
    connected = websocket_server.connect(
        "socket-1",
        {},
        {"role": "staff", "assessment_id": 21, "token": "valid-jwt"},
    )

    assert connected is False
    assert websocket_server.connections == {}
    assert websocket_server.authenticated_sockets == {}


def test_websocket_handshake_rejects_anonymous_and_duplicate_identities(monkeypatch):
    websocket_server.active_rooms.clear()
    websocket_server.connections.clear()
    websocket_server.authenticated_sockets.clear()
    monkeypatch.setattr(
        websocket_server,
        "_verify_candidate_token",
        lambda token, assessment_id: token == "valid-token" and assessment_id == 21,
    )

    assert websocket_server.connect("anonymous", {}, None) is False
    assert websocket_server.connect(
        "candidate-1",
        {},
        {
            "role": "candidate",
            "assessment_id": 21,
            "access_token": "valid-token",
        },
    ) is True
    assert websocket_server.connect(
        "candidate-duplicate",
        {},
        {
            "role": "candidate",
            "assessment_id": 21,
            "access_token": "valid-token",
        },
    ) is False


def test_candidate_socket_token_uses_forward_schedule_link(monkeypatch):
    cursor = FakeCursor(fetchone_values=[(1,)])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(websocket_server, "get_connection", lambda: connection)
    monkeypatch.setattr(websocket_server, "return_connection", _close_connection)

    assert websocket_server._verify_candidate_token("candidate-token", 21) is True

    query, params = cursor.executions[0]
    assert "a.scheduled_assessment_id = sa.id" in " ".join(query.split())
    assert "sa.assessment_id" not in query
    assert "sa.access_token_hash = %s" in " ".join(query.split())
    assert params == (
        websocket_server.hash_assessment_token("candidate-token"),
        21,
    )
    assert connection.closed is True


def test_websocket_active_list_only_contains_joined_assessment(monkeypatch):
    emitted = []
    websocket_server.active_rooms.clear()
    websocket_server.connections.clear()
    websocket_server.active_rooms.update({
        21: {"candidate": "candidate-21", "interviewers": ["staff"]},
        22: {"candidate": "candidate-22", "interviewers": ["other-staff"]},
    })
    websocket_server.connections["staff"] = {
        "type": "interviewer",
        "assessment_id": 21,
        "user_id": 7,
        "role": "proctor",
    }
    monkeypatch.setattr(
        websocket_server.sio,
        "emit",
        lambda event, data, room=None: emitted.append((event, data, room)),
    )

    websocket_server.get_active_assessments("staff", {})

    assert emitted == [(
        "active_assessments",
        {
            "assessments": [{
                "assessment_id": 21,
                "has_candidate": True,
                "interviewer_count": 1,
            }]
        },
        "staff",
    )]


def test_websocket_offer_requires_candidate_role(monkeypatch):
    emitted = []
    websocket_server.active_rooms.clear()
    websocket_server.connections.clear()
    websocket_server.active_rooms[21] = {"candidate": "candidate", "interviewers": ["staff"]}
    websocket_server.connections["staff"] = {"type": "interviewer", "assessment_id": 21}
    monkeypatch.setattr(
        websocket_server.sio,
        "emit",
        lambda event, data, room=None: emitted.append((event, data, room)),
    )

    websocket_server.webrtc_offer("staff", {"assessment_id": 21, "offer": {"sdp": "..."}})

    assert emitted == [("error", {"message": "Not authorized for this assessment"}, "staff")]
