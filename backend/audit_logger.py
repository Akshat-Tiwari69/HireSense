"""
Audit Logging Module
Tracks all user actions and system events for compliance and debugging
"""

import json
import logging
from typing import Dict, Optional, Any
from flask import request
from db_config import get_connection, return_connection

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Centralized audit logging for all system actions
    """
    
    @staticmethod
    def log_action(
        user_id: Optional[int],
        user_email: str,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log a user action to the audit trail
        
        Args:
            user_id: ID of the user performing the action
            user_email: Email of the user
            action: Action being performed (e.g., 'create_job', 'send_email')
            entity_type: Type of entity (e.g., 'job_posting', 'candidate')
            entity_id: ID of the affected entity
            details: Additional context as dictionary
        
        Returns:
            True if logged successfully, False otherwise
        """
        conn = None
        try:
            # Get request context if available
            ip_address = None
            user_agent = None
            
            try:
                if request:
                    ip_address = request.remote_addr
                    user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
            except:
                pass  # Outside request context
            
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_logs (
                    user_id, user_email, action, entity_type, entity_id,
                    details, ip_address, user_agent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                user_email,
                action,
                entity_type,
                entity_id,
                json.dumps(details) if details else None,
                ip_address,
                user_agent
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to log audit action: {str(e)}")
            return False
        finally:
            if conn:
                return_connection(conn)
    
    @staticmethod
    def log_email_sent(
        sender_user_id: int,
        sender_email: str,
        recipient_email: str,
        email_type: str,
        sector_id: Optional[int] = None,
        details: Optional[Dict] = None
    ) -> bool:
        """
        Log an email send action
        
        Args:
            sender_user_id: ID of user who sent the email
            sender_email: Email of the sender
            recipient_email: Recipient email address
            email_type: Type of email sent
            sector_id: Sector ID if applicable
            details: Additional details
        
        Returns:
            True if logged successfully
        """
        return AuditLogger.log_action(
            user_id=sender_user_id,
            user_email=sender_email,
            action='send_email',
            entity_type='email',
            details={
                'recipient_email': recipient_email,
                'email_type': email_type,
                'sector_id': sector_id,
                **(details or {})
            }
        )
    
    @staticmethod
    def log_job_created(
        user_id: int,
        user_email: str,
        job_id: int,
        job_title: str,
        sector_id: Optional[int] = None
    ) -> bool:
        """
        Log job posting creation
        """
        return AuditLogger.log_action(
            user_id=user_id,
            user_email=user_email,
            action='create_job',
            entity_type='job_posting',
            entity_id=job_id,
            details={
                'job_title': job_title,
                'sector_id': sector_id
            }
        )
    
    @staticmethod
    def log_job_updated(
        user_id: int,
        user_email: str,
        job_id: int,
        changes: Dict
    ) -> bool:
        """
        Log job posting update
        """
        return AuditLogger.log_action(
            user_id=user_id,
            user_email=user_email,
            action='update_job',
            entity_type='job_posting',
            entity_id=job_id,
            details={'changes': changes}
        )
    
    @staticmethod
    def log_job_deleted(
        user_id: int,
        user_email: str,
        job_id: int,
        job_title: str
    ) -> bool:
        """
        Log job posting deletion
        """
        return AuditLogger.log_action(
            user_id=user_id,
            user_email=user_email,
            action='delete_job',
            entity_type='job_posting',
            entity_id=job_id,
            details={'job_title': job_title}
        )
    
    @staticmethod
    def log_candidate_created(
        user_id: int,
        user_email: str,
        candidate_id: int,
        candidate_name: str,
        candidate_email: str
    ) -> bool:
        """
        Log candidate creation
        """
        return AuditLogger.log_action(
            user_id=user_id,
            user_email=user_email,
            action='create_candidate',
            entity_type='candidate',
            entity_id=candidate_id,
            details={
                'candidate_name': candidate_name,
                'candidate_email': candidate_email
            }
        )
    
    @staticmethod
    def log_candidate_updated(
        user_id: int,
        user_email: str,
        candidate_id: int,
        changes: Dict
    ) -> bool:
        """
        Log candidate update
        """
        return AuditLogger.log_action(
            user_id=user_id,
            user_email=user_email,
            action='update_candidate',
            entity_type='candidate',
            entity_id=candidate_id,
            details={'changes': changes}
        )
    
    @staticmethod
    def log_user_created(
        admin_id: int,
        admin_email: str,
        new_user_id: int,
        new_user_email: str,
        new_user_role: str
    ) -> bool:
        """
        Log user creation
        """
        return AuditLogger.log_action(
            user_id=admin_id,
            user_email=admin_email,
            action='create_user',
            entity_type='user',
            entity_id=new_user_id,
            details={
                'new_user_email': new_user_email,
                'new_user_role': new_user_role
            }
        )
    
    @staticmethod
    def get_audit_logs(
        limit: int = 100,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> list:
        """
        Retrieve audit logs with optional filtering
        
        Args:
            limit: Maximum number of logs to return
            user_id: Filter by user ID
            action: Filter by action type
            entity_type: Filter by entity type
        
        Returns:
            List of audit log entries
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)
            
            if action:
                query += " AND action = %s"
                params.append(action)
            
            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            logs = [dict(zip(columns, row)) for row in rows]
            
            # Convert timestamps to ISO format
            for log in logs:
                if log.get('created_at'):
                    log['created_at'] = log['created_at'].isoformat()
                # Parse JSON details
                if log.get('details'):
                    try:
                        log['details'] = json.loads(log['details']) if isinstance(log['details'], str) else log['details']
                    except:
                        pass
            
            return logs
            
        except Exception as e:
            logger.error(f"Error retrieving audit logs: {str(e)}")
            return []
        finally:
            if conn:
                return_connection(conn)
