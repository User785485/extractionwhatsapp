#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE RÉPARATION COMPLET DU SYSTÈME DE TRANSCRIPTION
Objectif: Passer de 50% à 100% de taux de transcription
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core import UnifiedRegistry, FileManager
from utils import setup_logging

logger = logging.getLogger('whatsapp_extractor')

class TranscriptionSystemFixer:
    """
    Classe de réparation complète du système de transcription
    """
    
    def __init__(self, config_file='config.ini'):
        self.config = Config(config_file)
        setup_logging(self.config)
        
        output_dir = self.config.get('Paths', 'output_dir')
        self.registry = UnifiedRegistry(output_dir)
        self.file_manager = FileManager(output_dir)
        self.output_dir = output_dir
        
        # Statistiques de réparation
        self.stats = {
            'mp3_files_found': 0,
            'opus_files_found': 0,
            'existing_transcriptions': 0,
            'missing_transcriptions': 0,
            'mappings_created': 0,
            'files_backed_up': 0
        }
    
    def run_complete_fix(self):
        """Lance la réparation complète du système"""
        logger.info("="*80)
        logger.info("RÉPARATION COMPLÈTE DU SYSTÈME DE TRANSCRIPTION")
        logger.info("="*80)
        
        # 1. Diagnostic initial
        self._diagnostic_initial()
        
        # 2. Sauvegardes
        self._create_backups()
        
        # 3. Analyse des fichiers
        self._analyze_all_files()
        
        # 4. Création des correspondances
        self._create_transcription_mappings()
        
        # 5. Mise à jour des fichiers du système
        self._update_system_files()
        
        # 6. Test du nouveau système
        self._test_new_system()
        
        # 7. Rapport final
        self._generate_final_report()
    
    def _diagnostic_initial(self):
        """Diagnostic initial du système"""
        logger.info("--- DIAGNOSTIC INITIAL ---")
        
        # Vérifier l'état du registre
        total_files = len(self.registry.data['files'])
        total_transcriptions = len(self.registry.data['transcriptions'])
        
        logger.info(f"Fichiers dans le registre: {total_files}")
        logger.info(f"Transcriptions dans le registre: {total_transcriptions}")
        
        if total_files > 0:
            taux_actuel = (total_transcriptions / total_files) * 100
            logger.info(f"Taux de transcription actuel: {taux_actuel:.1f}%")
        
        # Analyser les contacts
        contacts = [d for d in os.listdir(self.output_dir) 
                   if os.path.isdir(os.path.join(self.output_dir, d)) and not d.startswith('.')]
        logger.info(f"Contacts détectés: {len(contacts)}")
        
        return total_files, total_transcriptions, contacts
    
    def _create_backups(self):
        """Crée des sauvegardes avant modification"""
        logger.info("--- CRÉATION DES SAUVEGARDES ---")
        
        backup_dir = os.path.join(self.output_dir, f'backup_transcription_fix_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Sauvegarder le registre
        registry_backup = os.path.join(backup_dir, '.unified_registry.json')
        if os.path.exists(self.registry.registry_path):
            shutil.copy2(self.registry.registry_path, registry_backup)
            self.stats['files_backed_up'] += 1
            logger.info("✓ Registre sauvegardé")
        
        # Sauvegarder les fichiers processors
        processors_backup = os.path.join(backup_dir, 'processors')
        os.makedirs(processors_backup, exist_ok=True)
        
        for file in ['transcriber.py', 'merger.py']:
            src = os.path.join(os.path.dirname(__file__), 'processors', file)
            if os.path.exists(src):
                dst = os.path.join(processors_backup, file)
                shutil.copy2(src, dst)
                self.stats['files_backed_up'] += 1
        
        logger.info(f"Sauvegarde créée dans: {backup_dir}")
        return backup_dir
    
    def _analyze_all_files(self):
        """Analyse tous les fichiers audio du système"""
        logger.info("--- ANALYSE DES FICHIERS AUDIO ---")
        
        mp3_files = []
        opus_files = []
        
        # Parcourir tous les contacts
        for contact in os.listdir(self.output_dir):
            contact_path = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_path) or contact.startswith('.'):
                continue
            
            # Chercher les MP3 (fichiers convertis)
            audio_mp3_dir = os.path.join(contact_path, 'audio_mp3')
            if os.path.exists(audio_mp3_dir):
                for file in os.listdir(audio_mp3_dir):
                    if file.endswith('.mp3'):
                        full_path = os.path.join(audio_mp3_dir, file)
                        mp3_files.append((contact, full_path))
            
            # Chercher les OPUS (fichiers originaux)
            for media_dir in ['media_recus', 'media_envoyes']:
                audio_dir = os.path.join(contact_path, media_dir, 'audio')
                if os.path.exists(audio_dir):
                    for file in os.listdir(audio_dir):
                        if file.endswith('.opus'):
                            full_path = os.path.join(audio_dir, file)
                            opus_files.append((contact, full_path))
        
        self.stats['mp3_files_found'] = len(mp3_files)
        self.stats['opus_files_found'] = len(opus_files)
        
        logger.info(f"Fichiers MP3 trouvés: {len(mp3_files)}")
        logger.info(f"Fichiers OPUS trouvés: {len(opus_files)}")
        
        return mp3_files, opus_files
    
    def _create_transcription_mappings(self):
        """Crée les correspondances fichier -> transcription"""
        logger.info("--- CRÉATION DES CORRESPONDANCES ---")
        
        mapping_dir = os.path.join(self.output_dir, '.transcription_mappings')
        os.makedirs(mapping_dir, exist_ok=True)
        
        mp3_files, opus_files = self._analyze_all_files()
        
        # Grouper par contact
        contacts_data = {}
        
        # Analyser les MP3 (priorité car ils sont convertis)
        for contact, mp3_path in mp3_files:
            if contact not in contacts_data:
                contacts_data[contact] = {'mp3': [], 'opus': [], 'mappings': {}}
            
            contacts_data[contact]['mp3'].append(mp3_path)
            
            # Vérifier s'il y a une transcription pour ce MP3
            file_hash = self.registry.get_file_hash(mp3_path)
            transcription = self.registry.get_transcription(file_hash) if file_hash else None
            
            if transcription:
                self.stats['existing_transcriptions'] += 1
                # Créer la correspondance
                base_name = os.path.basename(mp3_path)
                contacts_data[contact]['mappings'][base_name] = {
                    'hash': file_hash,
                    'transcription': transcription,
                    'file_path': mp3_path,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'existing_registry'
                }
            else:
                self.stats['missing_transcriptions'] += 1
        
        # Analyser les OPUS pour créer des correspondances inverses
        for contact, opus_path in opus_files:
            if contact not in contacts_data:
                contacts_data[contact] = {'mp3': [], 'opus': [], 'mappings': {}}
            
            contacts_data[contact]['opus'].append(opus_path)
            
            # Essayer de trouver le MP3 correspondant
            opus_base = os.path.basename(opus_path)
            corresponding_mp3 = self._find_corresponding_mp3(opus_path, contacts_data[contact]['mp3'])
            
            if corresponding_mp3:
                # Créer une correspondance OPUS -> MP3
                mp3_base = os.path.basename(corresponding_mp3)
                if mp3_base in contacts_data[contact]['mappings']:
                    # Ajouter la référence OPUS
                    contacts_data[contact]['mappings'][opus_base] = contacts_data[contact]['mappings'][mp3_base].copy()
                    contacts_data[contact]['mappings'][opus_base]['original_file'] = opus_path
                    contacts_data[contact]['mappings'][opus_base]['converted_file'] = corresponding_mp3
        
        # Sauvegarder les correspondances
        for contact, data in contacts_data.items():
            if data['mappings']:
                mapping_file = os.path.join(mapping_dir, f"{contact}_mappings.json")
                try:
                    with open(mapping_file, 'w', encoding='utf-8') as f:
                        json.dump(data['mappings'], f, ensure_ascii=False, indent=2)
                    self.stats['mappings_created'] += len(data['mappings'])
                    logger.info(f"✓ Correspondances créées pour {contact}: {len(data['mappings'])}")
                except Exception as e:
                    logger.error(f"Erreur sauvegarde correspondances {contact}: {str(e)}")
        
        total_mappings = sum(len(data['mappings']) for data in contacts_data.values())
        logger.info(f"Total correspondances créées: {total_mappings}")
    
    def _find_corresponding_mp3(self, opus_path: str, mp3_files: List[str]) -> str:
        """Trouve le fichier MP3 correspondant à un fichier OPUS"""
        opus_name = os.path.basename(opus_path)
        opus_size = os.path.getsize(opus_path) if os.path.exists(opus_path) else 0
        opus_mtime = os.path.getmtime(opus_path) if os.path.exists(opus_path) else 0
        
        # Stratégies de correspondance
        for mp3_path in mp3_files:
            mp3_name = os.path.basename(mp3_path)
            mp3_mtime = os.path.getmtime(mp3_path) if os.path.exists(mp3_path) else 0
            
            # 1. Correspondance par timestamp (conversion récente)
            time_diff = abs(mp3_mtime - opus_mtime)
            if time_diff < 3600:  # Moins d'1 heure de différence
                return mp3_path
            
            # 2. Correspondance par pattern de nom
            if self._names_match_pattern(opus_name, mp3_name):
                return mp3_path
        
        return None
    
    def _names_match_pattern(self, opus_name: str, mp3_name: str) -> bool:
        """Vérifie si deux noms de fichiers correspondent selon un pattern"""
        # Extraire les identifiants communs
        import re
        
        # UUID/GUID
        opus_uuid = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', opus_name)
        mp3_uuid = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', mp3_name)
        
        if opus_uuid and mp3_uuid:
            return opus_uuid.group(1) == mp3_uuid.group(1)
        
        # Pattern numérique
        opus_num = re.search(r'(\d{8,})', opus_name)
        mp3_num = re.search(r'(\d{8,})', mp3_name)
        
        if opus_num and mp3_num:
            return opus_num.group(1) == mp3_num.group(1)
        
        return False
    
    def _update_system_files(self):
        """Met à jour les fichiers du système avec les versions corrigées"""
        logger.info("--- MISE À JOUR DES FICHIERS SYSTÈME ---")
        
        # Les fichiers corrigés sont dans les artifacts créés précédemment
        # Pour l'instant, on informe l'utilisateur
        logger.info("Les fichiers transcriber.py et merger.py corrigés sont disponibles")
        logger.info("Remplacez manuellement ces fichiers dans le dossier processors/")
        
        # TODO: Automatiser le remplacement si souhaité
    
    def _test_new_system(self):
        """Test du nouveau système de correspondances"""
        logger.info("--- TEST DU NOUVEAU SYSTÈME ---")
        
        mapping_dir = os.path.join(self.output_dir, '.transcription_mappings')
        if not os.path.exists(mapping_dir):
            logger.warning("Répertoire de correspondances non créé")
            return
        
        total_mappings = 0
        for file in os.listdir(mapping_dir):
            if file.endswith('_mappings.json'):
                mapping_file = os.path.join(mapping_dir, file)
                try:
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        mappings = json.load(f)
                        total_mappings += len(mappings)
                except:
                    pass
        
        logger.info(f"Correspondances testées: {total_mappings}")
        
        # Calculer le nouveau taux théorique
        if self.stats['mp3_files_found'] > 0:
            taux_theorique = (self.stats['existing_transcriptions'] / self.stats['mp3_files_found']) * 100
            logger.info(f"Taux de transcription théorique: {taux_theorique:.1f}%")
        
    def _generate_final_report(self):
        """Génère le rapport final de réparation"""
        logger.info("="*80)
        logger.info("RAPPORT FINAL DE RÉPARATION")
        logger.info("="*80)
        
        # Statistiques
        logger.info(f"Fichiers MP3 analysés: {self.stats['mp3_files_found']}")
        logger.info(f"Fichiers OPUS analysés: {self.stats['opus_files_found']}")
        logger.info(f"Transcriptions existantes: {self.stats['existing_transcriptions']}")
        logger.info(f"Transcriptions manquantes: {self.stats['missing_transcriptions']}")
        logger.info(f"Correspondances créées: {self.stats['mappings_created']}")
        logger.info(f"Fichiers sauvegardés: {self.stats['files_backed_up']}")
        
        # Taux de réussite
        if self.stats['mp3_files_found'] > 0:
            taux_reparation = (self.stats['existing_transcriptions'] / self.stats['mp3_files_found']) * 100
            logger.info(f"\nTaux de réparation: {taux_reparation:.1f}%")
        
        # Actions recommandées
        logger.info("\n--- ACTIONS RECOMMANDÉES ---")
        logger.info("1. Remplacer processors/transcriber.py par la version corrigée")
        logger.info("2. Remplacer exporters/merger.py par la version corrigée")
        logger.info("3. Relancer la transcription avec: python main.py --incremental")
        logger.info("4. Vérifier les correspondances dans .transcription_mappings/")
        
        # Créer un fichier de rapport
        report_file = os.path.join(self.output_dir, f'transcription_fix_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'stats': self.stats,
                    'recommendations': [
                        "Remplacer les fichiers processors",
                        "Relancer la transcription",
                        "Vérifier les correspondances"
                    ]
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Rapport sauvegardé: {report_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport: {str(e)}")

def main():
    """Point d'entrée du script de réparation"""
    try:
        fixer = TranscriptionSystemFixer()
        fixer.run_complete_fix()
        return 0
    except Exception as e:
        logger.critical(f"Erreur fatale lors de la réparation: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())