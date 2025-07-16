"""Content-based filtering"""

import re
from typing import List, Optional, Set, Pattern

from filters.base_filter import BaseFilter, FilterResult
from core.models import Message, MediaType


class ContentFilter(BaseFilter[Message]):
    """Filter messages by content patterns"""
    
    def __init__(self, include_patterns: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None,
                 case_sensitive: bool = False,
                 search_transcriptions: bool = True,
                 name: Optional[str] = None):
        """
        Initialize content filter
        
        Args:
            include_patterns: Regex patterns for content to include
            exclude_patterns: Regex patterns for content to exclude
            case_sensitive: Whether pattern matching is case sensitive
            search_transcriptions: Whether to search in transcriptions
            name: Optional filter name
        """
        super().__init__(name)
        
        if not include_patterns and not exclude_patterns:
            raise ValueError("At least one pattern list must be specified")
        
        self.search_transcriptions = search_transcriptions
        
        # Compile patterns
        flags = 0 if case_sensitive else re.IGNORECASE
        
        self.include_patterns: List[Pattern] = []
        if include_patterns:
            self.include_patterns = [re.compile(p, flags) for p in include_patterns]
        
        self.exclude_patterns: List[Pattern] = []
        if exclude_patterns:
            self.exclude_patterns = [re.compile(p, flags) for p in exclude_patterns]
    
    def apply(self, item: Message) -> FilterResult:
        """Apply content filter to message"""
        # Build searchable text
        search_text = item.content or ""
        
        # Include transcription if available
        if self.search_transcriptions and item.transcription:
            search_text = f"{search_text} {item.transcription}"
        
        if not search_text:
            return FilterResult(
                passed=False,
                reason="Message has no searchable content"
            )
        
        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if pattern.search(search_text):
                return FilterResult(
                    passed=False,
                    reason=f"Content matches exclude pattern: {pattern.pattern}"
                )
        
        # Check include patterns
        if self.include_patterns:
            for pattern in self.include_patterns:
                if pattern.search(search_text):
                    return FilterResult(
                        passed=True,
                        metadata={'matched_pattern': pattern.pattern}
                    )
            
            # No include pattern matched
            return FilterResult(
                passed=False,
                reason="Content doesn't match any include pattern"
            )
        
        # Only exclude patterns specified, and none matched
        return FilterResult(passed=True)


class ContentTypeFilter(BaseFilter[Message]):
    """Filter messages by content type (media type)"""
    
    def __init__(self, include_types: Optional[Set[MediaType]] = None,
                 exclude_types: Optional[Set[MediaType]] = None,
                 name: Optional[str] = None):
        """
        Initialize content type filter
        
        Args:
            include_types: Media types to include
            exclude_types: Media types to exclude
            name: Optional filter name
        """
        super().__init__(name)
        
        if not include_types and not exclude_types:
            raise ValueError("At least one type set must be specified")
        
        self.include_types = include_types or set()
        self.exclude_types = exclude_types or set()
        
        # Validate no overlap
        if self.include_types and self.exclude_types:
            overlap = self.include_types & self.exclude_types
            if overlap:
                raise ValueError(f"Types cannot be both included and excluded: {overlap}")
    
    def apply(self, item: Message) -> FilterResult:
        """Apply content type filter to message"""
        media_type = item.media_type
        
        # Check exclude types first
        if media_type in self.exclude_types:
            return FilterResult(
                passed=False,
                reason=f"Media type {media_type.value} is excluded"
            )
        
        # Check include types
        if self.include_types:
            if media_type in self.include_types:
                return FilterResult(
                    passed=True,
                    metadata={'media_type': media_type.value}
                )
            else:
                return FilterResult(
                    passed=False,
                    reason=f"Media type {media_type.value} is not included"
                )
        
        # Only exclude types specified, and none matched
        return FilterResult(passed=True)
    
    def __repr__(self) -> str:
        parts = []
        if self.include_types:
            types = [t.value for t in self.include_types]
            parts.append(f"include={types}")
        if self.exclude_types:
            types = [t.value for t in self.exclude_types]
            parts.append(f"exclude={types}")
        return f"ContentTypeFilter({', '.join(parts)})"