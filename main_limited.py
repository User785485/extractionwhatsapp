#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Version modifiée de main.py avec support de limite pour les tests
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
from exporters import TextExporter, CSVExporter, TranscriptionMerger

# Monkey patch pour ajouter la limite au HTMLParser
original_init = HTMLParser.__init__
def patched_init(self, config, registry, file_manager, limit=None):
    original_init(self, config, registry, file_manager)
    self.test_limit = limit

HTMLParser.__init__ = patched_init

# Monkey patch parse_all_conversations
original_parse_all = HTMLParser.parse_all_conversations
def limited_parse_all(self, incremental=True):
    if hasattr(self, 'test_limit') and self.test_limit:
        print(f"\n*** MODE TEST: Limite fixée à {self.test_limit} éléments ***\n")
        
    conversations = {}
    html_files = self._get_html_files()
    
    if not html_files:
        return conversations
    
    # Appliquer la limite si définie
    if hasattr(self, 'test_limit') and self.test_limit:
        html_files = html_files[:self.test_limit]
        print(f"Fichiers HTML limités à: {len(html_files)}")
    
    logger = logging.getLogger('whatsapp_extractor')
    logger.info(f"Fichiers HTML trouvés: {len(html_files)}")
    
    for i, html_file in enumerate(html_files):
        if incremental and self.registry.is_file_processed(html_file, 'registered'):
            stored_info = self.registry.data['files'].get(self.registry.get_file_hash(html_file), {})
            if stored_info.get('source_hash') == self.registry.get_file_hash(html_file):
                logger.info(f"Fichier déjà traité et inchangé: {os.path.basename(html_file)}")
                contact = stored_info.get('contact')
                if contact:
                    cached_msgs = self._load_cached_conversation(contact)
                    if cached_msgs:
                        conversations[contact] = cached_msgs
                        continue
        
        logger.info(f"Traitement [{i+1}/{len(html_files)}]: {os.path.basename(html_file)}")
        contact, messages = self.parse_html_file(html_file)
        
        if contact and messages:
            # Limiter aussi les messages si limite définie
            if hasattr(self, 'test_limit') and self.test_limit:
                messages = messages[:self.test_limit]
                print(f"  Messages limités à {len(messages)} pour {contact}")
            conversations[contact] = messages
            self.registry.register_file(
                html_file, 'html', 'source', contact,
                {'source_hash': self.registry.get_file_hash(html_file), 'message_count': len(messages)}
            )
    
    self.registry.save()
    return conversations

HTMLParser.parse_all_conversations = limited_parse_all

def main():
    """Point d'entrée principal avec support de --limit"""
    start_time = time.time()
    
    # Arguments avec --limit ajouté
    parser = argparse.ArgumentParser(description='WhatsApp Extractor v2 - Version optimisée')
    parser.add_argument('--config', default='config.ini', help='Fichier de configuration')
    parser.add_argument('--mode', choices=['received_only', 'sent_only', 'both'], 
                       help='Mode de traitement')
    parser.add_argument('--no-audio', action='store_true', help='Désactiver la conversion audio')
    parser.add_argument('--no-transcription', action='store_true', help='Désactiver la transcription')
    parser.add_argument('--incremental', action='store_true', help='Mode incrémental')
    parser.add_argument('--full', action='store_true', help='Mode complet (retraiter tout)')
    parser.add_argument('--limit', type=int, help='Limiter le nombre de fichiers/messages (pour tests)')
    
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
    
    # Le reste du code reste identique...
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
        output_dir = os.path.join(os.path.expanduser('~'), 'Desktop', 'Data Leads')
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
    logger.info(f"Dossier de sortie final: {output_dir}")
    logger.info(f"Mode: {config.get('Processing', 'mode', fallback='received_only')}")
    logger.info(f"Incrémental: {incremental}")
    logger.info(f"Conversion audio: {'Non' if args.no_audio else 'Oui'}")
    logger.info(f"Transcription: {'Non' if args.no_transcription else 'Oui'}")
    
    try:
        registry = UnifiedRegistry(output_dir)
        file_manager = FileManager(output_dir)
        
        # Phase 1: Extraction HTML avec limite
        logger.info("\n" + "="*40)
        logger.info("PHASE 1/4: EXTRACTION DES CONVERSATIONS")
        logger.info("="*40)
        
        # Passer la limite au parser
        parser = HTMLParser(config, registry, file_manager, limit=args.limit)
        conversations = parser.parse_all_conversations(incremental)
        
        if not conversations:
            logger.error("Aucune conversation extraite")
            return 1
        
        logger.info(f"[OK] {len(conversations)} conversations extraites")
        
        # Phase 2: Traitement audio
        if not args.no_audio:
            logger.info("\n" + "="*40)
            logger.info("PHASE 2/4: TRAITEMENT AUDIO")
            logger.info("="*40)
            
            audio_processor = AudioProcessor(config, registry, file_manager)
            audio_stats = audio_processor.process_all_audio(conversations)
            
            total_converted = sum(s['converted'] for s in audio_stats.values())
            total_super = sum(s['super_files'] for s in audio_stats.values())
            logger.info(f"[OK] {total_converted} fichiers convertis, {total_super} super fichiers créés")
        
        # Phase 3: Transcription
        if not args.no_transcription and config.get('API', 'openai_key'):
            logger.info("\n" + "="*40)
            logger.info("PHASE 3/4: TRANSCRIPTION")
            logger.info("="*40)
            
            transcriber = Transcriber(config, registry, file_manager)
            trans_stats = transcriber.transcribe_all_super_files()
            
            total_transcribed = sum(trans_stats.values())
            logger.info(f"[OK] {total_transcribed} fichiers transcrits")
        
        # Phase 4: Export
        logger.info("\n" + "="*40)
        logger.info("PHASE 4/4: GÉNÉRATION DES EXPORTS")
        logger.info("="*40)
        
        text_exporter = TextExporter(config, registry, file_manager)
        text_exporter.export_all_formats(conversations)
        
        csv_exporter = CSVExporter(config, registry, file_manager)
        csv_exporter.export_special_csv(conversations)
        
        merger = TranscriptionMerger(config, registry, file_manager)
        merger.merge_all_transcriptions()
        
        logger.info("[OK] Tous les exports générés")
        
        elapsed = time.time() - start_time
        logger.info("\n" + "="*60)
        logger.info(f"TRAITEMENT TERMINÉ EN {elapsed:.1f} SECONDES")
        logger.info("="*60)
        logger.info(f"Résultats disponibles dans: {output_dir}")
        
        important_files = [
            'transcriptions_speciales.csv',
            'toutes_conversations_avec_transcriptions.txt',
            'messages_recus_avec_transcriptions.txt'
        ]
        
        logger.info("\nFichiers principaux générés:")
        for file in important_files:
            file_path = os.path.join(output_dir, file)
            if os.path.exists(file_path):
                size = format_size(os.path.getsize(file_path))
                logger.info(f"  [OK] {file} ({size})")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nInterrompu par l'utilisateur")
        return 0
    except Exception as e:
        logger.error(f"ERREUR FATALE: {str(e)}")
        logger.exception("Détails:")
        return 1

if __name__ == "__main__":
    sys.exit(main())
