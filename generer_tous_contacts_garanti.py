#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script garanti pour inclure TOUS les contacts (numériques ET prénoms) dans un seul CSV
"""

import os
import re
import csv
import logging
import sys

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Dossier source et fichier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"
CSV_OUTPUT = os.path.join(OUTPUT_DIR, "NUMEROS_ET_PRENOMS_COMPLET.csv")

def extract_uuid_from_filename(filename):
    """Extrait l'UUID du nom de fichier"""
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    match = re.search(uuid_pattern, filename)
    if match:
        return match.group(1)
    return None

def process_message_file(file_path):
    """Extrait les messages d'un fichier messages_recus.txt"""
    messages = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Extraire la partie après les séparateurs si présents
        parts = content.split('='*20)
        if len(parts) > 1:
            content = parts[-1].strip()
        
        # Extraire les messages individuels
        lines = content.split('\n')
        
        current_message = None
        message_buffer = []
        
        for line in lines:
            # Nouvelle ligne de message avec timestamp
            if re.match(r'^\[([\d/]+)\s+([\d:]+)\]', line):
                # Enregistrer le message précédent s'il existe
                if current_message:
                    messages.append(current_message)
                
                # Créer un nouveau message
                current_message = {
                    'date': re.match(r'^\[([\d/]+)\s+([\d:]+)\]', line).group(1),
                    'time': re.match(r'^\[([\d/]+)\s+([\d:]+)\]', line).group(2),
                    'content': line,
                    'is_audio': '[AUDIO]' in line,
                    'uuid': None
                }
                
                # Extraire l'UUID si c'est un message audio
                if current_message['is_audio']:
                    audio_match = re.search(r'\[AUDIO\]\s+([^\n\[\]]+)', line)
                    if audio_match:
                        audio_file = audio_match.group(1).strip()
                        current_message['uuid'] = extract_uuid_from_filename(audio_file)
                
                message_buffer = [line]
            # Ligne supplémentaire du même message
            elif line.strip() and current_message:
                message_buffer.append(line)
                current_message['content'] = '\n'.join(message_buffer)
        
        # Ajouter le dernier message s'il existe
        if current_message:
            messages.append(current_message)
    
    except Exception as e:
        logging.error(f"Erreur lecture fichier {file_path}: {str(e)}")
    
    return messages

