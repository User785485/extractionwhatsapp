#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import argparse
import logging
from colorama import init, Fore, Style
from datetime import datetime
from tqdm import tqdm

# Initialize colorama for colored console output
init()

def setup_logging(log_dir="logs"):
    """Configure le système de logging"""
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"search_number_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def normalize_phone_number(phone_number):
    """Standardise le format du numéro de téléphone en supprimant tous les caractères non numériques"""
    return re.sub(r'\D', '', phone_number)

def generate_phone_variants(phone_number):
    """Génère différentes variantes possibles du numéro de téléphone"""
    # Normaliser d'abord le numéro (supprimer tous les caractères non numériques)
    clean_number = normalize_phone_number(phone_number)
    
    # Vérifier si le numéro est suffisamment long pour générer des variantes
    if len(clean_number) < 9:  # Numéro trop court, pas assez de chiffres
        return [phone_number, clean_number]
    
    # Format international avec différentes variantes d'espacement
    if clean_number.startswith('33'):
        base = clean_number[2:]  # Sans le code pays
        if len(base) < 9:  # Pas assez de chiffres après le code pays
            return [phone_number, f"+33{base}", f"+33 {base}"]
        
        variants = []
        # Sécuriser l'accès aux indices
        try:
            variants = [
                f"+33 {base[0]} {base[1:3]} {base[3:5]} {base[5:7]} {base[7:9]}",  # +33 6 70 63 82 20
                f"+33{base[0]}{base[1:3]}{base[3:5]}{base[5:7]}{base[7:9]}",       # +33670638220
                f"+33 {base[0]}{base[1:3]}{base[3:5]}{base[5:7]}{base[7:9]}",      # +33 670638220
                f"+33{base[0]} {base[1:3]} {base[3:5]} {base[5:7]} {base[7:9]}",   # +336 70 63 82 20
                f"0{base[0]}{base[1:3]}{base[3:5]}{base[5:7]}{base[7:9]}",         # 0670638220
                f"0{base[0]} {base[1:3]} {base[3:5]} {base[5:7]} {base[7:9]}"      # 06 70 63 82 20
            ]
        except IndexError:
            # Si une erreur d'index se produit, utiliser des formats simplifiés
            variants = [phone_number, f"+33{base}", f"+33 {base}", f"0{base}"]
    else:
        # Si le numéro ne commence pas par 33, on suppose qu'il est déjà au format local
        if clean_number.startswith('0'):
            base = clean_number[1:]  # Sans le 0 initial
            if len(base) < 9:  # Pas assez de chiffres après le 0
                return [phone_number, f"+33{base}", f"+33 {base}", clean_number]
            
            variants = []
            try:
                variants = [
                    f"+33 {base[0]} {base[1:3]} {base[3:5]} {base[5:7]} {base[7:9]}",  # +33 6 70 63 82 20
                    f"+33{base[0]}{base[1:3]}{base[3:5]}{base[5:7]}{base[7:9]}",       # +33670638220
                    f"+33 {base[0]}{base[1:3]}{base[3:5]}{base[5:7]}{base[7:9]}",      # +33 670638220
                    f"+33{base[0]} {base[1:3]} {base[3:5]} {base[5:7]} {base[7:9]}",   # +336 70 63 82 20
                    f"{clean_number}",                                                 # 0670638220
                    f"0{base[0]} {base[1:3]} {base[3:5]} {base[5:7]} {base[7:9]}"      # 06 70 63 82 20
                ]
            except IndexError:
                variants = [phone_number, f"+33{base}", f"+33 {base}", clean_number]
        else:
            # Si le format n'est pas reconnu, on l'ajoute tel quel aux variantes
            variants = [phone_number]
            if len(clean_number) >= 9:  # Si assez long, ajouter des variantes communes
                variants.append(f"+33{clean_number}")
                variants.append(f"+33 {clean_number}")
                variants.append(clean_number)
    
    return variants

