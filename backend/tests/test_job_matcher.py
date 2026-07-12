"""Deterministic scoring and AI-boundary tests for job matching."""

import job_matcher


def matcher_without_ai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    return job_matcher.JobMatcher()


def test_required_only_job_can_reach_full_skill_score(monkeypatch):
    matcher = matcher_without_ai(monkeypatch)

    score = matcher._rule_based_score(
        ["Python"],
        0,
        {
            "required_skills": ["Python"],
            "preferred_skills": [],
            "min_experience": 0,
            "max_experience": 0,
            "experience_level": "junior",
        },
    )

    assert score["skill_match_score"] == 100
    assert score["experience_match_score"] == 100
    assert score["match_score"] == 100


def test_skill_aliases_and_duplicates_are_normalised(monkeypatch):
    matcher = matcher_without_ai(monkeypatch)

    score = matcher._rule_based_score(
        ["React.js", "Node.js", "React.js"],
        3,
        {
            "required_skills": ["react", "node"],
            "preferred_skills": [],
            "min_experience": 2,
            "max_experience": 5,
            "experience_level": "mid",
        },
    )

    assert score["skill_match_score"] == 100


def test_matching_returns_every_active_job_not_only_ai_top_five(monkeypatch):
    matcher = matcher_without_ai(monkeypatch)
    jobs = [
        {
            "id": job_id,
            "title": f"Job {job_id}",
            "required_skills": ["Python"],
            "min_experience": 0,
            "max_experience": 5,
            "experience_level": "mid",
        }
        for job_id in range(1, 8)
    ]

    matches = matcher.match_candidate_to_jobs(["Python"], 3, "", "", jobs)

    assert len(matches) == 7
    assert {match["job_id"] for match in matches} == set(range(1, 8))


def test_ai_results_are_bounded_deduplicated_and_authorized(monkeypatch):
    matcher = matcher_without_ai(monkeypatch)

    validated = matcher._validated_ai_matches(
        [
            {"job_id": 1, "match_score": 900, "ai_reasoning": "x" * 2000},
            {"job_id": 1, "match_score": 5, "ai_reasoning": "duplicate"},
            {"job_id": 99, "match_score": 100, "ai_reasoning": "unknown"},
            {"job_id": "bad", "match_score": 50},
        ],
        {1, 2},
    )

    assert set(validated) == {1}
    assert validated[1]["match_score"] == 100
    assert len(validated[1]["ai_reasoning"]) == 1000


def test_explicit_zero_max_experience_is_not_treated_as_missing(monkeypatch):
    matcher = matcher_without_ai(monkeypatch)

    score = matcher._rule_based_score(
        ["Python"],
        5,
        {
            "required_skills": ["Python"],
            "min_experience": 0,
            "max_experience": 0,
            "experience_level": "junior",
        },
    )

    assert score["experience_match_score"] == 50
