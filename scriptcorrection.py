#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour appliquer toutes les corrections au projet WhatsApp Extractor
"""

import os
import shutil
import re

def create_simple_exporter():
    """Crée le fichier simple_exporter.py"""
    
    simple_exporter_code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Exporter pour WhatsApp Extractor
Export simple : Contact | Messages reçus avec transcriptions
"""

import os
import csv
import logging
from typing import Dict, List, Optional
from datetime import datetime

from core import UnifiedRegistry, FileManager
from exporters.base_exporter import BaseExporter

logger = logging.getLogger('whatsapp_extractor')

class SimpleExporter(BaseExporter):
    """
    Exporteur simple qui génère uniquement :
    - 1 fichier CSV : Contact | Messages
    - 1 fichier TXT : même format
    
    Inclut automatiquement les transcriptions des audios
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        super().__init__(config, registry, file_manager)
        
    def export(self, conversations: Dict[str, List[Dict]], **kwargs) -> bool:
        """Interface requise par BaseExporter"""
        return self.export_simple(conversations)
    
    def export_simple(self, conversations: Dict[str, List[Dict]]) -> bool:
        """
        Export simple : génère CSV et TXT avec Contact | Messages reçus
        """
        logger.info("="*60)
        logger.info("EXPORT SIMPLE - DÉBUT")
        logger.info("="*60)
        
        try:
            # Collecter les données
            output_data = self._collect_messages_with_transcriptions(conversations)
            
            if not output_data:
                logger.warning("Aucune donnée à exporter")
                return False
            
            # Générer les fichiers
            csv_success = self._write_csv_simple(output_data)
            txt_success = self._write_txt_simple(output_data)
            
            if csv_success and txt_success:
                logger.info("✅ Export simple terminé avec succès!")
                return True
            else:
                logger.error("Erreur lors de l'export")
                return False
                
        except Exception as e:
            logger.error(f"Erreur fatale dans export simple: {str(e)}", exc_info=True)
            return False
    
    def _collect_messages_with_transcriptions(self, conversations: Dict[str, List[Dict]]) -> Dict[str, str]:
        """Collecte tous les messages reçus avec leurs transcriptions"""
        logger.info("Collecte des messages et transcriptions...")
        output_data = {}
        
        total_contacts = 0
        total_messages = 0
        total_audios = 0
        total_transcribed = 0
        
        for contact, messages in conversations.items():
            contact_content = []
            
            # Filtrer et traiter seulement les messages reçus
            for msg in messages:
                if msg.get('direction') != 'received':
                    continue
                
                total_messages += 1
                
                if msg.get('type') == 'text':
                    # Message texte simple
                    content = msg.get('content', '').strip()
                    if content:
                        contact_content.append(content)
                        
                elif msg.get('type') == 'audio':
                    total_audios += 1
                    # Message audio : chercher la transcription
                    transcription = self._get_audio_transcription(msg, contact)
                    
                    if transcription:
                        contact_content.append(f"[AUDIO] {transcription}")
                        total_transcribed += 1
                    else:
                        # Pas de transcription disponible
                        contact_content.append("[AUDIO non transcrit]")
            
            # Joindre tous les messages du contact
            if contact_content:
                total_contacts += 1
                # Joindre avec un espace
                output_data[contact] = " ".join(contact_content)
        
        # Statistiques
        logger.info(f"Collecte terminée:")
        logger.info(f"  - Contacts avec messages reçus: {total_contacts}")
        logger.info(f"  - Total messages reçus: {total_messages}")
        logger.info(f"  - Total audios: {total_audios}")
        logger.info(f"  - Audios transcrits: {total_transcribed}")
        
        if total_audios > 0:
            transcription_rate = (total_transcribed / total_audios) * 100
            logger.info(f"  - Taux de transcription: {transcription_rate:.1f}%")
        
        return output_data
    
    def _get_audio_transcription(self, message: Dict, contact: str) -> Optional[str]:
        """Récupère la transcription d'un message audio"""
        media_path = message.get('media_path')
        if not media_path:
            return None
        
        # Chercher par hash du fichier
        try:
            file_hash = self.registry.get_file_hash(media_path)
            if file_hash:
                # Chercher dans les transcriptions
                trans_data = self.registry.data.get('transcriptions', {}).get(file_hash)
                if trans_data and trans_data.get('text'):
                    return trans_data['text'].strip()
                
                # Chercher si c'est un fichier converti (OPUS -> MP3)
                file_info = self.registry.data.get('files', {}).get(file_hash)
                if file_info and file_info.get('converted_path'):
                    # Chercher le hash du MP3
                    mp3_hash = self.registry.get_file_hash(file_info['converted_path'])
                    if mp3_hash:
                        trans_data = self.registry.data.get('transcriptions', {}).get(mp3_hash)
                        if trans_data and trans_data.get('text'):
                            return trans_data['text'].strip()
        except Exception as e:
            logger.debug(f"Erreur recherche transcription: {e}")
        
        return None
    
    def _write_csv_simple(self, output_data: Dict[str, str]) -> bool:
        """Écrit le fichier CSV simple"""
        csv_path = os.path.join(self.output_dir, 'export_simple.csv')
        
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # En-tête
                writer.writerow(['Contact/Identifiant', 'Messages reçus et transcriptions'])
                
                # Données triées par contact
                for contact, content in sorted(output_data.items()):
                    writer.writerow([contact, content])
            
            logger.info(f"✓ CSV créé: {csv_path}")
            logger.info(f"  - Nombre de contacts: {len(output_data)}")
            
            # Créer aussi version Excel si possible
            try:
                import pandas as pd
                df = pd.read_csv(csv_path, encoding='utf-8')
                excel_path = csv_path.replace('.csv', '.xlsx')
                
                with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Messages')
                    
                    # Ajuster la largeur des colonnes
                    worksheet = writer.sheets['Messages']
                    worksheet.column_dimensions['A'].width = 30
                    worksheet.column_dimensions['B'].width = 100
                
                logger.info(f"✓ Excel créé aussi: {excel_path}")
            except:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur écriture CSV: {str(e)}")
            return False
    
    def _write_txt_simple(self, output_data: Dict[str, str]) -> bool:
        """Écrit le fichier TXT simple"""
        txt_path = os.path.join(self.output_dir, 'export_simple.txt')
        
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                # En-tête
                f.write("EXPORT SIMPLE - MESSAGES REÇUS AVEC TRANSCRIPTIONS\\n")
                f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                f.write(f"Nombre de contacts: {len(output_data)}\\n")
                f.write("="*60 + "\\n\\n")
                
                # Données
                for contact, content in sorted(output_data.items()):
                    f.write(f"{contact}:\\n")
                    f.write(f"{content}\\n")
                    f.write("\\n" + "-"*60 + "\\n\\n")
                
                # Résumé
                f.write("\\n" + "="*60 + "\\n")
                f.write(f"TOTAL: {len(output_data)} contacts avec messages reçus\\n")
            
            logger.info(f"✓ TXT créé: {txt_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur écriture TXT: {str(e)}")
            return False
