#!/usr/bin/env python3
"""
Système de logging avancé pour l'interface WhatsApp Extractor v2
Logs détaillés avec fichiers horodatés et niveaux multiples
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import traceback


class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour la console"""
    
    # Codes couleur ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Ajouter la couleur selon le niveau
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class GUILogHandler(logging.Handler):
    """Handler personnalisé pour envoyer les logs vers l'interface"""
    
    def __init__(self, gui_callback=None):
        super().__init__()
        self.gui_callback = gui_callback
        
    def emit(self, record):
        """Émettre un log vers l'interface"""
        if self.gui_callback:
            try:
                msg = self.format(record)
                self.gui_callback(msg, record.levelname)
            except Exception:
                pass  # Éviter les boucles d'erreur


class WhatsAppLogger:
    """Gestionnaire de logs principal pour WhatsApp Extractor v2"""
    
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Créer un nom de fichier unique avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.logs_dir / f"whatsapp_extractor_GUI_{timestamp}.log"
        
        # Configurer le logger principal
        self.logger = logging.getLogger("WhatsApp_Extractor")
        self.logger.setLevel(logging.DEBUG)
        
        # Éviter la duplication des handlers
        if not self.logger.handlers:
            self.setup_handlers()
            
    def setup_handlers(self):
        """Configurer tous les handlers de logging"""
        
        # Format pour les logs
        detailed_format = (
            "[%(asctime)s] %(levelname)-8s "
            "[%(filename)s:%(lineno)d] %(funcName)s() - %(message)s"
        )
        simple_format = "[%(asctime)s] %(levelname)s: %(message)s"
        
        # 1. Handler pour fichier (logs détaillés)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(detailed_format)
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # 2. Handler pour console (avec couleurs)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter(simple_format)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 3. Handler pour l'interface GUI
        if self.gui_callback:
            gui_handler = GUILogHandler(self.gui_callback)
            gui_handler.setLevel(logging.INFO)
            gui_formatter = logging.Formatter(simple_format)
            gui_handler.setFormatter(gui_formatter)
            self.logger.addHandler(gui_handler)
            
        # Log de démarrage
        self.logger.info("=== WhatsApp Extractor v2 - Session de logging démarrée ===")
        self.logger.info(f"Fichier de log: {self.log_file}")
        
    def debug(self, message: str, **kwargs):
        """Log niveau DEBUG"""
        self.logger.debug(self._format_message(message, **kwargs))
        
    def info(self, message: str, **kwargs):
        """Log niveau INFO"""
        self.logger.info(self._format_message(message, **kwargs))
        
    def warning(self, message: str, **kwargs):
        """Log niveau WARNING"""
        self.logger.warning(self._format_message(message, **kwargs))
        
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log niveau ERROR avec stack trace optionnel"""
        formatted_msg = self._format_message(message, **kwargs)
        
        if exception:
            # Ajouter la stack trace
            formatted_msg += f"\nException: {type(exception).__name__}: {str(exception)}"
            formatted_msg += f"\nStack trace:\n{traceback.format_exc()}"
            
        self.logger.error(formatted_msg)
        
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log niveau CRITICAL"""
        formatted_msg = self._format_message(message, **kwargs)
        
        if exception:
            formatted_msg += f"\nException: {type(exception).__name__}: {str(exception)}"
            formatted_msg += f"\nStack trace:\n{traceback.format_exc()}"
            
        self.logger.critical(formatted_msg)
        
    def log_action(self, action: str, details: str = "", **kwargs):
        """Logger une action utilisateur"""
        msg = f"ACTION: {action}"
        if details:
            msg += f" - {details}"
        self.info(msg, **kwargs)
        
    def log_button_click(self, button_name: str, tab: str = "", **kwargs):
        """Logger un clic de bouton"""
        location = f" dans {tab}" if tab else ""
        self.log_action(f"Clic bouton '{button_name}'{location}", **kwargs)
        
    def log_error_with_context(self, error: Exception, context: str = "", **kwargs):
        """Logger une erreur avec contexte"""
        ctx = f" - Contexte: {context}" if context else ""
        self.error(f"Erreur rencontrée{ctx}", exception=error, **kwargs)
        
    def log_processing_step(self, step: str, progress: float = None, **kwargs):
        """Logger une étape de traitement"""
        msg = f"TRAITEMENT: {step}"
        if progress is not None:
            msg += f" ({progress:.1f}%)"
        self.info(msg, **kwargs)
        
    def _format_message(self, message: str, **kwargs) -> str:
        """Formater le message avec des informations supplémentaires"""
        if kwargs:
            extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
            return f"{message} [{extra_info}]"
        return message
        
    def get_log_file_path(self) -> Path:
        """Obtenir le chemin du fichier de log actuel"""
        return self.log_file
        
    def get_all_log_files(self) -> list[Path]:
        """Obtenir tous les fichiers de log"""
        return list(self.logs_dir.glob("whatsapp_extractor_GUI_*.log"))
        
    def export_logs_archive(self, output_path: Optional[Path] = None) -> Path:
        """Créer une archive avec tous les logs"""
        import zipfile
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"logs_export_{timestamp}.zip")
            
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Ajouter tous les fichiers de log
            for log_file in self.get_all_log_files():
                zf.write(log_file, log_file.name)
                
            # Ajouter les fichiers de configuration
            config_files = [
                Path("config.ini"),
                Path("gui_preferences.json"),
                Path("GUIDE_COMPLET.md")
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    zf.write(config_file, f"config/{config_file.name}")
                    
        self.info(f"Archive de logs créée: {output_path}")
        return output_path
        
    def clean_old_logs(self, keep_days: int = 7):
        """Nettoyer les anciens fichiers de log"""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
        cleaned_count = 0
        
        for log_file in self.get_all_log_files():
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.warning(f"Impossible de supprimer {log_file}: {e}")
                    
        if cleaned_count > 0:
            self.info(f"Nettoyage terminé: {cleaned_count} anciens fichiers de log supprimés")
            
    def set_verbose_mode(self, verbose: bool = True):
        """Activer/désactiver le mode verbose"""
        level = logging.DEBUG if verbose else logging.INFO
        
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, GUILogHandler):
                handler.setLevel(level)
                
        self.info(f"Mode verbose {'activé' if verbose else 'désactivé'}")


