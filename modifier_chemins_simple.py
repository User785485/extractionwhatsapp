#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour modifier les chemins des fichiers HTML et média (version simple)
"""

import os
import sys
import configparser
import argparse
import shutil

def main():
    """Fonction principale"""
    # Créer le parser d'arguments
    parser = argparse.ArgumentParser(description='Modifier les chemins de WhatsApp Extractor')
    parser.add_argument('--html', help='Nouveau chemin pour les fichiers HTML')
    parser.add_argument('--media', help='Nouveau chemin pour les fichiers média')
    parser.add_argument('--output', help='Nouveau chemin pour les fichiers de sortie')
    parser.add_argument('--show', action='store_true', help='Afficher seulement les chemins actuels')
    
    # Parser les arguments
    args = parser.parse_args()
    
    # Chemins du fichier de configuration
    config_file = 'config.ini'
    backup_file = 'config.ini.bak'
    
    # Vérifier si le fichier existe
    if not os.path.exists(config_file):
        print(f"Erreur: Le fichier {config_file} n'existe pas.")
        sys.exit(1)
    
    # Sauvegarder le fichier de configuration avant toute modification
    shutil.copy2(config_file, backup_file)
    print(f"Sauvegarde du fichier de configuration dans {backup_file}")
    
    # Charger la configuration
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file, encoding='utf-8')
    
    # Vérifier les sections
    if config.has_section('Paths'):
        section = 'Paths'
    elif config.has_section('PATHS'):
        section = 'PATHS'
    else:
        # Créer la section si elle n'existe pas
        section = 'Paths'
        config.add_section(section)
        print("Section 'Paths' créée dans le fichier de configuration.")
    
    # Récupérer les chemins actuels
    html_dir = config.get(section, 'html_dir', fallback='')
    media_dir = config.get(section, 'media_dir', fallback='')
    output_dir = config.get(section, 'output_dir', fallback='')
    
    # Afficher les chemins actuels
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
    
    # Si l'option --show est spécifiée, on s'arrête ici
    if args.show:
        sys.exit(0)
    
    # Mettre à jour les chemins si spécifiés
    changes_made = False
    
    if args.html:
        print(f"\nModification du chemin HTML:")
        print(f"  Ancien: {html_dir}")
        print(f"  Nouveau: {args.html}")
        print(f"  Existe: {'OUI' if os.path.exists(args.html) else 'NON'}")
        config.set(section, 'html_dir', args.html)
        changes_made = True
    
    if args.media:
        print(f"\nModification du chemin Media:")
        print(f"  Ancien: {media_dir}")
        print(f"  Nouveau: {args.media}")
        print(f"  Existe: {'OUI' if os.path.exists(args.media) else 'NON'}")
        config.set(section, 'media_dir', args.media)
        changes_made = True
    
    if args.output:
        print(f"\nModification du chemin de Sortie:")
        print(f"  Ancien: {output_dir}")
        print(f"  Nouveau: {args.output}")
        print(f"  Existe: {'OUI' if os.path.exists(args.output) else 'NON'}")
        
        # Créer le répertoire de sortie s'il n'existe pas
        if not os.path.exists(args.output):
            try:
                os.makedirs(args.output)
                print(f"  Répertoire créé: {args.output}")
            except Exception as e:
                print(f"  Erreur lors de la création du répertoire: {str(e)}")
        
        config.set(section, 'output_dir', args.output)
        changes_made = True
    
    # Sauvegarder les modifications si nécessaire
    if changes_made:
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            print("\n[SUCCÈS] Configuration sauvegardée avec succès!")
            print("Pour appliquer les changements, relancez le programme principal.")
        except Exception as e:
            print(f"\n[ERREUR] Erreur lors de la sauvegarde de la configuration: {str(e)}")
            print(f"La sauvegarde est disponible dans {backup_file}")
    else:
        print("\nAucun changement demandé. Configuration inchangée.")

if __name__ == "__main__":
    main()
