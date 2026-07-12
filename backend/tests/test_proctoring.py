"""Regression tests for proctoring persistence, routes, and socket authorization."""

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


def test_legacy_event_helper_uses_canonical_violation_log(monkeypatch):
    recorded = {}
    monkeypatch.setattr(
        proctoring_db,
        "record_proctoring_violation",
        lambda **kwargs: recorded.update(kwargs),
    )

    proctoring_db.log_proctoring_event(3, "no_face", "medium", {"frames": 4})

    assert recorded == {
        "assessment_id": 3,
        "violation_type": "no_face",
        "description": {"frames": 4},
        "severity": "medium",
    }


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


def test_quality_metrics_cannot_query_another_proctor(monkeypatch):
    app = _jwt_app()
    response = app.test_client().get(
        "/api/proctor/quality-metrics?proctor_id=8",
        headers={"Authorization": f"Bearer {_token(app, user_id='7')}"},
    )

    assert response.status_code == 403
    assert "own quality metrics" in response.get_json()["message"]


def test_violation_screenshot_requires_assignment_and_serves_private_file(
    monkeypatch, tmp_path
):
    app = _jwt_app()
    screenshot = tmp_path / "violations" / "proof.png"
    screenshot.parent.mkdir()
    screenshot.write_bytes(b"private-image")
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path))

    cursor = FakeCursor(
        fetchone_values=[{"screenshot_url": "/uploads/violations/proof.png"}]
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
        json={"assessment_id": 13},
    )

    assert response.status_code == 409
    assert connection.committed is False
    assert connection.rolled_back is True
    assert connection.closed is True


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


def test_websocket_rejects_staff_not_assigned_to_assessment(monkeypatch):
    emitted = []
    websocket_server.active_rooms.clear()
    websocket_server.connections.clear()
    monkeypatch.setattr(websocket_server, "_verify_interviewer_jwt", lambda token: (7, "proctor"))
    monkeypatch.setattr(
        websocket_server,
        "_verify_staff_assessment_access",
        lambda user_id, role, assessment_id: False,
    )
    monkeypatch.setattr(
        websocket_server.sio,
        "emit",
        lambda event, data, room=None: emitted.append((event, data, room)),
    )

    websocket_server.join_as_interviewer(
        "socket-1", {"assessment_id": 21, "token": "valid-jwt"}
    )

    assert websocket_server.connections == {}
    assert emitted == [("error", {"message": "Not assigned to this active assessment"}, "socket-1")]


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
