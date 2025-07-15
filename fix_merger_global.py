#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic et correction pour le problème du fichier global vide
"""

import os
import sys
import shutil
from datetime import datetime

def check_source_files(output_dir):
    """Vérifie quels fichiers sources existent"""
    print("\n=== VÉRIFICATION DES FICHIERS SOURCES ===")
    
    files_to_check = [
        'toutes_conversations.txt',
        'all_conversations.txt',
        'messages_recus.txt',
        'tous_messages.txt'
    ]
    
    existing_files = []
    
    for filename in files_to_check:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✓ {filename}: {size:,} octets")
            if size > 1000:  # Plus de 1KB
                existing_files.append(filename)
        else:
            print(f"✗ {filename}: MANQUANT")
    
    return existing_files

def fix_merger_py():
    """Corrige le merger.py pour chercher le bon fichier source"""
    merger_path = os.path.join('exporters', 'merger.py')
    
    # Faire une sauvegarde
    backup_path = f"{merger_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(merger_path, backup_path)
    print(f"\nSauvegarde créée: {backup_path}")
    
    # Lire le fichier
    with open(merger_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la méthode _merge_global_file
    old_method = '''def _merge_global_file(self):
        """Met a jour le fichier global avec les transcriptions"""
        source = os.path.join(self.output_dir, 'toutes_conversations.txt')
        target = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')
        
        if not os.path.exists(source):
            logger.warning(f"Fichier source non trouve: {source}")
            return'''
    
    new_method = '''def _merge_global_file(self):
        """Met a jour le fichier global avec les transcriptions"""
        # Essayer plusieurs noms possibles pour le fichier source
        possible_sources = [
            'toutes_conversations.txt',
            'all_conversations.txt',
            'tous_messages.txt'
        ]
        
        source = None
        for filename in possible_sources:
            test_path = os.path.join(self.output_dir, filename)
            if os.path.exists(test_path) and os.path.getsize(test_path) > 100:
                source = test_path
                logger.info(f"Fichier source trouvé: {filename}")
                break
        
        if not source:
            logger.error("Aucun fichier source valide trouvé pour le merge global!")
            logger.error(f"Fichiers recherchés dans {self.output_dir}: {possible_sources}")
            return
        
        target = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')'''
    
    # Remplacer dans le contenu
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✓ Méthode _merge_global_file corrigée")
    else:
        print("⚠ Méthode _merge_global_file non trouvée, recherche alternative...")
        # Recherche plus flexible
        import re
        pattern = r'def _merge_global_file\(self\):[^}]+?return'
        if re.search(pattern, content, re.DOTALL):
            print("Pattern trouvé, remplacement...")
            # Insérer la nouvelle méthode après _merge_all_transcriptions
            insertion_point = content.find('def _merge_contact_files(self):')
            if insertion_point > 0:
                content = content[:insertion_point] + new_method.replace('def _merge_global_file(self):', '') + '\n\n    ' + content[insertion_point:]
    
    # Sauvegarder
    with open(merger_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Fichier merger.py mis à jour")

def create_diagnostic_script():
    """Crée un script pour diagnostiquer et corriger manuellement"""
    script_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de diagnostic et fusion manuelle"""

import os
import re
import json
import sys

def manual_merge():
    output_dir = r"C:\\Datalead3webidu13juillet"
    
    # 1. Trouver le fichier source
    print("Recherche du fichier source...")
    source_file = None
    for filename in ['all_conversations.txt', 'toutes_conversations.txt', 'tous_messages.txt']:
        test_path = os.path.join(output_dir, filename)
        if os.path.exists(test_path) and os.path.getsize(test_path) > 1000:
            source_file = test_path
            print(f"Fichier source trouvé: {filename} ({os.path.getsize(test_path):,} octets)")
            break
    
    if not source_file:
        print("ERREUR: Aucun fichier source trouvé!")
        return
    
    # 2. Charger les mappings de transcription
    print("\\nChargement des transcriptions...")
    transcriptions = {}
    mapping_dir = os.path.join(output_dir, '.transcription_mappings')
    
    if os.path.exists(mapping_dir):
        for file in os.listdir(mapping_dir):
            if file.endswith('_mappings.json'):
                with open(os.path.join(mapping_dir, file), 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
                    for audio_file, data in mappings.items():
                        if 'transcription' in data:
                            # Extraire l'UUID
                            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_file)
                            if uuid_match:
                                uuid = uuid_match.group(1)
                                transcriptions[uuid] = data['transcription']
    
    print(f"Transcriptions trouvées: {len(transcriptions)}")
    
    # 3. Lire et fusionner
    print("\\nFusion en cours...")
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern pour remplacer [AUDIO] xxxxx
    pattern = r'\\[AUDIO\\](?:\\s+([^\\n\\[\\]]+))?'
    replacements = 0
    
    def replace_func(match):
        nonlocal replacements
        audio_ref = match.group(1) if match.group(1) else None
        if not audio_ref:
            return '[AUDIO]'
        
        # Extraire UUID
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_ref)
        if uuid_match:
            uuid = uuid_match.group(1)
            if uuid in transcriptions:
                replacements += 1
                return f'[AUDIO TRANSCRIT] "{transcriptions[uuid]}"'
        
        return f'[AUDIO] {audio_ref}'
    
    updated_content = re.sub(pattern, replace_func, content)
    
    # 4. Sauvegarder
    target_file = os.path.join(output_dir, 'toutes_conversations_avec_transcriptions.txt')
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"\\n✓ Fichier créé: {target_file}")
    print(f"✓ {replacements} transcriptions ajoutées")
    print(f"✓ Taille finale: {os.path.getsize(target_file):,} octets")

if __name__ == "__main__":
    manual_merge()
'''
    
    with open('manual_merge.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("\n✓ Script de fusion manuelle créé: manual_merge.py")

def main():
    print("=== DIAGNOSTIC ET CORRECTION DU MERGER ===")
    
    # 1. Vérifier les fichiers sources
    output_dir = r"C:\Datalead3webidu13juillet"
    existing_files = check_source_files(output_dir)
    
    if not existing_files:
        print("\n❌ PROBLÈME CRITIQUE: Aucun fichier source valide trouvé!")
        print("Le problème vient de l'étape 1 (TextExporter)")
        print("\nSolutions possibles:")
        print("1. Relancer l'extraction complète: python main_enhanced.py")
        print("2. Ou relancer uniquement l'export de base: python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription")
        return
    
    # 2. Corriger le merger
    print("\n=== CORRECTION DU MERGER ===")
    try:
        fix_merger_py()
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {str(e)}")
    
    # 3. Créer le script de fusion manuelle
    create_diagnostic_script()
    
    print("\n=== PROCHAINES ÉTAPES ===")
    print("1. Exécuter la fusion manuelle:")
    print("   python manual_merge.py")
    print("\n2. Puis relancer uniquement l'export CSV:")
    print("   python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription --skip-merger")
    print("\nOu relancer tout l'export avec le merger corrigé:")
    print("   python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription --force-merger")

if __name__ == "__main__":
    main()