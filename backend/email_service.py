"""
Email Notification Service
Handles all email communications for the CYGNUSA Elite-Hire system
Supports Resend API (recommended for cloud) and SMTP fallback
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, Dict
from db_helpers import log_email

# Try to import resend (optional dependency)
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False

# Setup logger
logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending notifications to candidates and interviewers
    Uses Resend API (if configured) or falls back to SMTP
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_pass: Optional[str] = None,
        use_tls: bool = True
    ):
        """
        Initialize email service with SMTP configuration
        
        Args:
            smtp_host: SMTP server hostname (default: from env SMTP_HOST)
            smtp_port: SMTP server port (default: from env SMTP_PORT or 587)
            smtp_user: SMTP username/email (default: from env SMTP_USER)
            smtp_pass: SMTP password (default: from env SMTP_PASS)
            use_tls: Whether to use TLS encryption (default: True)
        """
        # Resend API configuration (preferred for cloud deployments)
        self.resend_api_key = os.environ.get('RESEND_API_KEY')
        self.resend_from_email = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        
        # SMTP configuration (fallback)
        self.smtp_host = smtp_host or os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.environ.get('SMTP_PORT', 587))
        self.smtp_user = smtp_user or os.environ.get('SMTP_USER')
        self.smtp_pass = smtp_pass or os.environ.get('SMTP_PASS')
        self.use_tls = use_tls
        
        # Sender information
        self.sender_email = self.smtp_user
        self.sender_name = os.environ.get('SMTP_SENDER_NAME', 'HireSense')
        
        # Configure Resend if available
        if self.resend_api_key and RESEND_AVAILABLE:
            resend.api_key = self.resend_api_key
            print(f"[EMAIL] ✅ Resend API configured (from: {self.resend_from_email})", flush=True)
        elif not self.smtp_user or not self.smtp_pass:
            print("[EMAIL] ⚠️ No email service configured (set RESEND_API_KEY or SMTP_USER/SMTP_PASS)", flush=True)
    
    def _send_via_resend(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_body: str,
        email_type: str
    ) -> bool:
        """Send email via Resend API"""
        try:
            print(f"[EMAIL] Sending via Resend API to {recipient_email}...", flush=True)
            
            params = {
                "from": f"{self.sender_name} <{self.resend_from_email}>",
                "to": [recipient_email],
                "subject": subject,
                "html": html_body,
            }
            
            response = resend.Emails.send(params)
            print(f"[EMAIL] ✅ Resend success! ID: {response.get('id', 'unknown')}", flush=True)
            
            log_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                email_type=email_type,
                subject=subject,
                status='sent',
                error_message=None
            )
            return True
            
        except Exception as e:
            print(f"[EMAIL] ❌ Resend failed: {e}", flush=True)
            log_email(recipient_email, recipient_name, email_type, subject, 'failed', str(e))
            return False
    
    def _send_email(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        email_type: str = "general"
    ) -> bool:
        """
        Internal method to send email via Resend API or SMTP
        
        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's name
            subject: Email subject line
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            email_type: Type of email for logging
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        print(f"[EMAIL] Starting send: {email_type} to {recipient_email}", flush=True)
        
        # Try Resend API first (works on cloud platforms like Render)
        if self.resend_api_key and RESEND_AVAILABLE:
            return self._send_via_resend(recipient_email, recipient_name, subject, html_body, email_type)
        
        # Fall back to SMTP
        if not self.smtp_user or not self.smtp_pass:
            print(f"[EMAIL] ⚠️ No email service configured, skipping email to {recipient_email}", flush=True)
            return False
        
        try:
            print(f"[EMAIL] SMTP config: {self.smtp_host}:{self.smtp_port}", flush=True)
            
            # Create message
            message = MIMEMultipart('alternative')
            message['From'] = f"{self.sender_name} <{self.sender_email}>"
            message['To'] = f"{recipient_name} <{recipient_email}>"
            message['Subject'] = subject
            
            # Add plain text version if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                message.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_body, 'html')
            message.attach(html_part)
            
            print(f"[EMAIL] Connecting to SMTP...", flush=True)
            
            # Connect to SMTP server and send (with 10 second timeout)
            try:
                print(f"[EMAIL] Trying TLS on port {self.smtp_port}...", flush=True)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(message)
                    print("[EMAIL] TLS send succeeded!", flush=True)
            except Exception as e_tls:
                print(f"[EMAIL] TLS failed: {e_tls}, trying SSL:465...", flush=True)
                with smtplib.SMTP_SSL(self.smtp_host, 465, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_pass)
                    server.send_message(message)
                    print("[EMAIL] SSL send succeeded!", flush=True)
            
            print(f"[EMAIL] ✅ Email sent successfully to {recipient_email}!", flush=True)
            
            log_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                email_type=email_type,
                subject=subject,
                status='sent',
                error_message=None
            )
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {str(e)}"
            print(f"[EMAIL] ❌ {error_msg}", flush=True)
            log_email(recipient_email, recipient_name, email_type, subject, 'failed', error_msg)
            return False
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            print(f"[EMAIL] ❌ {error_msg}", flush=True)
            log_email(recipient_email, recipient_name, email_type, subject, 'failed', error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"[EMAIL] ❌ {error_msg}", flush=True)
            logger.exception(f"❌ {error_msg}")
            log_email(recipient_email, recipient_name, email_type, subject, 'failed', error_msg)
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
            <h2>Dear {candidate_name},</h2>
            
            <p>Thank you for your interest in joining our team and for taking the time to submit your application.</p>
            
            <p>After careful review of your qualifications, we regret to inform you that we will not be moving forward with your application at this time.</p>
            
            {f'<p><strong>Feedback:</strong> {reason}</p>' if reason else ''}
            
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

