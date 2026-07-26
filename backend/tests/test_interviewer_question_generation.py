"""Focused scheduling question-generation concurrency contracts."""

from concurrent.futures import ThreadPoolExecutor as RealThreadPoolExecutor
import threading

import interviewer_routes


def test_question_generation_is_concurrent_and_bounded(monkeypatch):
    barrier = threading.Barrier(3)
    lock = threading.Lock()
    active = 0
    peak = 0

    def generate(result):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            barrier.wait(timeout=1)
            return result
        finally:
            with lock:
                active -= 1

    class Generator:
        def generate_mcq_questions(self, *_args, **_kwargs):
            return generate([{"source": "generated-mcq"}])

        def generate_coding_problem(self, *_args, **_kwargs):
            return generate({"source": "generated-code"})

        def generate_psychometric_scenarios(self, *_args, **_kwargs):
            return generate([{"source": "generated-psychometric"}])

    worker_limits = []

    def executor(*, max_workers, **kwargs):
        worker_limits.append(max_workers)
        return RealThreadPoolExecutor(max_workers=max_workers, **kwargs)

    monkeypatch.setattr(
        interviewer_routes, "get_ai_question_generator", lambda: Generator(), raising=False
    )
    monkeypatch.setattr(
        interviewer_routes, "ThreadPoolExecutor", executor, raising=False
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_mcq_questions",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_coding_problem",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_psychometric_scenarios",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
        raising=False,
    )

    result = interviewer_routes._generate_assessment_questions(
        candidate_skills=["Python"],
        job_required_skills=["PostgreSQL"],
        applied_job_title="Platform Engineer",
        is_technical_role=True,
    )

    assert peak == 3
    assert worker_limits == [3]
    assert result == {
        "mcq_questions": [{"source": "generated-mcq"}],
        "coding_problem": {"source": "generated-code"},
        "psychometric_scenarios": [{"source": "generated-psychometric"}],
    }


def test_question_generation_failures_fall_back_independently(monkeypatch):
    class Generator:
        @staticmethod
        def generate_mcq_questions(*_args, **_kwargs):
            raise TimeoutError("provider timeout")

        @staticmethod
        def generate_coding_problem(*_args, **_kwargs):
            return {"source": "generated-code"}

        @staticmethod
        def generate_psychometric_scenarios(*_args, **_kwargs):
            return []

    monkeypatch.setattr(
        interviewer_routes, "get_ai_question_generator", lambda: Generator(), raising=False
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_mcq_questions",
        lambda **_kwargs: [{"source": "fallback-mcq"}],
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_coding_problem",
        lambda **_kwargs: {"source": "fallback-code"},
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_psychometric_scenarios",
        lambda **_kwargs: [{"source": "fallback-psychometric"}],
        raising=False,
    )

    result = interviewer_routes._generate_assessment_questions(
        candidate_skills=["Python"],
        job_required_skills=[],
        applied_job_title="Engineer",
        is_technical_role=True,
    )

    assert result == {
        "mcq_questions": [{"source": "fallback-mcq"}],
        "coding_problem": {"source": "generated-code"},
        "psychometric_scenarios": [{"source": "fallback-psychometric"}],
    }
