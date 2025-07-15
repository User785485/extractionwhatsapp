#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de correction manuelle qui bypasse le merger defaillant
"""

import os
import re
import json

def manual_fix():
    output_dir = r"C:\Datalead3webidu13juillet"
    
    print("=== CORRECTION MANUELLE ===")
    
    # 1. Trouver le fichier source principal
    source_file = None
    for name in ['all_conversations.txt', 'toutes_conversations.txt']:
        path = os.path.join(output_dir, name)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            source_file = path
            print(f"Fichier source trouve: {name}")
            break
    
    if not source_file:
        print("ERREUR: Pas de fichier source!")
        return
    
    # 2. Charger toutes les transcriptions
    transcriptions = {}
    mapping_dir = os.path.join(output_dir, '.transcription_mappings')
    
    if os.path.exists(mapping_dir):
        for file in os.listdir(mapping_dir):
            if file.endswith('_mappings.json'):
                with open(os.path.join(mapping_dir, file), 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                    for audio_file, data in mappings.items():
                        if 'transcription' in data:
                            # Extraire UUID
                            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_file)
                            if uuid_match:
                                uuid = uuid_match.group(1)
                                transcriptions[uuid] = data['transcription']
    
    print(f"Transcriptions trouvees: {len(transcriptions)}")
    
    # 3. Lire et fusionner
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les [AUDIO] avec transcriptions
    def replace_audio(match):
        audio_ref = match.group(1) if match.group(1) else None
        if not audio_ref:
            return '[AUDIO]'
        
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_ref)
        if uuid_match:
            uuid = uuid_match.group(1)
            if uuid in transcriptions:
                return f'[AUDIO TRANSCRIT] "{transcriptions[uuid]}"'
        
        return f'[AUDIO] {audio_ref}'
    
    pattern = r'\[AUDIO\](?:\s+([^\n\[\]]+))?'
    updated_content = re.sub(pattern, replace_audio, content)
    
    # 4. Sauvegarder
    target = os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"\n[OK] Fichier cree: {target}")
    print(f"[OK] Taille: {os.path.getsize(target)} octets")
    
    # 5. Faire de meme pour messages_recus.txt
    source_recus = os.path.join(output_dir, 'messages_recus.txt')
    if os.path.exists(source_recus):
        with open(source_recus, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_content = re.sub(pattern, replace_audio, content)
        
        target_recus = os.path.join(output_dir, 'messages_recus_avec_transcriptions.txt')
        with open(target_recus, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"\n[OK] Fichier messages recus cree: {target_recus}")
        print(f"[OK] Taille: {os.path.getsize(target_recus)} octets")

if __name__ == "__main__":
    manual_fix()