'''
    
    # Créer le fichier
    output_path = os.path.join('exporters', 'simple_exporter.py')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(simple_exporter_code)
    
    print(f"[OK] Créé: {output_path}")

def fix_csv_exporter():
    """Corrige le bug dans csv_exporter.py"""
    csv_path = os.path.join('exporters', 'csv_exporter.py')
    
    if not os.path.exists(csv_path):
        print(f"[ERREUR] {csv_path} non trouvé")
        return
    
    # Lire le fichier
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher et corriger le bug de double vérification
    # Pattern pour trouver la double vérification
    pattern = r'(if not os\.path\.exists\(source_file\):.*?return)\s*if not os\.path\.exists\(source_file\):.*?return'
    
    # Remplacer par une seule vérification
    replacement = r'\1'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if new_content != content:
        # Écrire le fichier corrigé
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("[OK] Bug corrigé dans csv_exporter.py")
    else:
        print("[INFO] Bug déjà corrigé ou non trouvé dans csv_exporter.py")

def update_main_py():
    """Met à jour main.py pour ajouter l'option --simple-export"""
    main_path = 'main.py'
    
    if not os.path.exists(main_path):
        print(f"[ERREUR] {main_path} non trouvé")
        return
    
    # Lire le fichier
    with open(main_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Ajouter l'import si pas déjà présent
    if 'from exporters import SimpleExporter' not in content:
        # Ajouter après les autres imports d'exporters
        import_pattern = r'(from exporters import.*?FocusedCSVExporter)'
        replacement = r'\1, SimpleExporter'
        content = re.sub(import_pattern, replacement, content)
        print("[OK] Import SimpleExporter ajouté")
    
    # 2. Ajouter l'argument --simple-export si pas déjà présent
    if '--simple-export' not in content:
        # Ajouter après --limit
        arg_pattern = r"(parser\.add_argument\('--limit'.*?\))"
        replacement = r"\1\n    parser.add_argument('--simple-export', action='store_true', help='Export simple (CSV et TXT avec 2 colonnes seulement)')"
        content = re.sub(arg_pattern, replacement, content, flags=re.DOTALL)
        print("[OK] Argument --simple-export ajouté")
    
    # 3. Modifier la phase d'export pour ajouter le mode simple
    if 'args.simple_export' not in content:
        # Pattern pour trouver la phase d'export
        export_pattern = r'(# Phase 5: Export.*?logger\.info\("=".*?\))\s*\n\s*(# ORDRE CORRIGÉ.*?)'
        
        replacement = r'''\1
    
    # Mode export simple (NOUVEAU)
    if args.simple_export:
        logger.info("Mode export SIMPLE activé")
        simple_exporter = SimpleExporter(config, registry, file_manager)
        success = simple_exporter.export_simple(conversations)
        
        if success:
            logger.info("Export simple terminé avec succès!")
            # Afficher les fichiers créés
            for filename in ['export_simple.csv', 'export_simple.txt', 'export_simple.xlsx']:
                filepath = os.path.join(output_dir, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    logger.info(f"  - {filename}: {format_size(size)}")
        else:
            logger.error("Erreur lors de l'export simple")
    
    # Mode export standard (ANCIEN)
    else:
        \2'''
        
        content = re.sub(export_pattern, replacement, content, flags=re.DOTALL)
        print("[OK] Mode export simple ajouté dans main.py")
    
    # Écrire le fichier modifié
    with open(main_path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_exporters_init():
    """Met à jour __init__.py des exporters"""
    init_path = os.path.join('exporters', '__init__.py')
    
    if not os.path.exists(init_path):
        print(f"[ERREUR] {init_path} non trouvé")
        return
    
    # Lire le fichier
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ajouter l'import si pas déjà présent
    if 'SimpleExporter' not in content:
        # Ajouter à la fin
        content = content.rstrip() + '\nfrom .simple_exporter import SimpleExporter\n'
        
        # Écrire le fichier
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] SimpleExporter ajouté dans __init__.py")

def main():
    """Applique toutes les corrections"""
    print("="*60)
    print("APPLICATION DES CORRECTIONS WHATSAPP EXTRACTOR")
    print("="*60)
    print()
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('main.py'):
        print("[ERREUR] Ce script doit être exécuté depuis la racine du projet")
        print("[INFO] Placez ce script dans le dossier contenant main.py")
        return
    
    # 1. Créer SimpleExporter
    print("[1/4] Création de SimpleExporter...")
    create_simple_exporter()
    
    # 2. Corriger bug CSV
    print("\n[2/4] Correction du bug dans csv_exporter.py...")
    fix_csv_exporter()
    
    # 3. Mettre à jour main.py
    print("\n[3/4] Mise à jour de main.py...")
    update_main_py()
    
    # 4. Mettre à jour __init__.py
    print("\n[4/4] Mise à jour de exporters/__init__.py...")
    update_exporters_init()
    
    print("\n" + "="*60)
    print("CORRECTIONS APPLIQUÉES AVEC SUCCÈS!")
    print("="*60)
    print("\nPour tester:")
    print("  python main.py --simple-export --no-transcription --limit 5")
    print("\nPour un export complet:")
    print("  python main.py --simple-export")
    print("\nLes fichiers générés seront:")
    print("  - export_simple.csv")
    print("  - export_simple.txt")
    print("  - export_simple.xlsx (si pandas est installé)")

if __name__ == "__main__":
    main()