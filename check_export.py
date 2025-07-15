#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de vérification du contenu des exports CSV
"""

import csv
import os
import sys

# Augmenter la limite de taille des champs CSV (valeur sécurisée)
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    # Pour Windows, sys.maxsize peut causer un overflow
    csv.field_size_limit(2147483647) # 2^31-1

def check_export_content(csv_path):
    """Vérifie le contenu du CSV"""
    print(f"Vérification de: {csv_path}")
    
    if not os.path.exists(csv_path):
        print("[ERREUR] Fichier non trouvé!")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        
        rows = list(reader)
        print(f"\n[OK] Nombre de contacts dans le CSV: {len(rows)}")
        
        # Chercher des contacts spécifiques
        contacts_to_find = ['Test', 'Wahiba', 'Zaina', 'Zakia', 'webi441']
        
        print("\nRecherche de contacts spécifiques:")
        for contact_name in contacts_to_find:
            found = False
            for row in rows:
                if contact_name.lower() in row[0].lower():
                    found = True
                    print(f"[TROUVE] {contact_name}: {row[0][:50]}...")
                    break
            
            if not found:
                print(f"[ABSENT] {contact_name} non trouvé dans le CSV!")
        
        # Afficher les 10 dernières lignes (avec gestion des caractères spéciaux)
        print("\n10 dernières lignes du CSV:")
        for row in rows[-10:]:
            # Nettoyer le texte pour éviter les problèmes d'encodage
            contact = row[0].encode('ascii', 'ignore').decode('ascii')
            try:
                content = row[1][:50].encode('ascii', 'ignore').decode('ascii')
            except:
                content = "[Contenu avec caractères spéciaux]"
            print(f"- {contact}: {content}...")

if __name__ == "__main__":
    # Utilisation
    csv_path = r"C:\Datalead3webidu13juillet\export_simple.csv"
    check_export_content(csv_path)
