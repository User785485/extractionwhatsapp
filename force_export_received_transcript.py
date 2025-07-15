#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de génération forcée du fichier messages_recus_avec_transcriptions.txt
Ce script parcourt tous les dossiers de contact, trouve les transcriptions
et génère directement le fichier principal avec les transcriptions.
"""

import os
import re
import json
import shutil
import logging
import sys
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
logger = logging.getLogger('force_export')

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"

def find_transcription_files():
    """Trouve tous les fichiers de transcription dans les dossiers de contact"""
    transcription_files = []
    contact_folders = []

    # Trouver tous les dossiers de contact (commençant par _)
    for item in os.listdir(OUTPUT_DIR):
        if os.path.isdir(os.path.join(OUTPUT_DIR, item)) and item.startswith('_'):
            contact_folders.append(item)

    logger.info(f"Trouvé {len(contact_folders)} dossiers de contact")

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
    return transcription_files, contact_folders

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

def find_message_with_audio(messages_file, audio_uuid):
    """Trouve un message contenant un audio avec l'UUID spécifié"""
    try:
        with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Chercher des lignes contenant l'UUID
        pattern = r'\[(.*?)\] ← \[AUDIO\] .*?' + audio_uuid
        match = re.search(pattern, content)
        if match:
            return match.group(0), match.group(1)  # ligne complète, date/heure
        return None, None
    except Exception as e:
        logger.error(f"Erreur recherche message {messages_file}: {str(e)}")
        return None, None

def generate_messages_with_transcriptions():
    """Génère le fichier messages_recus_avec_transcriptions.txt"""
    transcription_files, contact_folders = find_transcription_files()
    
    # Fichier de sortie
    output_file = os.path.join(OUTPUT_DIR, 'messages_recus_avec_transcriptions.txt')
    
    # Sauvegarde si le fichier existe déjà
    if os.path.exists(output_file):
        backup = f"{output_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(output_file, backup)
        logger.info(f"Sauvegarde créée: {backup}")
    
    # Collecter toutes les transcriptions
    all_transcriptions = []
    total_transcriptions = 0
    
    for contact in contact_folders:
        contact_dir = os.path.join(OUTPUT_DIR, contact)
        messages_file = os.path.join(contact_dir, 'tous_messages.txt')
        
        if not os.path.exists(messages_file):
            logger.warning(f"Fichier messages non trouvé pour {contact}")
            continue
        
        contact_transcriptions = []
        
        # Trouver les transcriptions pour ce contact
        for trans in transcription_files:
            if trans['contact'] == contact:
                uuid = extract_uuid_from_filename(trans['file'])
                if uuid:
                    # Trouver le message correspondant
                    message_line, timestamp = find_message_with_audio(messages_file, uuid)
                    transcription_text = read_transcription_file(trans['path'])
                    
                    if message_line and transcription_text:
                        # Format: [Date Heure] ← [AUDIO] fichier.opus
                        # Devient: [Date Heure] ← [AUDIO] fichier.opus
                        #          [TRANSCRIPTION] texte de la transcription
                        entry = f"{message_line}\n[TRANSCRIPTION] {transcription_text}"
                        contact_transcriptions.append({
                            'timestamp': timestamp,
                            'entry': entry
                        })
                        total_transcriptions += 1
        
        if contact_transcriptions:
            # Trier par timestamp
            contact_transcriptions.sort(key=lambda x: x['timestamp'] if x['timestamp'] else "")
            
            # Ajouter au résultat global
            all_transcriptions.append({
                'contact': contact,
                'transcriptions': [t['entry'] for t in contact_transcriptions]
            })
    
    # Générer le fichier final
    with open(output_file, 'w', encoding='utf-8') as f:
        # Écrire l'en-tête
        f.write("TOUS LES MESSAGES REÇUS AVEC TRANSCRIPTIONS\n")
        f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        
        for contact_data in all_transcriptions:
            contact = contact_data['contact']
            if not contact_data['transcriptions']:
                continue
                
            f.write(f"\n{'='*30}\n")
            f.write(f"DE: {contact}\n")
            f.write(f"{'='*30}\n\n")
            
            for entry in contact_data['transcriptions']:
                f.write(f"{entry}\n\n")
        
        # Ajouter un résumé
        f.write(f"\n\nTOTAL MESSAGES REÇUS AVEC TRANSCRIPTIONS: {total_transcriptions}\n")
    
    size = os.path.getsize(output_file)
    logger.info(f"Fichier généré: {output_file} - Taille: {size} octets")
    
    return output_file, size, total_transcriptions

def generate_csv_export():
    """Force la génération du fichier CSV à partir du fichier transcriptions généré"""
    try:
        # Appeler directement le CSVExporter pour générer le CSV à partir de notre fichier
        import sys
        from exporters.csv_exporter import CSVExporter
        
        logger.info("Création directe du CSV à partir du fichier de transcriptions...")
        exporter = CSVExporter(OUTPUT_DIR)
        
        # Appel direct à la méthode d'export avec le bon fichier source
        result = exporter.export_special_csv(received_only=True)
        
        if result:
            logger.info("Fichier CSV généré avec succès")
            return True
        else:
            logger.error("Échec de génération du fichier CSV")
            return False
    except Exception as e:
        logger.error(f"Erreur lors de la génération CSV: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    logger.info("="*50)
    logger.info("GÉNÉRATION FORCÉE DU FICHIER MESSAGES_RECUS_AVEC_TRANSCRIPTIONS")
    logger.info("="*50)
    
    try:
        # Générer le fichier avec transcriptions
        output_file, size, count = generate_messages_with_transcriptions()
        
        if size < 1000:  # Moins de 1 Ko
            logger.warning(f"Fichier généré anormalement petit: {size} octets")
            if count == 0:
                logger.error("Aucune transcription trouvée!")
                return False
        
        # Générer le CSV correspondant
        logger.info("\nGénération du fichier CSV...")
        generate_csv_export()
        
        # Vérifier les fichiers générés
        csv_file = os.path.join(OUTPUT_DIR, 'messages_recus_only.csv')
        if os.path.exists(csv_file):
            csv_size = os.path.getsize(csv_file)
            logger.info(f"Fichier CSV généré: {csv_size} octets")
            if csv_size < 1000:
                logger.warning("Fichier CSV anormalement petit!")
        else:
            logger.warning("Fichier CSV non généré!")
        
        logger.info("\n===== OPÉRATION TERMINÉE =====")
        return True
    except Exception as e:
        logger.error(f"Erreur critique: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
