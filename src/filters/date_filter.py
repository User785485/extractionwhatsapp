"""Date-based filtering"""

from datetime import datetime
from typing import Optional, Union

from filters.base_filter import BaseFilter, FilterResult
from core.models import Message, Contact


class DateFilter(BaseFilter[Union[Message, Contact]]):
    """Filter messages or contacts by date"""
    
    def __init__(self, after_date: Optional[datetime] = None, 
                 before_date: Optional[datetime] = None,
                 name: Optional[str] = None):
        """
        Initialize date filter
        
        Args:
            after_date: Include items after this date
            before_date: Include items before this date
            name: Optional filter name
        """
        super().__init__(name)
        self.after_date = after_date
        self.before_date = before_date
        
        if not after_date and not before_date:
            raise ValueError("At least one of after_date or before_date must be specified")
        
        if after_date and before_date and after_date > before_date:
            raise ValueError("after_date must be before before_date")
    
    def apply(self, item: Union[Message, Contact]) -> FilterResult:
        """Apply date filter to message or contact"""
        # Get relevant date
        if isinstance(item, Message):
            item_date = item.timestamp
        elif isinstance(item, Contact):
            # Use last message date for contacts
            item_date = item.last_message_date
        else:
            return FilterResult(
                passed=False,
                reason=f"Unsupported item type: {type(item)}"
            )
        
        if not item_date:
            return FilterResult(
                passed=False,
                reason="Item has no date"
            )
        
        # Check date range
        if self.after_date and item_date < self.after_date:
            return FilterResult(
                passed=False,
                reason=f"Date {item_date} is before {self.after_date}"
            )
        
        if self.before_date and item_date > self.before_date:
            return FilterResult(
                passed=False,
                reason=f"Date {item_date} is after {self.before_date}"
            )
        
        return FilterResult(
            passed=True,
            metadata={'date': item_date.isoformat()}
        )
    
    def __repr__(self) -> str:
        parts = []
        if self.after_date:
            parts.append(f"after={self.after_date.isoformat()}")
        if self.before_date:
            parts.append(f"before={self.before_date.isoformat()}")
        return f"DateFilter({', '.join(parts)})"