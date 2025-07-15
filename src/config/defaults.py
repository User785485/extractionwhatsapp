"""Default configuration values"""

from pathlib import Path

DEFAULT_CONFIG = {
    "paths": {
        "whatsapp_export_path": "./whatsapp_export",
        "media_output_dir": "./output/media",
        "export_output_dir": "./output/exports",
        "transcription_cache_dir": "./output/transcriptions",
        "database_path": "./whatsapp_extractor.db"
    },
    "transcription": {
        "model": "whisper-1",
        "transcribe_sent": True,
        "transcribe_received": True,
        "batch_size": 10,
        "max_retries": 3,
        "timeout": 300,
        "language": None
    },
    "filters": {
        "min_messages": None,
        "after_date": None,
        "before_date": None,
        "contact_patterns": [],
        "exclude_patterns": [],
        "content_types": ["text", "audio", "video", "image", "document"]
    },
    "export": {
        "formats": ["csv", "excel"],
        "include_media_links": True,
        "anonymize_data": False,
        "max_message_length": None,
        "separate_by_contact": False,
        "include_stats": True
    },
    "processing": {
        "parallel_processing": True,
        "max_workers": None,
        "resume_on_error": True,
        "verbose": True,
        "dry_run": False
    }
}

# Legacy config mapping for backward compatibility
LEGACY_CONFIG_MAPPING = {
    # Old INI sections to new config structure
    "Paths": "paths",
    "PATHS": "paths",
    "paths": "paths",
    "Transcription": "transcription",
    "TRANSCRIPTION": "transcription",
    "transcription": "transcription",
    "Export": "export",
    "EXPORT": "export",
    "export": "export",
    
    # Old field names to new field names
    "whatsapp_export_folder": "whatsapp_export_path",
    "WHATSAPP_EXPORT_PATH": "whatsapp_export_path",
    "media_organized_folder": "media_output_dir",
    "MEDIA_ORGANIZED_FOLDER": "media_output_dir",
    "transcriptions_folder": "transcription_cache_dir",
    "TRANSCRIPTIONS_FOLDER": "transcription_cache_dir",
    "export_folder": "export_output_dir",
    "EXPORT_FOLDER": "export_output_dir",
    "openai_api_key": "api_key",
    "OPENAI_API_KEY": "api_key"
}