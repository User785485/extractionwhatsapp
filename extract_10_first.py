#!/usr/bin/env python3
"""
Script pour extraire et transcrire les 10 premières conversations WhatsApp
"""

import os
import sys
import glob
from pathlib import Path

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.config_manager import ConfigManager
from parsers.mobiletrans_parser import MobileTransParser
from processors.transcription.whisper_transcriber import WhisperTranscriber
from exporters.csv_exporter import CSVExporter
from exporters.json_exporter import JSONExporter
from utils.logger import setup_logger

def main():
    # Initialiser le logger
    logger = setup_logger('extract_10_first')
    logger.info("Démarrage de l'extraction des 10 premières conversations")
    
    # Charger la configuration
    config = ConfigManager()
    
    # Obtenir les 10 premiers fichiers HTML
    html_dir = config.get('Paths', 'html_dir')
    html_files = glob.glob(os.path.join(html_dir, '*.html'))[:10]
    
    logger.info(f"Trouvé {len(html_files)} fichiers HTML à traiter")
    
    # Initialiser le parser
    parser = MobileTransParser(config)
    
    # Initialiser le transcriber si configuré
    transcriber = None
    if config.get('Processing', 'transcribe_received', fallback='True').lower() == 'true':
        try:
            transcriber = WhisperTranscriber(config)
            logger.info("Transcriber initialisé")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser le transcriber: {e}")
    
    # Traiter chaque fichier
    all_messages = []
    
    for i, html_file in enumerate(html_files, 1):
        contact_name = Path(html_file).stem
        logger.info(f"[{i}/10] Traitement de: {contact_name}")
        
        try:
            # Parser le fichier
            messages = parser.parse_file(html_file)
            
            # Filtrer uniquement les messages reçus
            received_messages = [m for m in messages if m.get('type') == 'received']
            
            logger.info(f"  - {len(received_messages)} messages reçus trouvés")
            
            # Transcrire les messages audio si possible
            if transcriber:
                for msg in received_messages:
                    if msg.get('media_type') == 'audio' and msg.get('media_path'):
                        try:
                            transcription = transcriber.transcribe(msg['media_path'])
                            if transcription:
                                msg['transcription'] = transcription
                                logger.info(f"  - Audio transcrit: {msg.get('media_filename', 'unknown')}")
                        except Exception as e:
                            logger.error(f"  - Erreur transcription: {e}")
            
            all_messages.extend(received_messages)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de {contact_name}: {e}")
    
    logger.info(f"\nTotal: {len(all_messages)} messages reçus extraits")
    
    # Exporter les résultats
    output_dir = config.get('Paths', 'output_dir')
    os.makedirs(output_dir, exist_ok=True)
    
    # Export CSV
    try:
        csv_exporter = CSVExporter(config)
        csv_file = os.path.join(output_dir, '10_premieres_conversations.csv')
        csv_exporter.export(all_messages, csv_file)
        logger.info(f"Export CSV créé: {csv_file}")
    except Exception as e:
        logger.error(f"Erreur export CSV: {e}")
    
    # Export JSON
    try:
        json_exporter = JSONExporter(config)
        json_file = os.path.join(output_dir, '10_premieres_conversations.json')
        json_exporter.export(all_messages, json_file)
        logger.info(f"Export JSON créé: {json_file}")
    except Exception as e:
        logger.error(f"Erreur export JSON: {e}")
    
    # Créer un rapport texte simple
    txt_file = os.path.join(output_dir, '10_premieres_conversations.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("EXTRACTION DES 10 PREMIÈRES CONVERSATIONS WHATSAPP\n")
        f.write("=" * 60 + "\n\n")
        
        # Grouper par contact
        contacts = {}
        for msg in all_messages:
            contact = msg.get('contact', 'Unknown')
            if contact not in contacts:
                contacts[contact] = []
            contacts[contact].append(msg)
        
        for contact, messages in contacts.items():
            f.write(f"\nCONTACT: {contact}\n")
            f.write(f"Messages reçus: {len(messages)}\n")
            f.write("-" * 40 + "\n")
            
            for msg in messages:
                f.write(f"\nDate: {msg.get('timestamp', 'Unknown')}\n")
                
                if msg.get('media_type') == 'audio':
                    f.write(f"Type: Audio ({msg.get('media_filename', 'unknown')})\n")
                    if msg.get('transcription'):
                        f.write(f"Transcription: {msg['transcription']}\n")
                    else:
                        f.write("Transcription: [Non disponible]\n")
                else:
                    f.write(f"Message: {msg.get('content', '')}\n")
                
                f.write("-" * 20 + "\n")
            
            f.write("=" * 60 + "\n")
    
    logger.info(f"Rapport texte créé: {txt_file}")
    logger.info("\nExtraction terminée!")

if __name__ == "__main__":
    main()