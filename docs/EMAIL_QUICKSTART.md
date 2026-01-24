# Quick Start: Email Service

## ⚡ Fast Setup (3 Minutes)

### Step 1: Get Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (if not already)
3. Search for "App passwords"
4. Select App: **Mail**, Device: **Other** (enter "Elite-Hire")
5. Copy the 16-character password

### Step 2: Configure Backend

```bash
cd backend

# Windows PowerShell
$env:SMTP_HOST="smtp.gmail.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="your-email@gmail.com"
$env:SMTP_PASS="xxxx xxxx xxxx xxxx"  # Your app password
$env:SMTP_SENDER_NAME="CYGNUSA Elite-Hire"

# Or create .env file
echo SMTP_HOST=smtp.gmail.com >> .env
echo SMTP_PORT=587 >> .env
echo SMTP_USER=your-email@gmail.com >> .env
echo SMTP_PASS=xxxx-xxxx-xxxx-xxxx >> .env
```

### Step 3: Test It

```bash
python email_service.py
```

When prompted, enter your test email address to receive sample emails.

---

## 🚀 Usage Examples

### Send Rejection Email

```python
from email_service import send_rejection_email

send_rejection_email(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    reason="Seeking candidates with more Python experience"
)
```

### Send Assessment Invitation

```python
from email_service import send_assessment_invitation

send_assessment_invitation(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    assessment_link="http://localhost:5173/assessment/123",
    scheduled_time="January 25, 2026 at 10:00 AM EST",
    interviewer_name="Jane Smith"
)
```

### Send Final Decision

```python
from email_service import send_final_decision_email

# Hired
send_final_decision_email(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    decision="Hire",
    rationale="Excellent performance!",
    scores={"technical": 90, "overall": 88}
)

# Not Hired
send_final_decision_email(
    candidate_email="candidate@example.com",
    candidate_name="John Doe",
    decision="No-Hire",
    rationale="Good effort, keep improving!",
    scores={"technical": 65, "overall": 68}
)
```

---

## ✅ What You Get

For each email type:

**Rejection:**
- Professional, respectful tone
- Optional feedback/reason
- Encourages future applications

**Assessment Invitation:**
- Congratulatory message
- Assessment link with time window
- Detailed instructions
- Contact person info

**Final Decision:**
- Hired: Welcoming message + next steps
- Not Hired: Respectful + constructive feedback
- Optional score display

---

## 📊 Email Features

- ✅ **Beautiful HTML templates** (responsive design)
- ✅ **Plain text fallback** (for all email clients)
- ✅ **Auto database logging** (tracks all sends)
- ✅ **Error handling** (logs failures)
- ✅ **Professional branding** (CYGNUSA themed)
- ✅ **Customizable content** (reasons, scores, instructions)

---

## ❓ Troubleshooting

### "SMTP credentials not configured"
```bash
# Set environment variables
$env:SMTP_USER="your-email@gmail.com"
$env:SMTP_PASS="your-app-password"
```

### "SMTP authentication failed"
- Generate new Gmail app password
- Make sure 2FA is enabled
- Use app password, not regular password

### Emails in spam
- Normal for first sends
- Recipients should mark as "Not Spam"
- Consider using SendGrid for production

---

## 📈 Next Steps

**For Akshat (Backend):**
- Integrate with Interviewer Dashboard APIs (Task A8)
- Add email functions to reject/schedule/decision endpoints
- Test with real Gmail account

**For Shaivi (Frontend):**
- Email templates are ready
- No frontend changes needed
- Emails sent automatically from backend

---

## 💰 Email Limits

**Gmail (Free):**
- 500 emails/day
- Good for development + small deployments

**Production Options:**
- **SendGrid**: $19.95/mo for 50k emails
- **AWS SES**: $0.10 per 1,000 emails
- **Mailgun**: $35/mo for 50k emails

---

**Full Guide:** See `docs/EMAIL_SERVICE_GUIDE.md`

**Created:** January 21, 2026  
**Quick Reference for:** CYGNUSA Elite-Hire Team
