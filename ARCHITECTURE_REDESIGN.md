# WhatsApp Extractor v2 - Architecture Redesign

## Overview

This document outlines the complete architectural redesign of WhatsApp Extractor v2 to create a professional, robust, and scalable application.

## Core Design Principles

1. **Modularity**: Clear separation of concerns with well-defined interfaces
2. **Testability**: All components must be unit testable
3. **Performance**: Parallel processing where applicable
4. **Reliability**: Comprehensive error handling and recovery
5. **Extensibility**: Easy to add new features and formats
6. **User Experience**: Clear feedback and progress tracking

## New Architecture

### 1. Project Structure

```
whatsapp_extractor_v2/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point with Click CLI
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_manager.py      # Unified configuration management
│   │   ├── schemas.py             # Pydantic models for validation
│   │   └── defaults.py            # Default configurations
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py              # Data models (Contact, Message, etc.)
│   │   ├── database.py            # SQLite cache management
│   │   ├── state_manager.py       # Application state management
│   │   └── exceptions.py          # Custom exceptions
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py         # Abstract parser interface
│   │   ├── html_parser.py         # WhatsApp HTML parser
│   │   └── message_classifier.py  # Message direction detection
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── media_processor.py     # Media file organization
│   │   ├── audio_converter.py     # Audio format conversion
│   │   └── transcription/
│   │       ├── __init__.py
│   │       ├── base_transcriber.py    # Abstract transcriber
│   │       ├── whisper_transcriber.py  # OpenAI Whisper implementation
│   │       └── batch_processor.py      # Parallel batch processing
│   ├── filters/
│   │   ├── __init__.py
│   │   ├── date_filter.py         # Date-based filtering
│   │   ├── contact_filter.py      # Contact-based filtering
│   │   ├── content_filter.py      # Content type filtering
│   │   └── composite_filter.py    # Combine multiple filters
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── base_exporter.py       # Abstract exporter interface
│   │   ├── csv_exporter.py        # CSV export
│   │   ├── excel_exporter.py      # Excel export with formatting
│   │   ├── json_exporter.py       # JSON export
│   │   ├── html_exporter.py       # HTML report generation
│   │   └── export_manager.py      # Manages export pipeline
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_utils.py          # File operations
│   │   ├── text_utils.py          # Text processing
│   │   ├── progress.py            # Progress tracking
│   │   └── logging_config.py      # Centralized logging
│   └── cli/
│       ├── __init__.py
│       ├── commands.py            # CLI command definitions
│       └── interactive.py         # Interactive mode
├── tests/
│   ├── __init__.py
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── fixtures/                  # Test data
│   └── conftest.py               # Pytest configuration
├── scripts/
│   ├── install.py                 # Installation script
│   ├── setup_ffmpeg.py           # FFmpeg setup
│   └── migrate_data.py           # Data migration
├── docs/
│   ├── API.md                    # API documentation
│   ├── USER_GUIDE.md             # User guide
│   └── DEVELOPMENT.md            # Development guide
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI/CD
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── README.md
└── LICENSE
```

### 2. Core Components

#### 2.1 Configuration Management

```python
# config/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path

class PathConfig(BaseModel):
    whatsapp_export_path: Path
    media_output_dir: Path
    export_output_dir: Path
    transcription_cache_dir: Path
    
class TranscriptionConfig(BaseModel):
    api_key: str = Field(..., env='OPENAI_API_KEY')
    model: str = "whisper-1"
    transcribe_sent: bool = True
    transcribe_received: bool = True
    batch_size: int = 10
    max_retries: int = 3
    timeout: int = 300
    
class FilterConfig(BaseModel):
    min_messages: Optional[int] = None
    after_date: Optional[str] = None
    contact_patterns: List[str] = []
    content_types: List[str] = ["text", "audio", "video", "image"]
    
class ExportConfig(BaseModel):
    formats: List[str] = ["csv", "excel"]
    include_media_links: bool = True
    anonymize_data: bool = False
    max_message_length: Optional[int] = None
```

#### 2.2 Database Schema

