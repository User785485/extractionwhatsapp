"""Core data models"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path


class MessageDirection(Enum):
    """Message direction enumeration"""
    SENT = "sent"
    RECEIVED = "received"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class MediaType(Enum):
    """Media type enumeration"""
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"
    STICKER = "sticker"
    GIF = "gif"
    LOCATION = "location"
    CONTACT = "contact"
    UNKNOWN = "unknown"


@dataclass
class Contact:
    """Represents a WhatsApp contact"""
    phone_number: str
    display_name: str
    message_count: int = 0
    sent_count: int = 0
    received_count: int = 0
    first_message_date: Optional[datetime] = None
    last_message_date: Optional[datetime] = None
    media_count: Dict[str, int] = field(default_factory=dict)
    
    @property
    def identifier(self) -> str:
        """Get unique identifier for contact"""
        return self.phone_number or self.display_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'phone_number': self.phone_number,
            'display_name': self.display_name,
            'message_count': self.message_count,
            'sent_count': self.sent_count,
            'received_count': self.received_count,
            'first_message_date': self.first_message_date.isoformat() if self.first_message_date else None,
            'last_message_date': self.last_message_date.isoformat() if self.last_message_date else None,
            'media_count': self.media_count
        }


@dataclass
class Message:
    """Represents a WhatsApp message"""
    id: Optional[str] = None
    contact: Optional[Contact] = None
    direction: MessageDirection = MessageDirection.UNKNOWN
    content: str = ""
    timestamp: Optional[datetime] = None
    media_type: MediaType = MediaType.TEXT
    media_path: Optional[Path] = None
    media_filename: Optional[str] = None
    transcription: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_media(self) -> bool:
        """Check if message has media"""
        return self.media_type != MediaType.TEXT
    
    @property
    def needs_transcription(self) -> bool:
        """Check if message needs transcription"""
        return self.media_type == MediaType.AUDIO and not self.transcription
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'contact': self.contact.identifier if self.contact else None,
            'direction': self.direction.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'media_type': self.media_type.value,
            'media_path': str(self.media_path) if self.media_path else None,
            'media_filename': self.media_filename,
            'transcription': self.transcription,
            'metadata': self.metadata
        }


@dataclass
class TranscriptionResult:
    """Represents a transcription result"""
    file_path: Path
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if transcription was successful"""
        return self.error is None and bool(self.text)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'file_path': str(self.file_path),
            'text': self.text,
            'language': self.language,
            'confidence': self.confidence,
            'duration': self.duration,
            'timestamp': self.timestamp.isoformat(),
            'error': self.error,
            'success': self.success
        }


@dataclass
class ProcessingStats:
    """Tracks processing statistics"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Contacts
    total_contacts: int = 0
    processed_contacts: int = 0
    skipped_contacts: int = 0
    
    # Messages
    total_messages: int = 0
    processed_messages: int = 0
    text_messages: int = 0
    media_messages: int = 0
    
    # Media
    total_media_files: int = 0
    organized_media_files: int = 0
    
    # Transcriptions
    total_audio_files: int = 0
    transcribed_files: int = 0
    failed_transcriptions: int = 0
    cached_transcriptions: int = 0
    
    # Exports
    exported_formats: List[str] = field(default_factory=list)
    export_files_created: int = 0
    
    # Errors
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[float]:
        """Get processing duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_messages == 0:
            return 0.0
        return (self.processed_messages / self.total_messages) * 100
    
    @property
    def transcription_success_rate(self) -> float:
        """Calculate transcription success rate"""
        if self.total_audio_files == 0:
            return 0.0
        return (self.transcribed_files / self.total_audio_files) * 100
    
    def add_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to the stats"""
        self.errors.append({
            'type': error_type,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def add_warning(self, warning_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a warning to the stats"""
        self.warnings.append({
            'type': warning_type,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'contacts': {
                'total': self.total_contacts,
                'processed': self.processed_contacts,
                'skipped': self.skipped_contacts
            },
            'messages': {
                'total': self.total_messages,
                'processed': self.processed_messages,
                'text': self.text_messages,
                'media': self.media_messages
            },
            'media': {
                'total': self.total_media_files,
                'organized': self.organized_media_files
            },
            'transcriptions': {
                'total': self.total_audio_files,
                'transcribed': self.transcribed_files,
                'failed': self.failed_transcriptions,
                'cached': self.cached_transcriptions,
                'success_rate': self.transcription_success_rate
            },
            'exports': {
                'formats': self.exported_formats,
                'files_created': self.export_files_created
            },
            'performance': {
                'success_rate': self.success_rate
            },
            'errors': len(self.errors),
            'warnings': len(self.warnings)
        }