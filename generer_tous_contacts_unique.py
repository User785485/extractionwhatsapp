#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour générer un CSV unique avec TOUS les contacts (numéros ET prénoms)
"""

import os
import re
import csv
import shutil
import logging
import sys
from datetime import datetime
from collections import defaultdict

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('tous_contacts_unique')

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"

def list_all_contact_folders():
    """Liste tous les dossiers de contact, y compris ceux avec des prénoms"""
    all_folders = []
    
    for item in os.listdir(OUTPUT_DIR):
        full_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(full_path):
            # Vérifier si c'est un dossier de contact potentiel
            if item.startswith('_') or not any(item.startswith(x) for x in ['messages_', 'conversations_', 'toutes_']):
                all_folders.append(item)
    
    # Séparation des contacts par type
    numeric_contacts = [c for c in all_folders if c.startswith('_')]
    named_contacts = [c for c in all_folders if not c.startswith('_')]
    
    logger.info(f"Trouvé {len(all_folders)} dossiers de contact au total")
    logger.info(f" - Contacts avec numéro: {len(numeric_contacts)}")
    logger.info(f" - Contacts avec prénom: {len(named_contacts)}")
    
    return all_folders

def extract_uuid_from_filename(filename):
    """Extrait l'UUID du nom de fichier"""
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    match = re.search(uuid_pattern, filename)
    if match:
        return match.group(1)
    return None

