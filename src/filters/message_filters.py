"""Message filter processor for applying multiple filters to WhatsApp data"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.schemas import FilterConfig
from filters.base_filter import BaseFilter, FilterResult
from filters.date_filter import DateFilter
from filters.contact_filter import ContactFilter
from filters.content_filter import ContentFilter, ContentTypeFilter
from filters.composite_filter import CompositeFilter, FilterMode
from filters.message_count_filter import MessageCountFilter

logger = logging.getLogger(__name__)


class MessageFilterProcessor:
    """Processes and applies filters to messages and contacts"""
    
    def __init__(self, filter_config: FilterConfig):
        """
        Initialize filter processor with configuration
        
        Args:
            filter_config: Filter configuration settings
        """
        self.config = filter_config
        self.active_filters = []
        self._setup_filters()
    
    def _setup_filters(self):
        """Setup filters based on configuration"""
        try:
            # Date filters
            if self.config.date_from or self.config.date_to:
                date_filter = DateFilter(
                    start_date=self.config.date_from,
                    end_date=self.config.date_to
                )
                self.active_filters.append(date_filter)
                logger.info(f"Date filter added: {self.config.date_from} to {self.config.date_to}")
            
            # Contact filters
            if self.config.include_contacts or self.config.exclude_contacts:
                contact_filter = ContactFilter(
                    include_contacts=self.config.include_contacts or [],
                    exclude_contacts=self.config.exclude_contacts or []
                )
                self.active_filters.append(contact_filter)
                logger.info(f"Contact filter added: include {len(self.config.include_contacts or [])} contacts")
            
            # Content filters
            if self.config.keywords or self.config.exclude_keywords:
                content_filter = ContentFilter(
                    include_keywords=self.config.keywords or [],
                    exclude_keywords=self.config.exclude_keywords or [],
                    case_sensitive=self.config.case_sensitive
                )
                self.active_filters.append(content_filter)
                logger.info(f"Content filter added: {len(self.config.keywords or [])} keywords")
            
            # Message type filters
            if (self.config.include_text_messages or
                self.config.include_audio_messages or
                self.config.include_image_messages or
                self.config.include_video_messages or
                self.config.include_document_messages):
                
                media_types = []
                if self.config.include_text_messages:
                    media_types.append('text')
                if self.config.include_audio_messages:
                    media_types.append('audio')
                if self.config.include_image_messages:
                    media_types.append('image')
                if self.config.include_video_messages:
                    media_types.append('video')
                if self.config.include_document_messages:
                    media_types.append('document')
                
                type_filter = ContentTypeFilter(allowed_types=media_types)
                self.active_filters.append(type_filter)
                logger.info(f"Media type filter added: {media_types}")
            
            # Message count filter
            if self.config.min_message_length or self.config.max_message_length:
                count_filter = MessageCountFilter(
                    min_count=self.config.min_message_length or 0,
                    max_count=self.config.max_message_length or float('inf')
                )
                self.active_filters.append(count_filter)
                logger.info("Message count filter added")
            
            logger.info(f"Initialized {len(self.active_filters)} filters")
            
        except Exception as e:
            logger.error(f"Failed to setup filters: {e}")
            self.active_filters = []
    
    def filter_messages(self, messages: List[Any]) -> List[Any]:
        """
        Apply filters to a list of messages
        
        Args:
            messages: List of message objects
            
        Returns:
            Filtered list of messages
        """
        if not self.active_filters:
            logger.info("No active filters, returning all messages")
            return messages
        
        try:
            original_count = len(messages)
            filtered_messages = messages.copy()
            
            # Apply each filter sequentially
            for filter_obj in self.active_filters:
                filtered_messages = [
                    msg for msg in filtered_messages
                    if filter_obj.apply(msg).should_include
                ]
                logger.debug(f"After {filter_obj.__class__.__name__}: {len(filtered_messages)} messages")
            
            logger.info(f"Filtered {original_count} messages to {len(filtered_messages)}")
            return filtered_messages
            
        except Exception as e:
            logger.error(f"Message filtering failed: {e}")
            return messages
    
    def filter_contacts(self, contacts: List[Any]) -> List[Any]:
        """
        Apply filters to a list of contacts
        
        Args:
            contacts: List of contact objects
            
        Returns:
            Filtered list of contacts
        """
        if not self.active_filters:
            logger.info("No active filters, returning all contacts")
            return contacts
        
        try:
            original_count = len(contacts)
            filtered_contacts = contacts.copy()
            
            # Apply contact-specific filters
            for filter_obj in self.active_filters:
                if isinstance(filter_obj, ContactFilter):
                    filtered_contacts = [
                        contact for contact in filtered_contacts
                        if filter_obj.apply(contact).should_include
                    ]
                    logger.debug(f"After contact filter: {len(filtered_contacts)} contacts")
            
            logger.info(f"Filtered {original_count} contacts to {len(filtered_contacts)}")
            return filtered_contacts
            
        except Exception as e:
            logger.error(f"Contact filtering failed: {e}")
            return contacts
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of active filters"""
        summary = {
            'total_filters': len(self.active_filters),
            'filter_types': [f.__class__.__name__ for f in self.active_filters],
            'details': {}
        }
        
        # Add specific filter details
        if self.config.date_from or self.config.date_to:
            summary['details']['date_range'] = {
                'from': self.config.date_from.isoformat() if self.config.date_from else None,
                'to': self.config.date_to.isoformat() if self.config.date_to else None
            }
        
        if self.config.include_contacts:
            summary['details']['include_contacts'] = len(self.config.include_contacts)
            
        if self.config.exclude_contacts:
            summary['details']['exclude_contacts'] = len(self.config.exclude_contacts)
        
        if self.config.keywords:
            summary['details']['keywords'] = len(self.config.keywords)
        
        return summary
    
    def apply_composite_filter(self, messages: List[Any], 
                             filter_mode: FilterMode = FilterMode.AND) -> List[Any]:
        """
        Apply filters using composite mode
        
        Args:
            messages: List of messages to filter
            filter_mode: How to combine filters (ALL, ANY, NONE)
            
        Returns:
            Filtered messages
        """
        if not self.active_filters:
            return messages
        
        try:
            composite = CompositeFilter(self.active_filters, filter_mode)
            filtered_messages = [
                msg for msg in messages
                if composite.apply(msg).should_include
            ]
            
            logger.info(f"Composite filter ({filter_mode.value}) resulted in {len(filtered_messages)} messages")
            return filtered_messages
            
        except Exception as e:
            logger.error(f"Composite filtering failed: {e}")
            return messages
    
    def test_filters(self, sample_data: List[Any]) -> Dict[str, Any]:
        """
        Test filters on sample data
        
        Args:
            sample_data: Sample messages or contacts to test
            
        Returns:
            Test results showing filter effectiveness
        """
        results = {
            'original_count': len(sample_data),
            'filter_results': {},
            'final_count': 0,
            'reduction_percentage': 0.0
        }
        
        try:
            # Test each filter individually
            current_data = sample_data.copy()
            
            for i, filter_obj in enumerate(self.active_filters):
                filter_name = filter_obj.__class__.__name__
                
                filtered_data = [
                    item for item in current_data
                    if filter_obj.apply(item).should_include
                ]
                
                results['filter_results'][filter_name] = {
                    'input_count': len(current_data),
                    'output_count': len(filtered_data),
                    'filtered_out': len(current_data) - len(filtered_data)
                }
                
                current_data = filtered_data
            
            results['final_count'] = len(current_data)
            if len(sample_data) > 0:
                results['reduction_percentage'] = (
                    (len(sample_data) - len(current_data)) / len(sample_data)
                ) * 100
            
            logger.info(f"Filter test complete: {results['reduction_percentage']:.1f}% reduction")
            return results
            
        except Exception as e:
            logger.error(f"Filter testing failed: {e}")
            return results
    
    def clear_filters(self):
        """Clear all active filters"""
        self.active_filters.clear()
        logger.info("All filters cleared")
    
    def add_custom_filter(self, filter_obj: BaseFilter):
        """Add a custom filter"""
        if isinstance(filter_obj, BaseFilter):
            self.active_filters.append(filter_obj)
            logger.info(f"Added custom filter: {filter_obj.__class__.__name__}")
        else:
            raise ValueError("Filter must inherit from BaseFilter")
    
    def remove_filter(self, filter_type: type):
        """Remove filters of a specific type"""
        original_count = len(self.active_filters)
        self.active_filters = [f for f in self.active_filters if not isinstance(f, filter_type)]
        removed_count = original_count - len(self.active_filters)
        logger.info(f"Removed {removed_count} filters of type {filter_type.__name__}")