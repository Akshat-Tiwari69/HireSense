"""
Test Email Service
Sends a test email to verify email configuration is working
"""

import os
import sys
from email_service import EmailService

def test_email():
    """Send a test email"""
    print("=" * 60)
    print("EMAIL SERVICE TEST")
    print("=" * 60)
    
    # Get recipient email
    test_email = input("\nEnter recipient email address: ").strip()
    
    if not test_email:
        print(" No email address provided")
        return
    
    print(f"\n Sending test email to: {test_email}")
    print("=" * 60)
    
    # Initialize email service
    email_service = EmailService()
    
    # Prepare test email
    subject = "HireSense - Email Service Test"
    html_body = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                     color: white; padding: 30px; text-align: center; border-radius: 10px; }
            .content { padding: 30px; background: #f9f9f9; border-radius: 10px; margin-top: 20px; }
            .success { color: #10b981; font-size: 24px; font-weight: bold; }
            .footer { text-align: center; color: #666; margin-top: 30px; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1> Email Service Test</h1>
                <p>HireSense Platform</p>
            </div>
            <div class="content">
                <p class="success">Success! </p>
                <p>If you're reading this, your email service is working correctly.</p>
                <p><strong>Test Details:</strong></p>
                <ul>
                    <li>Service: HireSense Email Service</li>
                    <li>Configuration: SMTP (Gmail)</li>
                    <li>Status:  Working</li>
                </ul>
                <p>You can now send assessment invitations, reminders, and results to candidates.</p>
            </div>
            <div class="footer">
                <p>This is a test email from the HireSense Platform</p>
                <p>© 2026 HireSense. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        # Send the email
        success = email_service._send_email(
            recipient_email=test_email,
            recipient_name="Test User",
            subject=subject,
            html_body=html_body,
            email_type="test"
        )
        
        if success:
            print("\n TEST EMAIL SENT SUCCESSFULLY!")
            print(f"   Check inbox: {test_email}")
            print("   Email service is working correctly")
        else:
            print("\n FAILED TO SEND TEST EMAIL")
            print("   Please check your email configuration")
            
    except Exception as e:
        print(f"\n ERROR: {e}")
        print("   Email service encountered an error")

if __name__ == "__main__":
    test_email()
