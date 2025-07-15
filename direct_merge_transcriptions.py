#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de fusion directe des transcriptions avec les messages
Ce script analyse tous les messages audio pour retrouver leurs UUID,
puis fusionne directement les transcriptions correspondantes.
"""

import os
import re
import csv
import shutil
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
logger = logging.getLogger('direct_merge')

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"

def list_contact_folders():
    """Liste tous les dossiers de contact dans le dossier de sortie"""
    contact_folders = []
    
    for item in os.listdir(OUTPUT_DIR):
        if os.path.isdir(os.path.join(OUTPUT_DIR, item)) and item.startswith('_'):
            contact_folders.append(item)
    
    logger.info(f"Trouvé {len(contact_folders)} dossiers de contact")
    return contact_folders

def find_transcription_files():
    """Trouve tous les fichiers de transcription dans les dossiers de contact"""
    transcription_files = []
    
    contact_folders = list_contact_folders()
    
    # Parcourir chaque dossier de contact pour trouver les transcriptions
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        transcription_dir = os.path.join(contact_dir, 'transcriptions')
        
        if os.path.isdir(transcription_dir):
            for file in os.listdir(transcription_dir):
                if file.endswith('.txt'):
                    full_path = os.path.join(transcription_dir, file)
                    uuid = extract_uuid_from_filename(file)
                    if uuid:
                        transcription_files.append({
                            'contact': contact,
                            'file': file,
                            'path': full_path,
                            'uuid': uuid
                        })
    
    logger.info(f"Trouvé {len(transcription_files)} fichiers de transcription avec UUID")
    return transcription_files

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
    """Crée un mapping des transcriptions par UUID"""
    transcription_files = find_transcription_files()
    mapping = {}
    
    for trans in transcription_files:
        uuid = trans['uuid']
        if uuid:
            # Lire le contenu de la transcription
            transcription = read_transcription_file(trans['path'])
            if transcription:
                mapping[uuid] = {
                    'contact': trans['contact'],
                    'file': trans['file'],
                    'path': trans['path'],
                    'content': transcription
                }
    
    logger.info(f"Mapping de transcription créé pour {len(mapping)} UUIDs")
    return mapping

def find_all_audio_messages():
    """Trouve tous les messages audio avec leurs UUID dans tous les fichiers par contact"""
    audio_messages = []
    contact_folders = list_contact_folders()
    
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        messages_file = os.path.join(contact_dir, 'messages_recus.txt')
        
        if not os.path.exists(messages_file):
            continue
        
        try:
            with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Chercher les messages audio (peut contenir ou non le symbole ←)
            # Format: [YYYY/MM/DD HH:MM] (← optionnel) [AUDIO] received_UUID_1.opus
            pattern = r'\[([\d/]+)\s+([\d:]+)\].*?\[AUDIO\]\s+([^\n\[\]]+)'
            matches = re.finditer(pattern, content)
            
            for match in matches:
                date = match.group(1)
                time = match.group(2)
                audio_file = match.group(3).strip()
                
                # Extraire l'UUID
                uuid = extract_uuid_from_filename(audio_file)
                if uuid:
                    audio_messages.append({
                        'contact': contact,
                        'date': date,
                        'time': time,
                        'audio_file': audio_file,
                        'uuid': uuid,
                        'message': match.group(0)
                    })
        except Exception as e:
            logger.error(f"Erreur lecture messages audio {contact}: {str(e)}")
    
    logger.info(f"Trouvé {len(audio_messages)} messages audio avec UUID dans les fichiers par contact")
    return audio_messages

def build_transcript_enriched_file():
    """Construit un fichier enrichi avec toutes les transcriptions associées aux messages audio"""
    # Fichier global de tous les messages reçus
    global_file = os.path.join(OUTPUT_DIR, 'messages_recus.txt')
    
    # Fichier de sortie pour les messages avec transcriptions
    output_file = os.path.join(OUTPUT_DIR, 'messages_recus_avec_transcriptions.txt')
    
    # Sauvegarde si le fichier existe déjà
    if os.path.exists(output_file):
        backup = f"{output_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(output_file, backup)
        logger.info(f"Sauvegarde créée: {backup}")
    
    # Charger le mapping des transcriptions
    trans_mapping = create_transcription_mapping()
    
    # Trouver tous les messages audio avec leurs UUID
    audio_messages = find_all_audio_messages()
    
    # Création d'un index pour retrouver rapidement les messages par UUID
    audio_index = {}
    for msg in audio_messages:
        audio_index[msg['uuid']] = msg
    
    # Correspondances entre UUID des transcriptions et messages audio
    matches = []
    missing_msgs = []
    for uuid in trans_mapping:
        if uuid in audio_index:
            matches.append({
                'uuid': uuid,
                'audio_msg': audio_index[uuid],
                'transcription': trans_mapping[uuid]['content']
            })
        else:
            missing_msgs.append(uuid)
    
    logger.info(f"Correspondances trouvées: {len(matches)} sur {len(trans_mapping)} transcriptions")
    if missing_msgs:
        logger.warning(f"{len(missing_msgs)} transcriptions sans correspondance de message audio")
        logger.warning(f"Exemples: {missing_msgs[:5]}")
    
    # Générer le fichier avec les transcriptions
    try:
        # Créer le contenu du fichier par contact
        content_by_contact = {}
        
        for match in matches:
            contact = match['audio_msg']['contact']
            message = match['audio_msg']['message']
            transcription = match['transcription']
            
            # Format du message avec transcription
            enriched_msg = f"{message}\n[TRANSCRIPTION] {transcription}"
            
            if contact not in content_by_contact:
                content_by_contact[contact] = []
                
            content_by_contact[contact].append(enriched_msg)
        
        # Écrire l'en-tête du fichier
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("TOUS LES MESSAGES REÇUS AVEC TRANSCRIPTIONS\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            
            # Écrire les messages par contact
            for contact, messages in content_by_contact.items():
                f.write(f"\n{'='*30}\n")
                f.write(f"DE: {contact}\n")
                f.write(f"{'='*30}\n\n")
                
                for msg in messages:
                    f.write(f"{msg}\n\n")
            
            # Ajouter un résumé
            f.write(f"\n\nTOTAL MESSAGES AVEC TRANSCRIPTIONS: {len(matches)}\n")
            f.write(f"TOTAL CONTACTS: {len(content_by_contact)}\n")
        
        size = os.path.getsize(output_file)
        logger.info(f"Fichier généré: {output_file} - Taille: {size} octets")
        
        return output_file, size, len(matches)
    except Exception as e:
        logger.error(f"Erreur lors de la génération du fichier avec transcriptions: {str(e)}")
        return None, 0, 0

def generate_csv_export(all_messages=False):
    """Génère un fichier CSV à partir des messages avec transcriptions"""
    # Fichier source pour CSV avec transcriptions uniquement
    source_file = os.path.join(OUTPUT_DIR, 'messages_recus_avec_transcriptions.txt')
    
    if not os.path.exists(source_file):
        logger.error(f"Fichier source introuvable: {source_file}")
        return False
    
    # Fichier de sortie CSV
    output_csv = os.path.join(OUTPUT_DIR, "messages_recus_only.csv")
    
    try:
        logger.info(f"Lecture du fichier source: {source_file}")
        with open(source_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extraire les sections par contact
        sections = re.split(r'\n={30}\nDE: (.+?)\n={30}\n', content)
        
        if len(sections) <= 1:
            logger.warning("Aucune section de contact trouvée dans le fichier")
            return False
        
        # Préparer la liste des messages
        messages = []
        
        # Traiter chaque section (le premier élément est l'en-tête)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                contact = sections[i]
                content = sections[i + 1]
                
                # Diviser en blocs de messages
                blocks = re.split(r'\n\n+', content)
                
                for block in blocks:
                    if not block.strip():
                        continue
                    
                    # Vérifier si ce bloc contient une transcription
                    if '[TRANSCRIPTION]' in block:
                        # Extraire les informations du message
                        date_match = re.search(r'\[([\d/]+)\s+([\d:]+)\]', block)
                        audio_match = re.search(r'\[AUDIO\]\s+([^\n\[\]]+)', block)
                        trans_match = re.search(r'\[TRANSCRIPTION\]\s+(.+)', block)
                        
                        if date_match and audio_match and trans_match:
                            date = date_match.group(1)
                            time = date_match.group(2)
                            audio_file = audio_match.group(1).strip()
                            transcription = trans_match.group(1).strip()
                            
                            messages.append({
                                'contact': contact,
                                'date': date,
                                'time': time,
                                'audio_file': audio_file,
                                'transcription': transcription
                            })
        
        logger.info(f"{len(messages)} messages avec transcriptions trouvés")
        
        # Générer le CSV
        logger.info(f"Génération du fichier CSV: {output_csv}")
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
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
        
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV généré avec succès: {size} octets")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("FUSION DIRECTE DES TRANSCRIPTIONS")
    logger.info("="*50)
    
    # 1. Construire le fichier enrichi avec les transcriptions
    logger.info("\n=== ÉTAPE 1: CONSTRUCTION DU FICHIER AVEC TRANSCRIPTIONS ===")
    output_file, size, count = build_transcript_enriched_file()
    
    if not output_file or size < 1000:
        logger.error("Échec de la génération du fichier avec transcriptions")
        return False
    
    # 2. Générer le fichier CSV
    logger.info("\n=== ÉTAPE 2: GÉNÉRATION DU FICHIER CSV ===")
    success = generate_csv_export()
    
    if success:
        logger.info("\n===== OPÉRATION TERMINÉE AVEC SUCCÈS =====")
        logger.info(f"Total messages avec transcriptions: {count}")
        return True
    else:
        logger.error("\n===== ÉCHEC DE L'OPÉRATION =====")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
