#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Diagnostic Complet pour Export WhatsApp
Analyse en profondeur pourquoi certains contacts ont des données manquantes
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set
import csv
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('diagnostic_export_deep.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ExportDiagnostic:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.issues = []
        self.stats = {
            'total_contacts': 0,
            'contacts_with_html': 0,
            'contacts_with_json': 0,
            'contacts_with_transcriptions': 0,
            'contacts_with_text_messages': 0,
            'contacts_with_audio_messages': 0,
            'contacts_missing_in_export': 0
        }
        
    def run_diagnostic(self):
        """Lance le diagnostic complet"""
        logger.info("="*80)
        logger.info("DIAGNOSTIC COMPLET DE L'EXPORT WHATSAPP")
        logger.info("="*80)
        
        # 1. Analyser tous les contacts
        all_contacts = self.scan_all_contacts()
        
        # 2. Analyser les données de chaque contact
        contact_analysis = {}
        for contact in all_contacts:
            logger.info(f"\nAnalyse de {contact}...")
            contact_analysis[contact] = self.analyze_contact(contact)
            
        # 3. Charger l'export actuel
        export_data = self.load_current_export()
        
        # 4. Comparer et identifier les problèmes
        self.compare_with_export(contact_analysis, export_data)
        
        # 5. Générer le rapport
        self.generate_report(contact_analysis, export_data)
        
    def scan_all_contacts(self) -> Set[str]:
        """Scanne tous les dossiers de contacts"""
        contacts = set()
        
        for item in self.output_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                contacts.add(item.name)
                self.stats['total_contacts'] += 1
                
        logger.info(f"Contacts trouvés: {len(contacts)}")
        return contacts
        
    def analyze_contact(self, contact: str) -> Dict:
        """Analyse complète d'un contact"""
        contact_dir = self.output_dir / contact
        analysis = {
            'name': contact,
            'has_conversation_json': False,
            'has_transcriptions': False,
            'text_messages_received': [],
            'audio_messages_received': [],
            'all_messages': [],
            'transcription_files': [],
            'issues': []
        }
        
        # 1. Vérifier conversation.json
        json_file = contact_dir / "conversation.json"
        if json_file.exists():
            analysis['has_conversation_json'] = True
            self.stats['contacts_with_json'] += 1
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                    
                for msg in messages:
                    if msg.get('direction') == 'received':
                        if msg.get('type') == 'text':
                            content = msg.get('content', '').strip()
                            if content:
                                analysis['text_messages_received'].append({
                                    'date': msg.get('date'),
                                    'time': msg.get('time'),
                                    'content': content
                                })
                        elif msg.get('type') == 'audio':
                            analysis['audio_messages_received'].append({
                                'date': msg.get('date'),
                                'time': msg.get('time'),
                                'file': msg.get('content', ''),
                                'media_path': msg.get('media_path', '')
                            })
                    
                    analysis['all_messages'].append(msg)
                    
            except Exception as e:
                analysis['issues'].append(f"Erreur lecture JSON: {str(e)}")
                logger.error(f"Erreur JSON pour {contact}: {e}")
        else:
            analysis['issues'].append("Pas de conversation.json")
            
        # 2. Vérifier les transcriptions
        trans_dir = contact_dir / "transcriptions"
        if trans_dir.exists():
            txt_files = list(trans_dir.glob("*.txt"))
            if txt_files:
                analysis['has_transcriptions'] = True
                self.stats['contacts_with_transcriptions'] += 1
                
                for txt_file in txt_files:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extraire la transcription
                        lines = content.split('\n')
                        if len(lines) > 5:
                            transcription = '\n'.join(lines[5:]).strip()
                            if transcription:
                                analysis['transcription_files'].append({
                                    'file': txt_file.name,
                                    'content': transcription[:100] + "..." if len(transcription) > 100 else transcription
                                })
                    except Exception as e:
                        analysis['issues'].append(f"Erreur lecture transcription {txt_file.name}: {str(e)}")
                        
        # Statistiques
        if analysis['text_messages_received']:
            self.stats['contacts_with_text_messages'] += 1
        if analysis['audio_messages_received']:
            self.stats['contacts_with_audio_messages'] += 1
            
        return analysis
        
    def load_current_export(self) -> Dict[str, str]:
        """Charge l'export actuel"""
        export_data = {}
        
        # Essayer CSV
        csv_path = self.output_dir / "export_simple.csv"
        if csv_path.exists():
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        contact = row.get('Contact/Identifiant', '')
                        content = row.get('Messages reçus et transcriptions', '')
                        if contact:
                            export_data[contact] = content
                logger.info(f"Export CSV chargé: {len(export_data)} contacts")
            except Exception as e:
                logger.error(f"Erreur lecture CSV: {e}")
                
        # Sinon essayer TXT
        if not export_data:
            txt_path = self.output_dir / "export_simple.txt"
            if txt_path.exists():
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Parser le TXT (format simple)
                    lines = content.split('\n')
                    current_contact = None
                    for line in lines:
                        if line and not line.startswith(' ') and ':' in line:
                            current_contact = line.rstrip(':')
                        elif current_contact and line.strip():
                            export_data[current_contact] = line.strip()
                except Exception as e:
                    logger.error(f"Erreur lecture TXT: {e}")
                    
        return export_data
        
    def compare_with_export(self, contact_analysis: Dict, export_data: Dict):
        """Compare l'analyse avec l'export actuel"""
        logger.info("\n" + "="*60)
        logger.info("COMPARAISON AVEC L'EXPORT")
        logger.info("="*60)
        
        for contact, analysis in contact_analysis.items():
            export_content = export_data.get(contact, "NON TROUVÉ DANS L'EXPORT")
            
            # Vérifier si le contact a des données mais n'est pas dans l'export
            has_data = (analysis['text_messages_received'] or 
                       analysis['audio_messages_received'] or 
                       analysis['has_transcriptions'])
            
            if has_data and (contact not in export_data or export_content == "[Aucun message reçu]"):
                self.stats['contacts_missing_in_export'] += 1
                
                logger.warning(f"\n⚠️ PROBLÈME DÉTECTÉ pour {contact}:")
                logger.warning(f"  - Messages texte reçus: {len(analysis['text_messages_received'])}")
                logger.warning(f"  - Messages audio reçus: {len(analysis['audio_messages_received'])}")
                logger.warning(f"  - Transcriptions: {len(analysis['transcription_files'])}")
                logger.warning(f"  - Dans l'export: {export_content}")
                
                # Afficher les messages texte manquants
                if analysis['text_messages_received']:
                    logger.warning("  - Textes reçus NON exportés:")
                    for msg in analysis['text_messages_received']:
                        logger.warning(f"    * {msg['date']} {msg['time']}: {msg['content'][:50]}...")
                        
    def generate_report(self, contact_analysis: Dict, export_data: Dict):
        """Génère un rapport détaillé"""
        report_path = self.output_dir / f"diagnostic_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RAPPORT DE DIAGNOSTIC EXPORT WHATSAPP\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Statistiques globales
            f.write("STATISTIQUES GLOBALES:\n")
            f.write(f"- Total contacts scannés: {self.stats['total_contacts']}\n")
            f.write(f"- Contacts avec conversation.json: {self.stats['contacts_with_json']}\n")
            f.write(f"- Contacts avec transcriptions: {self.stats['contacts_with_transcriptions']}\n")
            f.write(f"- Contacts avec messages texte: {self.stats['contacts_with_text_messages']}\n")
            f.write(f"- Contacts avec messages audio: {self.stats['contacts_with_audio_messages']}\n")
            f.write(f"- Contacts dans l'export: {len(export_data)}\n")
            f.write(f"- CONTACTS AVEC DONNÉES MANQUANTES: {self.stats['contacts_missing_in_export']}\n")
            f.write("\n" + "="*80 + "\n\n")
            
            # Détails des problèmes
            f.write("CONTACTS PROBLÉMATIQUES:\n\n")
            
            for contact, analysis in sorted(contact_analysis.items()):
                export_content = export_data.get(contact, "NON TROUVÉ")
                has_data = (analysis['text_messages_received'] or 
                           analysis['audio_messages_received'] or 
                           analysis['has_transcriptions'])
                
                if has_data and (contact not in export_data or export_content == "[Aucun message reçu]"):
                    f.write(f"{'='*60}\n")
                    f.write(f"CONTACT: {contact}\n")
                    f.write(f"{'='*60}\n")
                    
                    f.write(f"STATUT EXPORT: {export_content}\n\n")
                    
                    f.write("DONNÉES TROUVÉES:\n")
                    f.write(f"- conversation.json: {'OUI' if analysis['has_conversation_json'] else 'NON'}\n")
                    f.write(f"- Dossier transcriptions: {'OUI' if analysis['has_transcriptions'] else 'NON'}\n")
                    f.write(f"- Messages texte reçus: {len(analysis['text_messages_received'])}\n")
                    f.write(f"- Messages audio reçus: {len(analysis['audio_messages_received'])}\n")
                    f.write(f"- Fichiers transcription: {len(analysis['transcription_files'])}\n\n")
                    
                    if analysis['text_messages_received']:
                        f.write("MESSAGES TEXTE REÇUS (NON EXPORTÉS):\n")
                        for msg in analysis['text_messages_received']:
                            f.write(f"  [{msg['date']} {msg['time']}] {msg['content']}\n")
                        f.write("\n")
                    
                    if analysis['audio_messages_received']:
                        f.write("MESSAGES AUDIO REÇUS:\n")
                        for msg in analysis['audio_messages_received']:
                            f.write(f"  [{msg['date']} {msg['time']}] {msg['file']}\n")
                        f.write("\n")
                    
                    if analysis['transcription_files']:
                        f.write("TRANSCRIPTIONS TROUVÉES:\n")
                        for trans in analysis['transcription_files']:
                            f.write(f"  - {trans['file']}: {trans['content']}\n")
                        f.write("\n")
                    
                    if analysis['issues']:
                        f.write("PROBLÈMES DÉTECTÉS:\n")
                        for issue in analysis['issues']:
                            f.write(f"  ⚠️ {issue}\n")
                        f.write("\n")
                    
                    f.write("\n")
            
            # Recommandations
            f.write("="*80 + "\n")
            f.write("RECOMMANDATIONS:\n")
            f.write("="*80 + "\n")
            
            if self.stats['contacts_missing_in_export'] > 0:
                f.write("\n⚠️ Des contacts ont des données qui n'apparaissent pas dans l'export!\n")
                f.write("\nCauses possibles:\n")
                f.write("1. Le parser HTML n'a pas extrait ces contacts\n")
                f.write("2. Le SimpleExporter ne lit pas correctement les conversation.json\n")
                f.write("3. Problème de correspondance des noms de dossiers\n")
                f.write("4. Les données sont écrasées lors du traitement\n")
                
        logger.info(f"\n✅ Rapport généré: {report_path}")
        
        # Afficher un résumé
        logger.info("\n" + "="*60)
        logger.info("RÉSUMÉ DU DIAGNOSTIC")
        logger.info("="*60)
        logger.info(f"Contacts avec données manquantes dans l'export: {self.stats['contacts_missing_in_export']}")
        
        if self.stats['contacts_missing_in_export'] > 0:
            logger.info("\nExemples de contacts problématiques:")
            count = 0
            for contact, analysis in contact_analysis.items():
                if count >= 5:  # Limiter à 5 exemples
                    break
                    
                export_content = export_data.get(contact, "NON TROUVÉ")
                has_data = (analysis['text_messages_received'] or 
                           analysis['audio_messages_received'] or 
                           analysis['has_transcriptions'])
                
                if has_data and (contact not in export_data or export_content == "[Aucun message reçu]"):
                    logger.info(f"\n- {contact}:")
                    if analysis['text_messages_received']:
                        logger.info(f"  Texte reçu: {analysis['text_messages_received'][0]['content'][:50]}...")
                    logger.info(f"  Export actuel: {export_content}")
                    count += 1

def main():
    """Point d'entrée principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python diagnostic_export_deep.py <output_directory>")
        print("Exemple: python diagnostic_export_deep.py C:\\Datalead3webidu13juillet")
        sys.exit(1)
        
    output_dir = sys.argv[1]
    
    if not os.path.exists(output_dir):
        print(f"Erreur: Le répertoire {output_dir} n'existe pas")
        sys.exit(1)
        
    diagnostic = ExportDiagnostic(output_dir)
    diagnostic.run_diagnostic()

if __name__ == "__main__":
    main()