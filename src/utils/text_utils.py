"""Text processing utility functions"""

import re
from typing import List, Optional
import unicodedata
import logging

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str, default_country_code: str = '+1') -> str:
    """
    Normalize phone number to consistent format
    
    Args:
        phone: Phone number string
        default_country_code: Default country code if missing
        
    Returns:
        Normalized phone number
    """
    # Remove all non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', phone)
    
    # Handle different formats
    if normalized.startswith('+'):
        return normalized
    elif normalized.startswith('00'):
        # International format without +
        return '+' + normalized[2:]
    elif len(normalized) == 10:
        # Likely US number without country code
        return default_country_code + normalized
    elif len(normalized) == 11 and normalized.startswith('1'):
        # US number with country code
        return '+' + normalized
    else:
        # Assume it needs default country code
        return default_country_code + normalized


def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_at = max_length - len(suffix)
    
    # Try to break at word boundary
    if ' ' in text[:truncate_at]:
        truncate_at = text.rfind(' ', 0, truncate_at)
    
    return text[:truncate_at] + suffix


def remove_emojis(text: str) -> str:
    """
    Remove emoji characters from text
    
    Args:
        text: Text containing emojis
        
    Returns:
        Text without emojis
    """
    # Remove emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00010000-\U0010FFFF"  # Supplementary Private Use Area
        "]+", flags=re.UNICODE
    )
    
    return emoji_pattern.sub('', text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text
    
    Args:
        text: Text containing URLs
        
    Returns:
        List of URLs found
    """
    # Improved URL regex pattern
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+|'
        r'(?:www\.)?(?:[a-zA-Z0-9]+\.)+[a-zA-Z]{2,}(?:/[^\\s]*)?',
        re.IGNORECASE
    )
    
    return url_pattern.findall(text)


def clean_message_content(text: str, remove_timestamps: bool = True,
                         remove_urls: bool = False) -> str:
    """
    Clean message content for export
    
    Args:
        text: Original message text
        remove_timestamps: Remove WhatsApp timestamps
        remove_urls: Replace URLs with [URL]
        
    Returns:
        Cleaned text
    """
    # Remove WhatsApp timestamps like [12:34 PM]
    if remove_timestamps:
        text = re.sub(r'\[\d{1,2}:\d{2}(?:\s*[AP]M)?\]', '', text)
    
    # Replace URLs
    if remove_urls:
        urls = extract_urls(text)
        for url in urls:
            text = text.replace(url, '[URL]')
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def anonymize_phone_numbers(text: str) -> str:
    """
    Anonymize phone numbers in text
    
    Args:
        text: Text containing phone numbers
        
    Returns:
        Text with anonymized phone numbers
    """
    # Pattern for phone numbers
    phone_pattern = re.compile(
        r'(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{0,4}'
    )
    
    def replace_phone(match):
        phone = match.group(0)
        # Keep first few digits, replace rest with X
        if len(phone) > 6:
            return phone[:3] + 'X' * (len(phone) - 3)
        return 'XXX-XXXX'
    
    return phone_pattern.sub(replace_phone, text)


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text
    
    Args:
        text: Text containing mentions
        
    Returns:
        List of mentioned usernames
    """
    mention_pattern = re.compile(r'@(\w+)')
    return mention_pattern.findall(text)


def normalize_whitespace(text: str) -> str:
    """
    Normalize various types of whitespace
    
    Args:
        text: Text with irregular whitespace
        
    Returns:
        Text with normalized whitespace
    """
    # Replace various whitespace characters with regular space
    text = re.sub(r'[\xa0\u200b\u2028\u2029]+', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    return text.strip()


def is_media_placeholder(text: str) -> bool:
    """
    Check if text is a media placeholder
    
    Args:
        text: Message text
        
    Returns:
        True if text appears to be a media placeholder
    """
    media_patterns = [
        r'<Media omitted>',
        r'<Médias omis>',
        r'\[Photo\]',
        r'\[Video\]',
        r'\[Audio\]',
        r'\[Document\]',
        r'\[Sticker\]',
        r'\[GIF\]',
        r'image omitted',
        r'video omitted',
        r'audio omitted'
    ]
    
    pattern = '|'.join(media_patterns)
    return bool(re.search(pattern, text, re.IGNORECASE))