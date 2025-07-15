#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de reconstruction complète des exports
Ce script collecte tous les fichiers messages_recus.txt par contact,
les concatène en un fichier global, fusionne les transcriptions,
et génère le CSV final avec tous les messages (avec ou sans transcription).
"""

import os
import re
import json
import shutil
import logging
import sys
import csv
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('rebuild_export')

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
                    transcription_files.append({
                        'contact': contact,
                        'file': file,
                        'path': full_path
                    })
    
    logger.info(f"Trouvé {len(transcription_files)} fichiers de transcription")
    return transcription_files

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

def extract_uuid_from_filename(filename):
    """Extrait l'UUID du nom de fichier"""
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    match = re.search(uuid_pattern, filename)
    if match:
        return match.group(1)
    return None

def rebuild_received_messages_file():
    """Reconstruit le fichier global messages_recus.txt à partir des fichiers par contact"""
    contact_folders = list_contact_folders()
    
    # Fichier de sortie
    output_file = os.path.join(OUTPUT_DIR, 'messages_recus.txt')
    
    # Sauvegarde si le fichier existe déjà
    if os.path.exists(output_file):
        backup = f"{output_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(output_file, backup)
        logger.info(f"Sauvegarde créée: {backup}")
    
    # Collecter tous les messages reçus
    all_messages = []
    total_contacts = 0
    total_messages = 0
    
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        messages_file = os.path.join(contact_dir, 'messages_recus.txt')
        
        if not os.path.exists(messages_file):
            continue
            
        try:
            with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Extraire uniquement les lignes de messages (sans les en-têtes)
            lines = content.split('\n')
            message_lines = []
            in_messages = False
            
            for line in lines:
                if '='*30 in line and not in_messages:
                    in_messages = True
                    continue
                    
                if in_messages:
                    message_lines.append(line)
            
            if message_lines:
                total_contacts += 1
                message_count = sum(1 for line in message_lines if line.strip() and '[' in line)
                total_messages += message_count
                
                all_messages.append({
                    'contact': contact,
                    'messages': '\n'.join(message_lines)
                })
        except Exception as e:
            logger.error(f"Erreur lecture messages {contact}: {str(e)}")
    
    # Générer le fichier final
    with open(output_file, 'w', encoding='utf-8') as f:
        # Écrire l'en-tête
        f.write("TOUS LES MESSAGES REÇUS\n")
        f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        
        for msg_data in all_messages:
            contact = msg_data['contact']
            messages = msg_data['messages']
            
            f.write(f"\n{'='*30}\n")
            f.write(f"DE: {contact}\n")
            f.write(f"{'='*30}\n\n")
            f.write(messages + "\n\n")
        
        # Ajouter un résumé
        f.write(f"\n\nTOTAL MESSAGES REÇUS: {total_messages}\n")
        f.write(f"TOTAL CONTACTS: {total_contacts}\n")
    
    size = os.path.getsize(output_file)
    logger.info(f"Fichier généré: {output_file} - Taille: {size} octets")
    
    return output_file, size, total_messages

def find_audio_references_in_file(file_path):
    """Trouve toutes les références à des fichiers audio dans un fichier"""
    audio_refs = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Pattern pour trouver les références audio et les UUID
        pattern = r'\[([\d-]+)\s+([\d:]+)\].*?\[AUDIO\]\s+([^\n\[\]]+)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            date = match.group(1)
            time = match.group(2)
            audio_file = match.group(3).strip()
            
            # Extraire l'UUID si possible
            uuid = None
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_file)
            if uuid_match:
                uuid = uuid_match.group(1)
                
            audio_refs.append({
                'date': date,
                'time': time,
                'audio_file': audio_file,
                'uuid': uuid,
                'line': match.group(0)
            })
            
        logger.info(f"Trouvé {len(audio_refs)} références audio dans {os.path.basename(file_path)}")
        return audio_refs
    except Exception as e:
        logger.error(f"Erreur lors de la recherche des références audio: {str(e)}")
        return []

def create_transcription_mapping():
    """Crée un mapping des fichiers de transcription par UUID"""
    transcription_files = find_transcription_files()
    mapping = {}
    
    for trans in transcription_files:
        uuid = extract_uuid_from_filename(trans['file'])
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

