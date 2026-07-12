"""Security contract tests for the admin database inspector."""

from admin_analytics import _visible_inspection_columns


def test_user_password_hash_is_hidden_from_database_inspector():
    columns = _visible_inspection_columns(
        "users",
        ["id", "email", "password_hash", "role"],
    )

    assert columns == ["id", "email", "role"]


def test_assessment_access_token_is_hidden_from_database_inspector():
    columns = _visible_inspection_columns(
        "scheduled_assessments",
        ["id", "candidate_id", "access_token", "status"],
    )

    assert columns == ["id", "candidate_id", "status"]