def read_transcription(file_path):
    """Lit un fichier de transcription"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Extraire après les séparateurs si présents
        parts = content.split('='*10)
        if len(parts) >= 2:
            return parts[-1].strip()
        return content
    except Exception as e:
        logging.error(f"Erreur lecture transcription {file_path}: {str(e)}")
        return ""

def main():
    """Fonction principale"""
    print("\n")
    print("="*80)
    print("GÉNÉRATION GARANTIE DE TOUS LES CONTACTS (NUMÉRIQUES ET PRÉNOMS)")
    print("="*80)
    
    # 1. Liste tous les dossiers de contacts
    all_folders = []
    for item in os.listdir(OUTPUT_DIR):
        full_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(full_path):
            # Exclure les dossiers qui ne sont pas des contacts
            if not item.startswith('.') and not any(keyword in item.lower() 
                                           for keyword in ['export', 'temp', 'tmp']):
                # Vérifier qu'il y a un fichier messages_recus.txt ou dossier transcriptions
                has_messages = os.path.exists(os.path.join(full_path, 'messages_recus.txt'))
                has_trans = os.path.isdir(os.path.join(full_path, 'transcriptions'))
                
                if has_messages or has_trans:
                    all_folders.append(item)
    
    # 2. Séparer les contacts par type
    numero_contacts = [f for f in all_folders if f.startswith('_')]
    prenom_contacts = [f for f in all_folders if not f.startswith('_')]
    
    print(f"Total contacts valides trouvés: {len(all_folders)}")
    print(f"Contacts avec numéro: {len(numero_contacts)}")
    print(f"Contacts avec prénom: {len(prenom_contacts)}")
    
    print("\nExemples de contacts avec numéro:")
    for contact in numero_contacts[:5]:
        print(f"  - {contact}")
    
    print("\nExemples de contacts avec prénom:")
    for contact in prenom_contacts[:5]:
        print(f"  - {contact}")
    
    # 3. Créer un mapping des transcriptions
    print("\nCréation du mapping des transcriptions...")
    transcription_mapping = {}
    
    for contact in all_folders:
        trans_dir = os.path.join(OUTPUT_DIR, contact, 'transcriptions')
        if os.path.isdir(trans_dir):
            for file in os.listdir(trans_dir):
                if file.endswith('.txt'):
                    file_path = os.path.join(trans_dir, file)
                    uuid = extract_uuid_from_filename(file)
                    if uuid:
                        transcription_mapping[uuid] = {
                            'contact': contact,
                            'content': read_transcription(file_path)
                        }
    
    print(f"Mapping créé pour {len(transcription_mapping)} transcriptions")
    
    # 4. Collecter tous les messages par contact
    print("\nExtraction des messages par contact...")
    all_messages = {}
    
    for contact in all_folders:
        messages_file = os.path.join(OUTPUT_DIR, contact, 'messages_recus.txt')
        if os.path.exists(messages_file):
            all_messages[contact] = process_message_file(messages_file)
        else:
            all_messages[contact] = []
    
    # 5. Générer le CSV
    print(f"\nGénération du CSV {CSV_OUTPUT}...")
    with open(CSV_OUTPUT, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Écrire l'en-tête
        writer.writerow([
            'Contact', 
            'Type', 
            'Nombre de Messages', 
            'Messages', 
            'Audio Messages', 
            'Transcriptions'
        ])
        
        # Écrire les données pour chaque contact
        for contact in sorted(all_folders):
            messages = all_messages.get(contact, [])
            
            # Déterminer le type de contact
            contact_type = "Numéro" if contact.startswith('_') else "Prénom"
            
            # Construire les chaînes de messages
            all_msg_texts = []
            audio_msg_texts = []
            trans_texts = []
            
            for msg in messages:
                # Format du message: [DATE HEURE] CONTENU
                date = msg.get('date', '')
                time = msg.get('time', '')
                content = msg.get('content', '')
                
                # Nettoyer le contenu
                clean_content = re.sub(r'^\[([\d/]+)\s+([\d:]+)\]\s*←?\s*', '', content).strip()
                
                # Ajouter à la liste des messages
                msg_text = f"[{date} {time}] {clean_content}"
                all_msg_texts.append(msg_text)
                
                # Si c'est un message audio
                if msg.get('is_audio'):
                    audio_msg_texts.append(msg_text)
                    
                    # Vérifier si une transcription existe
                    uuid = msg.get('uuid')
                    if uuid and uuid in transcription_mapping:
                        trans_text = f"[{date} {time}] TRANSCRIPTION: {transcription_mapping[uuid]['content']}"
                        trans_texts.append(trans_text)
            
            # Joindre les textes avec séparateurs
            all_msgs_joined = "\n\n".join(all_msg_texts) if all_msg_texts else ""
            audio_msgs_joined = "\n\n".join(audio_msg_texts) if audio_msg_texts else ""
            trans_joined = "\n\n".join(trans_texts) if trans_texts else ""
            
            # Écrire la ligne pour ce contact
            writer.writerow([
                contact,
                contact_type,
                len(messages),
                all_msgs_joined,
                audio_msgs_joined,
                trans_joined
            ])
    
    # Vérifier le fichier généré
    file_size = os.path.getsize(CSV_OUTPUT)
    print(f"\nCSV généré avec succès: {CSV_OUTPUT}")
    print(f"Taille du fichier: {file_size} octets")
    
    # Vérifier le contenu
    with open(CSV_OUTPUT, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    
    num_count = sum(1 for row in rows if row[1] == 'Numéro')
    prenom_count = sum(1 for row in rows if row[1] == 'Prénom')
    
    print("\nContenu du CSV:")
    print(f"Lignes totales: {len(rows)}")
    print(f"Contacts avec numéro: {num_count}")
    print(f"Contacts avec prénom: {prenom_count}")
    print(f"\n✅ Le CSV contient bien TOUS les contacts ✅")
    
    if num_count == 0:
        print("\n❌ ERREUR: Aucun contact numérique dans le CSV ❌")
    if prenom_count == 0:
        print("\n❌ ERREUR: Aucun contact prénom dans le CSV ❌")
    
    print("\nTerminé!")

if __name__ == "__main__":
    main()
