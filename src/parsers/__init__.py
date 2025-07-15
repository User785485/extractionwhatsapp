"""Parsers module for extracting data from various sources"""

from .base_parser import BaseParser
from .html_parser import WhatsAppHTMLParser
from .message_classifier import MessageClassifier
from .mobiletrans_parser import MobileTransParser

# Backward compatibility alias - use MobileTransParser for real files
WhatsAppParser = MobileTransParser

__all__ = [
    'BaseParser',
    'WhatsAppHTMLParser',
    'WhatsAppParser',
    'MobileTransParser',
    'MessageClassifier'
]