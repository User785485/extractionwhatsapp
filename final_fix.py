#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic et correction definitive pour l'export WhatsApp
"""

import os
import sys
import json
from datetime import datetime

def diagnostic():
    """Diagnostique le probleme"""
    output_dir = r"C:\Datalead3webidu13juillet"
    print("=== DIAGNOSTIC DU PROBLEME ===")
    print(f"Repertoire: {output_dir}\n")
    
    # 1. Verifier les fichiers sources
    print("1. FICHIERS SOURCES:")
    files_to_check = [
        'toutes_conversations.txt',
        'all_conversations.txt',
        'messages_recus.txt',
        'toutes_conversations_avec_transcriptions.txt',
        'messages_recus_avec_transcriptions.txt'
    ]
    
    source_exists = False
    for filename in files_to_check:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  {'OK' if size > 1000 else 'X'} {filename}: {size:,} octets")
            if filename in ['toutes_conversations.txt', 'all_conversations.txt'] and size > 1000:
                source_exists = True
        else:
            print(f"  X {filename}: MANQUANT")
    
    # 2. Verifier le registre
    print("\n2. REGISTRE:")
    registry_path = os.path.join(output_dir, '.unified_registry.json')
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
        contacts = registry.get('contacts', {})
        print(f"  Contacts dans le registre: {len(contacts)}")
        
        # Compter les messages
        total_messages = 0
        for contact, data in contacts.items():
            stats = data.get('stats', {})
            total_messages += stats.get('total_messages', 0)
        print(f"  Total messages dans le registre: {total_messages}")
    
    # 3. Verifier les conversations
    print("\n3. DOSSIERS DE CONTACTS:")
    contact_dirs = [d for d in os.listdir(output_dir) 
                   if os.path.isdir(os.path.join(output_dir, d)) 
                   and not d.startswith('.')]
    print(f"  Nombre de contacts: {len(contact_dirs)}")
    
    # Verifier quelques contacts
    messages_found = 0
    for i, contact in enumerate(contact_dirs[:5]):
        contact_path = os.path.join(output_dir, contact)
        msg_file = os.path.join(contact_path, 'tous_messages.txt')
        if os.path.exists(msg_file) and os.path.getsize(msg_file) > 100:
            messages_found += 1
    
    print(f"  Contacts avec messages (echantillon): {messages_found}/5")
    
    return source_exists, len(contact_dirs)

def recreate_global_files():
    """Recree les fichiers globaux a partir des fichiers individuels"""
    output_dir = r"C:\Datalead3webidu13juillet"
    print("\n=== RECREATION DES FICHIERS GLOBAUX ===")
    
    # Conteneurs pour tous les messages
    all_conversations = []
    all_received = []
    
    all_conversations.append("TOUTES LES CONVERSATIONS WHATSAPP")
    all_conversations.append(f"Genere le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_received.append("TOUS LES MESSAGES RECUS")
    all_received.append(f"Genere le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    all_received.append("=" * 50 + "\n")
    
    # Parcourir tous les contacts
    contact_dirs = [d for d in os.listdir(output_dir) 
                   if os.path.isdir(os.path.join(output_dir, d)) 
                   and not d.startswith('.')]
    
    total_messages = 0
    total_received = 0
    contacts_with_messages = 0
    
    print(f"Traitement de {len(contact_dirs)} contacts...")
    
    for i, contact in enumerate(sorted(contact_dirs)):
        contact_path = os.path.join(output_dir, contact)
        
        # Lire tous_messages.txt
        msg_file = os.path.join(contact_path, 'tous_messages.txt')
        if os.path.exists(msg_file) and os.path.getsize(msg_file) > 100:
            try:
                with open(msg_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Ajouter au fichier global
                all_conversations.append(f"\n{'='*50}")
                all_conversations.append(f"CONVERSATION AVEC: {contact}")
                all_conversations.append(f"{'='*50}\n")
                all_conversations.append(content)
                
                # Compter les messages
                import re
                messages = re.findall(r'\[\d{2}:\d{2}\]', content)
                total_messages += len(messages)
                contacts_with_messages += 1
                
            except Exception as e:
                print(f"  Erreur avec {contact}: {str(e)}")
        
        # Lire messages_recus.txt
        received_file = os.path.join(contact_path, 'messages_recus.txt')
        if os.path.exists(received_file) and os.path.getsize(received_file) > 100:
            try:
                with open(received_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Ajouter aux messages recus
                all_received.append(f"\n{'='*30}")
                all_received.append(f"DE: {contact}")
                all_received.append(f"{'='*30}\n")
                all_received.append(content)
                
                # Compter
                messages = re.findall(r'\[\d{4}/\d{2}/\d{2} \d{2}:\d{2}\]', content)
                total_received += len(messages)
                
            except Exception as e:
                print(f"  Erreur messages recus {contact}: {str(e)}")
        
        # Progression
        if (i + 1) % 100 == 0:
            print(f"  Traite: {i + 1}/{len(contact_dirs)}")
    
    # Ajouter les statistiques
    all_conversations.append(f"\n\n{'='*50}")
    all_conversations.append("RESUME GLOBAL")
    all_conversations.append(f"{'='*50}\n")
    all_conversations.append(f"Total contacts: {len(contact_dirs)}")
    all_conversations.append(f"Contacts avec messages: {contacts_with_messages}")
    all_conversations.append(f"Total messages: {total_messages}")
    
    all_received.append(f"\n\nTOTAL MESSAGES RECUS: {total_received}")
    
    # Sauvegarder les fichiers
    print("\nSauvegarde des fichiers...")
    
    # toutes_conversations.txt
    global_file = os.path.join(output_dir, 'toutes_conversations.txt')
    with open(global_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_conversations))
    print(f"OK {global_file}: {os.path.getsize(global_file):,} octets")
    
    # messages_recus.txt
    received_file = os.path.join(output_dir, 'messages_recus.txt')
    with open(received_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_received))
    print(f"OK {received_file}: {os.path.getsize(received_file):,} octets")
    
    return total_messages > 0

def force_merger():
    """Force le merger a s'executer"""
    print("\n=== FORCE LE MERGER ===")
    
    import subprocess
    result = subprocess.run([
        sys.executable, 
        'main_enhanced.py',
        '--skip-extraction',
        '--skip-media', 
        '--skip-audio',
        '--skip-transcription',
        '--force-merger'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("OK Merger execute avec succes")
        return True
    else:
        print(f"X Erreur du merger: {result.stderr}")
        return False

def verify_results():
    """Verifie les resultats finaux"""
    output_dir = r"C:\Datalead3webidu13juillet"
    print("\n=== VERIFICATION DES RESULTATS ===")
    
    files_to_check = [
        ('toutes_conversations_avec_transcriptions.txt', 'Fichier fusionne'),
        ('messages_recus_only.csv', 'CSV messages recus'),
        ('contacts_messages_simplifies.csv', 'CSV simplifie')
    ]
    
    all_ok = True
    for filename, description in files_to_check:
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 1000:
                print(f"OK {description}: {size:,} octets")
            else:
                print(f"X {description}: Trop petit ({size} octets)")
                all_ok = False
        else:
            print(f"X {description}: MANQUANT")
            all_ok = False
    
    return all_ok

def main():
    print("=== CORRECTION DEFINITIVE DE L'EXPORT WHATSAPP ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Diagnostic
    source_exists, num_contacts = diagnostic()
    
    if not source_exists or num_contacts == 0:
        print("\n! Les fichiers sources n'existent pas ou sont vides")
        print("  Tentative de recreation...")
        
        # 2. Recreer les fichiers globaux
        if recreate_global_files():
            print("\nOK Fichiers globaux recrees avec succes")
        else:
            print("\nX Impossible de recreer les fichiers")
            print("  Verifiez que l'extraction initiale a bien fonctionne")
            return 1
    
    # 3. Forcer le merger
    print("\nExecution du merger...")
    if not force_merger():
        print("X Le merger a echoue")
        print("  Utilisez le script correction.py comme solution alternative")
        return 1
    
    # 4. Verifier les resultats
    if verify_results():
        print("\n" + "="*50)
        print("OK TOUT EST CORRIGE!")
        print("="*50)
        print("\nLes fichiers d'export sont maintenant generes correctement.")
        print("Vous pouvez utiliser 'full bro.bat' normalement.")
    else:
        print("\n! Certains fichiers manquent encore")
        print("  Essayez: python correction.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
