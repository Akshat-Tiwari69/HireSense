"""Mocked tests for email delivery and persistence. No network calls are made."""

from datetime import datetime
import smtplib
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

import email_db
import email_service
from email_service import EmailService
from user_db import DatabaseError


def _smtp_service(**overrides) -> EmailService:
    options = {
        "smtp_host": "smtp.example.test",
        "smtp_port": 587,
        "smtp_user": "sender@example.test",
        "smtp_pass": "smtp-password",
        "provider": "smtp",
    }
    options.update(overrides)
    with patch.dict("os.environ", {}, clear=True):
        return EmailService(**options)


def _resend_service(timeout_seconds=7) -> EmailService:
    with patch.dict(
        "os.environ",
        {
            "RESEND_API_KEY": "re_test_secret",
            "RESEND_FROM_EMAIL": "sender@example.test",
        },
        clear=True,
    ):
        return EmailService(provider="resend", timeout_seconds=timeout_seconds)


def test_invalid_recipient_is_not_sent_and_is_logged_once():
    service = _smtp_service()

    with (
        patch.object(service, "_send_via_smtp") as smtp_send,
        patch.object(service, "_send_via_resend") as resend_send,
        patch("email_service.log_email") as log_email,
    ):
        result = service._send_email(
            "victim@example.test\r\nBcc: attacker@example.test",
            "Candidate",
            "Subject",
            "<p>Body</p>",
        )

    assert result is False
    smtp_send.assert_not_called()
    resend_send.assert_not_called()
    log_email.assert_called_once()
    assert log_email.call_args.kwargs["status"] == "failed"
    assert log_email.call_args.kwargs["error_message"] == "invalid recipient email"


def test_successful_delivery_is_not_retried_when_database_logging_fails():
    service = _smtp_service()

    with (
        patch.object(service, "_deliver_smtp_message") as deliver,
        patch(
            "email_service.log_email",
            side_effect=RuntimeError("postgresql://user:secret@database"),
        ) as log_email,
    ):
        result = service._send_email(
            "candidate@example.test", "Candidate", "Subject", "<p>Body</p>"
        )

    assert result is True
    deliver.assert_called_once()
    log_email.assert_called_once()


def test_smtp_authentication_failure_does_not_retry_over_ssl_or_leak_details():
    service = _smtp_service()
    auth_error = smtplib.SMTPAuthenticationError(535, b"super-secret provider detail")

    with (
        patch.object(service, "_deliver_smtp_message", side_effect=auth_error) as deliver,
        patch("email_service.log_email") as log_email,
    ):
        result = service._send_email(
            "candidate@example.test", "Candidate", "Subject", "<p>Body</p>"
        )

    assert result is False
    deliver.assert_called_once()
    logged_error = log_email.call_args.kwargs["error_message"]
    assert logged_error == "SMTP authentication failed"
    assert "super-secret" not in logged_error


def test_auto_provider_falls_back_without_writing_contradictory_log_rows():
    with patch.dict(
        "os.environ",
        {
            "RESEND_API_KEY": "re_test_secret",
            "RESEND_FROM_EMAIL": "sender@example.test",
        },
        clear=True,
    ):
        service = EmailService(
            smtp_host="smtp.example.test",
            smtp_user="sender@example.test",
            smtp_pass="smtp-password",
            provider="auto",
        )

    with (
        patch.object(service, "_send_via_smtp", return_value=False) as smtp_send,
        patch.object(service, "_send_via_resend", return_value=True) as resend_send,
        patch("email_service.log_email") as log_email,
    ):
        result = service._send_email(
            "candidate@example.test", "Candidate", "Subject", "<p>Body</p>"
        )

    assert result is True
    smtp_send.assert_called_once()
    resend_send.assert_called_once()
    log_email.assert_called_once()
    assert log_email.call_args.kwargs["status"] == "sent"
    assert log_email.call_args.kwargs["error_message"] is None


def test_resend_request_uses_timeout_and_logs_one_success():
    service = _resend_service(timeout_seconds=7)
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"id": "email_123"}'

    with (
        patch("email_service.urlopen", return_value=response) as urlopen,
        patch("email_service.log_email") as log_email,
    ):
        result = service._send_email(
            "candidate@example.test", "Candidate", "Subject", "<p>Body</p>"
        )

    assert result is True
    assert urlopen.call_args.kwargs["timeout"] == 7
    request = urlopen.call_args.args[0]
    assert request.full_url == email_service.RESEND_API_URL
    log_email.assert_called_once()
    assert log_email.call_args.kwargs["status"] == "sent"


