#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour trouver les contacts ayant des transcriptions mais manquants dans l'export simple
"""

import os
import csv
import sys
from pathlib import Path

# Augmenter la limite de taille des champs CSV (valeur sécurisée)
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    # Pour Windows, sys.maxsize peut causer un overflow
    csv.field_size_limit(2147483647) # 2^31-1

def find_missing_contacts(output_dir):
    """Trouve les contacts qui ont des transcriptions mais n'apparaissent pas dans l'export"""
    
    print("=== RECHERCHE DES CONTACTS MANQUANTS ===\n")
    
    # 1. Lister TOUS les dossiers de contacts
    all_contacts = []
    for item in Path(output_dir).iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            all_contacts.append(item.name)
    
    print(f"Total dossiers contacts: {len(all_contacts)}")
    
    # 2. Vérifier qui a des transcriptions
    contacts_with_transcriptions = []
    for contact in all_contacts:
        trans_dir = Path(output_dir) / contact / "transcriptions"
        if trans_dir.exists():
            txt_files = list(trans_dir.glob("*.txt"))
            if txt_files:
                contacts_with_transcriptions.append((contact, len(txt_files)))
    
    print(f"Contacts avec transcriptions: {len(contacts_with_transcriptions)}")
    
    # 3. Lire le CSV export simple
    csv_path = os.path.join(output_dir, "export_simple.csv")
    contacts_in_csv = set()
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row:
                    contacts_in_csv.add(row[0])
    
    print(f"Contacts dans export_simple.csv: {len(contacts_in_csv)}")
    
    # 4. Trouver les manquants
    print("\n=== CONTACTS MANQUANTS AVEC TRANSCRIPTIONS ===")
    missing_count = 0
    
    for contact, trans_count in contacts_with_transcriptions:
        if contact not in contacts_in_csv:
            print(f"[MANQUANT] {contact} - {trans_count} transcriptions")
            missing_count += 1
            
            # Chercher des variantes possibles
            found_variant = False
            for csv_contact in contacts_in_csv:
                if contact.lower() in csv_contact.lower() or csv_contact.lower() in contact.lower():
                    print(f"   -> Variante possible dans CSV: {csv_contact}")
                    found_variant = True
                    break
            
            if not found_variant and "webi441" in contact:
                print(f"   -> [IMPORTANT] C'EST LE CONTACT QUE VOUS CHERCHEZ!")
    
    print(f"\nTotal contacts manquants: {missing_count}")
    
    # 5. Vérifier le dossier webi441 spécifiquement
    print("\n=== RECHERCHE SPÉCIFIQUE webi441 ===")
    for contact in all_contacts:
        if "webi441" in contact.lower():
            print(f"[TROUVÉ] Dossier: {contact}")
            trans_dir = Path(output_dir) / contact / "transcriptions"
            if trans_dir.exists():
                files = list(trans_dir.glob("*.txt"))
                print(f"  - Transcriptions: {len(files)}")
                if files:
                    print(f"  - Exemple: {files[0].name}")

if __name__ == "__main__":
    # Utilisation
    output_dir = r"C:\Datalead3webidu13juillet"
    find_missing_contacts(output_dir)
