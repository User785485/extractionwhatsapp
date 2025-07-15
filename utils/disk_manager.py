#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Gestionnaire d'espace disque - WhatsApp Extractor V2
Fournit des fonctions pour vérifier l'espace disque disponible et éviter les saturations
"""

import os
import shutil
import logging
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger('whatsapp_extractor')

def check_disk_space(path: str, min_gb: float = 5.0) -> Tuple[bool, float]:
    """
    Vérifie si l'espace disque disponible est suffisant
    
    Args:
        path: Chemin du disque à vérifier
        min_gb: Minimum d'espace libre requis en GB
        
    Returns:
        Tuple: (suffisant, espace_libre_gb)
    """
    try:
        if not os.path.exists(path):
            path = os.path.dirname(path)
            if not os.path.exists(path):
                logger.error(f"Impossible de vérifier l'espace disque pour: {path}")
                return False, 0
                
        # Obtenir l'usage du disque
        total, used, free = shutil.disk_usage(path)
        
        # Convertir en GB
        free_gb = free / (1024 ** 3)
        
        # Calculer le pourcentage
        free_percent = (free / total) * 100
        
        # Vérification
        if free_gb < min_gb:
            logger.warning(f"Espace disque critique: {free_gb:.2f} GB disponibles (min. {min_gb:.1f} GB)")
            return False, free_gb
            
        # Avertissement si moins de 10%
        if free_percent < 10:
            logger.warning(f"Espace disque faible: {free_percent:.1f}% ({free_gb:.2f} GB) disponibles")
            
        return True, free_gb
        
    except Exception as e:
        logger.error(f"Erreur vérification espace disque: {str(e)}")
        return False, 0

def format_size(size_bytes: int) -> str:
    """
    Formate une taille en octets en unité lisible
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        Taille formatée (ex: '2.5 MB')
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.1f} {units[unit_index]}"

class DiskManager:
    """
    Gestionnaire avancé d'espace disque
    """
    
    def __init__(self, config=None):
        self.config = config
        
        # Configuration par défaut
        self.min_free_gb = 5.0
        self.min_free_percent = 10.0
        self.space_buffer_factor = 1.3
        
        # Charger la configuration si disponible
        if config:
            self.min_free_gb = config.getfloat('DiskSpace', 'min_free_gb', fallback=5.0)
            self.min_free_percent = config.getfloat('DiskSpace', 'min_free_percent', fallback=10.0)
            self.space_buffer_factor = config.getfloat('DiskSpace', 'space_buffer_factor', fallback=1.3)
    
    def check_space_for_operation(self, path: str, required_mb: float) -> bool:
        """
        Vérifie si une opération requérant un certain espace peut être exécutée
        
        Args:
            path: Chemin où l'opération sera effectuée
            required_mb: Espace requis en mégaoctets
            
        Returns:
            Boolean indiquant si l'opération peut être exécutée
        """
        # Convertir MB en GB pour la comparaison
        required_gb = required_mb / 1024
        required_with_buffer = required_gb * self.space_buffer_factor
        
        try:
            # Vérifier si le chemin existe
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Obtenir l'espace disque
            total, used, free = shutil.disk_usage(os.path.dirname(path))
            total_gb = total / (1024 ** 3)
            free_gb = free / (1024 ** 3)
            free_percent = (free_gb / total_gb) * 100
            
            # Vérifier l'espace minimal
            if free_gb < self.min_free_gb:
                logger.error(f"ESPACE DISQUE CRITIQUE: seulement {free_gb:.1f} GB disponibles (min. {self.min_free_gb} GB)")
                return False
                
            # Vérifier le pourcentage minimal
            if free_percent < self.min_free_percent:
                logger.error(f"ESPACE DISQUE CRITIQUE: seulement {free_percent:.1f}% libre (min. {self.min_free_percent}%)")
                return False
                
            # Vérifier l'espace requis pour l'opération
            if required_with_buffer > free_gb:
                logger.error(f"ESPACE INSUFFISANT: {free_gb:.2f} GB disponibles, {required_with_buffer:.2f} GB requis")
                return False
                
            logger.info(f"ESPACE DISQUE OK: {free_gb:.2f} GB disponibles ({free_percent:.1f}%), {required_gb:.2f} GB requis")
            return True
            
        except Exception as e:
            logger.error(f"Erreur vérification espace: {str(e)}")
            return False
    
    def estimate_conversion_size(self, audio_files: List[str]) -> float:
        """
        Estime l'espace nécessaire pour la conversion audio
        
        Returns:
            Taille estimée en MB
        """
        total_size = sum(os.path.getsize(f) for f in audio_files if os.path.exists(f))
        # MP3 est généralement plus petit que l'original, mais on garde une marge
        return (total_size / (1024 * 1024)) * 0.8
    
    def estimate_super_file_size(self, mp3_files: List[str]) -> float:
        """
        Estime l'espace nécessaire pour la création d'un super fichier
        
        Returns:
            Taille estimée en MB
        """
        total_size = sum(os.path.getsize(f) for f in mp3_files if os.path.exists(f))
        # Ajout de 5% pour les métadonnées
        return (total_size / (1024 * 1024)) * 1.05
        
    def cleanup_temp_files(self, path: str, pattern: str = None) -> Tuple[int, float]:
        """
        Nettoie les fichiers temporaires dans un répertoire
        
        Args:
            path: Répertoire à nettoyer
            pattern: Motif de fichier (ex: *.txt)
            
        Returns:
            (nombre_fichiers_supprimés, espace_libéré_mb)
        """
        import fnmatch
        
        if not os.path.exists(path):
            logger.warning(f"Répertoire inexistant pour nettoyage: {path}")
            return 0, 0
            
        files_deleted = 0
        space_freed = 0
        
        for root, dirs, files in os.walk(path):
            for filename in files:
                # Vérifier le motif si spécifié
                if pattern and not fnmatch.fnmatch(filename, pattern):
                    continue
                    
                file_path = os.path.join(root, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    logger.debug(f"Supprimé: {file_path}")
                    
                    files_deleted += 1
                    space_freed += file_size / (1024 * 1024)  # MB
                except OSError as e:
                    logger.error(f"Erreur suppression {file_path}: {str(e)}")
        
        return files_deleted, space_freed