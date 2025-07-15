#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de vérification des contacts - affiche des exemples des deux types
"""

import os
import csv

# Dossier de sortie
OUTPUT_DIR = r"C:\Datalead3webidu13juillet"

def main():
    """Point d'entrée principal"""
    print("="*50)
    print("VÉRIFICATION DES CONTACTS")
    print("="*50)
    
    # Vérifier les dossiers de contacts
    all_dirs = [d for d in os.listdir(OUTPUT_DIR) if os.path.isdir(os.path.join(OUTPUT_DIR, d))]
    
    # Séparer les contacts par type
    numero_dirs = [d for d in all_dirs if d.startswith('_')]
    prenom_dirs = [d for d in all_dirs if not d.startswith('_') and not d.startswith('.')]
    
    print(f"\nDossiers dans {OUTPUT_DIR}:")
    print(f"Total dossiers: {len(all_dirs)}")
    print(f"Contacts avec numéro: {len(numero_dirs)}")
    print(f"Contacts avec prénom: {len(prenom_dirs)}")
    
    print("\nExemples de contacts avec numéro:")
    for i, contact in enumerate(numero_dirs[:10]):
        print(f"  {i+1}. {contact}")
    
    print("\nExemples de contacts avec prénom:")
    for i, contact in enumerate(prenom_dirs[:10]):
        print(f"  {i+1}. {contact}")
    
    # Maintenant, générons un nouveau CSV très simple pour être sûr
    output_csv = os.path.join(OUTPUT_DIR, "TOUS_LES_CONTACTS_LISTE.csv")
    
    with open(output_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Contact', 'Type'])
        
        # Ajouter tous les contacts avec numéro
        for contact in numero_dirs:
            writer.writerow([contact, 'Numéro'])
        
        # Ajouter tous les contacts avec prénom
        for contact in prenom_dirs:
            if not contact.startswith('.') and not any(kw in contact.lower() for kw in ['export', 'messages_']):
                writer.writerow([contact, 'Prénom'])
    
    print(f"\nFichier CSV simple créé: {output_csv}")
    print(f"Taille: {os.path.getsize(output_csv)} octets")
    
    # Vérifier le contenu du CSV créé
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    
    num_count = sum(1 for row in rows if row[1] == 'Numéro')
    prenom_count = sum(1 for row in rows if row[1] == 'Prénom')
    
    print(f"\nContenu du CSV:")
    print(f"Total lignes: {len(rows)}")
    print(f"Contacts avec numéro: {num_count}")
    print(f"Contacts avec prénom: {prenom_count}")
    
if __name__ == "__main__":
    main()