def merge_transcriptions_with_messages():
    """Fusionne les transcriptions avec le fichier messages_recus.txt"""
    # Fichiers source et destination
    messages_file = os.path.join(OUTPUT_DIR, 'messages_recus.txt')
    output_file = os.path.join(OUTPUT_DIR, 'messages_recus_avec_transcriptions.txt')
    
    if not os.path.exists(messages_file):
        logger.error(f"Fichier source introuvable: {messages_file}")
        return None, 0, 0
    
    # Sauvegarde si le fichier existe déjà
    if os.path.exists(output_file):
        backup = f"{output_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(output_file, backup)
        logger.info(f"Sauvegarde créée: {backup}")
    
    # Créer le mapping des transcriptions par UUID
    trans_mapping = create_transcription_mapping()
    
    # Trouver toutes les références audio dans le fichier
    audio_refs = find_audio_references_in_file(messages_file)
    
    # Lire le contenu du fichier source
    with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Compteurs
    total_replaced = 0
    total_found = 0
    
    # Remplacer chaque référence audio par la version avec transcription
    for ref in audio_refs:
        uuid = ref['uuid']
        if uuid and uuid in trans_mapping:
            total_found += 1
            transcription = trans_mapping[uuid]['content']
            
            # Format du remplacement:
            # [Date Heure] ← [AUDIO] fichier.opus
            # devient:
            # [Date Heure] ← [AUDIO] fichier.opus
            # [TRANSCRIPTION] texte de la transcription
            original = ref['line']
            replacement = f"{original}\n[TRANSCRIPTION] {transcription}"
            
            if original in content:
                content = content.replace(original, replacement)
                total_replaced += 1
    
    # Écrire le contenu mis à jour
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    size = os.path.getsize(output_file)
    logger.info(f"Fichier généré: {output_file} - Taille: {size} octets")
    logger.info(f"Transcriptions trouvées: {total_found}, remplacées: {total_replaced}")
    
    return output_file, size, total_replaced

def extract_messages_from_file(file_path):
    """Extrait tous les messages d'un fichier (avec ou sans transcriptions)"""
    if not os.path.exists(file_path):
        logger.error(f"Fichier introuvable: {file_path}")
        return []
    
    messages = []
    current_contact = None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Extraire les sections par contact
        sections = re.split(r'\n={30}\nDE: (.+?)\n={30}\n', content)
        
        if len(sections) <= 1:
            logger.warning("Aucune section de contact trouvée dans le fichier")
            return []
        
        # Traiter chaque section (le premier élément est l'en-tête)
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                contact = sections[i]
                content = sections[i + 1]
                
                # Diviser en lignes de message
                lines = content.split('\n')
                
                # Regrouper les lignes en messages
                message_buffer = []
                current_message = None
                
                for line in lines:
                    # Nouvelle ligne de message
                    if re.match(r'^\[([\d-]+)\s+([\d:]+)\]', line):
                        # Enregistrer le message précédent s'il existe
                        if current_message:
                            messages.append(current_message)
                        
                        # Extraire la date et l'heure
                        date_match = re.match(r'^\[([\d-]+)\s+([\d:]+)\]', line)
                        date = date_match.group(1)
                        time = date_match.group(2)
                        
                        # Créer un nouveau message
                        current_message = {
                            'contact': contact,
                            'date': date,
                            'time': time,
                            'content': line,
                            'has_audio': '[AUDIO]' in line,
                            'has_transcription': False,
                            'transcription': '',
                            'audio_file': ''
                        }
                        
                        # Extraire le nom du fichier audio si présent
                        if current_message['has_audio']:
                            audio_match = re.search(r'\[AUDIO\]\s+([^\n\[\]]+)', line)
                            if audio_match:
                                current_message['audio_file'] = audio_match.group(1).strip()
                        
                        message_buffer = [line]
                    # Ligne de transcription
                    elif line.strip().startswith('[TRANSCRIPTION]') and current_message:
                        current_message['has_transcription'] = True
                        trans_match = re.search(r'\[TRANSCRIPTION\]\s+(.+)', line)
                        if trans_match:
                            current_message['transcription'] = trans_match.group(1).strip()
                        message_buffer.append(line)
                    # Ligne supplémentaire du même message
                    elif line.strip() and current_message:
                        message_buffer.append(line)
                        current_message['content'] = '\n'.join(message_buffer)
                
                # Ajouter le dernier message s'il existe
                if current_message:
                    messages.append(current_message)
        
        logger.info(f"{len(messages)} messages extraits de {os.path.basename(file_path)}")
        
        # Compter les statistiques
        audio_count = sum(1 for m in messages if m['has_audio'])
        trans_count = sum(1 for m in messages if m['has_transcription'])
        logger.info(f"Messages avec audio: {audio_count}, avec transcription: {trans_count}")
        
        return messages
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction des messages: {str(e)}")
        return []

