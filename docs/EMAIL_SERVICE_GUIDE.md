# Email Service Guide

## Overview
The Email Service module provides a comprehensive email notification system for the CYGNUSA Elite-Hire platform. It handles all candidate communications with professional HTML templates and automatic database logging.

---

## Features

### 📧 Email Types

1. **Rejection Email**
   - Sent when a candidate is not selected after resume review
   - Professional tone with optional feedback
   - Encourages future applications

2. **Assessment Invitation**
   - Sent when candidate is selected for assessment
   - Includes assessment link and scheduled time
   - Provides detailed instructions and requirements
   - ±30 minute time window notification

3. **Final Decision Email**
   - Sent after assessment completion
   - **Hire**: Congratulatory message with next steps
   - **No-Hire**: Respectful message with optional scores/feedback
   - Can include assessment scores

### 🎨 Template Features

- **Responsive HTML Design**: Works on all devices
- **Professional Branding**: CYGNUSA Elite-Hire themed
- **Plain Text Fallback**: For email clients that don't support HTML
- **Dynamic Content**: Customizable messages, scores, and instructions
- **Emojis**: Modern, friendly visual elements

### 🔒 Security & Logging

- **SMTP Authentication**: Secure email sending
- **TLS Encryption**: Email content encrypted in transit
- **Database Logging**: All emails logged to `email_logs` table
- **Error Tracking**: Failed emails logged with error messages
- **Environment Variables**: Credentials never hardcoded

---

## Installation

### 1. SMTP Configuration

The email service uses Python's built-in `smtplib` (no additional packages needed beyond standard library).

### 2. Get Gmail App Password

If using Gmail:

1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Go to App Passwords
4. Generate password for "Mail"
5. Copy the 16-character password

**Alternative SMTP Providers:**
- **SendGrid**: More reliable for production
- **AWS SES**: Cost-effective at scale
- **Custom SMTP**: Your own mail server

### 3. Configure Environment Variables

Create/update `.env` file in backend directory:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=xxxx-xxxx-xxxx-xxxx  # Gmail app password
SMTP_SENDER_NAME="CYGNUSA Elite-Hire"
```

**For Windows PowerShell:**
```powershell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="your-email@gmail.com"
$env:SMTP_PASS="your-app-password"
$env:SMTP_SENDER_NAME="CYGNUSA Elite-Hire"
```

---

## Usage

### Method 1: Convenience Functions (Recommended)

```python
from email_service import (
    send_rejection_email,
    send_assessment_invitation,
    send_final_decision_email
)

# Send rejection
send_rejection_email(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    reason="After review, we found candidates with more experience in Python."
)

# Send assessment invitation
send_assessment_invitation(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    assessment_link="http://localhost:5173/assessment/123",
    scheduled_time="January 25, 2026 at 10:00 AM EST",
    interviewer_name="Jane Smith",
    additional_info="Please ensure you have a stable internet connection."
)

# Send final decision (hired)
send_final_decision_email(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    decision="Hire",
    rationale="Excellent performance across all assessment areas.",
    next_steps="HR will contact you within 2-3 business days.",
    scores={"technical": 85, "psychometric": 90, "overall": 87}
)

# Send final decision (not hired)
send_final_decision_email(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    decision="No-Hire",
    rationale="Good performance, but looking for candidates with more experience.",
    scores={"technical": 65, "psychometric": 75, "overall": 69}
)
```

### Method 2: EmailService Class (Advanced)

```python
from email_service import EmailService

# Initialize with custom config
email_service = EmailService(
    smtp_host="smtp.sendgrid.net",
    smtp_port=587,
    smtp_user="apikey",
    smtp_pass="your-sendgrid-api-key",
    use_tls=True
)

