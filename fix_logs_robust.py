#!/usr/bin/env python
import os
import re

def fix_file_content(file_path):
    """Corrige tous les problèmes de guillemets échappés dans un fichier"""
    print(f"Traitement du fichier: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Cas spécifique: logger.info(f\"DIAGNOSTIC...)
    content = re.sub(r'logger\.info\(f\\\"DIAGNOSTIC:', r'logger.info("DIAGNOSTIC:', content)
    content = re.sub(r'\\\"DIAGNOSTIC:', r'"DIAGNOSTIC:', content)
    
    # Cas général: f\"
    content = re.sub(r'f\\\"', r'f"', content)
    
    # Supprimer le code de log mal placé dans get_super_files
    content = re.sub(r'return super_files\n\s+logger\.info\(.*\n\s+for.*\n\s+logger\.info\(.*\n', 'return super_files\n', content)
    
    # Ajouter les logs corrects au bon endroit dans get_super_files
    if 'get_super_files' in content:
        lines = content.split('\n')
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if "super_files.sort(key=lambda x: x[1])" in line:
                # Ajouter logs avant le return
                new_lines.append('        logger.info("DIAGNOSTIC: get_super_files retourne %d fichiers" % len(super_files))')
                new_lines.append('        for sf_path, period in super_files:')
                new_lines.append('            logger.info("DIAGNOSTIC: Retourne super fichier: %s" % os.path.basename(sf_path))')
        content = '\n'.join(new_lines)
    
    # Enregistrer les modifications
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fichier corrigé: {file_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Liste des fichiers à corriger
    files_to_fix = [
        os.path.join(base_dir, 'core', 'file_manager.py'),
        os.path.join(base_dir, 'processors', 'transcriber.py'),
        os.path.join(base_dir, 'processors', 'audio_processor.py')
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fix_file_content(file_path)

if __name__ == "__main__":
    main()
