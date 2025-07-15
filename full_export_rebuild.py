#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de reconstruction complète des exports incluant TOUS les contacts
et TOUS leurs messages reçus, avec ou sans transcriptions.

Ce script assure que tous les contacts apparaissent dans l'export final,
et que tous les messages reçus sont inclus, qu'ils aient une transcription ou non.
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
logger = logging.getLogger('full_rebuild')

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
    """Crée un mapping des transcriptions par UUID et par contact"""
    transcription_mapping = {}
    contact_folders = list_contact_folders()
    
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        transcription_dir = os.path.join(contact_dir, 'transcriptions')
        
        if not os.path.isdir(transcription_dir):
            continue
        
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
    
    logger.info(f"Mapping de transcription créé pour {len(transcription_mapping)} UUIDs")
    return transcription_mapping

def extract_all_messages_by_contact():
    """Extrait tous les messages par contact"""
    all_messages = defaultdict(list)
    contact_folders = list_contact_folders()
    
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
    
    # Compter les statistiques
    total_messages = sum(len(msgs) for msgs in all_messages.values())
    audio_messages = sum(sum(1 for m in msgs if m['is_audio']) for msgs in all_messages.values())
    transcribed_messages = sum(sum(1 for m in msgs if m['has_transcription']) for msgs in all_messages.values())
    
    logger.info(f"Extraction terminée: {total_messages} messages au total")
    logger.info(f"Messages audio: {audio_messages}, messages avec transcription: {transcribed_messages}")
    
    return all_messages

def generate_complete_csv(all_messages):
    """Génère un CSV complet avec tous les contacts et leurs messages"""
    output_csv = os.path.join(OUTPUT_DIR, "messages_recus_complet.csv")
    
    try:
        logger.info(f"Génération du fichier CSV complet: {output_csv}")
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Date', 'Heure', 'Type', 'Contenu', 'Fichier Audio', 'Transcription'])
            
            # Parcourir tous les contacts et leurs messages
            for contact, messages in all_messages.items():
                # Si le contact n'a pas de messages, ajouter au moins une ligne vide pour ce contact
                if not messages:
                    writer.writerow([contact, '', '', '', '', '', ''])
                    continue
                
                for msg in messages:
                    # Détecter le type de message
                    msg_type = 'TEXTE'
                    if msg['is_audio']:
                        msg_type = 'AUDIO'
                    elif '[IMAGE]' in msg['content']:
                        msg_type = 'IMAGE'
                    elif '[VIDEO]' in msg['content']:
                        msg_type = 'VIDEO'
                    
                    # Extraire le contenu textuel
                    content = msg['content']
                    if msg_type != 'TEXTE':
                        # Enlever les tags du type de media pour n'avoir que le texte
                        content = re.sub(r'\[(AUDIO|IMAGE|VIDEO)\]\s+[^\n]+', '', content)
                    
                    # Nettoyer le contenu - FORMAT CORRIGÉ
                    content = re.sub(r'^\[([\d/]+)\s+([\d:]+)\]\s*←?\s*', '', content).strip()
                    
                    writer.writerow([
                        msg['contact'],
                        msg['date'],
                        msg['time'],
                        msg_type,
                        content,
                        msg['audio_file'] if msg['is_audio'] else '',
                        msg['transcription']
                    ])
        
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV complet généré: {size} octets")
        return True, size
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV complet: {str(e)}")
        return False, 0

def generate_audio_only_csv(all_messages):
    """Génère un CSV contenant uniquement les messages audio avec ou sans transcription"""
    output_csv = os.path.join(OUTPUT_DIR, "messages_audio.csv")
    
    try:
        audio_messages = []
        
        # Extraire tous les messages audio
        for contact, messages in all_messages.items():
            for msg in messages:
                if msg['is_audio']:
                    audio_messages.append(msg)
        
        logger.info(f"Génération du fichier CSV audio uniquement: {output_csv} ({len(audio_messages)} messages)")
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Date', 'Heure', 'Fichier Audio', 'A Transcription', 'Transcription'])
            
            # Écrire tous les messages audio
            for msg in audio_messages:
                writer.writerow([
                    msg['contact'],
                    msg['date'],
                    msg['time'],
                    msg['audio_file'],
                    'OUI' if msg['has_transcription'] else 'NON',
                    msg['transcription']
                ])
        
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV audio généré: {size} octets")
        return True, size
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV audio: {str(e)}")
        return False, 0

