"""Message count based filtering"""

from typing import Optional

from filters.base_filter import BaseFilter, FilterResult
from core.models import Contact


class MessageCountFilter(BaseFilter[Contact]):
    """Filter contacts by message count"""
    
    def __init__(self, min_messages: Optional[int] = None,
                 max_messages: Optional[int] = None,
                 min_sent: Optional[int] = None,
                 min_received: Optional[int] = None,
                 name: Optional[str] = None):
        """
        Initialize message count filter
        
        Args:
            min_messages: Minimum total messages
            max_messages: Maximum total messages
            min_sent: Minimum sent messages
            min_received: Minimum received messages
            name: Optional filter name
        """
        super().__init__(name)
        
        if not any([min_messages, max_messages, min_sent, min_received]):
            raise ValueError("At least one count criterion must be specified")
        
        self.min_messages = min_messages
        self.max_messages = max_messages
        self.min_sent = min_sent
        self.min_received = min_received
        
        # Validate
        if min_messages and max_messages and min_messages > max_messages:
            raise ValueError("min_messages must be <= max_messages")
    
    def apply(self, item: Contact) -> FilterResult:
        """Apply message count filter to contact"""
        # Check total messages
        if self.min_messages and item.message_count < self.min_messages:
            return FilterResult(
                passed=False,
                reason=f"Message count {item.message_count} is below minimum {self.min_messages}"
            )
        
        if self.max_messages and item.message_count > self.max_messages:
            return FilterResult(
                passed=False,
                reason=f"Message count {item.message_count} is above maximum {self.max_messages}"
            )
        
        # Check sent messages
        if self.min_sent and item.sent_count < self.min_sent:
            return FilterResult(
                passed=False,
                reason=f"Sent count {item.sent_count} is below minimum {self.min_sent}"
            )
        
        # Check received messages
        if self.min_received and item.received_count < self.min_received:
            return FilterResult(
                passed=False,
                reason=f"Received count {item.received_count} is below minimum {self.min_received}"
            )
        
        return FilterResult(
            passed=True,
            metadata={
                'message_count': item.message_count,
                'sent_count': item.sent_count,
                'received_count': item.received_count
            }
        )
    
    def __repr__(self) -> str:
        criteria = []
        if self.min_messages:
            criteria.append(f"min_messages={self.min_messages}")
        if self.max_messages:
            criteria.append(f"max_messages={self.max_messages}")
        if self.min_sent:
            criteria.append(f"min_sent={self.min_sent}")
        if self.min_received:
            criteria.append(f"min_received={self.min_received}")
        return f"MessageCountFilter({', '.join(criteria)})"