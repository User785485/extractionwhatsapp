#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script d'optimisation pour AudioProcessor - Accélère la vérification des fichiers déjà convertis
en utilisant une méthode de cache plutôt que des vérifications fichier par fichier
"""

import os
import re
import time
import logging
import configparser
from typing import Dict, Set

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger()

def optimize_audio_processor():
    """
    Optimise le fichier audio_processor.py pour accélérer la vérification des fichiers déjà convertis
    """
    # Chemins des fichiers
    processors_dir = os.path.join(os.getcwd(), "processors")
    audio_processor_path = os.path.join(processors_dir, "audio_processor.py")
    backup_path = os.path.join(processors_dir, "audio_processor.py.backup")
    
    # Créer une sauvegarde
    if os.path.exists(audio_processor_path):
        logger.info(f"Création d'une sauvegarde: {backup_path}")
        with open(audio_processor_path, 'r', encoding='utf-8') as f_src:
            content = f_src.read()
        with open(backup_path, 'w', encoding='utf-8') as f_dst:
            f_dst.write(content)
    else:
        logger.error(f"Fichier audio_processor.py introuvable à: {audio_processor_path}")
        return False
    
    # Lire le contenu du fichier
    with open(audio_processor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Modifier le contenu pour ajouter le cache
    
    # 1. Ajouter import time
    if 'import time' not in content:
        content = content.replace('import os', 'import os\nimport time')
    
    # 2. Ajouter méthode de construction du cache après _get_ffmpeg_path
    build_cache_method = """
    def _build_converted_files_cache(self):
        \"\"\"
        OPTIMISATION : Pré-scanner tous les fichiers MP3 déjà convertis
        et créer un cache pour accélérer les vérifications
        \"\"\"
        cache = {}
        start_time = time.time()
        
        # Scanner le répertoire de sortie pour tous les contacts
        output_dir = self.file_manager.output_dir
        contacts_found = 0
        
        logger.info("Création du cache des fichiers audio déjà convertis...")
        
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            
            if not os.path.isdir(item_path) or item.startswith('.'):
                continue
                
            contacts_found += 1
            mp3_dir = os.path.join(item_path, "audio_mp3")
            
            if not os.path.exists(mp3_dir):
                continue
            
            # Scanner les fichiers MP3 existants
            for mp3_file in os.listdir(mp3_dir):
                if mp3_file.endswith('.mp3'):
                    mp3_path = os.path.join(mp3_dir, mp3_file)
                    
                    # Vérifier que le fichier est valide
                    if os.path.getsize(mp3_path) > 1000:
                        # Extraire le nom de base sans extension
                        basename = re.sub(r'\\.mp3$', '', mp3_file)
                        cache[basename] = True
        
        duration = time.time() - start_time
        logger.info(f"Cache créé en {duration:.2f} secondes: {len(cache)} fichiers MP3 dans {contacts_found} contacts")
        return cache
    """
    
    # Trouver la fin de la méthode _get_ffmpeg_path pour insérer le nouveau code
    ffmpeg_end_pattern = "        return ffmpeg_path"
    if ffmpeg_end_pattern in content:
        content = content.replace(ffmpeg_end_pattern, ffmpeg_end_pattern + build_cache_method)
    
    # 3. Initialiser le cache dans __init__
    init_end_pattern = "        # Logger de debug\n        self.debug_log = []"
    cache_init_code = """        # Logger de debug
        self.debug_log = []
        
        # OPTIMISATION : Créer un cache des fichiers déjà convertis
        self.converted_files_cache = self._build_converted_files_cache()
        logger.info(f"Cache des fichiers convertis créé avec {len(self.converted_files_cache)} entrées")"""
    
    if init_end_pattern in content:
        content = content.replace(init_end_pattern, cache_init_code)
    
    # 4. Modifier la méthode _convert_single_file pour utiliser le cache
    old_check = """        # Si déjà converti et valide
        if os.path.exists(final_output) and os.path.getsize(final_output) > 1000:
            logger.info(f"Déjà converti: {safe_name}")
            self.stats['skipped'][direction] += 1
            return final_output"""
    
    new_check = """        # OPTIMISATION : Vérifier le cache au lieu du disque
        if safe_name in self.converted_files_cache:
            # Vérification plus rapide via le cache
            logger.info(f"Déjà converti (cache): {safe_name}")
            self.stats['skipped'][direction] += 1
            return final_output
            
        # Fallback: vérifier sur le disque et ajouter au cache si trouvé
        if os.path.exists(final_output) and os.path.getsize(final_output) > 1000:
            logger.info(f"Déjà converti (disque): {safe_name}")
            self.converted_files_cache[safe_name] = True
            self.stats['skipped'][direction] += 1
            return final_output"""
    
    if old_check in content:
        content = content.replace(old_check, new_check)
    
    # Écrire le contenu modifié
    with open(audio_processor_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"AudioProcessor optimisé avec succès: {audio_processor_path}")
    logger.info("Les vérifications de conversion sont maintenant accélérées grâce au cache en mémoire.")
    return True

if __name__ == "__main__":
    logger.info("=== DÉBUT OPTIMISATION AUDIOPROCESSOR ===")
    success = optimize_audio_processor()
    if success:
        logger.info("Optimisation réussie ! Le processus de vérification est maintenant beaucoup plus rapide.")
    else:
        logger.error("L'optimisation a échoué.")
    logger.info("=== FIN OPTIMISATION AUDIOPROCESSOR ===")
