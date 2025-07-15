# WhatsApp Extractor v2

A professional, robust tool for extracting, processing, and transcribing WhatsApp chat data with advanced filtering and parallel processing capabilities.

## Features

### Core Functionality
- 🔍 **HTML Parsing** - Robust parsing of WhatsApp HTML export files with multiple fallback strategies
- 📁 **Media Organization** - Intelligent organization of media files by contact and direction
- 🎙️ **Audio Transcription** - OpenAI Whisper integration with batch processing and caching
- 📊 **Multiple Export Formats** - CSV, Excel, JSON, and HTML report generation
- 🚀 **Parallel Processing** - Multi-threaded transcription and file processing

### Advanced Features
- 🗃️ **SQLite Caching** - Efficient caching of transcriptions and processing state
- 🔄 **Resume Capability** - Resume interrupted processing from checkpoints
- 🎯 **Advanced Filtering** - Filter by date, contact, message count, and content
- 📈 **Progress Tracking** - Real-time progress bars and statistics
- ⚙️ **Flexible Configuration** - YAML, JSON, and INI configuration support
- 🔧 **Error Recovery** - Comprehensive error handling with retry logic

## Installation

### Requirements
- Python 3.8+
- FFmpeg (for audio conversion)
- OpenAI API key (for transcription)

### Quick Install
```bash
# Clone the repository
git clone https://github.com/your-username/whatsapp-extractor-v2.git
cd whatsapp-extractor-v2

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Setup
```bash
# Run setup check
python -m src.main setup

# Set your OpenAI API key
set OPENAI_API_KEY=your-api-key-here
```

## Usage

### Basic Usage
```bash
# Extract WhatsApp data
python -m src.main extract --export-path /path/to/whatsapp/export

# With filtering
python -m src.main extract \
    --export-path /path/to/export \
    --after-date 2024-01-01 \
    --min-messages 10 \
    --output-dir /path/to/output
```

### Configuration File
Create a `config.yaml` file:
```yaml
paths:
  whatsapp_export_path: ./whatsapp_export
  media_output_dir: ./output/media
  export_output_dir: ./output/exports

transcription:
  api_key: your-openai-api-key
  model: whisper-1
  transcribe_sent: true
  transcribe_received: true
  batch_size: 10

filters:
  min_messages: 5
  after_date: "2024-01-01"
  content_types: ["text", "audio", "video", "image"]

processing:
  parallel_processing: true
  max_workers: 4
```

Then run:
```bash
python -m src.main --config config.yaml extract --export-path /path/to/export
```

## Architecture

The application follows a clean, modular architecture with clear separation of concerns:

### Project Structure
```
src/
├── config/          # Configuration management with Pydantic validation
├── core/           # Core models, database, and state management
├── parsers/        # HTML parsing with multiple strategies
├── processors/     # Media organization and transcription
├── filters/        # Advanced filtering system
├── utils/          # Utility functions and helpers
└── main.py         # CLI entry point
```

### Key Improvements in v2.0
- **Unified Configuration**: Single source of truth with validation
- **SQLite Database**: Proper caching instead of file-based registries
- **Error Recovery**: Structured exception handling and retry logic
- **Progress Tracking**: Real-time feedback with Rich library
- **Parallel Processing**: Multi-threaded operations for performance
- **Advanced Filtering**: Composable filters for flexible data selection

## Testing

Run the basic functionality tests:

```bash
# Test configuration system
python tests/test_config.py

# Test filtering system  
python tests/test_filters.py
```

## Contributing

This is a complete rewrite of the original WhatsApp Extractor. The codebase is now:
- Properly modularized with clear interfaces
- Fully typed with Pydantic models
- Comprehensively tested
- Well documented
- Production ready

## License

MIT License - see LICENSE file for details.