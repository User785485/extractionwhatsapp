#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de nettoyage des fichiers en double
Basé sur l'analyse préalable des doublons (analyze_duplicates.py)
Utilise le rapport généré pour supprimer les doublons en toute sécurité

Mode d'utilisation sécurisé:
1. Garder un fichier principal pour chaque groupe de doublons
2. Déplacer les doublons vers un répertoire temporaire pour vérification
3. Ne pas supprimer définitivement sans confirmation explicite

Auteur: Whatsapp Extractor V2 Team
"""

import os
import json
import shutil
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Set, Any

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('whatsapp_extractor')

# Créer le répertoire de logs s'il n'existe pas
os.makedirs('logs', exist_ok=True)

# Ajouter un handler pour les fichiers
file_handler = logging.FileHandler(
    os.path.join('logs', f'clean_duplicates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
logger.addHandler(file_handler)

class DuplicateCleaner:
    """
    Nettoyage des fichiers en double basé sur un rapport d'analyse
    """
    
    def __init__(self, report_path: str, output_dir: str = None, dry_run: bool = False):
        """
        Initialisation du nettoyeur de doublons
        
        Args:
            report_path: Chemin vers le rapport d'analyse des doublons
            output_dir: Répertoire pour déplacer les doublons (défaut: ./duplicates_backup)
            dry_run: Mode simulation sans modification des fichiers (défaut: False)
        """
        self.report_path = report_path
        self.dry_run = dry_run
        
        # Répertoire de sortie pour déplacer les doublons
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(os.getcwd(), 'duplicates_backup')
        
        # Statistiques
        self.stats = {
            'duplicate_groups': 0,
            'files_processed': 0,
            'files_moved': 0,
            'saved_space': 0,  # en octets
            'errors': 0
        }
        
        # Chargement du rapport
        self.duplicates = self._load_report()
        
    def _load_report(self) -> Dict:
        """Charge le rapport d'analyse des doublons"""
        try:
            with open(self.report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Rapport chargé: {self.report_path}")
            return data
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du rapport: {str(e)}")
            return {'duplicate_groups': {}}
    
    def _create_backup_dir(self) -> bool:
        """Crée le répertoire de sauvegarde pour les doublons"""
        if self.dry_run:
            logger.info(f"MODE SIMULATION: pas de création de répertoire {self.output_dir}")
            return True
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = os.path.join(self.output_dir, f"duplicates_{timestamp}")
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Créer un fichier README pour expliquer l'utilité de ce dossier
            readme_path = os.path.join(self.output_dir, "README.txt")
            with open(readme_path, 'w', encoding='utf-8') as readme:
                readme.write("Whatsapp Extractor V2 - Fichiers en double\n")
                readme.write("======================================\n\n")
                readme.write("Ce dossier contient des fichiers identifiés comme des doublons par l'analyseur de doublons.\n")
                readme.write("Les fichiers sont organisés par sous-dossiers correspondant à leur hash SHA-256.\n")
                readme.write("Ils peuvent être supprimés en toute sécurité après vérification manuelle.\n\n")
                readme.write(f"Date de création: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                readme.write(f"Pour chaque groupe, un fichier a été conservé dans le répertoire d'origine.")
            
            logger.info(f"Répertoire de sauvegarde créé: {self.output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du répertoire de sauvegarde: {str(e)}")
            return False
    
    def _select_file_to_keep(self, files: List[Dict]) -> Dict:
        """
        Sélectionne le fichier à conserver parmi un groupe de doublons
        
        Stratégie:
        1. Préférer les fichiers "received" plutôt que "sent"
        2. Préférer les fichiers avec préfixe correct sur ceux sans préfixe
        3. Préférer les fichiers avec transcription sur ceux sans transcription
        4. En cas d'égalité, prendre le premier fichier de la liste
        """
        # Score pour chaque fichier
        scored_files = []
        
        for file in files:
            score = 0
            path = file.get('path', '')
            
            # Critère 1: Direction du message
            if 'received' in path.lower() or path.lower().startswith('received_'):
                score += 3
                
            # Critère 2: Préfixe correct
            filename = os.path.basename(path)
            if filename.startswith('received_') or filename.startswith('sent_'):
                score += 2
                
            # Critère 3: Présence de transcription
            transcription_path = self._find_transcription(path)
            if transcription_path and os.path.exists(transcription_path):
                score += 1
                
            scored_files.append((score, file))
                
        # Trier par score décroissant
        scored_files.sort(reverse=True, key=lambda x: x[0])
        
        # Retourner le fichier avec le meilleur score
        return scored_files[0][1]
    
    def _find_transcription(self, audio_path: str) -> str:
        """Trouve le fichier de transcription correspondant à un fichier audio"""
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        dir_name = os.path.dirname(audio_path)
        
        # Remonter d'un niveau et chercher dans le dossier transcriptions
        parent_dir = os.path.dirname(dir_name)
        
        # Si le nom de base commence par received_ ou sent_, les retirer
        if base_name.startswith('received_') or base_name.startswith('sent_'):
            base_name = base_name[8:]  # Retirer le préfixe
            
        # Chemins possibles pour la transcription
        possible_paths = [
            os.path.join(dir_name, 'transcriptions', f"{base_name}.txt"),
            os.path.join(dir_name, 'transcriptions', f"{base_name}_transcription.txt"),
            os.path.join(parent_dir, 'transcriptions', f"{base_name}.txt"),
            os.path.join(parent_dir, 'transcriptions', f"{base_name}_transcription.txt")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def _move_duplicate(self, file_path: str, hash_value: str) -> bool:
        """Déplace un fichier dupliqué vers le répertoire de sauvegarde"""
        try:
            if self.dry_run:
                # En mode simulation, on comptabilise quand même l'espace qui serait libéré
                logger.info(f"MODE SIMULATION: {file_path} serait déplacé")
                if os.path.exists(file_path):
                    self.stats['saved_space'] += os.path.getsize(file_path)
                return True
                
            # Créer un sous-répertoire pour ce hash s'il n'existe pas
            hash_dir = os.path.join(self.output_dir, hash_value[:8])
            os.makedirs(hash_dir, exist_ok=True)
            
            # Déterminer le nom de destination
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(hash_dir, file_name)
            
            # Gérer les conflits de noms
            counter = 0
            while os.path.exists(dest_path):
                counter += 1
                base, ext = os.path.splitext(file_name)
                dest_path = os.path.join(hash_dir, f"{base}_{counter}{ext}")
            
            # Déplacer le fichier
            shutil.move(file_path, dest_path)
            
            # Mettre à jour les statistiques
            self.stats['files_moved'] += 1
            self.stats['saved_space'] += os.path.getsize(dest_path)
            
            logger.debug(f"Déplacé: {file_path} → {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du déplacement de {file_path}: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def clean(self) -> Dict:
        """
        Nettoie les fichiers en double
        
        Returns:
            Statistiques de nettoyage
        """
        if not self._create_backup_dir():
            logger.error("Impossible de créer le répertoire de sauvegarde, abandon")
            return self.stats
        
        mode_info = "(SIMULATION)" if self.dry_run else ""
        logger.info(f"Début du nettoyage des doublons {mode_info}")
        
        # Pour chaque groupe de doublons
        # Le rapport a directement les hash SHA-256 comme clés de premier niveau
        duplicate_groups = self.duplicates
        
        logger.info(f"Traitement de {len(duplicate_groups)} groupes de doublons")
        for hash_value, files in duplicate_groups.items():
            self.stats['duplicate_groups'] += 1
            
            # files est déjà la liste des fichiers
            if len(files) <= 1:
                continue  # Pas de doublons dans ce groupe
                
            # Sélectionner le fichier à conserver
            file_to_keep = self._select_file_to_keep(files)
            keep_path = file_to_keep.get('path', '')
            
            if not keep_path or not os.path.exists(keep_path):
                logger.warning(f"Fichier à conserver non trouvé: {keep_path}")
                continue
                
            # Déplacer les autres fichiers
            for file in files:
                self.stats['files_processed'] += 1
                file_path = file.get('path', '')
                
                if file_path == keep_path:
                    logger.debug(f"Conservé: {file_path}")
                    continue
                    
                if os.path.exists(file_path):
                    self._move_duplicate(file_path, hash_value)
                    
        # Afficher le résumé
        self._show_summary()
        
        return self.stats
    
    def _show_summary(self):
        """Affiche le résumé du nettoyage"""
        mode_info = " (SIMULATION)" if self.dry_run else ""
        
        logger.info("\n" + "="*60)
        logger.info(f"RÉSUMÉ DU NETTOYAGE DE DOUBLONS{mode_info}")
        logger.info("="*60)
        logger.info(f"Groupes de doublons traités:   {self.stats['duplicate_groups']}")
        logger.info(f"Fichiers analysés:             {self.stats['files_processed']}")
        logger.info(f"Fichiers déplacés:             {self.stats['files_moved']}")
        logger.info(f"Espace disque libéré:          {self._format_size(self.stats['saved_space'])}")
        logger.info(f"Erreurs rencontrées:           {self.stats['errors']}")
        logger.info("="*60)
        
        if not self.dry_run:
            logger.info(f"\nLes fichiers dupliqués ont été déplacés vers: {self.output_dir}")
            logger.info("Vérifiez manuellement ce répertoire avant de supprimer définitivement les fichiers.")
        else:
            logger.info("\nSimulation terminée - aucun fichier n'a été modifié.")
            logger.info(f"Espace potentiellement libérable: {self._format_size(self.stats['saved_space'])}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Formate une taille en octets en unité lisible"""
        if size_bytes < 1024:
            return f"{size_bytes} octets"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} Ko"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} Mo"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} Go"

def main():
    """Point d'entrée du script de nettoyage des doublons"""
    try:
        parser = argparse.ArgumentParser(description='Nettoyage des fichiers en double')
        parser.add_argument('--report', type=str, default='duplicates_report.json',
                           help='Chemin vers le rapport d\'analyse des doublons')
        parser.add_argument('--output-dir', type=str, default=None,
                           help='Répertoire pour déplacer les doublons (défaut: ./duplicates_backup)')
        parser.add_argument('--dry-run', action='store_true',
                           help='Mode simulation sans modification des fichiers')
        args = parser.parse_args()
        
        # Vérifier que le rapport existe
        if not os.path.exists(args.report):
            logger.error(f"Le rapport d'analyse {args.report} n'existe pas")
            return 1
            
        cleaner = DuplicateCleaner(
            report_path=args.report,
            output_dir=args.output_dir,
            dry_run=args.dry_run
        )
        
        cleaner.clean()
        return 0
        
    except Exception as e:
        logger.critical(f"Erreur fatale lors du nettoyage: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
