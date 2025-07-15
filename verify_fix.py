#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import time

def verify_and_fix():
    """Vérifie et répare les fichiers consolidés"""
    print("=== VÉRIFICATION ET RÉPARATION DES FICHIERS CONSOLIDÉS ===")
    
    output_dir = r"C:\Datalead3webidu13juillet"
    
    # Vérification des fichiers
    files_to_check = [
        'toutes_conversations.txt',
        'messages_recus.txt',
        'toutes_conversations_avec_transcriptions.txt',
        'messages_recus_avec_transcriptions.txt'
    ]
    
    files_info = {}
    for filename in files_to_check:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            files_info[filename] = {
                'exists': True,
                'size': size,
                'path': filepath
            }
            print(f"  {filename}: {size:,} octets")
        else:
            files_info[filename] = {
                'exists': False,
                'size': 0,
                'path': filepath
            }
            print(f"  {filename}: MANQUANT")
    
    # Vérification des problèmes
    problems = []
    if files_info['toutes_conversations_avec_transcriptions.txt']['size'] < 1000000:
        problems.append("Le fichier toutes_conversations_avec_transcriptions.txt est trop petit")
    
    if files_info['messages_recus_avec_transcriptions.txt']['size'] < 100000:
        problems.append("Le fichier messages_recus_avec_transcriptions.txt est trop petit")
    
    if not problems:
        print("\nTout semble correct!")
        return
    
    print("\nProblèmes détectés:")
    for problem in problems:
        print(f"  - {problem}")
    
    # Tentative de réparation
    print("\nTentative de réparation...")
    
    # Si les fichiers consolidés sont créés par correction.py mais pas utilisés par main_enhanced.py
    # On va créer des copies avec le bon chemin
    if files_info['toutes_conversations_avec_transcriptions.txt']['exists'] and files_info['toutes_conversations_avec_transcriptions.txt']['size'] < 1000000:
        # Vérifier si le fichier source existe
        source_file = files_info['toutes_conversations.txt']['path']
        if os.path.exists(source_file) and os.path.getsize(source_file) > 1000000:
            # Faire une sauvegarde du petit fichier
            target_file = files_info['toutes_conversations_avec_transcriptions.txt']['path']
            if os.path.exists(target_file):
                backup_file = target_file + '.bak'
                try:
                    shutil.copy2(target_file, backup_file)
                    print(f"  Backup créé: {backup_file}")
                except Exception as e:
                    print(f"  Erreur lors de la création du backup: {str(e)}")
            
            # Copier le fichier source vers le fichier cible
            try:
                shutil.copy2(source_file, target_file)
                new_size = os.path.getsize(target_file)
                print(f"  ✓ Réparation effectuée: {target_file} ({new_size:,} octets)")
            except Exception as e:
                print(f"  ✗ Erreur lors de la réparation: {str(e)}")
    
    # Même chose pour messages_recus
    if files_info['messages_recus_avec_transcriptions.txt']['exists'] and files_info['messages_recus_avec_transcriptions.txt']['size'] < 100000:
        # Vérifier si le fichier source existe
        source_file = files_info['messages_recus.txt']['path']
        if os.path.exists(source_file) and os.path.getsize(source_file) > 100000:
            # Faire une sauvegarde du petit fichier
            target_file = files_info['messages_recus_avec_transcriptions.txt']['path']
            if os.path.exists(target_file):
                backup_file = target_file + '.bak'
                try:
                    shutil.copy2(target_file, backup_file)
                    print(f"  Backup créé: {backup_file}")
                except Exception as e:
                    print(f"  Erreur lors de la création du backup: {str(e)}")
            
            # Copier le fichier source vers le fichier cible
            try:
                shutil.copy2(source_file, target_file)
                new_size = os.path.getsize(target_file)
                print(f"  ✓ Réparation effectuée: {target_file} ({new_size:,} octets)")
            except Exception as e:
                print(f"  ✗ Erreur lors de la réparation: {str(e)}")
    
    print("\nVérification après réparation...")
    for filename in files_to_check:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  {filename}: {size:,} octets")
        else:
            print(f"  {filename}: MANQUANT")
    
    print("\nFinalisation...")
    print("  Patientez 3 secondes...")
    time.sleep(3)  # Pour s'assurer que les changements sont bien enregistrés
    
    print("\nRéparation terminée. Vous pouvez maintenant lancer:")
    print("python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription")

if __name__ == "__main__":
    verify_and_fix()
