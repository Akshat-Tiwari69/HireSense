"""Input-boundary tests for candidate code execution."""

from app import app


def _active_assessment(_token):
    return {"id": 1, "status": "in_progress"}


def test_code_execution_rejects_unknown_language_without_provider_call(monkeypatch):
    monkeypatch.setattr("interviewee_answers.get_assessment_by_token", _active_assessment)

    def unexpected_provider_call(*_args, **_kwargs):
        raise AssertionError("invalid input must be rejected before calling Piston")

    monkeypatch.setattr("interviewee_answers.urllib.request.urlopen", unexpected_provider_call)
    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "active-token"},
        json={"language": "unknown", "code": "print('hello')"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Unsupported language"


def test_code_execution_rejects_oversized_source(monkeypatch):
    monkeypatch.setattr("interviewee_answers.get_assessment_by_token", _active_assessment)
    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "active-token"},
        json={"language": "python", "code": "x" * 100_001},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Code exceeds the 100 KB limit"


def test_code_execution_rejects_expired_assessment_before_provider_call(monkeypatch):
    monkeypatch.setattr(
        "interviewee_answers.get_assessment_by_token",
        lambda _token: {
            "id": 1,
            "status": "in_progress",
            "deadline_reached": True,
        },
    )

    def unexpected_provider_call(*_args, **_kwargs):
        raise AssertionError("expired assessments must not call Piston")

    monkeypatch.setattr("interviewee_answers.urllib.request.urlopen", unexpected_provider_call)
    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "expired-token"},
        json={"language": "python", "code": "print('hello')"},
    )

    assert response.status_code == 409
    assert "time limit has expired" in response.get_json()["message"]
