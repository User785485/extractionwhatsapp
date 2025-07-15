"""Media file organization and processing"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import logging
import re
from collections import defaultdict

from ..core.models import Contact, MessageDirection, MediaType
from ..core.database import CacheDatabase
from ..core.exceptions import MediaProcessingError
from ..utils.file_utils import sanitize_filename, create_unique_filename

logger = logging.getLogger(__name__)


class MediaProcessor:
    """Organizes and processes media files from WhatsApp export"""
    
    # Media file patterns
    MEDIA_EXTENSIONS = {
        MediaType.AUDIO: {'.opus', '.mp3', '.m4a', '.wav', '.ogg', '.aac', '.flac', '.wma'},
        MediaType.VIDEO: {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v', '.3gp'},
        MediaType.IMAGE: {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif'},
        MediaType.DOCUMENT: {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.zip', '.rar'},
        MediaType.STICKER: {'.webp'}  # WhatsApp stickers are usually webp
    }
    
    # WhatsApp media naming patterns
    WHATSAPP_PATTERNS = [
        # Pattern: WhatsApp Audio 2024-01-15 at 14.30.00.opus
        (r'WhatsApp\s+(Audio|Video|Image|Animated Gifs?)\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{2}\.\d{2}\.\d{2})', 'whatsapp_standard'),
        # Pattern: AUD-20240115-WA0001.opus
        (r'(AUD|VID|IMG|DOC|STK)-(\d{8})-WA(\d+)', 'whatsapp_short'),
        # Pattern: audio_2024-01-15_14-30-00.opus
        (r'(audio|video|image|document|sticker)_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})', 'generic_timestamp'),
        # Pattern with sender/receiver: sent_audio_abc123.opus
        (r'(sent|received)_?(audio|video|image|document|sticker)?_?([a-zA-Z0-9\-]+)', 'directional')
    ]
    
    def __init__(self, source_dir: Path, output_dir: Path, 
                 database: Optional[CacheDatabase] = None):
        """
        Initialize media processor
        
        Args:
            source_dir: Directory containing WhatsApp export files
            output_dir: Directory for organized media output
            database: Optional database for caching
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.database = database
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self._stats = {
            'total_files': 0,
            'organized_files': 0,
            'skipped_files': 0,
            'errors': 0,
            'by_type': defaultdict(int),
            'by_contact': defaultdict(int)
        }
    
    def organize_media(self, contacts: List[Contact], 
                      copy_files: bool = True) -> Dict[str, List[Path]]:
        """
        Organize media files by contact and direction
        
        Args:
            contacts: List of contacts to organize media for
            copy_files: Whether to copy files (True) or move them (False)
            
        Returns:
            Dictionary mapping contact identifiers to organized file paths
        """
        logger.info(f"Organizing media files for {len(contacts)} contacts")
        
        # Scan for all media files
        media_files = self._scan_media_files()
        self._stats['total_files'] = len(media_files)
        logger.info(f"Found {len(media_files)} media files")
        
        # Create contact lookup
        contact_lookup = self._create_contact_lookup(contacts)
        
        # Organize files
        organized_files = defaultdict(list)
        
        for media_file in media_files:
            try:
                contact, direction = self._identify_file_owner(media_file, contact_lookup)
                
                if contact:
                    # Create output path
                    output_path = self._create_output_path(contact, media_file, direction)
                    
                    # Check cache
                    if self.database:
                        cached = self.database.get_media_cache(media_file)
                        if cached and Path(cached['organized_path']).exists():
                            organized_files[contact.identifier].append(Path(cached['organized_path']))
                            self._stats['organized_files'] += 1
                            continue
                    
                    # Copy or move file
                    if copy_files:
                        shutil.copy2(media_file, output_path)
                    else:
                        shutil.move(str(media_file), str(output_path))
                    
                    organized_files[contact.identifier].append(output_path)
                    self._stats['organized_files'] += 1
                    self._stats['by_contact'][contact.identifier] += 1
                    
                    # Update cache
                    if self.database and contact:
                        contact_id, _ = self.database.get_or_create_contact(
                            contact.phone_number, contact.display_name
                        )
                        self.database.add_media_cache(
                            media_file, output_path,
                            self._get_media_type(media_file).value,
                            contact_id, direction.value
                        )
                else:
                    self._stats['skipped_files'] += 1
                    logger.debug(f"Could not identify owner for: {media_file.name}")
                    
            except Exception as e:
                logger.error(f"Failed to organize {media_file}: {e}")
                self._stats['errors'] += 1
        
        self._log_stats()
        return dict(organized_files)
    
    def _scan_media_files(self) -> List[Path]:
        """Scan source directory for media files"""
        media_files = []
        
        # Get all extensions to search for
        all_extensions = set()
        for extensions in self.MEDIA_EXTENSIONS.values():
            all_extensions.update(extensions)
        
        # Scan directory
        for file_path in self.source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in all_extensions:
                media_files.append(file_path)
                
                # Track media types
                media_type = self._get_media_type(file_path)
                self._stats['by_type'][media_type.value] += 1
        
        return media_files
    
    def _get_media_type(self, file_path: Path) -> MediaType:
        """Determine media type from file extension"""
        ext = file_path.suffix.lower()
        
        for media_type, extensions in self.MEDIA_EXTENSIONS.items():
            if ext in extensions:
                return media_type
        
        return MediaType.UNKNOWN
    
    def _create_contact_lookup(self, contacts: List[Contact]) -> Dict[str, Contact]:
        """Create lookup dictionary for contacts"""
        lookup = {}
        
        for contact in contacts:
            # Add by phone number
            if contact.phone_number:
                lookup[self._normalize_phone(contact.phone_number)] = contact
            
            # Add by display name
            if contact.display_name:
                lookup[contact.display_name.lower()] = contact
                
                # Also add sanitized version
                sanitized = sanitize_filename(contact.display_name)
                lookup[sanitized.lower()] = contact
        
        return lookup
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for matching"""
        # Remove all non-digits
        normalized = re.sub(r'\D', '', phone)
        
        # Remove country code variations
        if normalized.startswith('1') and len(normalized) == 11:
            normalized = normalized[1:]  # Remove US country code
        elif normalized.startswith('33') and len(normalized) == 11:
            normalized = normalized[2:]  # Remove FR country code
        
        return normalized
    
    def _identify_file_owner(self, file_path: Path, 
                           contact_lookup: Dict[str, Contact]) -> Tuple[Optional[Contact], MessageDirection]:
        """Identify which contact owns a media file"""
        filename = file_path.name.lower()
        
        # Check for direction indicators
        direction = MessageDirection.UNKNOWN
        if 'sent' in filename or 'envoyé' in filename:
            direction = MessageDirection.SENT
        elif 'received' in filename or 'reçu' in filename:
            direction = MessageDirection.RECEIVED
        
        # Try to extract contact info from filename
        for pattern, pattern_type in self.WHATSAPP_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                if pattern_type == 'directional':
                    # Pattern includes direction
                    if match.group(1) == 'sent':
                        direction = MessageDirection.SENT
                    else:
                        direction = MessageDirection.RECEIVED
                break
        
        # Check parent directory name
        parent_name = file_path.parent.name.lower()
        
        # Look for contact in lookup
        for key, contact in contact_lookup.items():
            if key in filename or key in parent_name:
                return contact, direction
        
        # Try partial matching
        for key, contact in contact_lookup.items():
            # Check if any significant part matches
            key_parts = key.split()
            if any(part in filename or part in parent_name for part in key_parts if len(part) > 3):
                return contact, direction
        
        return None, direction
    
    def _create_output_path(self, contact: Contact, media_file: Path, 
                          direction: MessageDirection) -> Path:
        """Create organized output path for media file"""
        # Create contact directory
        contact_dir = self.output_dir / sanitize_filename(contact.identifier)
        
        # Create direction subdirectory
        if direction == MessageDirection.SENT:
            dir_name = "sent"
        elif direction == MessageDirection.RECEIVED:
            dir_name = "received"
        else:
            dir_name = "unknown"
        
        direction_dir = contact_dir / dir_name
        
        # Create media type subdirectory
        media_type = self._get_media_type(media_file)
        type_dir = direction_dir / media_type.value
        
        # Create directories
        type_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename if needed
        output_path = type_dir / media_file.name
        if output_path.exists():
            output_path = create_unique_filename(output_path)
        
        return output_path
    
    def get_audio_files_for_contact(self, contact: Contact) -> Dict[str, List[Path]]:
        """
        Get all audio files for a specific contact
        
        Args:
            contact: Contact to get audio files for
            
        Returns:
            Dictionary with 'sent' and 'received' lists of audio files
        """
        audio_files = {'sent': [], 'received': []}
        
        contact_dir = self.output_dir / sanitize_filename(contact.identifier)
        
        if contact_dir.exists():
            # Check sent directory
            sent_audio = contact_dir / 'sent' / 'audio'
            if sent_audio.exists():
                audio_files['sent'] = list(sent_audio.glob('*'))
            
            # Check received directory
            received_audio = contact_dir / 'received' / 'audio'
            if received_audio.exists():
                audio_files['received'] = list(received_audio.glob('*'))
        
        return audio_files
    
    def _log_stats(self):
        """Log processing statistics"""
        logger.info("Media organization completed:")
        logger.info(f"  Total files: {self._stats['total_files']}")
        logger.info(f"  Organized: {self._stats['organized_files']}")
        logger.info(f"  Skipped: {self._stats['skipped_files']}")
        logger.info(f"  Errors: {self._stats['errors']}")
        logger.info("  By type:")
        for media_type, count in self._stats['by_type'].items():
            logger.info(f"    {media_type}: {count}")
        
        if self._stats['by_contact']:
            logger.info(f"  Organized for {len(self._stats['by_contact'])} contacts")
    
    def get_stats(self) -> Dict[str, any]:
        """Get processing statistics"""
        return dict(self._stats)