#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Exporter pour WhatsApp Extractor
Export simple : Contact | Messages reçus avec transcriptions
"""

import os
import csv
import re
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
        
        # Méthode 1: Chercher par hash du fichier directement
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
            logger.debug(f"Méthode 1 échec: {e}")
        
        # Méthode 2: Essayer par le nom du fichier
        try:
            filename = os.path.basename(media_path)
            # Extraire l'UUID du nom
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', filename)
            if uuid_match:
                uuid = uuid_match.group(1)
                # Parcourir toutes les transcriptions
                for hash_id, trans_data in self.registry.data.get('transcriptions', {}).items():
                    if uuid in hash_id or (trans_data.get('source', '') and uuid in trans_data.get('source', '')):
                        if trans_data.get('text'):
                            return trans_data['text'].strip()
        except Exception as e:
            logger.debug(f"Méthode 2 échec: {e}")
        
        # Méthode 3: Chercher dans tous les fichiers audio du contact
        try:
            contact_key = contact.replace(' ', '_').lower()
            # Parcourir tous les fichiers MP3 dans le répertoire du contact
            contact_dir = os.path.join(self.output_dir, contact_key)
            audio_dir = os.path.join(contact_dir, 'audio')
            
            if os.path.exists(audio_dir):
                for trans_hash, trans_data in self.registry.data.get('transcriptions', {}).items():
                    if trans_data.get('text') and trans_data.get('source'):
                        source = trans_data['source']
                        if contact_key in source.lower():
                            return trans_data['text'].strip()
        except Exception as e:
            logger.debug(f"Méthode 3 échec: {e}")
        
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
                f.write("EXPORT SIMPLE - MESSAGES REÇUS AVEC TRANSCRIPTIONS\n")
                f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Nombre de contacts: {len(output_data)}\n")
                f.write("="*60 + "\n\n")
                
                # Données
                for contact, content in sorted(output_data.items()):
                    f.write(f"{contact}:\n")
                    f.write(f"{content}\n")
                    f.write("\n" + "-"*60 + "\n\n")
                
                # Résumé
                f.write("\n" + "="*60 + "\n")
                f.write(f"TOTAL: {len(output_data)} contacts avec messages reçus\n")
            
            logger.info(f"✓ TXT créé: {txt_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur écriture TXT: {str(e)}")
            return False
