#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour analyser tous les contacts, y compris ceux avec des prénoms
"""

import os
import sys
import logging
import re
from collections import defaultdict

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('analyze_contacts')

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"

def analyze_contacts():
    """Analyse tous les dossiers de contacts"""
    all_directories = []
    
    for item in os.listdir(OUTPUT_DIR):
        full_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(full_path):
            # Vérifier si c'est un dossier de contact potentiel
            if item.startswith('_') or not any(item.startswith(x) for x in ['messages_', 'conversations_', 'toutes_']):
                all_directories.append(item)
    
    # Séparation entre contacts numériques et nommés
    numeric_contacts = [d for d in all_directories if d.startswith('_')]
    named_contacts = [d for d in all_directories if not d.startswith('_')]
    
    logger.info(f"Total dossiers: {len(all_directories)}")
    logger.info(f"Contacts avec numéro (commençant par '_'): {len(numeric_contacts)}")
    logger.info(f"Contacts avec nom (sans '_'): {len(named_contacts)}")
    
    # Afficher quelques exemples de contacts nommés
    if named_contacts:
        logger.info("\nExemples de contacts avec nom:")
        for i, contact in enumerate(named_contacts[:20]):
            logger.info(f"  {i+1}. {contact}")
        
        if len(named_contacts) > 20:
            logger.info(f"  ...et {len(named_contacts) - 20} autres")
    
    # Analyser la structure des dossiers de contacts nommés
    contact_stats = {}
    
    for contact in named_contacts:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        messages_file = os.path.join(contact_dir, 'messages_recus.txt')
        has_messages = os.path.exists(messages_file)
        
        transcription_dir = os.path.join(contact_dir, 'transcriptions')
        has_transcriptions = os.path.isdir(transcription_dir) and len(os.listdir(transcription_dir)) > 0
        
        contact_stats[contact] = {
            'has_messages': has_messages,
            'has_transcriptions': has_transcriptions
        }
        
        if has_messages:
            try:
                with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Compter les messages audio
                audio_count = content.count('[AUDIO]')
                
                contact_stats[contact]['file_size'] = os.path.getsize(messages_file)
                contact_stats[contact]['audio_count'] = audio_count
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de {contact}: {str(e)}")
    
    # Afficher les statistiques pour les contacts nommés avec des messages
    contacts_with_messages = [c for c, stats in contact_stats.items() if stats['has_messages']]
    contacts_with_audio = [c for c, stats in contact_stats.items() if stats.get('audio_count', 0) > 0]
    contacts_with_transcriptions = [c for c, stats in contact_stats.items() if stats['has_transcriptions']]
    
    logger.info(f"\nContacts nommés avec messages: {len(contacts_with_messages)}")
    logger.info(f"Contacts nommés avec messages audio: {len(contacts_with_audio)}")
    logger.info(f"Contacts nommés avec transcriptions: {len(contacts_with_transcriptions)}")
    
    if contacts_with_audio:
        logger.info("\nContacts nommés avec messages audio:")
        for i, contact in enumerate(contacts_with_audio):
            stats = contact_stats[contact]
            logger.info(f"  {i+1}. {contact}: {stats.get('audio_count', 0)} messages audio")
            
            # Si ce contact a des transcriptions, les lister
            if stats['has_transcriptions']:
                transcription_dir = os.path.join(OUTPUT_DIR, contact, 'transcriptions')
                trans_files = os.listdir(transcription_dir)
                logger.info(f"     - {len(trans_files)} fichiers de transcription")
    
    return numeric_contacts, named_contacts, contact_stats

def extract_uuid_from_filename(filename):
    """Extrait l'UUID du nom de fichier"""
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    match = re.search(uuid_pattern, filename)
    if match:
        return match.group(1)
    return None

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("ANALYSE DE TOUS LES CONTACTS")
    logger.info("="*50)
    
    # Analyser les contacts
    numeric_contacts, named_contacts, contact_stats = analyze_contacts()
    
    # Afficher un résumé
    logger.info("\n=== RÉSUMÉ DE L'ANALYSE ===")
    logger.info(f"Total contacts: {len(numeric_contacts) + len(named_contacts)}")
    logger.info(f"Contacts numériques: {len(numeric_contacts)}")
    logger.info(f"Contacts nommés: {len(named_contacts)}")
    
    return True

if __name__ == "__main__":
    main()
    sys.exit(0)
