#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de diagnostic pour analyser les problèmes d'export CSV
Ce script vérifie les fichiers d'entrée et de sortie, examine leur contenu
et aide à comprendre pourquoi le processus d'export peut échouer.
"""

import os
import sys
import re
import json
import logging
from datetime import datetime
import configparser

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("diagnostic")

class ExportDiagnostic:
    def __init__(self, output_dir=None):
        """Initialise le diagnostic avec le répertoire de sortie"""
        config = configparser.ConfigParser()
        
        try:
            config.read('config.ini')
            self.output_dir = config.get('Paths', 'output_dir')
        except Exception:
            # Fallback
            self.output_dir = output_dir or os.path.join(os.path.expanduser('~'), 'Desktop', 'DataLeads')
        
        logger.info(f"Répertoire analysé: {self.output_dir}")
        
    def run_diagnostic(self):
        """Exécute le diagnostic complet"""
        logger.info("===== DIAGNOSTIC DE L'EXPORT CSV =====")
        
        # 1. Vérifier l'existence des fichiers clés
        self.check_key_files()
        
        # 2. Analyser le contenu du fichier global
        self.analyze_global_file()
        
        # 3. Analyser un échantillon de fichiers de messages reçus
        self.analyze_received_files()
        
        # 4. Examiner le registre unifié
        self.analyze_registry()
        
        # 5. Diagnostiquer les problèmes spécifiques
        self.diagnose_issues()
        
        logger.info("===== FIN DU DIAGNOSTIC =====")
        
    def check_key_files(self):
        """Vérifie l'existence et la taille des fichiers clés"""
        logger.info("Vérification des fichiers clés...")
        
        key_files = [
            'all_conversations.txt',
            'toutes_conversations_avec_transcriptions.txt',
            'messages_recus.txt',
            'messages_recus_avec_transcriptions.txt',
            'messages_recus_only.csv',
            'messages_all.csv',
            'contacts_messages_simplifies.csv'
        ]
        
        for filename in key_files:
            filepath = os.path.join(self.output_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                logger.info(f"  - {filename}: {self._format_size(size)}")
                
                # Vérification si le fichier est vide ou suspect
                if size == 0:
                    logger.error(f"PROBLÈME: {filename} est vide!")
                elif size < 1000:
                    logger.warning(f"SUSPECT: {filename} est très petit ({size} octets)")
            else:
                logger.warning(f"  - {filename}: MANQUANT")
    
    def analyze_global_file(self):
        """Analyse le contenu du fichier global avec transcriptions"""
        logger.info("Analyse du fichier global avec transcriptions...")
        
        # Fichier principal
        global_file = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')
        
        if not os.path.exists(global_file):
            logger.error("Le fichier global n'existe pas!")
            return
            
        size = os.path.getsize(global_file)
        if size < 1000:
            # Afficher tout le contenu pour les petits fichiers
            try:
                with open(global_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.warning(f"Contenu du fichier global (taille suspecte: {size} octets):")
                logger.warning(f"--- DÉBUT ---\n{content}\n--- FIN ---")
                
                # Rechercher des marqueurs spécifiques
                if '[AUDIO]' in content:
                    logger.error("Des balises [AUDIO] n'ont pas été remplacées!")
                
            except Exception as e:
                logger.error(f"Erreur lecture fichier global: {str(e)}")
        else:
            # Compter les messages, contacts et transcriptions
            try:
                with open(global_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                contacts = re.findall(r'===== CONVERSATION: (.*?) =====', content)
                audio_tags = re.findall(r'\[AUDIO\]', content)
                transcriptions = re.findall(r'\[TRANSCRIPTION:\s*(.*?)\s*\]', content)
                
                logger.info(f"  - Contacts trouvés: {len(set(contacts))}")
                logger.info(f"  - Tags [AUDIO] restants: {len(audio_tags)}")
                logger.info(f"  - Transcriptions insérées: {len(transcriptions)}")
                
            except Exception as e:
                logger.error(f"Erreur analyse fichier global: {str(e)}")
    
    def analyze_received_files(self):
        """Analyse les fichiers de messages reçus"""
        logger.info("Analyse des fichiers de messages reçus...")
        
        # Fichier global des messages reçus
        received_file = os.path.join(self.output_dir, 'messages_recus_avec_transcriptions.txt')
        
        if not os.path.exists(received_file):
            logger.warning("Le fichier global des messages reçus n'existe pas!")
        else:
            size = os.path.getsize(received_file)
            logger.info(f"  - Taille du fichier messages_recus_avec_transcriptions.txt: {self._format_size(size)}")
            
            if size < 1000:
                # Afficher tout le contenu pour les petits fichiers
                try:
                    with open(received_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    logger.warning(f"Contenu du fichier des messages reçus (taille suspecte: {size} octets):")
                    logger.warning(f"--- DÉBUT ---\n{content}\n--- FIN ---")
                except Exception as e:
                    logger.error(f"Erreur lecture fichier messages reçus: {str(e)}")
        
        # Vérifier quelques fichiers de contact au hasard
        contact_dirs = [d for d in os.listdir(self.output_dir) if os.path.isdir(os.path.join(self.output_dir, d))]
        
        if not contact_dirs:
            logger.warning("Aucun dossier de contact trouvé!")
            return
            
        # Échantillon de contacts (max 5)
        sample = contact_dirs[:5]
        logger.info(f"Analyse de {len(sample)} dossiers de contacts (échantillon)...")
        
        for contact in sample:
            contact_path = os.path.join(self.output_dir, contact)
            received_file = os.path.join(contact_path, 'messages_recus_avec_transcriptions.txt')
            
            if os.path.exists(received_file):
                size = os.path.getsize(received_file)
                logger.info(f"  - {contact}: {self._format_size(size)}")
                
                # Vérifier la présence de transcriptions
                if size > 0:
                    try:
                        with open(received_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        transcriptions = re.findall(r'\[TRANSCRIPTION:\s*(.*?)\s*\]', content)
                        audio_tags = re.findall(r'\[AUDIO\]', content)
                        
                        if transcriptions:
                            logger.info(f"    - Transcriptions: {len(transcriptions)}")
                        if audio_tags:
                            logger.warning(f"    - Tags [AUDIO] non remplacés: {len(audio_tags)}")
                    except Exception as e:
                        logger.error(f"Erreur analyse {contact}: {str(e)}")
            else:
                logger.warning(f"  - {contact}: Pas de fichier avec transcriptions")
    
    def analyze_registry(self):
        """Examine le registre unifié pour vérifier les transcriptions"""
        logger.info("Analyse du registre unifié...")
        
        registry_file = os.path.join(self.output_dir, '.unified_registry.json')
        
        if not os.path.exists(registry_file):
            logger.error("Le registre unifié n'existe pas!")
            return
            
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
                
            # Compter les fichiers audio et les transcriptions
            audio_files = sum(1 for info in registry.get('files', {}).values() 
                             if info.get('type') == 'audio')
            transcriptions = len(registry.get('transcriptions', {}))
            
            logger.info(f"  - Fichiers audio: {audio_files}")
            logger.info(f"  - Transcriptions: {transcriptions}")
            
            # Éviter la division par zéro
            if audio_files > 0:
                taux = transcriptions / audio_files * 100
                logger.info(f"  - Taux de transcription: {taux:.1f}%")
            else:
                logger.info(f"  - Taux de transcription: N/A (pas de fichiers audio)")
            
            # Vérifier quelques exemples de transcriptions
            trans_sample = list(registry.get('transcriptions', {}).items())[:3]
            if trans_sample:
                logger.info("Exemples de transcriptions:")
                for hash_key, trans_data in trans_sample:
                    text = trans_data.get('text', '')
                    audio_path = trans_data.get('audio_path', '')
                    truncated_text = text[:50] + '...' if len(text) > 50 else text
                    logger.info(f"  - {os.path.basename(audio_path)}: {truncated_text}")
        
        except Exception as e:
            logger.error(f"Erreur analyse registre: {str(e)}")
    
    def diagnose_issues(self):
        """Diagnostique des problèmes spécifiques et propose des solutions"""
        logger.info("Diagnostic des problèmes potentiels...")
        
        # 1. Vérifier si le fichier global est vide ou trop petit
        global_file = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')
        if os.path.exists(global_file) and os.path.getsize(global_file) < 1000:
            logger.error("PROBLÈME: Le fichier global avec transcriptions est trop petit.")
            logger.error("SOLUTION: Vérifier la méthode _merge_global_file dans merger.py")
            logger.error("          Il peut y avoir un problème lors du remplacement des balises [AUDIO].")
            logger.error("          Exécuter avec --force-merger pour régénérer ce fichier.")
        
        # 2. Vérifier si les fichiers de messages reçus sont corrects
        received_file = os.path.join(self.output_dir, 'messages_recus_avec_transcriptions.txt')
        if not os.path.exists(received_file) or os.path.getsize(received_file) < 1000:
            logger.error("PROBLÈME: Le fichier des messages reçus avec transcriptions est manquant ou trop petit.")
            logger.error("SOLUTION: Vérifier la méthode _merge_received_files dans merger.py")
            logger.error("          Le fichier source 'messages_recus.txt' peut être manquant.")
            
        # 3. Vérifier si le problème vient du CSVExporter
        csv_file = os.path.join(self.output_dir, 'messages_recus_only.csv')
        if os.path.exists(csv_file) and os.path.getsize(csv_file) > 10000:
            logger.warning("Le fichier CSV semble OK en taille mais les exports rapportent 0 contacts/messages.")
            logger.warning("SOLUTION: Vérifier la méthode export_special_csv dans csv_exporter.py")
            logger.warning("          Il peut y avoir un problème de parsing du fichier source.")
            
        # 4. Vérifier notre nouvel export simplifié
        simplified_csv = os.path.join(self.output_dir, 'contacts_messages_simplifies.csv')
        if not os.path.exists(simplified_csv):
            logger.error("PROBLÈME: Notre nouvel export simplifié n'a pas été généré.")
            logger.error("SOLUTION: Vérifier que le PhoneNameCSVExporter est bien appelé dans main_enhanced.py")
            logger.error("          Modifier la méthode export_simplified_csv pour utiliser directement les conversations")
            logger.error("          au lieu de dépendre des fichiers fusionnés.")
        
    def _format_size(self, size):
        """Formate la taille d'un fichier"""
        if size < 1024:
            return f"{size} octets"
        elif size < 1024 * 1024:
            return f"{size/1024:.2f} KB"
        else:
            return f"{size/(1024*1024):.2f} MB"

if __name__ == "__main__":
    diagnostic = ExportDiagnostic()
    diagnostic.run_diagnostic()
    print("\nPour exécuter un fix automatique, lancez: python fix_export.py")
