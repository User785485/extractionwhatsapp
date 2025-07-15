#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour modifier les chemins des fichiers HTML et média
"""

import os
import sys
import logging
import configparser
from pathlib import Path

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('modifier_chemins')

def charger_config(config_file='config.ini'):
    """Charge la configuration depuis le fichier"""
    config = configparser.ConfigParser(interpolation=None)
    
    if os.path.exists(config_file):
        try:
            config.read(config_file, encoding='utf-8')
            logger.info(f"Configuration chargée depuis {config_file}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
            sys.exit(1)
    else:
        logger.error(f"Le fichier de configuration {config_file} n'existe pas")
        sys.exit(1)
    
    return config

def sauvegarder_config(config, config_file='config.ini'):
    """Sauvegarde la configuration dans le fichier"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        logger.info(f"Configuration sauvegardée dans {config_file}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
        return False

def verifier_chemin(chemin, type_chemin):
    """Vérifie si le chemin existe et est valide"""
    if not chemin:
        logger.warning(f"Le chemin {type_chemin} est vide")
        return False
    
    path = Path(chemin)
    
    if not path.exists():
        logger.warning(f"Le chemin {type_chemin} n'existe pas: {chemin}")
        return False
    
    if not path.is_dir():
        logger.warning(f"Le chemin {type_chemin} n'est pas un répertoire: {chemin}")
        return False
    
    logger.info(f"Le chemin {type_chemin} est valide: {chemin}")
    return True

def afficher_chemins_actuels(config):
    """Affiche les chemins actuels"""
    section = 'Paths' if config.has_section('Paths') else 'PATHS'
    
    if not config.has_section(section):
        logger.error("Aucune section de chemins trouvée dans la configuration")
        return
    
    html_dir = config.get(section, 'html_dir', fallback='Non défini')
    media_dir = config.get(section, 'media_dir', fallback='Non défini')
    output_dir = config.get(section, 'output_dir', fallback='Non défini')
    
    print("\n" + "="*60)
    print("CHEMINS ACTUELS")
    print("="*60)
    print(f"HTML:    {html_dir}")
    print(f"Media:   {media_dir}")
    print(f"Sortie:  {output_dir}")
    print("="*60)
    
    # Vérifier si les chemins existent
    html_valide = verifier_chemin(html_dir, "HTML") if html_dir != 'Non défini' else False
    media_valide = verifier_chemin(media_dir, "Media") if media_dir != 'Non défini' else False
    output_valide = verifier_chemin(output_dir, "Sortie") if output_dir != 'Non défini' else False
    
    print("\nValidation des chemins:")
    print(f"HTML:    {'[OK] Valide' if html_valide else '[X] Invalide ou inexistant'}")
    print(f"Media:   {'[OK] Valide' if media_valide else '[X] Invalide ou inexistant'}")
    print(f"Sortie:  {'[OK] Valide' if output_valide else '[X] Invalide ou inexistant'}")
    print("="*60)
    
    return {
        'html_dir': html_dir,
        'media_dir': media_dir,
        'output_dir': output_dir
    }

def demander_nouveaux_chemins(anciens_chemins):
    """Demande à l'utilisateur de nouveaux chemins"""
    print("\nEntrez les nouveaux chemins (laissez vide pour garder l'ancien):")
    
    html_dir = input(f"Dossier HTML [{anciens_chemins['html_dir']}]: ").strip()
    if not html_dir:
        html_dir = anciens_chemins['html_dir']
    
    media_dir = input(f"Dossier Media [{anciens_chemins['media_dir']}]: ").strip()
    if not media_dir:
        media_dir = anciens_chemins['media_dir']
    
    output_dir = input(f"Dossier Sortie [{anciens_chemins['output_dir']}]: ").strip()
    if not output_dir:
        output_dir = anciens_chemins['output_dir']
    
    return {
        'html_dir': html_dir,
        'media_dir': media_dir,
        'output_dir': output_dir
    }

def verifier_et_mettre_a_jour_chemins(config, nouveaux_chemins):
    """Vérifie et met à jour les chemins dans la configuration"""
    print("\nVérification des nouveaux chemins...")
    
    # Vérification des chemins
    html_valide = verifier_chemin(nouveaux_chemins['html_dir'], "HTML")
    media_valide = verifier_chemin(nouveaux_chemins['media_dir'], "Media")
    output_valide = verifier_chemin(nouveaux_chemins['output_dir'], "Sortie")
    
    # Validation globale
    if not html_valide:
        print("ATTENTION: Le dossier HTML n'est pas valide!")
        confirmer = input("Voulez-vous continuer quand même? (o/n): ").strip().lower()
        if confirmer != 'o':
            return False
    
    if not media_valide:
        print("ATTENTION: Le dossier Media n'est pas valide!")
        confirmer = input("Voulez-vous continuer quand même? (o/n): ").strip().lower()
        if confirmer != 'o':
            return False
    
    if not output_valide:
        print("ATTENTION: Le dossier de sortie n'est pas valide!")
        print("Création du dossier de sortie...")
        try:
            os.makedirs(nouveaux_chemins['output_dir'], exist_ok=True)
        except Exception as e:
            print(f"Erreur lors de la création du dossier de sortie: {str(e)}")
            return False
    
    # Mettre à jour la configuration
    section = 'Paths' if config.has_section('Paths') else 'PATHS'
    
    if not config.has_section(section):
        config.add_section(section)
    
    config.set(section, 'html_dir', nouveaux_chemins['html_dir'])
    config.set(section, 'media_dir', nouveaux_chemins['media_dir'])
    config.set(section, 'output_dir', nouveaux_chemins['output_dir'])
    
    print("\n" + "="*60)
    print("NOUVEAUX CHEMINS À ENREGISTRER")
    print("="*60)
    print(f"HTML:    {nouveaux_chemins['html_dir']}")
    print(f"Media:   {nouveaux_chemins['media_dir']}")
    print(f"Sortie:  {nouveaux_chemins['output_dir']}")
    print("="*60)
    
    confirmer = input("\nConfirmez-vous ces modifications? (o/n): ").strip().lower()
    return confirmer == 'o'

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("OUTIL DE MODIFICATION DES CHEMINS WHATSAPP EXTRACTOR")
    print("="*60)
    
    # Chemin du fichier de configuration
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
    
    # Charger la configuration
    config = charger_config(config_file)
    
    # Afficher les chemins actuels
    anciens_chemins = afficher_chemins_actuels(config)
    
    # Demander les nouveaux chemins
    nouveaux_chemins = demander_nouveaux_chemins(anciens_chemins)
    
    # Vérifier et mettre à jour les chemins
    if verifier_et_mettre_a_jour_chemins(config, nouveaux_chemins):
        # Sauvegarder la configuration
        if sauvegarder_config(config, config_file):
            print("\n[SUCCÈS] Les modifications ont été sauvegardées avec succès!")
            print("Pour appliquer les changements, relancez le programme principal.")
        else:
            print("\n[ERREUR] Erreur lors de la sauvegarde des modifications.")
    else:
        print("\n[ANNULÉ] Les modifications n'ont pas été sauvegardées.")
    
    print("\nAppuyez sur une touche pour quitter...")
    input()

if __name__ == "__main__":
    main()
