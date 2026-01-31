from email_service import EmailService

email = EmailService()
result = email.send_rejection_email('penguinisreal5@gmail.com', 'Test User', 'Testing email service')
print(f"Email sent: {result}")