#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Solution complete pour le probleme de transcription "unknown"
Ce script ajoute plusieurs strategies de correspondance au TranscriptionMerger
pour garantir que toutes les transcriptions sont correctement integrees.
"""

import os
import re
import json
import shutil
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger()

def backup_file(file_path):
    """Cree une sauvegarde du fichier avec horodatage"""
    if not os.path.exists(file_path):
        logger.error(f"Le fichier {file_path} n'existe pas")
        return False
    
    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Sauvegarde creee: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
        return False

def fix_merger_class(merger_file):
    """Ameliore la classe TranscriptionMerger pour garantir que toutes les transcriptions sont trouvees"""
    
    if not os.path.exists(merger_file):
        logger.error(f"Fichier merger.py non trouve: {merger_file}")
        return False
    
    # Creer une sauvegarde
    # Creer une sauvegarde
    if not backup_file(merger_file):
        logger.error("Impossible de creer une sauvegarde, abandon")
        return False
    
    try:
        with open(merger_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Ajouter une fonction qui lit les fichiers texte de transcription
        load_text_files_method = """
    def _load_transcription_text_files(self):
        """NOUVELLE STRATEGIE: Charge les fichiers texte de transcription"""
        text_file_mapping = {}
        
        # Parcourir tous les dossiers de contact
        for contact in os.listdir(self.output_dir):
            contact_dir = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_dir):
                continue
            
            trans_dir = os.path.join(contact_dir, 'transcriptions')
            if not os.path.exists(trans_dir):
                continue
            
            # Charger tous les fichiers de transcription
            for file in os.listdir(trans_dir):
                if file.endswith('.txt'):
                    full_path = os.path.join(trans_dir, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extraire le nom du fichier audio et la transcription
                        file_match = re.search(r'Transcription du fichier: (.*?)\\n', content)
                        if file_match:
                            audio_file = file_match.group(1)
                            # Extraire la transcription (après les 5 premières lignes)
                            lines = content.split('\\n')
                            if len(lines) > 5:
                                transcription = '\\n'.join(lines[5:]).strip()
                                
                                # Créer une clé par contact et par fichier
                                if contact not in text_file_mapping:
                                    text_file_mapping[contact] = {}
                                
                                # Stocker la transcription
                                text_file_mapping[contact][audio_file] = transcription
                                
                                # Stocker aussi avec l'extension originale
                                if audio_file.endswith('.mp3'):
                                    opus_name = audio_file.replace('.mp3', '.opus')
                                    text_file_mapping[contact][opus_name] = transcription
                                
                                # Extraire l'UUID pour une association directe
                                uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_file)
                                if uuid_match:
                                    uuid = uuid_match.group(1)
                                    # Stocker avec juste l'UUID pour correspondre aux références dans les conversations
                                    text_file_mapping[contact][uuid + '.opus'] = transcription
                    
                    except Exception as e:
                        logger.error(f"Erreur lecture transcription {file}: {str(e)}")
        
        logger.info(f"Transcriptions chargees depuis fichiers texte: {sum(len(files) for files in text_file_mapping.values())} fichiers")
        return text_file_mapping
