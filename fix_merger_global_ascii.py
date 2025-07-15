#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic complet pour comprendre pourquoi l'export échoue
"""

import os
import sys
import re
import json
from datetime import datetime

def check_all_files():
    """Vérifie tous les fichiers importants"""
    output_dir = r"C:\Datalead3webidu13juillet"
    print(f"\n=== DIAGNOSTIC COMPLET DU RÉPERTOIRE {output_dir} ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Vérifier les fichiers de base
    print("1. FICHIERS DE BASE:")
    print("-" * 50)
    base_files = [
        'all_conversations.txt',
        'toutes_conversations.txt',
        'messages_recus.txt',
        'tous_messages.txt'
    ]
    
    found_base = False
    for filename in base_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✓ {filename}: {size:,} octets")
            if size > 1000:
                found_base = True
                # Afficher un échantillon
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(500)
                    print(f"  Échantillon: {sample[:100]}...")
        else:
            print(f"✗ {filename}: MANQUANT")
    
    if not found_base:
        print("\n❌ PROBLÈME: Aucun fichier de base valide trouvé!")
    
    # 2. Vérifier les fichiers fusionnés
    print("\n2. FICHIERS FUSIONNÉS:")
    print("-" * 50)
    fused_files = [
        'toutes_conversations_avec_transcriptions.txt',
        'messages_recus_avec_transcriptions.txt'
    ]
    
    for filename in fused_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"{'✓' if size > 1000 else '⚠'} {filename}: {size:,} octets")
            if size < 1000:
                # Afficher tout le contenu si petit
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    print(f"  Contenu complet:\n{content}\n")
        else:
            print(f"✗ {filename}: MANQUANT")
    
    # 3. Vérifier les transcriptions
    print("\n3. TRANSCRIPTIONS DISPONIBLES:")
    print("-" * 50)
    mapping_dir = os.path.join(output_dir, '.transcription_mappings')
    if os.path.exists(mapping_dir):
        total_transcriptions = 0
        for file in os.listdir(mapping_dir):
            if file.endswith('_mappings.json'):
                filepath = os.path.join(mapping_dir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        total_transcriptions += len(data)
                except:
                    pass
        print(f"✓ Total transcriptions dans les mappings: {total_transcriptions}")
    else:
        print("✗ Répertoire de mappings manquant")
    
    # 4. Vérifier un contact au hasard
    print("\n4. EXEMPLE DE CONTACT:")
    print("-" * 50)
    try:
        contacts = [d for d in os.listdir(output_dir) 
                   if os.path.isdir(os.path.join(output_dir, d)) 
                   and not d.startswith('.')]
        if contacts:
            sample_contact = contacts[0]
            contact_dir = os.path.join(output_dir, sample_contact)
            print(f"Contact exemple: {sample_contact}")
            
            # Vérifier les fichiers du contact
            for filename in ['tous_messages.txt', 'messages_recus.txt']:
                filepath = os.path.join(contact_dir, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    print(f"  ✓ {filename}: {size:,} octets")
                    
                    # Chercher des [AUDIO] dans le fichier
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        audio_refs = re.findall(r'\[AUDIO\](?:\s+([^\n\[\]]+))?', content)
                        if audio_refs:
                            print(f"    - {len(audio_refs)} références [AUDIO] trouvées")
                            print(f"    - Exemple: {audio_refs[0] if audio_refs[0] else 'vide'}")
    except Exception as e:
        print(f"Erreur: {str(e)}")
    
    return output_dir

def create_manual_fix():
    """Crée un script de correction manuelle"""
    fix_script = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de correction manuelle qui bypasse le merger défaillant
"""

import os
import re
import json