def generate_transcribed_only_csv(all_messages):
    """Génère un CSV contenant uniquement les messages avec transcription"""
    output_csv = os.path.join(OUTPUT_DIR, "messages_transcription.csv")
    
    try:
        transcribed_messages = []
        
        # Extraire tous les messages avec transcription
        for contact, messages in all_messages.items():
            for msg in messages:
                if msg['has_transcription']:
                    transcribed_messages.append(msg)
        
        logger.info(f"Génération du fichier CSV transcriptions uniquement: {output_csv} ({len(transcribed_messages)} messages)")
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Date', 'Heure', 'Fichier Audio', 'Transcription'])
            
            # Écrire tous les messages avec transcription
            for msg in transcribed_messages:
                writer.writerow([
                    msg['contact'],
                    msg['date'],
                    msg['time'],
                    msg['audio_file'],
                    msg['transcription']
                ])
        
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV transcriptions généré: {size} octets")
        return True, size
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV transcriptions: {str(e)}")
        return False, 0

def count_contacts_with_messages(all_messages):
    """Compte le nombre de contacts avec au moins un message"""
    contacts_with_messages = sum(1 for contact, messages in all_messages.items() if messages)
    return contacts_with_messages

def analyze_contact_distribution(all_messages):
    """Analyse la distribution des messages par contact"""
    contact_stats = []
    
    for contact, messages in all_messages.items():
        if not messages:
            contact_stats.append({
                'contact': contact,
                'total': 0,
                'audio': 0,
                'transcription': 0
            })
        else:
            audio_count = sum(1 for m in messages if m['is_audio'])
            trans_count = sum(1 for m in messages if m['has_transcription'])
            
            contact_stats.append({
                'contact': contact,
                'total': len(messages),
                'audio': audio_count,
                'transcription': trans_count
            })
    
    # Trier par nombre de messages
    contact_stats.sort(key=lambda x: x['total'], reverse=True)
    
    # Afficher les statistiques
    logger.info("\n=== DISTRIBUTION DES MESSAGES PAR CONTACT ===")
    logger.info(f"Total contacts: {len(contact_stats)}")
    
    contacts_with_messages = sum(1 for stats in contact_stats if stats['total'] > 0)
    logger.info(f"Contacts avec messages: {contacts_with_messages}")
    
    contacts_with_audio = sum(1 for stats in contact_stats if stats['audio'] > 0)
    logger.info(f"Contacts avec messages audio: {contacts_with_audio}")
    
    contacts_with_trans = sum(1 for stats in contact_stats if stats['transcription'] > 0)
    logger.info(f"Contacts avec transcriptions: {contacts_with_trans}")
    
    # Afficher les 10 contacts avec le plus de messages
    logger.info("\nTop 10 des contacts avec le plus de messages:")
    for i, stats in enumerate(contact_stats[:10]):
        logger.info(f"  {i+1}. {stats['contact']}: {stats['total']} messages, {stats['audio']} audio, {stats['transcription']} transcriptions")
    
    return contact_stats

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("RECONSTRUCTION COMPLÈTE DES EXPORTS - TOUS CONTACTS")
    logger.info("="*50)
    
    # 1. Extraire tous les messages par contact
    logger.info("\n=== ÉTAPE 1: EXTRACTION DE TOUS LES MESSAGES PAR CONTACT ===")
    all_messages = extract_all_messages_by_contact()
    
    # Analyser la distribution des contacts
    analyze_contact_distribution(all_messages)
    
    # 2. Générer les fichiers CSV
    logger.info("\n=== ÉTAPE 2: GÉNÉRATION DES FICHIERS CSV ===")
    
    # CSV complet avec tous les contacts et messages
    success_complete, size_complete = generate_complete_csv(all_messages)
    
    # CSV avec uniquement les messages audio
    success_audio, size_audio = generate_audio_only_csv(all_messages)
    
    # CSV avec uniquement les messages avec transcription
    success_trans, size_trans = generate_transcribed_only_csv(all_messages)
    
    if success_complete and success_audio and success_trans:
        logger.info("\n===== RECONSTRUCTION TERMINÉE AVEC SUCCÈS =====")
        
        total_contacts = len(all_messages)
        contacts_with_messages = count_contacts_with_messages(all_messages)
        
        logger.info(f"Total contacts: {total_contacts}")
        logger.info(f"Contacts avec messages: {contacts_with_messages}")
        logger.info(f"Fichiers générés:")
        logger.info(f"  - messages_recus_complet.csv: {size_complete} octets")
        logger.info(f"  - messages_audio.csv: {size_audio} octets")
        logger.info(f"  - messages_transcription.csv: {size_trans} octets")
        
        return True
    else:
        logger.error("\n===== ÉCHEC DE LA RECONSTRUCTION =====")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
