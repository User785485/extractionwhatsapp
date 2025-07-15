#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classe de base pour tous les exporters
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class BaseExporter(ABC):
    """Classe de base pour tous les exporters"""
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
        
    @abstractmethod
    def export(self, conversations: Dict[str, List[Dict]], **kwargs) -> bool:
        """Methode abstraite a implementer par chaque exporter"""
        pass
    
    def _ensure_directory(self, directory: str) -> bool:
        """S'assure qu'un repertoire existe"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Impossible de creer le repertoire {directory}: {e}")
            return False
    
    def _write_file_safe(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Ecrit un fichier de maniere securisee"""
        try:
            # Ecrire dans un fichier temporaire d'abord
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Renommer atomiquement
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)
            
            return True
        except Exception as e:
            logger.error(f"Erreur ecriture fichier {file_path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def get_processing_mode(self) -> str:
        """Retourne le mode de traitement configure"""
        return self.config.get('Processing', 'mode', fallback='received_only')
