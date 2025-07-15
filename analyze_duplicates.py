#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ANALYZE_DUPLICATES.PY
=====================

Analyse des fichiers audio en double dans les données WhatsApp.
Utilise un hachage SHA-256 du contenu pour identifier les vrais doublons.

Créé : 05/06/2025
Auteur : Système WhatsApp Extractor V2

COMMENT ÇA FONCTIONNE :
1. Parcourt le répertoire de données spécifié dans config.ini
2. Calcule un hash SHA-256 unique pour chaque fichier audio
3. Groupe les fichiers par hash identiques
4. Génère un rapport JSON détaillé des doublons
5. Fournit des statistiques sur l'espace disque gaspillé

UTILISATION :
    python analyze_duplicates.py [--output FICHIER] [--data-dir RÉPERTOIRE]
"""

import os
import sys
import json
import time
import logging
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, DefaultDict, Set
from datetime import datetime
from collections import defaultdict

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(f"logs/duplicates_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("analyze_duplicates")

# Extensions de fichiers à analyser
AUDIO_EXTENSIONS = ('.opus', '.mp3', '.m4a', '.ogg', '.aac', '.wav')
# Motifs pour identifier les super fichiers
SUPER_FILE_PATTERNS = ('tous_', 'all_', 'combined_', 'received_', 'sent_')


def parse_config() -> Dict:
    """
    Parse le fichier config.ini pour obtenir les chemins de configuration.
    
    Returns:
        Dict: Dictionnaire avec les paramètres de configuration
    """
    import configparser
    
    config = configparser.ConfigParser()
    
    # Essayer de charger depuis le répertoire courant
    try:
        config.read('config.ini', encoding='utf-8')
        
        # Vérifier si la section Paths existe
        if 'Paths' not in config:
            logger.error("Section 'Paths' manquante dans config.ini")
            return {"data_dir": "C:\\Users\\Moham\\Desktop\\Data Leads"}
            
        # Lire le répertoire de données
        data_dir = config['Paths'].get('output_dir', 
                                      "C:\\Users\\Moham\\Desktop\\Data Leads")
        
        return {"data_dir": data_dir}
            
    except Exception as e:
        logger.error(f"Erreur lors de la lecture de config.ini: {e}")
        return {"data_dir": "C:\\Users\\Moham\\Desktop\\Data Leads"}


def calculate_file_hash(file_path: str) -> str:
    """
    Calcule un hash SHA-256 unique pour un fichier.
    
    Args:
        file_path (str): Chemin complet vers le fichier
        
    Returns:
        str: Hash SHA-256 du contenu du fichier ou chaîne vide si erreur
    """
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            # Lire par morceaux pour éviter de charger de gros fichiers en mémoire
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Erreur lors du calcul du hash pour {file_path}: {e}")
        return ""


def human_readable_size(size_bytes: int) -> str:
    """
    Convertit une taille en octets en format lisible (KB, MB, GB).
    
    Args:
        size_bytes (int): Taille en octets
        
    Returns:
        str: Taille formatée avec unité
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def is_super_file(file_path: str) -> bool:
    """
    Détermine si un fichier est un "super fichier" basé sur son nom.
    
    Args:
        file_path (str): Chemin du fichier à vérifier
        
    Returns:
        bool: True si c'est un super fichier, False sinon
    """
    file_name = os.path.basename(file_path).lower()
    return any(pattern in file_name for pattern in SUPER_FILE_PATTERNS)