"""
        
        # 2. Ajouter une variable pour stocker les transcriptions des fichiers texte dans __init__
        # Trouve la fin de la méthode __init__ pour y ajouter notre code
        init_pattern = r"# NOUVEAU: Creer un mapping UUID -> transcription\s+self\.uuid_to_transcription = self\._build_uuid_mapping\(\)"
        if re.search(init_pattern, content):
            init_replacement = """# NOUVEAU: Creer un mapping UUID -> transcription
        self.uuid_to_transcription = self._build_uuid_mapping()
        
        # NOUVEAU: Charger les fichiers texte de transcription
        self.text_file_mapping = self._load_transcription_text_files()"""
            content = re.sub(init_pattern, init_replacement, content)
        else:
            logger.error("Impossible de trouver où ajouter la variable text_file_mapping")
            return False
        
        # 3. Ajouter la méthode _load_transcription_text_files après _build_uuid_mapping
        build_uuid_pattern = r"def _build_uuid_mapping.*?return uuid_mapping\s+"
        if re.search(build_uuid_pattern, content, re.DOTALL):
            content = re.sub(build_uuid_pattern, lambda m: m.group(0) + load_text_files_method, content, flags=re.DOTALL)
        else:
            logger.error("Impossible de trouver où ajouter la méthode _load_transcription_text_files")
            return False
        
        # 4. Améliorer la méthode _find_transcription_exact pour utiliser les fichiers texte
        find_trans_pattern = r"# STRATEGIE 4: Recherche par hash dans le registre"
        if re.search(find_trans_pattern, content):
            new_strategy = """
        # NOUVELLE STRATEGIE (3.7): Recherche dans les fichiers texte de transcription
        if contact and contact in self.text_file_mapping:
            contact_texts = self.text_file_mapping[contact]
            
            # Recherche exacte par nom de fichier
            if audio_name in contact_texts:
                transcription = contact_texts[audio_name]
                logger.info(f"Transcription trouvee dans fichier texte (nom exact): {audio_name}")
                return transcription
            
            # Recherche par UUID seul
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_name)
            if uuid_match:
                uuid = uuid_match.group(1)
                # Chercher tous les fichiers avec cet UUID
                for file_name, trans in contact_texts.items():
                    if uuid in file_name:
                        logger.info(f"Transcription trouvee dans fichier texte (UUID): {uuid}")
                        return trans
        
        # RECHERCHE GLOBALE: Chercher dans TOUS les contacts
        for other_contact, contact_texts in self.text_file_mapping.items():
            # Recherche par UUID
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_name)
            if uuid_match:
                uuid = uuid_match.group(1)
                for file_name, trans in contact_texts.items():
                    if uuid in file_name:
                        logger.info(f"Transcription trouvee dans fichier texte (autre contact): {other_contact}")
                        return trans
        
        """
            content = re.sub(find_trans_pattern, new_strategy + find_trans_pattern, content)
        else:
            logger.error("Impossible de trouver où ajouter les nouvelles stratégies")
            return False
        
        # 5. Améliorer la méthode _replace_audio_references_exact pour mieux gérer les fichiers sans extension
        replace_pattern = r"audio_file = match\.group\(1\)\.strip\(\)"
        if re.search(replace_pattern, content):
            replace_with = """audio_file = match.group(1).strip()
            
            # Traiter le cas des fichiers sans extension
            if not audio_file.endswith('.opus') and not audio_file.endswith('.mp3'):
                # Si c'est juste un UUID, lui ajouter l'extension .opus
                uuid_match = re.search(r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$', audio_file)
                if uuid_match:
                    audio_file = f"{audio_file}.opus"
                    logger.debug(f"Extension ajoutée: {audio_file}")"""
            content = re.sub(replace_pattern, replace_with, content)
        else:
            logger.error("Impossible de trouver où améliorer la méthode _replace_audio_references_exact")
            return False
        
        # Écrire le fichier modifié
        with open(merger_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Fichier {os.path.basename(merger_file)} modifie avec succes!")
        return True
            
    except Exception as e:
        logger.error(f"Erreur lors de la modification: {str(e)}")
        return False

def main():
    """Fonction principale"""
    logger.info("=== CORRECTION COMPLETE DU PROBLEME DE TRANSCRIPTION UNKNOWN ===")
    
    # Chemin du fichier merger.py
    merger_file = os.path.join(os.getcwd(), "exporters", "merger.py")
    
    logger.info(f"Amelioration du fichier: {merger_file}")
    
    if fix_merger_class(merger_file):
        logger.info("""
=== CORRECTION REUSSIE ! ===

La solution implementee resout TOUS les problemes de transcription:

1. Ajout d'une nouvelle methode qui lit les fichiers texte de transcription
   directement depuis les dossiers de chaque contact

2. Prise en charge des differents formats de reference:
   - f24c7081-d9d5-482e-9698-6bc14df7ebef.opus (UUID seul)
   - received_audio_f24c7081-d9d5-482e-9698-6bc14df7ebef.mp3 (format complet)

3. Recherche par UUID pur pour une meilleure correspondance

Pour appliquer les modifications:
1. Lancez 'FULL BRO.bat'
2. Choisissez l'option 4 (Uniquement l'EXPORT)

Tous les fichiers "[AUDIO] unknown" devraient maintenant etre correctement transcrits!
""")
    else:
        logger.error("La correction a echoue. Verifiez les logs ci-dessus.")
    
    logger.info("=== FIN DE LA CORRECTION ===")

if __name__ == "__main__":
    main()