{'Feedback: ' + reason if reason else ''}

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
            <h2>Dear {candidate_name},</h2>
            
            <p>Great news! After reviewing your application, we are pleased to invite you to take our technical assessment.</p>
            
            <div class="highlight">
                <p><strong>📅 Scheduled Time:</strong> {scheduled_time}</p>
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
            
            {f'<p><strong>Contact Person:</strong> {interviewer_name}</p>' if interviewer_name else ''}
            
            {f'<div class="instructions"><p>{additional_info}</p></div>' if additional_info else ''}
            
            <p><strong>Important:</strong> Please ensure you:</p>
            <ul>
                <li>Have a stable internet connection</li>
                <li>Are in a quiet environment</li>
                <li>Have completed the assessment within the scheduled time window</li>
                <li>Do not refresh the page during the assessment</li>
            </ul>
            
            <center>
                <a href="{assessment_link}" class="button">Start Assessment</a>
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

{'Contact Person: ' + interviewer_name if interviewer_name else ''}

{additional_info if additional_info else ''}

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
        is_hired = decision.lower() in ['hire', 'hired', 'selected']
        
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
            <h2>Dear {candidate_name},</h2>
            
            <div class="success-box">
                <h3>We are delighted to offer you a position with CYGNUSA!</h3>
            </div>
            
            <p>We were impressed by your performance in the assessment and believe you will be a valuable addition to our team.</p>
            
            {f'<p><strong>Assessment Feedback:</strong> {rationale}</p>' if rationale else ''}
            
            {self._format_scores_html(scores) if scores else ''}
            
            {f'<div class="success-box"><h4>Next Steps:</h4><p>{next_steps}</p></div>' if next_steps else 
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
            <h2>Dear {candidate_name},</h2>
            
            <p>Thank you for completing our assessment. We appreciate the time and effort you invested in the process.</p>
            
            <p>After careful evaluation of your assessment results, we have decided not to proceed with your application at this time.</p>
            
            {f'<div class="feedback-box"><strong>Feedback:</strong> {rationale}</div>' if rationale else ''}
            
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

{'Assessment Feedback: ' + rationale if rationale else ''}

{self._format_scores_text(scores) if scores else ''}

Next Steps:
{next_steps if next_steps else 'Our HR team will contact you within 2-3 business days with your offer letter and onboarding details.'}

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

{'Feedback: ' + rationale if rationale else ''}

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
        
        # Use list and join() instead of += concatenation (10-100x faster for multiple strings)
        score_items = ['<div class="scores"><h4>Your Assessment Scores:</h4><ul>']
        
        if 'technical' in scores:
            score_items.append(f'<li><strong>Technical Score:</strong> {scores["technical"]}%</li>')
        if 'psychometric' in scores:
            score_items.append(f'<li><strong>Psychometric Score:</strong> {scores["psychometric"]}%</li>')
        if 'overall' in scores:
            score_items.append(f'<li><strong>Overall Score:</strong> {scores["overall"]}%</li>')
        
        score_items.append('</ul></div>')
        return ''.join(score_items)
    
    def _format_scores_text(self, scores: Dict) -> str:
        """Format scores dictionary as plain text"""
        if not scores:
            return ""
        
        # Use list and join() instead of += concatenation (10-100x faster)
        text_items = ["Your Assessment Scores:"]
        
        if 'technical' in scores:
            text_items.append(f"- Technical Score: {scores['technical']}%")
        if 'psychometric' in scores:
            text_items.append(f"- Psychometric Score: {scores['psychometric']}%")
        if 'overall' in scores:
            text_items.append(f"- Overall Score: {scores['overall']}%")
        
        return "\n".join(text_items) + "\n"


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


# Test function
def test_email_service():
    """Test email service with sample data"""
    print("=" * 60)
    print("Testing Email Service")
    print("=" * 60)
    
    # Check configuration
    service = EmailService()
    print(f"\nSMTP Configuration:")
    print(f"  Host: {service.smtp_host}")
    print(f"  Port: {service.smtp_port}")
    print(f"  User: {service.smtp_user}")
    print(f"  Pass: {'*' * 8 if service.smtp_pass else 'NOT SET'}")
    
    if not service.smtp_user or not service.smtp_pass:
        print("\n⚠️  SMTP credentials not configured!")
        print("Set environment variables:")
        print("  SMTP_USER=your-email@gmail.com")
        print("  SMTP_PASS=your-app-password")
        return
    
    test_email = input("\nEnter test email address (or press Enter to skip): ").strip()
    
    if not test_email:
        print("\n✅ Configuration check passed. Skipping actual email send.")
        return
    
    print(f"\nSending test emails to {test_email}...")
    
    # Test 1: Rejection email
    print("\n1. Testing rejection email...")
    result1 = service.send_rejection_email(
        candidate_email=test_email,
        candidate_name="Test Candidate",
        reason="Thank you for your application. After review, we found other candidates with more experience in our required tech stack."
    )
    print(f"   Result: {'✅ Sent' if result1 else '❌ Failed'}")
    
    # Test 2: Assessment invitation
    print("\n2. Testing assessment invitation...")
    result2 = service.send_assessment_invitation(
        candidate_email=test_email,
        candidate_name="Test Candidate",
        assessment_link="http://localhost:5173/assessment/123",
        scheduled_time="January 25, 2026 at 10:00 AM EST",
        interviewer_name="Jane Doe"
    )
    print(f"   Result: {'✅ Sent' if result2 else '❌ Failed'}")
    
    # Test 3: Final decision (hired)
    print("\n3. Testing final decision email (hired)...")
    result3 = service.send_final_decision_email(
        candidate_email=test_email,
        candidate_name="Test Candidate",
        decision="Hire",
        rationale="Excellent performance across all assessment areas.",
        scores={"technical": 85, "psychometric": 90, "overall": 87}
    )
    print(f"   Result: {'✅ Sent' if result3 else '❌ Failed'}")
    
    print("\n" + "=" * 60)
    print("Email service test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_email_service()
