import os
import sys
import shutil
import logging
from datetime import datetime

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_backup(filepath):
    """Crée une sauvegarde du fichier s'il existe"""
    if not os.path.exists(filepath):
        logger.warning(f"Le fichier {filepath} n'existe pas, aucune sauvegarde créée")
        return False
        
    backup_path = f"{filepath}.bak_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        shutil.copy2(filepath, backup_path)
        logger.info(f"Sauvegarde créée : {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la création de la sauvegarde : {str(e)}")
        return False

def fix_merger_export_issue():
    """
    Force la suppression des exports existants problématiques pour forcer leur régénération
    correcte avec les améliorations du TranscriptionMerger.
    """
    
    # 1. Chemins des fichiers à supprimer
    output_dir = "C:\\Datalead3webidu13juillet"
    problematic_files = [
        os.path.join(output_dir, "toutes_conversations_avec_transcriptions.txt"),
        os.path.join(output_dir, "messages_recus_only.txt"),
        os.path.join(output_dir, "messages_recus_only.csv"),
        os.path.join(output_dir, "messages_all.txt"),
        os.path.join(output_dir, "messages_all.csv"),
    ]
    
    # 2. Sauvegarder et supprimer les fichiers problématiques
    logger.info("=== CORRECTION DES EXPORTS AVEC TRANSCRIPTIONS ===")
    for file_path in problematic_files:
        if os.path.exists(file_path):
            create_backup(file_path)
            try:
                os.remove(file_path)
                logger.info(f"Fichier supprimé pour régénération: {file_path}")
            except Exception as e:
                logger.error(f"Impossible de supprimer {file_path}: {str(e)}")
        else:
            logger.warning(f"Le fichier n'existe pas: {file_path}")
    
    # 3. Exécuter main_enhanced.py avec les options pour générer uniquement les exports
    logger.info("Lancement de la régénération des exports...")
    
    # Astuce pour forcer la recréation complète des fichiers d'export
    # en incluant explicitement l'option --force-merger qui sera détectée dans main_enhanced.py
    try:
        import subprocess
        cmd = [
            "python", 
            "main_enhanced.py", 
            "--skip-extraction", 
            "--skip-media", 
            "--skip-audio", 
            "--skip-transcription",
            "--force-merger"  # Nouveau flag pour forcer la régénération
        ]
        logger.info(f"Exécution de la commande: {' '.join(cmd)}")
        
        # Exécuter la commande
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Régénération des exports réussie!")
            logger.info("Sortie: " + result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        else:
            logger.error(f"Erreur lors de la régénération: {result.returncode}")
            logger.error("Erreur: " + result.stderr)
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de main_enhanced.py: {str(e)}")
        
    logger.info("=== FIN DE LA CORRECTION ===")
    logger.info("Pour appliquer les changements, veuillez exécuter: python fix_export_complete.py")

if __name__ == "__main__":
    fix_merger_export_issue()