# Instance globale du logger
_global_logger: Optional[WhatsAppLogger] = None


def setup_logger(gui_callback=None) -> WhatsAppLogger:
    """Configurer le logger global"""
    global _global_logger
    if _global_logger is None:
        _global_logger = WhatsAppLogger(gui_callback)
    return _global_logger


def get_logger() -> WhatsAppLogger:
    """Obtenir le logger global"""
    global _global_logger
    if _global_logger is None:
        _global_logger = WhatsAppLogger()
    return _global_logger


# Fonctions de convenance
def log_debug(message: str, **kwargs):
    get_logger().debug(message, **kwargs)


def log_info(message: str, **kwargs):
    get_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs):
    get_logger().warning(message, **kwargs)


def log_error(message: str, exception: Optional[Exception] = None, **kwargs):
    get_logger().error(message, exception, **kwargs)


def log_critical(message: str, exception: Optional[Exception] = None, **kwargs):
    get_logger().critical(message, exception, **kwargs)


def log_action(action: str, details: str = "", **kwargs):
    get_logger().log_action(action, details, **kwargs)


def log_button_click(button_name: str, tab: str = "", **kwargs):
    get_logger().log_button_click(button_name, tab, **kwargs)


if __name__ == "__main__":
    # Test du système de logging
    logger = WhatsAppLogger()
    
    logger.info("Test du système de logging")
    logger.debug("Message de debug")
    logger.warning("Message d'avertissement")
    logger.error("Message d'erreur")
    
    try:
        raise ValueError("Test d'exception")
    except Exception as e:
        logger.error("Test d'erreur avec exception", exception=e)
        
    logger.info(f"Fichier de log créé: {logger.get_log_file_path()}")