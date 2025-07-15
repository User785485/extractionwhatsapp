#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de nettoyage des exports superflus dans les dossiers clients.
Utile après l'activation du mode d'export minimal pour libérer de l'espace disque.

Usage:
    python cleanup_exports.py /chemin/vers/output_dir
    python cleanup_exports.py --dry-run /chemin/vers/output_dir
"""

import os
import sys
import shutil
import argparse
import logging
from datetime import datetime
from typing import List, Tuple

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('export_cleaner')

# Fichiers à conserver (les autres seront supprimés)
FILES_TO_KEEP = [
    'messages_recus.txt',
    'messages_recus_avec_transcriptions.txt',
    'messages_recus_only.csv',
    'messages_recus_only.xlsx'
]

# Répertoires à exclure du nettoyage
EXCLUDE_DIRS = ['.transcription_mappings', '.registry']

def is_export_file(filename: str) -> bool:
    """Détermine si un fichier est un export."""
    export_patterns = [
        'all_conversations.txt', 
        'toutes_conversations.txt',
        'toutes_conversations_avec_transcriptions.txt',
        'tous_messages.txt',
        'tous_messages_avec_transcriptions.txt',
        'messages_all.csv',
        'messages_all.xlsx',
        'transcriptions_speciales.csv'
    ]
    
    return any(pattern in filename for pattern in export_patterns)

def get_files_to_delete(output_dir: str) -> List[Tuple[str, int]]:
    """
    Parcourt les dossiers et identifie les fichiers à supprimer.
    Retourne une liste de tuples (chemin_fichier, taille).
    """
    files_to_delete = []
    total_dirs = 0
    
    # Parcourir le répertoire racine
    for root_item in os.listdir(output_dir):
        full_path = os.path.join(output_dir, root_item)
        
        # Vérifier les fichiers au niveau racine
        if os.path.isfile(full_path):
            if is_export_file(root_item) and root_item not in FILES_TO_KEEP:
                size = os.path.getsize(full_path)
                files_to_delete.append((full_path, size))
                logger.debug(f"Fichier à supprimer: {full_path} ({size} octets)")
        
        # Vérifier les sous-dossiers (contacts)
        elif os.path.isdir(full_path) and root_item not in EXCLUDE_DIRS:
            total_dirs += 1
            
            # Vérifier les fichiers d'export dans les dossiers contact
            for contact_item in os.listdir(full_path):
                contact_file_path = os.path.join(full_path, contact_item)
                
                if os.path.isfile(contact_file_path):
                    # Les seuls fichiers conservés dans les dossiers contact sont messages_recus*.txt
                    if contact_item not in FILES_TO_KEEP and is_export_file(contact_item):
                        size = os.path.getsize(contact_file_path)
                        files_to_delete.append((contact_file_path, size))
                        logger.debug(f"Fichier contact à supprimer: {contact_file_path} ({size} octets)")
    
    logger.info(f"Dossiers analysés: {total_dirs}")
    return files_to_delete

def format_size(size_bytes: int) -> str:
    """Formatte une taille en octets en format lisible."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def delete_files(files_to_delete: List[Tuple[str, int]], dry_run: bool = False) -> int:
    """
    Supprime les fichiers de la liste fournie.
    Si dry_run est True, simule seulement la suppression.
    Retourne la taille totale libérée.
    """
    total_size = sum(size for _, size in files_to_delete)
    
    if dry_run:
        logger.info(f"MODE SIMULATION - Aucun fichier ne sera réellement supprimé")
    
    for file_path, size in files_to_delete:
        try:
            if not dry_run:
                os.remove(file_path)
                logger.info(f"Supprimé: {file_path} ({format_size(size)})")
            else:
                logger.info(f"Simulation - Supprimerait: {file_path} ({format_size(size)})")
        except Exception as e:
            logger.error(f"Erreur suppression {file_path}: {str(e)}")
    
    return total_size

def backup_output_dir(output_dir: str, dry_run: bool = False) -> str:
    """
    Crée une sauvegarde du répertoire avant de procéder au nettoyage.
    Retourne le chemin de la sauvegarde.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"{output_dir}_backup_{timestamp}"
    
    if not dry_run:
        try:
            logger.info(f"Création d'une sauvegarde: {backup_dir}")
            shutil.copytree(output_dir, backup_dir)
            logger.info(f"Sauvegarde terminée avec succès")
            return backup_dir
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
            return ""
    else:
        logger.info(f"Simulation - Créerait une sauvegarde: {backup_dir}")
        return backup_dir

def main():
    """Fonction principale du script."""
    parser = argparse.ArgumentParser(description="Nettoie les exports superflus dans les dossiers clients")
    parser.add_argument('output_dir', help="Répertoire de sortie contenant les dossiers clients")
    parser.add_argument('--dry-run', action='store_true', help="Mode simulation (n'effectue aucune suppression réelle)")
    parser.add_argument('--skip-backup', action='store_true', help="Ne pas créer de sauvegarde avant le nettoyage")
    parser.add_argument('--verbose', action='store_true', help="Afficher les informations détaillées")
    
    args = parser.parse_args()
    
    # Configurer le niveau de logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    output_dir = args.output_dir
    
    # Vérifier que le répertoire existe
    if not os.path.exists(output_dir):
        logger.error(f"Le répertoire {output_dir} n'existe pas")
        return 1
    
    # Créer une sauvegarde si nécessaire
    if not args.skip_backup:
        backup_dir = backup_output_dir(output_dir, args.dry_run)
        if not backup_dir and not args.dry_run:
            logger.error("Impossible de créer une sauvegarde, abandon du nettoyage")
            return 1
    
    # Obtenir la liste des fichiers à supprimer
    files_to_delete = get_files_to_delete(output_dir)
    
    # Afficher un résumé
    logger.info(f"Fichiers à supprimer: {len(files_to_delete)}")
    total_size = sum(size for _, size in files_to_delete)
    logger.info(f"Espace à libérer: {format_size(total_size)}")
    
    # Demander confirmation si ce n'est pas un dry run
    if not args.dry_run and files_to_delete:
        confirmation = input("Voulez-vous supprimer ces fichiers ? (oui/non) ")
        if confirmation.lower() not in ('oui', 'o', 'yes', 'y'):
            logger.info("Nettoyage annulé par l'utilisateur")
            return 0
    
    # Supprimer les fichiers
    freed_space = delete_files(files_to_delete, args.dry_run)
    
    # Afficher le résumé final
    if args.dry_run:
        logger.info(f"SIMULATION terminée: {len(files_to_delete)} fichiers auraient été supprimés")
        logger.info(f"Espace qui aurait été libéré: {format_size(freed_space)}")
    else:
        logger.info(f"Nettoyage terminé: {len(files_to_delete)} fichiers supprimés")
        logger.info(f"Espace libéré: {format_size(freed_space)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
