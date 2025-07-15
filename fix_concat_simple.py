#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import datetime
import subprocess

# Configuration simplifiée
output_dir = r"C:\Datalead3webidu13juillet"
target_file = os.path.join(output_dir, "toutes_conversations.txt")
target_file_transcriptions = os.path.join(output_dir, "toutes_conversations_avec_transcriptions.txt")

print("=== CORRECTION PAR CONCATÉNATION DES CONVERSATIONS ===")

# Créer des backups des fichiers existants
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
for file_path in [target_file, target_file_transcriptions]:
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup.{timestamp}"
        try:
            shutil.copy2(file_path, backup_path)
            print(f"Sauvegarde créée: {backup_path}")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de {file_path}: {e}")

# Liste tous les dossiers de contacts (qui commencent par _)
contact_folders = [d for d in os.listdir(output_dir) 
                  if os.path.isdir(os.path.join(output_dir, d)) 
                  and d.startswith('_')
                  and d != '_WhatsApp']

print(f"Nombre de contacts trouvés: {len(contact_folders)}")

if not contact_folders:
    print("Aucun dossier de contact trouvé!")
    exit(1)

# Compter le nombre total de messages pour l'en-tête
total_contacts = len(contact_folders)
total_messages = 0
total_medias = 0

# Collecter toutes les conversations
all_conversations = []
all_conversations_with_transcriptions = []

for contact in contact_folders:
    contact_dir = os.path.join(output_dir, contact)
    print(f"Traitement du contact: {contact}")
    
    # Fichier de tous les messages (sans transcriptions)
    tous_messages_file = os.path.join(contact_dir, "tous_messages.txt")
    if os.path.exists(tous_messages_file):
        with open(tous_messages_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            all_conversations.append(f"\n\n{'='*50}\nCONTACT: {contact}\n{'='*50}\n\n{content}")
            
            # Compter approximativement les messages et médias
            message_lines = [line for line in content.split('\n') if '] ' in line]
            total_messages += len(message_lines)
            media_lines = [line for line in message_lines if '[AUDIO]' in line or '[IMAGE]' in line or '[VIDEO]' in line]
            total_medias += len(media_lines)
    
    # Fichier de tous les messages avec transcriptions
    tous_messages_trans_file = os.path.join(contact_dir, "tous_messages_avec_transcriptions.txt")
    if os.path.exists(tous_messages_trans_file):
        with open(tous_messages_trans_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            all_conversations_with_transcriptions.append(f"\n\n{'='*50}\nCONTACT: {contact}\n{'='*50}\n\n{content}")

# Générer les en-têtes
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
header = f"""TOUTES LES CONVERSATIONS WHATSAPP
Généré le: {now}
Nombre de contacts: {total_contacts}


{'='*50}
RÉSUMÉ GLOBAL
{'='*50}

Total contacts: {total_contacts}
Total messages: {total_messages}
Total médias: {total_medias}
"""

print(f"Écriture du fichier: {target_file}")
# Écrire le fichier consolidé sans transcriptions
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(header)
    for conversation in all_conversations:
        f.write(conversation)

print(f"Écriture du fichier: {target_file_transcriptions}")
# Écrire le fichier consolidé avec transcriptions
with open(target_file_transcriptions, 'w', encoding='utf-8') as f:
    f.write(header)
    for conversation in all_conversations_with_transcriptions:
        f.write(conversation)

# Vérifier les tailles des fichiers créés
file_size_regular = os.path.getsize(target_file)
file_size_trans = os.path.getsize(target_file_transcriptions)

print(f"Fichier généré: {target_file} - Taille: {file_size_regular} octets")
print(f"Fichier généré: {target_file_transcriptions} - Taille: {file_size_trans} octets")

# Régénérer les exports avec main_enhanced.py
print("\n=== RÉGÉNÉRATION DES EXPORTS ===\n")
cmd = ["python", "main_enhanced.py", 
       "--skip-extraction",  # On utilise les conversations concaténées 
       "--skip-media",       # On garde les médias extraits
       "--skip-audio",       # On garde les conversions audio
       "--skip-transcription",  # On garde les transcriptions
       "--force-merger",     # On force la fusion des transcriptions
       "--minimal-export"]   # Mode minimal (uniquement messages reçus)

try:
    print(f"Exécution de la commande: {' '.join(cmd)}")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(f"Sortie: {stdout.decode('utf-8', errors='ignore')[:500]}...")
    if stderr:
        print(f"Erreurs: {stderr.decode('utf-8', errors='ignore')}")
except Exception as e:
    print(f"Erreur lors de l'exécution de la commande: {e}")

# Vérification des fichiers générés
expected_files = [
    r"C:\Datalead3webidu13juillet\messages_recus.txt",
    r"C:\Datalead3webidu13juillet\messages_recus_avec_transcriptions.txt",
]

print("\n=== VÉRIFICATION DES FICHIERS ===")
for file_path in expected_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        if size < 1000:  # Moins de 1 Ko
            print(f"⚠ Fichier anormalement petit: {os.path.basename(file_path)} ({size} octets)")
        else:
            print(f"✓ Fichier généré avec succès: {os.path.basename(file_path)} ({size} octets)")
    else:
        print(f"❌ Fichier manquant: {os.path.basename(file_path)}")

print("\n===== RÉPARATION TERMINÉE =====")