def generate_csv_export(messages, include_all=True):
    """Génère un fichier CSV à partir des messages"""
    if not messages:
        logger.warning("Aucun message à exporter")
        return False
    
    try:
        # Fichier de sortie
        if include_all:
            output_csv = os.path.join(OUTPUT_DIR, "messages_recus_all.csv")
        else:
            output_csv = os.path.join(OUTPUT_DIR, "messages_recus_only.csv")
        
        logger.info(f"Génération du fichier CSV: {output_csv}")
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Date', 'Heure', 'Type', 'Contenu', 'Fichier Audio', 'Transcription'])
            
            # Filtrer si nécessaire
            if not include_all:
                messages = [m for m in messages if m['has_transcription']]
            
            # Données
            for msg in messages:
                # Détecter le type de message
                msg_type = 'TEXTE'
                if msg['has_audio']:
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
                
                # Nettoyer le contenu
                content = re.sub(r'^\[([\d-]+)\s+([\d:]+)\]\s*←\s*', '', content).strip()
                
                writer.writerow([
                    msg['contact'],
                    msg['date'],
                    msg['time'],
                    msg_type,
                    content,
                    msg['audio_file'] if msg['has_audio'] else '',
                    msg['transcription']
                ])
                
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV généré avec succès: {size} octets ({len(messages)} messages)")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la génération du CSV: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("RECONSTRUCTION COMPLÈTE DES EXPORTS")
    logger.info("="*50)
    
    # 1. Reconstruire le fichier messages_recus.txt
    logger.info("\n=== ÉTAPE 1: RECONSTRUCTION DU FICHIER MESSAGES_RECUS.TXT ===")
    messages_file, size, total_messages = rebuild_received_messages_file()
    
    if size < 1000:  # Moins de 1 Ko
        logger.error(f"Fichier généré anormalement petit: {size} octets")
        return False
    
    # 2. Fusionner les transcriptions
    logger.info("\n=== ÉTAPE 2: FUSION DES TRANSCRIPTIONS ===")
    transcribed_file, trans_size, total_transcriptions = merge_transcriptions_with_messages()
    
    if not transcribed_file:
        logger.error("Échec de la fusion des transcriptions")
        return False
    
    # 3. Extraire tous les messages du fichier avec transcriptions
    logger.info("\n=== ÉTAPE 3: EXTRACTION DES MESSAGES ===")
    all_messages = extract_messages_from_file(transcribed_file)
    
    if not all_messages:
        logger.error("Aucun message extrait du fichier")
        return False
    
    # 4. Générer les fichiers CSV
    logger.info("\n=== ÉTAPE 4: GÉNÉRATION DES FICHIERS CSV ===")
    
    # CSV avec tous les messages (avec ou sans transcription)
    logger.info("Génération du CSV avec tous les messages...")
    success_all = generate_csv_export(all_messages, include_all=True)
    
    # CSV avec uniquement les messages avec transcription
    logger.info("Génération du CSV avec uniquement les messages avec transcription...")
    success_trans = generate_csv_export(all_messages, include_all=False)
    
    if success_all and success_trans:
        logger.info("\n===== RECONSTRUCTION TERMINÉE AVEC SUCCÈS =====")
        logger.info(f"Total messages: {total_messages}")
        logger.info(f"Total transcriptions: {total_transcriptions}")
        return True
    else:
        logger.error("\n===== ÉCHEC DE LA RECONSTRUCTION =====")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
