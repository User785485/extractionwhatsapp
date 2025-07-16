#!/usr/bin/env python3
"""
Système de logging multi-niveaux avancé pour WhatsApp Extractor v2
Logs séparés par type avec identifiants uniques et alertes critiques
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import traceback
import json
import uuid
from typing import Dict, Any, Optional
from enum import Enum
import threading
import time


class LogLevel(Enum):
    """Niveaux de log personnalisés"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Catégories d'erreurs pour un logging ciblé"""
    FILE_READ = "FILE_READ"
    HTML_PARSING = "HTML_PARSING"
    MESSAGE_CLASSIFICATION = "MESSAGE_CLASSIFICATION"
    MEDIA_ORGANIZATION = "MEDIA_ORGANIZATION"
    AUDIO_CONVERSION = "AUDIO_CONVERSION"
    TRANSCRIPTION_API = "TRANSCRIPTION_API"
    EXPORT_CREATION = "EXPORT_CREATION"
    REGISTRY_ACCESS = "REGISTRY_ACCESS"
    DATABASE_OPERATION = "DATABASE_OPERATION"
    CONFIGURATION = "CONFIGURATION"
    NETWORK = "NETWORK"
    PERMISSION = "PERMISSION"
    MEMORY = "MEMORY"
    UNKNOWN = "UNKNOWN"


