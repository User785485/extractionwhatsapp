"""Main entry point for WhatsApp Extractor v2"""

import sys
import logging
from pathlib import Path
from typing import Optional
import click
from datetime import datetime

from .config import ConfigManager
from .core import CacheDatabase, StateManager
from .parsers import WhatsAppHTMLParser
from .processors import MediaProcessor, AudioConverter
from .processors.transcription import WhisperTranscriber, BatchTranscriptionProcessor
from .filters import DateFilter, ContactFilter, MessageCountFilter, CompositeFilter, FilterMode
from .utils import setup_logging, ProgressTracker


@click.group()
@click.version_option(version="2.0.0")
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """WhatsApp Extractor v2 - Professional WhatsApp data extraction tool"""
    ctx.ensure_object(dict)
    
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level=log_level, console_level=log_level)
    
    # Load configuration
    config_manager = ConfigManager(config)
    ctx.obj['config'] = config_manager.load()
    ctx.obj['config_manager'] = config_manager


@cli.command()
@click.option('--export-path', type=click.Path(exists=True), required=True,
              help='Path to WhatsApp HTML export files')
@click.option('--output-dir', type=click.Path(), 
              help='Output directory (default from config)')
@click.option('--after-date', type=str,
              help='Process messages after this date (YYYY-MM-DD)')
@click.option('--min-messages', type=int,
              help='Minimum message count per contact')
@click.option('--transcribe/--no-transcribe', default=True,
              help='Enable/disable audio transcription')
@click.option('--parallel/--sequential', default=True,
              help='Enable/disable parallel processing')
@click.option('--resume/--restart', default=True,
              help='Resume from last checkpoint')
@click.pass_context
def extract(ctx, export_path, output_dir, after_date, min_messages, 
           transcribe, parallel, resume):
    """Extract and process WhatsApp data"""
    config = ctx.obj['config']
    logger = logging.getLogger(__name__)
    
    # Update paths if provided
    if export_path:
        config.paths.whatsapp_export_path = Path(export_path)
    if output_dir:
        config.paths.export_output_dir = Path(output_dir)
    
    # Setup database and state
    database = CacheDatabase(config.paths.database_path)
    state_manager = StateManager(database)
    progress = ProgressTracker()
    
    try:
        # Start main task
        resumed = state_manager.start_task("full_extraction")
        if resumed:
            logger.info("Resuming from previous extraction")
        
        # Find HTML files
        html_files = list(config.paths.whatsapp_export_path.glob("*.html"))
        if not html_files:
            raise click.ClickException(f"No HTML files found in {config.paths.whatsapp_export_path}")
        
        logger.info(f"Found {len(html_files)} HTML file(s) to process")
        
        # Parse HTML files
        parser = WhatsAppHTMLParser()
        all_contacts = []
        all_messages_by_contact = {}
        
        with progress.track_task("Parsing HTML files", len(html_files)) as update:
            for i, html_file in enumerate(html_files):
                try:
                    contacts = parser.extract_contacts(html_file)
                    messages_by_contact = parser.parse(html_file)
                    
                    all_contacts.extend(contacts)
                    all_messages_by_contact.update(messages_by_contact)
                    
                    update(i + 1, f"Parsed {html_file.name}")
                except Exception as e:
                    logger.error(f"Failed to parse {html_file}: {e}")
                    state_manager.add_error("parsing_error", str(e), {"file": str(html_file)})
        
        logger.info(f"Parsed {len(all_contacts)} contacts with {sum(len(msgs) for msgs in all_messages_by_contact.values())} messages")
        
        # Apply filters
        filters = []
        
        if after_date:
            try:
                date_obj = datetime.strptime(after_date, "%Y-%m-%d")
                filters.append(DateFilter(after_date=date_obj))
            except ValueError:
                raise click.ClickException(f"Invalid date format: {after_date}. Use YYYY-MM-DD")
        
        if min_messages:
            filters.append(MessageCountFilter(min_messages=min_messages))
        
        if filters:
            composite_filter = CompositeFilter(filters, mode=FilterMode.AND)
            filtered_contacts = composite_filter.filter_many(all_contacts)
            logger.info(f"Filtered to {len(filtered_contacts)} contacts")
        else:
            filtered_contacts = all_contacts
        
        # Track contacts
        for contact in filtered_contacts:
            state_manager.track_contact(contact, True)
        
        # Organize media files
        if config.paths.whatsapp_export_path != config.paths.media_output_dir:
            media_processor = MediaProcessor(
                config.paths.whatsapp_export_path,
                config.paths.media_output_dir,
                database
            )
            
            with progress.track_task("Organizing media files") as update:
                organized_files = media_processor.organize_media(filtered_contacts)
                update(1, f"Organized {sum(len(files) for files in organized_files.values())} files")
        
        # Audio transcription
        if transcribe and config.transcription.api_key:
            transcriber = WhisperTranscriber(
                api_key=config.transcription.api_key,
                model=config.transcription.model,
                timeout=config.transcription.timeout,
                max_retries=config.transcription.max_retries
            )
            
            batch_processor = BatchTranscriptionProcessor(
                transcriber=transcriber,
                database=database,
                max_workers=config.processing.max_workers
            )
            
            # Find audio files to transcribe
            audio_files = []
            for contact in filtered_contacts:
                media_processor = MediaProcessor(
                    config.paths.whatsapp_export_path,
                    config.paths.media_output_dir
                )
                contact_audio = media_processor.get_audio_files_for_contact(contact)
                
                if config.transcription.transcribe_sent:
                    audio_files.extend(contact_audio['sent'])
                if config.transcription.transcribe_received:
                    audio_files.extend(contact_audio['received'])
            
            if audio_files:
                with progress.track_task("Transcribing audio files", len(audio_files)) as update:
                    def progress_callback(current, total):
                        update(current, f"Transcribed {current}/{total} files")
                    
                    results = batch_processor.process_files(
                        audio_files,
                        language=config.transcription.language,
                        progress_callback=progress_callback
                    )
                    
                    successful = sum(1 for r in results.values() if r.success)
                    logger.info(f"Successfully transcribed {successful}/{len(audio_files)} audio files")
            else:
                logger.info("No audio files found for transcription")
        
        # Complete task
        state_manager.complete_task()
        
        # Display statistics
        stats = state_manager.get_stats_summary()
        progress.display_stats(stats, "Extraction Complete")
        
        logger.info("Extraction completed successfully!")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        state_manager.fail_task(str(e))
        raise click.ClickException(str(e))