def analyze_duplicates(data_dir: str, output_file: str = "duplicates_report.json") -> Dict:
    """
    Analyse le répertoire de données pour trouver les fichiers en double.
    
    Args:
        data_dir (str): Répertoire à analyser
        output_file (str): Fichier de sortie pour le rapport JSON
        
    Returns:
        Dict: Statistiques sur les doublons trouvés
    """
    logger.info(f"Démarrage de l'analyse des doublons dans: {data_dir}")
    start_time = time.time()
    
    # Vérifier si le répertoire existe
    if not os.path.isdir(data_dir):
        logger.error(f"Le répertoire {data_dir} n'existe pas.")
        print(f"ERREUR: Le répertoire {data_dir} n'existe pas.")
        sys.exit(1)
    
    # Dictionnaire qui associe chaque hash à une liste de fichiers
    hash_to_files: DefaultDict[str, List[Dict]] = defaultdict(list)
    
    # Statistiques
    stats = {
        "total_files_scanned": 0,
        "audio_files_found": 0,
        "unique_files_count": 0,
        "duplicate_groups_count": 0,
        "total_size_bytes": 0,
        "duplicate_size_bytes": 0,
        "largest_duplicate_group": 0,
        "super_files_count": 0
    }
    
    # Parcourir tous les fichiers du répertoire
    logger.info("Scan des fichiers en cours...")
    print("\nAnalyse des fichiers audio en cours...")
    print("Cela peut prendre plusieurs minutes pour de grandes collections...")
    
    # Compteur pour l'affichage de progression
    progress_counter = 0
    
    for root, _, files in os.walk(data_dir):
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            
            # Ne traiter que les fichiers audio
            if file_ext in AUDIO_EXTENSIONS:
                progress_counter += 1
                if progress_counter % 100 == 0:
                    print(f"Fichiers analysés: {progress_counter}", end='\r')
                
                file_path = os.path.join(root, file)
                
                stats["audio_files_found"] += 1
                
                try:
                    # Obtenir la taille du fichier
                    file_size = os.path.getsize(file_path)
                    stats["total_size_bytes"] += file_size
                    
                    # Vérifier si c'est un super fichier
                    is_super = is_super_file(file_path)
                    if is_super:
                        stats["super_files_count"] += 1
                    
                    # Calculer le hash du fichier
                    file_hash = calculate_file_hash(file_path)
                    if not file_hash:
                        continue
                    
                    # Ajouter à notre dictionnaire de hash
                    hash_to_files[file_hash].append({
                        "path": file_path,
                        "size": file_size,
                        "name": file,
                        "super_file": is_super,
                        "directory": os.path.basename(root)
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de {file_path}: {e}")
    
    # Màj des statistiques
    stats["total_files_scanned"] = progress_counter
    
    # Trouver les fichiers uniques et les doublons
    unique_hashes = 0
    duplicate_groups = {}
    
    for file_hash, files in hash_to_files.items():
        if len(files) > 1:
            # C'est un groupe de doublons
            duplicate_groups[file_hash] = files
            stats["duplicate_groups_count"] += 1
            
            # Mettre à jour le plus grand groupe de doublons
            if len(files) > stats["largest_duplicate_group"]:
                stats["largest_duplicate_group"] = len(files)
            
            # Calculer l'espace gaspillé = (nombre de copies - 1) * taille
            wasted_space = (len(files) - 1) * files[0]["size"]
            stats["duplicate_size_bytes"] += wasted_space
        else:
            unique_hashes += 1
    
    stats["unique_files_count"] = unique_hashes
    
    # Générer le rapport JSON avec les doublons
    if duplicate_groups:
        # Trier par taille d'espace gaspillé
        sorted_duplicates = dict(sorted(
            duplicate_groups.items(),
            key=lambda x: len(x[1]) * x[1][0]["size"],
            reverse=True
        ))
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_duplicates, f, indent=2, ensure_ascii=False)
            logger.info(f"Rapport détaillé sauvé dans '{output_file}'")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du rapport: {e}")
    
    # Afficher un résumé des résultats
    elapsed_time = time.time() - start_time
    print(f"\nAnalyse terminée en {elapsed_time:.2f} secondes.")
    
    return stats


def main():
    """Fonction principale."""
    # Créer le répertoire logs s'il n'existe pas
    os.makedirs("logs", exist_ok=True)
    
    # Parser les arguments de ligne de commande
    parser = argparse.ArgumentParser(description="Analyse des fichiers audio en double dans les données WhatsApp")
    parser.add_argument("--output", default="duplicates_report.json", help="Fichier de sortie pour le rapport JSON")
    parser.add_argument("--data-dir", help="Répertoire à analyser (remplace celui dans config.ini)")
    args = parser.parse_args()
    
    # Obtenir le répertoire de données
    config = parse_config()
    data_dir = args.data_dir if args.data_dir else config["data_dir"]
    
    # Lancer l'analyse
    try:
        stats = analyze_duplicates(data_dir, args.output)
        
        # Afficher les statistiques
        print("\n" + "=" * 60)
        print("                RAPPORT D'ANALYSE DES DOUBLONS")
        print("=" * 60)
        print(f"Répertoire analysé       : {data_dir}")
        print(f"Fichiers audio trouvés   : {stats['audio_files_found']}")
        print(f"Fichiers uniques         : {stats['unique_files_count']}")
        print(f"Groupes de doublons      : {stats['duplicate_groups_count']}")
        print(f"Super fichiers trouvés   : {stats['super_files_count']}")
        print("-" * 60)
        print(f"Taille totale            : {human_readable_size(stats['total_size_bytes'])}")
        print(f"Espace gaspillé          : {human_readable_size(stats['duplicate_size_bytes'])}")
        print(f"Pourcentage gaspillé     : {stats['duplicate_size_bytes'] / max(stats['total_size_bytes'], 1) * 100:.2f}%")
        print("-" * 60)
        
        # Si des doublons ont été trouvés
        if stats['duplicate_groups_count'] > 0:
            print(f"\nRapport détaillé sauvegardé dans: {args.output}")
            print("\nACTIONS RECOMMANDÉES:")
            print("1. Consultez le rapport JSON pour voir les détails des doublons")
            print("2. Utilisez l'option 'Déplacer les anciens super fichiers' dans clean_duplicates.bat")
            print("3. Recréez les super fichiers avec l'option correspondante")
        else:
            print("\nAucun doublon trouvé! Le système est déjà optimisé.")
            
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"\nERREUR: Une erreur est survenue lors de l'analyse: {e}")
        print("Consultez les logs pour plus de détails.")


if __name__ == "__main__":
    main()
