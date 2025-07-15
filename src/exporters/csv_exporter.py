"""CSV Exporter for WhatsApp Extractor v2"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """Export WhatsApp data to CSV format"""
    
    def __init__(self):
        self.default_fields = [
            'contact_name',
            'message_id', 
            'timestamp',
            'direction',
            'message_type',
            'content',
            'transcription',
            'media_path',
            'media_type',
            'file_size'
        ]
    
    def export(self, data: List[Dict[str, Any]], output_path: Path, 
               fields: Optional[List[str]] = None) -> bool:
        """
        Export data to CSV file
        
        Args:
            data: List of message dictionaries
            output_path: Path where to save CSV file
            fields: List of field names to include (default: all fields)
            
        Returns:
            bool: True if export successful
        """
        try:
            if not data:
                logger.warning("No data to export")
                return False
                
            # Use default fields if none specified
            if fields is None:
                fields = self.default_fields
                
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write CSV file
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                for row in data:
                    # Ensure all required fields exist
                    cleaned_row = {}
                    for field in fields:
                        value = row.get(field, '')
                        
                        # Handle special data types
                        if isinstance(value, dict) or isinstance(value, list):
                            value = json.dumps(value, ensure_ascii=False)
                        elif value is None:
                            value = ''
                        else:
                            value = str(value)
                            
                        cleaned_row[field] = value
                        
                    writer.writerow(cleaned_row)
                    
            logger.info(f"CSV export successful: {output_path} ({len(data)} rows)")
            return True
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return False
            
    def export_contacts(self, contacts: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export contacts summary to CSV"""
        try:
            contact_fields = [
                'contact_name',
                'phone_number', 
                'total_messages',
                'sent_messages',
                'received_messages',
                'audio_messages',
                'first_message_date',
                'last_message_date'
            ]
            
            return self.export(contacts, output_path, contact_fields)
            
        except Exception as e:
            logger.error(f"Contacts CSV export failed: {e}")
            return False
            
    def export_transcriptions(self, transcriptions: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export transcriptions to CSV"""
        try:
            transcription_fields = [
                'contact_name',
                'audio_file',
                'timestamp',
                'direction',
                'transcription',
                'confidence',
                'language',
                'duration'
            ]
            
            return self.export(transcriptions, output_path, transcription_fields)
            
        except Exception as e:
            logger.error(f"Transcriptions CSV export failed: {e}")
            return False
            
    def get_sample_data(self) -> List[Dict[str, Any]]:
        """Generate sample data for testing"""
        return [
            {
                'contact_name': 'John Doe',
                'message_id': '1',
                'timestamp': '2024-01-01 12:00:00',
                'direction': 'received',
                'message_type': 'text',
                'content': 'Hello, how are you?',
                'transcription': '',
                'media_path': '',
                'media_type': '',
                'file_size': '0'
            },
            {
                'contact_name': 'John Doe', 
                'message_id': '2',
                'timestamp': '2024-01-01 12:01:00',
                'direction': 'sent',
                'message_type': 'text',
                'content': 'I am fine, thanks!',
                'transcription': '',
                'media_path': '',
                'media_type': '',
                'file_size': '0'
            },
            {
                'contact_name': 'John Doe',
                'message_id': '3', 
                'timestamp': '2024-01-01 12:02:00',
                'direction': 'received',
                'message_type': 'audio',
                'content': '[Audio Message]',
                'transcription': 'Hey, can you call me later?',
                'media_path': 'audio/john_doe_001.opus',
                'media_type': 'audio/opus',
                'file_size': '1024'
            }
        ]