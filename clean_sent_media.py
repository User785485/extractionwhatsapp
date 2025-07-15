#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de nettoyage des médias envoyés
Ce script parcourt tous les dossiers des contacts et supprime tous les médias envoyés
pour libérer de l'espace disque.
"""

import os
import shutil
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def clean_sent_media(base_dir):
    """
    Supprime tous les dossiers 'media_envoyes' dans chaque dossier de contact
    
    Args:
        base_dir: Chemin du répertoire de base contenant tous les dossiers contacts
    
    Returns:
        tuple: (espace libéré en octets, nombre de dossiers supprimés)
    """
    total_size_freed = 0
    folders_removed = 0
    
    # Vérifier si le répertoire de base existe
    if not os.path.exists(base_dir):
        logger.error(f"Le répertoire {base_dir} n'existe pas!")
        return 0, 0
    
    # Parcourir tous les dossiers du répertoire de base
    logger.info(f"Analyse du répertoire: {base_dir}")
    contact_folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
    logger.info(f"Nombre total de contacts trouvés: {len(contact_folders)}")
    
    # Pour chaque dossier contact
    for contact in contact_folders:
        contact_dir = os.path.join(base_dir, contact)
        sent_media_dir = os.path.join(contact_dir, 'media_envoyes')
        
        # Si le dossier media_envoyes existe
        if os.path.exists(sent_media_dir) and os.path.isdir(sent_media_dir):
            # Calculer la taille du dossier
            folder_size = get_folder_size(sent_media_dir)
            total_size_freed += folder_size
            
            # Supprimer le dossier
            try:
                shutil.rmtree(sent_media_dir)
                folders_removed += 1
                logger.info(f"✓ Supprimé: {contact}/media_envoyes - {format_size(folder_size)}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de {sent_media_dir}: {str(e)}")
    
    return total_size_freed, folders_removed

def get_folder_size(folder_path):
    """Calcule la taille totale d'un dossier en octets"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            file_path = os.path.join(dirpath, f)
            if not os.path.islink(file_path):  # Ignorer les liens symboliques
                total_size += os.path.getsize(file_path)
    return total_size

def format_size(size_bytes):
    """Formate une taille en octets en format lisible (Ko, Mo, Go)"""
    if size_bytes < 1024:
        return f"{size_bytes} octets"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} Ko"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} Mo"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} Go"

if __name__ == "__main__":
    # Répertoire de base contenant tous les dossiers contacts
    base_directory = "C:\\Datalead3webidu13juillet"
    
    # Afficher un message d'information
    print("=" * 80)
    print("SUPPRESSION DES MEDIAS ENVOYES EN COURS")
    print("=" * 80)
    
    # Exécuter le nettoyage directement
    start_time = datetime.now()
    space_freed, folders_deleted = clean_sent_media(base_directory)
    end_time = datetime.now()
    
    # Afficher le résultat
    duration = (end_time - start_time).total_seconds()
    print("\n" + "=" * 80)
    print(f"NETTOYAGE TERMINÉ EN {duration:.2f} SECONDES")
    print(f"- Dossiers supprimés: {folders_deleted}")
    print(f"- Espace libéré: {format_size(space_freed)}")
    print("=" * 80)
