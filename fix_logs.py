#!/usr/bin/env python
import os

def fix_file_manager(file_path):
    """Corrige le fichier file_manager.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les guillemets mal échappés
    content = content.replace('f\"DIAGNOSTIC:', 'f"DIAGNOSTIC:')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier {file_path} corrigé")

def fix_transcriber(file_path):
    """Corrige le fichier transcriber.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les guillemets mal échappés
    content = content.replace('f\"DIAGNOSTIC:', 'f"DIAGNOSTIC:')
    content = content.replace('\"DIAGNOSTIC:', '"DIAGNOSTIC:')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier {file_path} corrigé")

def fix_audio_processor(file_path):
    """Corrige le fichier audio_processor.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer les guillemets mal échappés
    content = content.replace('f\"DIAGNOSTIC:', 'f"DIAGNOSTIC:')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier {file_path} corrigé")

def fix_all_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Corriger le file_manager
    file_manager_path = os.path.join(base_dir, 'core', 'file_manager.py')
    fix_file_manager(file_manager_path)
    
    # Corriger le transcriber
    transcriber_path = os.path.join(base_dir, 'processors', 'transcriber.py')
    fix_transcriber(transcriber_path)
    
    # Corriger l'audio_processor
    audio_processor_path = os.path.join(base_dir, 'processors', 'audio_processor.py')
    fix_audio_processor(audio_processor_path)
    
    print("Tous les fichiers ont été corrigés.")

if __name__ == "__main__":
    fix_all_files()
