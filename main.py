#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WhatsApp Extractor V2 - Version optimisée
Module principal pour l'extraction et le traitement des conversations WhatsApp
"""

import os
import sys
import argparse
import logging
import time
from datetime import datetime

# Imports des modules
from config import Config
from utils import setup_logging, check_disk_space, format_size
from core import UnifiedRegistry, FileManager
from processors import HTMLParser, MediaOrganizer, AudioProcessor, Transcriber
from exporters import TextExporter, CSVExporter, TranscriptionMerger, FocusedCSVExporter, SimpleExporter

def main():
    """Point d'entrée principal"""
    start_time = time.time()
    
    # Arguments
    parser = argparse.ArgumentParser(description='WhatsApp Extractor v2 - Version optimisée')
    parser.add_argument('--config', default='config.ini', help='Fichier de configuration')
    parser.add_argument('--mode', choices=['received_only', 'sent_only', 'both'], 
                       help='Mode de traitement')
    parser.add_argument('--no-audio', action='store_true', help='Désactiver la conversion audio')
    parser.add_argument('--no-transcription', action='store_true', help='Désactiver la transcription')
    parser.add_argument('--incremental', action='store_true', help='Mode incrémental')
    parser.add_argument('--full', action='store_true', help='Mode complet (retraiter tout)')
    parser.add_argument('--limit', type=int, help='Limiter le nombre de fichiers/messages (pour tests)
    parser.add_argument('--simple-export', action='store_true', help='Export simple (CSV et TXT avec 2 colonnes seulement)')')
    
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
    
    logger.info(f"Début de l'extraction - Mode: {'complet' if not incremental else 'incrémental'}")
    logger.info(f"Dossier HTML final: {html_dir}")
    logger.info(f"Dossier Média final: {media_dir}")
    
    # Préparation des composants
    registry = UnifiedRegistry(output_dir)
    file_manager = FileManager(output_dir)
    
    # Stocker le dernier mode utilisé
    config.set('User', 'last_mode', 'full' if not incremental else 'incremental')
    config.save()
    
    # Phase 1: Extraction HTML
    logger.info("="*60)
    logger.info("PHASE 1: EXTRACTION HTML")
    logger.info("="*60)
    
    html_parser = HTMLParser(config, registry, file_manager)
    if args.limit:
        # Si une limite est spécifiée, appliquer la limitation
        html_parser.test_limit = args.limit
        
    conversations = html_parser.parse_all_conversations(incremental=incremental)
    
    if not conversations:
        logger.warning("Aucune conversation trouvée ou à traiter.")
        logger.info(f"Temps total d'exécution: {time.time() - start_time:.2f} secondes")
        return 0
    
    logger.info(f"Conversations extraites: {len(conversations)}")
    
    # Pause pour stabiliser le système
    time.sleep(1)
    
    # Phase 2: Organisation des médias
    logger.info("="*60)
    logger.info("PHASE 2: ORGANISATION DES MÉDIAS")
    logger.info("="*60)
    
    media_organizer = MediaOrganizer(config, registry, file_manager)
    media_organizer.organize_media(conversations, media_dir)
    
    # Phase 3: Conversion audio
    if not args.no_audio:
        logger.info("="*60)
        logger.info("PHASE 3: CONVERSION AUDIO")
        logger.info("="*60)
        
        audio_processor = AudioProcessor(config, registry, file_manager)
        # Propagation de la limite si spécifiée
        if args.limit:
            audio_processor.test_limit = args.limit
        audio_processor.process_all_audio(conversations)
    else:
        logger.info("Conversion audio désactivée")
    
    # Phase 4: Transcription
    if not args.no_transcription and not args.no_audio:
        logger.info("="*60)
        logger.info("PHASE 4: TRANSCRIPTION")
        logger.info("="*60)
        
        transcriber = Transcriber(config, registry, file_manager)

        # La classe Transcriber utilise transcribe_all_super_files, pas transcribe_all_audio
        # Note: la limite n'est pas supportée dans la méthode actuelle
        stats = transcriber.transcribe_all_super_files()

        if stats:
            logger.info(f"Transcriptions terminées: {sum(stats.values())} super fichiers transcrits")
        else:
            logger.warning("Aucune transcription effectuée")
    else:
        logger.info("Transcription désactivée")
    
    # Phase 5: Export
    logger.info("="*60)
    logger.info("PHASE 5: EXPORT")
    logger.info("="*60)
    
    # Mode export simple (NOUVEAU)
    if args.simple_export:
        logger.info("Mode export SIMPLE activé")
        simple_exporter = SimpleExporter(config, registry, file_manager)
        success = simple_exporter.export_simple(conversations)
        
        if success:
            logger.info("Export simple terminé avec succès!")
            # Afficher les fichiers créés
            for filename in ['export_simple.csv', 'export_simple.txt', 'export_simple.xlsx']:
                filepath = os.path.join(output_dir, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    logger.info(f"  - {filename}: {format_size(size)}")
        else:
            logger.error("Erreur lors de l'export simple")
    
    # Mode export standard (ANCIEN)
    else:
        # ORDRE CORRIGÉ :
    
    # 1. D'ABORD exporter les textes de base (SANS transcriptions)
    text_exporter = TextExporter(config, registry, file_manager)
    text_exporter.export_all_formats(conversations)
    
    # 2. ENSUITE fusionner avec les transcriptions (crée toutes_conversations_avec_transcriptions.txt)
    merger = TranscriptionMerger(config, registry, file_manager)
    merger.merge_all_transcriptions()
    
    # 3. MAINTENANT exporter les CSV (qui liront le fichier AVEC transcriptions)
    csv_exporter = CSVExporter(config, registry, file_manager)
    csv_exporter.export_special_csv(conversations)
    
    # 4. Exporter CSV focalisé (1 ligne par contact)
    focused_csv_exporter = FocusedCSVExporter(config, registry, file_manager)
    focused_csv_exporter.export_focused_csv(conversations)
    
    # Résumé
    execution_time = time.time() - start_time
    logger.info("="*60)
    logger.info(f"EXTRACTION TERMINÉE - Temps total: {execution_time:.2f} secondes")
    logger.info("="*60)
    
    logger.info("Fichiers importants générés:")
    for file in [
        os.path.join(output_dir, 'all_conversations.txt'),
        os.path.join(output_dir, 'all_transcriptions.txt'),
        os.path.join(output_dir, 'special_export.csv'),
        os.path.join(output_dir, 'messages_recus_par_contact.csv'),
    ]:
        if os.path.exists(file):
            size = os.path.getsize(file)
            logger.info(f"  - {os.path.basename(file)}: {format_size(size)}")
    
    # Récupérer les statistiques de transcription
    total_audios = sum(1 for f in registry.data['files'].values() if f.get('type') == 'audio')
    total_transcribed = len(registry.data['transcriptions'])
    
    if total_audios > 0:
        transcription_rate = (total_transcribed / total_audios) * 100
        logger.info(f"Taux de transcription: {transcription_rate:.1f}% ({total_transcribed}/{total_audios})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())