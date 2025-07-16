"""Filtering system for messages and contacts"""

from filters.base_filter import BaseFilter, FilterResult
from filters.date_filter import DateFilter
from filters.contact_filter import ContactFilter
from filters.content_filter import ContentFilter, ContentTypeFilter
from filters.composite_filter import CompositeFilter, FilterMode
from filters.message_count_filter import MessageCountFilter
from filters.message_filters import MessageFilterProcessor

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