def manual_fix():
    output_dir = r"C:\\Datalead3webidu13juillet"
    
    print("=== CORRECTION MANUELLE ===")
    
    # 1. Trouver le fichier source principal
    source_file = None
    for name in ['all_conversations.txt', 'toutes_conversations.txt']:
        path = os.path.join(output_dir, name)
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            source_file = path
            print(f"Fichier source trouvé: {name}")
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
    
    print(f"Transcriptions trouvées: {len(transcriptions)}")
    
    # 3. Lire et fusionner
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les [AUDIO] avec transcriptions
    def replace_audio(match):
        audio_ref = match.group(1) if match.group(1) else None
        if not audio_ref:
            return '[AUDIO]'
        
        # Extraire UUID
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_ref)
        if uuid_match:
            uuid = uuid_match.group(1)
            if uuid in transcriptions:
                return f'[AUDIO TRANSCRIT] "{transcriptions[uuid]}"'
        
        return f'[AUDIO] {audio_ref}'
    
    pattern = r'\\[AUDIO\\](?:\\s+([^\\n\\[\\]]+))?'
    updated_content = re.sub(pattern, replace_audio, content)
    
    # 4. Sauvegarder
    target = os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt')
    with open(target, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"\\n✓ Fichier créé: {target}")
    print(f"✓ Taille: {os.path.getsize(target):,} octets")
    
    # 5. Faire de même pour messages_recus.txt
    source_recus = os.path.join(output_dir, 'messages_recus.txt')
    if os.path.exists(source_recus):
        with open(source_recus, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_content = re.sub(pattern, replace_audio, content)
        
        target_recus = os.path.join(output_dir, 'messages_recus_avec_transcriptions.txt')
        with open(target_recus, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"\\n✓ Fichier messages reçus créé: {target_recus}")
        print(f"✓ Taille: {os.path.getsize(target_recus):,} octets")

if __name__ == "__main__":
    manual_fix()
'''
    
    with open('manual_fix.py', 'w', encoding='utf-8') as f:
        f.write(fix_script)
    
    print("\n✓ Script de correction créé: manual_fix.py")

def analyze_merger_issue():
    """Analyse pourquoi le merger échoue"""
    print("\n5. ANALYSE DU PROBLÈME DU MERGER:")
    print("-" * 50)
    
    # Vérifier si le merger trouve les bons fichiers
    output_dir = r"C:\Datalead3webidu13juillet"
    
    # Le merger cherche 'toutes_conversations.txt'
    old_name = os.path.join(output_dir, 'toutes_conversations.txt')
    new_name = os.path.join(output_dir, 'all_conversations.txt')
    
    if not os.path.exists(old_name) and os.path.exists(new_name):
        print("❌ PROBLÈME IDENTIFIÉ:")
        print(f"   - Le merger cherche: toutes_conversations.txt")
        print(f"   - Mais le fichier s'appelle: all_conversations.txt")
        print("\nSOLUTION: Renommer le fichier")
        
        # Proposer de renommer
        print("\nVoulez-vous renommer le fichier maintenant? (y/n)")
        response = input().strip().lower()
        if response == 'y':
            try:
                os.rename(new_name, old_name)
                print(f"✓ Fichier renommé avec succès!")
            except Exception as e:
                print(f"❌ Erreur: {str(e)}")

def main():
    print("=== DIAGNOSTIC COMPLET DE L'EXPORT WHATSAPP ===")
    
    # 1. Diagnostic complet
    output_dir = check_all_files()
    
    # 2. Analyser le problème
    analyze_merger_issue()
    
    # 3. Créer le script de correction
    create_manual_fix()
    
    print("\n=== SOLUTIONS PROPOSÉES ===")
    print("\n1. CORRECTION MANUELLE (recommandé):")
    print("   python manual_fix.py")
    print("   python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription")
    
    print("\n2. RENOMMER LE FICHIER et relancer:")
    print("   Renommer all_conversations.txt en toutes_conversations.txt")
    print("   python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription --force-merger")
    
    print("\n3. SI TOUT ÉCHOUE, utiliser l'export robuste:")
    print("   python fix_export.py")

if __name__ == "__main__":
    main()