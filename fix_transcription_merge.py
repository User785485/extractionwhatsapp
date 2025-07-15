#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de correction pour le problème de transcription "unknown"
Ce script améliore le TranscriptionMerger pour qu'il puisse mieux faire correspondre
les fichiers audio dans la conversation avec leurs transcriptions existantes.
"""

import os
import re
import shutil
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger()

def backup_file(file_path):
    """Crée une sauvegarde du fichier avec horodatage"""
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return False
    
    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Sauvegarde créée: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
        return False

def fix_find_transcription_exact(merger_file):
    """Améliore la méthode _find_transcription_exact pour mieux gérer les différences de format"""
    
    if not os.path.exists(merger_file):
        logger.error(f"Fichier merger.py non trouvé: {merger_file}")
        return False
    
    # Créer une sauvegarde
    if not backup_file(merger_file):
        logger.error("Impossible de créer une sauvegarde, abandon")
        return False
    
    try:
        with open(merger_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Amélioration: Ajouter une nouvelle stratégie pour faire correspondre les fichiers
        # avec seulement l'UUID même si le format de nom est différent
        
        # Position où insérer la nouvelle stratégie (juste avant STRATEGIE 4)
        pattern = r'# STRATEGIE 4: Recherche par hash dans le registre'
        if re.search(pattern, content):
            # Création de la nouvelle stratégie
            new_strategy = """
        # NOUVELLE STRATEGIE (3.5): Correspondance par UUID pur
        # Cette stratégie extrait l'UUID du nom du fichier audio et cherche
        # dans tous les mappings s'il existe une transcription avec cet UUID
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_name)
        if uuid_match:
            uuid = uuid_match.group(1)
            logger.debug(f"Recherche par UUID pur: {uuid}")
            
            # Parcourir tous les contacts et leurs mappings
            for contact_name, contact_maps in self.transcription_mappings.items():
                for mp3_name, data in contact_maps.items():
                    if uuid in mp3_name:
                        transcription = data.get('transcription', '')
                        if transcription and len(transcription) > 10:
                            logger.info(f"Correspondance par UUID pur trouvée: {uuid} dans {mp3_name}")
                            return transcription
        
        """
            # Insérer la nouvelle stratégie
            content = re.sub(pattern, new_strategy + pattern, content)
            
            # Écrire le fichier modifié
            with open(merger_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Fichier {os.path.basename(merger_file)} modifié avec succès!")
            logger.info("La nouvelle stratégie de correspondance par UUID pur a été ajoutée.")
            return True
        else:
            logger.error("Pattern d'insertion non trouvé dans le fichier")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification: {str(e)}")
        return False

def main():
    """Fonction principale"""
    logger.info("=== CORRECTION DU PROBLÈME DE TRANSCRIPTION UNKNOWN ===")
    
    # Chemin du fichier merger.py
    merger_file = os.path.join(os.getcwd(), "exporters", "merger.py")
    
    logger.info(f"Tentative d'amélioration du fichier: {merger_file}")
    
    if fix_find_transcription_exact(merger_file):
        logger.info("Correction réussie!")
        logger.info("\nPour appliquer les modifications:")
        logger.info("1. Lancez 'FULL BRO.bat'")
        logger.info("2. Choisissez l'option 4 (Uniquement l'EXPORT)")
        logger.info("\nCela va régénérer les fichiers d'export avec les transcriptions correctement fusionnées.")
    else:
        logger.error("La correction a échoué. Vérifiez les logs ci-dessus.")
    
    logger.info("=== FIN DE LA CORRECTION ===")

if __name__ == "__main__":
    main()
