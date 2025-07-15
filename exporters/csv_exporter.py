import os
import csv
import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class CSVExporter:
    """
    Exporteur intelligent qui lit toutes_conversations_avec_transcriptions.txt
    et génère 4 fichiers clairs
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
        self.cell_limit = 50000  # Limite Excel par cellule
        
    def export_special_csv(self, conversations: Dict[str, List[Dict]], received_only: bool = False):
        """Point d'entrée principal - lit le fichier qui marche et génère les exports CSV
        
        Args:
            conversations: Dictionnaire des conversations
            received_only: Si True, génère uniquement l'export des messages reçus
        """
        logger.info("=== GÉNÉRATION DES EXPORTS CSV À PARTIR DU FICHIER QUI MARCHE ===")
        if received_only:
            logger.info("Mode export minimal: uniquement messages reçus")
            # En mode minimal, utiliser le fichier de messages reçus
            source_file = os.path.join(self.output_dir, 'messages_recus_avec_transcriptions.txt')
            logger.info(f"Utilisation du fichier source: {source_file}")
        else:
            # Mode standard - utiliser le fichier global
            source_file = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')
            logger.info(f"Utilisation du fichier source: {source_file}")
            
        if not os.path.exists(source_file):
            logger.warning(f"Le fichier {os.path.basename(source_file)} n'existe pas encore")
            logger.info("Attendez que le merger ait fini de le creer")
            return
            
        # Verifier aussi la taille du fichier
        if not os.path.exists(source_file):
            logger.warning(f"Le fichier {os.path.basename(source_file)} n'existe pas")
            return
            
        if os.path.getsize(source_file) < 100:
            logger.error(f"Le fichier {os.path.basename(source_file)} est trop petit ({os.path.getsize(source_file)} octets)")
            return
            
        logger.info(f"Lecture du fichier source: {source_file}")
        
        # 2. Parser le fichier
        parsed_data = self._parse_master_file(source_file)
        
        if not parsed_data:
            logger.error("Aucune donnée parsée du fichier source")
            return
            
        # 3. Générer les fichiers
        # Si received_only est activé, on ne génère que les fichiers de messages reçus
        if not received_only:
            self._generate_txt_files(parsed_data)
        self._generate_csv_files(parsed_data, received_only)
        
        logger.info("✅ Export terminé avec succès !")
    
    def _parse_master_file(self, file_path: str) -> Dict[str, Dict[str, List[str]]]:
        """
        Parse le fichier toutes_conversations_avec_transcriptions.txt
        
        Returns:
            Dict avec structure:
            {
                'contact1': {
                    'all': [tous les messages],
                    'received': [messages reçus only]
                },
                ...
            }
        """
        logger.info("Début du parsing du fichier maître...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Erreur lecture fichier: {str(e)}")
            return {}
        
        parsed_data = {}
        current_contact = None
        
        # Patterns pour détecter les sections et messages
        contact_pattern = r'CONVERSATION AVEC:\s*(.+)'
        message_pattern = r'\[(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\]\s*(←|→)\s*(.+)'
        
        lines = content.split('\n')
        
        for line in lines:
            # Détecter nouveau contact
            contact_match = re.search(contact_pattern, line)
            if contact_match:
                current_contact = contact_match.group(1).strip()
                logger.info(f"Contact trouvé: {current_contact}")
                if current_contact not in parsed_data:
                    parsed_data[current_contact] = {
                        'all': [],
                        'received': []
                    }
                continue
            
            # Détecter message
            if current_contact:
                message_match = re.search(message_pattern, line)
                if message_match:
                    date = message_match.group(1)
                    time = message_match.group(2)
                    direction = message_match.group(3)
                    content = message_match.group(4).strip()
                    
                    # Formater le message
                    formatted_msg = f"[{date} {time}] {content}"
                    
                    # Ajouter à 'all'
                    parsed_data[current_contact]['all'].append(formatted_msg)
                    
                    # Si reçu (←), ajouter aussi à 'received'
                    if direction == '←':
                        parsed_data[current_contact]['received'].append(formatted_msg)
        
        # Résumé du parsing
        total_contacts = len(parsed_data)
        total_messages = sum(len(data['all']) for data in parsed_data.values())
        total_received = sum(len(data['received']) for data in parsed_data.values())
        
        logger.info(f"Parsing terminé:")
        logger.info(f"  - Contacts: {total_contacts}")
        logger.info(f"  - Total messages: {total_messages}")
        logger.info(f"  - Messages reçus: {total_received}")
        
        return parsed_data
    
    def _generate_txt_files(self, parsed_data: Dict[str, Dict[str, List[str]]]):
        """Génère les 2 fichiers TXT"""
        logger.info("Génération des fichiers TXT...")
        
        # 1. Messages reçus only
        received_file = os.path.join(self.output_dir, 'messages_recus_only.txt')
        with open(received_file, 'w', encoding='utf-8') as f:
            f.write("MESSAGES REÇUS SEULEMENT (AVEC TRANSCRIPTIONS)\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            total_received = 0
            
            for contact, data in parsed_data.items():
                received_msgs = data['received']
                if received_msgs:
                    f.write(f"\n{'='*40}\n")
                    f.write(f"CONTACT: {contact}\n")
                    f.write(f"Messages reçus: {len(received_msgs)}\n")
                    f.write(f"{'='*40}\n\n")
                    
                    for msg in received_msgs:
                        f.write(msg + "\n")
                    
                    total_received += len(received_msgs)
            
            f.write(f"\n\nTOTAL MESSAGES REÇUS: {total_received}\n")
        
        logger.info(f"✓ Créé: {received_file}")
        
        # 2. Tous les messages
        all_file = os.path.join(self.output_dir, 'messages_all.txt')
        with open(all_file, 'w', encoding='utf-8') as f:
            f.write("TOUS LES MESSAGES (REÇUS + ENVOYÉS) AVEC TRANSCRIPTIONS\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            total_all = 0
            
            for contact, data in parsed_data.items():
                all_msgs = data['all']
                if all_msgs:
                    f.write(f"\n{'='*40}\n")
                    f.write(f"CONTACT: {contact}\n")
                    f.write(f"Total messages: {len(all_msgs)}\n")
                    f.write(f"{'='*40}\n\n")
                    
                    for msg in all_msgs:
                        f.write(msg + "\n")
                    
                    total_all += len(all_msgs)
            
            f.write(f"\n\nTOTAL TOUS MESSAGES: {total_all}\n")
        
        logger.info(f"✓ Créé: {all_file}")
    
    def _generate_csv_files(self, parsed_data: Dict[str, Dict[str, List[str]]], received_only: bool = False):
        """Génère les fichiers CSV avec débordement sur colonnes
        
        Args:
            parsed_data: Données parsées des fichiers
            received_only: Si True, génère uniquement le CSV des messages reçus
        """
        logger.info("Génération des fichiers CSV...")
        
        # 1. Messages reçus only (toujours généré)
        self._write_csv(
            {contact: data['received'] for contact, data in parsed_data.items()},
            'messages_recus_only.csv',
            'Messages Reçus avec Transcriptions'
        )
        
        # 2. Tous les messages (uniquement si mode complet)
        if not received_only:
            logger.info("Génération du fichier CSV avec tous les messages...")
            self._write_csv(
                {contact: data['all'] for contact, data in parsed_data.items()},
                'messages_all.csv',
                'Tous les Messages avec Transcriptions'
            )
    
    def _write_csv(self, messages_dict: Dict[str, List[str]], filename: str, description: str):
        """
        Écrit un fichier CSV avec gestion du débordement sur colonnes
        Format: Contact | Messages | Suite... | Suite...
        """
        csv_file = os.path.join(self.output_dir, filename)
        
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            # Calculer le nombre max de colonnes nécessaires
            max_columns = 1
            for messages in messages_dict.values():
                if messages:
                    # Joindre tous les messages avec séparateur
                    content = " | ".join(messages)
                    # Calculer combien de colonnes il faut
                    columns_needed = (len(content) // self.cell_limit) + 1
                    max_columns = max(max_columns, columns_needed)
            
            # Créer l'en-tête
            headers = ['Contact/Téléphone']
            for i in range(max_columns):
                if i == 0:
                    headers.append(description)
                else:
                    headers.append(f'Suite (partie {i+1})')
            
            writer = csv.writer(f)
            writer.writerow(headers)
            
            # Écrire les données
            for contact, messages in sorted(messages_dict.items()):
                if not messages:
                    continue
                    
                row = [contact]
                
                # Joindre tous les messages
                content = " | ".join(messages)
                
                # Diviser en chunks si nécessaire
                for i in range(0, len(content), self.cell_limit):
                    chunk = content[i:i + self.cell_limit]
                    row.append(chunk)
                
                # Compléter avec des cellules vides si nécessaire
                while len(row) < len(headers):
                    row.append('')
                
                writer.writerow(row)
        
        logger.info(f"✓ Créé: {csv_file} ({len([m for m in messages_dict.values() if m])} contacts)")
        
        # Créer aussi la version Excel si pandas est disponible
        try:
            import pandas as pd
            df = pd.read_csv(csv_file, encoding='utf-8')
            excel_file = csv_file.replace('.csv', '.xlsx')
            df.to_excel(excel_file, index=False, engine='openpyxl')
            logger.info(f"✓ Créé aussi: {excel_file}")
        except Exception as e:
            logger.debug(f"Pas de conversion Excel (pandas non installé): {e}")