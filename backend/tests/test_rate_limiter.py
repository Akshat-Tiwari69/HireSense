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
