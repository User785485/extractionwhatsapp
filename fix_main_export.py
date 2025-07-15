#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger le problème d'export dans WhatsApp Extractor V2
Ce script remplace la phase d'export défectueuse
"""

import os
import sys
import time
import logging
import shutil
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_export')

def backup_main_enhanced():
    """Fait une sauvegarde du fichier main_enhanced.py original"""
    original = 'main_enhanced.py'
    backup = f'main_enhanced_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
    
    if os.path.exists(original):
        shutil.copy2(original, backup)
        logger.info(f"Sauvegarde créée: {backup}")
        return True
    else:
        logger.error(f"Fichier {original} introuvable!")
        return False

def fix_export_phase():
    """Corrige la phase d'export dans main_enhanced.py"""
    
    # Lire le fichier original
    with open('main_enhanced.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver le début de la Phase 5
    phase5_start = content.find('# Phase 5: Export (toujours exécutée)')
    if phase5_start == -1:
        logger.error("Impossible de trouver la Phase 5 dans le fichier!")
        return False
    
    # Trouver la fin de la Phase 5 (début du résumé ou fin de main)
    resume_start = content.find('# Résumé', phase5_start)
    if resume_start == -1:
        resume_start = content.find('execution_time = time.time() - start_time', phase5_start)
    
    if resume_start == -1:
        logger.error("Impossible de trouver la fin de la Phase 5!")
        return False
    
    # Nouveau code pour la Phase 5
    new_phase5 = '''# Phase 5: Export (toujours exécutée)
    logger.info("="*60)
    logger.info("PHASE 5: EXPORT")
    logger.info("="*60)
    
    # Vérifier si on est en mode export minimal
    if args.minimal_export:
        logger.info("MODE EXPORT MINIMAL ACTIVÉ")
        logger.info("Génération uniquement des exports essentiels (messages reçus avec transcriptions)")
        
        # 1. D'ABORD exporter uniquement les textes des messages reçus
        logger.info("Étape 1/5: Export des textes de messages reçus...")
        text_exporter = TextExporter(config, registry, file_manager)
        text_exporter.export_received_only(conversations)
        
        # Pause pour s'assurer que les fichiers sont écrits
        time.sleep(2)
        
        # 2. ENSUITE fusionner avec les transcriptions
        logger.info("Étape 2/5: Fusion avec les transcriptions...")
        logger.info(f"  - Force-merger: {'OUI' if args.force_merger else 'NON'}")
        merger = TranscriptionMerger(config, registry, file_manager)
        if args.force_merger:
            for target_name in ['toutes_conversations_avec_transcriptions.txt', 'messages_recus_avec_transcriptions.txt']:
                target_file = os.path.join(output_dir, target_name)
                if os.path.exists(target_file):
                    try:
                        os.remove(target_file)
                        logger.info(f"Fichier supprimé pour forcer la régénération: {target_file}")
                    except Exception as e:
                        logger.error(f"Impossible de supprimer {target_file}: {str(e)}")
        merger.merge_all_transcriptions(minimal_export=True)
        
        # Pause pour s'assurer que les fichiers fusionnés sont écrits
        time.sleep(2)
        
        # 3. Vérifier que les fichiers existent avant de continuer
        messages_file = os.path.join(output_dir, 'messages_recus_avec_transcriptions.txt')
        if os.path.exists(messages_file):
            logger.info(f"✓ Fichier de messages créé: {os.path.getsize(messages_file)} octets")
        else:
            logger.error("✗ Fichier de messages manquant!")
        
        # 4. Exporter uniquement le CSV des messages reçus
        logger.info("Étape 3/5: Export CSV des messages reçus...")
        csv_exporter = CSVExporter(config, registry, file_manager)
        csv_exporter.export_special_csv(conversations, received_only=True)
        
        # 5. Exporter CSV simplifié ROBUSTE
        logger.info("Étape 4/5: Export CSV simplifié robuste...")
        robust_exporter = RobustPhoneNameCSVExporter(config, registry, file_manager)
        robust_exporter.export_all_contacts_csv(conversations)
    else:
        # COMPORTEMENT PAR DÉFAUT - ORDRE CORRIGÉ
        
        # 1. D'ABORD exporter les textes de base (SANS transcriptions)
        logger.info("Étape 1/5: Export des textes de base...")
        text_exporter = TextExporter(config, registry, file_manager)
        text_exporter.export_all_formats(conversations)
        
        # Pause importante pour s'assurer que tous les fichiers sont écrits
        time.sleep(2)
        
        # Vérifier que les fichiers sources existent
        source_files = ['toutes_conversations.txt', 'messages_recus.txt']
        for sf in source_files:
            sf_path = os.path.join(output_dir, sf)
            if os.path.exists(sf_path):
                logger.info(f"✓ Fichier source présent: {sf} ({os.path.getsize(sf_path)} octets)")
            else:
                logger.error(f"✗ Fichier source manquant: {sf}")
        
        # 2. ENSUITE fusionner avec les transcriptions
        logger.info("Étape 2/5: Fusion avec les transcriptions...")
        logger.info(f"  - Force-merger: {'OUI' if args.force_merger else 'NON'}")
        merger = TranscriptionMerger(config, registry, file_manager)
        if args.force_merger:
            target_file = os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt')
            if os.path.exists(target_file):
                try:
                    os.remove(target_file)
                    logger.info(f"Fichier supprimé pour forcer la régénération: {target_file}")
                except Exception as e:
                    logger.error(f"Impossible de supprimer {target_file}: {str(e)}")
        merger.merge_all_transcriptions()
        
        # Pause critique pour s'assurer que les fichiers fusionnés sont complètement écrits
        time.sleep(3)
        
        # Vérifier que les fichiers fusionnés existent et ont du contenu
        fused_file = os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt')
        if os.path.exists(fused_file):
            size = os.path.getsize(fused_file)
            logger.info(f"✓ Fichier fusionné créé: {size} octets")
            if size < 1000:
                logger.warning("⚠ Le fichier fusionné semble trop petit!")
        else:
            logger.error("✗ Fichier fusionné manquant!")
        
        # 3. MAINTENANT exporter les CSV (qui liront le fichier AVEC transcriptions)
        logger.info("Étape 3/5: Export CSV standard...")
        csv_exporter = CSVExporter(config, registry, file_manager)
        csv_exporter.export_special_csv(conversations)
        
        # 4. Exporter CSV focalisé (1 ligne par contact)
        logger.info("Étape 4/5: Export CSV focalisé...")
        focused_csv_exporter = FocusedCSVExporter(config, registry, file_manager)
        focused_csv_exporter.export_focused_csv(conversations)
        
        # 5. Exporter CSV simplifié ROBUSTE (indépendant des fichiers fusionnés)
        logger.info("Étape 5/5: Export CSV simplifié robuste...")
        robust_exporter = RobustPhoneNameCSVExporter(config, registry, file_manager)
        robust_exporter.export_all_contacts_csv(conversations)
    
    '''
    
    # Remplacer la phase 5
    new_content = content[:phase5_start] + new_phase5 + content[resume_start:]
    
    # Écrire le fichier corrigé
    with open('main_enhanced.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    logger.info("✓ Phase d'export corrigée avec succès!")
    return True

def main():
    logger.info("=== CORRECTION DU PROBLÈME D'EXPORT ===")
    
    # 1. Faire une sauvegarde
    if not backup_main_enhanced():
        logger.error("Impossible de faire la sauvegarde. Arrêt.")
        return 1
    
    # 2. Appliquer la correction
    if fix_export_phase():
        logger.info("\n✅ CORRECTION APPLIQUÉE AVEC SUCCÈS!")
        logger.info("\nMaintenant, relancez votre script:")
        logger.info("  full bro.bat")
        logger.info("\nOu pour tester uniquement l'export:")
        logger.info("  python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription")
        logger.info("\nPour forcer la régénération des fichiers fusionnés:")
        logger.info("  python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription --force-merger")
    else:
        logger.error("\n❌ La correction a échoué!")
        logger.error("Vérifiez manuellement le fichier main_enhanced.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())