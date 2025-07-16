"""Application state management"""

import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging

from core.database import CacheDatabase
from core.models import ProcessingStats, Contact, Message
from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state and processing checkpoints"""
    
    def __init__(self, database: CacheDatabase):
        self.db = database
        self.current_task: Optional[str] = None
        self.stats = ProcessingStats()
        self._checkpoints: Dict[str, Any] = {}
    
    def start_task(self, task_name: str):
        """Start a new task"""
        self.current_task = task_name
        self.stats = ProcessingStats()
        
        # Check for existing state
        existing_state = self.db.get_processing_state(task_name)
        if existing_state and existing_state['state'] != 'completed':
            logger.info(f"Resuming task '{task_name}' from checkpoint")
            self._checkpoints = existing_state.get('checkpoint_data', {})
            return True
        
        # Save initial state
        self.db.save_processing_state(task_name, 'started')
        return False
    
    def save_checkpoint(self, checkpoint_name: str, data: Any):
        """Save a checkpoint"""
        if not self.current_task:
            raise ValueError("No active task")
        
        self._checkpoints[checkpoint_name] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.db.save_processing_state(
            self.current_task,
            'in_progress',
            self._checkpoints
        )
    
    def get_checkpoint(self, checkpoint_name: str) -> Optional[Any]:
        """Get checkpoint data"""
        checkpoint = self._checkpoints.get(checkpoint_name)
        if checkpoint:
            return checkpoint.get('data')
        return None
    
    def complete_task(self):
        """Mark current task as completed"""
        if not self.current_task:
            raise ValueError("No active task")
        
        self.stats.end_time = datetime.now()
        
        # Save final state
        self.db.save_processing_state(
            self.current_task,
            'completed',
            {
                'stats': self.stats.to_dict(),
                'completed_at': datetime.now().isoformat()
            }
        )
        
        self.current_task = None
    
    def fail_task(self, error: str):
        """Mark current task as failed"""
        if not self.current_task:
            raise ValueError("No active task")
        
        self.stats.end_time = datetime.now()
        self.stats.add_error('task_failed', error)
        
        # Update error count in database
        state = self.db.get_processing_state(self.current_task)
        error_count = (state.get('error_count', 0) if state else 0) + 1
        
        self.db.save_processing_state(
            self.current_task,
            'failed',
            {
                'stats': self.stats.to_dict(),
                'error': error,
                'error_count': error_count,
                'failed_at': datetime.now().isoformat()
            }
        )
        
        self.current_task = None
    
    def track_contact(self, contact: Contact, is_processed: bool = True):
        """Track contact processing"""
        self.stats.total_contacts += 1
        if is_processed:
            self.stats.processed_contacts += 1
        else:
            self.stats.skipped_contacts += 1
    
    def track_message(self, message: Message):
        """Track message processing"""
        self.stats.total_messages += 1
        self.stats.processed_messages += 1
        
        if message.media_type.value == 'text':
            self.stats.text_messages += 1
        else:
            self.stats.media_messages += 1
    
    def track_media(self, total: int = 0, organized: int = 0):
        """Track media processing"""
        if total:
            self.stats.total_media_files += total
        if organized:
            self.stats.organized_media_files += organized
    
    def track_transcription(self, total: int = 0, transcribed: int = 0, 
                          failed: int = 0, cached: int = 0):
        """Track transcription processing"""
        if total:
            self.stats.total_audio_files += total
        if transcribed:
            self.stats.transcribed_files += transcribed
        if failed:
            self.stats.failed_transcriptions += failed
        if cached:
            self.stats.cached_transcriptions += cached
    
    def track_export(self, format: str):
        """Track export creation"""
        if format not in self.stats.exported_formats:
            self.stats.exported_formats.append(format)
        self.stats.export_files_created += 1
    
    def add_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add an error to stats"""
        self.stats.add_error(error_type, message, details)
        logger.error(f"{error_type}: {message}", extra={'details': details})
    
    def add_warning(self, warning_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Add a warning to stats"""
        self.stats.add_warning(warning_type, message, details)
        logger.warning(f"{warning_type}: {message}", extra={'details': details})
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get summary of current stats"""
        summary = self.stats.to_dict()
        
        # Add database stats
        try:
            db_stats = self.db.get_stats()
            summary['database'] = db_stats
        except DatabaseError as e:
            logger.error(f"Failed to get database stats: {e}")
        
        return summary
    
    def should_skip_contact(self, contact: Contact, min_messages: Optional[int] = None,
                          after_date: Optional[datetime] = None) -> bool:
        """Check if contact should be skipped based on filters"""
        # Check message count
        if min_messages and contact.message_count < min_messages:
            return True
        
        # Check date filter
        if after_date and contact.last_message_date:
            if contact.last_message_date < after_date:
                return True
        
        return False
    
    def get_resume_info(self) -> Dict[str, Any]:
        """Get information for resuming processing"""
        if not self.current_task:
            return {}
        
        state = self.db.get_processing_state(self.current_task)
        if not state:
            return {}
        
        return {
            'task': self.current_task,
            'state': state['state'],
            'checkpoints': list(self._checkpoints.keys()),
            'error_count': state.get('error_count', 0),
            'last_error': state.get('last_error'),
            'updated_at': state.get('updated_at')
        }