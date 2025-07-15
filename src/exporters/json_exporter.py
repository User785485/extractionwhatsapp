"""JSON Exporter for WhatsApp Extractor v2"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export WhatsApp data to JSON format"""
    
    def __init__(self):
        pass
    
    def export(self, data: List[Dict[str, Any]], output_path: Path,
               pretty: bool = True) -> bool:
        """
        Export data to JSON file
        
        Args:
            data: List of message dictionaries
            output_path: Path where to save JSON file
            pretty: Whether to format JSON for readability
            
        Returns:
            bool: True if export successful
        """
        try:
            if not data:
                logger.warning("No data to export")
                return False
                
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare JSON structure
            json_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_messages': len(data),
                    'version': '2.0',
                    'source': 'WhatsApp Extractor v2'
                },
                'messages': data
            }
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                if pretty:
                    json.dump(json_data, jsonfile, ensure_ascii=False, indent=2)
                else:
                    json.dump(json_data, jsonfile, ensure_ascii=False)
                    
            logger.info(f"JSON export successful: {output_path} ({len(data)} messages)")
            return True
            
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            return False
            
    def export_contacts_summary(self, contacts: List[Dict[str, Any]], 
                               output_path: Path) -> bool:
        """Export contacts summary to JSON"""
        try:
            # Calculate summary statistics
            total_contacts = len(contacts)
            total_messages = sum(contact.get('total_messages', 0) for contact in contacts)
            
            summary_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_contacts': total_contacts,
                    'total_messages': total_messages,
                    'version': '2.0'
                },
                'summary': {
                    'contacts_count': total_contacts,
                    'messages_count': total_messages,
                    'avg_messages_per_contact': total_messages / total_contacts if total_contacts > 0 else 0
                },
                'contacts': contacts
            }
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(summary_data, jsonfile, ensure_ascii=False, indent=2)
                
            logger.info(f"Contacts JSON export successful: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Contacts JSON export failed: {e}")
            return False
            
    def export_transcriptions(self, transcriptions: List[Dict[str, Any]], 
                             output_path: Path) -> bool:
        """Export transcriptions to JSON"""
        try:
            # Calculate transcription statistics
            total_transcriptions = len(transcriptions)
            successful_transcriptions = len([t for t in transcriptions if t.get('transcription')])
            
            transcription_data = {
                'metadata': {
                    'export_date': datetime.now().isoformat(),
                    'total_audio_files': total_transcriptions,
                    'successful_transcriptions': successful_transcriptions,
                    'success_rate': successful_transcriptions / total_transcriptions if total_transcriptions > 0 else 0,
                    'version': '2.0'
                },
                'transcriptions': transcriptions
            }
            
            with open(output_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(transcription_data, jsonfile, ensure_ascii=False, indent=2)
                
            logger.info(f"Transcriptions JSON export successful: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Transcriptions JSON export failed: {e}")
            return False
            
    def load_json(self, input_path: Path) -> Optional[Dict[str, Any]]:
        """Load JSON data from file"""
        try:
            with open(input_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
                
            logger.info(f"JSON loaded successfully: {input_path}")
            return data
            
        except Exception as e:
            logger.error(f"JSON load failed: {e}")
            return None
            
    def validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """Validate JSON structure"""
        try:
            # Check required fields
            required_fields = ['metadata', 'messages']
            
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return False
                    
            # Check metadata structure
            metadata = data['metadata']
            required_metadata = ['export_date', 'total_messages', 'version']
            
            for field in required_metadata:
                if field not in metadata:
                    logger.error(f"Missing metadata field: {field}")
                    return False
                    
            # Check messages structure
            messages = data['messages']
            if not isinstance(messages, list):
                logger.error("Messages must be a list")
                return False
                
            logger.info("JSON structure validation successful")
            return True
            
        except Exception as e:
            logger.error(f"JSON validation failed: {e}")
            return False