class AdvancedLogger:
    """Logger avancé avec séparation par types et alertes"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("logs")
        self.base_dir.mkdir(exist_ok=True)
        
        # Session unique
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        
        # Compteurs d'erreurs
        self.error_counters = {category.value: 0 for category in ErrorCategory}
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_files = set()
        
        # Lock pour thread safety
        self.lock = threading.Lock()
        
        # Configuration des loggers
        self.loggers = self._setup_loggers()
        
        # Fichier critique
        self.critical_file = self.base_dir / "CRITICAL_ERRORS.txt"
        
        # Démarrer session
        self._log_session_start()
    
    def _setup_loggers(self) -> Dict[str, logging.Logger]:
        """Configuration des différents loggers"""
        loggers = {}
        
        # Format détaillé avec millisecondes
        detailed_formatter = logging.Formatter(
            fmt='[%(asctime)s.%(msecs)03d] [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Format simple pour le main log
        simple_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Logger principal
        main_logger = self._create_logger(
            'main',
            self.base_dir / f"main_{self.session_id}.log",
            simple_formatter,
            logging.INFO
        )
        loggers['main'] = main_logger
        
        # Logger d'erreurs
        error_logger = self._create_logger(
            'errors',
            self.base_dir / f"errors_{self.session_id}.log",
            detailed_formatter,
            logging.ERROR
        )
        loggers['errors'] = error_logger
        
        # Logger debug
        debug_logger = self._create_logger(
            'debug',
            self.base_dir / f"debug_{self.session_id}.log",
            detailed_formatter,
            logging.DEBUG
        )
        loggers['debug'] = debug_logger
        
        # Logger transcription
        transcription_logger = self._create_logger(
            'transcription',
            self.base_dir / f"transcription_errors_{self.session_id}.log",
            detailed_formatter,
            logging.WARNING
        )
        loggers['transcription'] = transcription_logger
        
        # Logger parsing
        parsing_logger = self._create_logger(
            'parsing',
            self.base_dir / f"parsing_errors_{self.session_id}.log",
            detailed_formatter,
            logging.WARNING
        )
        loggers['parsing'] = parsing_logger
        
        # Logger média
        media_logger = self._create_logger(
            'media',
            self.base_dir / f"media_errors_{self.session_id}.log",
            detailed_formatter,
            logging.WARNING
        )
        loggers['media'] = media_logger
        
        return loggers
    
    def _create_logger(self, name: str, file_path: Path, formatter: logging.Formatter, level: int) -> logging.Logger:
        """Créer un logger avec handler de fichier"""
        logger = logging.getLogger(f"whatsapp_extractor_{name}_{self.session_id}")
        logger.setLevel(level)
        
        # Éviter les handlers dupliqués
        if logger.handlers:
            logger.handlers.clear()
        
        # Handler fichier
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
        
        # Handler console pour les erreurs critiques
        if name in ['errors', 'main']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.ERROR if name == 'errors' else logging.INFO)
            logger.addHandler(console_handler)
        
        return logger
    
    def _log_session_start(self):
        """Logger le début de session"""
        session_info = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'python_version': sys.version,
            'platform': sys.platform,
            'log_directory': str(self.base_dir.absolute())
        }
        
        self.info("=== WhatsApp Extractor v2 - Session Started ===")
        self.info(f"Session ID: {self.session_id}")
        self.debug(f"Session info: {json.dumps(session_info, indent=2)}")
    
    def _generate_error_id(self) -> str:
        """Générer un ID unique d'erreur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"ERR_{timestamp}_{unique_suffix}"
    
    def _save_context(self, error_id: str, context: Dict[str, Any]):
        """Sauvegarder le contexte d'une erreur"""
        context_file = self.base_dir / f"context_{error_id}.json"
        try:
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'error_id': error_id,
                    'timestamp': datetime.now().isoformat(),
                    'context': context
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save error context: {e}")
    
    def _write_critical_alert(self, error_id: str, message: str, category: ErrorCategory):
        """Écrire une alerte critique"""
        alert_message = f"""
{'='*60}
CRITICAL ERROR ALERT
{'='*60}
Error ID: {error_id}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}
Category: {category.value}
Session: {self.session_id}

Message: {message}

This error has been logged in detail in the error logs.
Check the logs directory for full context and stack trace.
{'='*60}

"""
        
        try:
            with open(self.critical_file, 'a', encoding='utf-8') as f:
                f.write(alert_message)
            
            # Afficher en rouge dans la console
            print(f"\033[91m{alert_message}\033[0m")
            
        except Exception as e:
            print(f"Failed to write critical alert: {e}")
    
    def _increment_counter(self, category: ErrorCategory):
        """Incrémenter le compteur d'erreurs"""
        with self.lock:
            self.error_counters[category.value] += 1
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log niveau INFO"""
        self.loggers['main'].info(message)
        if context:
            self.loggers['debug'].info(f"{message} | Context: {json.dumps(context)}")
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log niveau DEBUG"""
        self.loggers['debug'].debug(message)
        if context:
            self.loggers['debug'].debug(f"Context: {json.dumps(context)}")
    
    def warning(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN, 
                context: Optional[Dict[str, Any]] = None):
        """Log niveau WARNING"""
        self.loggers['main'].warning(message)
        self.loggers['debug'].warning(f"{message} | Category: {category.value}")
        
        if context:
            self.loggers['debug'].warning(f"Context: {json.dumps(context)}")
    
    def error(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
              context: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Log niveau ERROR avec contexte et stack trace"""
        error_id = self._generate_error_id()
        
        # Incrémenter compteur
        self._increment_counter(category)
        
        # Message d'erreur complet
        full_message = f"[{error_id}] [{category.value}] {message}"
        
        # Logger dans les différents logs
        self.loggers['errors'].error(full_message)
        self.loggers['main'].error(f"Error {error_id}: {message}")
        
        # Logger spécialisé selon la catégorie
        if category == ErrorCategory.TRANSCRIPTION_API:
            self.loggers['transcription'].error(full_message)
        elif category in [ErrorCategory.HTML_PARSING, ErrorCategory.MESSAGE_CLASSIFICATION]:
            self.loggers['parsing'].error(full_message)
        elif category in [ErrorCategory.MEDIA_ORGANIZATION, ErrorCategory.AUDIO_CONVERSION]:
            self.loggers['media'].error(full_message)
        
        # Stack trace si exception
        if exception:
            stack_trace = traceback.format_exc()
            self.loggers['errors'].error(f"[{error_id}] Stack trace:\n{stack_trace}")
            self.loggers['debug'].error(f"[{error_id}] Full exception: {repr(exception)}")
        
        # Sauvegarder contexte
        if context:
            full_context = {
                'error_id': error_id,
                'category': category.value,
                'message': message,
                'exception': repr(exception) if exception else None,
                'stack_trace': traceback.format_exc() if exception else None,
                **context
            }
            self._save_context(error_id, full_context)
        
        return error_id
    
    def critical(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 context: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Log niveau CRITICAL avec alerte immédiate"""
        error_id = self._generate_error_id()
        
        # Incrémenter compteur
        self._increment_counter(category)
        
        # Message critique complet
        full_message = f"[{error_id}] [CRITICAL] [{category.value}] {message}"
        
        # Logger partout
        self.loggers['errors'].critical(full_message)
        self.loggers['main'].critical(f"CRITICAL {error_id}: {message}")
        self.loggers['debug'].critical(full_message)
        
        # Stack trace si exception
        if exception:
            stack_trace = traceback.format_exc()
            self.loggers['errors'].critical(f"[{error_id}] Critical stack trace:\n{stack_trace}")
        
        # Sauvegarder contexte complet
        full_context = {
            'error_id': error_id,
            'category': category.value,
            'message': message,
            'level': 'CRITICAL',
            'exception': repr(exception) if exception else None,
            'stack_trace': traceback.format_exc() if exception else None,
            'session_id': self.session_id,
            **(context or {})
        }
        self._save_context(error_id, full_context)
        
        # Alerte critique
        self._write_critical_alert(error_id, message, category)
        
        return error_id
    
    def log_file_processing(self, file_path: str, success: bool, 
                           error_message: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None):
        """Logger le traitement d'un fichier"""
        with self.lock:
            self.total_operations += 1
            
            if success:
                self.successful_operations += 1
                self.info(f"File processed successfully: {file_path}", context)
            else:
                self.failed_files.add(file_path)
                error_context = {
                    'file_path': file_path,
                    'operation_number': self.total_operations,
                    **(context or {})
                }
                self.error(
                    f"Failed to process file: {file_path} - {error_message}",
                    ErrorCategory.FILE_READ,
                    error_context
                )
    
    def log_contact_processing(self, contact_name: str, messages_count: int, 
                              success: bool, error_message: Optional[str] = None):
        """Logger le traitement d'un contact"""
        context = {
            'contact_name': contact_name,
            'messages_count': messages_count
        }
        
        if success:
            self.info(f"Contact processed: {contact_name} ({messages_count} messages)", context)
        else:
            self.error(
                f"Failed to process contact: {contact_name} - {error_message}",
                ErrorCategory.HTML_PARSING,
                context
            )
    
    def log_transcription_attempt(self, audio_file: str, success: bool,
                                 api_response: Optional[Dict] = None,
                                 error_code: Optional[str] = None):
        """Logger une tentative de transcription"""
        context = {
            'audio_file': audio_file,
            'api_response': api_response,
            'error_code': error_code
        }
        
        if success:
            self.info(f"Transcription successful: {audio_file}", context)
        else:
            self.error(
                f"Transcription failed: {audio_file} (Code: {error_code})",
                ErrorCategory.TRANSCRIPTION_API,
                context
            )
    
    def log_media_conversion(self, media_file: str, target_format: str,
                           success: bool, error_message: Optional[str] = None):
        """Logger une conversion de média"""
        context = {
            'media_file': media_file,
            'target_format': target_format
        }
        
        if success:
            self.info(f"Media converted: {media_file} -> {target_format}", context)
        else:
            self.error(
                f"Media conversion failed: {media_file} -> {target_format} - {error_message}",
                ErrorCategory.AUDIO_CONVERSION,
                context
            )
    
    def log_export_creation(self, export_type: str, file_path: str,
                          records_count: int, success: bool,
                          error_message: Optional[str] = None):
        """Logger la création d'un export"""
        context = {
            'export_type': export_type,
            'file_path': file_path,
            'records_count': records_count
        }
        
        if success:
            self.info(f"Export created: {export_type} ({records_count} records) -> {file_path}", context)
        else:
            self.error(
                f"Export creation failed: {export_type} -> {file_path} - {error_message}",
                ErrorCategory.EXPORT_CREATION,
                context
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques de la session"""
        elapsed_time = time.time() - self.start_time
        
        with self.lock:
            success_rate = (self.successful_operations / max(self.total_operations, 1)) * 100
            
            stats = {
                'session_id': self.session_id,
                'elapsed_time_seconds': round(elapsed_time, 2),
                'total_operations': self.total_operations,
                'successful_operations': self.successful_operations,
                'failed_operations': self.total_operations - self.successful_operations,
                'success_rate_percent': round(success_rate, 2),
                'error_counters': dict(self.error_counters),
                'failed_files_count': len(self.failed_files),
                'failed_files': list(self.failed_files)
            }
        
        return stats
    
    def log_session_summary(self):
        """Logger le résumé de la session"""
        stats = self.get_statistics()
        
        self.info("=== Session Summary ===")
        self.info(f"Total operations: {stats['total_operations']}")
        self.info(f"Success rate: {stats['success_rate_percent']}%")
        self.info(f"Elapsed time: {stats['elapsed_time_seconds']}s")
        
        # Erreurs par catégorie
        total_errors = sum(stats['error_counters'].values())
        if total_errors > 0:
            self.warning(f"Total errors: {total_errors}")
            for category, count in stats['error_counters'].items():
                if count > 0:
                    self.warning(f"  {category}: {count}")
        
        # Sauvegarder les stats
        stats_file = self.base_dir / f"session_stats_{self.session_id}.json"
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.error(f"Failed to save session stats: {e}", ErrorCategory.FILE_READ)
    
    def close(self):
        """Fermer le logger et finaliser la session"""
        self.log_session_summary()
        
        # Fermer tous les handlers
        for logger in self.loggers.values():
            for handler in logger.handlers:
                handler.close()
        
        self.info("=== Session Ended ===")


# Instance globale pour faciliter l'utilisation
_global_logger: Optional[AdvancedLogger] = None

def get_logger() -> AdvancedLogger:
    """Obtenir l'instance globale du logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AdvancedLogger()
    return _global_logger

def init_logger(base_dir: Optional[Path] = None) -> AdvancedLogger:
    """Initialiser le logger global"""
    global _global_logger
    _global_logger = AdvancedLogger(base_dir)
    return _global_logger

def close_logger():
    """Fermer le logger global"""
    global _global_logger
    if _global_logger:
        _global_logger.close()
        _global_logger = None