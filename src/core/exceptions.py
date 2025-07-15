"""Custom exceptions for WhatsApp Extractor"""

from typing import Optional, Dict, Any


class WhatsAppExtractorError(Exception):
    """Base exception for all WhatsApp Extractor errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(WhatsAppExtractorError):
    """Configuration related errors"""
    pass


class ParsingError(WhatsAppExtractorError):
    """HTML parsing errors"""
    pass


class MediaProcessingError(WhatsAppExtractorError):
    """Media file processing errors"""
    pass


class TranscriptionError(WhatsAppExtractorError):
    """Transcription processing errors"""
    pass


class ExportError(WhatsAppExtractorError):
    """Export processing errors"""
    pass


class DatabaseError(WhatsAppExtractorError):
    """Database operation errors"""
    pass


class ValidationError(WhatsAppExtractorError):
    """Data validation errors"""
    pass


class APIError(WhatsAppExtractorError):
    """External API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.status_code = status_code
        self.response = response


class FileSystemError(WhatsAppExtractorError):
    """File system operation errors"""
    pass


class ProcessingError(WhatsAppExtractorError):
    """General processing errors"""
    pass