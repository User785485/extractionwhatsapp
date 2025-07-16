"""Audio format conversion using FFmpeg"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from core.exceptions import MediaProcessingError
from utils.file_utils import create_unique_filename

logger = logging.getLogger(__name__)


class AudioConverter:
    """Converts audio files to MP3 format using FFmpeg"""
    
    SUPPORTED_INPUT_FORMATS = {'.opus', '.m4a', '.wav', '.ogg', '.aac', '.flac', '.wma', '.webm'}
    DEFAULT_BITRATE = '128k'
    DEFAULT_SAMPLE_RATE = 44100
    
    def __init__(self, ffmpeg_path: Optional[Path] = None, max_workers: int = 4):
        """
        Initialize audio converter
        
        Args:
            ffmpeg_path: Path to ffmpeg executable (auto-detect if None)
            max_workers: Maximum number of parallel conversions
        """
        self.ffmpeg_path = self._find_ffmpeg(ffmpeg_path)
        self.max_workers = max_workers
        
        if not self.ffmpeg_path:
            raise MediaProcessingError("FFmpeg not found. Please install FFmpeg or provide path.")
        
        logger.info(f"Using FFmpeg at: {self.ffmpeg_path}")
        
        self._stats = {
            'total': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0
        }
    
    def _find_ffmpeg(self, ffmpeg_path: Optional[Path] = None) -> Optional[Path]:
        """Find FFmpeg executable"""
        if ffmpeg_path and ffmpeg_path.exists():
            return ffmpeg_path
        
        # Check common locations
        possible_paths = [
            'ffmpeg',  # System PATH
            './ffmpeg/bin/ffmpeg.exe',  # Local installation
            'C:/ffmpeg/bin/ffmpeg.exe',  # Common Windows location
            '/usr/local/bin/ffmpeg',  # Common macOS/Linux location
            '/usr/bin/ffmpeg'  # Common Linux location
        ]
        
        # Add .exe for Windows
        if os.name == 'nt':
            possible_paths = [p if p.endswith('.exe') else f"{p}.exe" for p in possible_paths]
        
        for path in possible_paths:
            try:
                # Test if ffmpeg works
                result = subprocess.run(
                    [path, '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return Path(path)
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def convert_to_mp3(self, input_path: Path, output_path: Optional[Path] = None,
                      bitrate: str = DEFAULT_BITRATE, 
                      sample_rate: int = DEFAULT_SAMPLE_RATE) -> Optional[Path]:
        """
        Convert audio file to MP3
        
        Args:
            input_path: Path to input audio file
            output_path: Path for output MP3 (auto-generated if None)
            bitrate: Output bitrate (e.g., '128k', '192k')
            sample_rate: Output sample rate
            
        Returns:
            Path to converted file or None if failed
        """
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return None
        
        # Check if already MP3
        if input_path.suffix.lower() == '.mp3':
            logger.debug(f"File already MP3: {input_path}")
            self._stats['skipped'] += 1
            return input_path
        
        # Generate output path if not provided
        if not output_path:
            output_path = input_path.with_suffix('.mp3')
            if output_path.exists():
                output_path = create_unique_filename(output_path)
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build FFmpeg command
        cmd = [
            str(self.ffmpeg_path),
            '-i', str(input_path),
            '-acodec', 'mp3',
            '-b:a', bitrate,
            '-ar', str(sample_rate),
            '-y',  # Overwrite output
            str(output_path)
        ]
        
        try:
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode == 0 and output_path.exists():
                logger.info(f"Converted: {input_path.name} -> {output_path.name}")
                self._stats['converted'] += 1
                return output_path
            else:
                logger.error(f"FFmpeg error for {input_path.name}: {result.stderr}")
                self._stats['failed'] += 1
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout converting {input_path}")
            self._stats['failed'] += 1
            return None
        except Exception as e:
            logger.error(f"Failed to convert {input_path}: {e}")
            self._stats['failed'] += 1
            return None
    
    def convert_batch(self, audio_files: List[Path], output_dir: Optional[Path] = None,
                     preserve_structure: bool = True) -> Dict[Path, Optional[Path]]:
        """
        Convert multiple audio files in parallel
        
        Args:
            audio_files: List of audio files to convert
            output_dir: Output directory (use source directory if None)
            preserve_structure: Preserve directory structure in output
            
        Returns:
            Dictionary mapping input paths to output paths (None if failed)
        """
        logger.info(f"Converting {len(audio_files)} audio files")
        self._stats['total'] = len(audio_files)
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit conversion tasks
            future_to_file = {}
            
            for audio_file in audio_files:
                # Determine output path
                if output_dir:
                    if preserve_structure:
                        # Maintain relative path structure
                        try:
                            rel_path = audio_file.relative_to(audio_file.parent.parent)
                            output_path = output_dir / rel_path.with_suffix('.mp3')
                        except ValueError:
                            # If relative path fails, just use filename
                            output_path = output_dir / audio_file.with_suffix('.mp3').name
                    else:
                        output_path = output_dir / audio_file.with_suffix('.mp3').name
                else:
                    output_path = None
                
                future = executor.submit(self.convert_to_mp3, audio_file, output_path)
                future_to_file[future] = audio_file
            
            # Process completed conversions
            for future in as_completed(future_to_file):
                input_file = future_to_file[future]
                try:
                    output_file = future.result()
                    results[input_file] = output_file
                except Exception as e:
                    logger.error(f"Conversion failed for {input_file}: {e}")
                    results[input_file] = None
                    self._stats['failed'] += 1
        
        self._log_stats()
        return results
    
    def get_audio_info(self, audio_path: Path) -> Optional[Dict[str, any]]:
        """
        Get information about an audio file using FFprobe
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio information or None if failed
        """
        ffprobe_path = self.ffmpeg_path.parent / 'ffprobe'
        if os.name == 'nt':
            ffprobe_path = ffprobe_path.with_suffix('.exe')
        
        if not ffprobe_path.exists():
            # Try same directory as ffmpeg
            ffprobe_path = self.ffmpeg_path.with_name('ffprobe')
            if os.name == 'nt':
                ffprobe_path = ffprobe_path.with_suffix('.exe')
        
        if not ffprobe_path.exists():
            logger.warning("FFprobe not found")
            return None
        
        cmd = [
            str(ffprobe_path),
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(audio_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Extract relevant info
                format_info = data.get('format', {})
                audio_stream = next(
                    (s for s in data.get('streams', []) if s['codec_type'] == 'audio'),
                    {}
                )
                
                return {
                    'duration': float(format_info.get('duration', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'format': format_info.get('format_name', ''),
                    'codec': audio_stream.get('codec_name', ''),
                    'sample_rate': int(audio_stream.get('sample_rate', 0)),
                    'channels': int(audio_stream.get('channels', 0)),
                    'size': int(format_info.get('size', 0))
                }
            
        except Exception as e:
            logger.error(f"Failed to get audio info for {audio_path}: {e}")
        
        return None
    
    def _log_stats(self):
        """Log conversion statistics"""
        logger.info("Audio conversion completed:")
        logger.info(f"  Total files: {self._stats['total']}")
        logger.info(f"  Converted: {self._stats['converted']}")
        logger.info(f"  Skipped (already MP3): {self._stats['skipped']}")
        logger.info(f"  Failed: {self._stats['failed']}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get conversion statistics"""
        return dict(self._stats)