"""
Email model for QuoteSnap application.

This module defines the Email data model and related operations
for storing and managing email data in the database.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

@dataclass
class EmailAttachment:
    """
    Data class for email attachment information.
    """
    filename: str
    content_type: str
    size_bytes: int
    attachment_id: Optional[str] = None
    content: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert attachment to dictionary format."""
        return {
            'filename': self.filename,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
            'attachment_id': self.attachment_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmailAttachment':
        """Create EmailAttachment from dictionary."""
        return cls(
            filename=data.get('filename', ''),
            content_type=data.get('content_type', ''),
            size_bytes=data.get('size_bytes', 0),
            attachment_id=data.get('attachment_id')
        )

@dataclass
class Email:
    """
    Data class for email information and content.
    """
    # Required fields
    gmail_id: str
    subject: str
    sender: str
    recipient: str
    received_at: datetime
    
    # Optional content fields
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    
    # Processing fields
    id: Optional[str] = None
    status: str = 'received'
    processed_at: Optional[datetime] = None
    
    # Metadata fields
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Email object to dictionary format for database storage.
        
        Returns:
            Dict[str, Any]: Email data as dictionary
        """
        return {
            'id': self.id,
            'gmail_id': self.gmail_id,
            'subject': self.subject,
            'sender': self.sender,
            'recipient': self.recipient,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'body_text': self.body_text,
            'body_html': self.body_html,
            'attachments': json.dumps([att.to_dict() for att in self.attachments]),
            'status': self.status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Email':
        """
        Create Email object from dictionary data.
        
        Args:
            data (Dict[str, Any]): Email data dictionary
            
        Returns:
            Email: Email object instance
        """
        # Parse datetime fields
        received_at = None
        if data.get('received_at'):
            if isinstance(data['received_at'], str):
                received_at = datetime.fromisoformat(data['received_at'].replace('Z', '+00:00'))
            else:
                received_at = data['received_at']
        
        processed_at = None
        if data.get('processed_at'):
            if isinstance(data['processed_at'], str):
                processed_at = datetime.fromisoformat(data['processed_at'].replace('Z', '+00:00'))
            else:
                processed_at = data['processed_at']
        
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            else:
                created_at = data['created_at']
        
        updated_at = None
        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            else:
                updated_at = data['updated_at']
        
        # Parse attachments
        attachments = []
        if data.get('attachments'):
            if isinstance(data['attachments'], str):
                try:
                    attachments_data = json.loads(data['attachments'])
                    attachments = [EmailAttachment.from_dict(att) for att in attachments_data]
                except json.JSONDecodeError:
                    pass
            elif isinstance(data['attachments'], list):
                attachments = [EmailAttachment.from_dict(att) for att in data['attachments']]
        
        return cls(
            id=data.get('id'),
            gmail_id=data['gmail_id'],
            subject=data.get('subject', ''),
            sender=data.get('sender', ''),
            recipient=data.get('recipient', ''),
            received_at=received_at or datetime.now(),
            body_text=data.get('body_text'),
            body_html=data.get('body_html'),
            attachments=attachments,
            status=data.get('status', 'received'),
            processed_at=processed_at,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def get_plain_text_content(self) -> str:
        """
        Get plain text content from email, preferring text over HTML.
        
        Returns:
            str: Plain text email content
        """
        if self.body_text:
            return self.body_text
        elif self.body_html:
            # TODO: Convert HTML to plain text
            # For now, return HTML as-is
            return self.body_html
        else:
            return ""
    
    def has_attachments(self) -> bool:
        """
        Check if email has attachments.
        
        Returns:
            bool: True if email has attachments
        """
        return len(self.attachments) > 0
    
    def get_attachment_count(self) -> int:
        """
        Get number of attachments.
        
        Returns:
            int: Number of attachments
        """
        return len(self.attachments)
    
    def get_total_attachment_size(self) -> int:
        """
        Get total size of all attachments in bytes.
        
        Returns:
            int: Total attachment size in bytes
        """
        return sum(att.size_bytes for att in self.attachments)
    
    def is_processed(self) -> bool:
        """
        Check if email has been processed.
        
        Returns:
            bool: True if email status indicates processing is complete
        """
        return self.status in ['processed', 'completed', 'quotation_generated']
    
    def is_pending(self) -> bool:
        """
        Check if email is pending processing.
        
        Returns:
            bool: True if email is pending processing
        """
        return self.status in ['received', 'pending', 'processing']
    
    def has_error(self) -> bool:
        """
        Check if email processing resulted in an error.
        
        Returns:
            bool: True if email has error status
        """
        return self.status in ['error', 'failed', 'extraction_failed']
    
    def update_status(self, new_status: str):
        """
        Update email processing status.
        
        Args:
            new_status (str): New status value
        """
        self.status = new_status
        self.updated_at = datetime.now()
        
        if new_status in ['processed', 'completed', 'quotation_generated']:
            self.processed_at = datetime.now()
    
    def validate(self) -> List[str]:
        """
        Validate email data and return list of validation errors.
        
        Returns:
            List[str]: List of validation error messages
        """
        errors = []
        
        if not self.gmail_id:
            errors.append("Gmail ID is required")
        
        if not self.sender:
            errors.append("Sender email is required")
        
        if not self.recipient:
            errors.append("Recipient email is required")
        
        if not self.received_at:
            errors.append("Received timestamp is required")
        
        # Validate email addresses
        from app.utils.helpers import validate_email
        
        if self.sender and not validate_email(self.sender):
            errors.append("Invalid sender email format")
        
        if self.recipient and not validate_email(self.recipient):
            errors.append("Invalid recipient email format")
        
        return errors
    
    def __str__(self) -> str:
        """String representation of Email object."""
        return f"Email(id={self.id}, subject='{self.subject[:50]}...', sender={self.sender}, status={self.status})"
    
    def __repr__(self) -> str:
        """Detailed string representation of Email object."""
        return (f"Email(id={self.id}, gmail_id={self.gmail_id}, subject='{self.subject}', "
                f"sender={self.sender}, recipient={self.recipient}, status={self.status}, "
                f"attachments={len(self.attachments)})")