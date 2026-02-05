"""
Audit Logging Middleware
Logs all user actions for compliance and security auditing
"""

from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request
from db_helpers import log_audit
import logging

logger = logging.getLogger(__name__)


def audit_log(action, resource_type):
    """
    Decorator to automatically log user actions
    
    Usage:
        @audit_log('create', 'job')
        def create_job():
            pass
    
    Args:
        action (str): Action type (e.g., 'create', 'update', 'delete', 'view')
        resource_type (str): Resource type (e.g., 'job', 'candidate', 'user')
    
    Returns:
        Decorator function
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Execute the function first
            result = fn(*args, **kwargs)
            
            # Then log the audit entry (fire and forget)
            try:
                verify_jwt_in_request(optional=True)
                user_id = get_jwt_identity()
                claims = get_jwt()
                
                # Get user info from JWT claims
                user_email = claims.get('sub', 'unknown')
                
                # Try to get user email from database if not in claims
                if user_id:
                    from db_helpers import get_user_by_id
                    user = get_user_by_id(user_id)
                    if user:
                        user_email = user.get('email', user_email)
                
                # Extract resource ID from kwargs, args, or request
                resource_id = kwargs.get('id') or kwargs.get('job_id') or kwargs.get('candidate_id') or kwargs.get('user_id')
                
                # Get request details
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                user_agent = request.headers.get('User-Agent')
                
                # Extract details from request
                details = {}
                if request.is_json:
                    data = request.get_json(silent=True)
                    if data:
                        # Don't log sensitive information
                        details = {k: v for k, v in data.items() if k not in ['password', 'password_hash', 'token']}
                
                if request.args:
                    details['query_params'] = dict(request.args)
                
                # Log the audit entry
                log_audit(
                    user_id=int(user_id) if user_id else None,
                    user_email=user_email,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details=details if details else None,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                logger.info(f"[AUDIT] {action.upper()} {resource_type} by {user_email} (ID: {resource_id})")
                
            except Exception as e:
                # Don't fail the request if audit logging fails
                logger.error(f"[AUDIT ERROR] Failed to log audit: {str(e)}")
            
            return result
        return wrapper
    return decorator


def log_email_sent(recipient_email, recipient_name, email_type, subject, sender_user_id=None, sender_email=None, sector=None, status='sent', error_message=None):
    """
    Log email sending with sender information
    
    Args:
        recipient_email (str): Recipient's email address
        recipient_name (str): Recipient's name
        email_type (str): Type of email (e.g., 'rejection', 'assessment_invitation')
        subject (str): Email subject
        sender_user_id (int, optional): ID of user who triggered the email
        sender_email (str, optional): Email of user who triggered the email
        sector (str, optional): Sector associated with the email
        status (str): Status of email sending ('sent', 'failed')
        error_message (str, optional): Error message if failed
    """
    try:
        from db_helpers import log_email
        from db_config import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO email_logs 
               (recipient_email, recipient_name, email_type, subject, sender_user_id, sender_email, sector, status, error_message)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (recipient_email, recipient_name, email_type, subject, sender_user_id, sender_email, sector, status, error_message)
        )
        
        email_log_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        logger.info(f"[EMAIL LOG] {email_type} to {recipient_email} - Status: {status}")
        return email_log_id
        
    except Exception as e:
        logger.error(f"[EMAIL LOG ERROR] Failed to log email: {str(e)}")
        return None
