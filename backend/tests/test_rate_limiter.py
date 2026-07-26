"""Rate-limiter response contract tests."""

from flask import Flask, abort

from rate_limiter import init_rate_limiting


def test_rate_limit_errors_are_json(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    test_app = Flask(__name__)

    @test_app.get("/limited")
    def limited():
        abort(429)

    init_rate_limiting(test_app)
    response = test_app.test_client().get("/limited")

    assert response.status_code == 429
    assert response.get_json() == {
        "status": "error",
        "message": "Too many requests. Please try again later.",
    }


def test_named_endpoint_limit_wraps_the_registered_view(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    test_app = Flask(__name__)
    test_app.add_url_rule(
        "/login",
        endpoint="auth.login",
        view_func=lambda: {"status": "ok"},
        methods=["POST"],
    )
    init_rate_limiting(test_app)

    client = test_app.test_client()
    statuses = [client.post("/login").status_code for _ in range(11)]

    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429


def test_coding_submission_limit_is_scoped_without_throttling_other_answers(
    monkeypatch,
):
    monkeypatch.delenv("REDIS_URL", raising=False)
    test_app = Flask(__name__)
    test_app.add_url_rule(
        "/assessment/<int:assessment_id>/submit-answer",
        endpoint="interviewee.interviewee_answers.submit_answer",
        view_func=lambda assessment_id: {"status": "ok", "assessment_id": assessment_id},
        methods=["POST"],
    )
    init_rate_limiting(test_app)
    client = test_app.test_client()
    token_a = {"X-Assessment-Token": "candidate-token-a"}

    coding_statuses = [
        client.post(
            "/assessment/7/submit-answer",
            headers=token_a,
            json={"type": "coding"},
        ).status_code
        for _ in range(7)
    ]

    assert coding_statuses[:6] == [200] * 6
    assert coding_statuses[6] == 429
    assert client.post(
        "/assessment/7/submit-answer",
        headers=token_a,
        json={"type": "mcq"},
    ).status_code == 200
    assert client.post(
        "/assessment/7/submit-answer",
        headers={"X-Assessment-Token": "candidate-token-b"},
        json={"type": "coding"},
    ).status_code == 200
    assert client.post(
        "/assessment/8/submit-answer",
        headers=token_a,
        json={"type": "coding"},
    ).status_code == 200


def test_screenshot_limit_is_token_scoped_without_throttling_plain_events(
    monkeypatch,
):
    monkeypatch.delenv("REDIS_URL", raising=False)
    test_app = Flask(__name__)
    test_app.add_url_rule(
        "/assessment/<int:assessment_id>/violation",
        endpoint="interviewee.interviewee_monitoring.report_violation",
        view_func=lambda assessment_id: {"status": "ok", "assessment_id": assessment_id},
        methods=["POST"],
    )
    init_rate_limiting(test_app)
    client = test_app.test_client()
    token_a = {"X-Assessment-Token": "candidate-token-a"}

    statuses = [
        client.post(
            "/assessment/7/violation",
            headers=token_a,
            json={"violation_type": "tab_hidden", "screenshot": "image-data"},
        ).status_code
        for _ in range(7)
    ]

    assert statuses[:6] == [200] * 6
    assert statuses[6] == 429
    assert client.post(
        "/assessment/7/violation",
        headers=token_a,
        json={"violation_type": "camera_interrupted"},
    ).status_code == 200
    assert client.post(
        "/assessment/7/violation",
        headers={"X-Assessment-Token": "candidate-token-b"},
        json={"violation_type": "tab_hidden", "screenshot": "image-data"},
    ).status_code == 200
