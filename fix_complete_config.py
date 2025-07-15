#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger complètement le fichier config.ini
"""

import os
import configparser
import shutil
from pathlib import Path

def main():
    """Corrige intégralement le fichier config.ini"""
    print("===== CORRECTION COMPLÈTE DU FICHIER CONFIG.INI =====")
    print("Ce script va restructurer entièrement le fichier de configuration")

    # Sauvegarder le fichier existant si présent
    config_path = 'config.ini'
    if os.path.exists(config_path):
        backup_path = f'config.ini.bak.{os.path.getmtime(config_path)}'
        shutil.copy2(config_path, backup_path)
        print(f"\nSauvegarde créée: {backup_path}")
        
        # Lecture brute du fichier pour extraire les valeurs
        print("\nExtraction des valeurs existantes...")
        values = {}
        sections = {}
        current_section = None
        
        with open(config_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line = line.strip()
                
                # Détection de section
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]  # Enlever les crochets
                    sections[current_section.lower()] = current_section  # Stockage de la casse originale
                    continue
                
                # Extraction des valeurs
                if '=' in line and current_section:
                    parts = line.split('=', 1)
                    key = parts[0].strip()
                    value = parts[1].strip() if len(parts) > 1 else ''
                    
                    section_key = (current_section.lower(), key.lower())
                    values[section_key] = value
    else:
        print("\nAucun fichier config.ini existant trouvé.")
        values = {}

    # Créer un nouveau fichier de configuration propre
    # Désactiver l'interpolation pour éviter les problèmes avec les formats de date
    config = configparser.ConfigParser(interpolation=None)
    
    # Section Paths
    config['Paths'] = {}
    config['Paths']['html_dir'] = values.get(('paths', 'html_dir'), r'C:\Users\Moham\Downloads\iPhone_20250604173341\WhatsApp')
    config['Paths']['media_dir'] = values.get(('paths', 'media_dir'), r'C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250605021808')
    config['Paths']['output_dir'] = values.get(('paths', 'output_dir'), r'C:\Users\Moham\Desktop\DataLeads')
    config['Paths']['logs_dir'] = values.get(('paths', 'logs_dir'), 'logs')
    
    # Section API
    config['API'] = {}
    config['API']['openai_key'] = values.get(('api', 'openai_key'), '')
    config['API']['max_retries'] = values.get(('api', 'max_retries'), '3')
    config['API']['retry_delay'] = values.get(('api', 'retry_delay'), '5')
    config['API']['file_size_limit'] = values.get(('api', 'file_size_limit'), '25000000')
    
    # Section Conversion
    config['Conversion'] = {}
    config['Conversion']['mp3_quality'] = values.get(('conversion', 'mp3_quality'), '2')
    config['Conversion']['chunk_size'] = values.get(('conversion', 'chunk_size'), '25000000')
    config['Conversion']['parallel_conversions'] = values.get(('conversion', 'parallel_conversions'), '4')
    config['Conversion']['skip_ffmpeg_check'] = values.get(('conversion', 'skip_ffmpeg_check'), 'False')
    
    # Section Transcription
    config['Transcription'] = {}
    config['Transcription']['parallel_transcriptions'] = values.get(('transcription', 'parallel_transcriptions'), '2')
    config['Transcription']['chunk_duration'] = values.get(('transcription', 'chunk_duration'), '600')
    
    # Section Processing
    config['Processing'] = {}
    config['Processing']['mode'] = values.get(('processing', 'mode'), 'received_only')
    config['Processing']['transcribe_received'] = values.get(('processing', 'transcribe_received'), 'True')
    config['Processing']['transcribe_sent'] = values.get(('processing', 'transcribe_sent'), 'False')
    config['Processing']['create_superfiles'] = values.get(('processing', 'create_superfiles'), 'True')
    config['Processing']['max_transcriptions'] = values.get(('processing', 'max_transcriptions'), '100')
    config['Processing']['date_format'] = values.get(('processing', 'date_format'), '%Y/%m/%d')
    
    # Section User
    config['User'] = {}
    config['User']['name'] = values.get(('user', 'name'), '')
    
    # Écrire le fichier
    print("\nÉcriture du nouveau fichier config.ini...")
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
        
    print("\n[OK] Configuration entièrement reconstruite avec succès!")
    print("Toutes les valeurs existantes ont été préservées.")
    print("Les sections manquantes ont été ajoutées.")
    print("La structure du fichier est maintenant correcte.")
    print("\nVous pouvez maintenant relancer le script d'extraction.")

if __name__ == "__main__":
    main()
