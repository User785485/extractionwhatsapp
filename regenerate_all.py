#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Solution complète pour régénérer tous les fichiers d'export
Ce script résout le problème des transcriptions manquantes en relançant
le pipeline complet avec les bonnes étapes
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def backup_files(output_dir):
    """Crée une sauvegarde des fichiers importants"""
    backup_dir = os.path.join(output_dir, f'backup_{datetime.now().strftime("%Y%m%d%H%M%S")}')
    
    # Créer le dossier de sauvegarde s'il n'existe pas
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Fichiers à sauvegarder
    important_files = [
        'toutes_conversations.txt',
        'toutes_conversations_avec_transcriptions.txt',
        'messages_all.txt',
        'messages_all.csv',
        'messages_recus_only.txt',
        'messages_recus_only.csv'
    ]
    
    for filename in important_files:
        src = os.path.join(output_dir, filename)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, filename)
            try:
                import shutil
                shutil.copy2(src, dst)
                logger.info(f"Fichier sauvegardé: {filename}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de {filename}: {str(e)}")
    
    return backup_dir

def regenerate_pipeline(restart_from_extraction=False):
    """
    Régénère tous les fichiers d'export en relançant le pipeline
    
    Args:
        restart_from_extraction: Si True, relance depuis l'extraction HTML
    """
    output_dir = "C:\\Datalead3webidu13juillet"
    
    # 1. Sauvegarde des fichiers existants
    logger.info("=== SOLUTION COMPLÈTE POUR LES TRANSCRIPTIONS ===")
    backup_dir = backup_files(output_dir)
    logger.info(f"Sauvegarde créée dans: {backup_dir}")
    
    # 2. Déterminer la commande à exécuter
    if restart_from_extraction:
        logger.info("Relance du pipeline COMPLET depuis l'extraction HTML")
        cmd = ["python", "main_enhanced.py", "--full"]
    else:
        logger.info("Relance du pipeline à partir de la phase d'export")
        cmd = [
            "python", 
            "main_enhanced.py", 
            "--skip-extraction", 
            "--skip-media", 
            "--skip-audio", 
            "--skip-transcription",
            "--force-merger"
        ]
    
    # 3. Exécuter la commande
    logger.info(f"Exécution de la commande: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("Régénération réussie!")
        success_msg = (
            "OPERATION REUSSIE\n\n"
            "Le pipeline a ete execute avec succes.\n"
            f"Verifiez les fichiers dans: {output_dir}\n\n"
            "Si les transcriptions n'apparaissent toujours pas correctement, "
            "utilisez l'option --full pour relancer depuis l'extraction HTML:\n"
            "python regenerate_all.py --full"
        )
        print(success_msg)
    else:
        logger.error(f"Erreur lors de la régénération: {result.returncode}")
        logger.error(f"Message d'erreur: {result.stderr}")
        error_msg = (
            "ERREUR DURANT LA REGENERATION\n\n"
            f"Code d'erreur: {result.returncode}\n"
            "Consultez les logs pour plus d'informations."
        )
        print(error_msg)

if __name__ == "__main__":
    # Vérifier les arguments
    full_extraction = "--full" in sys.argv
    
    # Exécuter la régénération
    regenerate_pipeline(restart_from_extraction=full_extraction)
