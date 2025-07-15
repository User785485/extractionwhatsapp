"""Centralized logging configuration"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import sys


def setup_logging(
    log_file: Optional[Path] = None,
    log_level: str = "INFO",
    console_level: str = "INFO",
    log_format: Optional[str] = None,
    max_bytes: int = 10_485_760,  # 10MB
    backup_count: int = 5,
    log_dir: Optional[Path] = None
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_file: Path to log file (auto-generated if None)
        log_level: File logging level
        console_level: Console logging level
        log_format: Custom log format
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        log_dir: Directory for log files
        
    Returns:
        Configured root logger
    """
    # Create log directory
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Generate log file name if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"whatsapp_extractor_{timestamp}.log"
    
    # Default format
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Create formatters
    file_formatter = logging.Formatter(log_format)
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level.upper()))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log setup information
    root_logger.info(f"Logging initialized - File: {log_file}, Level: {log_level}")
    
    return root_logger


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS and sys.stdout.isatty():
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        return super().format(record)


class StructuredLogger:
    """Logger wrapper for structured logging"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_event(self, event: str, level: str = "INFO", **kwargs):
        """
        Log structured event
        
        Args:
            event: Event name
            level: Log level
            **kwargs: Additional fields
        """
        extra = {
            'event': event,
            'fields': kwargs
        }
        
        message = f"{event}: {', '.join(f'{k}={v}' for k, v in kwargs.items())}"
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """
        Log error with context
        
        Args:
            error: Exception object
            context: Additional context
        """
        context = context or {}
        
        self.logger.error(
            f"{error.__class__.__name__}: {str(error)}",
            extra={
                'error_type': error.__class__.__name__,
                'error_message': str(error),
                'context': context
            },
            exc_info=True
        )
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """
        Log performance metrics
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            **kwargs: Additional metrics
        """
        self.log_event(
            'performance',
            operation=operation,
            duration_ms=int(duration * 1000),
            **kwargs
        )


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(logging.getLogger(name))


# Convenience function to suppress noisy libraries
def configure_library_logging():
    """Configure logging levels for common libraries"""
    # Suppress noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Set appropriate levels for our modules
    logging.getLogger('src.processors').setLevel(logging.INFO)
    logging.getLogger('src.parsers').setLevel(logging.INFO)
    logging.getLogger('src.exporters').setLevel(logging.INFO)