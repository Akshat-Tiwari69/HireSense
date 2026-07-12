"""
Email Notification Service
Handles all email communications for the CYGNUSA Elite-Hire system
Supports Resend API (recommended for cloud) and SMTP fallback
"""

import json
import logging
import os
import re
import smtplib
import socket
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, parseaddr
from html import escape
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from email_db import log_email

# Setup logger
logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
VALID_PROVIDERS = {"auto", "smtp", "resend"}
EMAIL_PATTERN = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


def _bounded_float(value: object, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def _bounded_port(value: object, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if 1 <= parsed <= 65535 else default


class EmailService:
    """Send candidate notifications through a configured provider."""

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        use_tls: bool = True,
        provider: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        """Initialize provider configuration without opening network connections."""
        configured_provider = (provider or os.environ.get("EMAIL_PROVIDER", "auto")).lower()
        if configured_provider not in VALID_PROVIDERS:
            logger.warning("Unknown EMAIL_PROVIDER; falling back to automatic selection")
            configured_provider = "auto"
        self.provider = configured_provider

        self.timeout_seconds = _bounded_float(
            timeout_seconds or os.environ.get("EMAIL_TIMEOUT_SECONDS"),
            default=10.0,
            minimum=1.0,
            maximum=60.0,
        )
        self.resend_api_key = os.environ.get("RESEND_API_KEY")
        self.resend_from_email = os.environ.get(
            "RESEND_FROM_EMAIL", "onboarding@resend.dev"
        )

        self.smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
        configured_port = smtp_port or os.environ.get("SMTP_PORT", "587")
        self.smtp_port = _bounded_port(configured_port, 587)
        if str(self.smtp_port) != str(configured_port):
            logger.warning("Invalid SMTP_PORT; using port 587")
        self.smtp_ssl_port = _bounded_port(os.environ.get("SMTP_SSL_PORT", "465"), 465)
        self.smtp_user = smtp_user or os.environ.get("SMTP_USER")
        self.smtp_pass = smtp_pass or os.environ.get("SMTP_PASS")
        self.use_tls = use_tls
        self.sender_email = os.environ.get("SMTP_SENDER_EMAIL") or self.smtp_user
        self.sender_name = os.environ.get("SMTP_SENDER_NAME", "HireSense")
        self._last_provider_error = "delivery failed"

    @staticmethod
    def _is_valid_email(value: object) -> bool:
        if not isinstance(value, str):
            return False
        address = value.strip()
        if not address or len(address) > 254 or "\r" in address or "\n" in address:
            return False
        display_name, parsed_address = parseaddr(address)
        return not display_name and parsed_address == address and bool(EMAIL_PATTERN.fullmatch(address))

    @staticmethod
    def _safe_display_name(value: object) -> str:
        name = str(value or "Candidate").replace("\r", " ").replace("\n", " ").strip()
        return name[:200] or "Candidate"

    @staticmethod
    def _is_valid_http_url(value: object) -> bool:
        if not isinstance(value, str) or len(value) > 2048:
            return False
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def _smtp_is_configured(self) -> bool:
        return bool(
            self.smtp_host
            and self.smtp_user
            and self.smtp_pass
            and self._is_valid_email(self.sender_email)
        )

    def _resend_is_configured(self) -> bool:
        return bool(self.resend_api_key and self._is_valid_email(self.resend_from_email))

    def _provider_order(self) -> list[str]:
        if self.provider == "smtp":
            return ["smtp"] if self._smtp_is_configured() else []
        if self.provider == "resend":
            return ["resend"] if self._resend_is_configured() else []

        providers = []
        # Preserve the existing SMTP-first behavior in automatic mode.
        if self._smtp_is_configured():
            providers.append("smtp")
        if self._resend_is_configured():
            providers.append("resend")
        return providers

    def _safe_log_email(
        self,
        recipient_email: str,
        recipient_name: str,
        email_type: str,
        subject: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Persist one final outcome without changing the delivery result."""
        try:
            log_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                email_type=email_type,
                subject=subject,
                status=status,
                error_message=error_message,
            )
        except Exception as exc:
            # Database failures must never trigger a duplicate provider send.
            logger.error("Could not persist email outcome (%s)", type(exc).__name__)

    def _send_via_resend(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_body: str,
        email_type: str,
    ) -> bool:
        """Send through Resend with a bounded HTTP timeout."""
        del recipient_name, email_type
        payload = json.dumps(
            {
                "from": formataddr(
                    (self._safe_display_name(self.sender_name), self.resend_from_email)
                ),
                "to": [recipient_email],
                "subject": subject,
                "html": html_body,
            }
        ).encode("utf-8")
        request = Request(
            RESEND_API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "HireSense/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read(65_536)
                status_code = getattr(response, "status", None) or response.getcode()
            if not 200 <= status_code < 300:
                self._last_provider_error = f"Resend rejected request (HTTP {status_code})"
                return False
            result = json.loads(response_body or b"{}")
            if not isinstance(result, dict) or not result.get("id"):
                self._last_provider_error = "Resend returned an invalid response"
                return False
            return True
        except HTTPError as exc:
            self._last_provider_error = f"Resend rejected request (HTTP {exc.code})"
        except (URLError, TimeoutError, socket.timeout):
            self._last_provider_error = "Resend request timed out or was unreachable"
        except (json.JSONDecodeError, ValueError, OSError):
            self._last_provider_error = "Resend returned an invalid response"
        except Exception as exc:
            self._last_provider_error = "Resend delivery failed"
            logger.warning("Unexpected Resend failure (%s)", type(exc).__name__)
        return False

    def _send_email(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        email_type: str = "general",
    ) -> bool:
        """Validate, send through configured providers, and log one outcome."""
        recipient_email = str(recipient_email or "").strip()
        recipient_name = self._safe_display_name(recipient_name)
        validation_error = None
        if not self._is_valid_email(recipient_email):
            validation_error = "invalid recipient email"
        elif not subject or len(subject) > 255 or "\r" in subject or "\n" in subject:
            validation_error = "invalid email subject"
        elif not isinstance(html_body, str) or not html_body.strip():
            validation_error = "empty email body"

        if validation_error:
            self._safe_log_email(
                recipient_email,
                recipient_name,
                email_type,
                subject[:255] if isinstance(subject, str) else "",
                "failed",
                validation_error,
            )
            return False

        providers = self._provider_order()
        for provider_name in providers:
            if provider_name == "smtp":
                sent = self._send_via_smtp(
                    recipient_email,
                    recipient_name,
                    subject,
                    html_body,
                    text_body,
                    email_type,
                )
            else:
                sent = self._send_via_resend(
                    recipient_email,
                    recipient_name,
                    subject,
                    html_body,
                    email_type,
                )
            if sent:
                self._safe_log_email(
                    recipient_email, recipient_name, email_type, subject, "sent"
                )
                return True

        error_message = self._last_provider_error if providers else "no email provider configured"
        self._safe_log_email(
            recipient_email,
            recipient_name,
            email_type,
            subject,
            "failed",
            error_message,
        )
        return False

    def _deliver_smtp_message(self, message: MIMEMultipart, use_ssl: bool) -> None:
        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        port = self.smtp_ssl_port if use_ssl else self.smtp_port
        kwargs = {"timeout": self.timeout_seconds}
        if use_ssl:
            kwargs["context"] = ssl.create_default_context()
        with smtp_class(self.smtp_host, port, **kwargs) as server:
            server.ehlo()
            if self.use_tls and not use_ssl:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(message)

    def _send_via_smtp(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_body: str,
        text_body: Optional[str],
        email_type: str,
    ) -> bool:
        """Send through SMTP, falling back to SSL only for transport failures."""
        del email_type
        message = MIMEMultipart("alternative")
        message["From"] = formataddr(
            (self._safe_display_name(self.sender_name), self.sender_email)
        )
        message["To"] = formataddr((self._safe_display_name(recipient_name), recipient_email))
        message["Subject"] = subject
        if text_body:
            message.attach(MIMEText(text_body, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            self._deliver_smtp_message(message, use_ssl=self.smtp_port == self.smtp_ssl_port)
            return True
        except smtplib.SMTPAuthenticationError:
            self._last_provider_error = "SMTP authentication failed"
            return False
        except smtplib.SMTPRecipientsRefused:
            self._last_provider_error = "SMTP recipient was rejected"
            return False
        except (smtplib.SMTPSenderRefused, smtplib.SMTPDataError):
            self._last_provider_error = "SMTP sender or message was rejected"
            return False
        except (smtplib.SMTPException, OSError, TimeoutError, socket.timeout, ssl.SSLError) as exc:
            if self.use_tls and self.smtp_port != self.smtp_ssl_port:
                logger.info("SMTP TLS transport failed; trying configured SSL port")
                try:
                    self._deliver_smtp_message(message, use_ssl=True)
                    return True
                except smtplib.SMTPAuthenticationError:
                    self._last_provider_error = "SMTP authentication failed"
                    return False
                except smtplib.SMTPRecipientsRefused:
                    self._last_provider_error = "SMTP recipient was rejected"
                    return False
                except Exception as ssl_exc:
                    self._last_provider_error = "SMTP connection or delivery failed"
                    logger.warning("SMTP SSL fallback failed (%s)", type(ssl_exc).__name__)
                    return False
            self._last_provider_error = "SMTP connection or delivery failed"
            logger.warning("SMTP delivery failed (%s)", type(exc).__name__)
            return False
        except Exception as exc:
            self._last_provider_error = "SMTP delivery failed"
            logger.warning("Unexpected SMTP failure (%s)", type(exc).__name__)
            return False
    
    def send_rejection_email(
        self,
        candidate_email: str,
        candidate_name: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Send rejection email to candidate
        
        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            reason: Optional reason for rejection
        
        Returns:
            bool: True if sent successfully
        """
        subject = "Application Status - CYGNUSA Elite-Hire"
        candidate_name = self._safe_display_name(candidate_name)
        candidate_name_html = escape(candidate_name)
        reason_text = str(reason).strip()[:4_000] if reason else None
        reason_html = escape(reason_text) if reason_text else None
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #3498db; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CYGNUSA Elite-Hire</h1>
        </div>
        <div class="content">
            <h2>Dear {candidate_name_html},</h2>
            
            <p>Thank you for your interest in joining our team and for taking the time to submit your application.</p>
            
            <p>After careful review of your qualifications, we regret to inform you that we will not be moving forward with your application at this time.</p>
            
            {f'<p><strong>Feedback:</strong> {reason_html}</p>' if reason_html else ''}
            
            <p>We appreciate the effort you put into your application. We encourage you to apply for future opportunities that match your skills and experience.</p>
            
            <p>We wish you the best in your job search and future career endeavors.</p>
            
            <p>Best regards,<br>
            <strong>CYGNUSA Elite-Hire Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>&copy; 2026 CYGNUSA Elite-Hire. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Plain text version
        text_body = f"""
Dear {candidate_name},

Thank you for your interest in joining our team and for taking the time to submit your application.

After careful review of your qualifications, we regret to inform you that we will not be moving forward with your application at this time.

{'Feedback: ' + reason_text if reason_text else ''}

We appreciate the effort you put into your application. We encourage you to apply for future opportunities that match your skills and experience.

We wish you the best in your job search and future career endeavors.

Best regards,
CYGNUSA Elite-Hire Team

---
This is an automated message. Please do not reply to this email.
© 2026 CYGNUSA Elite-Hire. All rights reserved.
"""
        
        return self._send_email(
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type="rejection"
        )
    
    def send_assessment_invitation(
        self,
        candidate_email: str,
        candidate_name: str,
        assessment_link: str,
        scheduled_time: str,
        interviewer_name: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> bool:
        """
        Send assessment invitation email to candidate
        
        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            assessment_link: Link to assessment portal
            scheduled_time: Scheduled assessment time (formatted string)
            interviewer_name: Name of the interviewer (optional)
            additional_info: Additional instructions (optional)
        
        Returns:
            bool: True if sent successfully
        """
        subject = "Assessment Invitation - CYGNUSA Elite-Hire"
        candidate_name = self._safe_display_name(candidate_name)
        assessment_link = str(assessment_link or "").strip()
        if not self._is_valid_http_url(assessment_link):
            self._safe_log_email(
                str(candidate_email or "").strip(),
                candidate_name,
                "assessment_invitation",
                subject,
                "failed",
                "invalid assessment link",
            )
            return False

        scheduled_time = str(scheduled_time or "").strip()[:500]
        interviewer_text = (
            self._safe_display_name(interviewer_name) if interviewer_name else None
        )
        additional_text = str(additional_info).strip()[:8_000] if additional_info else None
        candidate_name_html = escape(candidate_name)
        assessment_link_html = escape(assessment_link, quote=True)
        scheduled_time_html = escape(scheduled_time)
        interviewer_html = escape(interviewer_text) if interviewer_text else None
        additional_html = escape(additional_text) if additional_text else None
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .highlight {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .button {{ 
            display: inline-block; 
            padding: 15px 30px; 
            background-color: #27ae60; 
            color: white !important; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0;
            font-weight: bold;
        }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
        .instructions {{ background-color: #e8f5e9; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Congratulations!</h1>
        </div>
        <div class="content">
            <h2>Dear {candidate_name_html},</h2>
            
            <p>Great news! After reviewing your application, we are pleased to invite you to take our technical assessment.</p>
            
            <div class="highlight">
                <p><strong>📅 Scheduled Time:</strong> {scheduled_time_html}</p>
                <p><strong>⏰ Assessment Window:</strong> ±30 minutes from scheduled time</p>
                <p><strong>⏱️ Duration:</strong> Approximately 60-90 minutes</p>
            </div>
            
            <div class="instructions">
                <h3>Assessment Components:</h3>
                <ul>
                    <li><strong>Multiple Choice Questions:</strong> 10 technical questions</li>
                    <li><strong>Coding Challenge:</strong> 1 programming problem</li>
                    <li><strong>Psychometric Assessment:</strong> 3 scenario-based questions</li>
                </ul>
            </div>
            
            {f'<p><strong>Contact Person:</strong> {interviewer_html}</p>' if interviewer_html else ''}
            
            {f'<div class="instructions"><p>{additional_html}</p></div>' if additional_html else ''}
            
            <p><strong>Important:</strong> Please ensure you:</p>
            <ul>
                <li>Have a stable internet connection</li>
                <li>Are in a quiet environment</li>
                <li>Have completed the assessment within the scheduled time window</li>
                <li>Do not refresh the page during the assessment</li>
            </ul>
            
            <center>
                <a href="{assessment_link_html}" class="button">Start Assessment</a>
            </center>
            
            <p>If you need to reschedule or have any questions, please contact us as soon as possible.</p>
            
            <p>Good luck! We're excited to see your skills in action.</p>
            
            <p>Best regards,<br>
            <strong>CYGNUSA Elite-Hire Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>&copy; 2026 CYGNUSA Elite-Hire. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Plain text version
        text_body = f"""
🎉 Congratulations!

Dear {candidate_name},

Great news! After reviewing your application, we are pleased to invite you to take our technical assessment.

📅 Scheduled Time: {scheduled_time}
⏰ Assessment Window: ±30 minutes from scheduled time
⏱️ Duration: Approximately 60-90 minutes

Assessment Components:
- Multiple Choice Questions: 10 technical questions
- Coding Challenge: 1 programming problem
- Psychometric Assessment: 3 scenario-based questions

{'Contact Person: ' + interviewer_text if interviewer_text else ''}

{additional_text if additional_text else ''}

Important: Please ensure you:
- Have a stable internet connection
- Are in a quiet environment
- Have completed the assessment within the scheduled time window
- Do not refresh the page during the assessment

Assessment Link: {assessment_link}

If you need to reschedule or have any questions, please contact us as soon as possible.

Good luck! We're excited to see your skills in action.

Best regards,
CYGNUSA Elite-Hire Team

---
This is an automated message. Please do not reply to this email.
© 2026 CYGNUSA Elite-Hire. All rights reserved.
"""
        
        return self._send_email(
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type="assessment_invitation"
        )
    
    def send_final_decision_email(
        self,
        candidate_email: str,
        candidate_name: str,
        decision: str,
        rationale: Optional[str] = None,
        next_steps: Optional[str] = None,
        scores: Optional[Dict] = None
    ) -> bool:
        """
        Send final hiring decision email to candidate
        
        Args:
            candidate_email: Candidate's email address
            candidate_name: Candidate's name
            decision: "Hire" or "No-Hire"
            rationale: Explanation for the decision (optional)
            next_steps: Information about next steps (optional)
            scores: Assessment scores dictionary (optional)
        
        Returns:
            bool: True if sent successfully
        """
        candidate_name = self._safe_display_name(candidate_name)
        candidate_name_html = escape(candidate_name)
        rationale_text = str(rationale).strip()[:8_000] if rationale else None
        rationale_html = escape(rationale_text) if rationale_text else None
        next_steps_text = str(next_steps).strip()[:8_000] if next_steps else None
        next_steps_html = escape(next_steps_text) if next_steps_text else None
        is_hired = str(decision or "").strip().lower() in {"hire", "hired", "selected"}
        
        subject = f"{'Congratulations' if is_hired else 'Assessment Results'} - CYGNUSA Elite-Hire"
        
        if is_hired:
            # Positive decision email
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #27ae60; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .success-box {{ background-color: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
        .scores {{ background-color: #fff; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Congratulations!</h1>
        </div>
        <div class="content">
            <h2>Dear {candidate_name_html},</h2>
            
            <div class="success-box">
                <h3>We are delighted to offer you a position with CYGNUSA!</h3>
            </div>
            
            <p>We were impressed by your performance in the assessment and believe you will be a valuable addition to our team.</p>
            
            {f'<p><strong>Assessment Feedback:</strong> {rationale_html}</p>' if rationale_html else ''}
            
            {self._format_scores_html(scores) if scores else ''}
            
            {f'<div class="success-box"><h4>Next Steps:</h4><p>{next_steps_html}</p></div>' if next_steps_html else
            '<div class="success-box"><h4>Next Steps:</h4><p>Our HR team will contact you within 2-3 business days with your offer letter and onboarding details.</p></div>'}
            
            <p>Welcome to the team! We look forward to working with you.</p>
            
            <p>Best regards,<br>
            <strong>CYGNUSA Elite-Hire Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>&copy; 2026 CYGNUSA Elite-Hire. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        else:
            # Negative decision email
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .footer {{ text-align: center; padding: 20px; color: #777; font-size: 12px; }}
        .scores {{ background-color: #fff; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        .feedback-box {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Assessment Results</h1>
        </div>
        <div class="content">
            <h2>Dear {candidate_name_html},</h2>
            
            <p>Thank you for completing our assessment. We appreciate the time and effort you invested in the process.</p>
            
            <p>After careful evaluation of your assessment results, we have decided not to proceed with your application at this time.</p>
            
            {f'<div class="feedback-box"><strong>Feedback:</strong> {rationale_html}</div>' if rationale_html else ''}
            
            {self._format_scores_html(scores) if scores else ''}
            
            <p>We encourage you to continue developing your skills and apply for future opportunities with us. Your dedication to completing the assessment is commendable.</p>
            
            <p>We wish you the best in your job search and future career endeavors.</p>
            
            <p>Best regards,<br>
            <strong>CYGNUSA Elite-Hire Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message. Please do not reply to this email.</p>
            <p>&copy; 2026 CYGNUSA Elite-Hire. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Plain text version
        if is_hired:
            text_body = f"""
🎉 Congratulations!

Dear {candidate_name},

We are delighted to offer you a position with CYGNUSA!

We were impressed by your performance in the assessment and believe you will be a valuable addition to our team.

{'Assessment Feedback: ' + rationale_text if rationale_text else ''}

{self._format_scores_text(scores) if scores else ''}

Next Steps:
{next_steps_text if next_steps_text else 'Our HR team will contact you within 2-3 business days with your offer letter and onboarding details.'}

Welcome to the team! We look forward to working with you.

Best regards,
CYGNUSA Elite-Hire Team
"""
        else:
            text_body = f"""
Assessment Results

Dear {candidate_name},

Thank you for completing our assessment. We appreciate the time and effort you invested in the process.

After careful evaluation of your assessment results, we have decided not to proceed with your application at this time.

{'Feedback: ' + rationale_text if rationale_text else ''}

{self._format_scores_text(scores) if scores else ''}

We encourage you to continue developing your skills and apply for future opportunities with us.

We wish you the best in your job search and future career endeavors.

Best regards,
CYGNUSA Elite-Hire Team
"""
        
        return self._send_email(
            recipient_email=candidate_email,
            recipient_name=candidate_name,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            email_type="final_decision"
        )
    
    def _format_scores_html(self, scores: Dict) -> str:
        """Format scores dictionary as HTML"""
        if not scores:
            return ""
        
        html = '<div class="scores"><h4>Your Assessment Scores:</h4><ul>'
        
        if 'technical' in scores:
            html += f'<li><strong>Technical Score:</strong> {escape(str(scores["technical"]))}%</li>'
        if 'psychometric' in scores:
            html += f'<li><strong>Psychometric Score:</strong> {escape(str(scores["psychometric"]))}%</li>'
        if 'overall' in scores:
            html += f'<li><strong>Overall Score:</strong> {escape(str(scores["overall"]))}%</li>'
        
        html += '</ul></div>'
        return html
    
    def _format_scores_text(self, scores: Dict) -> str:
        """Format scores dictionary as plain text"""
        if not scores:
            return ""
        
        text = "Your Assessment Scores:\n"
        
        if 'technical' in scores:
            text += f"- Technical Score: {scores['technical']}%\n"
        if 'psychometric' in scores:
            text += f"- Psychometric Score: {scores['psychometric']}%\n"
        if 'overall' in scores:
            text += f"- Overall Score: {scores['overall']}%\n"
        
        return text


# Convenience functions for easy import
_email_service = None

def get_email_service() -> EmailService:
    """Get or create email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def send_rejection_email(candidate_email: str, candidate_name: str, reason: Optional[str] = None) -> bool:
    """Send rejection email - convenience function"""
    return get_email_service().send_rejection_email(candidate_email, candidate_name, reason)


def send_assessment_invitation(
    candidate_email: str,
    candidate_name: str,
    assessment_link: str,
    scheduled_time: str,
    interviewer_name: Optional[str] = None,
    additional_info: Optional[str] = None
) -> bool:
    """Send assessment invitation - convenience function"""
    return get_email_service().send_assessment_invitation(
        candidate_email, candidate_name, assessment_link, scheduled_time,
        interviewer_name, additional_info
    )


def send_final_decision_email(
    candidate_email: str,
    candidate_name: str,
    decision: str,
    rationale: Optional[str] = None,
    next_steps: Optional[str] = None,
    scores: Optional[Dict] = None
) -> bool:
    """Send final decision email - convenience function"""
    return get_email_service().send_final_decision_email(
        candidate_email, candidate_name, decision, rationale, next_steps, scores
    )