def test_resend_http_error_is_reduced_to_secret_safe_status():
    service = _resend_service()
    provider_error = HTTPError(
        email_service.RESEND_API_URL,
        401,
        "re_test_secret is invalid",
        hdrs=None,
        fp=None,
    )

    with (
        patch("email_service.urlopen", side_effect=provider_error),
        patch("email_service.log_email") as log_email,
    ):
        result = service._send_email(
            "candidate@example.test", "Candidate", "Subject", "<p>Body</p>"
        )

    assert result is False
    logged_error = log_email.call_args.kwargs["error_message"]
    assert logged_error == "Resend rejected request (HTTP 401)"
    assert "re_test_secret" not in logged_error


def test_invitation_escapes_untrusted_html_and_rejects_unsafe_links():
    service = _smtp_service()

    with patch.object(service, "_send_email", return_value=True) as send:
        assert service.send_assessment_invitation(
            "candidate@example.test",
            "<b>Candidate</b>",
            'https://example.test/assessment?next="quoted"',
            "<tomorrow>",
            interviewer_name="<Admin>",
            additional_info="<script>alert(1)</script>",
        )

    html_body = send.call_args.kwargs["html_body"]
    assert "<script>alert(1)</script>" not in html_body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_body
    assert "&lt;b&gt;Candidate&lt;/b&gt;" in html_body
    assert "&quot;quoted&quot;" in html_body

    with (
        patch.object(service, "_send_email") as send,
        patch("email_service.log_email") as log_email,
    ):
        result = service.send_assessment_invitation(
            "candidate@example.test",
            "Candidate",
            "javascript:alert(1)",
            "tomorrow",
        )

    assert result is False
    send.assert_not_called()
    assert log_email.call_args.kwargs["error_message"] == "invalid assessment link"


def test_log_email_commits_and_releases_cursor_and_connection():
    conn = MagicMock()
    cursor = conn.cursor.return_value
    cursor.fetchone.return_value = (42,)

    with (
        patch("email_db.get_connection", return_value=conn),
        patch("email_db.return_connection") as return_connection,
    ):
        log_id = email_db.log_email(
            "candidate@example.test", "Candidate", "rejection", "Subject"
        )

    assert log_id == 42
    conn.commit.assert_called_once()
    cursor.close.assert_called_once()
    return_connection.assert_called_once_with(conn)


def test_log_email_rolls_back_and_raises_generic_database_error():
    conn = MagicMock()
    cursor = conn.cursor.return_value
    cursor.execute.side_effect = RuntimeError("postgresql://user:secret@database")

    with (
        patch("email_db.get_connection", return_value=conn),
        patch("email_db.return_connection") as return_connection,
        pytest.raises(DatabaseError, match="^Error logging email$") as error,
    ):
        email_db.log_email(
            "candidate@example.test", "Candidate", "rejection", "Subject"
        )

    assert "secret" not in str(error.value)
    conn.rollback.assert_called_once()
    cursor.close.assert_called_once()
    return_connection.assert_called_once_with(conn)


def test_get_candidate_emails_releases_connection_on_success_and_failure():
    sent_at = datetime(2026, 7, 13, 12, 0)
    conn = MagicMock()
    cursor = conn.cursor.return_value
    cursor.fetchall.return_value = [
        (1, "candidate@example.test", "Candidate", "rejection", "Subject", "sent", None, sent_at)
    ]

    with (
        patch("email_db.get_connection", return_value=conn),
        patch("email_db.return_connection") as return_connection,
    ):
        history = email_db.get_candidate_emails("candidate@example.test")

    assert history[0]["sent_at"] == sent_at
    cursor.close.assert_called_once()
    return_connection.assert_called_once_with(conn)

    failed_conn = MagicMock()
    failed_cursor = failed_conn.cursor.return_value
    failed_cursor.execute.side_effect = RuntimeError("database unavailable")
    with (
        patch("email_db.get_connection", return_value=failed_conn),
        patch("email_db.return_connection") as failed_return,
        pytest.raises(DatabaseError, match="^Error retrieving candidate emails$"),
    ):
        email_db.get_candidate_emails("candidate@example.test")

    failed_cursor.close.assert_called_once()
    failed_return.assert_called_once_with(failed_conn)
