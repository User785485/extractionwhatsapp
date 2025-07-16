"""Parsers module for extracting data from various sources"""

from parsers.base_parser import BaseParser
from parsers.html_parser import WhatsAppHTMLParser
from parsers.message_classifier import MessageClassifier
from parsers.mobiletrans_parser import MobileTransParser

# Backward compatibility alias - use MobileTransParser for real files
WhatsAppParser = MobileTransParser

__all__ = [
    'BaseParser',
    'WhatsAppHTMLParser',
    'WhatsAppParser',
    'MobileTransParser',
    'MessageClassifier'
]