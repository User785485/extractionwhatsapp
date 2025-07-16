"""WhatsApp HTML export parser with robust error handling"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict
import logging
from bs4 import BeautifulSoup, Tag
import chardet

from parsers.base_parser import BaseParser
from parsers.message_classifier import MessageClassifier
from core.models import Contact, Message, MessageDirection, MediaType
from core.exceptions import ParsingError

logger = logging.getLogger(__name__)


class WhatsAppHTMLParser(BaseParser):
    """Parser for WhatsApp HTML export files"""
    
    # Media type patterns
    MEDIA_PATTERNS = {
        MediaType.AUDIO: r'\.(opus|mp3|m4a|wav|ogg|aac|flac|wma)$',
        MediaType.VIDEO: r'\.(mp4|avi|mov|wmv|flv|mkv|webm|m4v|3gp)$',
        MediaType.IMAGE: r'\.(jpg|jpeg|png|gif|bmp|webp|svg|tiff?)$',
        MediaType.DOCUMENT: r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|txt|zip|rar)$',
        MediaType.STICKER: r'sticker|autocollant',
        MediaType.GIF: r'\.gif$|giphy|tenor'
    }
    
    # Date patterns for various formats
    DATE_PATTERNS = [
        # ISO format: 2024-01-15 14:30:00
        (r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
        # European format: 15/01/2024 14:30
        (r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2})', '%d/%m/%Y %H:%M'),
        # US format: 01/15/2024 2:30 PM
        (r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2})\s*(AM|PM)?', '%m/%d/%Y %I:%M %p'),
        # WhatsApp format: [15/01/2024, 14:30:00]
        (r'\[(\d{1,2}/\d{1,2}/\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?)\]', '%d/%m/%Y %H:%M:%S')
    ]
    
    def __init__(self):
        self.classifier = MessageClassifier()
        self._encoding_cache: Dict[Path, str] = {}
    
    def validate_file(self, file_path: Path) -> bool:
        """Validate if file is a WhatsApp HTML export"""
        if not file_path.exists():
            return False
        
        if file_path.suffix.lower() not in ['.html', '.htm']:
            return False
        
        # Check file content for WhatsApp markers
        try:
            content = self._read_file_safely(file_path)
            soup = BeautifulSoup(content[:10000], 'html.parser')  # Check first 10KB
            
            # Look for WhatsApp-specific elements
            whatsapp_markers = [
                'whatsapp', 'message', 'chat', 'conversation',
                '_3j7s9', '_2wP_Y', '_3_7W3'  # WhatsApp CSS classes
            ]
            
            text_content = soup.get_text().lower()
            html_content = str(soup).lower()
            
            return any(marker in text_content or marker in html_content 
                      for marker in whatsapp_markers)
            
        except Exception as e:
            logger.error(f"Failed to validate file {file_path}: {e}")
            return False
    
    def parse(self, file_path: Path) -> Dict[str, List[Message]]:
        """Parse WhatsApp HTML file and extract messages by contact"""
        if not self.validate_file(file_path):
            raise ParsingError(f"Invalid WhatsApp HTML file: {file_path}")
        
        logger.info(f"Parsing WhatsApp HTML file: {file_path}")
        
        try:
            content = self._read_file_safely(file_path)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Analyze CSS structure
            css_patterns = self.classifier.analyze_css_structure(content)
            
            # Extract messages
            messages_by_contact = defaultdict(list)
            message_elements = self._find_message_elements(soup)
            
            logger.info(f"Found {len(message_elements)} message elements")
            
            for element in message_elements:
                try:
                    message = self._parse_message_element(element)
                    if message and message.contact:
                        contact_key = message.contact.identifier
                        messages_by_contact[contact_key].append(message)
                except Exception as e:
                    logger.warning(f"Failed to parse message element: {e}")
                    continue
            
            # Sort messages by timestamp
            for contact_messages in messages_by_contact.values():
                contact_messages.sort(key=lambda m: m.timestamp or datetime.min)
            
            logger.info(f"Successfully parsed {sum(len(msgs) for msgs in messages_by_contact.values())} messages from {len(messages_by_contact)} contacts")
            
            return dict(messages_by_contact)
            
        except Exception as e:
            raise ParsingError(f"Failed to parse HTML file: {str(e)}", {'file': str(file_path)})
    
    def extract_contacts(self, file_path: Path) -> List[Contact]:
        """Extract unique contacts from file"""
        messages_by_contact = self.parse(file_path)
        contacts = []
        
        for contact_id, messages in messages_by_contact.items():
            if not messages:
                continue
            
            # Get contact info from first message
            first_msg = messages[0]
            if not first_msg.contact:
                continue
            
            contact = Contact(
                phone_number=first_msg.contact.phone_number,
                display_name=first_msg.contact.display_name,
                message_count=len(messages),
                sent_count=sum(1 for m in messages if m.direction == MessageDirection.SENT),
                received_count=sum(1 for m in messages if m.direction == MessageDirection.RECEIVED)
            )
            
            # Calculate date range
            timestamps = [m.timestamp for m in messages if m.timestamp]
            if timestamps:
                contact.first_message_date = min(timestamps)
                contact.last_message_date = max(timestamps)
            
            # Count media types
            for message in messages:
                if message.media_type != MediaType.TEXT:
                    media_key = message.media_type.value
                    contact.media_count[media_key] = contact.media_count.get(media_key, 0) + 1
            
            contacts.append(contact)
        
        return contacts
    
    def _read_file_safely(self, file_path: Path) -> str:
        """Read file with automatic encoding detection"""
        # Check cache
        if file_path in self._encoding_cache:
            encoding = self._encoding_cache[file_path]
        else:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                self._encoding_cache[file_path] = encoding
                logger.debug(f"Detected encoding for {file_path}: {encoding}")
        
        # Read with detected encoding
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            logger.warning(f"Failed to read with {encoding}, falling back to utf-8 with errors='replace'")
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
    
    def _find_message_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """Find all message elements in the HTML"""
        # Try multiple strategies to find messages
        strategies = [
            # Strategy 1: Look for common message classes
            lambda: soup.find_all(class_=re.compile(r'message|msg|chat-msg|_3_7W3', re.I)),
            
            # Strategy 2: Look for divs with timestamp
            lambda: [elem for elem in soup.find_all('div') 
                    if self._has_timestamp(elem)],
            
            # Strategy 3: Look for specific structure patterns
            lambda: soup.find_all('div', {'data-pre-plain-text': True}),
            
            # Strategy 4: Look for elements with media
            lambda: [elem.parent for elem in soup.find_all(['img', 'audio', 'video']) 
                    if elem.parent]
        ]
        
        for strategy in strategies:
            try:
                elements = strategy()
                if elements:
                    logger.debug(f"Found {len(elements)} messages using strategy")
                    return elements
            except Exception as e:
                logger.debug(f"Strategy failed: {e}")
                continue
        
        # If all strategies fail, try to find any reasonable container
        containers = soup.find_all(['div', 'p', 'span'])
        return [elem for elem in containers if self._looks_like_message(elem)]
    
    def _has_timestamp(self, element: Tag) -> bool:
        """Check if element contains a timestamp"""
        text = element.get_text()
        for pattern, _ in self.DATE_PATTERNS:
            if re.search(pattern, text):
                return True
        return False
    
    def _looks_like_message(self, element: Tag) -> bool:
        """Heuristic to determine if element looks like a message"""
        text = element.get_text(strip=True)
        
        # Must have some content
        if len(text) < 2:
            return False
        
        # Should not be too long (probably not a container)
        if len(text) > 10000:
            return False
        
        # Check for timestamp
        if self._has_timestamp(element):
            return True
        
        # Check for media
        if element.find(['img', 'audio', 'video', 'a']):
            return True
        
        return False
    
    def _parse_message_element(self, element: Tag) -> Optional[Message]:
        """Parse a single message element"""
        # Extract timestamp
        timestamp = self._extract_timestamp(element)
        
        # Extract contact info
        contact_info = self._extract_contact_info(element)
        if not contact_info:
            return None
        
        phone_number, display_name = contact_info
        contact = Contact(phone_number=phone_number, display_name=display_name)
        
        # Classify message direction
        direction = self.classifier.classify(element)
        
        # Extract content and media
        content = self._extract_content(element)
        media_type, media_info = self._extract_media_info(element)
        
        message = Message(
            contact=contact,
            direction=direction,
            content=content,
            timestamp=timestamp,
            media_type=media_type,
            media_filename=media_info.get('filename') if media_info else None
        )
        
        # Add metadata
        if media_info:
            message.metadata.update(media_info)
        
        return message
    
    def _extract_timestamp(self, element: Tag) -> Optional[datetime]:
        """Extract timestamp from message element"""
        # Check data attributes first
        timestamp_attr = element.get('data-pre-plain-text', '')
        if timestamp_attr:
            for pattern, date_format in self.DATE_PATTERNS:
                match = re.search(pattern, timestamp_attr)
                if match:
                    try:
                        date_str = ' '.join(match.groups())
                        return datetime.strptime(date_str, date_format)
                    except ValueError:
                        continue
        
        # Search in element text
        text = element.get_text()
        for pattern, date_format in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = ' '.join(filter(None, match.groups()))
                    # Handle AM/PM if present
                    if 'AM' in date_str or 'PM' in date_str:
                        date_format = date_format.replace('%H:%M', '%I:%M')
                    return datetime.strptime(date_str, date_format)
                except ValueError:
                    continue
        
        return None
    
    def _extract_contact_info(self, element: Tag) -> Optional[Tuple[str, str]]:
        """Extract contact information from message"""
        # Try classifier method first
        contact_info = self.classifier.extract_contact_from_message(element)
        if contact_info:
            return contact_info
        
        # Check data attributes
        pre_text = element.get('data-pre-plain-text', '')
        if pre_text:
            # Pattern: [timestamp] Contact Name/Phone:
            match = re.search(r'\]\s*([^:]+):', pre_text)
            if match:
                contact_str = match.group(1).strip()
                # Extract phone if present
                phone_match = re.search(r'(\+?\d[\d\s\-\(\)]+\d)', contact_str)
                if phone_match:
                    phone = phone_match.group(1)
                    name = contact_str.replace(phone, '').strip()
                    return (phone, name or phone)
                return ('', contact_str)
        
        # Look for author elements
        author_elems = element.find_all(class_=re.compile(r'author|sender|from|copyable-text', re.I))
        for author in author_elems:
            text = author.get_text(strip=True)
            if text and not text.isdigit():
                return ('', text)
        
        return None
    
    def _extract_content(self, element: Tag) -> str:
        """Extract message content"""
        # Remove metadata elements
        for meta_elem in element.find_all(class_=re.compile(r'meta|time|timestamp|copyable-text', re.I)):
            meta_elem.decompose()
        
        # Get text content
        content = element.get_text(separator=' ', strip=True)
        
        # Clean up content
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = content.strip()
        
        return content
    
    def _extract_media_info(self, element: Tag) -> Tuple[MediaType, Optional[Dict]]:
        """Extract media information from message"""
        media_info = {}
        
        # Check for media elements
        media_elem = element.find(['img', 'audio', 'video', 'a'])
        if not media_elem:
            return MediaType.TEXT, None
        
        # Get file reference
        file_ref = (media_elem.get('src') or 
                   media_elem.get('href') or 
                   media_elem.get('data-src'))
        
        if not file_ref:
            return MediaType.TEXT, None
        
        media_info['filename'] = Path(file_ref).name
        media_info['original_path'] = file_ref
        
        # Determine media type
        media_type = MediaType.UNKNOWN
        
        # Check by element type
        if media_elem.name == 'img':
            media_type = MediaType.IMAGE
        elif media_elem.name == 'audio':
            media_type = MediaType.AUDIO
        elif media_elem.name == 'video':
            media_type = MediaType.VIDEO
        else:
            # Check by file extension
            for mtype, pattern in self.MEDIA_PATTERNS.items():
                if re.search(pattern, file_ref, re.I):
                    media_type = mtype
                    break
        
        # Check for special types
        if 'sticker' in file_ref.lower() or 'sticker' in element.get_text().lower():
            media_type = MediaType.STICKER
        
        return media_type, media_info