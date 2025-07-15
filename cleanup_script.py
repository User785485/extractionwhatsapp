#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de nettoyage et optimisation pour WhatsApp Extractor V2
ASCII only - pas d'emojis ou caracteres speciaux
"""

import os
import shutil
import re
from datetime import datetime
from typing import List, Dict, Tuple

class WhatsAppExtractorCleaner:
    """Classe pour nettoyer et optimiser le projet WhatsApp Extractor"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.backup_dir = os.path.join(project_path, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.files_to_delete = []
        self.files_to_keep = []
        self.optimizations = []
        
    def analyze_project(self) -> Dict[str, List[str]]:
        """Analyse le projet et identifie les fichiers a supprimer"""
        
        # Patterns des fichiers a supprimer
        delete_patterns = [
            # Scripts de fix temporaires
            r'^fix_.*\.py$',
            r'^force_.*\.py$',
            r'^final_fix\.py$',
            r'^manual_fix\.py$',
            
            # Scripts d'analyse temporaires
            r'^analyze_.*\.py$',
            r'^check_.*\.py$',
            
            # Versions alternatives de main
            r'^main_enhanced\.py$',
            r'^main_limited\.py$',
            r'^main_test_.*\.py$',
            
            # Scripts obsoletes
            r'^add_.*\.py$',
            r'^apply_transcriptions_manually\.py$',
            r'^clean_.*\.py$',
            r'^complete_export_all_contacts\.py$',
            r'^create_perfect_system\.py$',
            r'^direct_.*\.py$',
            r'^generer_tous_contacts_.*\.py$',
            r'^optimize_audio_processor\.py$',
            r'^restaurer_main\.py$',
            r'^regenerate_all\.py$',
            r'^rebuild_.*\.py$',
            
            # Fichiers de debug vides
            r'^mini_debug\.py$',
            r'^debug_transcriptions\.py$',
            
            # Copies
            r'.*- Copie\..*$',
            r'.*\.bak\..*$',
        ]
        
        # Fichiers essentiels a garder
        keep_patterns = [
            r'^main\.py$',
            r'^config\.py$',
            r'^requirements.*\.txt$',
            r'^README\.md$',
            r'^\.gitignore$',
            # Dossiers core
            r'^core/.*\.py$',
            r'^processors/.*\.py$',
            r'^exporters/(csv_exporter|text_exporter|merger|focused_csv_exporter|__init__)\.py$',
            r'^utils/.*\.py$',
        ]
        
        # Parcourir tous les fichiers
        for root, dirs, files in os.walk(self.project_path):
            # Ignorer le dossier de backup et .git
            if 'backup_' in root or '.git' in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.project_path)
                
                # Verifier si le fichier doit etre supprime
                should_delete = False
                for pattern in delete_patterns:
                    if re.match(pattern, file) or re.match(pattern, relative_path.replace('\\', '/')):
                        should_delete = True
                        break
                
                # Verifier si c'est un fichier essentiel
                is_essential = False
                for pattern in keep_patterns:
                    if re.match(pattern, file) or re.match(pattern, relative_path.replace('\\', '/')):
                        is_essential = True
                        break
                
                if should_delete and not is_essential:
                    self.files_to_delete.append(relative_path)
                elif file.endswith('.py'):
                    self.files_to_keep.append(relative_path)
        
        return {
            'to_delete': sorted(self.files_to_delete),
            'to_keep': sorted(self.files_to_keep)
        }
    
    def create_backup(self, files_to_backup: List[str]) -> bool:
        """Cree une sauvegarde des fichiers a supprimer"""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            
            for file_path in files_to_backup:
                full_path = os.path.join(self.project_path, file_path)
                if os.path.exists(full_path):
                    backup_path = os.path.join(self.backup_dir, file_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(full_path, backup_path)
            
            print(f"[OK] Backup cree dans: {self.backup_dir}")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur lors du backup: {e}")
            return False
    
    def fix_csv_exporter_bug(self) -> bool:
        """Corrige le bug dans csv_exporter.py"""
        csv_exporter_path = os.path.join(self.project_path, 'exporters', 'csv_exporter.py')
        
        if not os.path.exists(csv_exporter_path):
            print("[ERREUR] csv_exporter.py non trouve")
            return False
        
        try:
            with open(csv_exporter_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Corriger le bug du code duplique
            buggy_pattern = r'if os\.path\.getsize\(source_file\) < 100:[\s\S]*?logger\.warning\(f"Le fichier.*?n\'existe pas.*?"\)[\s\S]*?return'
            
            fixed_code = '''if not os.path.exists(source_file):
            logger.warning(f"Le fichier {os.path.basename(source_file)} n'existe pas")
            return
            
        if os.path.getsize(source_file) < 100:
            logger.error(f"Le fichier {os.path.basename(source_file)} est trop petit ({os.path.getsize(source_file)} octets)")
            return'''
            
            # Remplacer le code bugue
            if re.search(buggy_pattern, content):
                content = re.sub(buggy_pattern, fixed_code, content, count=1)
                
                with open(csv_exporter_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print("[OK] Bug corrige dans csv_exporter.py")
                self.optimizations.append("csv_exporter.py: bug du code duplique corrige")
                return True
            else:
                print("[INFO] Bug non trouve ou deja corrige dans csv_exporter.py")
                return True
                
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la correction: {e}")
            return False
    
    def optimize_logging(self) -> int:
        """Optimise les logs en remplacant les logger.info verbeux par logger.debug"""
        optimized_count = 0
        
        # Patterns de logs a optimiser
        verbose_patterns = [
            (r'logger\.info\(f?"UUID mapping.*?"\)', 'logger.debug'),
            (r'logger\.info\(f?"Mapping OPUS->MP3:.*?"\)', 'logger.debug'),
            (r'logger\.info\(f?"Correspondance.*?trouvee.*?"\)', 'logger.debug'),
            (r'logger\.info\(f?"Recherche transcription pour:.*?"\)', 'logger.debug'),
            (r'logger\.info\(f?"UUID extrait:.*?"\)', 'logger.debug'),
        ]
        
        for file_path in self.files_to_keep:
            if not file_path.endswith('.py'):
                continue
                
            full_path = os.path.join(self.project_path, file_path)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Appliquer les optimisations
                for pattern, replacement in verbose_patterns:
                    content = re.sub(pattern, replacement + '(\\1)', content)
                
                if content != original_content:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    optimized_count += 1
                    self.optimizations.append(f"{file_path}: logs optimises")
                    
            except Exception as e:
                print(f"[ATTENTION] Erreur optimisation {file_path}: {e}")
        
        return optimized_count
    
    def create_base_exporter(self) -> bool:
        """Cree une classe de base pour les exporters"""
        base_exporter_code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classe de base pour tous les exporters
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class BaseExporter(ABC):
    """Classe de base pour tous les exporters"""
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
        
    @abstractmethod
    def export(self, conversations: Dict[str, List[Dict]], **kwargs) -> bool:
        """Methode abstraite a implementer par chaque exporter"""
        pass
    
    def _ensure_directory(self, directory: str) -> bool:
        """S'assure qu'un repertoire existe"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Impossible de creer le repertoire {directory}: {e}")
            return False
    
    def _write_file_safe(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """Ecrit un fichier de maniere securisee"""
        try:
            # Ecrire dans un fichier temporaire d'abord
            temp_path = file_path + '.tmp'
            with open(temp_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Renommer atomiquement
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rename(temp_path, file_path)
            
            return True
        except Exception as e:
            logger.error(f"Erreur ecriture fichier {file_path}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def get_processing_mode(self) -> str:
        """Retourne le mode de traitement configure"""
        return self.config.get('Processing', 'mode', fallback='received_only')
'''
        
        base_exporter_path = os.path.join(self.project_path, 'exporters', 'base_exporter.py')
        
        try:
            with open(base_exporter_path, 'w', encoding='utf-8') as f:
                f.write(base_exporter_code)
            
            print("[OK] Classe BaseExporter creee")
            self.optimizations.append("base_exporter.py: nouvelle classe de base creee")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur creation BaseExporter: {e}")
            return False
    
    def delete_files(self, files_list: List[str], dry_run: bool = False) -> Tuple[int, int]:
        """Supprime les fichiers de la liste"""
        deleted_count = 0
        error_count = 0
        
        for file_path in files_list:
            full_path = os.path.join(self.project_path, file_path)
            
            if dry_run:
                if os.path.exists(full_path):
                    print(f"[DRY-RUN] Supprimerait: {file_path}")
                    deleted_count += 1
            else:
                try:
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        deleted_count += 1
                        print(f"[SUPPRIME] {file_path}")
                except Exception as e:
                    error_count += 1
                    print(f"[ERREUR] Impossible de supprimer {file_path}: {e}")
        
        return deleted_count, error_count
    
    def print_summary(self, analysis: Dict[str, List[str]]):
        """Affiche un resume de l'analyse"""
        print("\n" + "="*60)
        print("RESUME DE L'ANALYSE")
        print("="*60)
        print(f"Fichiers a supprimer: {len(analysis['to_delete'])}")
        print(f"Fichiers a garder: {len(analysis['to_keep'])}")
        print(f"\nReduction estimee: {len(analysis['to_delete']) + len(analysis['to_keep'])} -> {len(analysis['to_keep'])} fichiers")
        print(f"Gain: -{len(analysis['to_delete'])} fichiers ({len(analysis['to_delete'])*100//(len(analysis['to_delete']) + len(analysis['to_keep']))}%)")
        
        print("\n" + "-"*60)
        print("FICHIERS A SUPPRIMER (top 20):")
        print("-"*60)
        for file in analysis['to_delete'][:20]:
            print(f"  - {file}")
        if len(analysis['to_delete']) > 20:
            print(f"  ... et {len(analysis['to_delete']) - 20} autres fichiers")
    
    def run_cleanup(self, dry_run: bool = False, skip_backup: bool = False, auto_confirm: bool = False):
        """Execute le processus complet de nettoyage"""
        print("\n" + "="*60)
        print("WHATSAPP EXTRACTOR - NETTOYAGE ET OPTIMISATION")
        print("="*60)
        
        # 1. Analyse
        print("\n[1/5] Analyse du projet...")
        analysis = self.analyze_project()
        self.print_summary(analysis)
        
        if not analysis['to_delete']:
            print("\n[INFO] Aucun fichier a supprimer. Le projet est deja propre!")
            return
        
        # 2. Confirmation
        if not dry_run and not auto_confirm:
            print(f"\n[ATTENTION] {len(analysis['to_delete'])} fichiers vont etre supprimes!")
            response = input("Continuer? (oui/non): ").lower()
            if response not in ['oui', 'o', 'yes', 'y']:
                print("[ANNULE] Operation annulee par l'utilisateur")
                return
        elif not dry_run:
            print(f"\n[AUTO] Confirmation automatique pour supprimer {len(analysis['to_delete'])} fichiers")
        
        # 3. Backup
        if not skip_backup and not dry_run:
            print("\n[2/5] Creation du backup...")
            if not self.create_backup(analysis['to_delete']):
                print("[ERREUR] Echec du backup. Operation annulee.")
                return
        else:
            print("\n[2/5] Backup ignore")
        
        # 4. Corrections
        print("\n[3/5] Application des corrections...")
        self.fix_csv_exporter_bug()
        self.create_base_exporter()
        
        # 5. Optimisations
        print("\n[4/5] Optimisation des logs...")
        opt_count = self.optimize_logging()
        print(f"[OK] {opt_count} fichiers optimises")
        
        # 6. Suppression
        print("\n[5/5] Suppression des fichiers...")
        deleted, errors = self.delete_files(analysis['to_delete'], dry_run)
        
        # Resume final
        print("\n" + "="*60)
        print("NETTOYAGE TERMINE")
        print("="*60)
        print(f"Fichiers supprimes: {deleted}")
        print(f"Erreurs: {errors}")
        print(f"Optimisations: {len(self.optimizations)}")
        
        if self.optimizations:
            print("\nOptimisations appliquees:")
            for opt in self.optimizations:
                print(f"  - {opt}")
        
        if not dry_run:
            print(f"\n[INFO] Backup disponible dans: {self.backup_dir}")
            print("[INFO] Pour restaurer: copiez les fichiers du backup vers le projet")


def main():
    """Point d'entree principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nettoie et optimise WhatsApp Extractor')
    parser.add_argument('path', nargs='?', default='.',
                       help='Chemin vers le projet (defaut: repertoire actuel)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Mode simulation - ne supprime rien')
    parser.add_argument('--skip-backup', action='store_true',
                       help='Ne pas creer de backup (dangereux!)')
    parser.add_argument('--auto-confirm', action='store_true',
                       help='Confirmer automatiquement sans demander')
    
    args = parser.parse_args()
    
    # Verifier que le chemin existe
    if not os.path.exists(args.path):
        print(f"[ERREUR] Le chemin '{args.path}' n'existe pas")
        return 1
    
    # Verifier qu'on est dans un projet WhatsApp Extractor
    main_py = os.path.join(args.path, 'main.py')
    if not os.path.exists(main_py):
        print(f"[ERREUR] Pas de main.py trouve dans '{args.path}'")
        print("[INFO] Assurez-vous d'etre dans le repertoire du projet WhatsApp Extractor")
        return 1
    
    # Executer le nettoyage
    cleaner = WhatsAppExtractorCleaner(args.path)
    cleaner.run_cleanup(dry_run=args.dry_run, skip_backup=args.skip_backup, auto_confirm=args.auto_confirm)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())