def search_in_file(file_path, number_variants):
    """Recherche les variantes du numéro dans un fichier"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            for variant in number_variants:
                if variant in content:
                    return True, variant
                    
            # Recherche avec regex pour éviter les problèmes d'espaces ou de formatage
            clean_number = normalize_phone_number(number_variants[0])
            if len(clean_number) >= 9:  # Éviter les faux positifs avec des nombres courts
                last_digits = clean_number[-9:]  # Prendre les 9 derniers chiffres
                pattern = r'[^\d]' + r'[^\d]?'.join(last_digits) + r'[^\d]'
                if re.search(pattern, content):
                    return True, "format inattendu (regex match)"
                    
        return False, None
    except Exception as e:
        return False, f"Erreur: {str(e)}"

def search_phone_in_directory(directory, phone_number, logger):
    """Recherche un numéro de téléphone dans tous les fichiers d'un répertoire"""
    if not os.path.exists(directory):
        logger.error(f"Le répertoire {directory} n'existe pas.")
        return []
    
    logger.info(f"Recherche du numéro {phone_number} dans {directory}...")
    
    # Générer les variantes de numéro à rechercher
    number_variants = generate_phone_variants(phone_number)
    logger.info(f"Variantes recherchées: {number_variants}")
    
    results = []
    file_count = sum(len(files) for _, _, files in os.walk(directory))
    
    # Utiliser tqdm pour afficher une barre de progression
    with tqdm(total=file_count, desc="Fichiers analysés") as pbar:
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Vérifier uniquement les fichiers HTML pour les conversations WhatsApp
                if file_path.endswith('.html'):
                    found, variant = search_in_file(file_path, number_variants)
                    
                    if found:
                        results.append({
                            'file': os.path.relpath(file_path, directory),
                            'variant': variant
                        })
                        logger.info(f"Trouvé dans {file_path} (variant: {variant})")
                        print(f"{Fore.GREEN}✓ Trouvé dans: {Style.BRIGHT}{os.path.basename(file_path)}{Style.RESET_ALL}")
                
                pbar.update(1)
    
    return results

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Recherche un numéro de téléphone dans les exports WhatsApp.")
    parser.add_argument("phone_number", help="Le numéro de téléphone à rechercher")
    parser.add_argument("--directory", "-d", default=None, help="Le répertoire où effectuer la recherche")
    
    args = parser.parse_args()
    
    # Configuration du logger
    logger = setup_logging()
    
    # Si aucun répertoire n'est spécifié, utiliser le répertoire par défaut
    if not args.directory:
        # Utiliser le chemin des exports récents par défaut
        default_dir = r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp"
        if os.path.exists(default_dir):
            directory = default_dir
        else:
            # Chercher le dossier iPhone_* le plus récent dans Downloads
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
            iphone_dirs = [d for d in os.listdir(downloads_dir) if d.startswith("iPhone_") and os.path.isdir(os.path.join(downloads_dir, d))]
            
            if iphone_dirs:
                # Trier par date de modification, le plus récent en premier
                iphone_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(downloads_dir, d)), reverse=True)
                directory = os.path.join(downloads_dir, iphone_dirs[0], "WhatsApp")
                
                if not os.path.exists(directory):
                    directory = os.path.join(downloads_dir, iphone_dirs[0])
            else:
                # Si aucun répertoire iPhone_ n'est trouvé, utiliser le répertoire Downloads
                directory = downloads_dir
    else:
        directory = args.directory
    
    # Afficher le titre avec style
    print(f"\n{Fore.CYAN}{Style.BRIGHT}==== RECHERCHE DE NUMÉRO WHATSAPP ===={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Numéro: {Style.BRIGHT}{args.phone_number}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Répertoire: {Style.BRIGHT}{directory}{Style.RESET_ALL}\n")
    
    # Rechercher le numéro
    results = search_phone_in_directory(directory, args.phone_number, logger)
    
    # Afficher les résultats
    if results:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ Numéro trouvé dans {len(results)} fichier(s):{Style.RESET_ALL}")
        for result in results:
            print(f"{Fore.GREEN}  - {result['file']} (variant: {result['variant']}){Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}{Style.BRIGHT}✗ Le numéro {args.phone_number} n'a pas été trouvé.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Conseils:{Style.RESET_ALL}")
        print("  - Vérifiez que le format du numéro est correct")
        print("  - Le contact est peut-être enregistré sous un nom plutôt que son numéro")
        print("  - La conversation a peut-être été supprimée avant l'export")
        print("  - Essayez avec d'autres formats (avec/sans +33, avec/sans espaces)")
    
    return 0 if results else 1

if __name__ == "__main__":
    sys.exit(main())
