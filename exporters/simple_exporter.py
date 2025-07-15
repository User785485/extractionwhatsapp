#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Exporter Unifié pour WhatsApp Extractor
Version corrigée qui unifie TOUTES les sources de données
"""

import os
import csv
import re
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path

from core import UnifiedRegistry, FileManager
from exporters.base_exporter import BaseExporter
from transcription_reader import TranscriptionReader

logger = logging.getLogger('whatsapp_extractor')

class SimpleExporter(BaseExporter):
    """
    Exporteur simple unifié qui génère :
    - 1 fichier CSV : Contact | Messages
    - 1 fichier TXT : même format
    
    UNIFIE toutes les sources :
    - Messages des conversations HTML
    - Transcriptions orphelines
    - Fichiers conversation.json
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        super().__init__(config, registry, file_manager)
        self.transcription_reader = TranscriptionReader(self.output_dir)
        
    def export(self, conversations: Dict[str, List[Dict]], **kwargs) -> bool:
        """Interface requise par BaseExporter"""
        return self.export_simple(conversations)
    
    def export_simple(self, conversations: Dict[str, List[Dict]]) -> bool:
        """
        Export simple unifié : génère CSV et TXT avec TOUS les contacts et messages
        """
        logger.info("="*60)
        logger.info("EXPORT SIMPLE UNIFIÉ - DÉBUT")
        logger.info("="*60)
        
        try:
            # ÉTAPE 1: Collecter toutes les sources de données
            all_contacts_data = self._collect_all_data_sources(conversations)
            
            if not all_contacts_data:
                logger.warning("Aucune donnée à exporter")
                return False
            
            # ÉTAPE 2: Générer les fichiers
            csv_success = self._write_csv_simple(all_contacts_data)
            txt_success = self._write_txt_simple(all_contacts_data)
            
            if csv_success and txt_success:
                logger.info(f"✅ Export simple terminé avec succès! Total contacts: {len(all_contacts_data)}")
                return True
            else:
                logger.error("Erreur lors de l'export")
                return False
                
        except Exception as e:
            logger.error(f"Erreur fatale dans export simple: {str(e)}", exc_info=True)
            return False
    
    def _collect_all_data_sources(self, conversations: Dict[str, List[Dict]]) -> Dict[str, str]:
        """
        Collecte et unifie TOUTES les sources de données :
        1. Messages des conversations HTML
        2. Transcriptions depuis TranscriptionReader
        3. Fichiers conversation.json orphelins
        4. Dossiers avec transcriptions mais sans conversations
        """
        logger.info("Collecte unifiée de TOUTES les sources de données...")
        
        # Dictionnaire unifié {contact: contenu}
        unified_data = {}
        
        # Statistiques
        stats = {
            'contacts_html': 0,
            'contacts_transcriptions_only': 0,
            'contacts_json_only': 0,
            'total_messages': 0,
            'total_audios': 0,
            'total_transcribed': 0,
            'contacts_without_content': 0
        }
        
        # ÉTAPE 1: Traiter les conversations HTML
        logger.info("1. Traitement des conversations HTML...")
        for contact, messages in conversations.items():
            contact_content = []
            has_received = False
            
            for msg in messages:
                if msg.get('direction') == 'received':
                    has_received = True
                    stats['total_messages'] += 1
                    
                    if msg.get('type') == 'text':
                        content = msg.get('content', '').strip()
                        if content:
                            contact_content.append(content)
                            
                    elif msg.get('type') == 'audio':
                        stats['total_audios'] += 1
                        # Chercher la transcription via TranscriptionReader
                        transcription = self._get_audio_transcription(msg, contact)
                        
                        if transcription:
                            contact_content.append(f"[AUDIO] {transcription}")
                            stats['total_transcribed'] += 1
                        else:
                            # Essayer de trouver via d'autres méthodes
                            transcription = self._find_transcription_alternative(msg, contact)
                            if transcription:
                                contact_content.append(f"[AUDIO] {transcription}")
                                stats['total_transcribed'] += 1
                            else:
                                contact_content.append("[AUDIO non transcrit]")
            
            # Ajouter le contact même sans messages reçus
            if contact_content:
                unified_data[contact] = " ".join(contact_content)
            else:
                unified_data[contact] = "[Aucun message reçu]"
                if not has_received:
                    stats['contacts_without_content'] += 1
            
            stats['contacts_html'] += 1
        
        # ÉTAPE 2: Scanner TOUS les dossiers pour trouver les contacts manquants
        logger.info("2. Scan des dossiers pour contacts manquants...")
        contacts_added_from_folders = self._scan_for_missing_contacts(unified_data, stats)
        
        # ÉTAPE 3: Intégrer les transcriptions orphelines
        logger.info("3. Intégration des transcriptions orphelines...")
        self._integrate_orphan_transcriptions(unified_data, stats)
        
        # Afficher les statistiques
        logger.info("="*60)
        logger.info("STATISTIQUES DE COLLECTE UNIFIÉE:")
        logger.info(f"  - Contacts depuis HTML: {stats['contacts_html']}")
        logger.info(f"  - Contacts ajoutés (transcriptions seules): {stats['contacts_transcriptions_only']}")
        logger.info(f"  - Contacts ajoutés (JSON seuls): {stats['contacts_json_only']}")
        logger.info(f"  - TOTAL contacts: {len(unified_data)}")
        logger.info(f"  - Total messages texte: {stats['total_messages']}")
        logger.info(f"  - Total audios: {stats['total_audios']}")
        logger.info(f"  - Audios transcrits: {stats['total_transcribed']}")
        if stats['total_audios'] > 0:
            rate = (stats['total_transcribed'] / stats['total_audios']) * 100
            logger.info(f"  - Taux de transcription: {rate:.1f}%")
        logger.info("="*60)
        
        return unified_data
    
    def _scan_for_missing_contacts(self, unified_data: Dict[str, str], stats: Dict) -> int:
        """Scanne tous les dossiers pour trouver les contacts manquants"""
        added = 0
        
        for contact_dir in Path(self.output_dir).iterdir():
            if not contact_dir.is_dir() or contact_dir.name.startswith('.'):
                continue
                
            contact_name = contact_dir.name
            
            # Si le contact est déjà dans unified_data, passer
            if contact_name in unified_data:
                continue
            
            # Vérifier s'il y a du contenu intéressant
            content_parts = []
            
            # 1. D'ABORD vérifier conversation.json (PRIORITÉ)
            json_file = contact_dir / "conversation.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                    
                    # Extraire les messages reçus
                    received_content = []
                    for msg in messages:
                        if msg.get('direction') == 'received':
                            if msg.get('type') == 'text':
                                content = msg.get('content', '').strip()
                                if content:
                                    received_content.append(content)
                            elif msg.get('type') == 'audio':
                                # Essayer de trouver la transcription
                                transcription = self._get_audio_transcription(msg, contact_name)
                                if transcription:
                                    received_content.append(f"[AUDIO] {transcription}")
                                else:
                                    received_content.append("[AUDIO non transcrit]")
                    
                    if received_content:
                        unified_data[contact_name] = " ".join(received_content)
                        logger.info(f"Ajout du contact manquant: {contact_name} ({len(received_content)} éléments)")
                        stats['contacts_json_only'] += 1
                        added += 1
                        continue  # Passer au contact suivant
                        
                except Exception as e:
                    logger.error(f"Erreur lecture conversation.json pour {contact_name}: {e}")
            
            # 2. Si pas de conversation.json ou vide, vérifier les transcriptions
            trans_dir = contact_dir / "transcriptions"
            if trans_dir.exists():
                txt_files = list(trans_dir.glob("*.txt"))
                if txt_files:
                    # Lire et ajouter les transcriptions
                    for txt_file in txt_files:
                        try:
                            transcription = self._read_transcription_file(txt_file)
                            if transcription:
                                content_parts.append(f"[AUDIO] {transcription}")
                        except Exception as e:
                            logger.error(f"Erreur lecture {txt_file}: {e}")
                    
                    if content_parts:
                        unified_data[contact_name] = " ".join(content_parts)
                        logger.info(f"Ajout du contact manquant: {contact_name} ({len(txt_files)} transcriptions)")
                        stats['contacts_transcriptions_only'] += 1
                        added += 1
                        continue
            
            # 3. Si rien trouvé mais le dossier existe, l'ajouter quand même
            unified_data[contact_name] = "[Aucun message reçu]"
            logger.info(f"Ajout du contact manquant: {contact_name} (aucun message reçu)")
            added += 1
        
        return added
    
    def _integrate_orphan_transcriptions(self, unified_data: Dict[str, str], stats: Dict):
        """Intègre les transcriptions qui n'ont pas été liées à des messages"""
        # Utiliser le cache du TranscriptionReader
        for contact, transcriptions in self.transcription_reader.cache.items():
            if contact in unified_data:
                # Le contact existe déjà, vérifier s'il manque des transcriptions
                current_content = unified_data[contact]
                
                # Si le contact n'a que "[Aucun message reçu]", remplacer par les transcriptions
                if current_content == "[Aucun message reçu]" and transcriptions:
                    trans_contents = []
                    for uuid, trans_text in transcriptions.items():
                        if trans_text and len(trans_text.strip()) > 10:
                            trans_contents.append(f"[AUDIO] {trans_text}")
                    
                    if trans_contents:
                        unified_data[contact] = " ".join(trans_contents)
                        logger.info(f"Remplacement du contenu vide pour {contact} avec {len(trans_contents)} transcriptions")
    
    def _find_transcription_alternative(self, message: Dict, contact: str) -> Optional[str]:
        """Méthodes alternatives pour trouver une transcription"""
        media_path = message.get('media_path')
        if not media_path:
            return None
        
        # Méthode 1: Chercher directement dans le dossier transcriptions
        contact_dir = Path(self.output_dir) / contact / "transcriptions"
        if contact_dir.exists():
            # Extraire l'UUID du media_path
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', media_path)
            if uuid_match:
                uuid = uuid_match.group(1)
                
                # Chercher un fichier avec cet UUID
                for txt_file in contact_dir.glob("*.txt"):
                    if uuid in str(txt_file):
                        transcription = self._read_transcription_file(txt_file)
                        if transcription:
                            return transcription
        
        return None
    
    def _read_transcription_file(self, file_path: Path) -> Optional[str]:
        """Lit et extrait la transcription d'un fichier"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Trouver le séparateur
            lines = content.split('\n')
            separator_idx = -1
            
            for i, line in enumerate(lines):
                if '=' * 40 in line:
                    separator_idx = i
                    break
            
            if separator_idx == -1:
                # Pas de séparateur, prendre tout après les 5 premières lignes
                if len(lines) > 5:
                    return '\n'.join(lines[5:]).strip()
            else:
                # Prendre tout après le séparateur
                if separator_idx < len(lines) - 1:
                    return '\n'.join(lines[separator_idx + 1:]).strip()
                    
        except Exception as e:
            logger.error(f"Erreur lecture fichier {file_path}: {e}")
            
        return None
    
    def _get_audio_transcription(self, message: Dict, contact: str) -> Optional[str]:
        """Version améliorée utilisant TranscriptionReader"""
        media_path = message.get('media_path')
        if not media_path:
            return None
        
        # Extraire l'UUID
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', media_path)
        if not uuid_match:
            return None
        
        uuid = uuid_match.group(1)
        
        # Utiliser le reader
        return self.transcription_reader.get_transcription(uuid, contact)
    
    def _write_csv_simple(self, output_data: Dict[str, str]) -> bool:
        """Écrit le fichier CSV simple avec validation"""
        csv_path = os.path.join(self.output_dir, 'export_simple.csv')
        
        try:
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                
                # En-tête
                writer.writerow(['Contact/Identifiant', 'Messages reçus et transcriptions'])
                
                # Écrire TOUTES les données
                contacts_written = 0
                for contact, content in sorted(output_data.items()):
                    writer.writerow([contact, content])
                    contacts_written += 1
            
            logger.info(f"✓ CSV créé: {csv_path}")
            logger.info(f"  - Nombre de contacts ÉCRITS: {contacts_written}")
            logger.info(f"  - Nombre de contacts ATTENDUS: {len(output_data)}")
            
            if contacts_written != len(output_data):
                logger.error(f"⚠️ PROBLÈME : {len(output_data) - contacts_written} contacts manquants !")
                return False
            
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
                logger.info(f"  - Nombre de lignes dans Excel: {len(df)}")
                
            except Exception as e:
                logger.warning(f"Excel non créé (pandas/openpyxl manquant?): {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur écriture CSV: {str(e)}", exc_info=True)
            return False
    
    def _write_txt_simple(self, output_data: Dict[str, str]) -> bool:
        """Écrit le fichier TXT simple avec statistiques"""
        txt_path = os.path.join(self.output_dir, 'export_simple.txt')
        
        try:
            # Calculer des statistiques
            contacts_with_messages = sum(1 for content in output_data.values() if content != "[Aucun message reçu]")
            contacts_with_audio = sum(1 for content in output_data.values() if "[AUDIO]" in content)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                # En-tête enrichi
                f.write("EXPORT SIMPLE UNIFIÉ - MESSAGES REÇUS AVEC TRANSCRIPTIONS\n")
                f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Nombre total de contacts: {len(output_data)}\n")
                f.write(f"Contacts avec messages: {contacts_with_messages}\n")
                f.write(f"Contacts avec audio: {contacts_with_audio}\n")
                f.write("="*60 + "\n\n")
                
                # Données triées par contact
                for contact, content in sorted(output_data.items()):
                    f.write(f"{contact}:\n")
                    f.write(f"{content}\n")
                    f.write("\n" + "-"*60 + "\n\n")
                
                # Résumé final
                f.write("\n" + "="*60 + "\n")
                f.write("RÉSUMÉ FINAL:\n")
                f.write(f"- Total contacts exportés: {len(output_data)}\n")
                f.write(f"- Contacts avec messages reçus: {contacts_with_messages}\n")
                f.write(f"- Contacts sans messages: {len(output_data) - contacts_with_messages}\n")
                f.write(f"- Contacts avec transcriptions audio: {contacts_with_audio}\n")
            
            logger.info(f"✓ TXT créé: {txt_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur écriture TXT: {str(e)}", exc_info=True)
            return False