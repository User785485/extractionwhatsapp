"""Main extraction pipeline for WhatsApp Extractor v2"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import threading
import queue
import time

from ..config.config_manager import ConfigManager
from ..core.database import CacheDatabase
from ..parsers import WhatsAppParser
from ..processors.media_processor import MediaProcessor
from ..processors.transcription.batch_processor import BatchTranscriptionProcessor
from ..filters.message_filters import MessageFilterProcessor
from ..exporters import CSVExporter, ExcelExporter, JSONExporter
from ..utils.logger import WhatsAppLogger

logger = logging.getLogger(__name__)


class ExtractionPipeline:
    """Main pipeline for processing WhatsApp data"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize extraction pipeline
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.config = config_manager.config
        self.database = None
        self.parser = None
        self.media_processor = None
        self.transcription_processor = None
        self.filter_processor = None
        
        # Progress tracking
        self._progress_callback = None
        self._stop_event = threading.Event()
        self._current_task = ""
        self._progress = 0.0
        
        # Results
        self.results = {
            'contacts': [],
            'messages': [],
            'transcriptions': [],
            'media_files': {},
            'stats': {}
        }
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all pipeline components"""
        try:
            # Initialize database
            db_path = self.config.paths.database_path
            self.database = CacheDatabase(db_path)
            
            # Initialize parser
            self.parser = WhatsAppParser()
            
            # Initialize media processor
            if hasattr(self.config.paths, 'whatsapp_export_path'):
                self.media_processor = MediaProcessor(
                    source_dir=self.config.paths.whatsapp_export_path,
                    output_dir=self.config.paths.media_output_dir,
                    database=self.database
                )
            
            # Initialize transcription processor
            if self.config.transcription.api_key:
                self.transcription_processor = BatchTranscriptionProcessor(
                    config=self.config.transcription,
                    database=self.database
                )
            
            # Initialize filter processor
            self.filter_processor = MessageFilterProcessor(self.config.filters)
            
            logger.info("Pipeline components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline components: {e}")
            raise
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set progress update callback"""
        self._progress_callback = callback
    
    def _update_progress(self, task: str, progress: float):
        """Update progress and notify callback"""
        self._current_task = task
        self._progress = progress
        
        if self._progress_callback:
            try:
                self._progress_callback(task, progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def stop_processing(self):
        """Stop the extraction process"""
        self._stop_event.set()
        logger.info("Stop signal sent to extraction pipeline")
    
    def extract_full_pipeline(self, source_path: str) -> Dict[str, Any]:
        """
        Run the complete extraction pipeline
        
        Args:
            source_path: Path to WhatsApp export directory
            
        Returns:
            Dictionary with extraction results
        """
        try:
            logger.info(f"Starting full extraction pipeline for: {source_path}")
            self._stop_event.clear()
            
            # Phase 1: Parse HTML files
            self._update_progress("Parsing WhatsApp HTML files...", 10)
            if self._stop_event.is_set():
                return self._get_cancelled_result()
                
            contacts, messages = self._parse_html_files(source_path)
            self.results['contacts'] = contacts
            self.results['messages'] = messages
            
            # Phase 2: Process media files
            self._update_progress("Organizing media files...", 30)
            if self._stop_event.is_set():
                return self._get_cancelled_result()
                
            media_files = self._process_media_files(contacts)
            self.results['media_files'] = media_files
            
            # Phase 3: Transcribe audio files
            if self.config.transcription.api_key and any(contacts):
                self._update_progress("Transcribing audio files...", 50)
                if self._stop_event.is_set():
                    return self._get_cancelled_result()
                    
                transcriptions = self._transcribe_audio_files()
                self.results['transcriptions'] = transcriptions
            
            # Phase 4: Apply filters
            self._update_progress("Applying filters...", 70)
            if self._stop_event.is_set():
                return self._get_cancelled_result()
                
            filtered_data = self._apply_filters()
            
            # Phase 5: Generate exports
            self._update_progress("Generating exports...", 90)
            if self._stop_event.is_set():
                return self._get_cancelled_result()
                
            export_paths = self._generate_exports(filtered_data)
            
            # Complete
            self._update_progress("Extraction completed!", 100)
            
            # Calculate final stats
            self.results['stats'] = self._calculate_stats()
            self.results['export_paths'] = export_paths
            
            logger.info("Full extraction pipeline completed successfully")
            return self.results
            
        except Exception as e:
            logger.error(f"Extraction pipeline failed: {e}")
            self._update_progress(f"Error: {str(e)}", 0)
            raise
    
    def _parse_html_files(self, source_path: str) -> tuple:
        """Parse HTML files from WhatsApp export"""
        contacts = []
        messages = []
        
        try:
            source_dir = Path(source_path)
            html_files = list(source_dir.glob("*.html"))
            
            if not html_files:
                logger.warning("No HTML files found in source directory")
                return contacts, messages
            
            logger.info(f"Found {len(html_files)} HTML files to parse")
            
            for i, html_file in enumerate(html_files):
                if self._stop_event.is_set():
                    break
                    
                progress = 10 + (i / len(html_files)) * 15  # 10-25%
                self._update_progress(f"Parsing {html_file.name}...", progress)
                
                try:
                    # Parse HTML file - returns dict mapping contacts to messages
                    contact_messages = self.parser.parse(html_file)
                    
                    # Extract contacts and messages from the parser result
                    for contact_key, contact_messages_list in contact_messages.items():
                        messages.extend(contact_messages_list)
                        
                        # Create contact object from messages
                        if contact_messages_list:
                            # Get contact info from first message
                            first_message = contact_messages_list[0]
                            contact_name = getattr(first_message, 'contact_name', contact_key)
                            
                            # Create contact object (simplified)
                            from ..core.models import Contact
                            contact = Contact(
                                phone_number=contact_key if contact_key.startswith('+') else '',
                                display_name=contact_name,
                                message_count=len(contact_messages_list)
                            )
                            contacts.append(contact)
                            
                            # Save to database
                            contact_id, _ = self.database.get_or_create_contact(
                                contact.phone_number, contact.display_name
                            )
                            
                            # Save messages to database
                            for message in contact_messages_list:
                                self.database.add_message(message, contact_id)
                    
                except Exception as e:
                    logger.error(f"Failed to parse {html_file}: {e}")
                    continue
            
            logger.info(f"Parsed {len(contacts)} contacts and {len(messages)} messages")
            return contacts, messages
            
        except Exception as e:
            logger.error(f"HTML parsing failed: {e}")
            return contacts, messages
    
    def _process_media_files(self, contacts: List) -> Dict[str, List[Path]]:
        """Process and organize media files"""
        if not self.media_processor:
            logger.warning("Media processor not initialized")
            return {}
        
        try:
            return self.media_processor.organize_media(contacts, copy_files=True)
        except Exception as e:
            logger.error(f"Media processing failed: {e}")
            return {}
    
    def _transcribe_audio_files(self) -> List[Dict[str, Any]]:
        """Transcribe audio files"""
        if not self.transcription_processor:
            logger.warning("Transcription processor not initialized")
            return []
        
        try:
            # Get all audio files from organized media
            audio_files = []
            for contact_files in self.results['media_files'].values():
                for file_path in contact_files:
                    if file_path.suffix.lower() in {'.opus', '.mp3', '.m4a', '.wav', '.ogg'}:
                        audio_files.append(file_path)
            
            if not audio_files:
                logger.info("No audio files found for transcription")
                return []
            
            logger.info(f"Starting transcription of {len(audio_files)} audio files")
            
            # Process transcriptions with progress updates
            transcriptions = []
            for i, audio_file in enumerate(audio_files):
                if self._stop_event.is_set():
                    break
                    
                progress = 50 + (i / len(audio_files)) * 15  # 50-65%
                self._update_progress(f"Transcribing {audio_file.name}...", progress)
                
                try:
                    result = self.transcription_processor.transcribe_file(audio_file)
                    if result:
                        transcriptions.append({
                            'file_path': str(audio_file),
                            'transcription': result.text,
                            'language': result.language,
                            'confidence': result.confidence,
                            'duration': result.duration,
                            'error': result.error
                        })
                        
                        # Save to database
                        self.database.add_transcription(result)
                        
                except Exception as e:
                    logger.error(f"Transcription failed for {audio_file}: {e}")
                    continue
            
            logger.info(f"Completed {len(transcriptions)} transcriptions")
            return transcriptions
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {e}")
            return []
    
    def _apply_filters(self) -> Dict[str, List]:
        """Apply configured filters to the data"""
        try:
            filtered_contacts = self.filter_processor.filter_contacts(self.results['contacts'])
            filtered_messages = self.filter_processor.filter_messages(self.results['messages'])
            
            logger.info(f"Filters applied: {len(filtered_contacts)} contacts, {len(filtered_messages)} messages")
            
            return {
                'contacts': filtered_contacts,
                'messages': filtered_messages,
                'transcriptions': self.results['transcriptions']
            }
            
        except Exception as e:
            logger.error(f"Filter application failed: {e}")
            return {
                'contacts': self.results['contacts'],
                'messages': self.results['messages'],
                'transcriptions': self.results['transcriptions']
            }
    
    def _generate_exports(self, filtered_data: Dict[str, List]) -> Dict[str, str]:
        """Generate export files in configured formats"""
        export_paths = {}
        output_dir = self.config.paths.export_output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Prepare data for export
            export_data = self._prepare_export_data(filtered_data)
            
            # CSV Export
            if 'csv' in self.config.export.formats:
                csv_path = output_dir / f"whatsapp_messages_{timestamp}.csv"
                csv_exporter = CSVExporter()
                if csv_exporter.export(export_data, csv_path):
                    export_paths['csv'] = str(csv_path)
            
            # Excel Export
            if 'excel' in self.config.export.formats:
                excel_path = output_dir / f"whatsapp_messages_{timestamp}.xlsx"
                excel_exporter = ExcelExporter()
                if excel_exporter.export(export_data, excel_path):
                    export_paths['excel'] = str(excel_path)
            
            # JSON Export
            if 'json' in self.config.export.formats:
                json_path = output_dir / f"whatsapp_messages_{timestamp}.json"
                json_exporter = JSONExporter()
                if json_exporter.export(export_data, json_path):
                    export_paths['json'] = str(json_path)
            
            # Contacts summary
            contacts_data = self._prepare_contacts_summary(filtered_data['contacts'])
            if contacts_data:
                contacts_path = output_dir / f"whatsapp_contacts_{timestamp}.json"
                json_exporter = JSONExporter()
                if json_exporter.export_contacts_summary(contacts_data, contacts_path):
                    export_paths['contacts'] = str(contacts_path)
            
            # Transcriptions export
            if filtered_data['transcriptions']:
                transcriptions_path = output_dir / f"whatsapp_transcriptions_{timestamp}.json"
                json_exporter = JSONExporter()
                if json_exporter.export_transcriptions(filtered_data['transcriptions'], transcriptions_path):
                    export_paths['transcriptions'] = str(transcriptions_path)
            
            logger.info(f"Generated {len(export_paths)} export files")
            return export_paths
            
        except Exception as e:
            logger.error(f"Export generation failed: {e}")
            return export_paths
    
    def _prepare_export_data(self, filtered_data: Dict[str, List]) -> List[Dict[str, Any]]:
        """Prepare data for export formats"""
        export_data = []
        
        # Create transcription lookup
        transcription_lookup = {}
        for trans in filtered_data.get('transcriptions', []):
            transcription_lookup[trans['file_path']] = trans['transcription']
        
        for message in filtered_data.get('messages', []):
            row = {
                'contact_name': getattr(message, 'contact_name', ''),
                'message_id': getattr(message, 'id', ''),
                'timestamp': getattr(message, 'timestamp', '').isoformat() if hasattr(getattr(message, 'timestamp', ''), 'isoformat') else str(getattr(message, 'timestamp', '')),
                'direction': getattr(message, 'direction', '').value if hasattr(getattr(message, 'direction', ''), 'value') else str(getattr(message, 'direction', '')),
                'message_type': getattr(message, 'media_type', '').value if hasattr(getattr(message, 'media_type', ''), 'value') else str(getattr(message, 'media_type', '')),
                'content': getattr(message, 'content', ''),
                'transcription': transcription_lookup.get(str(getattr(message, 'media_path', '')), ''),
                'media_path': str(getattr(message, 'media_path', '')) if getattr(message, 'media_path', None) else '',
                'media_type': getattr(message, 'media_type', '').value if hasattr(getattr(message, 'media_type', ''), 'value') else '',
                'file_size': getattr(message, 'file_size', 0)
            }
            export_data.append(row)
        
        return export_data
    
    def _prepare_contacts_summary(self, contacts: List) -> List[Dict[str, Any]]:
        """Prepare contacts summary data"""
        contacts_data = []
        
        for contact in contacts:
            summary = {
                'contact_name': getattr(contact, 'display_name', ''),
                'phone_number': getattr(contact, 'phone_number', ''),
                'total_messages': getattr(contact, 'message_count', 0),
                'sent_messages': getattr(contact, 'sent_count', 0),
                'received_messages': getattr(contact, 'received_count', 0),
                'first_message_date': getattr(contact, 'first_message_date', '').isoformat() if hasattr(getattr(contact, 'first_message_date', ''), 'isoformat') else str(getattr(contact, 'first_message_date', '')),
                'last_message_date': getattr(contact, 'last_message_date', '').isoformat() if hasattr(getattr(contact, 'last_message_date', ''), 'isoformat') else str(getattr(contact, 'last_message_date', '')),
                'media_count': getattr(contact, 'media_count', {})
            }
            contacts_data.append(summary)
        
        return contacts_data
    
    def _calculate_stats(self) -> Dict[str, Any]:
        """Calculate processing statistics"""
        stats = {
            'total_contacts': len(self.results['contacts']),
            'total_messages': len(self.results['messages']),
            'total_transcriptions': len(self.results['transcriptions']),
            'total_media_files': sum(len(files) for files in self.results['media_files'].values()),
            'processing_time': datetime.now().isoformat(),
            'database_stats': self.database.get_stats() if self.database else {}
        }
        
        # Add media processor stats if available
        if self.media_processor:
            stats['media_stats'] = self.media_processor.get_stats()
        
        return stats
    
    def _get_cancelled_result(self) -> Dict[str, Any]:
        """Get result when processing is cancelled"""
        return {
            'status': 'cancelled',
            'message': 'Processing was cancelled by user',
            'partial_results': self.results
        }
    
    def get_current_progress(self) -> tuple:
        """Get current processing progress"""
        return self._current_task, self._progress
    
    def test_configuration(self) -> Dict[str, bool]:
        """Test if configuration is valid and all components can be initialized"""
        test_results = {
            'config_valid': False,
            'database_accessible': False,
            'source_path_exists': False,
            'output_dir_writable': False,
            'api_key_valid': False,
            'ffmpeg_available': False
        }
        
        try:
            # Test config
            test_results['config_valid'] = self.config is not None
            
            # Test database
            if self.database:
                try:
                    stats = self.database.get_stats()
                    test_results['database_accessible'] = True
                except:
                    test_results['database_accessible'] = False
            
            # Test source path
            if hasattr(self.config.paths, 'whatsapp_export_path'):
                source_path = self.config.paths.whatsapp_export_path
                test_results['source_path_exists'] = source_path.exists()
            
            # Test output directory
            output_dir = self.config.paths.export_output_dir
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                test_file = output_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                test_results['output_dir_writable'] = True
            except:
                test_results['output_dir_writable'] = False
            
            # Test API key
            if self.config.transcription.api_key:
                # TODO: Add actual API test
                test_results['api_key_valid'] = len(self.config.transcription.api_key) > 20
            
            # Test FFmpeg
            import subprocess
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                test_results['ffmpeg_available'] = True
            except:
                test_results['ffmpeg_available'] = False
                
        except Exception as e:
            logger.error(f"Configuration test failed: {e}")
        
        return test_results