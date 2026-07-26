"""Datetime normalization contract tests."""

from datetime import datetime, timezone

from datetime_utils import parse_client_datetime


def test_naive_browser_datetime_is_interpreted_as_india_time():
    assert parse_client_datetime("2026-07-14T10:00:00") == datetime(
        2026, 7, 14, 4, 30, tzinfo=timezone.utc
    )


def test_offset_datetime_keeps_its_instant():
    assert parse_client_datetime("2026-07-14T10:00:00+05:30") == datetime(
        2026, 7, 14, 4, 30, tzinfo=timezone.utc
    )
