"""Batch processing for parallel transcriptions"""

import asyncio
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any
import logging
from datetime import datetime

from processors.transcription.base_transcriber import BaseTranscriber
from core.models import TranscriptionResult
from core.database import CacheDatabase
from core.exceptions import TranscriptionError

logger = logging.getLogger(__name__)


class BatchTranscriptionProcessor:
    """Handles batch transcription with parallel processing"""
    
    def __init__(self, transcriber: BaseTranscriber, database: Optional[CacheDatabase] = None,
                 max_workers: Optional[int] = None, use_cache: bool = True):
        """
        Initialize batch processor
        
        Args:
            transcriber: Transcriber instance to use
            database: Optional database for caching
            max_workers: Maximum number of parallel workers
            use_cache: Whether to use cache for transcriptions
        """
        self.transcriber = transcriber
        self.database = database
        self.use_cache = use_cache
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        
        self._stats = {
            'total': 0,
            'processed': 0,
            'cached': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }
    
    def process_files(self, audio_files: List[Path], 
                     language: Optional[str] = None,
                     progress_callback: Optional[Callable[[int, int], None]] = None,
                     filter_callback: Optional[Callable[[Path], bool]] = None) -> Dict[Path, TranscriptionResult]:
        """
        Process multiple audio files with caching and parallel execution
        
        Args:
            audio_files: List of audio files to process
            language: Optional language for transcription
            progress_callback: Callback function for progress updates (current, total)
            filter_callback: Optional callback to filter files
            
        Returns:
            Dictionary mapping file paths to transcription results
        """
        logger.info(f"Starting batch transcription of {len(audio_files)} files")
        
        self._stats['total'] = len(audio_files)
        self._stats['start_time'] = datetime.now()
        
        # Filter files if callback provided
        if filter_callback:
            audio_files = [f for f in audio_files if filter_callback(f)]
            logger.info(f"Filtered to {len(audio_files)} files")
        
        results = {}
        files_to_process = []
        
        # Check cache first
        if self.use_cache and self.database:
            for audio_file in audio_files:
                cached_result = self._get_cached_transcription(audio_file)
                if cached_result:
                    results[audio_file] = cached_result
                    self._stats['cached'] += 1
                    if progress_callback:
                        progress_callback(len(results), len(audio_files))
                else:
                    files_to_process.append(audio_file)
        else:
            files_to_process = audio_files
        
        logger.info(f"Found {self._stats['cached']} cached transcriptions, processing {len(files_to_process)} files")
        
        # Process remaining files in parallel
        if files_to_process:
            if len(files_to_process) == 1:
                # Single file - process directly
                result = self._process_single_file(files_to_process[0], language)
                results[files_to_process[0]] = result
                if progress_callback:
                    progress_callback(len(results), len(audio_files))
            else:
                # Multiple files - use parallel processing
                batch_results = self._process_parallel(
                    files_to_process, 
                    language, 
                    progress_callback,
                    current_count=len(results),
                    total_count=len(audio_files)
                )
                results.update(batch_results)
        
        self._stats['end_time'] = datetime.now()
        self._log_stats()
        
        return results
    
    def _process_parallel(self, files: List[Path], language: Optional[str],
                         progress_callback: Optional[Callable] = None,
                         current_count: int = 0, total_count: int = 0) -> Dict[Path, TranscriptionResult]:
        """Process files in parallel using thread pool"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self._process_single_file, file, language): file
                for file in files
            }
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results[file] = result
                    
                    if progress_callback:
                        progress_callback(current_count + len(results), total_count)
                        
                except Exception as e:
                    logger.error(f"Failed to process {file}: {e}")
                    results[file] = TranscriptionResult(
                        file_path=file,
                        text="",
                        error=str(e)
                    )
                    self._stats['failed'] += 1
        
        return results
    
    def _process_single_file(self, audio_file: Path, language: Optional[str]) -> TranscriptionResult:
        """Process a single audio file"""
        try:
            # Transcribe
            result = self.transcriber.transcribe(audio_file, language)
            
            # Update stats
            if result.success:
                self._stats['processed'] += 1
            else:
                self._stats['failed'] += 1
            
            # Cache result
            if self.use_cache and self.database and result.success:
                self._cache_transcription(audio_file, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription error for {audio_file}: {e}")
            self._stats['failed'] += 1
            return TranscriptionResult(
                file_path=audio_file,
                text="",
                error=str(e)
            )
    
    def _get_cached_transcription(self, audio_file: Path) -> Optional[TranscriptionResult]:
        """Get transcription from cache"""
        try:
            return self.database.get_transcription(audio_file)
        except Exception as e:
            logger.warning(f"Failed to get cached transcription for {audio_file}: {e}")
            return None
    
    def _cache_transcription(self, audio_file: Path, result: TranscriptionResult):
        """Cache transcription result"""
        try:
            self.database.add_transcription(result)
        except Exception as e:
            logger.warning(f"Failed to cache transcription for {audio_file}: {e}")
    
    def process_with_super_files(self, audio_files: List[Path], 
                                batch_size: int = 50,
                                output_dir: Optional[Path] = None) -> Dict[Path, TranscriptionResult]:
        """
        Process files by creating super files for batch transcription
        
        Args:
            audio_files: List of audio files
            batch_size: Number of files per super file
            output_dir: Directory for temporary super files
            
        Returns:
            Dictionary mapping original files to transcription results
        """
        if not hasattr(self.transcriber, 'create_super_file'):
            logger.warning("Transcriber doesn't support super files, falling back to regular processing")
            return self.process_files(audio_files)
        
        results = {}
        output_dir = output_dir or Path.cwd() / 'temp_super_files'
        output_dir.mkdir(exist_ok=True)
        
        # Process in batches
        for i in range(0, len(audio_files), batch_size):
            batch = audio_files[i:i + batch_size]
            super_file = output_dir / f"super_batch_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            
            try:
                # Create super file
                created_file = self.transcriber.create_super_file(batch, super_file)
                if created_file:
                    # Transcribe super file
                    result = self.transcriber.transcribe(created_file)
                    
                    if result.success:
                        # Split transcription back to individual files
                        # This is a simplified approach - in reality you'd need timestamps
                        text_parts = self._split_transcription(result.text, len(batch))
                        
                        for j, audio_file in enumerate(batch):
                            individual_result = TranscriptionResult(
                                file_path=audio_file,
                                text=text_parts[j] if j < len(text_parts) else "",
                                language=result.language
                            )
                            results[audio_file] = individual_result
                            
                            if self.use_cache and self.database:
                                self._cache_transcription(audio_file, individual_result)
                    
                    # Clean up super file
                    created_file.unlink()
                    
            except Exception as e:
                logger.error(f"Failed to process batch {i}: {e}")
                # Fall back to individual processing for this batch
                for audio_file in batch:
                    results[audio_file] = self._process_single_file(audio_file, None)
        
        return results
    
    def _split_transcription(self, text: str, num_parts: int) -> List[str]:
        """Split transcription text into parts (simplified)"""
        # This is a basic implementation - in production you'd use
        # timestamps or silence detection to split accurately
        if not text or num_parts <= 1:
            return [text]
        
        words = text.split()
        words_per_part = max(1, len(words) // num_parts)
        
        parts = []
        for i in range(num_parts):
            start = i * words_per_part
            end = start + words_per_part if i < num_parts - 1 else len(words)
            parts.append(' '.join(words[start:end]))
        
        return parts
    
    def _log_stats(self):
        """Log processing statistics"""
        duration = (self._stats['end_time'] - self._stats['start_time']).total_seconds()
        
        logger.info(f"Batch transcription completed:")
        logger.info(f"  Total files: {self._stats['total']}")
        logger.info(f"  Processed: {self._stats['processed']}")
        logger.info(f"  From cache: {self._stats['cached']}")
        logger.info(f"  Failed: {self._stats['failed']}")
        logger.info(f"  Duration: {duration:.2f} seconds")
        logger.info(f"  Average time per file: {duration / max(1, self._stats['total']):.2f} seconds")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self._stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration'] = (stats['end_time'] - stats['start_time']).total_seconds()
        return stats