```python
# core/database.py
import sqlite3
from contextlib import contextmanager
from typing import List, Optional
import json

class CacheDatabase:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY,
                    phone_number TEXT UNIQUE,
                    display_name TEXT,
                    last_message_date TEXT,
                    message_count INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    contact_id INTEGER,
                    message_hash TEXT UNIQUE,
                    direction TEXT,
                    content TEXT,
                    media_path TEXT,
                    timestamp TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (contact_id) REFERENCES contacts(id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY,
                    message_id INTEGER,
                    file_path TEXT,
                    transcription TEXT,
                    language TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (message_id) REFERENCES messages(id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processing_state (
                    id INTEGER PRIMARY KEY,
                    task_name TEXT UNIQUE,
                    state TEXT,
                    metadata TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
```

#### 2.3 Data Models

```python
# core/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class MessageDirection(Enum):
    SENT = "sent"
    RECEIVED = "received"
    SYSTEM = "system"

class MediaType(Enum):
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"
    DOCUMENT = "document"

@dataclass
class Contact:
    phone_number: str
    display_name: str
    message_count: int = 0
    last_message_date: Optional[datetime] = None
    
@dataclass
class Message:
    contact: Contact
    direction: MessageDirection
    content: str
    timestamp: datetime
    media_type: MediaType = MediaType.TEXT
    media_path: Optional[str] = None
    transcription: Optional[str] = None
    
@dataclass
class ProcessingStats:
    total_contacts: int = 0
    processed_contacts: int = 0
    total_messages: int = 0
    processed_messages: int = 0
    transcribed_files: int = 0
    failed_transcriptions: int = 0
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None
```

### 3. Key Features Implementation

#### 3.1 Parallel Processing

```python
# processors/transcription/batch_processor.py
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import multiprocessing

class BatchTranscriptionProcessor:
    def __init__(self, transcriber, max_workers=None):
        self.transcriber = transcriber
        self.max_workers = max_workers or multiprocessing.cpu_count()
        
    async def process_batch(self, audio_files: List[Path], 
                          progress_callback=None) -> Dict[str, str]:
        """Process multiple audio files in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._process_single, file): file 
                for file in audio_files
            }
            
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    transcription = future.result()
                    results[str(file)] = transcription
                    if progress_callback:
                        progress_callback(len(results), len(audio_files))
                except Exception as e:
                    logger.error(f"Failed to transcribe {file}: {e}")
                    results[str(file)] = None
                    
        return results
```

#### 3.2 Advanced Filtering

```python
# filters/composite_filter.py
from typing import List, Callable
from abc import ABC, abstractmethod

class MessageFilter(ABC):
    @abstractmethod
    def apply(self, message: Message) -> bool:
        pass

class CompositeFilter(MessageFilter):
    def __init__(self, filters: List[MessageFilter], mode='AND'):
        self.filters = filters
        self.mode = mode
        
    def apply(self, message: Message) -> bool:
        if self.mode == 'AND':
            return all(f.apply(message) for f in self.filters)
        else:  # OR mode
            return any(f.apply(message) for f in self.filters)

class DateFilter(MessageFilter):
    def __init__(self, after_date: datetime):
        self.after_date = after_date
        
    def apply(self, message: Message) -> bool:
        return message.timestamp >= self.after_date

class ContactFilter(MessageFilter):
    def __init__(self, contact_patterns: List[str]):
        self.patterns = [re.compile(p) for p in contact_patterns]
        
    def apply(self, message: Message) -> bool:
        contact_str = f"{message.contact.phone_number} {message.contact.display_name}"
        return any(p.search(contact_str) for p in self.patterns)
```

#### 3.3 Progress Tracking

```python
# utils/progress.py
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from contextlib import contextmanager

class ProgressTracker:
    def __init__(self):
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
        
    @contextmanager
    def track_task(self, description: str, total: int):
        with self.progress:
            task_id = self.progress.add_task(description, total=total)
            
            def update(current: int, description: str = None):
                if description:
                    self.progress.update(task_id, description=description)
                self.progress.update(task_id, completed=current)
                
            yield update
```

