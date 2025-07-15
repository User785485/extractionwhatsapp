#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de nettoyage d'urgence pour libérer de l'espace disque
Supprime les MP3 intermédiaires qui ont déjà été concaténés en super fichiers
"""

import os
import sys
import shutil
import logging
import argparse
from typing import Dict, List, Tuple

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('disk_cleanup')

def get_disk_usage(path: str) -> Tuple[float, float, float]:
    """
    Récupère l'utilisation du disque pour le chemin spécifié
    
    Args:
        path: Chemin à vérifier
        
    Returns:
        Tuple (total_space_gb, used_space_gb, free_space_gb)
    """
    if not os.path.exists(path):
        logger.warning(f"Chemin inexistant pour vérification disque: {path}")
        path = os.path.dirname(path)
        if not os.path.exists(path):
            logger.error(f"Impossible de vérifier l'espace disque pour: {path}")
            return 0, 0, 0
    
    # Obtenir l'usage du disque
    total, used, free = shutil.disk_usage(path)
    
    # Convertir en GB pour plus de lisibilité
    total_gb = total / (1024 ** 3)
    used_gb = used / (1024 ** 3)
    free_gb = free / (1024 ** 3)
    
    return total_gb, used_gb, free_gb

def clean_intermediate_mp3s(base_dir: str, dry_run: bool = True) -> Tuple[int, float]:
    """
    Nettoie les MP3 intermédiaires lorsqu'un super fichier existe
    
    Args:
        base_dir: Dossier de base des conversations
        dry_run: Si True, simule seulement sans supprimer
        
    Returns:
        (nombre_fichiers_supprimés, espace_libéré_mb)
    """
    total_removed = 0
    total_freed = 0
    
    # Parcourir les répertoires de contacts
    for item in os.listdir(base_dir):
        contact_dir = os.path.join(base_dir, item)
        
        # Ignorer les fichiers ou dossiers spéciaux
        if not os.path.isdir(contact_dir) or item == 'logs':
            continue
            
        # Chemins importants
        super_files_dir = os.path.join(contact_dir, 'SUPER_FICHIERS')
        mp3_dir = os.path.join(contact_dir, 'audio_mp3')
        
        # Vérifier si le contact a des super fichiers
        if os.path.exists(super_files_dir) and os.path.exists(mp3_dir):
            super_files = [f for f in os.listdir(super_files_dir) if f.endswith('.mp3')]
            
            if super_files:
                logger.info(f"Contact {item} a {len(super_files)} super fichiers")
                
                # Si les super fichiers existent, on peut nettoyer les MP3 intermédiaires
                mp3_files = [f for f in os.listdir(mp3_dir) if f.endswith('.mp3')]
                if mp3_files:
                    total_size_mb = 0
                    for mp3_file in mp3_files:
                        file_path = os.path.join(mp3_dir, mp3_file)
                        try:
                            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                            total_size_mb += file_size_mb
                            
                            if dry_run:
                                logger.info(f"[SIMULATION] Suppression: {file_path} ({file_size_mb:.2f} MB)")
                            else:
                                logger.info(f"Suppression: {file_path} ({file_size_mb:.2f} MB)")
                                os.remove(file_path)
                                
                            total_removed += 1
                            total_freed += file_size_mb
                        except OSError as e:
                            logger.error(f"Erreur lors de la suppression de {file_path}: {str(e)}")
                    
                    action = "Simulé" if dry_run else "Supprimé"
                    logger.info(f"{action} {len(mp3_files)} fichiers MP3 intermédiaires ({total_size_mb:.2f} MB) pour {item}")
    
    return total_removed, total_freed

def clean_temp_files(base_dir: str, dry_run: bool = True) -> Tuple[int, float]:
    """
    Nettoie les fichiers temporaires (concaténation, etc.)
    
    Args:
        base_dir: Dossier de base des conversations
        dry_run: Si True, simule seulement sans supprimer
        
    Returns:
        (nombre_fichiers_supprimés, espace_libéré_mb)
    """
    total_removed = 0
    total_freed = 0
    
    # Types de fichiers temporaires à nettoyer
    temp_extensions = ['.txt', '.tmp', '.temp']
    
    # Parcourir tous les fichiers récursivement
    for root, _, files in os.walk(base_dir):
        for file in files:
            # Vérifier si c'est un fichier temporaire
            is_temp = False
            for ext in temp_extensions:
                if file.endswith(ext):
                    is_temp = True
                    break
            
            # Concaténation FFmpeg
            if '.mp3.txt' in file:
                is_temp = True
            
            if is_temp:
                file_path = os.path.join(root, file)
                try:
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    
                    if dry_run:
                        logger.info(f"[SIMULATION] Suppression fichier temporaire: {file_path} ({file_size_mb:.2f} MB)")
                    else:
                        logger.info(f"Suppression fichier temporaire: {file_path} ({file_size_mb:.2f} MB)")
                        os.remove(file_path)
                    
                    total_removed += 1
                    total_freed += file_size_mb
                except OSError as e:
                    logger.error(f"Erreur suppression {file_path}: {str(e)}")
    
    return total_removed, total_freed

def main():
    parser = argparse.ArgumentParser(description="Script de nettoyage d'urgence pour libérer de l'espace disque")
    parser.add_argument('--output-dir', type=str, default=None, help='Dossier de sortie du projet')
    parser.add_argument('--clean-mp3', action='store_true', help='Nettoyer les MP3 intermédiaires')
    parser.add_argument('--clean-temp', action='store_true', help='Nettoyer les fichiers temporaires')
    parser.add_argument('--dry-run', action='store_true', help='Simulation sans suppression réelle')
    
    args = parser.parse_args()
    
    # Détection automatique du dossier de sortie si non spécifié
    if not args.output_dir:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_output = os.path.join(script_dir, 'output')
        if os.path.exists(default_output):
            args.output_dir = default_output
        else:
            # Chercher dans le répertoire parent
            parent_output = os.path.join(os.path.dirname(script_dir), 'output')
            if os.path.exists(parent_output):
                args.output_dir = parent_output
            else:
                args.output_dir = os.path.join(script_dir, 'output')  # Default fallback
    
    # Si aucune option spécifiée, activer les deux par défaut
    if not (args.clean_mp3 or args.clean_temp):
        args.clean_mp3 = True
        args.clean_temp = True
    
    # Afficher l'état initial du disque
    total_gb, used_gb, free_gb = get_disk_usage(args.output_dir)
    logger.info("=" * 50)
    logger.info(f"ESPACE DISQUE INITIAL: {free_gb:.2f} GB libre sur {total_gb:.2f} GB ({(free_gb/total_gb*100):.1f}%)")
    logger.info("=" * 50)
    
    total_files_removed = 0
    total_space_freed = 0
    
    # Mode simulation ou réel
    mode = "SIMULATION" if args.dry_run else "RÉEL"
    logger.info(f"Mode: {mode}")
    
    # Nettoyer les MP3 intermédiaires
    if args.clean_mp3:
        logger.info("NETTOYAGE DES MP3 INTERMÉDIAIRES")
        files_removed, space_freed = clean_intermediate_mp3s(args.output_dir, args.dry_run)
        logger.info(f"MP3 intermédiaires: {files_removed} fichiers, {space_freed:.2f} MB libérés")
        total_files_removed += files_removed
        total_space_freed += space_freed
    
    # Nettoyer les fichiers temporaires
    if args.clean_temp:
        logger.info("NETTOYAGE DES FICHIERS TEMPORAIRES")
        files_removed, space_freed = clean_temp_files(args.output_dir, args.dry_run)
        logger.info(f"Fichiers temporaires: {files_removed} fichiers, {space_freed:.2f} MB libérés")
        total_files_removed += files_removed
        total_space_freed += space_freed
    
    # Afficher le résumé
    logger.info("=" * 50)
    logger.info(f"RÉSUMÉ NETTOYAGE: {total_files_removed} fichiers, {total_space_freed:.2f} MB ({total_space_freed/1024:.2f} GB) libérés")
    
    # Afficher l'état final du disque (seulement si des suppressions réelles ont eu lieu)
    if not args.dry_run:
        final_total_gb, final_used_gb, final_free_gb = get_disk_usage(args.output_dir)
        logger.info(f"ESPACE DISQUE FINAL: {final_free_gb:.2f} GB libre sur {final_total_gb:.2f} GB ({(final_free_gb/final_total_gb*100):.1f}%)")
        logger.info(f"GAIN RÉEL: {final_free_gb - free_gb:.2f} GB")
    
    logger.info("=" * 50)
    
    if args.dry_run:
        logger.info("CECI ÉTAIT UNE SIMULATION. Pour effectuer un nettoyage réel, exécutez sans --dry-run")

if __name__ == "__main__":
    main()
