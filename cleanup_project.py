#!/usr/bin/env python
"""
Script de nettoyage pour organiser le projet WhatsApp Extractor v2
Supprime les fichiers obsolètes tout en préservant le nouveau code v2
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectCleaner:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.files_to_delete = []
        self.dirs_to_delete = []
        self.files_to_keep = []
        
    def analyze_project(self):
        """Analyser le projet et identifier les fichiers à supprimer/garder"""
        
        # FICHIERS À GARDER ABSOLUMENT (nouveau code v2)
        keep_patterns = [
            # Nouveau code v2.0
            'src/',
            'tests/',
            'scripts/',
            'docs/',
            
            # Configuration et documentation importante
            'requirements.txt',
            'requirements-dev.txt',
            'setup.py',
            'README_v2.md',
            'ARCHITECTURE_REDESIGN.md',
            'PROGRESS_REPORT.md',
            'claude.md',
            
            # Scripts de backup et nettoyage
            'create_full_backup.py',
            'cleanup_project.py',
            
            # Données importantes
            'config.ini',  # Configuration actuelle
            'ffmpeg/',     # FFmpeg binaire
            
            # Backups récents (garder le plus récent)
            'backup_20250715_234326.zip',
            'backup_20250715_234326_info.txt',
        ]
        
        # FICHIERS/DOSSIERS À SUPPRIMER (ancien code v1)
        delete_patterns = [
            # Ancien backup énorme
            'backup_20250715_101140/',
            
            # Autres backups (garder seulement le plus récent)
            'backup_20250715_234254.zip',
            'backup_20250715_234314.zip',
            'backup_20250715_234314_info.txt',
            
            # Ancien code v1 et fichiers obsolètes
            'core/',  # Ancien core (remplacé par src/core/)
            'exporters/',  # Ancien exporters (remplacé par src/exporters/)
            'processors/',  # Ancien processors (remplacé par src/processors/)
            'utils/',  # Ancien utils (remplacé par src/utils/)
            
            # Scripts de test et développement obsolètes
            'analyze_contacts_by_date.bat',
            'analyze_contacts_clean.py',
            'analyze_contacts_date.py',
            'check_export.py',
            'cleanup_disk.py',
            'cleanup_exports.py',
            'cleanup_script.py',
            'correction.py',
            'correction_simple.py',
            'create_backups.py',
            'diagnostic.py',
            'diagnostic_export.py',
            'find_missing_contacts.py',
            'full_export_rebuild.py',
            'migrate.py',
            'scriptcorrection.py',
            'search_number.py',
            'test_export.py',
            'transcription_reader.py',
            'verif_contacts.py',
            'verify_fix.py',
            'modifier_chemins.py',
            'modifier_chemins_simple.py',
            'afficher_chemins.py',
            
            # Fichiers batch obsolètes
            '*.bat',
            
            # Fichiers de configuration obsolètes
            'config.py',  # Remplacé par src/config/
            'config.ini.bak',
            'config_new.ini',
            
            # Fichiers de données temporaires
            'contacts_apres_*.json',
            'contacts_apres_*.txt',
            'duplicates_report.json',
            'duplicates_backup/',
            
            # Fichiers de logs anciens
            'logs/',
            '*.log',
            
            # Fichiers de documentation obsolètes
            'code_*.txt',
            'flux_exportation_documentation.txt',
            'structure_projet.txt',
            'fichiers_avec_parentheses.txt',
            'diagnostic_export_deep.log',
            
            # Backups de fichiers
            '*.backup',
            '*.backup_*',
            '*.bak',
            'main.py.backup_*',
            'main_enhanced_backup_*.py',
            
            # Fichiers temporaires
            'nul',
            
            # Test data (si vide)
            'test_data/',
        ]
        
        # Parcourir le projet
        for item in self.project_root.rglob('*'):
            relative_path = item.relative_to(self.project_root)
            
            # Vérifier si le fichier doit être gardé
            should_keep = False
            for pattern in keep_patterns:
                if str(relative_path).startswith(pattern) or relative_path.name == pattern:
                    should_keep = True
                    self.files_to_keep.append(item)
                    break
            
            if should_keep:
                continue
                
            # Vérifier si le fichier doit être supprimé
            should_delete = False
            for pattern in delete_patterns:
                if pattern.endswith('/'):
                    # Dossier
                    if str(relative_path).startswith(pattern.rstrip('/')):
                        should_delete = True
                        break
                elif '*' in pattern:
                    # Pattern avec wildcard
                    import fnmatch
                    if fnmatch.fnmatch(relative_path.name, pattern):
                        should_delete = True
                        break
                else:
                    # Fichier exact
                    if str(relative_path) == pattern or relative_path.name == pattern:
                        should_delete = True
                        break
            
            if should_delete:
                if item.is_dir():
                    self.dirs_to_delete.append(item)
                else:
                    self.files_to_delete.append(item)
    
    def show_cleanup_plan(self):
        """Afficher le plan de nettoyage"""
        logger.info("PLAN DE NETTOYAGE")
        logger.info("=" * 50)
        
        logger.info(f"FICHIERS À GARDER ({len(self.files_to_keep)}):")
        for file in sorted(self.files_to_keep)[:20]:  # Montrer les 20 premiers
            logger.info(f"  ✓ {file.relative_to(self.project_root)}")
        if len(self.files_to_keep) > 20:
            logger.info(f"  ... et {len(self.files_to_keep) - 20} autres")
        
        logger.info(f"\nFICHIERS À SUPPRIMER ({len(self.files_to_delete)}):")
        for file in sorted(self.files_to_delete)[:20]:  # Montrer les 20 premiers
            logger.info(f"  ✗ {file.relative_to(self.project_root)}")
        if len(self.files_to_delete) > 20:
            logger.info(f"  ... et {len(self.files_to_delete) - 20} autres")
        
        logger.info(f"\nDOSSIERS À SUPPRIMER ({len(self.dirs_to_delete)}):")
        for dir in sorted(self.dirs_to_delete):
            logger.info(f"  ✗ {dir.relative_to(self.project_root)}/")
    
    def calculate_space_savings(self):
        """Calculer l'espace qui sera libéré"""
        total_size = 0
        
        for file in self.files_to_delete:
            if file.exists():
                total_size += file.stat().st_size
        
        for dir in self.dirs_to_delete:
            if dir.exists():
                for file in dir.rglob('*'):
                    if file.is_file():
                        total_size += file.stat().st_size
        
        return total_size
    
    def perform_cleanup(self, dry_run=True):
        """Effectuer le nettoyage"""
        if dry_run:
            logger.info("MODE SIMULATION - Aucun fichier ne sera supprimé")
            space_saved = self.calculate_space_savings()
            logger.info(f"Espace qui serait libéré: {space_saved / (1024*1024):.2f} MB")
            return
        
        logger.info("DÉBUT DU NETTOYAGE RÉEL")
        
        # Créer un backup avant nettoyage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.project_root / f"backup_before_cleanup_{timestamp}.zip"
        
        try:
            import zipfile
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Backup seulement les fichiers importants
                for file in self.files_to_keep[:50]:  # Limiter pour éviter un backup trop gros
                    if file.is_file():
                        arcname = file.relative_to(self.project_root)
                        zf.write(file, arcname)
            logger.info(f"Backup créé: {backup_file}")
        except Exception as e:
            logger.error(f"Erreur lors du backup: {e}")
            return
        
        # Supprimer les fichiers
        deleted_files = 0
        for file in self.files_to_delete:
            try:
                if file.exists():
                    file.unlink()
                    deleted_files += 1
                    logger.debug(f"Supprimé: {file.relative_to(self.project_root)}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de {file}: {e}")
        
        # Supprimer les dossiers
        deleted_dirs = 0
        for dir in sorted(self.dirs_to_delete, reverse=True):  # Supprimer les plus profonds en premier
            try:
                if dir.exists():
                    shutil.rmtree(dir)
                    deleted_dirs += 1
                    logger.info(f"Dossier supprimé: {dir.relative_to(self.project_root)}/")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression du dossier {dir}: {e}")
        
        logger.info(f"NETTOYAGE TERMINÉ: {deleted_files} fichiers et {deleted_dirs} dossiers supprimés")

def main():
    project_root = Path(__file__).parent
    cleaner = ProjectCleaner(project_root)
    
    logger.info("Analyse du projet...")
    cleaner.analyze_project()
    
    logger.info("Plan de nettoyage:")
    cleaner.show_cleanup_plan()
    
    space_saved = cleaner.calculate_space_savings()
    logger.info(f"\nEspace à libérer: {space_saved / (1024*1024):.2f} MB")
    
    # Nettoyage automatique (préservation du nouveau code v2.0)
    print("\n" + "="*50)
    print("NETTOYAGE AUTOMATIQUE")
    print("- Le nouveau code v2.0 dans src/ sera préservé")
    print("- Les fichiers obsolètes seront supprimés")
    print("- Un backup sera créé avant la suppression")
    print("="*50)
    
    logger.info("Procédure de nettoyage automatique...")
    cleaner.perform_cleanup(dry_run=False)
    logger.info("Nettoyage terminé ! Projet organisé et propre.")

if __name__ == "__main__":
    main()