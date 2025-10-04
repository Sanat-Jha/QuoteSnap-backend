"""
Gmail API service for QuoteSnap application.

This module handles all Gmail API interactions including
email monitoring, fetching, and authentication management.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import threading
import time
import json
import os
import base64
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# AI Extraction Service
from app.services.ai_email_extraction import extract_hardware_quotation_details

# File processing utilities
from utils import process_attachment

logger = logging.getLogger(__name__)

class GmailService:
    """
    Service class for handling Gmail API operations.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize Gmail service with authentication credentials.
        
        Args:
            credentials_path (str): Path to Gmail API credentials file
            token_path (str): Path to store OAuth tokens
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.credentials = None
        self.monitoring_active = False
        self.monitoring_thread = None
        self.last_check_time = None
        
        logger.info("Gmail service initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.
        
        Returns:
            bool: True if authentication successful
        """
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                  'https://www.googleapis.com/auth/gmail.modify']
        
        creds = None
        token_path = self.token_path or 'token.json'
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {str(e)}")
                    return False
            else:
                if not self.credentials_path or not os.path.exists(self.credentials_path):
                    logger.error("Gmail credentials file not found")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Failed to authenticate with Gmail: {str(e)}")
                    return False
            
            # Save the credentials for the next run
            try:
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"Failed to save token: {str(e)}")
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            logger.info("Gmail API authentication successful")
            return True
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {str(e)}")
            return False
    
    def start_monitoring(self, check_interval: int = 300) -> bool:
        """
        Start monitoring Gmail inbox for new emails.
        
        Args:
            check_interval (int): Interval between checks in seconds
            
        Returns:
            bool: True if monitoring started successfully
        """
        if self.monitoring_active:
            logger.warning("Email monitoring is already active")
            return True
        
        if not self.service:
            logger.error("Gmail service not authenticated")
            return False
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Gmail monitoring started with {check_interval}s interval")
        return True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        logger.info(f"Email monitoring started with {check_interval}s interval")
        return True
    
    def stop_monitoring(self) -> bool:
        """
        Stop monitoring Gmail inbox.
        
        Returns:
            bool: True if monitoring stopped successfully
        """
        if not self.monitoring_active:
            logger.warning("Email monitoring is not active")
            return True
        
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("Email monitoring stopped")
        return True
    
    def _monitoring_loop(self, check_interval: int):
        """
        Main monitoring loop that runs in background thread.
        
        Args:
            check_interval (int): Interval between checks in seconds
        """
        logger.info("Email monitoring loop started")
        
        while self.monitoring_active:
            try:
                new_emails = self._check_for_new_emails()
                if new_emails:
                    logger.info(f"Found {len(new_emails)} new emails")
                    for email_data in new_emails:
                        # Combine email body and attachment contents
                        combined_content = self._combine_email_content(email_data)
                        
                        print(f"\n🔔 NEW EMAIL RECEIVED:")
                        print(f"Subject: {email_data.get('subject', 'No Subject')}")
                        print(f"From: {email_data.get('sender', 'Unknown')}")
                        print(f"Received: {email_data.get('received_at', 'Unknown')}")
                        print(f"Attachments: {len(email_data.get('attachments', []))} files")
                        
                        # Process with AI extraction
                        print(f"\n🤖 AI EXTRACTION RESULT:")
                        print("=" * 80)
                        try:
                            extraction_result = extract_hardware_quotation_details(combined_content)
                            print(json.dumps(extraction_result, indent=2))
                        except Exception as e:
                            print(f"❌ AI extraction failed: {str(e)}")
                            logger.error(f"AI extraction error: {str(e)}")
                        print("=" * 80)
                        print("✅ END OF AI PROCESSING\n")
                
                self.last_check_time = datetime.now()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _check_for_new_emails(self):
        """
        Check Gmail inbox for new emails since last check.
        
        Returns:
            List[Dict]: List of new email data
        """
        try:
            # Build query for recent emails
            query = "in:inbox"
            if self.last_check_time:
                # Get emails newer than last check (within last hour for safety)
                hours_ago = max(1, int((datetime.now() - self.last_check_time).total_seconds() / 3600) + 1)
                query += f" newer_than:{hours_ago}h"
            else:
                # First run, get emails from last 1 hour
                query += " newer_than:1h"
            
            logger.debug(f"Searching emails with query: {query}")
            
            # Search for emails
            results = self.service.users().messages().list(
                userId='me', q=query, maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_emails = []
            
            for message in messages:
                try:
                    email_data = self.get_email_details(message['id'])
                    if email_data:
                        new_emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing email {message['id']}: {str(e)}")
                    continue
            
            return new_emails
            
        except HttpError as e:
            logger.error(f"Gmail API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error checking emails: {str(e)}")
            return []
        # Mock implementation - no actual checking yet
        pass
    
    def get_email_list(self, max_results: int = 100, query: str = "") -> List[Dict]:
        """
        Get list of emails from Gmail inbox.
        
        Args:
            max_results (int): Maximum number of emails to retrieve
            query (str): Gmail search query to filter emails
            
        Returns:
            List[Dict]: List of email metadata dictionaries
        """
        # TODO: Implement email list retrieval
        # - Use Gmail API to search emails
        # - Apply query filters
        # - Extract basic email metadata
        # - Return structured email data
        
        logger.info(f"Retrieving email list (max: {max_results}, query: '{query}')")
        
        # Mock response for now
        return []
    
    def get_email_details(self, email_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific email including attachments.
        
        Args:
            email_id (str): Gmail message ID
            
        Returns:
            Optional[Dict]: Email details or None if not found
        """
        if not self.service:
            logger.error("Gmail service not authenticated")
            return None
        
        try:
            # Get the email
            message = self.service.users().messages().get(
                userId='me', id=email_id, format='full'
            ).execute()
            
            # Extract headers
            headers = {}
            for header in message['payload'].get('headers', []):
                headers[header['name'].lower()] = header['value']
            
            # Extract body and attachments
            body_text = ""
            body_html = ""
            attachments = []
            
            def extract_parts(part):
                nonlocal body_text, body_html, attachments
                
                if part.get('mimeType') == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8')
                elif part.get('mimeType') == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8')
                elif 'parts' in part:
                    for subpart in part['parts']:
                        extract_parts(subpart)
                else:
                    # Check if this part is an attachment
                    filename = part.get('filename', '')
                    if filename and part['body'].get('attachmentId'):
                        # This is an attachment
                        attachment_info = {
                            'filename': filename,
                            'mimeType': part.get('mimeType', ''),
                            'size': part['body'].get('size', 0),
                            'attachmentId': part['body']['attachmentId']
                        }
                        attachments.append(attachment_info)
            
            # Handle both simple and multipart messages
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    extract_parts(part)
            else:
                extract_parts(message['payload'])
            
            # Process attachments and get their content
            attachment_contents = []
            for attachment in attachments:
                if self._is_supported_file(attachment['filename']):
                    content = self._get_attachment_content(email_id, attachment['attachmentId'])
                    if content:
                        processed_content = process_attachment(attachment['filename'], content)
                        attachment_contents.append(f"\n\n---\n# Attachment: {attachment['filename']}\n\n{processed_content}")
            
            # Convert timestamp
            timestamp = int(message['internalDate']) / 1000
            received_at = datetime.fromtimestamp(timestamp)
            
            return {
                'gmail_id': email_id,
                'subject': headers.get('subject', ''),
                'sender': headers.get('from', ''),
                'recipient': headers.get('to', ''),
                'received_at': received_at.isoformat(),
                'body_text': body_text,
                'body_html': body_html,
                'attachments': attachments,
                'attachment_contents': attachment_contents
            }
            
        except Exception as e:
            logger.error(f"Error retrieving email details: {str(e)}")
            return None
    
    def _is_supported_file(self, filename: str) -> bool:
        """Check if the file type is supported for processing."""
        supported_extensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc']
        return any(filename.lower().endswith(ext) for ext in supported_extensions)
    
    def _get_attachment_content(self, email_id: str, attachment_id: str) -> Optional[bytes]:
        """Get the content of an attachment."""
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=email_id, id=attachment_id
            ).execute()
            
            data = attachment.get('data')
            if data:
                return base64.urlsafe_b64decode(data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving attachment content: {str(e)}")
            return None
    
    def _combine_email_content(self, email_data: Dict) -> str:
        """
        Combine email body and attachment contents into one markdown string.
        
        Args:
            email_data (Dict): Email data containing body and attachments
            
        Returns:
            str: Combined content in markdown format
        """
        combined = []
        
        # Add email metadata
        combined.append("# Email Content\n")
        combined.append(f"**Subject:** {email_data.get('subject', 'No Subject')}\n")
        combined.append(f"**From:** {email_data.get('sender', 'Unknown')}\n")
        combined.append(f"**To:** {email_data.get('recipient', 'Unknown')}\n")
        combined.append(f"**Received:** {email_data.get('received_at', 'Unknown')}\n\n")
        
        # Add email body
        body_text = email_data.get('body_text', '').strip()
        body_html = email_data.get('body_html', '').strip()
        
        if body_text:
            combined.append("## Email Body\n\n")
            combined.append(f"{body_text}\n\n")
        elif body_html:
            combined.append("## Email Body (HTML)\n\n")
            # Basic HTML to text conversion (remove tags)
            import re
            clean_html = re.sub('<.*?>', '', body_html)
            combined.append(f"{clean_html}\n\n")
        else:
            combined.append("## Email Body\n\n*[No text content]*\n\n")
        
        # Add attachment contents
        attachment_contents = email_data.get('attachment_contents', [])
        if attachment_contents:
            combined.append("# Attachments\n")
            for content in attachment_contents:
                combined.append(content)
        else:
            attachments = email_data.get('attachments', [])
            if attachments:
                combined.append("# Attachments\n\n")
                for attachment in attachments:
                    filename = attachment.get('filename', 'Unknown')
                    if not self._is_supported_file(filename):
                        combined.append(f"## Attachment: {filename}\n\n")
                        combined.append("*[Unsupported file type - content not extracted]*\n\n")
        
        return "".join(combined)

    def get_email_content(self, email_id: str) -> Optional[Dict]:
        """
        Get full content of a specific email (alias for get_email_details).
        
        Args:
            email_id (str): Gmail message ID
            
        Returns:
            Optional[Dict]: Email content data or None if not found
        """
        return self.get_email_details(email_id)
    
    def get_email_attachments(self, email_id: str) -> List[Dict]:
        """
        Get attachments from a specific email.
        
        Args:
            email_id (str): Gmail message ID
            
        Returns:
            List[Dict]: List of attachment metadata and content
        """
        # TODO: Implement attachment retrieval
        # - Extract attachment metadata from email
        # - Download attachment content
        # - Handle different attachment types
        # - Return attachment data with content
        
        logger.info(f"Retrieving attachments for email ID: {email_id}")
        
        return []
    
    def mark_email_processed(self, email_id: str, label: str = "PROCESSED") -> bool:
        """
        Mark an email as processed by adding a label.
        
        Args:
            email_id (str): Gmail message ID
            label (str): Label to add to the email
            
        Returns:
            bool: True if successfully labeled
        """
        # TODO: Implement email labeling
        # - Create custom labels if they don't exist
        # - Apply label to email
        # - Handle Gmail API errors
        # - Log labeling activity
        
        logger.info(f"Marking email {email_id} as processed with label: {label}")
        
        return True
    
    def get_quota_usage(self) -> Dict:
        """
        Get current Gmail API quota usage information.
        
        Returns:
            Dict: Quota usage statistics
        """
        # TODO: Implement quota monitoring
        # - Check current API usage
        # - Calculate remaining quota
        # - Return quota statistics
        
        return {
            'daily_limit': 1000000000,
            'used_today': 0,
            'remaining_today': 1000000000,
            'reset_time': (datetime.now() + timedelta(days=1)).isoformat()
        }
    
    def test_connection(self) -> bool:
        """
        Test Gmail API connection and permissions.
        
        Returns:
            bool: True if connection is working
        """
        # TODO: Implement connection test
        # - Make simple API call to verify connectivity
        # - Check required permissions
        # - Return connection status
        
        logger.info("Testing Gmail API connection")
        
        if not self.service:
            return False
        
        try:
            # Mock connection test for now
            return True
        except Exception as e:
            logger.error(f"Gmail API connection test failed: {str(e)}")
            return False
    
    def get_monitoring_status(self) -> Dict:
        """
        Get current monitoring status and statistics.
        
        Returns:
            Dict: Monitoring status information
        """
        return {
            'is_active': self.monitoring_active,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'thread_alive': self.monitoring_thread.is_alive() if self.monitoring_thread else False,
            'emails_processed_today': 0,  # TODO: Get from database
            'last_error': None
        }