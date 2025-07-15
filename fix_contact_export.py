#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour corriger les exports de contacts spécifiques
Ce script fusionne les messages par contact plutôt que de les séparer ligne par ligne
"""

import os
import csv
import shutil
import logging
import sys
import re
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
logger = logging.getLogger('fix_contact')

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"

# Liste des contacts à analyser/corriger
CONTACTS_TO_CHECK = [
    "_33_7_82_79_70_04",
    "_33_7_82_85_46_87", 
    "_33_7_83_07_41_99",
    "_33_7_83_16_34_02",
    "_33_7_83_34_22_19"
]

def analyze_contact_files():
    """Analyse les fichiers individuels des contacts spécifiés"""
    contact_data = {}
    
    for contact in CONTACTS_TO_CHECK:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        messages_file = os.path.join(contact_dir, 'messages_recus.txt')
        
        if not os.path.exists(contact_dir):
            logger.warning(f"Dossier de contact introuvable: {contact}")
            continue
            
        if not os.path.exists(messages_file):
            logger.warning(f"Fichier messages_recus.txt absent pour {contact}")
            continue
        
        try:
            # Lire le fichier messages_recus.txt
            with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extraire les messages (format: [YYYY/MM/DD HH:MM] message)
            messages = []
            for line in content.split('\n'):
                if re.match(r'^\[([\d/]+)\s+([\d:]+)\]', line):
                    messages.append(line)
            
            # Vérifier les transcriptions
            transcription_dir = os.path.join(contact_dir, 'transcriptions')
            transcriptions = []
            
            if os.path.isdir(transcription_dir):
                for file in os.listdir(transcription_dir):
                    if file.endswith('.txt'):
                        trans_path = os.path.join(transcription_dir, file)
                        uuid = extract_uuid_from_filename(file)
                        
                        with open(trans_path, 'r', encoding='utf-8', errors='ignore') as f:
                            trans_content = f.read()
                        
                        # Extraire la transcription (après les ===)
                        parts = trans_content.split('='*10)
                        if len(parts) >= 2:
                            trans_text = parts[-1].strip()
                        else:
                            trans_text = trans_content.strip()
                        
                        transcriptions.append({
                            'uuid': uuid,
                            'file': file,
                            'content': trans_text
                        })
            
            contact_data[contact] = {
                'messages': messages,
                'transcriptions': transcriptions
            }
            
            logger.info(f"Analysé {contact}: {len(messages)} messages, {len(transcriptions)} transcriptions")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de {contact}: {str(e)}")
    
    return contact_data

def extract_uuid_from_filename(filename):
    """Extrait l'UUID du nom de fichier"""
    uuid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
    match = re.search(uuid_pattern, filename)
    if match:
        return match.group(1)
    return None

