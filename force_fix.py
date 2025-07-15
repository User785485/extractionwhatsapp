#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import time
from datetime import datetime

def force_fix_files():
    """Force la correction des fichiers en copiant les fichiers bien nommés"""
    output_dir = r"C:\Datalead3webidu13juillet"
    print("=== CORRECTION FORCÉE DES FICHIERS ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Répertoire: {output_dir}\n")
    
    # Vérifier si le dossier existe
    if not os.path.exists(output_dir):
        print(f"ERREUR: Le dossier n'existe pas: {output_dir}")
        return False
    
    # Tester les permissions d'écriture
    test_file = os.path.join(output_dir, "_test_permission.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("Test d'écriture")
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✓ Permissions d'écriture OK")
    except Exception as e:
        print(f"ERREUR de permission: {str(e)}")
        return False
    
    # Récupérer les chemins des fichiers existants
    file_paths = {}
    for root, _, files in os.walk(output_dir):
        for filename in files:
            if filename.endswith('.txt'):
                full_path = os.path.join(root, filename)
                size = os.path.getsize(full_path)
                # On ne garde que les fichiers de plus de 1MB
                if size > 1000000:
                    print(f"Fichier trouvé: {filename} ({size:,} octets)")
                    file_paths[filename] = {
                        'path': full_path,
                        'size': size
                    }
    
    # Créer les noms de fichiers cibles
    target_files = [
        'toutes_conversations.txt',
        'toutes_conversations_avec_transcriptions.txt',
        'messages_recus.txt',
        'messages_recus_avec_transcriptions.txt'
    ]
    
    # S'il y a un fichier source de taille correcte mais pas les fichiers cibles
    # Utiliser le plus grand fichier comme source
    if file_paths:
        print("\nFichiers sources trouvés!")
        
        # Identifier le plus grand fichier pour les conversations
        conversations_files = [f for f in file_paths if 'conversation' in f.lower()]
        if conversations_files:
            largest_conv = max(conversations_files, key=lambda x: file_paths[x]['size'])
            print(f"Plus grand fichier de conversations: {largest_conv} ({file_paths[largest_conv]['size']:,} octets)")
            
            # Copier vers les fichiers cibles
            for target in ['toutes_conversations.txt', 'toutes_conversations_avec_transcriptions.txt']:
                target_path = os.path.join(output_dir, target)
                
                # Faire une sauvegarde
                if os.path.exists(target_path):
                    backup_path = target_path + '.bak'
                    try:
                        shutil.copy2(target_path, backup_path)
                        print(f"✓ Sauvegarde créée: {backup_path}")
                    except Exception as e:
                        print(f"! Erreur de sauvegarde: {str(e)}")
                
                # Copier le fichier source
                try:
                    shutil.copy2(file_paths[largest_conv]['path'], target_path)
                    print(f"✓ Fichier créé: {target} ({os.path.getsize(target_path):,} octets)")
                except Exception as e:
                    print(f"! Erreur de copie: {str(e)}")
        
        # Identifier le plus grand fichier pour les messages reçus
        messages_files = [f for f in file_paths if 'recu' in f.lower() or 'reçu' in f.lower()]
        if messages_files:
            largest_msg = max(messages_files, key=lambda x: file_paths[x]['size'])
            print(f"Plus grand fichier de messages: {largest_msg} ({file_paths[largest_msg]['size']:,} octets)")
            
            # Copier vers les fichiers cibles
            for target in ['messages_recus.txt', 'messages_recus_avec_transcriptions.txt']:
                target_path = os.path.join(output_dir, target)
                
                # Faire une sauvegarde
                if os.path.exists(target_path):
                    backup_path = target_path + '.bak'
                    try:
                        shutil.copy2(target_path, backup_path)
                        print(f"✓ Sauvegarde créée: {backup_path}")
                    except Exception as e:
                        print(f"! Erreur de sauvegarde: {str(e)}")
                
                # Copier le fichier source
                try:
                    shutil.copy2(file_paths[largest_msg]['path'], target_path)
                    print(f"✓ Fichier créé: {target} ({os.path.getsize(target_path):,} octets)")
                except Exception as e:
                    print(f"! Erreur de copie: {str(e)}")
    else:
        print("! Aucun fichier source de taille correcte trouvé")
        return False
    
    # Forcer le flush des fichiers
    time.sleep(2)
    
    # Vérifier les fichiers
    print("\nVérification finale des fichiers:")
    all_ok = True
    for filename in target_files:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 1000000:
                print(f"✓ {filename}: {size:,} octets")
            else:
                print(f"✗ {filename}: Trop petit ({size:,} octets)")
                all_ok = False
        else:
            print(f"✗ {filename}: MANQUANT")
            all_ok = False
    
    if all_ok:
        print("\nCORRECTION RÉUSSIE!")
        print("Vous pouvez maintenant lancer:")
        print("python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription")
        return True
    else:
        print("\nCertains fichiers n'ont pas pu être corrigés.")
        return False

if __name__ == "__main__":
    if force_fix_files():
        sys.exit(0)
    else:
        sys.exit(1)
