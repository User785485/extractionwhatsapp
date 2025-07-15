"""File system utility functions"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional, Callable, Any
import unicodedata
import logging

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for cross-platform compatibility
    
    Args:
        filename: Original filename
        max_length: Maximum length for filename
        
    Returns:
        Sanitized filename safe for all platforms
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Replace problematic characters
    # Windows forbidden characters: < > : " | ? * \0-\31
    # Unix hidden files start with .
    # Spaces at start/end can cause issues
    filename = re.sub(r'[<>:"|?*\x00-\x1f\\]', '_', filename)
    
    # Replace other problematic characters
    filename = filename.replace('/', '_')
    filename = filename.replace('\n', ' ')
    filename = filename.replace('\r', ' ')
    filename = filename.replace('\t', ' ')
    
    # Remove multiple spaces and trim
    filename = re.sub(r'\s+', ' ', filename).strip()
    
    # Remove leading dots (hidden files on Unix)
    filename = filename.lstrip('.')
    
    # Handle empty result
    if not filename:
        filename = 'unnamed'
    
    # Truncate if too long (leave room for extension)
    name_part, ext = os.path.splitext(filename)
    if len(filename) > max_length:
        max_name_length = max_length - len(ext) - 1
        name_part = name_part[:max_name_length]
        filename = name_part + ext
    
    # Ensure it doesn't end with space or dot (Windows issue)
    filename = filename.rstrip('. ')
    
    return filename


def create_unique_filename(file_path: Path, pattern: str = "_{count}") -> Path:
    """
    Create unique filename by adding counter if file exists
    
    Args:
        file_path: Original file path
        pattern: Pattern for counter (must contain {count})
        
    Returns:
        Unique file path that doesn't exist
    """
    if not file_path.exists():
        return file_path
    
    directory = file_path.parent
    stem = file_path.stem
    extension = file_path.suffix
    
    counter = 1
    while True:
        new_name = f"{stem}{pattern.format(count=counter)}{extension}"
        new_path = directory / new_name
        
        if not new_path.exists():
            return new_path
        
        counter += 1
        
        # Safety check to prevent infinite loop
        if counter > 9999:
            raise ValueError(f"Could not create unique filename for {file_path}")


def get_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file contents
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex digest of file hash
    """
    hash_func = getattr(hashlib, algorithm)()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def ensure_directory(directory: Path) -> Path:
    """
    Ensure directory exists, create if necessary
    
    Args:
        directory: Directory path
        
    Returns:
        Directory path (created if necessary)
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_file_operation(operation: Callable, *args, default: Any = None, **kwargs) -> Any:
    """
    Execute file operation safely with error handling
    
    Args:
        operation: File operation to execute
        *args: Arguments for operation
        default: Default value to return on error
        **kwargs: Keyword arguments for operation
        
    Returns:
        Result of operation or default value
    """
    try:
        return operation(*args, **kwargs)
    except (IOError, OSError) as e:
        logger.error(f"File operation failed: {e}")
        return default
    except Exception as e:
        logger.error(f"Unexpected error in file operation: {e}")
        return default


def get_directory_size(directory: Path) -> int:
    """
    Get total size of directory in bytes
    
    Args:
        directory: Directory path
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size


def clean_empty_directories(directory: Path) -> int:
    """
    Remove empty directories recursively
    
    Args:
        directory: Root directory to clean
        
    Returns:
        Number of directories removed
    """
    removed_count = 0
    
    for subdir in sorted(directory.rglob('*'), reverse=True):
        if subdir.is_dir():
            try:
                # Try to remove directory (will fail if not empty)
                subdir.rmdir()
                removed_count += 1
                logger.debug(f"Removed empty directory: {subdir}")
            except OSError:
                # Directory not empty, skip
                pass
    
    return removed_count


def copy_with_metadata(source: Path, destination: Path) -> bool:
    """
    Copy file preserving metadata
    
    Args:
        source: Source file path
        destination: Destination file path
        
    Returns:
        True if successful
    """
    try:
        import shutil
        shutil.copy2(source, destination)
        return True
    except Exception as e:
        logger.error(f"Failed to copy {source} to {destination}: {e}")
        return False