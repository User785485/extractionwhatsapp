"""SQLite database for caching and state management"""

import sqlite3
import json
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
import logging

from core.models import Contact, Message, TranscriptionResult, MessageDirection, MediaType
from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class CacheDatabase:
    """SQLite database for caching WhatsApp data"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Contacts table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE,
                    display_name TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    sent_count INTEGER DEFAULT 0,
                    received_count INTEGER DEFAULT 0,
                    first_message_date TEXT,
                    last_message_date TEXT,
                    media_count TEXT,  -- JSON
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Messages table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    contact_id INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    content TEXT,
                    timestamp TEXT,
                    media_type TEXT,
                    media_path TEXT,
                    media_filename TEXT,
                    content_hash TEXT,
                    metadata TEXT,  -- JSON
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                )
            ''')
            
            # Transcriptions table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    file_path TEXT UNIQUE,
                    transcription TEXT,
                    language TEXT,
                    confidence REAL,
                    duration REAL,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
                )
            ''')
            
            # Processing state table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processing_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT UNIQUE,
                    state TEXT NOT NULL,
                    checkpoint_data TEXT,  -- JSON
                    error_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Media cache table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS media_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_path TEXT UNIQUE,
                    organized_path TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    media_type TEXT,
                    contact_id INTEGER,
                    direction TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_contact ON messages(contact_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_media_type ON messages(media_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_transcriptions_file ON transcriptions(file_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_hash ON media_cache(file_hash)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise DatabaseError(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def get_or_create_contact(self, phone_number: str, display_name: str) -> Tuple[int, Contact]:
        """Get or create a contact"""
        with self._get_connection() as conn:
            # Try to get existing contact
            cursor = conn.execute(
                "SELECT * FROM contacts WHERE phone_number = ? OR display_name = ?",
                (phone_number, display_name)
            )
            row = cursor.fetchone()
            
            if row:
                contact = self._row_to_contact(row)
                return row['id'], contact
            
            # Create new contact
            cursor = conn.execute(
                '''INSERT INTO contacts (phone_number, display_name, media_count) 
                   VALUES (?, ?, ?)''',
                (phone_number, display_name, '{}')
            )
            conn.commit()
            
            contact = Contact(phone_number=phone_number, display_name=display_name)
            return cursor.lastrowid, contact
    
    def update_contact_stats(self, contact_id: int, stats: Dict[str, Any]):
        """Update contact statistics"""
        with self._get_connection() as conn:
            conn.execute(
                '''UPDATE contacts SET 
                   message_count = ?,
                   sent_count = ?,
                   received_count = ?,
                   first_message_date = ?,
                   last_message_date = ?,
                   media_count = ?,
                   updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?''',
                (
                    stats.get('message_count', 0),
                    stats.get('sent_count', 0),
                    stats.get('received_count', 0),
                    stats.get('first_message_date'),
                    stats.get('last_message_date'),
                    json.dumps(stats.get('media_count', {})),
                    contact_id
                )
            )
            conn.commit()
    
    def add_message(self, message: Message, contact_id: int) -> int:
        """Add a message to the database"""
        content_hash = self._hash_content(message.content)
        
        with self._get_connection() as conn:
            # Check if message already exists
            cursor = conn.execute(
                "SELECT id FROM messages WHERE content_hash = ? AND contact_id = ?",
                (content_hash, contact_id)
            )
            existing = cursor.fetchone()
            if existing:
                return existing['id']
            
            # Insert new message
            cursor = conn.execute(
                '''INSERT INTO messages (
                    message_id, contact_id, direction, content, timestamp,
                    media_type, media_path, media_filename, content_hash, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    message.id,
                    contact_id,
                    message.direction.value,
                    message.content,
                    message.timestamp.isoformat() if message.timestamp else None,
                    message.media_type.value,
                    str(message.media_path) if message.media_path else None,
                    message.media_filename,
                    content_hash,
                    json.dumps(message.metadata)
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_messages_for_contact(self, contact_id: int, 
                                limit: Optional[int] = None,
                                offset: int = 0) -> List[Message]:
        """Get messages for a contact"""
        with self._get_connection() as conn:
            query = '''SELECT * FROM messages WHERE contact_id = ? 
                      ORDER BY timestamp DESC'''
            params = [contact_id]
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            return [self._row_to_message(row) for row in cursor]
    
    def add_transcription(self, result: TranscriptionResult, 
                         message_id: Optional[int] = None) -> int:
        """Add a transcription result"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                '''INSERT OR REPLACE INTO transcriptions (
                    message_id, file_path, transcription, language,
                    confidence, duration, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    message_id,
                    str(result.file_path),
                    result.text,
                    result.language,
                    result.confidence,
                    result.duration,
                    result.error
                )
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_transcription(self, file_path: Path) -> Optional[TranscriptionResult]:
        """Get transcription for a file"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM transcriptions WHERE file_path = ?",
                (str(file_path),)
            )
            row = cursor.fetchone()
            return self._row_to_transcription(row) if row else None
    
    def has_transcription(self, file_path: Path) -> bool:
        """Check if file has been transcribed"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM transcriptions WHERE file_path = ? AND error IS NULL",
                (str(file_path),)
            )
            return cursor.fetchone() is not None
    
    def save_processing_state(self, task_name: str, state: str, 
                            checkpoint_data: Optional[Dict[str, Any]] = None):
        """Save processing state for resume capability"""
        with self._get_connection() as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO processing_state 
                   (task_name, state, checkpoint_data, updated_at)
                   VALUES (?, ?, ?, CURRENT_TIMESTAMP)''',
                (task_name, state, json.dumps(checkpoint_data) if checkpoint_data else None)
            )
            conn.commit()
    
    def get_processing_state(self, task_name: str) -> Optional[Dict[str, Any]]:
        """Get processing state"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM processing_state WHERE task_name = ?",
                (task_name,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'state': row['state'],
                    'checkpoint_data': json.loads(row['checkpoint_data']) if row['checkpoint_data'] else None,
                    'error_count': row['error_count'],
                    'last_error': row['last_error'],
                    'updated_at': row['updated_at']
                }
            return None
    
    def add_media_cache(self, original_path: Path, organized_path: Path,
                       media_type: str, contact_id: int, direction: str):
        """Add media file to cache"""
        file_hash = self._hash_file(original_path)
        
        with self._get_connection() as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO media_cache 
                   (original_path, organized_path, file_hash, file_size,
                    media_type, contact_id, direction)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    str(original_path),
                    str(organized_path),
                    file_hash,
                    original_path.stat().st_size,
                    media_type,
                    contact_id,
                    direction
                )
            )
            conn.commit()
    
    def get_media_cache(self, original_path: Path) -> Optional[Dict[str, Any]]:
        """Get media cache entry"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM media_cache WHERE original_path = ?",
                (str(original_path),)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self._get_connection() as conn:
            stats = {}
            
            # Count totals
            for table in ['contacts', 'messages', 'transcriptions', 'media_cache']:
                cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f'total_{table}'] = cursor.fetchone()['count']
            
            # Get message breakdown
            cursor = conn.execute(
                "SELECT media_type, COUNT(*) as count FROM messages GROUP BY media_type"
            )
            stats['messages_by_type'] = {row['media_type']: row['count'] for row in cursor}
            
            # Get transcription stats
            cursor = conn.execute(
                "SELECT COUNT(*) as count FROM transcriptions WHERE error IS NULL"
            )
            stats['successful_transcriptions'] = cursor.fetchone()['count']
            
            return stats
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old cached data"""
        cutoff_date = datetime.now().timestamp() - (days * 86400)
        
        with self._get_connection() as conn:
            # Clean old transcriptions
            conn.execute(
                "DELETE FROM transcriptions WHERE created_at < datetime(?, 'unixepoch')",
                (cutoff_date,)
            )
            
            # Clean old processing states
            conn.execute(
                "DELETE FROM processing_state WHERE updated_at < datetime(?, 'unixepoch')",
                (cutoff_date,)
            )
            
            conn.commit()
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _hash_file(self, file_path: Path) -> str:
        """Generate hash for file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _row_to_contact(self, row) -> Contact:
        """Convert database row to Contact object"""
        return Contact(
            phone_number=row['phone_number'],
            display_name=row['display_name'],
            message_count=row['message_count'],
            sent_count=row['sent_count'],
            received_count=row['received_count'],
            first_message_date=datetime.fromisoformat(row['first_message_date']) if row['first_message_date'] else None,
            last_message_date=datetime.fromisoformat(row['last_message_date']) if row['last_message_date'] else None,
            media_count=json.loads(row['media_count']) if row['media_count'] else {}
        )
    
    def _row_to_message(self, row) -> Message:
        """Convert database row to Message object"""
        return Message(
            id=row['message_id'],
            direction=MessageDirection(row['direction']),
            content=row['content'],
            timestamp=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else None,
            media_type=MediaType(row['media_type']),
            media_path=Path(row['media_path']) if row['media_path'] else None,
            media_filename=row['media_filename'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _row_to_transcription(self, row) -> TranscriptionResult:
        """Convert database row to TranscriptionResult object"""
        return TranscriptionResult(
            file_path=Path(row['file_path']),
            text=row['transcription'],
            language=row['language'],
            confidence=row['confidence'],
            duration=row['duration'],
            error=row['error'],
            timestamp=datetime.fromisoformat(row['created_at'])
        )

# Alias for backward compatibility
DatabaseManager = CacheDatabase