# Send emails
email_service.send_rejection_email(...)
email_service.send_assessment_invitation(...)
email_service.send_final_decision_email(...)
```

---

## API Reference

### `send_rejection_email()`

```python
send_rejection_email(
    candidate_email: str,
    candidate_name: str,
    reason: Optional[str] = None
) -> bool
```

**Parameters:**
- `candidate_email`: Candidate's email address (required)
- `candidate_name`: Candidate's full name (required)
- `reason`: Optional rejection reason or feedback

**Returns:** `True` if sent successfully, `False` otherwise

**Example:**
```python
success = send_rejection_email(
    candidate_email="john@example.com",
    candidate_name="John Doe",
    reason="Looking for candidates with 5+ years React experience"
)
```

---

### `send_assessment_invitation()`

```python
send_assessment_invitation(
    candidate_email: str,
    candidate_name: str,
    assessment_link: str,
    scheduled_time: str,
    interviewer_name: Optional[str] = None,
    additional_info: Optional[str] = None
) -> bool
```

**Parameters:**
- `candidate_email`: Candidate's email address (required)
- `candidate_name`: Candidate's full name (required)
- `assessment_link`: Full URL to assessment page (required)
- `scheduled_time`: Human-readable time (e.g., "Jan 25, 2026 at 10:00 AM EST") (required)
- `interviewer_name`: Contact person name (optional)
- `additional_info`: Custom instructions or notes (optional)

**Returns:** `True` if sent successfully, `False` otherwise

**Example:**
```python
success = send_assessment_invitation(
    candidate_email="john@example.com",
    candidate_name="John Doe",
    assessment_link="http://localhost:5173/assessment/abc123",
    scheduled_time="January 25, 2026 at 10:00 AM EST",
    interviewer_name="Jane Smith",
    additional_info="Please use Chrome or Firefox for best experience."
)
```

---

### `send_final_decision_email()`

```python
send_final_decision_email(
    candidate_email: str,
    candidate_name: str,
    decision: str,
    rationale: Optional[str] = None,
    next_steps: Optional[str] = None,
    scores: Optional[Dict] = None
) -> bool
```

**Parameters:**
- `candidate_email`: Candidate's email address (required)
- `candidate_name`: Candidate's full name (required)
- `decision`: "Hire", "Hired", "No-Hire", or similar (required)
- `rationale`: Explanation for the decision (optional)
- `next_steps`: Information about what happens next (optional)
- `scores`: Dictionary with score data (optional)
  - Example: `{"technical": 85, "psychometric": 90, "overall": 87}`

**Returns:** `True` if sent successfully, `False` otherwise

**Examples:**

**Hired:**
```python
success = send_final_decision_email(
    candidate_email="john@example.com",
    candidate_name="John Doe",
    decision="Hire",
    rationale="Outstanding technical skills and cultural fit.",
    next_steps="Our HR team will send your offer letter within 48 hours.",
    scores={"technical": 92, "psychometric": 88, "overall": 90}
)
```

**Not Hired:**
```python
success = send_final_decision_email(
    candidate_email="john@example.com",
    candidate_name="John Doe",
    decision="No-Hire",
    rationale="Good skills, but seeking candidates with more experience.",
    scores={"technical": 68, "psychometric": 72, "overall": 70}
)
```

---

## Testing

### Test the Email Service

```bash
cd backend
python email_service.py
```

**Interactive test:**
1. Checks SMTP configuration
2. Prompts for test email address
3. Sends all three email types
4. Reports success/failure for each

**Expected output:**
```
============================================================
Testing Email Service
============================================================

SMTP Configuration:
  Host: smtp.gmail.com
  Port: 587
  User: your-email@gmail.com
  Pass: ********

Enter test email address (or press Enter to skip): test@example.com

Sending test emails to test@example.com...

1. Testing rejection email...
✅ Email sent successfully to test@example.com
   Result: ✅ Sent

2. Testing assessment invitation...
✅ Email sent successfully to test@example.com
   Result: ✅ Sent

3. Testing final decision email (hired)...
✅ Email sent successfully to test@example.com
   Result: ✅ Sent

============================================================
Email service test completed!
============================================================
```

---

## Database Logging

All email attempts are logged to the `email_logs` table:

```sql
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT,
    email_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,  -- 'sent' or 'failed'
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Query email history:**
```python
from db_helpers import get_candidate_emails

# Get all emails sent to a candidate
emails = get_candidate_emails("candidate@example.com")

for email in emails:
    print(f"{email['email_type']}: {email['status']} at {email['sent_at']}")
```

---

## Email Templates

### Template Structure

Each email has:
1. **Header**: CYGNUSA Elite-Hire branding
2. **Content**: Dynamic message with candidate name
3. **Footer**: Copyright and disclaimer

### Customizing Templates

To modify templates, edit `email_service.py`:

```python
# In the respective send_*_email() method
html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        /* Your custom CSS */
    </style>
</head>
<body>
    <!-- Your custom HTML -->
</body>
</html>
"""
```

### Branding Colors

Current color scheme:
- **Success/Invitation**: `#27ae60` (green)
- **Neutral/Info**: `#3498db` (blue)
- **Warning**: `#ffc107` (yellow)
- **Header**: `#2c3e50` (dark blue-gray)

---

## Integration with Backend

### In Interviewer Dashboard APIs (Task A8)

