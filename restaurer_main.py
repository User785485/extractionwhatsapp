#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour restaurer main.py à son état original sans limitation
Exécuter ce script va créer un fichier main.py non patchée qui permettra 
de traiter l'intégralité des données.
"""

import os
import sys
import shutil
from datetime import datetime

def sauvegarder_main_actuel():
    """Sauvegarde le fichier main.py actuel avec horodatage"""
    main_path = 'main.py'
    if not os.path.exists(main_path):
        print("[ERREUR] main.py introuvable!")
        return False
    
    # Créer une sauvegarde avec horodatage
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'main.py.backup_{timestamp}'
    
    try:
        shutil.copy2(main_path, backup_path)
        print(f"[OK] Sauvegarde créée: {backup_path}")
        return True
    except Exception as e:
        print(f"[ERREUR] Échec de la sauvegarde: {str(e)}")
        return False

def creer_main_clean():
    """Crée un main.py sans les monkey patches de limitation"""
    
    main_content = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
WhatsApp Extractor V2 - Version optimisée
Module principal pour l'extraction et le traitement des conversations WhatsApp
\"\"\"

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
from exporters import TextExporter, CSVExporter, TranscriptionMerger, FocusedCSVExporter

def main():
    \"\"\"Point d'entrée principal\"\"\"
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
        html_dir = r'C:\\Users\\Moham\\Downloads\\iPhone_20250604173341\\WhatsApp'
        logger.warning(f"Aucun chemin HTML valide trouvé! Utilisation de secours: {html_dir}")
    
    if not media_dir:
        media_dir = r'C:\\ProgramData\\Wondershare\\MobileTrans\\ExportMedia\\20250605021808'
        logger.warning(f"Aucun chemin Media valide trouvé! Utilisation de secours: {media_dir}")
    
    logger.info(f"Début de l'extraction - Mode: {'complet' if not incremental else 'incrémental'}")
    logger.info(f"Dossier HTML final: {html_dir}")
    logger.info(f"Dossier Média final: {media_dir}")
    
    # Préparation des composants
    registry = UnifiedRegistry(output_dir)
    file_manager = FileManager(output_dir, html_dir)
    
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
        audio_processor.process_all_audio(incremental=incremental)
    else:
        logger.info("Conversion audio désactivée")
    
    # Phase 4: Transcription
    if not args.no_transcription and not args.no_audio:
        logger.info("="*60)
        logger.info("PHASE 4: TRANSCRIPTION")
        logger.info("="*60)
        
        transcriber = Transcriber(config, registry, file_manager)
        
        # Si une limite est spécifiée, l'appliquer aussi aux transcriptions
        if args.limit:
            logger.info(f"Limitation des transcriptions à {args.limit} éléments")
            transcriber.transcribe_all_audio(incremental=incremental, limit=args.limit)
        else:
            transcriber.transcribe_all_audio(incremental=incremental)
    else:
        logger.info("Transcription désactivée")
    
    # Phase 5: Export
    logger.info("="*60)
    logger.info("PHASE 5: EXPORT")
    logger.info("="*60)
    
    # Exporter texte
    text_exporter = TextExporter(config, registry, file_manager)
    text_exporter.export_all_text(conversations)
    
    # Exporter CSV
    csv_exporter = CSVExporter(config, registry, file_manager)
    csv_exporter.export_special_csv(conversations)
    
    # Nouveau: Exporter CSV focalisé (1 ligne par contact)
    focused_csv_exporter = FocusedCSVExporter(config, registry, file_manager)
    focused_csv_exporter.export_focused_csv(conversations)
    
    # Fusionner les transcriptions
    merger = TranscriptionMerger(config, registry, file_manager)
    merger.merge_all_transcriptions()
    
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
"""
    
    try:
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(main_content)
        print("[OK] Fichier main.py restauré avec succès!")
        return True
    except Exception as e:
        print(f"[ERREUR] Échec de la création du fichier main.py: {str(e)}")
        return False

def creer_batch_complet():
    """Crée un fichier batch spécifique pour le traitement complet"""
    
    batch_content = """@echo off
title WhatsApp Extractor V2 - TRAITEMENT COMPLET
color 0A
cls

echo ============================================================
echo              TRAITEMENT COMPLET DE TOUTES LES DONNÉES
echo ============================================================
echo.
echo Ce script va traiter TOUTES les données WhatsApp sans limite.
echo.

rem Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH.
    echo.
    pause
    exit /b 1
)

echo [1] Mode incrémental (traite uniquement les nouveaux fichiers)
echo [2] Mode complet (retraite tout)
echo.
set /p mode="Choisissez le mode (1-2): "

echo.
echo [1] Avec transcription (utilise l'API)
echo [2] Sans transcription (économie API)
echo.
set /p trans="Avec ou sans transcription (1-2): "

cls
echo ============================================================
echo              TRAITEMENT EN COURS - PATIENTEZ
echo ============================================================

if "%mode%"=="1" (
    if "%trans%"=="1" (
        echo Mode incrémental AVEC transcription...
        python main.py --incremental
    ) else (
        echo Mode incrémental SANS transcription...
        python main.py --incremental --no-transcription
    )
) else (
    if "%trans%"=="1" (
        echo Mode complet AVEC transcription...
        python main.py --full
    ) else (
        echo Mode complet SANS transcription...
        python main.py --full --no-transcription
    )
)

echo.
echo ============================================================
echo              TRAITEMENT TERMINÉ
echo ============================================================
echo.
echo Les fichiers générés sont disponibles dans le dossier de sortie.
echo Notamment: messages_recus_par_contact.csv et messages_recus_par_contact.xlsx
echo.
pause
"""
    
    try:
        with open('traitement_complet.bat', 'w', encoding='utf-8') as f:
            f.write(batch_content)
        print("[OK] Fichier traitement_complet.bat créé!")
        return True
    except Exception as e:
        print(f"[ERREUR] Échec de la création du fichier batch: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print("="*70)
    print("RESTAURATION DU FICHIER MAIN.PY POUR TRAITEMENT COMPLET")
    print("="*70)
    print("Ce script va restaurer main.py à son état original sans limitation")
    print("Une sauvegarde du fichier actuel sera créée avant modification.")
    print()
    
    if sauvegarder_main_actuel():
        if creer_main_clean():
            creer_batch_complet()
            print("\n[SUCCÈS] La restauration est terminée!")
            print("Pour lancer un traitement complet, exécutez: traitement_complet.bat")
    else:
        print("\n[ÉCHEC] La restauration a échoué.")
    
    print("\nAppuyez sur Entrée pour terminer...")
    input()

if __name__ == "__main__":
    main()