def create_merged_export():
    """Crée un export fusionné avec tous les messages par contact"""
    # Analyse des fichiers par contact
    contact_data = analyze_contact_files()
    
    # Fichier de sortie - TXT
    output_txt = os.path.join(OUTPUT_DIR, "contacts_specifiques_merged.txt")
    
    try:
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write("MESSAGES REÇUS - CONTACTS SPÉCIFIQUES (FUSIONNÉS)\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            
            for contact, data in contact_data.items():
                f.write(f"\n{'='*30}\n")
                f.write(f"DE: {contact}\n")
                f.write(f"{'='*30}\n\n")
                
                # Écrire tous les messages de ce contact
                for msg in data['messages']:
                    f.write(f"{msg}\n\n")
                
                # Résumé pour ce contact
                f.write(f"\nTOTAL POUR {contact}: {len(data['messages'])} messages, ")
                f.write(f"{len(data['transcriptions'])} transcriptions\n\n")
        
        logger.info(f"Fichier texte fusionné créé: {output_txt}")
        
        # Créer le fichier CSV fusionné
        create_merged_csv(contact_data)
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du fichier fusionné: {str(e)}")
        return False

def create_merged_csv(contact_data):
    """Crée un fichier CSV avec les messages fusionnés par contact"""
    output_csv = os.path.join(OUTPUT_DIR, "contacts_specifiques_merged.csv")
    
    try:
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes
            writer.writerow(['Contact', 'Nombre de messages', 'Nombre de transcriptions', 'Messages'])
            
            # Une ligne par contact, avec tous les messages fusionnés
            for contact, data in contact_data.items():
                # Formatter tous les messages en une seule cellule
                all_messages = "\n\n".join(data['messages'])
                
                writer.writerow([
                    contact,
                    len(data['messages']),
                    len(data['transcriptions']),
                    all_messages
                ])
        
        logger.info(f"Fichier CSV fusionné créé: {output_csv}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création du CSV fusionné: {str(e)}")
        return False

def correct_complete_csv():
    """Corrige le fichier CSV complet pour fusionner les messages par contact"""
    input_csv = os.path.join(OUTPUT_DIR, "messages_recus_complet.csv")
    output_csv = os.path.join(OUTPUT_DIR, "messages_recus_complet_merged.csv")
    
    if not os.path.exists(input_csv):
        logger.error(f"Fichier CSV source introuvable: {input_csv}")
        return False
    
    try:
        # Lire tout le CSV source
        with open(input_csv, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Lire les en-têtes
            
            # Regrouper les messages par contact
            messages_by_contact = defaultdict(list)
            
            for row in reader:
                if not row or len(row) < len(headers):
                    continue
                    
                contact = row[0]
                messages_by_contact[contact].append(row)
        
        # Créer le CSV fusionné
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # En-têtes modifiés
            writer.writerow(['Contact', 'Nombre de messages', 'Messages reçus', 'Nombre messages audio', 
                             'Nombre messages avec transcription'])
            
            # Une ligne par contact
            for contact, messages in messages_by_contact.items():
                # Compter les types de messages
                audio_count = sum(1 for m in messages if m[3] == 'AUDIO')
                trans_count = sum(1 for m in messages if len(m) > 6 and m[6].strip())
                
                # Fusionner tous les messages en texte
                merged_messages = []
                for m in messages:
                    if len(m) >= 5:  # S'assurer qu'il y a au moins les colonnes date, heure et contenu
                        date = m[1]
                        time = m[2]
                        content = m[4]
                        msg_type = m[3]
                        
                        if msg_type == 'AUDIO' and len(m) > 6 and m[6]:
                            # Inclure la transcription pour les messages audio
                            merged_msg = f"[{date} {time}] {msg_type}: {content}\nTRANSCRIPTION: {m[6]}"
                        else:
                            merged_msg = f"[{date} {time}] {msg_type}: {content}"
                            
                        merged_messages.append(merged_msg)
                
                # Joindre tous les messages avec séparateur
                all_messages = "\n\n".join(merged_messages)
                
                writer.writerow([
                    contact,
                    len(messages),
                    all_messages,
                    audio_count,
                    trans_count
                ])
        
        size = os.path.getsize(output_csv)
        logger.info(f"Fichier CSV complet fusionné créé: {output_csv} ({size} octets)")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la correction du CSV complet: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("CORRECTION DES EXPORTS POUR CONTACTS SPÉCIFIQUES")
    logger.info("="*50)
    
    # 1. Analyser les fichiers des contacts spécifiques
    logger.info("\n=== ÉTAPE 1: ANALYSE DES FICHIERS PAR CONTACT ===")
    create_merged_export()
    
    # 2. Corriger le CSV complet pour fusionner les messages par contact
    logger.info("\n=== ÉTAPE 2: CORRECTION DU CSV COMPLET ===")
    correct_complete_csv()
    
    logger.info("\n===== OPÉRATION TERMINÉE =====")
    logger.info("Fichiers créés:")
    logger.info("1. contacts_specifiques_merged.txt - Messages fusionnés par contact pour les contacts spécifiés")
    logger.info("2. contacts_specifiques_merged.csv - Version CSV des messages fusionnés par contact")
    logger.info("3. messages_recus_complet_merged.csv - Version fusionnée du CSV complet (une ligne par contact)")
    
    return True

if __name__ == "__main__":
    main()
    sys.exit(0)
