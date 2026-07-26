"""Input-boundary tests for candidate code execution."""

import json

import pytest

from app import app
import interviewee_answers
from interviewee_session import _format_coding_problem


def _active_assessment(_token):
    return {"assessment_id": 1, "status": "in_progress"}


def test_session_formats_legacy_signature_as_the_only_runnable_language():
    problem = _format_coding_problem({
        "id": 5,
        "title": "Count distinct elements",
        "description": "Return the count.",
        "difficulty": "easy",
        "starter_code": {
            "function_signature": "def count_distinct_elements(arr: List[int]) -> int:",
            "java": "public int countDistinctElements(int[] arr) { return 0; }",
        },
        "test_cases": [],
    })

    assert set(problem["starter_code"]) == {"python"}


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


def test_code_execution_is_unavailable_when_runner_is_disabled(monkeypatch):
    monkeypatch.setattr("interviewee_answers.get_assessment_by_token", _active_assessment)
    monkeypatch.setattr("interviewee_answers.code_runner_enabled", lambda: False)
    monkeypatch.setattr(
        "interviewee_answers.urllib.request.urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("disabled runner was called")
        ),
    )

    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "active-token"},
        json={"language": "python", "code": "print('hello')"},
    )

    assert response.status_code == 503
    assert response.get_json()["message"] == (
        "Coding assessments are temporarily unavailable."
    )


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


def test_code_execution_runs_only_assigned_visible_example(monkeypatch):
    monkeypatch.setattr("interviewee_answers.get_assessment_by_token", _active_assessment)
    monkeypatch.setattr(
        "interviewee_answers.get_assessment_questions",
        lambda assessment_id: {
            "coding_problem": {
                "id": 5,
                "starter_code": {"python": "def solve(value):\n    pass"},
                "test_cases": [
                    {"input": "2", "expected": "4"},
                    {"input": "99", "expected": "hidden", "is_hidden": True},
                ],
            }
        } if assessment_id == 1 else None,
    )
    captured = {}

    class ProviderResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, _limit):
            return json.dumps({
                "run": {"stdout": "4\n", "stderr": "", "code": 0},
            }).encode()

    def provider_call(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return ProviderResponse()

    monkeypatch.setattr("interviewee_answers.urllib.request.urlopen", provider_call)
    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "active-token"},
        json={
            "language": "python",
            "code": "def solve(value):\n    return value * 2",
            "problem_id": 5,
            "test_case_index": 0,
        },
    )

    assert response.status_code == 200
    assert response.get_json()["data"] == {
        "exit_code": 0,
        "expected": "4",
        "passed": True,
        "stderr": "",
        "stdout": "4",
    }
    payload = captured["payload"]
    assert "print(solve(2))" in payload["files"][0]["content"]
    assert "99" not in payload["files"][0]["content"]
    assert payload["version"] == "*"
    assert payload["run_timeout"] == 3_000
    assert payload["run_memory_limit"] == 256 * 1024 * 1024


def test_code_execution_normalizes_legacy_function_signature(monkeypatch):
    monkeypatch.setattr("interviewee_answers.get_assessment_by_token", _active_assessment)
    monkeypatch.setattr(
        "interviewee_answers.get_assessment_questions",
        lambda _assessment_id: {
            "coding_problem": {
                "id": 5,
                "starter_code": {
                    "function_signature": "def count_distinct_elements(arr: List[int]) -> int:"
                },
                "test_cases": [{"input": "[1, 1, 2]", "expected": "2"}],
            }
        },
    )
    captured = {}

    class ProviderResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self, _limit):
            return json.dumps({
                "run": {"stdout": "2\n", "stderr": "", "code": 0},
            }).encode()

    def provider_call(request, timeout):
        captured["source"] = json.loads(request.data)["files"][0]["content"]
        captured["timeout"] = timeout
        return ProviderResponse()

    monkeypatch.setattr("interviewee_answers.urllib.request.urlopen", provider_call)
    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "active-token"},
        json={
            "language": "python",
            "code": "def count_distinct_elements(arr):\n    return len(set(arr))",
            "problem_id": 5,
            "test_case_index": 0,
        },
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["passed"] is True
    assert "print(count_distinct_elements([1, 1, 2]))" in captured["source"]


def test_code_execution_does_not_expose_hidden_case_by_index(monkeypatch):
    monkeypatch.setattr("interviewee_answers.get_assessment_by_token", _active_assessment)
    monkeypatch.setattr(
        "interviewee_answers.get_assessment_questions",
        lambda _assessment_id: {
            "coding_problem": {
                "id": 5,
                "starter_code": {"python": "def solve(value):\n    pass"},
                "test_cases": [
                    {"input": "2", "expected": "4"},
                    {"input": "99", "expected": "hidden", "is_hidden": True},
                ],
            }
        },
    )

    response = app.test_client().post(
        "/api/interviewee/run-code",
        headers={"X-Assessment-Token": "active-token"},
        json={
            "language": "python",
            "code": "def solve(value):\n    return value * 2",
            "problem_id": 5,
            "test_case_index": 1,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Unknown visible test case"


def test_piston_transport_failure_is_not_treated_as_candidate_failure(monkeypatch):
    monkeypatch.setattr(
        interviewee_answers.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("runner offline")),
    )

    with pytest.raises(RuntimeError, match="evaluation service is unavailable"):
        interviewee_answers._run_one_piston(
            "def solve(value):\n    return value\nprint(solve(1))",
            "python",
        )


def test_piston_candidate_runtime_error_remains_a_failed_test(monkeypatch):
    class ProviderResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        @staticmethod
        def read(_limit):
            return json.dumps({
                "run": {"stdout": "", "stderr": "NameError", "code": 1},
            }).encode()

    monkeypatch.setattr(
        interviewee_answers.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: ProviderResponse(),
    )

    assert interviewee_answers._run_one_piston("print(missing)", "python") is None


def test_server_evaluation_propagates_runner_outage(monkeypatch):
    monkeypatch.setattr(
        interviewee_answers,
        "_run_one_piston",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("runner offline")),
    )

    with pytest.raises(RuntimeError, match="runner offline"):
        interviewee_answers._evaluate_server_side(
            "def solve(value):\n    return value * 2",
            "python",
            [{"input": "2", "expected": "4"}],
            {"python": "def solve(value):\n    pass"},
        )
