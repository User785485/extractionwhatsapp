#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour corriger le fichier config.ini
"""

import os
import configparser
import shutil
from pathlib import Path

def main():
    """Corrige le fichier config.ini en préservant les chemins"""
    print("===== UTILITAIRE DE RÉPARATION CONFIG.INI =====")
    print("Ce script va corriger le fichier de configuration")

    # Sauvegarder le fichier existant si présent
    config_path = 'config.ini'
    if os.path.exists(config_path):
        # Lecture des valeurs actuelles
        print("\nLecture de la configuration existante...")
        try:
            current_config = configparser.ConfigParser(interpolation=None)
            current_config.read(config_path, encoding='utf-8')
            
            # Récupérer les valeurs des chemins si elles existent
            html_dir = None
            media_dir = None
            output_dir = None
            logs_dir = None
            
            for section in ['Paths', 'PATHS', 'paths']:
                if section in current_config:
                    html_dir = current_config.get(section, 'html_dir', fallback=None)
                    media_dir = current_config.get(section, 'media_dir', fallback=None)
                    output_dir = current_config.get(section, 'output_dir', fallback=None)
                    logs_dir = current_config.get(section, 'logs_dir', fallback=None)
                    break
            
            print(f"Valeurs trouvées:")
            print(f"- HTML dir: {html_dir}")
            print(f"- Media dir: {media_dir}")
            print(f"- Output dir: {output_dir}")
            print(f"- Logs dir: {logs_dir}")
            
            # Créer une sauvegarde
            backup_path = f'config.ini.bak'
            shutil.copy2(config_path, backup_path)
            print(f"\nSauvegarde créée: {backup_path}")
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier: {e}")
            html_dir = None
            media_dir = None
            output_dir = None
            logs_dir = None
    else:
        print("\nAucun fichier config.ini existant trouvé.")
        html_dir = None
        media_dir = None
        output_dir = None
        logs_dir = None

    # Créer une nouvelle config avec la structure correcte
    config = configparser.ConfigParser(interpolation=None)
    
    # Section Paths (respecter la casse exacte)
    config['Paths'] = {}
    config['Paths']['html_dir'] = html_dir if html_dir else r'C:\Users\Moham\Downloads\iPhone_20250604173341\WhatsApp'
    config['Paths']['media_dir'] = media_dir if media_dir else r'C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250605021808'
    config['Paths']['output_dir'] = output_dir if output_dir else r'C:\Users\Moham\Desktop\Data Leads'
    config['Paths']['logs_dir'] = logs_dir if logs_dir else 'logs'
    
    # Section API
    config['API'] = {}
    config['API']['openai_key'] = ''
    config['API']['max_retries'] = '3'
    config['API']['retry_delay'] = '5'
    config['API']['file_size_limit'] = '25000000'
    
    # Section Conversion
    config['Conversion'] = {}
    config['Conversion']['mp3_quality'] = '2'
    config['Conversion']['chunk_size'] = '25000000'
    config['Conversion']['parallel_conversions'] = '4'
    config['Conversion']['skip_ffmpeg_check'] = 'False'
    
    # Section Transcription
    config['Transcription'] = {}
    config['Transcription']['parallel_transcriptions'] = '2'
    config['Transcription']['chunk_duration'] = '600'
    
    # Section Processing
    config['Processing'] = {}
    config['Processing']['mode'] = 'received_only'
    config['Processing']['transcribe_received'] = 'True'
    config['Processing']['transcribe_sent'] = 'False'
    config['Processing']['create_superfiles'] = 'True'
    config['Processing']['max_transcriptions'] = '100' 
    config['Processing']['date_format'] = '%Y/%m/%d'
    
    # Section User
    config['User'] = {}
    config['User']['name'] = ''
    
    # Écrire le fichier
    print("\nÉcriture du nouveau fichier config.ini...")
    with open(config_path, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
        
    print("\n[OK] Configuration corrigée avec succès!")
    print("Les chemins personnalisés ont été préservés.")
    print("\nVous pouvez maintenant relancer le script extraction_interactive_fixed.bat")

if __name__ == "__main__":
    main()