def read_transcription_file(file_path):
    """Lit un fichier de transcription et extrait le contenu"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extraire la transcription réelle (après les ===)
        parts = content.split('='*10)
        if len(parts) >= 2:
            return parts[-1].strip()
        return content
    except Exception as e:
        logger.error(f"Erreur lecture transcription {file_path}: {str(e)}")
        return ""

def create_transcription_mapping():
    """Crée un mapping des transcriptions par UUID pour tous les contacts"""
    transcription_mapping = {}
    contact_folders = list_all_contact_folders()
    
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        transcription_dir = os.path.join(contact_dir, 'transcriptions')
        
        if not os.path.isdir(transcription_dir):
            continue
        
        trans_count = 0
        for file in os.listdir(transcription_dir):
            if file.endswith('.txt'):
                full_path = os.path.join(transcription_dir, file)
                uuid = extract_uuid_from_filename(file)
                if uuid:
                    transcription = read_transcription_file(full_path)
                    transcription_mapping[uuid] = {
                        'contact': contact,
                        'file': file,
                        'content': transcription
                    }
                    trans_count += 1
        
        if trans_count > 0:
            logger.info(f"Contact {contact}: {trans_count} transcriptions")
    
    logger.info(f"Mapping de transcription créé pour {len(transcription_mapping)} UUIDs")
    return transcription_mapping

def extract_all_messages_by_contact():
    """Extrait tous les messages par contact"""
    all_messages = defaultdict(list)
    contact_folders = list_all_contact_folders()
    
    # Créer le mapping des transcriptions
    transcription_mapping = create_transcription_mapping()
    
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        messages_file = os.path.join(contact_dir, 'messages_recus.txt')
        
        if not os.path.exists(messages_file):
            # Assurer que chaque contact est au moins présent dans le dictionnaire
            all_messages[contact] = []
            continue
        
        try:
            with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extraire la partie pertinente (après les en-têtes)
            parts = content.split('='*20)
            if len(parts) > 1:
                content = parts[-1].strip()
            
            # Extraire les messages individuels
            lines = content.split('\n')
            
            # Regrouper les lignes en messages
            current_message = None
            message_buffer = []
            
            for line in lines:
                # Nouvelle ligne de message - FORMAT: [YYYY/MM/DD HH:MM]
                if re.match(r'^\[([\d/]+)\s+([\d:]+)\]', line):
                    # Enregistrer le message précédent s'il existe
                    if current_message:
                        all_messages[contact].append(current_message)
                    
                    # Extraire la date et l'heure
                    date_match = re.match(r'^\[([\d/]+)\s+([\d:]+)\]', line)
                    date = date_match.group(1)
                    time = date_match.group(2)
                    
                    # Vérifier si c'est un message audio
                    is_audio = '[AUDIO]' in line
                    audio_file = ""
                    uuid = None
                    
                    if is_audio:
                        audio_match = re.search(r'\[AUDIO\]\s+([^\n\[\]]+)', line)
                        if audio_match:
                            audio_file = audio_match.group(1).strip()
                            uuid = extract_uuid_from_filename(audio_file)
                    
                    # Créer un nouveau message
                    current_message = {
                        'contact': contact,
                        'date': date,
                        'time': time,
                        'content': line,
                        'is_audio': is_audio,
                        'audio_file': audio_file,
                        'uuid': uuid,
                        'has_transcription': False,
                        'transcription': ''
                    }
                    
                    # Vérifier si une transcription existe pour ce UUID
                    if uuid and uuid in transcription_mapping:
                        current_message['has_transcription'] = True
                        current_message['transcription'] = transcription_mapping[uuid]['content']
                    
                    message_buffer = [line]
                # Ligne supplémentaire du même message
                elif line.strip() and current_message:
                    message_buffer.append(line)
                    current_message['content'] = '\n'.join(message_buffer)
            
            # Ajouter le dernier message s'il existe
            if current_message:
                all_messages[contact].append(current_message)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des messages pour {contact}: {str(e)}")
    
    return all_messages

def generate_complete_unique_csv(all_messages):
    """Génère un CSV unique contenant tous les contacts (numériques et prénoms)"""
    output_csv = os.path.join(OUTPUT_DIR, "TOUS_CONTACTS_NUMERIQUES_ET_PRENOMS.csv")
    
    try:
        logger.info(f"Génération du fichier CSV unique: {output_csv}")
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Type de contact', 'Nombre de messages', 'Messages reçus', 
                           'Nombre messages audio', 'Nombre messages avec transcription'])
            
            # Une ligne par contact
            for contact, messages in all_messages.items():
                # Déterminer le type de contact
                contact_type = "Numéro" if contact.startswith('_') else "Prénom"
                
                # Compter les types de messages
                audio_count = sum(1 for m in messages if m['is_audio'])
                trans_count = sum(1 for m in messages if m['has_transcription'])
                
                # Fusionner tous les messages en texte
                merged_messages = []
                for m in messages:
                    date = m['date']
                    time = m['time']
                    content = m['content']
                    
                    if m['is_audio']:
                        msg_type = "AUDIO"
                        content_text = re.sub(r'\[AUDIO\]\s+[^\n]+', '', content).strip()
                        
                        if m['has_transcription']:
                            merged_msg = f"[{date} {time}] {msg_type}: {content_text}\nTRANSCRIPTION: {m['transcription']}"
                        else:
                            merged_msg = f"[{date} {time}] {msg_type}: {content_text}"
                    else:
                        msg_type = "TEXTE"
                        content_text = re.sub(r'^\[([\d/]+)\s+([\d:]+)\]\s*←?\s*', '', content).strip()
                        merged_msg = f"[{date} {time}] {msg_type}: {content_text}"
                            
                    merged_messages.append(merged_msg)
                
                # Joindre tous les messages avec séparateur
                all_messages_text = "\n\n".join(merged_messages) if merged_messages else ""
                
                writer.writerow([
                    contact,
                    contact_type,
                    len(messages),
                    all_messages_text,
                    audio_count,
                    trans_count
                ])
        
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV unique créé: {output_csv} ({size} octets)")
        return True, size
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV unique: {str(e)}")
        return False, 0

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("GÉNÉRATION CSV UNIQUE - TOUS CONTACTS (NUMÉRIQUES ET PRÉNOMS)")
    logger.info("="*50)
    
    # 1. Extraire tous les messages par contact
    logger.info("\n=== ÉTAPE 1: EXTRACTION DE TOUS LES MESSAGES PAR CONTACT ===")
    all_messages = extract_all_messages_by_contact()
    
    # 2. Générer le fichier CSV unique
    logger.info("\n=== ÉTAPE 2: GÉNÉRATION DU FICHIER CSV UNIQUE ===")
    success, size = generate_complete_unique_csv(all_messages)
    
    if success:
        logger.info("\n===== GÉNÉRATION TERMINÉE AVEC SUCCÈS =====")
        logger.info(f"Fichier généré: TOUS_CONTACTS_NUMERIQUES_ET_PRENOMS.csv ({size} octets)")
        logger.info(f"Emplacement: {OUTPUT_DIR}")
        
        # Compter les types de contacts
        numeric_contacts = sum(1 for c in all_messages.keys() if c.startswith('_'))
        named_contacts = sum(1 for c in all_messages.keys() if not c.startswith('_'))
        
        logger.info(f"\nStatistiques des contacts:")
        logger.info(f" - Total contacts: {len(all_messages)}")
        logger.info(f" - Contacts avec numéro: {numeric_contacts}")
        logger.info(f" - Contacts avec prénom: {named_contacts}")
        
        return True
    else:
        logger.error("\n===== ÉCHEC DE LA GÉNÉRATION =====")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