```python
from email_service import send_rejection_email, send_assessment_invitation

@app.route('/api/interviewer/candidates/<int:candidate_id>/reject', methods=['POST'])
@jwt_required()
def reject_candidate(candidate_id):
    # Get candidate info
    candidate = get_candidate_by_id(candidate_id)
    
    # Send rejection email
    send_rejection_email(
        candidate_email=candidate['email'],
        candidate_name=candidate['name'],
        reason=request.json.get('reason')
    )
    
    # Update database status
    update_candidate_status(candidate_id, 'rejected')
    
    return jsonify({"status": "success"})

@app.route('/api/interviewer/candidates/<int:candidate_id>/schedule', methods=['POST'])
@jwt_required()
def schedule_assessment(candidate_id):
    data = request.json
    
    # Create scheduled assessment
    scheduled_assessment_id = create_scheduled_assessment(
        candidate_id=candidate_id,
        interviewer_id=get_jwt_identity(),
        scheduled_time=data['scheduled_time']
    )
    
    # Get candidate info
    candidate = get_candidate_by_id(candidate_id)
    
    # Generate assessment link
    assessment_link = f"http://localhost:5173/assessment/{scheduled_assessment_id}"
    
    # Send invitation
    send_assessment_invitation(
        candidate_email=candidate['email'],
        candidate_name=candidate['name'],
        assessment_link=assessment_link,
        scheduled_time=data['scheduled_time'],
        interviewer_name=get_jwt()['name']
    )
    
    return jsonify({"status": "success"})
```

---

## Troubleshooting

### Issue: "SMTP credentials not configured"

**Cause**: Environment variables not set

**Solution:**
```bash
# Check if variables are set
echo $env:SMTP_USER
echo $env:SMTP_PASS

# Set them
$env:SMTP_USER="your-email@gmail.com"
$env:SMTP_PASS="your-app-password"
```

### Issue: "SMTP authentication failed"

**Causes:**
1. Wrong username/password
2. Gmail app password not generated
3. 2FA not enabled

**Solution:**
1. Verify credentials
2. Generate new Gmail app password
3. Enable 2-Factor Authentication first

### Issue: Emails not received

**Checks:**
1. Check spam/junk folder
2. Verify recipient email is correct
3. Check `email_logs` table for errors
4. Try sending to different email address

### Issue: "Connection timeout"

**Causes:**
1. Firewall blocking port 587
2. Network issues
3. SMTP server down

**Solution:**
1. Check firewall settings
2. Try different SMTP port (465 for SSL)
3. Verify SMTP server status

---

## Production Considerations

### 1. Use SendGrid or AWS SES

For production, use dedicated email service:

**SendGrid:**
```python
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your-sendgrid-api-key
```

**AWS SES:**
```python
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASS=your-ses-smtp-password
```

### 2. Rate Limiting

Implement sending limits:

```python
import time
from threading import Lock

send_lock = Lock()

def rate_limited_send(*args, **kwargs):
    with send_lock:
        result = send_email(*args, **kwargs)
        time.sleep(0.1)  # 10 emails per second max
        return result
```

### 3. Queue System

For high volume, use message queue:

```python
# Using Celery
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def send_email_async(email_type, *args, **kwargs):
    # Send email in background
    pass
```

### 4. Email Verification

Verify email addresses before sending:

```python
import re

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

### 5. Monitoring

Track email metrics:
- Send success rate
- Bounce rate
- Open rate (with tracking pixels)
- Click-through rate

---

## Best Practices

1. **Always provide plain text fallback** ✅ (Already implemented)
2. **Use environment variables for credentials** ✅ (Already implemented)
3. **Log all email attempts** ✅ (Already implemented)
4. **Handle errors gracefully** ✅ (Already implemented)
5. **Test with real emails before production**
6. **Keep templates professional and concise**
7. **Include unsubscribe links** (for marketing emails)
8. **Respect sending limits**
9. **Monitor bounce rates**
10. **Use DKIM/SPF/DMARC** (configured on domain)

---

## Cost Analysis

### Gmail (Development)
- **Free**: 500 emails/day
- **Limit**: 100 recipients per email
- **Best for**: Development and testing

### SendGrid (Production)
- **Free**: 100 emails/day
- **Essentials**: $19.95/month for 50k emails
- **Pro**: $89.95/month for 1.5M emails
- **Best for**: Production with moderate volume

### AWS SES (Scale)
- **Cost**: $0.10 per 1,000 emails
- **No monthly fee**
- **10,000 emails**: $1.00
- **100,000 emails**: $10.00
- **Best for**: High volume production

---

## Support

For issues or questions:
1. Check this guide
2. Review `email_service.py` source code
3. Check logs in `email_logs` table
4. Test with `python email_service.py`

---

**Created:** January 21, 2026  
**Task:** A7 - Email Notification Service  
**Author:** Akshat
