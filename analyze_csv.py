#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour analyser le contenu du fichier CSV généré
"""

import csv
import os
import sys

def analyze_csv():
    # Fichier à analyser
    csv_file = r"C:\Datalead3webidu13juillet\messages_recus_only.csv"
    
    if not os.path.exists(csv_file):
        print(f"Erreur: Fichier introuvable: {csv_file}")
        return False
    
    contacts = set()
    total_rows = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            
            for row in reader:
                if row and len(row) > 0:
                    contacts.add(row[0])
                    total_rows += 1
        
        print(f"\nANALYSE DU FICHIER CSV: {csv_file}")
        print(f"Taille du fichier: {os.path.getsize(csv_file)} octets")
        print(f"Nombre total de lignes (messages): {total_rows}")
        print(f"Nombre total de contacts uniques: {len(contacts)}")
        print("\nExemples de contacts:")
        
        for i, contact in enumerate(sorted(list(contacts))):
            if i < 20:  # Afficher jusqu'à 20 contacts
                print(f"  {i+1}. {contact}")
            else:
                print(f"  ...et {len(contacts) - 20} autres contacts")
                break
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'analyse du CSV: {str(e)}")
        return False

if __name__ == "__main__":
    analyze_csv()
