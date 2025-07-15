"""Filtering system for messages and contacts"""

from .base_filter import BaseFilter, FilterResult
from .date_filter import DateFilter
from .contact_filter import ContactFilter
from .content_filter import ContentFilter, ContentTypeFilter
from .composite_filter import CompositeFilter, FilterMode
from .message_count_filter import MessageCountFilter
from .message_filters import MessageFilterProcessor

__all__ = [
    'BaseFilter',
    'FilterResult',
    'DateFilter',
    'ContactFilter',
    'ContentFilter',
    'ContentTypeFilter',
    'CompositeFilter',
    'FilterMode',
    'MessageCountFilter',
    'MessageFilterProcessor'
]