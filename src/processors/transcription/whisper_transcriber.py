"""OpenAI Whisper transcription implementation"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from processors.transcription.base_transcriber import BaseTranscriber
from core.models import TranscriptionResult
from core.exceptions import TranscriptionError, APIError

logger = logging.getLogger(__name__)


class WhisperTranscriber(BaseTranscriber):
    """OpenAI Whisper API transcription service"""
    
    API_URL = "https://api.openai.com/v1/audio/transcriptions"
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB
    SUPPORTED_FORMATS = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
    
    def __init__(self, api_key: str, model: str = "whisper-1", 
                 timeout: int = 300, max_retries: int = 3):
        """
        Initialize Whisper transcriber
        
        Args:
            api_key: OpenAI API key
            model: Whisper model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        if not api_key:
            raise ValueError("API key is required for Whisper transcription")
        
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Setup session with retry strategy
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers
        session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })
        
        return session
    
    def transcribe(self, audio_path: Path, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe a single audio file"""
        logger.info(f"Transcribing file: {audio_path}")
        
        # Validate file
        if not self.validate_file(audio_path):
            error_msg = f"Invalid audio file: {audio_path}"
            logger.error(error_msg)
            return TranscriptionResult(
                file_path=audio_path,
                text="",
                error=error_msg
            )
        
        # Check file size
        file_size = audio_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            error_msg = f"File too large: {file_size / (1024*1024):.2f}MB (max: 25MB)"
            logger.error(error_msg)
            return TranscriptionResult(
                file_path=audio_path,
                text="",
                error=error_msg
            )
        
        # Prepare request
        start_time = time.time()
        
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'file': (audio_path.name, audio_file, 'audio/mpeg')}
                
                data = {
                    'model': self.model,
                    'response_format': 'verbose_json'
                }
                
                if language:
                    data['language'] = language
                
                # Make request with retries
                response = self._make_request(files, data)
                
                # Parse response
                result_data = response.json()
                
                duration = time.time() - start_time
                
                return TranscriptionResult(
                    file_path=audio_path,
                    text=result_data.get('text', ''),
                    language=result_data.get('language'),
                    duration=duration
                )
                
        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(f"{error_msg} for file: {audio_path}")
            
            return TranscriptionResult(
                file_path=audio_path,
                text="",
                error=error_msg,
                duration=time.time() - start_time
            )
    
    def _make_request(self, files: Dict, data: Dict) -> requests.Response:
        """Make API request with error handling"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    self.API_URL,
                    files=files,
                    data=data,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                last_error = "Request timed out"
                logger.warning(f"Attempt {attempt + 1} timed out")
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    # Rate limit - wait before retry
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    last_error = "Rate limited"
                elif e.response.status_code == 401:
                    raise APIError("Invalid API key", status_code=401)
                else:
                    last_error = f"HTTP error: {e.response.status_code}"
                    logger.error(f"HTTP error on attempt {attempt + 1}: {e}")
                    
            except requests.exceptions.RequestException as e:
                last_error = f"Request error: {str(e)}"
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = (2 ** attempt) * 1
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        raise TranscriptionError(f"Failed after {self.max_retries} attempts: {last_error}")
    
    def transcribe_batch(self, audio_paths: List[Path], 
                        language: Optional[str] = None) -> Dict[Path, TranscriptionResult]:
        """Transcribe multiple audio files"""
        results = {}
        
        for audio_path in audio_paths:
            result = self.transcribe(audio_path, language)
            results[audio_path] = result
            
            # Small delay to avoid rate limits
            if len(audio_paths) > 1:
                time.sleep(0.5)
        
        return results
    
    def validate_file(self, audio_path: Path) -> bool:
        """Validate if file can be transcribed"""
        if not audio_path.exists():
            return False
        
        if not audio_path.is_file():
            return False
        
        # Check extension
        if audio_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return False
        
        # Check file size
        if audio_path.stat().st_size == 0:
            return False
        
        if audio_path.stat().st_size > self.MAX_FILE_SIZE:
            return False
        
        return True
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported audio formats"""
        return self.SUPPORTED_FORMATS.copy()
    
    def create_super_file(self, audio_files: List[Path], output_path: Path) -> Optional[Path]:
        """
        Create a concatenated audio file for batch transcription
        
        Args:
            audio_files: List of audio files to concatenate
            output_path: Path for the output file
            
        Returns:
            Path to the created file or None if failed
        """
        try:
            # Check if ffmpeg is available
            import subprocess
            
            # Create file list for ffmpeg
            list_file = output_path.parent / f"{output_path.stem}_list.txt"
            with open(list_file, 'w', encoding='utf-8') as f:
                for audio_file in audio_files:
                    # Escape single quotes in filename
                    escaped_path = str(audio_file).replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")
            
            # Run ffmpeg to concatenate
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(list_file),
                '-c', 'copy',
                '-y',  # Overwrite output
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Clean up list file
            list_file.unlink()
            
            # Verify output
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Created super file: {output_path} ({output_path.stat().st_size / (1024*1024):.2f}MB)")
                return output_path
            else:
                logger.error("Super file creation failed - no output")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to create super file: {e}")
            return None