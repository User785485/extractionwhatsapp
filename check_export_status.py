#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour vérifier l'état de l'export
"""

import os
import sys
import json
import configparser
from datetime import datetime

def get_output_dir():
    """Récupère le répertoire de sortie depuis la config"""
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
        return config.get('Paths', 'output_dir')
    except:
        return os.path.join(os.path.expanduser('~'), 'Desktop', 'DataLeads')

def format_size(size):
    """Formate la taille en unités lisibles"""
    if size < 1024:
        return f"{size} octets"
    elif size < 1024 * 1024:
        return f"{size/1024:.2f} KB"
    else:
        return f"{size/(1024*1024):.2f} MB"

def check_files():
    """Vérifie l'état de tous les fichiers importants"""
    output_dir = get_output_dir()
    print(f"\n📁 Répertoire de sortie: {output_dir}\n")
    
    # Liste des fichiers à vérifier avec leur importance
    files_to_check = [
        ("📝 Fichiers de base (étape 1)", [
            "all_conversations.txt",
            "toutes_conversations.txt",
            "messages_recus.txt"
        ]),
        ("🔄 Fichiers fusionnés (étape 2)", [
            "toutes_conversations_avec_transcriptions.txt",
            "messages_recus_avec_transcriptions.txt"
        ]),
        ("📊 Fichiers CSV (étape 3-4)", [
            "messages_recus_only.csv",
            "messages_all.csv",
            "messages_recus_par_contact.csv",
            "contacts_messages_simplifies.csv"
        ]),
        ("📑 Fichiers Excel", [
            "messages_recus_only.xlsx",
            "messages_all.xlsx",
            "contacts_messages_simplifies.xlsx"
        ])
    ]
    
    total_ok = 0
    total_missing = 0
    total_empty = 0
    
    for category, files in files_to_check:
        print(f"\n{category}:")
        print("-" * 50)
        
        for filename in files:
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                if size == 0:
                    print(f"  ⚠️  {filename}: VIDE!")
                    total_empty += 1
                elif size < 1000:
                    print(f"  ⚠️  {filename}: {format_size(size)} (très petit!)")
                    total_ok += 1
                else:
                    print(f"  ✅ {filename}: {format_size(size)}")
                    total_ok += 1
            else:
                print(f"  ❌ {filename}: MANQUANT")
                total_missing += 1
    
    # Vérifier le registre
    print(f"\n🗄️  Registre unifié:")
    print("-" * 50)
    registry_file = os.path.join(output_dir, '.unified_registry.json')
    if os.path.exists(registry_file):
        size = os.path.getsize(registry_file)
        print(f"  ✅ .unified_registry.json: {format_size(size)}")
        
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            audio_count = sum(1 for f in registry.get('files', {}).values() if f.get('type') == 'audio')
            trans_count = len(registry.get('transcriptions', {}))
            
            print(f"     - Fichiers audio: {audio_count}")
            print(f"     - Transcriptions: {trans_count}")
            if audio_count > 0:
                print(f"     - Taux de transcription: {trans_count/audio_count*100:.1f}%")
        except:
            print("     ⚠️  Impossible de lire le registre")
    else:
        print(f"  ❌ .unified_registry.json: MANQUANT")
    
    # Résumé
    print(f"\n📈 RÉSUMÉ:")
    print("=" * 50)
    print(f"  ✅ Fichiers OK: {total_ok}")
    print(f"  ⚠️  Fichiers vides: {total_empty}")
    print(f"  ❌ Fichiers manquants: {total_missing}")
    
    if total_missing > 5:
        print(f"\n⚠️  DIAGNOSTIC: Beaucoup de fichiers manquent!")
        print("   → L'export n'a probablement pas fonctionné correctement")
        print("   → Exécutez: python fix_main_export.py")
    elif total_empty > 2:
        print(f"\n⚠️  DIAGNOSTIC: Plusieurs fichiers sont vides!")
        print("   → Les fichiers sources n'ont pas été correctement fusionnés")
        print("   → Exécutez: python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription --force-merger")
    else:
        print(f"\n✅ DIAGNOSTIC: L'export semble avoir fonctionné!")

if __name__ == "__main__":
    check_files()