@cli.command()
@click.pass_context
def status(ctx):
    """Show current processing status"""
    config = ctx.obj['config']
    
    database = CacheDatabase(config.paths.database_path)
    stats = database.get_stats()
    
    progress = ProgressTracker()
    progress.display_stats(stats, "Current Status")


@cli.command()
@click.option('--days', type=int, default=30, help='Remove data older than N days')
@click.pass_context
def cleanup(ctx, days):
    """Clean up old cached data"""
    config = ctx.obj['config']
    
    database = CacheDatabase(config.paths.database_path)
    database.cleanup_old_data(days)
    
    click.echo(f"Cleaned up data older than {days} days")


@cli.command()
@click.option('--check-ffmpeg/--skip-ffmpeg', default=True)
@click.option('--check-whisper/--skip-whisper', default=True)
def setup(check_ffmpeg, check_whisper):
    """Setup and verify installation"""
    click.echo("WhatsApp Extractor v2 Setup")
    click.echo("=" * 30)
    
    # Check Python version
    if sys.version_info < (3, 8):
        click.echo("❌ Python 3.8+ required")
        return
    else:
        click.echo("✅ Python version OK")
    
    # Check FFmpeg
    if check_ffmpeg:
        try:
            from .processors import AudioConverter
            converter = AudioConverter()
            click.echo("✅ FFmpeg found")
        except Exception as e:
            click.echo(f"❌ FFmpeg not found: {e}")
            click.echo("   Install FFmpeg from https://ffmpeg.org/")
    
    # Check OpenAI API
    if check_whisper:
        import os
        if os.getenv('OPENAI_API_KEY'):
            click.echo("✅ OpenAI API key found in environment")
        else:
            click.echo("⚠️  OpenAI API key not found")
            click.echo("   Set OPENAI_API_KEY environment variable")
    
    click.echo("\nSetup complete!")


if __name__ == '__main__':
    cli()