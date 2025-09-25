"""
Database service for QuoteSnap application.

This module handles all database operations including
table creation, data insertion, querying, and migrations.
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service class for handling database operations.
    """
    
    def __init__(self, db_path: str = "database/quotesnap.db"):
        """
        Initialize database service with database path.
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        logger.info(f"Database service initialized with path: {db_path}")
    
    def connect(self) -> bool:
        """
        Establish connection to SQLite database.
        
        Returns:
            bool: True if connection successful
        """
        # TODO: Implement database connection
        # - Create SQLite connection
        # - Set up connection settings (foreign keys, etc.)
        # - Test connection with simple query
        # - Handle connection errors
        
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """
        Close database connection.
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def create_tables(self) -> bool:
        """
        Create all required database tables.
        
        Returns:
            bool: True if tables created successfully
        """
        # TODO: Implement table creation
        # - Create emails table for raw email data
        # - Create quotation_requests table for extracted data
        # - Create quotation_history table for generated quotations
        # - Create logs table for audit trail
        # - Create indexes for performance
        
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Emails table - stores raw email metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    gmail_id TEXT UNIQUE NOT NULL,
                    subject TEXT,
                    sender TEXT,
                    recipient TEXT,
                    received_at DATETIME,
                    body_text TEXT,
                    body_html TEXT,
                    attachments TEXT,  -- JSON array of attachment info
                    status TEXT DEFAULT 'received',
                    processed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Quotation requests table - stores extracted/structured data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotation_requests (
                    id TEXT PRIMARY KEY,
                    email_id TEXT NOT NULL,
                    client_name TEXT,
                    client_email TEXT,
                    client_phone TEXT,
                    client_company TEXT,
                    requirements TEXT,  -- JSON array of requirement items
                    deadline DATE,
                    priority TEXT DEFAULT 'normal',
                    estimated_value DECIMAL(10,2),
                    status TEXT DEFAULT 'pending',
                    extracted_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (email_id) REFERENCES emails (id)
                )
            ''')
            
            # Quotation history table - stores generated quotations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotation_history (
                    id TEXT PRIMARY KEY,
                    quotation_request_id TEXT NOT NULL,
                    quotation_number TEXT UNIQUE,
                    items TEXT,  -- JSON array of quotation items
                    total_amount DECIMAL(10,2),
                    excel_file_path TEXT,
                    pdf_file_path TEXT,
                    status TEXT DEFAULT 'generated',
                    generated_at DATETIME,
                    sent_at DATETIME,
                    version INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (quotation_request_id) REFERENCES quotation_requests (id)
                )
            ''')
            
            # Logs table - stores audit trail and system events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    category TEXT,
                    message TEXT NOT NULL,
                    details TEXT,  -- JSON object with additional details
                    entity_type TEXT,  -- email, quotation, system, etc.
                    entity_id TEXT,
                    user_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_gmail_id ON emails (gmail_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_received_at ON emails (received_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_status ON emails (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotation_requests_email_id ON quotation_requests (email_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotation_requests_status ON quotation_requests (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_quotation_history_request_id ON quotation_history (quotation_request_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs (created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_entity ON logs (entity_type, entity_id)')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            return False
    
    def insert_email(self, email_data: Dict) -> Optional[str]:
        """
        Insert a new email record into the database.
        
        Args:
            email_data (Dict): Email data dictionary
            
        Returns:
            Optional[str]: Email ID if inserted successfully, None otherwise
        """
        # TODO: Implement email insertion
        # - Validate email data structure
        # - Generate unique email ID
        # - Insert email record with proper data types
        # - Handle duplicate gmail_ids
        # - Return generated email ID
        
        if not self.connection:
            logger.error("No database connection available")
            return None
        
        try:
            cursor = self.connection.cursor()
            email_id = f"email_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            cursor.execute('''
                INSERT INTO emails (
                    id, gmail_id, subject, sender, recipient, received_at,
                    body_text, body_html, attachments, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email_id,
                email_data.get('gmail_id'),
                email_data.get('subject'),
                email_data.get('sender'),
                email_data.get('recipient'),
                email_data.get('received_at'),
                email_data.get('body_text'),
                email_data.get('body_html'),
                json.dumps(email_data.get('attachments', [])),
                'received'
            ))
            
            self.connection.commit()
            logger.info(f"Email inserted with ID: {email_id}")
            return email_id
            
        except Exception as e:
            logger.error(f"Error inserting email: {str(e)}")
            return None
    
    def get_emails(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> List[Dict]:
        """
        Retrieve emails from database with pagination.
        
        Args:
            limit (int): Maximum number of emails to return
            offset (int): Number of emails to skip
            status (Optional[str]): Filter by email status
            
        Returns:
            List[Dict]: List of email records
        """
        # TODO: Implement email retrieval
        # - Build query with filters and pagination
        # - Execute query and fetch results
        # - Convert SQLite rows to dictionaries
        # - Handle JSON fields properly
        
        if not self.connection:
            logger.error("No database connection available")
            return []
        
        try:
            cursor = self.connection.cursor()
            
            query = "SELECT * FROM emails"
            params = []
            
            if status:
                query += " WHERE status = ?"
                params.append(status)
            
            query += " ORDER BY received_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            emails = []
            for row in rows:
                email = dict(row)
                # Parse JSON fields
                if email['attachments']:
                    email['attachments'] = json.loads(email['attachments'])
                emails.append(email)
            
            logger.info(f"Retrieved {len(emails)} emails from database")
            return emails
            
        except Exception as e:
            logger.error(f"Error retrieving emails: {str(e)}")
            return []
    
    def update_email_status(self, email_id: str, status: str) -> bool:
        """
        Update the status of an email record.
        
        Args:
            email_id (str): Email ID to update
            status (str): New status value
            
        Returns:
            bool: True if updated successfully
        """
        # TODO: Implement email status update
        # - Update email status in database
        # - Set updated_at timestamp
        # - Log the status change
        
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE emails 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (status, email_id))
            
            self.connection.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Email {email_id} status updated to: {status}")
                return True
            else:
                logger.warning(f"No email found with ID: {email_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating email status: {str(e)}")
            return False
    
    def insert_quotation_request(self, request_data: Dict) -> Optional[str]:
        """
        Insert a new quotation request record.
        
        Args:
            request_data (Dict): Quotation request data
            
        Returns:
            Optional[str]: Request ID if inserted successfully
        """
        # TODO: Implement quotation request insertion
        # - Generate unique request ID
        # - Insert quotation request with proper data types
        # - Handle JSON serialization for requirements
        # - Return generated request ID
        
        if not self.connection:
            logger.error("No database connection available")
            return None
        
        try:
            cursor = self.connection.cursor()
            request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            cursor.execute('''
                INSERT INTO quotation_requests (
                    id, email_id, client_name, client_email, client_phone,
                    client_company, requirements, deadline, priority,
                    estimated_value, status, extracted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_id,
                request_data.get('email_id'),
                request_data.get('client_name'),
                request_data.get('client_email'),
                request_data.get('client_phone'),
                request_data.get('client_company'),
                json.dumps(request_data.get('requirements', [])),
                request_data.get('deadline'),
                request_data.get('priority', 'normal'),
                request_data.get('estimated_value'),
                'pending',
                datetime.now()
            ))
            
            self.connection.commit()
            logger.info(f"Quotation request inserted with ID: {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Error inserting quotation request: {str(e)}")
            return None
    
    def log_event(self, level: str, category: str, message: str, details: Optional[Dict] = None) -> bool:
        """
        Log an event to the database.
        
        Args:
            level (str): Log level (INFO, WARNING, ERROR, etc.)
            category (str): Event category
            message (str): Log message
            details (Optional[Dict]): Additional details as JSON
            
        Returns:
            bool: True if logged successfully
        """
        # TODO: Implement event logging
        # - Insert log record with timestamp
        # - Serialize details as JSON
        # - Handle logging errors gracefully
        
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO logs (level, category, message, details)
                VALUES (?, ?, ?, ?)
            ''', (
                level,
                category,
                message,
                json.dumps(details) if details else None
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"Error logging event: {str(e)}")  # Don't use logger to avoid recursion
            return False
    
    def get_metrics(self) -> Dict:
        """
        Get system metrics from database.
        
        Returns:
            Dict: System metrics
        """
        # TODO: Implement metrics calculation
        # - Count records by status and date ranges
        # - Calculate processing statistics
        # - Return comprehensive metrics
        
        if not self.connection:
            return {}
        
        try:
            cursor = self.connection.cursor()
            metrics = {}
            
            # Email metrics
            cursor.execute("SELECT COUNT(*) FROM emails")
            metrics['total_emails'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM emails WHERE DATE(created_at) = DATE('now')")
            metrics['emails_today'] = cursor.fetchone()[0]
            
            # Quotation metrics
            cursor.execute("SELECT COUNT(*) FROM quotation_requests")
            metrics['total_quotation_requests'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM quotation_history")
            metrics['total_quotations_generated'] = cursor.fetchone()[0]
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error retrieving metrics: {str(e)}")
            return {}
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> bool:
        """
        Clean up old log entries to manage database size.
        
        Args:
            days_to_keep (int): Number of days of logs to retain
            
        Returns:
            bool: True if cleanup successful
        """
        # TODO: Implement log cleanup
        # - Delete logs older than specified days
        # - Preserve critical error logs longer
        # - Return cleanup statistics
        
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                DELETE FROM logs 
                WHERE created_at < datetime('now', '-{} days')
                AND level NOT IN ('ERROR', 'CRITICAL')
            '''.format(days_to_keep))
            
            deleted_count = cursor.rowcount
            self.connection.commit()
            
            logger.info(f"Cleaned up {deleted_count} old log entries")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up logs: {str(e)}")
            return False