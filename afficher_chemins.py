#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour afficher les chemins actuels des fichiers HTML et média
"""

import os
import configparser
import sys

def main():
    # Chemin du fichier de configuration
    config_file = 'config.ini'
    
    # Charger la configuration
    config = configparser.ConfigParser(interpolation=None)
    if os.path.exists(config_file):
        config.read(config_file, encoding='utf-8')
    else:
        print(f"Erreur: Le fichier {config_file} n'existe pas.")
        sys.exit(1)
    
    # Récupérer les chemins
    if config.has_section('Paths'):
        section = 'Paths'
    elif config.has_section('PATHS'):
        section = 'PATHS'
    else:
        print("Aucune section 'Paths' trouvée dans le fichier de configuration.")
        sys.exit(1)
    
    # Afficher les chemins actuels
    html_dir = config.get(section, 'html_dir', fallback='Non défini')
    media_dir = config.get(section, 'media_dir', fallback='Non défini')
    output_dir = config.get(section, 'output_dir', fallback='Non défini')
    
    print("\n" + "="*60)
    print("CHEMINS ACTUELS DANS CONFIG.INI")
    print("="*60)
    print(f"HTML:    {html_dir}")
    print(f"         Existe: {'OUI' if os.path.exists(html_dir) else 'NON'}")
    print(f"\nMedia:   {media_dir}")
    print(f"         Existe: {'OUI' if os.path.exists(media_dir) else 'NON'}")
    print(f"\nSortie:  {output_dir}")
    print(f"         Existe: {'OUI' if os.path.exists(output_dir) else 'NON'}")
    print("="*60)

if __name__ == "__main__":
    main()
