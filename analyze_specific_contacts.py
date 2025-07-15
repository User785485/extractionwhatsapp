#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script d'analyse des contacts spécifiques mentionnés
"""

import csv
import os
import sys

# Liste des contacts à analyser
CONTACTS_TO_CHECK = [
    "_33_7_82_79_70_04",
    "_33_7_82_85_46_87",
    "_33_7_83_07_41_99",
    "_33_7_83_16_34_02",
    "_33_7_83_34_22_19"
]

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"
CSV_FILE = os.path.join(OUTPUT_DIR, "messages_recus_complet.csv")

def analyze_csv():
    """Analyse le fichier CSV pour les contacts spécifiques"""
    if not os.path.exists(CSV_FILE):
        print(f"Erreur: Fichier CSV introuvable: {CSV_FILE}")
        return False
    
    try:
        print(f"Analyse du fichier: {CSV_FILE}")
        
        # Lire tout le fichier CSV
        with open(CSV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            headers = next(reader)  # Lire les en-têtes
            
            # Stocker toutes les lignes par contact
            rows_by_contact = {}
            for contact in CONTACTS_TO_CHECK:
                rows_by_contact[contact] = []
            
            # Analyser chaque ligne
            total_rows = 0
            for row in reader:
                if not row or len(row) < len(headers):
                    continue
                    
                contact = row[0]
                if contact in CONTACTS_TO_CHECK:
                    rows_by_contact[contact].append(row)
                    total_rows += 1
        
        print(f"\nTOTAL de {total_rows} lignes trouvées pour les contacts spécifiés")
        
        # Analyser les résultats par contact
        for contact, rows in rows_by_contact.items():
            print(f"\n{'='*50}")
            print(f"CONTACT: {contact} - {len(rows)} messages")
            
            if not rows:
                print("  Aucun message trouvé pour ce contact")
                continue
            
            # Analyser les types de messages
            message_types = {}
            for row in rows:
                msg_type = row[3] if len(row) > 3 else "INCONNU"
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            print("  Types de messages:")
            for msg_type, count in message_types.items():
                print(f"    - {msg_type}: {count} messages")
            
            # Vérifier les transcriptions
            transcriptions = [row for row in rows if len(row) > 6 and row[6].strip()]
            print(f"  Messages avec transcription: {len(transcriptions)}")
            
            # Afficher quelques exemples de messages
            if rows:
                print("\n  PREMIER MESSAGE:")
                for i, header in enumerate(headers):
                    if i < len(rows[0]):
                        value = rows[0][i]
                        # Limiter la taille de l'affichage
                        if len(value) > 50:
                            value = value[:47] + "..."
                        print(f"    {header}: {value}")
                
                print("\n  DERNIER MESSAGE:")
                for i, header in enumerate(headers):
                    if i < len(rows[-1]):
                        value = rows[-1][i]
                        if len(value) > 50:
                            value = value[:47] + "..."
                        print(f"    {header}: {value}")
        
        # Vérifier les fichiers texte individuels
        print(f"\n{'='*50}")
        print("VÉRIFICATION DES FICHIERS TEXTE INDIVIDUELS:")
        
        for contact in CONTACTS_TO_CHECK:
            contact_dir = os.path.join(OUTPUT_DIR, contact)
            messages_file = os.path.join(contact_dir, 'messages_recus.txt')
            
            if not os.path.exists(messages_file):
                print(f"\n{contact} - Fichier messages_recus.txt absent")
                continue
                
            try:
                with open(messages_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                size = os.path.getsize(messages_file)
                lines = content.split('\n')
                
                print(f"\n{contact} - Fichier de {size} octets, {len(lines)} lignes")
                
                # Chercher des exemples de messages audio
                audio_lines = [line for line in lines if '[AUDIO]' in line]
                
                print(f"  Messages audio: {len(audio_lines)}")
                
                if audio_lines:
                    print("  Exemple de ligne audio:")
                    print(f"    {audio_lines[0][:100]}...")
                
                # Transcriptions dans ce dossier
                transcription_dir = os.path.join(contact_dir, 'transcriptions')
                if os.path.isdir(transcription_dir):
                    trans_files = [f for f in os.listdir(transcription_dir) if f.endswith('.txt')]
                    print(f"  Fichiers de transcription: {len(trans_files)}")
                    
                    if trans_files:
                        trans_file = os.path.join(transcription_dir, trans_files[0])
                        with open(trans_file, 'r', encoding='utf-8', errors='ignore') as f:
                            trans_content = f.read()
                        
                        print(f"  Exemple de contenu de transcription ({os.path.basename(trans_file)}):")
                        lines = trans_content.split('\n')
                        for i, line in enumerate(lines[:3]):
                            print(f"    {line[:100]}...")
                        if len(lines) > 3:
                            print("    ...")
            except Exception as e:
                print(f"  Erreur lors de la lecture du fichier pour {contact}: {str(e)}")
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'analyse: {str(e)}")
        return False

if __name__ == "__main__":
    analyze_csv()
