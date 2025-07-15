#!/usr/bin/env python
import os
import re

def add_logs_to_transcriber(file_path):
    """Ajoute des logs de diagnostic au fichier transcriber.py"""
    print(f"Ajout de logs diagnostiques à {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter logs dans la méthode transcribe_all_super_files
    pattern = r"(super_files = self\.file_manager\.get_super_files\(contact\)[^\n]*\n)"
    replacement = r"\1        logger.info(f\"DIAGNOSTIC: Recherche de super fichiers pour contact {contact}\")\n        logger.info(f\"DIAGNOSTIC: Trouvé {len(super_files)} super fichiers\")\n        for sf_path, period in super_files:\n            logger.info(f\"DIAGNOSTIC: Super fichier trouvé: {os.path.basename(sf_path)}\")\n"
    content = re.sub(pattern, replacement, content)
    
    # Ajouter logs à la fin de transcribe_all_super_files avant le return
    pattern = r"(# Créer les fichiers consolidés[^\n]*\n\s+self\._create_consolidated_transcriptions\(\)[^\n]*\n)"
    replacement = r"\1        logger.info(\"DIAGNOSTIC: Exploration du répertoire de sortie pour trouver tous les MP3\")\n        mp3_count = 0\n        for root, dirs, files in os.walk(self.file_manager.output_dir):\n            for file in files:\n                if file.endswith('.mp3'):\n                    mp3_count += 1\n                    logger.info(f\"DIAGNOSTIC: MP3 existant: {os.path.join(root, file)}\")\n        logger.info(f\"DIAGNOSTIC: Total des fichiers MP3 trouvés: {mp3_count}\")\n"
    content = re.sub(pattern, replacement, content)
    
    # Ajouter logs dans _transcribe_file pour déboguer les appels API
    pattern = r"(try:[^\n]*\n\s+logger\.info\(f\"Transcription tentative [^\n]*\n)"
    replacement = r"\1                logger.info(f\"DIAGNOSTIC: Taille du fichier: {file_size / 1024 / 1024:.2f} MB\")\n                logger.info(f\"DIAGNOSTIC: Tentative d'envoi à l'API OpenAI...\")\n"
    content = re.sub(pattern, replacement, content)
    
    pattern = r"(response = self\.client\.audio\.transcriptions\.create[^\n]*\n)"
    replacement = r"\1                logger.info(f\"DIAGNOSTIC: Réponse API reçue avec succès\")\n"
    content = re.sub(pattern, replacement, content)
    
    # Sauvegarder les modifications
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Logs de diagnostic ajoutés à transcriber.py")

def add_logs_to_file_manager(file_path):
    """Ajoute des logs de diagnostic au fichier file_manager.py"""
    print(f"Ajout de logs diagnostiques à {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter logs au début de get_super_files
    pattern = r"(def get_super_files\(self, contact: str, direction: str = None\)[^\n]*\n\s+\"\"\"[^\"]*\"\"\")"
    replacement = r"\1\n        import logging\n        logger = logging.getLogger('whatsapp_extractor')\n        logger.info(f\"DIAGNOSTIC: get_super_files appelé pour contact {contact}, direction {direction}\")"
    content = re.sub(pattern, replacement, content)
    
    # Ajouter logs avant le return de get_super_files
    pattern = r"(# Trier par période[^\n]*\n\s+super_files\.sort[^\n]*\n\s+return super_files)"
    replacement = r"\1\n        logger.info(f\"DIAGNOSTIC: get_super_files retourne {len(super_files)} fichiers\")\n        for sf_path, period in super_files:\n            logger.info(f\"DIAGNOSTIC: Retourne super fichier: {os.path.basename(sf_path)}\")"
    content = re.sub(pattern, replacement, content)
    
    # Sauvegarder les modifications
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Logs de diagnostic ajoutés à file_manager.py")

def add_logs_to_audio_processor(file_path):
    """Ajoute des logs de diagnostic au fichier audio_processor.py"""
    print(f"Ajout de logs diagnostiques à {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter logs à la fin de _convert_single_file pour indiquer le chemin du fichier converti
    pattern = r"(return os.path.basename\(mp3_output\))"
    replacement = r"        logger.info(f\"DIAGNOSTIC: Fichier converti disponible à {mp3_output}\")\n        \1"
    content = re.sub(pattern, replacement, content)
    
    # Sauvegarder les modifications
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Logs de diagnostic ajoutés à audio_processor.py")

def add_diagnostic_logs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ajouter logs au transcriber
    transcriber_path = os.path.join(base_dir, 'processors', 'transcriber.py')
    add_logs_to_transcriber(transcriber_path)
    
    # Ajouter logs au file_manager
    file_manager_path = os.path.join(base_dir, 'core', 'file_manager.py')
    add_logs_to_file_manager(file_manager_path)
    
    # Ajouter logs à l'audio processor
    audio_processor_path = os.path.join(base_dir, 'processors', 'audio_processor.py')
    add_logs_to_audio_processor(audio_processor_path)
    
    print("Tous les logs diagnostiques ont été ajoutés avec succès.")
    print("Exécutez maintenant le test avec transcription pour obtenir les détails du problème.")

if __name__ == "__main__":
    add_diagnostic_logs()
