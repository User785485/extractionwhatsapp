#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de génération directe du CSV à partir du fichier messages_recus_avec_transcriptions.txt
Ce script contourne les problèmes du pipeline en parsant directement le fichier
et en générant un CSV simple avec les colonnes essentielles.
"""

import os
import re
import csv
import logging
import sys
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('direct_csv_export')

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"
SOURCE_FILE = os.path.join(OUTPUT_DIR, "messages_recus_avec_transcriptions.txt")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "messages_recus_only.csv")

def parse_messages_file():
    """Parse le fichier de messages avec transcriptions"""
    if not os.path.exists(SOURCE_FILE):
        logger.error(f"Fichier source introuvable: {SOURCE_FILE}")
        return []
    
    logger.info(f"Lecture du fichier source: {SOURCE_FILE}")
    messages = []
    current_contact = None
    
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Extraire les sections par contact
            contact_sections = re.split(r'\n={30}\nDE: (.+?)\n={30}\n', content)
            
            if len(contact_sections) <= 1:
                logger.warning("Aucune section de contact trouvée dans le fichier")
                return []
            
            # Traiter chaque section (le premier élément est l'en-tête)
            for i in range(1, len(contact_sections), 2):
                if i + 1 < len(contact_sections):
                    contact = contact_sections[i]
                    content = contact_sections[i + 1]
                    
                    # Extraire les messages avec transcriptions
                    message_blocks = content.split("\n\n")
                    
                    for block in message_blocks:
                        if not block.strip():
                            continue
                            
                        # Extraction des informations
                        message = {
                            'contact': contact,
                            'date': '',
                            'time': '',
                            'audio_file': '',
                            'transcription': ''
                        }
                        
                        # Trouver la date et l'heure
                        date_match = re.search(r'\[([\d-]+)\s+([\d:]+)\]', block)
                        if date_match:
                            message['date'] = date_match.group(1)
                            message['time'] = date_match.group(2)
                        
                        # Trouver le fichier audio
                        audio_match = re.search(r'\[AUDIO\]\s+([^\n]+)', block)
                        if audio_match:
                            message['audio_file'] = audio_match.group(1).strip()
                        
                        # Trouver la transcription
                        trans_match = re.search(r'\[TRANSCRIPTION\]\s+([^\n]+)', block)
                        if trans_match:
                            message['transcription'] = trans_match.group(1).strip()
                            
                        # Ajouter le message si on a une transcription
                        if message['transcription']:
                            messages.append(message)
        
        logger.info(f"{len(messages)} messages avec transcriptions trouvés")
        return messages
    except Exception as e:
        logger.error(f"Erreur lors du parsing du fichier: {str(e)}")
        return []

def generate_csv(messages):
    """Génère un fichier CSV à partir des messages parsés"""
    if not messages:
        logger.warning("Aucun message à exporter")
        return False
    
    try:
        logger.info(f"Génération du fichier CSV: {OUTPUT_CSV}")
        with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Date', 'Heure', 'Fichier Audio', 'Transcription'])
            
            # Données
            for msg in messages:
                writer.writerow([
                    msg['contact'],
                    msg['date'],
                    msg['time'],
                    msg['audio_file'],
                    msg['transcription']
                ])
                
        size = os.path.getsize(OUTPUT_CSV)
        logger.info(f"Fichier CSV généré avec succès: {size} octets")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("=" * 50)
    logger.info("GÉNÉRATION DIRECTE DU FICHIER CSV")
    logger.info("=" * 50)
    
    # Vérifier que le fichier source existe
    if not os.path.exists(SOURCE_FILE):
        logger.error(f"Fichier source non trouvé: {SOURCE_FILE}")
        return False
    
    # Afficher la taille du fichier source
    source_size = os.path.getsize(SOURCE_FILE)
    logger.info(f"Fichier source trouvé: {source_size} octets")
    
    if source_size < 1000:  # Moins de 1 Ko
        logger.warning(f"Fichier source anormalement petit: {source_size} octets")
        
    # Parser le fichier et générer le CSV
    messages = parse_messages_file()
    if messages:
        success = generate_csv(messages)
        if success:
            logger.info("Opération terminée avec succès")
            return True
    
    logger.error("Échec de l'opération")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
