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
from transcription_reader import TranscriptionReader

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
        # Initialiser le lecteur de transcriptions
        self.transcription_reader = TranscriptionReader(self.output_dir)
        
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
        """Collecte TOUS les contacts, même sans messages reçus"""
        logger.info("Collecte de TOUS les contacts...")
        output_data = {}
        
        total_contacts = 0
        total_messages = 0
        total_audios = 0
        total_transcribed = 0
        contacts_without_received = 0
        
        # Parcourir TOUS les contacts
        for contact, messages in conversations.items():
            contact_content = []
            has_received = False
            
            # Traiter tous les messages
            for msg in messages:
                # On cherche seulement les messages reçus
                if msg.get('direction') == 'received':
                    has_received = True
                    total_messages += 1
                    
                    if msg.get('type') == 'text':
                        content = msg.get('content', '').strip()
                        if content:
                            contact_content.append(content)
                            
                    elif msg.get('type') == 'audio':
                        total_audios += 1
                        # Chercher la transcription
                        transcription = self._get_audio_transcription(msg, contact)
                        
                        if transcription:
                            contact_content.append(f"[AUDIO] {transcription}")
                            total_transcribed += 1
                        else:
                            contact_content.append("[AUDIO non transcrit]")
        
            # IMPORTANT : Ajouter TOUS les contacts, même sans messages reçus
            total_contacts += 1
            
            if contact_content:
                # Contact avec des messages reçus
                output_data[contact] = " ".join(contact_content)
            else:
                # Contact SANS messages reçus - l'ajouter quand même !
                output_data[contact] = "[Aucun message reçu]"
                contacts_without_received += 1
                if not has_received:
                    logger.info(f"Contact sans messages reçus: {contact}")
        
        # Statistiques
        logger.info(f"Collecte terminée:")
        logger.info(f"  - TOTAL contacts traités: {total_contacts}")
        logger.info(f"  - Contacts avec messages reçus: {total_contacts - contacts_without_received}")
        logger.info(f"  - Contacts SANS messages reçus: {contacts_without_received}")
        logger.info(f"  - Total messages reçus: {total_messages}")
        logger.info(f"  - Total audios: {total_audios}")
        logger.info(f"  - Audios transcrits: {total_transcribed}")
        
        if total_audios > 0:
            transcription_rate = (total_transcribed / total_audios) * 100
            logger.info(f"  - Taux de transcription: {transcription_rate:.1f}%")
        
        return output_data
    
    def _get_audio_transcription(self, message: Dict, contact: str) -> Optional[str]:
        """Version simplifiée utilisant TranscriptionReader"""
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
