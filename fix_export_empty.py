#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Solution de correction pour les exports vides avec transcriptions manquantes
Ce script force la régénération complète des exports à partir du registre
"""

import os
import json
import re
from datetime import datetime
import logging
import subprocess
import shutil

# Configurer le logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_file(file_path):
    """Crée une sauvegarde du fichier"""
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup.{timestamp}"
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Sauvegarde créée: {backup_path}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {file_path}: {str(e)}")

def debug_transcriptions():
    """Fonction de debug des transcriptions pour trouver pourquoi elles ne sont pas fusionnées"""
    output_dir = r"C:\Datalead3webidu13juillet"
    
    # Exemple avec un contact spécifique
    contact_example = "_33_6_65_35_06_02"
    contact_dir = os.path.join(output_dir, contact_example)
    trans_dir = os.path.join(contact_dir, 'transcriptions')
    
    if not os.path.exists(trans_dir):
        logger.error(f"❌ Dossier transcriptions inexistant: {trans_dir}")
        return
    
    logger.info(f"✓ Dossier de transcriptions trouvé: {trans_dir}")
    
    # Vérifier les fichiers de transcription
    transcription_files = [f for f in os.listdir(trans_dir) if f.endswith('.txt')]
    logger.info(f"✓ {len(transcription_files)} fichiers de transcription trouvés")
    
    # Exemple avec un fichier de transcription
    if transcription_files:
        example_file = os.path.join(trans_dir, transcription_files[0])
        try:
            with open(example_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Contenu du fichier {os.path.basename(example_file)}:")
            logger.info("---")
            logger.info(content[:300] + "...")
            logger.info("---")
            
            # Extraire le nom du fichier audio et la transcription selon la logique du merger
            file_match = re.search(r'Transcription du fichier: (.*?)\n', content)
            if file_match:
                audio_file = file_match.group(1)
                logger.info(f"✓ Nom du fichier audio extrait: {audio_file}")
                
                # Extraire la transcription (après les 5 premières lignes)
                lines = content.split('\n')
                if len(lines) > 5:
                    transcription = '\n'.join(lines[5:]).strip()
                    logger.info(f"✓ Transcription extraite ({len(transcription)} caractères): {transcription[:50]}...")
                else:
                    logger.error("❌ Format de transcription incorrect (moins de 5 lignes)")
            else:
                logger.error("❌ Format de transcription incorrect (pas de ligne 'Transcription du fichier:')")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la lecture du fichier: {str(e)}")
    
    # Vérifier les fichiers d'export pour voir si les transcriptions y sont référencées
    messages_with_trans = os.path.join(contact_dir, "messages_recus_avec_transcriptions.txt")
    if os.path.exists(messages_with_trans):
        try:
            with open(messages_with_trans, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Compter les références [AUDIO]
            audio_refs = re.findall(r'\[AUDIO\]', content)
            audio_unknown = re.findall(r'\[AUDIO\] unknown', content)
            audio_with_trans = len(audio_refs) - len(audio_unknown)
            
            logger.info(f"Dans le fichier {os.path.basename(messages_with_trans)}:")
            logger.info(f"- Total références audio: {len(audio_refs)}")
            logger.info(f"- Audio sans transcription: {len(audio_unknown)}")
            logger.info(f"- Audio avec transcription: {audio_with_trans}")
            
            # Vérifier les UUID dans le fichier
            uuids_in_file = re.findall(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', content)
            logger.info(f"- UUID trouvés dans le fichier: {len(set(uuids_in_file))}")
            
            # Vérifier les UUID dans les noms de fichiers de transcription
            trans_uuids = []
            for tf in transcription_files:
                uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', tf)
                if uuid_match:
                    trans_uuids.append(uuid_match.group(1))
            
            logger.info(f"- UUID trouvés dans les fichiers de transcription: {len(set(trans_uuids))}")
            
            # Comparer les ensembles
            common_uuids = set(uuids_in_file).intersection(set(trans_uuids))
            logger.info(f"- UUID en commun: {len(common_uuids)}")
            
            if common_uuids:
                logger.info(f"- Exemples d'UUID en commun: {list(common_uuids)[:3]}")
            
            # Vérifier si les UUID des transcriptions apparaissent dans le contenu
            for uuid in trans_uuids[:3]:
                if uuid in content:
                    logger.info(f"✓ UUID {uuid} présent dans le fichier d'export")
                else:
                    logger.error(f"❌ UUID {uuid} ABSENT du fichier d'export")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification du fichier d'export: {str(e)}")

def fix_empty_exports():
    """Corrige les exports vides en forçant une régénération complète"""
    output_dir = "C:\\Datalead3webidu13juillet"
    registry_path = os.path.join(output_dir, ".unified_registry.json")
    
    logger.info("=== CORRECTION DES EXPORTS VIDES ===")
    
    # Débugger les transcriptions
    debug_transcriptions()
    
    # Vérifier que le registre existe
    if not os.path.exists(registry_path):
        logger.error(f"Registre non trouvé: {registry_path}")
        return False
    
    # Sauvegarder les fichiers importants avant de les supprimer
    important_files = [
        os.path.join(output_dir, "toutes_conversations.txt"),
        os.path.join(output_dir, "toutes_conversations_avec_transcriptions.txt"),
        os.path.join(output_dir, "messages_recus_only.txt"),
        os.path.join(output_dir, "messages_recus_only.csv"),
        os.path.join(output_dir, "messages_all.txt"),
        os.path.join(output_dir, "messages_all.csv")
    ]
    
    for file_path in important_files:
        backup_file(file_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Fichier supprimé pour régénération: {file_path}")
            except Exception as e:
                logger.error(f"Impossible de supprimer {file_path}: {str(e)}")
    
    # Forcer l'extraction complète et la régénération des fichiers
    logger.info("Lancement de la régénération complète des exports...")
    
    # Option 1: Régénérer complètement (désactivée)
    # cmd = ["python", "main_enhanced.py", "--full", "--debug"]  # Tout régénérer (peut être long)
    
    # Option 2: Sauter l'extraction mais forcer la fusion et l'export (activée)
    cmd = ["python", "main_enhanced.py", 
          "--skip-extraction",  # On garde les conversations extraites
          "--skip-media",       # On garde les médias extraits
          "--skip-audio",       # On garde les conversions audio
          "--skip-transcription",  # On garde les transcriptions
          "--force-merger",     # Force la fusion avec transcriptions
          "--minimal-export"]   # Mode export minimal (uniquement messages reçus avec transcriptions)
    
    try:
        logger.info(f"Exécution de la commande: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        logger.info(f"Sortie: {result.stdout[:500]}...")  # Afficher les 500 premiers caractères
        
        # Vérifier la taille des fichiers générés
        for file_path in important_files:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                logger.info(f"Fichier généré: {os.path.basename(file_path)} - Taille: {size} octets")
                if size < 1000:  # Si moins de 1Ko
                    logger.warning(f"Le fichier {os.path.basename(file_path)} est toujours très petit!")
            else:
                logger.warning(f"Fichier non généré: {os.path.basename(file_path)}")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erreur lors de la régénération: {str(e)}")
        logger.error(f"Stderr: {e.stderr}")
        return False

if __name__ == "__main__":
    # Configurer le niveau de logging à DEBUG pour voir tous les détails
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if fix_empty_exports():
        print("\n===== RÉPARATION TERMINÉE =====")
        print("1) Vérifiez les nouveaux fichiers d'export.")
        print("2) Si les fichiers sont toujours vides, essayez:")
        print("   - Vérifiez le dossier d'origine des fichiers HTML")
        print("   - Modifiez le script pour utiliser l'option --full")
        print("3) Les transcriptions devraient maintenant apparaître dans tous les exports.")
    else:
        print("\n===== ÉCHEC DE LA RÉPARATION =====")
        print("Veuillez vérifier les logs pour plus d'informations.")
        print("Conseil: Assurez-vous que le registre unifié est complet et valide.")
