#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour consolider correctement tous les fichiers de messages avec les transcriptions
"""

import os
import re
import json
from datetime import datetime

def load_all_transcriptions(output_dir):
    """Charge toutes les transcriptions depuis les mappings"""
    transcriptions = {}
    mapping_dir = os.path.join(output_dir, '.transcription_mappings')
    
    if not os.path.exists(mapping_dir):
        print("X Repertoire de mappings non trouve!")
        return transcriptions
    
    # Charger tous les fichiers de mapping
    for file in os.listdir(mapping_dir):
        if file.endswith('_mappings.json'):
            filepath = os.path.join(mapping_dir, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                    
                for mp3_name, data in mappings.items():
                    if 'transcription' in data:
                        # Extraire l'UUID du nom MP3
                        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', mp3_name)
                        if uuid_match:
                            uuid = uuid_match.group(1)
                            transcriptions[uuid] = data['transcription']
                            # Convertir le nom MP3 en differents formats audio possibles
                            base_name = mp3_name.replace('.mp3', '').replace('audio_', '')
                            # Stocker pour tous les formats possibles
                            for ext in ['.opus', '.ogg', '.m4a']:
                                audio_name = base_name + ext
                                transcriptions[audio_name] = data['transcription']
            except Exception as e:
                print(f"! Erreur lecture {file}: {str(e)}")
    
    print(f"OK {len(transcriptions)} transcriptions chargees")
    return transcriptions

def process_message_file(content, transcriptions):
    """Traite un fichier de messages et remplace les [AUDIO] par les transcriptions"""
    lines = content.split('\n')
    processed_lines = []
    replacements = 0
    
    for line in lines:
        # Chercher les references [AUDIO]
        audio_match = re.search(r'\[AUDIO\]\s+([^\n]+)', line)
        if audio_match:
            audio_ref = audio_match.group(1).strip()
            
            # Extraire l'UUID
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_ref)
            if uuid_match:
                uuid = uuid_match.group(1)
                
                # Chercher la transcription
                transcription = None
                
                # 1. Essayer avec l'UUID seul
                if uuid in transcriptions:
                    transcription = transcriptions[uuid]
                # 2. Essayer avec le nom complet
                elif audio_ref in transcriptions:
                    transcription = transcriptions[audio_ref]
                
                if transcription:
                    # Remplacer [AUDIO] par [AUDIO TRANSCRIT]
                    new_line = line.replace(f'[AUDIO] {audio_ref}', f'[AUDIO TRANSCRIT] "{transcription}"')
                    processed_lines.append(new_line)
                    replacements += 1
                else:
                    processed_lines.append(line)
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines), replacements

def consolidate_all_messages(output_dir, transcriptions):
    """Consolide tous les messages de tous les contacts"""
    all_content = []
    all_content.append("TOUTES LES CONVERSATIONS WHATSAPP")
    all_content.append(f"Genere le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    all_content.append("=" * 60 + "\n")
    
    received_content = []
    received_content.append("MESSAGES RECUS UNIQUEMENT")
    received_content.append(f"Genere le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    received_content.append("=" * 60 + "\n")
    
    total_messages = 0
    total_received = 0
    total_replacements = 0
    
    # Parcourir tous les contacts
    contacts = [d for d in os.listdir(output_dir) 
                if os.path.isdir(os.path.join(output_dir, d)) 
                and not d.startswith('.')]
    
    print(f"\nTraitement de {len(contacts)} contacts...")
    
    for i, contact in enumerate(sorted(contacts)):
        contact_dir = os.path.join(output_dir, contact)
        
        # Fichier tous messages
        all_msg_file = os.path.join(contact_dir, 'tous_messages.txt')
        if os.path.exists(all_msg_file) and os.path.getsize(all_msg_file) > 0:
            try:
                with open(all_msg_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Traiter le contenu avec les transcriptions
                processed_content, replacements = process_message_file(content, transcriptions)
                total_replacements += replacements
                
                # Ajouter au fichier global
                all_content.append(f"\n{'='*60}")
                all_content.append(f"CONVERSATION: {contact}")
                all_content.append(f"{'='*60}\n")
                all_content.append(processed_content)
                
                # Compter les messages
                messages = re.findall(r'\[\d{2}:\d{2}\]', content)
                total_messages += len(messages)
                
                # Sauvegarder la version avec transcriptions dans le contact
                target_file = os.path.join(contact_dir, 'tous_messages_avec_transcriptions.txt')
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                
            except Exception as e:
                print(f"! Erreur avec {contact}: {str(e)}")
        
        # Fichier messages recus
        received_file = os.path.join(contact_dir, 'messages_recus.txt')
        if os.path.exists(received_file) and os.path.getsize(received_file) > 0:
            try:
                with open(received_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Traiter avec transcriptions
                processed_content, _ = process_message_file(content, transcriptions)
                
                # Ajouter au fichier des messages recus
                received_content.append(f"\n{'='*40}")
                received_content.append(f"CONTACT: {contact}")
                received_content.append(f"{'='*40}\n")
                received_content.append(processed_content)
                
                # Compter
                messages = re.findall(r'\[\d{4}/\d{2}/\d{2} \d{2}:\d{2}\]', content)
                total_received += len(messages)
                
                # Sauvegarder dans le contact
                target_file = os.path.join(contact_dir, 'messages_recus_avec_transcriptions.txt')
                with open(target_file, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                    
            except Exception as e:
                print(f"! Erreur messages recus {contact}: {str(e)}")
        
        # Afficher la progression
        if (i + 1) % 50 == 0:
            print(f"  Traite: {i + 1}/{len(contacts)} contacts...")
    
    # Ajouter les statistiques
    all_content.append(f"\n\n{'='*60}")
    all_content.append(f"STATISTIQUES GLOBALES:")
    all_content.append(f"  - Contacts: {len(contacts)}")
    all_content.append(f"  - Total messages: {total_messages}")
    all_content.append(f"  - Transcriptions ajoutees: {total_replacements}")
    
    received_content.append(f"\n\n{'='*60}")
    received_content.append(f"STATISTIQUES:")
    received_content.append(f"  - Contacts: {len(contacts)}")
    received_content.append(f"  - Messages recus: {total_received}")
    
    # Sauvegarder les fichiers globaux
    global_file = os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt')
    with open(global_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_content))
    print(f"\nOK Fichier global cree: {global_file}")
    print(f"  Taille: {os.path.getsize(global_file):,} octets")
    
    received_global = os.path.join(output_dir, 'messages_recus_avec_transcriptions.txt')
    with open(received_global, 'w', encoding='utf-8') as f:
        f.write('\n'.join(received_content))
    print(f"\nOK Fichier messages recus cree: {received_global}")
    print(f"  Taille: {os.path.getsize(received_global):,} octets")
    
    print(f"\nRESUME:")
    print(f"  - Contacts traites: {len(contacts)}")
    print(f"  - Messages totaux: {total_messages}")
    print(f"  - Messages recus: {total_received}")
    print(f"  - Transcriptions ajoutees: {total_replacements}")

def main():
    print("=== CONSOLIDATION DES MESSAGES AVEC TRANSCRIPTIONS ===")
    
    output_dir = r"C:\Datalead3webidu13juillet"
    if not os.path.exists(output_dir):
        print(f"ERREUR: Le dossier de sortie n'existe pas: {output_dir}")
        sys.exit(1)
        
    # Vérifier les permissions d'écriture
    test_file = os.path.join(output_dir, "_test_write_permission.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("Test d'écriture")
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✓ Test d'écriture réussi")
    except Exception as e:
        print(f"ERREUR de permission d'écriture: {str(e)}")
        sys.exit(1)
    
    # 1. Charger toutes les transcriptions
    print("\n1. Chargement des transcriptions...")
    transcriptions = load_all_transcriptions(output_dir)
    
    if not transcriptions:
        print("X Aucune transcription trouvee! Arret.")
        return
    
    # 2. Consolider tous les messages
    print("\n2. Consolidation des messages...")
    consolidate_all_messages(output_dir, transcriptions)
    
    print("\nOK Consolidation terminee avec succes!")
    print("\nVous pouvez maintenant lancer:")
    print("python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription")

if __name__ == "__main__":
    main()