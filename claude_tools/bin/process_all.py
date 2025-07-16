#!/usr/bin/env python3
"""
Unified CLI for Claude's WhatsApp processing pipeline
Chain all tools together for complete workflow
"""

import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logger import setup_logger, LogLevel, LogCategory

# Import our tools
import parse_received
import find_media
import convert_audio
import transcribe
import analyze

class WhatsAppProcessor:
    """Main processor orchestrating all tools"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize processor with optional API key"""
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.logger = setup_logger("whatsapp_processor")
        self.results = {}
        
    def process_contacts(self, input_paths: List[Path], output_dir: Path,
                        skip_transcription: bool = False,
                        contacts_filter: Optional[List[str]] = None) -> Dict:
        """Process WhatsApp contacts through complete pipeline"""
        
        self.logger.operation_start("WhatsApp Processing Pipeline", {
            'input_files': len(input_paths),
            'output_dir': str(output_dir),
            'skip_transcription': skip_transcription
        })
        
        start_time = time.time()
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Parse HTML files for received messages
        self.logger.info("Step 1: Parsing HTML files for received messages", LogCategory.PARSING)
        parsed_messages = self._parse_html_files(input_paths, contacts_filter)
        
        if not parsed_messages:
            self.logger.error("No messages found in HTML files")
            return {'error': 'No messages found'}
        
        # Save parsed messages
        parsed_file = output_dir / 'parsed_messages.json'
        with open(parsed_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_messages, f, ensure_ascii=False, indent=2)
        self.logger.success(f"Parsed {len(parsed_messages)} messages", LogCategory.PARSING)
        
        # Step 2: Find media files
        self.logger.info("Step 2: Finding media files", LogCategory.MEDIA)
        media_files = self._find_media_files(input_paths, parsed_messages)
        
        # Step 3: Convert audio files
        audio_files = [f for f in media_files if f['category'] == 'audio']
        
        if audio_files and not skip_transcription:
            self.logger.info(f"Step 3: Converting {len(audio_files)} audio files", LogCategory.CONVERSION)
            converted_files = self._convert_audio_files(audio_files, output_dir)
            
            # Step 4: Transcribe audio
            if converted_files and self.api_key:
                self.logger.info(f"Step 4: Transcribing {len(converted_files)} audio files", LogCategory.TRANSCRIPTION)
                transcriptions = self._transcribe_audio_files(converted_files, output_dir)
                
                # Merge transcriptions with messages
                parsed_messages = self._merge_transcriptions(parsed_messages, transcriptions)
        
        # Step 5: Analyze and generate reports
        self.logger.info("Step 5: Analyzing data and generating reports", LogCategory.ANALYSIS)
        analysis_results = self._analyze_and_report(parsed_messages, output_dir)
        
        # Final summary
        duration = time.time() - start_time
        
        summary = {
            'success': True,
            'duration': round(duration, 2),
            'input_files': len(input_paths),
            'messages_parsed': len(parsed_messages),
            'media_found': len(media_files),
            'audio_transcribed': len([m for m in parsed_messages if m.get('transcription')]),
            'output_dir': str(output_dir),
            'files_generated': {
                'parsed_messages': str(parsed_file),
                'analysis_report': str(output_dir / 'analysis_report.md'),
                'summary': str(output_dir / 'processing_summary.json')
            }
        }
        
        # Save summary
        with open(output_dir / 'processing_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.logger.operation_end("WhatsApp Processing Pipeline", True, duration, summary)
        self.logger.save_summary()
        
        return summary
    
    def _parse_html_files(self, input_paths: List[Path], 
                         contacts_filter: Optional[List[str]] = None) -> List[Dict]:
        """Parse HTML files"""
        
        parser = parse_received.ReceivedMessageParser()
        all_messages = []
        
        for path in input_paths:
            if path.is_file() and path.suffix.lower() == '.html':
                files = [path]
            elif path.is_dir():
                files = list(path.glob('*.html'))
            else:
                continue
            
            for file in files:
                self.logger.debug(f"Parsing: {file.name}", LogCategory.PARSING)
                
                result = parser.parse_file(file)
                
                if 'error' not in result:
                    # Filter contacts if specified
                    if contacts_filter:
                        if result['contact'] not in contacts_filter:
                            continue
                    
                    # Extract messages
                    for msg in result.get('messages', []):
                        msg['contact'] = result['contact']
                        msg['source_file'] = str(file)
                        all_messages.append(msg)
                    
                    self.logger.success(
                        f"Parsed {file.name}: {result['received_count']} messages",
                        LogCategory.PARSING
                    )
                else:
                    self.logger.error(f"Failed to parse {file.name}: {result['error']}", 
                                    LogCategory.PARSING)
        
        return all_messages
    
    def _find_media_files(self, input_paths: List[Path], messages: List[Dict]) -> List[Dict]:
        """Find associated media files"""
        
        all_media = []
        
        for path in input_paths:
            search_dir = path if path.is_dir() else path.parent
            
            # Look for Media folder
            media_dirs = [
                search_dir / 'Media',
                search_dir / 'media',
                search_dir / 'WhatsApp Media',
                search_dir
            ]
            
            for media_dir in media_dirs:
                if media_dir.exists():
                    self.logger.debug(f"Searching media in: {media_dir}", LogCategory.MEDIA)
                    
                    finder = find_media.MediaFinder(media_dir)
                    media_results = finder.find_all_media()
                    
                    # Flatten results
                    for category, files in media_results.items():
                        all_media.extend(files)
                    
                    if all_media:
                        self.logger.success(
                            f"Found {len(all_media)} media files in {media_dir}",
                            LogCategory.MEDIA
                        )
                        break
        
        # Try to map media to messages
        if all_media and messages:
            finder = find_media.MediaFinder(Path('.'))
            messages = finder.map_media_to_messages(messages)
            
            mapped = sum(1 for m in messages if m.get('media_found'))
            self.logger.info(f"Mapped {mapped} media files to messages", LogCategory.MEDIA)
        
        return all_media
    
    def _convert_audio_files(self, audio_files: List[Dict], output_dir: Path) -> List[Path]:
        """Convert audio files to MP3"""
        
        converter = convert_audio.AudioConverter(
            output_dir=output_dir / 'converted_audio',
            preset='whisper'
        )
        
        # Check FFmpeg
        ffmpeg_check = converter.check_ffmpeg()
        if not ffmpeg_check['installed']:
            self.logger.error(f"FFmpeg not found: {ffmpeg_check['error']}", LogCategory.CONVERSION)
            return []
        
        # Convert files
        audio_paths = [Path(f['path']) for f in audio_files if Path(f['path']).exists()]
        
        results = converter.convert_batch(audio_paths, max_workers=4)
        
        converted = []
        for result in results:
            if result['success']:
                converted.append(Path(result['output']))
                self.logger.success(
                    f"Converted: {Path(result['input']).name}",
                    LogCategory.CONVERSION
                )
            else:
                self.logger.error(
                    f"Failed to convert {Path(result['input']).name}: {result['error']}",
                    LogCategory.CONVERSION
                )
        
        return converted
    
    def _transcribe_audio_files(self, audio_files: List[Path], output_dir: Path) -> List[Dict]:
        """Transcribe audio files"""
        
        if not self.api_key:
            self.logger.warning("No OpenAI API key, skipping transcription", LogCategory.TRANSCRIPTION)
            return []
        
        transcriber = transcribe.WhisperTranscriber(
            api_key=self.api_key,
            cache_dir=output_dir / 'transcription_cache'
        )
        
        results = transcriber.transcribe_batch(audio_files, max_workers=3)
        
        transcriptions = []
        for result in results:
            if result['success']:
                transcriptions.append({
                    'file': result['file'],
                    'transcription': result['transcription'],
                    'language': result.get('language'),
                    'cached': result.get('from_cache', False)
                })
                
                self.logger.success(
                    f"Transcribed: {Path(result['file']).name}" + 
                    (" (cached)" if result.get('from_cache') else ""),
                    LogCategory.TRANSCRIPTION
                )
            else:
                self.logger.error(
                    f"Failed to transcribe {Path(result['file']).name}: {result['error']}",
                    LogCategory.TRANSCRIPTION
                )
        
        # Save transcriptions
        trans_file = output_dir / 'transcriptions.json'
        with open(trans_file, 'w', encoding='utf-8') as f:
            json.dump(transcriptions, f, ensure_ascii=False, indent=2)
        
        return transcriptions
    
    def _merge_transcriptions(self, messages: List[Dict], 
                            transcriptions: List[Dict]) -> List[Dict]:
        """Merge transcriptions with messages"""
        
        # Create transcription index
        trans_index = {}
        for trans in transcriptions:
            file_name = Path(trans['file']).stem
            trans_index[file_name] = trans['transcription']
        
        # Merge with messages
        merged_count = 0
        for msg in messages:
            if msg.get('media_file'):
                file_stem = Path(msg['media_file']['path']).stem
                if file_stem in trans_index:
                    msg['transcription'] = trans_index[file_stem]
                    msg['transcribed'] = True
                    merged_count += 1
        
        self.logger.info(f"Merged {merged_count} transcriptions with messages", LogCategory.TRANSCRIPTION)
        
        return messages
    
    def _analyze_and_report(self, messages: List[Dict], output_dir: Path) -> Dict:
        """Analyze data and generate reports"""
        
        analyzer = analyze.WhatsAppAnalyzer()
        
        # Generate analysis
        analysis = analyzer.analyze_messages(messages)
        
        # Save analysis JSON
        with open(output_dir / 'analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        # Generate reports in multiple formats
        reports = {
            'markdown': output_dir / 'analysis_report.md',
            'csv': output_dir / 'messages.csv',
            'text': output_dir / 'summary.txt'
        }
        
        for format_type, output_path in reports.items():
            report = analyzer.generate_report(messages, format_type, output_path)
            self.logger.success(f"Generated {format_type} report: {output_path.name}", 
                              LogCategory.ANALYSIS)
        
        return analysis

def main():
    """CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description='Process WhatsApp data through complete pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Complete WhatsApp Processing Pipeline:
1. Parse HTML files for received messages only
2. Find and map media files
3. Convert audio files to MP3
4. Transcribe audio with Whisper API
5. Analyze data and generate reports

Examples:
  # Process single contact
  python process_all.py "/path/to/+1 234 567 8900.html"
  
  # Process entire WhatsApp folder
  python process_all.py /path/to/WhatsApp/
  
  # Filter specific contacts
  python process_all.py /path/to/WhatsApp/ --contacts "+1 234 567 8900,John Doe"
  
  # Skip transcription (no API key needed)
  python process_all.py /path/to/WhatsApp/ --skip-transcription
  
  # Custom output directory
  python process_all.py /path/to/WhatsApp/ -o my_analysis/
        """
    )
    
    parser.add_argument('input', nargs='+', help='Input HTML files or directories')
    parser.add_argument('-o', '--output', default='whatsapp_output', 
                       help='Output directory (default: whatsapp_output)')
    parser.add_argument('--contacts', help='Filter specific contacts (comma-separated)')
    parser.add_argument('--skip-transcription', action='store_true',
                       help='Skip audio transcription')
    parser.add_argument('--api-key', help='OpenAI API key for transcription')
    
    args = parser.parse_args()
    
    # Setup
    print("=== WHATSAPP PROCESSING PIPELINE ===")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Collect input paths
    input_paths = []
    for input_item in args.input:
        path = Path(input_item)
        if path.exists():
            input_paths.append(path)
        else:
            print(f"Warning: Path not found: {input_item}")
    
    if not input_paths:
        print("Error: No valid input paths found!")
        return 1
    
    # Parse contacts filter
    contacts_filter = None
    if args.contacts:
        contacts_filter = [c.strip() for c in args.contacts.split(',')]
    
    # Create processor
    processor = WhatsAppProcessor(api_key=args.api_key)
    
    # Process
    try:
        results = processor.process_contacts(
            input_paths=input_paths,
            output_dir=Path(args.output),
            skip_transcription=args.skip_transcription,
            contacts_filter=contacts_filter
        )
        
        if results.get('success'):
            print(f"\n=== PROCESSING COMPLETE ===")
            print(f"Duration: {results['duration']} seconds")
            print(f"Messages parsed: {results['messages_parsed']}")
            print(f"Media found: {results['media_found']}")
            print(f"Audio transcribed: {results['audio_transcribed']}")
            print(f"\nOutput directory: {results['output_dir']}")
            print(f"\nGenerated files:")
            for name, path in results['files_generated'].items():
                print(f"  - {name}: {Path(path).name}")
            
            return 0
        else:
            print(f"\nProcessing failed: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"\nCritical error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())