#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de vérification de la configuration des médias
Ce script vérifie que les modifications pour ignorer les médias envoyés sont bien appliquées
et affiche l'état actuel des dossiers
"""

import os
import sys
import logging
import time
from datetime import datetime

def setup_logging():
    """Configure le système de logging"""
    logger = logging.getLogger('media_checker')
    logger.setLevel(logging.INFO)
    
    # Handler console
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
    
    return logger

def check_media_organizer_modification():
    """Vérifie si la modification du MediaOrganizer est appliquée"""
    logger = logging.getLogger('media_checker')
    
    filepath = os.path.join("processors", "media_organizer.py")
    if not os.path.exists(filepath):
        logger.error(f"Fichier {filepath} introuvable!")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le code contient la modification pour ignorer les médias envoyés
    if "# MODIFICATION: Ignorer complètement les médias envoyés" in content and "if direction == 'sent':" in content:
        logger.info("✅ MediaOrganizer correctement modifié pour ignorer les médias envoyés")
        return True
    else:
        logger.error("⚠️ MediaOrganizer n'est PAS modifié pour ignorer les médias envoyés!")
        return False

def get_media_folders_stats(base_dir):
    """Analyse les dossiers de médias et retourne des statistiques"""
    logger = logging.getLogger('media_checker')
    stats = {
        'total_contacts': 0,
        'sent_media_folders': 0,
        'received_media_folders': 0,
        'sent_media_files': 0,
        'received_media_files': 0,
        'sent_media_size': 0,
        'received_media_size': 0,
    }
    
    if not os.path.exists(base_dir):
        logger.error(f"Répertoire de base {base_dir} introuvable!")
        return stats
    
    # Parcourir tous les dossiers de contacts
    for item in os.listdir(base_dir):
        contact_dir = os.path.join(base_dir, item)
        if not os.path.isdir(contact_dir):
            continue
        
        stats['total_contacts'] += 1
        
        # Vérifier les dossiers de médias envoyés
        sent_media_dir = os.path.join(contact_dir, 'media_envoyes')
        if os.path.exists(sent_media_dir):
            stats['sent_media_folders'] += 1
            
            # Compter les fichiers dans les sous-dossiers de types de médias
            for media_type in ['audio', 'images', 'videos', 'documents']:
                media_type_dir = os.path.join(sent_media_dir, media_type)
                if os.path.exists(media_type_dir):
                    for file in os.listdir(media_type_dir):
                        file_path = os.path.join(media_type_dir, file)
                        if os.path.isfile(file_path):
                            stats['sent_media_files'] += 1
                            stats['sent_media_size'] += os.path.getsize(file_path)
        
        # Vérifier les dossiers de médias reçus
        received_media_dir = os.path.join(contact_dir, 'media_recus')
        if os.path.exists(received_media_dir):
            stats['received_media_folders'] += 1
            
            # Compter les fichiers dans les sous-dossiers de types de médias
            for media_type in ['audio', 'images', 'videos', 'documents']:
                media_type_dir = os.path.join(received_media_dir, media_type)
                if os.path.exists(media_type_dir):
                    for file in os.listdir(media_type_dir):
                        file_path = os.path.join(media_type_dir, file)
                        if os.path.isfile(file_path):
                            stats['received_media_files'] += 1
                            stats['received_media_size'] += os.path.getsize(file_path)
    
    return stats

def format_size(size_bytes):
    """Formate une taille en bytes en format lisible"""
    if size_bytes < 1024:
        return f"{size_bytes} o"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} Ko"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} Mo"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} Go"

def main():
    """Point d'entrée principal"""
    logger = setup_logging()
    
    logger.info("="*60)
    logger.info("VÉRIFICATION DE LA CONFIGURATION DES MÉDIAS")
    logger.info("="*60)
    
    # Vérifier la modification du code
    is_modified = check_media_organizer_modification()
    
    # Demander le répertoire à analyser
    base_dir = input("\nEntrez le chemin du dossier client à analyser (laissez vide pour ignorer cette étape): ")
    
    if base_dir and os.path.exists(base_dir):
        logger.info(f"\nAnalyse du dossier: {base_dir}")
        
        # Obtenir les statistiques
        stats = get_media_folders_stats(base_dir)
        
        logger.info("\n--- STATISTIQUES DES MÉDIAS ---")
        logger.info(f"Nombre total de contacts: {stats['total_contacts']}")
        logger.info(f"Dossiers 'media_envoyes': {stats['sent_media_folders']}")
        logger.info(f"Dossiers 'media_recus': {stats['received_media_folders']}")
        logger.info(f"Fichiers médias envoyés: {stats['sent_media_files']} ({format_size(stats['sent_media_size'])})")
        logger.info(f"Fichiers médias reçus: {stats['received_media_files']} ({format_size(stats['received_media_size'])})")
        
        # Si des médias envoyés sont présents dans un dossier déjà traité
        if stats['sent_media_files'] > 0 and is_modified:
            logger.info("\n⚠️ Des médias envoyés sont toujours présents alors que la modification est active.")
            logger.info("👉 Cela signifie que ces médias ont été extraits avant la modification du code.")
            logger.info("👉 Utilisez clean_sent_media.py pour supprimer ces médias envoyés.")
        
        # Si aucun média envoyé n'est présent et la modification est active
        elif stats['sent_media_files'] == 0 and is_modified:
            logger.info("\n✅ Aucun média envoyé n'est présent - La modification fonctionne correctement!")
        
        # Si aucun média envoyé n'est présent mais la modification n'est pas détectée
        elif stats['sent_media_files'] == 0 and not is_modified:
            logger.info("\n❓ Aucun média envoyé n'est présent, mais la modification n'est pas détectée.")
            logger.info("👉 Il est possible que la modification ait été implémentée différemment.")
    
    logger.info("\n--- RECOMMANDATIONS ---")
    if is_modified:
        logger.info("✅ La modification pour ignorer les médias envoyés est correctement implémentée.")
        logger.info("👉 Les futures extractions ne créeront plus de médias envoyés.")
    else:
        logger.info("⚠️ La modification pour ignorer les médias envoyés n'est PAS détectée.")
        logger.info("👉 Vérifiez que le fichier processors/media_organizer.py contient bien le code pour ignorer les médias envoyés.")
    
    logger.info("\n👉 Utilisez clean_sent_media.py pour supprimer les médias envoyés existants.")
    logger.info("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
