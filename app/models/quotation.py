"""
Quotation models for QuoteSnap application.

This module defines the QuotationRequest and Quotation data models
for storing and managing quotation data in the database.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date
import json
from decimal import Decimal

@dataclass
class RequirementItem:
    """
    Data class for individual requirement/product items in a quotation.
    """
    serial_number: int
    product_name: str
    description: str
    quantity: Union[int, float]
    unit: str = 'pieces'
    specifications: Optional[str] = None
    unit_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement item to dictionary format."""
        return {
            'serial_number': self.serial_number,
            'product_name': self.product_name,
            'description': self.description,
            'quantity': float(self.quantity),
            'unit': self.unit,
            'specifications': self.specifications,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'total_price': float(self.total_price) if self.total_price else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequirementItem':
        """Create RequirementItem from dictionary."""
        unit_price = None
        if data.get('unit_price') is not None:
            unit_price = Decimal(str(data['unit_price']))
        
        total_price = None
        if data.get('total_price') is not None:
            total_price = Decimal(str(data['total_price']))
        
        return cls(
            serial_number=data.get('serial_number', 1),
            product_name=data.get('product_name', ''),
            description=data.get('description', ''),
            quantity=data.get('quantity', 1),
            unit=data.get('unit', 'pieces'),
            specifications=data.get('specifications'),
            unit_price=unit_price,
            total_price=total_price,
            notes=data.get('notes')
        )
    
    def calculate_total(self) -> Optional[Decimal]:
        """Calculate total price based on quantity and unit price."""
        if self.unit_price is not None:
            self.total_price = Decimal(str(self.quantity)) * self.unit_price
            return self.total_price
        return None

@dataclass
class QuotationRequest:
    """
    Data class for quotation request information extracted from emails.
    """
    # Required fields
    email_id: str
    requirements: List[RequirementItem] = field(default_factory=list)
    
    # Client information
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    client_company: Optional[str] = None
    
    # Project details
    deadline: Optional[date] = None
    priority: str = 'normal'
    estimated_value: Optional[Decimal] = None
    additional_notes: Optional[str] = None
    
    # Processing metadata
    id: Optional[str] = None
    status: str = 'pending'
    extracted_at: Optional[datetime] = None
    extraction_confidence: Optional[float] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert QuotationRequest object to dictionary format for database storage.
        
        Returns:
            Dict[str, Any]: QuotationRequest data as dictionary
        """
        return {
            'id': self.id,
            'email_id': self.email_id,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'client_phone': self.client_phone,
            'client_company': self.client_company,
            'requirements': json.dumps([req.to_dict() for req in self.requirements]),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority,
            'estimated_value': float(self.estimated_value) if self.estimated_value else None,
            'additional_notes': self.additional_notes,
            'status': self.status,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'extraction_confidence': self.extraction_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuotationRequest':
        """
        Create QuotationRequest object from dictionary data.
        
        Args:
            data (Dict[str, Any]): QuotationRequest data dictionary
            
        Returns:
            QuotationRequest: QuotationRequest object instance
        """
        # Parse datetime fields
        extracted_at = None
        if data.get('extracted_at'):
            if isinstance(data['extracted_at'], str):
                extracted_at = datetime.fromisoformat(data['extracted_at'].replace('Z', '+00:00'))
            else:
                extracted_at = data['extracted_at']
        
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
        
        # Parse deadline
        deadline = None
        if data.get('deadline'):
            if isinstance(data['deadline'], str):
                try:
                    deadline = datetime.fromisoformat(data['deadline']).date()
                except ValueError:
                    # Try parsing as date only
                    try:
                        deadline = date.fromisoformat(data['deadline'])
                    except ValueError:
                        pass
            elif isinstance(data['deadline'], date):
                deadline = data['deadline']
        
        # Parse requirements
        requirements = []
        if data.get('requirements'):
            if isinstance(data['requirements'], str):
                try:
                    requirements_data = json.loads(data['requirements'])
                    requirements = [RequirementItem.from_dict(req) for req in requirements_data]
                except json.JSONDecodeError:
                    pass
            elif isinstance(data['requirements'], list):
                requirements = [RequirementItem.from_dict(req) for req in data['requirements']]
        
        # Parse estimated value
        estimated_value = None
        if data.get('estimated_value') is not None:
            estimated_value = Decimal(str(data['estimated_value']))
        
        return cls(
            id=data.get('id'),
            email_id=data['email_id'],
            client_name=data.get('client_name'),
            client_email=data.get('client_email'),
            client_phone=data.get('client_phone'),
            client_company=data.get('client_company'),
            requirements=requirements,
            deadline=deadline,
            priority=data.get('priority', 'normal'),
            estimated_value=estimated_value,
            additional_notes=data.get('additional_notes'),
            status=data.get('status', 'pending'),
            extracted_at=extracted_at,
            extraction_confidence=data.get('extraction_confidence'),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def get_total_estimated_value(self) -> Decimal:
        """
        Calculate total estimated value from all requirements.
        
        Returns:
            Decimal: Total estimated value
        """
        total = Decimal('0')
        
        # Use estimated_value if available
        if self.estimated_value:
            return self.estimated_value
        
        # Otherwise calculate from requirements
        for req in self.requirements:
            if req.total_price:
                total += req.total_price
            elif req.unit_price:
                total += Decimal(str(req.quantity)) * req.unit_price
        
        return total
    
    def get_requirement_count(self) -> int:
        """Get number of requirement items."""
        return len(self.requirements)
    
    def add_requirement(self, requirement: RequirementItem):
        """Add a requirement item to the request."""
        if not requirement.serial_number:
            requirement.serial_number = len(self.requirements) + 1
        self.requirements.append(requirement)
        self.updated_at = datetime.now()
    
    def remove_requirement(self, serial_number: int) -> bool:
        """Remove requirement by serial number."""
        for i, req in enumerate(self.requirements):
            if req.serial_number == serial_number:
                del self.requirements[i]
                self.updated_at = datetime.now()
                return True
        return False
    
    def update_status(self, new_status: str):
        """Update quotation request status."""
        self.status = new_status
        self.updated_at = datetime.now()
    
    def is_high_priority(self) -> bool:
        """Check if request is high priority."""
        return self.priority.lower() in ['high', 'urgent', 'critical']
    
    def is_overdue(self) -> bool:
        """Check if request is past deadline."""
        if not self.deadline:
            return False
        return date.today() > self.deadline
    
    def days_until_deadline(self) -> Optional[int]:
        """Get number of days until deadline."""
        if not self.deadline:
            return None
        delta = self.deadline - date.today()
        return delta.days
    
    def validate(self) -> List[str]:
        """Validate quotation request and return list of errors."""
        errors = []
        
        if not self.email_id:
            errors.append("Email ID is required")
        
        if not self.requirements:
            errors.append("At least one requirement is needed")
        
        # Validate client email if provided
        if self.client_email:
            # Simple email validation
            import re
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.client_email):
                errors.append("Invalid client email format")
        
        # Validate requirements
        for i, req in enumerate(self.requirements):
            if not req.product_name:
                errors.append(f"Requirement {i+1}: Product name is required")
            if req.quantity <= 0:
                errors.append(f"Requirement {i+1}: Quantity must be positive")
        
        return errors

@dataclass
class Quotation:
    """
    Data class for generated quotation information.
    """
    # Required fields
    quotation_request_id: str
    quotation_number: str
    items: List[RequirementItem] = field(default_factory=list)
    
    # Pricing
    subtotal: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    
    # File paths
    excel_file_path: Optional[str] = None
    pdf_file_path: Optional[str] = None
    
    # Status and metadata
    id: Optional[str] = None
    status: str = 'generated'
    version: int = 1
    generated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Quotation object to dictionary format."""
        return {
            'id': self.id,
            'quotation_request_id': self.quotation_request_id,
            'quotation_number': self.quotation_number,
            'items': json.dumps([item.to_dict() for item in self.items]),
            'subtotal': float(self.subtotal) if self.subtotal else None,
            'tax_rate': float(self.tax_rate) if self.tax_rate else None,
            'tax_amount': float(self.tax_amount) if self.tax_amount else None,
            'discount_amount': float(self.discount_amount) if self.discount_amount else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'excel_file_path': self.excel_file_path,
            'pdf_file_path': self.pdf_file_path,
            'status': self.status,
            'version': self.version,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Quotation':
        """Create Quotation object from dictionary data."""
        # Parse datetime fields
        generated_at = None
        if data.get('generated_at'):
            if isinstance(data['generated_at'], str):
                generated_at = datetime.fromisoformat(data['generated_at'].replace('Z', '+00:00'))
            else:
                generated_at = data['generated_at']
        
        sent_at = None
        if data.get('sent_at'):
            if isinstance(data['sent_at'], str):
                sent_at = datetime.fromisoformat(data['sent_at'].replace('Z', '+00:00'))
            else:
                sent_at = data['sent_at']
        
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
        
        # Parse items
        items = []
        if data.get('items'):
            if isinstance(data['items'], str):
                try:
                    items_data = json.loads(data['items'])
                    items = [RequirementItem.from_dict(item) for item in items_data]
                except json.JSONDecodeError:
                    pass
            elif isinstance(data['items'], list):
                items = [RequirementItem.from_dict(item) for item in data['items']]
        
        # Parse decimal fields
        decimal_fields = ['subtotal', 'tax_rate', 'tax_amount', 'discount_amount', 'total_amount']
        parsed_decimals = {}
        for field in decimal_fields:
            if data.get(field) is not None:
                parsed_decimals[field] = Decimal(str(data[field]))
            else:
                parsed_decimals[field] = None
        
        return cls(
            id=data.get('id'),
            quotation_request_id=data['quotation_request_id'],
            quotation_number=data['quotation_number'],
            items=items,
            subtotal=parsed_decimals['subtotal'],
            tax_rate=parsed_decimals['tax_rate'],
            tax_amount=parsed_decimals['tax_amount'],
            discount_amount=parsed_decimals['discount_amount'],
            total_amount=parsed_decimals['total_amount'],
            excel_file_path=data.get('excel_file_path'),
            pdf_file_path=data.get('pdf_file_path'),
            status=data.get('status', 'generated'),
            version=data.get('version', 1),
            generated_at=generated_at,
            sent_at=sent_at,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def calculate_totals(self, tax_rate: Optional[Decimal] = None, discount_amount: Optional[Decimal] = None):
        """Calculate quotation totals."""
        # Calculate subtotal from items
        self.subtotal = Decimal('0')
        for item in self.items:
            if item.total_price:
                self.subtotal += item.total_price
            elif item.unit_price:
                item.calculate_total()
                if item.total_price:
                    self.subtotal += item.total_price
        
        # Apply discount
        discounted_subtotal = self.subtotal
        if discount_amount:
            self.discount_amount = discount_amount
            discounted_subtotal = self.subtotal - discount_amount
        
        # Calculate tax
        if tax_rate:
            self.tax_rate = tax_rate
            self.tax_amount = discounted_subtotal * tax_rate
        else:
            self.tax_amount = Decimal('0')
        
        # Calculate total
        self.total_amount = discounted_subtotal + (self.tax_amount or Decimal('0'))
        self.updated_at = datetime.now()
    
    def mark_as_sent(self):
        """Mark quotation as sent."""
        self.status = 'sent'
        self.sent_at = datetime.now()
        self.updated_at = datetime.now()
    
    def is_sent(self) -> bool:
        """Check if quotation has been sent."""
        return self.status == 'sent' and self.sent_at is not None
    
    def get_item_count(self) -> int:
        """Get number of items in quotation."""
        return len(self.items)