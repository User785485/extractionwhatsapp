"""Configuration schemas using Pydantic for validation"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import os


class PathConfig(BaseModel):
    """Paths configuration"""
    whatsapp_export_path: Path = Field(
        ..., 
        description="Path to WhatsApp HTML export files"
    )
    media_output_dir: Path = Field(
        default=Path("./output/media"),
        description="Directory for organized media files"
    )
    export_output_dir: Path = Field(
        default=Path("./output/exports"),
        description="Directory for export files"
    )
    transcription_cache_dir: Path = Field(
        default=Path("./output/transcriptions"),
        description="Directory for transcription cache"
    )
    database_path: Path = Field(
        default=Path("./whatsapp_extractor.db"),
        description="SQLite database path"
    )
    
    @validator('*', pre=True)
    def expand_paths(cls, v):
        if isinstance(v, str):
            return Path(os.path.expanduser(v))
        return v
    
    @validator('*')
    def create_directories(cls, v):
        if isinstance(v, Path) and not v.name.endswith('.db'):
            v.mkdir(parents=True, exist_ok=True)
        return v


class TranscriptionConfig(BaseModel):
    """Transcription configuration"""
    api_key: str = Field(
        default="",
        description="OpenAI API key for Whisper",
        env='OPENAI_API_KEY'
    )
    model: str = Field(
        default="whisper-1",
        description="Whisper model to use"
    )
    transcribe_sent: bool = Field(
        default=True,
        description="Transcribe sent audio messages"
    )
    transcribe_received: bool = Field(
        default=True,
        description="Transcribe received audio messages"
    )
    batch_size: int = Field(
        default=10,
        min=1,
        max=50,
        description="Number of files to process in parallel"
    )
    max_retries: int = Field(
        default=3,
        min=0,
        max=10,
        description="Maximum retry attempts for failed transcriptions"
    )
    timeout: int = Field(
        default=300,
        min=30,
        max=3600,
        description="Timeout in seconds for transcription requests"
    )
    language: Optional[str] = Field(
        default=None,
        description="Language code (e.g., 'fr', 'en') or None for auto-detection"
    )
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v and not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key must be provided in config or OPENAI_API_KEY environment variable")
        return v or os.getenv('OPENAI_API_KEY', '')


class FilterConfig(BaseModel):
    """Filtering configuration"""
    min_messages: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum number of messages per contact"
    )
    after_date: Optional[datetime] = Field(
        default=None,
        description="Process messages after this date"
    )
    before_date: Optional[datetime] = Field(
        default=None,
        description="Process messages before this date"
    )
    contact_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns to filter contacts"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list,
        description="Regex patterns to exclude contacts"
    )
    content_types: List[str] = Field(
        default_factory=lambda: ["text", "audio", "video", "image", "document"],
        description="Content types to include"
    )
    
    @validator('after_date', 'before_date', pre=True)
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return datetime.strptime(v, "%Y-%m-%d")
        return v


class ExportConfig(BaseModel):
    """Export configuration"""
    formats: List[str] = Field(
        default_factory=lambda: ["csv", "excel"],
        description="Export formats to generate"
    )
    include_media_links: bool = Field(
        default=True,
        description="Include media file paths in exports"
    )
    anonymize_data: bool = Field(
        default=False,
        description="Anonymize personal data in exports"
    )
    max_message_length: Optional[int] = Field(
        default=None,
        ge=10,
        description="Maximum message length (truncate if longer)"
    )
    separate_by_contact: bool = Field(
        default=False,
        description="Create separate export files per contact"
    )
    include_stats: bool = Field(
        default=True,
        description="Include statistics in exports"
    )
    
    @validator('formats')
    def validate_formats(cls, v):
        valid_formats = ['csv', 'excel', 'json', 'html', 'txt']
        invalid = [fmt for fmt in v if fmt not in valid_formats]
        if invalid:
            raise ValueError(f"Invalid export formats: {invalid}. Valid formats: {valid_formats}")
        return v


class ProcessingConfig(BaseModel):
    """Processing configuration"""
    parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing"
    )
    max_workers: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of parallel workers"
    )
    resume_on_error: bool = Field(
        default=True,
        description="Resume processing from last checkpoint on error"
    )
    verbose: bool = Field(
        default=True,
        description="Enable verbose output"
    )
    dry_run: bool = Field(
        default=False,
        description="Run without making changes"
    )


class AppConfig(BaseModel):
    """Main application configuration"""
    paths: PathConfig
    transcription: TranscriptionConfig = Field(default_factory=TranscriptionConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'