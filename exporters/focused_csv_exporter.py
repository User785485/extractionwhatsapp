import os
import csv
import logging
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class FocusedCSVExporter:
    """
    Exporte un CSV avec une ligne par contact
    Colonnes: Contact | Nombre de messages reçus | Premier message | Dernier message | 
              Nombre d'audios | Nombre d'audios transcrits | Aperçu messages
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
    
    def export_focused_csv(self, conversations: Dict[str, List[Dict]]):
        """
        Génère un CSV focalisé avec une ligne par contact
        """
        csv_file = os.path.join(self.output_dir, 'messages_recus_par_contact.csv')
        
        logger.info(f"Génération du CSV focalisé: {csv_file}")
        
        # Préparer les données
        contact_data = []
        
        for contact, messages in conversations.items():
            # Filtrer les messages reçus
            received_messages = [m for m in messages if m.get('direction') == 'received']
            
            if not received_messages:
                continue
            
            # Trier par date/heure
            received_messages.sort(key=lambda m: (m.get('date', ''), m.get('time', '')))
            
            # Statistiques
            row_data = {
                'Contact': contact,
                'Nombre de messages reçus': len(received_messages),
                'Premier message': '',
                'Dernier message': '',
                'Nombre d\'audios reçus': 0,
                'Audios transcrits': 0,
                'Aperçu messages (10 premiers)': ''
            }
            
            # Dates premier/dernier message
            if received_messages:
                first = received_messages[0]
                last = received_messages[-1]
                row_data['Premier message'] = f"{first.get('date', '')} {first.get('time', '')}"
                row_data['Dernier message'] = f"{last.get('date', '')} {last.get('time', '')}"
            
            # Compter les audios
            audio_count = 0
            transcribed_count = 0
            
            for msg in received_messages:
                if msg.get('type') == 'audio':
                    audio_count += 1
                    # Vérifier si transcrit
                    if msg.get('media_path'):
                        file_hash = self.registry.get_file_hash(msg['media_path'])
                        if file_hash and self.registry.get_transcription(file_hash):
                            transcribed_count += 1
            
            row_data['Nombre d\'audios reçus'] = audio_count
            row_data['Audios transcrits'] = transcribed_count
            
            # Aperçu des messages (10 premiers)
            preview_messages = []
            for i, msg in enumerate(received_messages[:10]):
                if msg.get('type') == 'text':
                    content = msg.get('content', '').strip()[:100]  # Limiter à 100 caractères
                    preview_messages.append(f"{i+1}. {content}")
                else:
                    preview_messages.append(f"{i+1}. [{msg.get('type', 'media').upper()}]")
            
            row_data['Aperçu messages (10 premiers)'] = " | ".join(preview_messages)
            
            contact_data.append(row_data)
        
        # Trier par nombre de messages (décroissant)
        contact_data.sort(key=lambda x: x['Nombre de messages reçus'], reverse=True)
        
        # Écrire le CSV
        if contact_data:
            fieldnames = [
                'Contact',
                'Nombre de messages reçus',
                'Premier message',
                'Dernier message',
                'Nombre d\'audios reçus',
                'Audios transcrits',
                'Aperçu messages (10 premiers)'
            ]
            
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(contact_data)
            
            logger.info(f"CSV focalisé généré avec {len(contact_data)} contacts")
            
            # Créer aussi une version Excel si pandas disponible
            try:
                import pandas as pd
                df = pd.read_csv(csv_file, encoding='utf-8')
                excel_file = csv_file.replace('.csv', '.xlsx')
                
                # Ajuster la largeur des colonnes
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Messages reçus')
                    
                    # Ajuster les largeurs
                    worksheet = writer.sheets['Messages reçus']
                    worksheet.column_dimensions['A'].width = 30  # Contact
                    worksheet.column_dimensions['B'].width = 20  # Nombre
                    worksheet.column_dimensions['C'].width = 20  # Premier
                    worksheet.column_dimensions['D'].width = 20  # Dernier
                    worksheet.column_dimensions['E'].width = 18  # Audios
                    worksheet.column_dimensions['F'].width = 15  # Transcrits
                    worksheet.column_dimensions['G'].width = 100 # Aperçu
                
                logger.info(f"Version Excel générée: {excel_file}")
            except Exception as e:
                logger.info(f"pandas/openpyxl non disponible, pas de version Excel: {str(e)}")
        else:
            logger.warning("Aucun message reçu trouvé dans les conversations")
