"""Message direction classifier"""

import re
from typing import Optional, Tuple, Dict
from bs4 import BeautifulSoup, Tag
import logging

from ..core.models import MessageDirection

logger = logging.getLogger(__name__)


class MessageClassifier:
    """Classifies message direction based on CSS classes and content"""
    
    # Common CSS class patterns for message direction
    SENT_PATTERNS = [
        r'message-out',
        r'sent',
        r'from-me',
        r'outgoing',
        r'my-message',
        r'self-message'
    ]
    
    RECEIVED_PATTERNS = [
        r'message-in',
        r'received',
        r'from-them',
        r'incoming',
        r'their-message',
        r'other-message'
    ]
    
    SYSTEM_PATTERNS = [
        r'system',
        r'notification',
        r'announcement',
        r'info-message'
    ]
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.sent_regex = re.compile('|'.join(self.SENT_PATTERNS), re.IGNORECASE)
        self.received_regex = re.compile('|'.join(self.RECEIVED_PATTERNS), re.IGNORECASE)
        self.system_regex = re.compile('|'.join(self.SYSTEM_PATTERNS), re.IGNORECASE)
        
        # Cache for CSS analysis results
        self._css_cache: Dict[str, MessageDirection] = {}
    
    def classify(self, element: Tag, css_classes: Optional[str] = None) -> MessageDirection:
        """
        Classify message direction from HTML element
        
        Args:
            element: BeautifulSoup Tag element
            css_classes: Optional CSS classes string
            
        Returns:
            MessageDirection enum value
        """
        # Get CSS classes
        if css_classes is None:
            css_classes = ' '.join(element.get('class', []))
        
        # Check cache first
        if css_classes in self._css_cache:
            return self._css_cache[css_classes]
        
        direction = self._classify_by_css(css_classes)
        
        # If CSS classification fails, try content analysis
        if direction == MessageDirection.UNKNOWN:
            direction = self._classify_by_content(element)
        
        # Cache the result
        if css_classes:
            self._css_cache[css_classes] = direction
        
        return direction
    
    def _classify_by_css(self, css_classes: str) -> MessageDirection:
        """Classify based on CSS classes"""
        if not css_classes:
            return MessageDirection.UNKNOWN
        
        # Check patterns in order of likelihood
        if self.sent_regex.search(css_classes):
            return MessageDirection.SENT
        elif self.received_regex.search(css_classes):
            return MessageDirection.RECEIVED
        elif self.system_regex.search(css_classes):
            return MessageDirection.SYSTEM
        
        return MessageDirection.UNKNOWN
    
    def _classify_by_content(self, element: Tag) -> MessageDirection:
        """Classify based on element content and structure"""
        # Look for specific indicators in the element structure
        
        # Check for author/sender information
        author_elem = element.find(class_=re.compile(r'author|sender|from', re.I))
        if author_elem:
            author_text = author_elem.get_text(strip=True).lower()
            if any(term in author_text for term in ['you', 'me', 'moi', 'yo']):
                return MessageDirection.SENT
            else:
                return MessageDirection.RECEIVED
        
        # Check parent elements
        parent = element.parent
        while parent and parent.name != 'body':
            parent_classes = ' '.join(parent.get('class', []))
            parent_direction = self._classify_by_css(parent_classes)
            if parent_direction != MessageDirection.UNKNOWN:
                return parent_direction
            parent = parent.parent
        
        # Check for system message patterns
        text = element.get_text(strip=True).lower()
        system_keywords = [
            'joined', 'left', 'added', 'removed', 'changed',
            'created', 'deleted', 'updated', 'encrypted'
        ]
        if any(keyword in text for keyword in system_keywords):
            return MessageDirection.SYSTEM
        
        return MessageDirection.UNKNOWN
    
    def analyze_css_structure(self, html_content: str) -> Dict[str, MessageDirection]:
        """
        Analyze HTML to determine CSS class patterns
        
        Args:
            html_content: HTML content to analyze
            
        Returns:
            Dictionary mapping CSS patterns to directions
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        patterns = {}
        
        # Find all message containers
        message_elements = soup.find_all(class_=re.compile(r'message|msg|chat', re.I))
        
        for elem in message_elements[:100]:  # Analyze first 100 messages
            css_classes = ' '.join(elem.get('class', []))
            if css_classes:
                direction = self.classify(elem, css_classes)
                if direction != MessageDirection.UNKNOWN:
                    patterns[css_classes] = direction
        
        logger.info(f"Identified {len(patterns)} CSS patterns for message classification")
        return patterns
    
    def extract_contact_from_message(self, element: Tag) -> Optional[Tuple[str, str]]:
        """
        Extract contact information from message element
        
        Args:
            element: Message element
            
        Returns:
            Tuple of (phone_number, display_name) or None
        """
        # Look for contact information in various places
        contact_patterns = [
            r'from|sender|author|de|par',
            r'contact|number|phone',
            r'name|nom|nombre'
        ]
        
        for pattern in contact_patterns:
            contact_elem = element.find(class_=re.compile(pattern, re.I))
            if contact_elem:
                text = contact_elem.get_text(strip=True)
                
                # Extract phone number
                phone_match = re.search(r'(\+?\d[\d\s\-\(\)]+\d)', text)
                phone = phone_match.group(1) if phone_match else None
                
                # Extract display name (remove phone number from text)
                display_name = text
                if phone:
                    display_name = text.replace(phone, '').strip()
                
                if phone or display_name:
                    return (phone or '', display_name or '')
        
        return None