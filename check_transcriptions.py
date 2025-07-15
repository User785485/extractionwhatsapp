#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vérifier où sont les transcriptions et pourquoi elles ne s'affichent pas
"""

import os
import json

def check_transcriptions():
    """Vérifie l'état des transcriptions"""
    
    output_dir = r"C:\Users\Moham\Desktop\DataLeads"
    
    print("=== VÉRIFICATION DES TRANSCRIPTIONS ===\n")
    
    # 1. Vérifier le registre unifié
    registry_path = os.path.join(output_dir, ".unified_registry.json")
    if os.path.exists(registry_path):
        print("(v) Registre unifié trouvé")
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
            trans_count = len(registry.get('transcriptions', {}))
            print(f"  -> {trans_count} transcriptions dans le registre")
            
            # Afficher les hash des transcriptions
            if trans_count > 0:
                print("\n  Transcriptions trouvées :")
                for hash_id, trans_info in list(registry['transcriptions'].items())[:5]:
                    text_preview = trans_info['text'][:100] + "..." if len(trans_info['text']) > 100 else trans_info['text']
                    print(f"    - Hash: {hash_id[:16]}... ({trans_info['length']} caractères)")
                    print(f"      Aperçu: {text_preview}")
    else:
        print("(x) Registre unifié NON trouvé")
    
    # 2. Vérifier les fichiers de transcription pour les 3 contacts
    contacts_with_audio = [
        "+1 (516) 852-6657",
        "+212 623-265006", 
        "+212 623-344696"
    ]
    
    print("\n=== FICHIERS DE TRANSCRIPTION PAR CONTACT ===")
    
    for contact in contacts_with_audio:
        print(f"\n{contact}:")
        trans_dir = os.path.join(output_dir, contact, "transcriptions")
        
        if os.path.exists(trans_dir):
            print(f"  (v) Dossier transcriptions existe")
            files = os.listdir(trans_dir)
            print(f"  -> {len(files)} fichiers trouvés:")
            
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(trans_dir, file)
                    size = os.path.getsize(file_path)
                    print(f"    - {file} ({size} octets)")
                    
                    # Lire un aperçu
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Ignorer l'en-tête et prendre le début du texte
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if line.strip() and not line.startswith('=') and not line.startswith('Transcription') and not line.startswith('Période'):
                                preview = line[:100] + "..." if len(line) > 100 else line
                                print(f"      Aperçu: {preview}")
                                break
        else:
            print(f"  (x) Dossier transcriptions NON trouvé")
    
    # 3. Vérifier le mapping des fichiers
    print("\n=== MAPPING DES FICHIERS AUDIO ===")
    
    # Pour +212 623-265006, vérifier le mapping
    contact = "+212 623-265006"
    contact_dir = os.path.join(output_dir, contact)
    
    # Lister les fichiers audio originaux
    audio_files = []
    media_dir = os.path.join(contact_dir, "media_recus", "audio")
    if os.path.exists(media_dir):
        for file in os.listdir(media_dir):
            if file.startswith('received_'):
                audio_files.append(file)
    
    print(f"\nFichiers audio reçus pour {contact}:")
    for audio in sorted(audio_files)[:10]:  # Afficher les 10 premiers
        print(f"  - {audio}")
    
    # Vérifier les super fichiers
    super_dir = os.path.join(contact_dir, "SUPER_FICHIERS")
    if os.path.exists(super_dir):
        print(f"\nSuper fichiers pour {contact}:")
        for file in os.listdir(super_dir):
            if file.endswith('.mp3'):
                print(f"  - {file}")
    
    # 4. Vérifier pourquoi la fusion ne fonctionne pas
    print("\n=== DIAGNOSTIC DE LA FUSION ===")
    
    # Lire le fichier de conversation
    conv_file = os.path.join(contact_dir, "tous_messages.txt")
    if os.path.exists(conv_file):
        with open(conv_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Compter les références [AUDIO]
        audio_refs = content.count('[AUDIO]')
        transcrit_refs = content.count('[AUDIO TRANSCRIT]')
        
        print(f"Dans tous_messages.txt de {contact}:")
        print(f"  - Références [AUDIO]: {audio_refs}")
        print(f"  - Références [AUDIO TRANSCRIT]: {transcrit_refs}")
        
        # Chercher des exemples
        lines = content.split('\n')
        print("\nExemples de lignes avec [AUDIO]:")
        count = 0
        for line in lines:
            if '[AUDIO]' in line and count < 3:
                print(f"  -> {line.strip()}")
                count += 1

if __name__ == "__main__":
    check_transcriptions()
