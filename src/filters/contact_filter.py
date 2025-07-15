"""Contact-based filtering"""

import re
from typing import List, Optional, Union, Pattern

from .base_filter import BaseFilter, FilterResult
from ..core.models import Message, Contact


class ContactFilter(BaseFilter[Union[Message, Contact]]):
    """Filter messages or contacts by contact patterns"""
    
    def __init__(self, include_patterns: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None,
                 case_sensitive: bool = False,
                 name: Optional[str] = None):
        """
        Initialize contact filter
        
        Args:
            include_patterns: Regex patterns for contacts to include
            exclude_patterns: Regex patterns for contacts to exclude
            case_sensitive: Whether pattern matching is case sensitive
            name: Optional filter name
        """
        super().__init__(name)
        
        if not include_patterns and not exclude_patterns:
            raise ValueError("At least one pattern list must be specified")
        
        # Compile patterns
        flags = 0 if case_sensitive else re.IGNORECASE
        
        self.include_patterns: List[Pattern] = []
        if include_patterns:
            self.include_patterns = [re.compile(p, flags) for p in include_patterns]
        
        self.exclude_patterns: List[Pattern] = []
        if exclude_patterns:
            self.exclude_patterns = [re.compile(p, flags) for p in exclude_patterns]
    
    def apply(self, item: Union[Message, Contact]) -> FilterResult:
        """Apply contact filter"""
        # Get contact from item
        if isinstance(item, Message):
            contact = item.contact
            if not contact:
                return FilterResult(
                    passed=False,
                    reason="Message has no contact"
                )
        elif isinstance(item, Contact):
            contact = item
        else:
            return FilterResult(
                passed=False,
                reason=f"Unsupported item type: {type(item)}"
            )
        
        # Create searchable text from contact
        contact_text = f"{contact.phone_number or ''} {contact.display_name or ''}"
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if pattern.search(contact_text):
                return FilterResult(
                    passed=False,
                    reason=f"Contact matches exclude pattern: {pattern.pattern}"
                )
        
        # Check include patterns
        if self.include_patterns:
            for pattern in self.include_patterns:
                if pattern.search(contact_text):
                    return FilterResult(
                        passed=True,
                        metadata={'matched_pattern': pattern.pattern}
                    )
            
            # No include pattern matched
            return FilterResult(
                passed=False,
                reason="Contact doesn't match any include pattern"
            )
        
        # Only exclude patterns specified, and none matched
        return FilterResult(passed=True)
    
    def __repr__(self) -> str:
        parts = []
        if self.include_patterns:
            parts.append(f"include={len(self.include_patterns)} patterns")
        if self.exclude_patterns:
            parts.append(f"exclude={len(self.exclude_patterns)} patterns")
        return f"ContactFilter({', '.join(parts)})"