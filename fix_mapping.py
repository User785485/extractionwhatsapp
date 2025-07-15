#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de correction des fichiers de mapping des transcriptions corrompus
Ce script identifie et répare les fichiers JSON corrompus dans le dossier des mappings
"""

import os
import json
import shutil
import logging
import sys
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('fix_mapping')

def setup_file_logger(output_dir):
    """Configure un logger qui écrit dans un fichier"""
    log_dir = os.path.join(output_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'fix_mapping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    logger.addHandler(file_handler)
    return log_file

def verify_and_fix_mapping_files(output_dir, auto_fix=True, backup=True):
    """Vérifie et répare les fichiers de mapping JSON corrompus
    
    Args:
        output_dir: Chemin du dossier de sortie principal
        auto_fix: Si True, tente de réparer automatiquement les fichiers corrompus
        backup: Si True, sauvegarde les fichiers avant réparation
    
    Returns:
        Tuple (fichiers_corrompus, fichiers_réparés, échecs)
    """
    mapping_dir = os.path.join(output_dir, '.transcription_mappings')
    if not os.path.exists(mapping_dir):
        logger.error(f"Dossier de mappings non trouvé: {mapping_dir}")
        return [], [], []
    
    logger.info(f"Vérification des fichiers de mapping dans {mapping_dir}")
    
    # Vérifier tous les fichiers de mapping
    corrupted = []
    for file in os.listdir(mapping_dir):
        if file.endswith('_mappings.json'):
            file_path = os.path.join(mapping_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                logger.info(f"✓ Fichier OK: {file}")
            except Exception as e:
                corrupted.append((file, str(e)))
                logger.warning(f"❌ Fichier corrompu: {file} - {str(e)}")
    
    if not corrupted:
        logger.info("Tous les fichiers de mapping sont valides!")
        return [], [], []
    
    logger.info(f"Trouvé {len(corrupted)} fichiers corrompus")
    
    if not auto_fix:
        return corrupted, [], []
    
    # Corriger les fichiers corrompus
    fixed = []
    failed = []
    
    for file, error in corrupted:
        file_path = os.path.join(mapping_dir, file)
        
        # Faire une sauvegarde
        if backup:
            backup_path = f"{file_path}.corrupt.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Sauvegarde de {file} vers {os.path.basename(backup_path)}")
            try:
                shutil.copy2(file_path, backup_path)
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de {file}: {str(e)}")
        
        # Essayer de réparer le fichier
        try:
            logger.info(f"Tentative de réparation de {file}...")
            
            # Lecture du contenu avec gestion des erreurs
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Tenter de corriger les erreurs JSON courantes
                content = content.replace("'", '"')  # Remplacer les guillemets simples
                content = content.replace("\\", "\\\\")  # Échapper les backslashes
                content = content.replace("\n", "\\n")  # Échapper les sauts de ligne
                
                # Essayer de parser le JSON modifié
                try:
                    json_obj = json.loads(content)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(json_obj, f, ensure_ascii=False, indent=2)
                    logger.info(f"✓ Fichier réparé: {file}")
                    fixed.append(file)
                except:
                    logger.warning(f"Impossible de réparer le JSON, création d'un fichier vide pour {file}")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, ensure_ascii=False, indent=2)
                    fixed.append(file)
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du fichier {file}: {str(e)}")
                # Créer un fichier vide si impossible de lire
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
                fixed.append(file)
                
        except Exception as e:
            logger.error(f"Erreur critique lors de la réparation de {file}: {str(e)}")
            failed.append((file, str(e)))
    
    return corrupted, fixed, failed

def main():
    """Point d'entrée principal"""
    # Par défaut, utiliser le dossier standard des exports
    output_dir = "C:\\Datalead3webidu13juillet"
    
    # Permettre de spécifier un dossier différent
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    # Vérifier que le dossier existe
    if not os.path.exists(output_dir):
        logger.error(f"Dossier de sortie non trouvé: {output_dir}")
        return False
    
    # Configurer le logger pour écrire dans un fichier
    log_file = setup_file_logger(output_dir)
    
    # En-tête
    logger.info("="*80)
    logger.info("CORRECTION DES FICHIERS DE MAPPING DES TRANSCRIPTIONS")
    logger.info(f"Dossier cible: {output_dir}")
    logger.info("="*80)
    
    # Vérifier et corriger les fichiers de mapping
    corrupted, fixed, failed = verify_and_fix_mapping_files(output_dir, auto_fix=True, backup=True)
    
    # Résumé
    logger.info("\n" + "="*80)
    logger.info(f"RÉSUMÉ DE LA CORRECTION")
    logger.info(f"- Fichiers corrompus trouvés: {len(corrupted)}")
    logger.info(f"- Fichiers réparés avec succès: {len(fixed)}")
    logger.info(f"- Échecs de réparation: {len(failed)}")
    
    for file, error in failed:
        logger.error(f"Échec de réparation pour {file}: {error}")
    
    logger.info(f"Journal détaillé sauvegardé dans: {log_file}")
    logger.info("="*80)
    
    # Suggérer l'étape suivante
    if corrupted:
        logger.info("\nÉTAPE SUIVANTE RECOMMANDÉE:")
        logger.info("Exécutez le script fix_export_empty.py pour régénérer les exports")
        logger.info("   python fix_export_empty.py")
    
    return len(failed) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