### 4. CLI Implementation

```python
# cli/commands.py
import click
from pathlib import Path

@click.group()
@click.version_option()
def cli():
    """WhatsApp Extractor v2 - Professional WhatsApp data extraction tool"""
    pass

@cli.command()
@click.option('--config', type=click.Path(exists=True), help='Configuration file')
@click.option('--export-path', type=click.Path(exists=True), required=True)
@click.option('--output-dir', type=click.Path())
@click.option('--formats', multiple=True, default=['csv', 'excel'])
@click.option('--filter-date', type=str, help='Process messages after this date')
@click.option('--filter-contacts', multiple=True, help='Contact patterns to include')
@click.option('--parallel/--sequential', default=True)
@click.option('--resume/--restart', default=True)
def extract(config, export_path, output_dir, formats, filter_date, 
           filter_contacts, parallel, resume):
    """Extract and process WhatsApp data"""
    # Implementation
    pass

@cli.command()
def interactive():
    """Run in interactive mode"""
    # Implementation
    pass

@cli.command()
@click.option('--check-ffmpeg/--skip-ffmpeg', default=True)
@click.option('--install-deps/--skip-deps', default=True)
def setup(check_ffmpeg, install_deps):
    """Setup and verify installation"""
    # Implementation
    pass
```

### 5. Testing Strategy

```python
# tests/unit/test_transcriber.py
import pytest
from unittest.mock import Mock, patch
from src.processors.transcription import WhisperTranscriber

class TestWhisperTranscriber:
    @pytest.fixture
    def transcriber(self):
        return WhisperTranscriber(api_key="test-key")
    
    @patch('openai.Audio.transcribe')
    def test_successful_transcription(self, mock_transcribe, transcriber):
        mock_transcribe.return_value = Mock(text="Test transcription")
        
        result = transcriber.transcribe("test.mp3")
        
        assert result == "Test transcription"
        mock_transcribe.assert_called_once()
    
    def test_retry_on_failure(self, transcriber):
        # Test retry logic
        pass
```

### 6. Performance Optimizations

1. **Lazy Loading**: Load data on demand
2. **Streaming**: Process large files in chunks
3. **Caching**: Intelligent caching with TTL
4. **Connection Pooling**: Reuse database connections
5. **Memory Management**: Clear large objects after use

### 7. Error Handling Strategy

```python
# core/exceptions.py
class WhatsAppExtractorError(Exception):
    """Base exception for all extractor errors"""
    pass

class ConfigurationError(WhatsAppExtractorError):
    """Configuration related errors"""
    pass

class ParsingError(WhatsAppExtractorError):
    """HTML parsing errors"""
    pass

class TranscriptionError(WhatsAppExtractorError):
    """Transcription processing errors"""
    pass

class ExportError(WhatsAppExtractorError):
    """Export processing errors"""
    pass
```

### 8. Deployment and Distribution

1. **PyPI Package**: Distribute via pip
2. **Docker Image**: Containerized deployment
3. **Executable**: PyInstaller for standalone exe
4. **GitHub Releases**: Binary releases for all platforms

## Implementation Plan

### Phase 1: Core Refactoring (Week 1)
- [ ] Restructure project layout
- [ ] Implement configuration system
- [ ] Create data models and database
- [ ] Setup logging and error handling

### Phase 2: Processing Pipeline (Week 2)
- [ ] Refactor HTML parser
- [ ] Implement parallel processing
- [ ] Create filter system
- [ ] Optimize transcription

### Phase 3: Export and UI (Week 3)
- [ ] Unified export system
- [ ] CLI implementation
- [ ] Progress tracking
- [ ] Interactive mode

### Phase 4: Testing and Documentation (Week 4)
- [ ] Unit tests (80% coverage)
- [ ] Integration tests
- [ ] Performance tests
- [ ] Documentation

### Phase 5: Polish and Release (Week 5)
- [ ] Bug fixes
- [ ] Performance optimization
- [ ] Package for distribution
- [ ] CI/CD setup