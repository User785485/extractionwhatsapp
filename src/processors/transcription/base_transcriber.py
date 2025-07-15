"""Abstract base class for transcription services"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any

from ...core.models import TranscriptionResult


class BaseTranscriber(ABC):
    """Abstract base class for transcription services"""
    
    @abstractmethod
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        """
        Transcribe a single audio file
        
        Args:
            audio_path: Path to the audio file
            language: Optional language code for transcription
            
        Returns:
            TranscriptionResult object
        """
        pass
    
    @abstractmethod
    def transcribe_batch(self, audio_paths: List[Path], 
                        language: Optional[str] = None) -> Dict[Path, TranscriptionResult]:
        """
        Transcribe multiple audio files
        
        Args:
            audio_paths: List of paths to audio files
            language: Optional language code for transcription
            
        Returns:
            Dictionary mapping file paths to TranscriptionResult objects
        """
        pass
    
    @abstractmethod
    def validate_file(self, audio_path: Path) -> bool:
        """
        Validate if file can be transcribed
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            True if file is valid for transcription
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats
        
        Returns:
            List of file extensions (e.g., ['.mp3', '.wav'])
        """
        pass
    
    def get_file_info(self, audio_path: Path) -> Dict[str, Any]:
        """
        Get information about an audio file
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary with file information
        """
        stat = audio_path.stat()
        return {
            'size': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'extension': audio_path.suffix.lower(),
            'name': audio_path.name
        }