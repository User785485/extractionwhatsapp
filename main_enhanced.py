#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WhatsApp Extractor V2 - Version améliorée avec options pour sauter des étapes
Ce script permet de commencer le traitement à différentes étapes du pipeline
"""

import os
import sys
import argparse
import logging
import time
import shutil
from datetime import datetime

# Imports des modules
from config import Config
from utils import setup_logging, check_disk_space, format_size
from core import UnifiedRegistry, FileManager
from processors import HTMLParser, MediaOrganizer, AudioProcessor, Transcriber
from exporters.merger import TranscriptionMerger
from exporters.text_exporter import TextExporter
from exporters.csv_exporter import CSVExporter
from exporters.focused_csv_exporter import FocusedCSVExporter
from exporters.robust_exporter import RobustPhoneNameCSVExporter

def main():
    """Point d'entrée principal avec options pour sauter des étapes"""
    start_time = time.time()
    
    # Arguments
    parser = argparse.ArgumentParser(description='WhatsApp Extractor v2 - Version améliorée')
    parser.add_argument('--config', default='config.ini', help='Fichier de configuration')
    parser.add_argument('--mode', choices=['received_only', 'sent_only', 'both'], 
                       help='Mode de traitement')
    parser.add_argument('--no-audio', action='store_true', help='Désactiver la conversion audio')
    parser.add_argument('--no-transcription', action='store_true', help='Désactiver la transcription')
    parser.add_argument('--incremental', action='store_true', help='Mode incrémental')
    parser.add_argument('--full', action='store_true', help='Mode complet (retraiter tout)')
    parser.add_argument('--limit', type=int, help='Limiter le nombre de fichiers/messages (pour tests)')
    
    # NOUVELLES OPTIONS
    parser.add_argument('--skip-extraction', action='store_true', help='Sauter l\'extraction HTML')
    parser.add_argument('--skip-media', action='store_true', help='Sauter l\'organisation des médias')
    parser.add_argument('--skip-audio', action='store_true', help='Sauter la conversion audio')
    parser.add_argument('--skip-transcription', action='store_true', help='Sauter la transcription')
    parser.add_argument('--force-merger', action='store_true', help='Forcer la régénération des fichiers fusionnés avec transcriptions')
    parser.add_argument('--minimal-export', action='store_true', help='Mode export minimal : uniquement TXT et CSV des messages reçus avec transcriptions')
    
    args = parser.parse_args()
    
    # Configuration
    config = Config(args.config)
    
    if args.mode:
        config.set('Processing', 'mode', args.mode)
    
    incremental = True
    if args.full:
        incremental = False
    elif args.incremental:
        incremental = True
    
    # Setup logging
    logger = setup_logging(config)
    
    # Si limite spécifiée, l'afficher clairement
    if args.limit:
        logger.info(f"*** MODE TEST ACTIVÉ: Limite fixée à {args.limit} éléments ***")
    
    # Déterminer les chemins
    output_dir = None
    
    if hasattr(config, 'get_paths'):
        try:
            paths = config.get_paths()
            output_dir = paths.get('output_dir')
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation de get_paths(): {str(e)}")
    
    if not output_dir:
        for section in ['PATHS', 'Paths', 'paths']:
            try:
                temp_dir = config.get(section, 'output_dir')
                if temp_dir:
                    output_dir = temp_dir
                    break
            except Exception:
                continue
    
    if not output_dir:
        output_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'DataLeads')
        logger.warning(f"Aucun chemin de sortie valide trouvé! Utilisation de secours: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    has_space, free_gb = check_disk_space(output_dir, 5.0)
    if not has_space:
        logger.warning(f"Espace disque faible: {free_gb:.2f} GB disponibles")
    
    logger.info("="*60)
    logger.info("WHATSAPP EXTRACTOR V2 - DÉMARRAGE")
    logger.info("="*60)
    
    html_dir = None
    media_dir = None
    
    if hasattr(config, 'get_paths'):
        try:
            paths = config.get_paths()
            html_dir = paths.get('html_dir')
            media_dir = paths.get('media_dir')
        except Exception as e:
            logger.error(f"Erreur lors de l'utilisation de get_paths(): {str(e)}")
    
    for path_name, path_var in [('html_dir', html_dir), ('media_dir', media_dir)]:
        if not path_var:
            for section in ['PATHS', 'Paths', 'paths']:
                try:
                    temp_path = config.get(section, path_name)
                    if temp_path and path_name == 'html_dir':
                        html_dir = temp_path
                        break
                    elif temp_path and path_name == 'media_dir':
                        media_dir = temp_path
                        break
                except Exception:
                    continue
    
    if not html_dir:
        html_dir = r'C:\Users\Moham\Downloads\iPhone_20250604173341\WhatsApp'
        logger.warning(f"Aucun chemin HTML valide trouvé! Utilisation de secours: {html_dir}")
    
    if not media_dir:
        media_dir = r'C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250605021808'
        logger.warning(f"Aucun chemin Media valide trouvé! Utilisation de secours: {media_dir}")
    
    # Afficher les étapes qui vont être exécutées
    logger.info(f"Début de l'extraction - Mode: {'complet' if not incremental else 'incrémental'}")
    logger.info("Étapes qui seront exécutées:")
    logger.info(f"  - Extraction HTML: {'NON' if args.skip_extraction else 'OUI'}")
    logger.info(f"  - Organisation médias: {'NON' if args.skip_media else 'OUI'}")
    logger.info(f"  - Conversion audio: {'NON' if args.skip_audio or args.no_audio else 'OUI'}")
    logger.info(f"  - Transcription: {'NON' if args.skip_transcription or args.no_transcription else 'OUI'}")
    logger.info(f"  - Export: OUI (toujours exécuté)")
    
    logger.info(f"Dossier HTML final: {html_dir}")
    logger.info(f"Dossier Média final: {media_dir}")
    
    # Préparation des composants
    registry = UnifiedRegistry(output_dir)
    file_manager = FileManager(output_dir)
    
    # Stocker le dernier mode utilisé
    config.set('User', 'last_mode', 'full' if not incremental else 'incremental')
    config.save()
    
    # Variable pour stocker les conversations
    conversations = {}
    
    # Phase 1: Extraction HTML (à moins qu'on la saute)
    if not args.skip_extraction:
        logger.info("="*60)
        logger.info("PHASE 1: EXTRACTION HTML")
        logger.info("="*60)
        
        html_parser = HTMLParser(config, registry, file_manager)
        if args.limit:
            html_parser.test_limit = args.limit
            
        conversations = html_parser.parse_all_conversations(incremental=incremental)
        
        if not conversations:
            logger.warning("Aucune conversation trouvée ou à traiter.")
            logger.info(f"Temps total d'exécution: {time.time() - start_time:.2f} secondes")
            return 0
        
        logger.info(f"Conversations extraites: {len(conversations)}")
        
        # Pause pour stabiliser le système
        time.sleep(1)
    else:
        logger.info("="*60)
        logger.info("PHASE 1: EXTRACTION HTML [SAUTÉE]")
        logger.info("="*60)
        # Charger les conversations depuis le registre si elles existent
        if 'conversations' in registry.data:
            conversations = registry.data['conversations']
            logger.info(f"Conversations chargées depuis le registre: {len(conversations)}")
        else:
            logger.warning("Aucune conversation trouvée dans le registre. Certaines fonctionnalités peuvent être limitées.")
    
    # Phase 2: Organisation des médias (à moins qu'on la saute)
    if not args.skip_media and not args.skip_extraction:
        logger.info("="*60)
        logger.info("PHASE 2: ORGANISATION DES MÉDIAS")
        logger.info("="*60)
        
        media_organizer = MediaOrganizer(config, registry, file_manager)
        media_organizer.organize_media(conversations, media_dir)
    else:
        logger.info("="*60)
        logger.info("PHASE 2: ORGANISATION DES MÉDIAS [SAUTÉE]")
        logger.info("="*60)
    
    # Phase 3: Conversion audio (à moins qu'on la saute)
    if not args.skip_audio and not args.no_audio:
        logger.info("="*60)
        logger.info("PHASE 3: CONVERSION AUDIO")
        logger.info("="*60)
        
        audio_processor = AudioProcessor(config, registry, file_manager)
        # Propagation de la limite si spécifiée
        if args.limit:
            audio_processor.test_limit = args.limit
        audio_processor.process_all_audio(conversations)
    else:
        logger.info("="*60)
        logger.info("PHASE 3: CONVERSION AUDIO [SAUTÉE]")
        logger.info("="*60)
    
    # Phase 4: Transcription (à moins qu'on la saute)
    if not args.skip_transcription and not args.no_transcription:
        logger.info("="*60)
        logger.info("PHASE 4: TRANSCRIPTION")
        logger.info("="*60)
        
        transcriber = Transcriber(config, registry, file_manager)

        stats = transcriber.transcribe_all_super_files()

        if stats:
            logger.info(f"Transcriptions terminées: {sum(stats.values())} super fichiers transcrits")
        else:
            logger.warning("Aucune transcription effectuée")
    else:
        logger.info("="*60)
        logger.info("PHASE 4: TRANSCRIPTION [SAUTÉE]")
        logger.info("="*60)
    
    # Phase 5: Export (toujours exécutée)
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
    
    # Résumé
    execution_time = time.time() - start_time
    logger.info("="*60)
    logger.info(f"EXTRACTION TERMINÉE - Temps total: {execution_time:.2f} secondes")
    logger.info("="*60)
    
    logger.info("Fichiers importants générés:")
    # Liste des fichiers à vérifier en fonction du mode d'export
    if args.minimal_export:
        important_files = [
            os.path.join(output_dir, 'messages_recus.txt'),
            os.path.join(output_dir, 'messages_recus_avec_transcriptions.txt'),
            os.path.join(output_dir, 'messages_recus_only.csv'),
            os.path.join(output_dir, 'contacts_messages_simplifies.csv')
        ]
    else:
        important_files = [
            os.path.join(output_dir, 'all_conversations.txt'),
            os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt'),
            os.path.join(output_dir, 'messages_recus_only.csv'),
            os.path.join(output_dir, 'messages_all.csv'),
            os.path.join(output_dir, 'messages_recus_par_contact.csv'),
            os.path.join(output_dir, 'contacts_messages_simplifies.csv'),
        ]
    
    for file in important_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            logger.info(f"  - {os.path.basename(file)}: {format_size(size)}")
    
    # Récupérer les statistiques de transcription
    total_audios = sum(1 for f in registry.data.get('files', {}).values() if f.get('type') == 'audio')
    total_transcribed = len(registry.data.get('transcriptions', {}))
    
    if total_audios > 0:
        transcription_rate = (total_transcribed / total_audios) * 100
        logger.info(f"Taux de transcription: {transcription_rate:.1f}% ({total_transcribed}/{total_audios})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
