import os
import logging
from datetime import datetime
from typing import Dict, List

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class TextExporter:
    """
    Exporte les conversations en fichiers texte
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
    
    def export_all_formats(self, conversations: Dict[str, List[Dict]]):
        """Génère tous les exports texte"""
        logger.info("Génération des exports texte")
        
        # 1. Fichiers globaux
        self._export_global_files(conversations)
        
        # 2. Fichiers par contact
        self._export_contact_files(conversations)
        
        # 3. Fichiers de messages reçus
        self._export_received_messages(conversations)
        
    def export_received_only(self, conversations: Dict[str, List[Dict]]):
        """Génère uniquement les exports de messages reçus (mode minimal)"""
        logger.info("Génération des exports texte en mode minimal (messages reçus uniquement)")
        
        # Uniquement les fichiers de messages reçus
        self._export_received_messages(conversations)
    
    def _export_global_files(self, conversations: Dict[str, List[Dict]]):
        """Génère les fichiers globaux"""
        # Fichier toutes conversations
        global_file = os.path.join(self.output_dir, 'toutes_conversations.txt')
        
        with open(global_file, 'w', encoding='utf-8') as f:
            f.write("TOUTES LES CONVERSATIONS WHATSAPP\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre de contacts: {len(conversations)}\n\n")
            
            total_messages = 0
            total_media = 0
            
            for contact, messages in conversations.items():
                f.write(f"\n{'='*50}\n")
                f.write(f"CONVERSATION AVEC: {contact}\n")
                f.write(f"{'='*50}\n\n")
                
                # Stats
                num_messages = len(messages)
                num_media = sum(1 for m in messages if m['type'] != 'text')
                f.write(f"Nombre de messages: {num_messages}\n")
                f.write(f"Nombre de médias: {num_media}\n\n")
                
                total_messages += num_messages
                total_media += num_media
                
                # Messages
                for msg in sorted(messages, key=lambda m: (m['date'], m['time'])):
                    direction_symbol = "→" if msg['direction'] == 'sent' else "←"
                    f.write(f"[{msg['date']} {msg['time']}] {direction_symbol} ")
                    
                    if msg['type'] == 'text':
                        f.write(f"{msg['content']}\n")
                    else:
                        media_name = os.path.basename(msg['media_path']) if msg['media_path'] else 'unknown'
                        f.write(f"[{msg['type'].upper()}] {media_name}\n")
            
            # Résumé
            f.write(f"\n\n{'='*50}\n")
            f.write("RÉSUMÉ GLOBAL\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"Total contacts: {len(conversations)}\n")
            f.write(f"Total messages: {total_messages}\n")
            f.write(f"Total médias: {total_media}\n")
        
        logger.info(f"Export global créé: {global_file}")
    
    def _export_contact_files(self, conversations: Dict[str, List[Dict]]):
        """Génère les fichiers par contact"""
        for contact, messages in conversations.items():
            paths = self.file_manager.setup_contact_directory(contact)
            
            # Fichier tous messages
            all_messages_file = os.path.join(paths['root'], 'tous_messages.txt')
            
            with open(all_messages_file, 'w', encoding='utf-8') as f:
                f.write(f"CONVERSATION AVEC: {contact}\n")
                f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Nombre de messages: {len(messages)}\n\n")
                f.write("="*50 + "\n\n")
                
                current_date = None
                for msg in sorted(messages, key=lambda m: (m['date'], m['time'])):
                    # Séparateur de date
                    if current_date != msg['date']:
                        current_date = msg['date']
                        f.write(f"\n--- {current_date} ---\n\n")
                    
                    direction_symbol = "→" if msg['direction'] == 'sent' else "←"
                    f.write(f"[{msg['time']}] {direction_symbol} ")
                    
                    if msg['type'] == 'text':
                        f.write(f"{msg['content']}\n")
                    else:
                        media_name = os.path.basename(msg['media_path']) if msg['media_path'] else 'unknown'
                        f.write(f"[{msg['type'].upper()}] {media_name}\n")
    
    def _export_received_messages(self, conversations: Dict[str, List[Dict]]):
        """Génère les fichiers de messages reçus"""
        # Fichier global des messages reçus
        global_received = os.path.join(self.output_dir, 'messages_recus.txt')
        
        with open(global_received, 'w', encoding='utf-8') as f:
            f.write("TOUS LES MESSAGES REÇUS\n")
            f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*50 + "\n\n")
            
            total_received = 0
            
            for contact, messages in conversations.items():
                # Filtrer les messages reçus
                received_msgs = [m for m in messages if m['direction'] == 'received']
                
                if not received_msgs:
                    continue
                
                total_received += len(received_msgs)
                
                f.write(f"\n{'='*30}\n")
                f.write(f"DE: {contact}\n")
                f.write(f"{'='*30}\n\n")
                
                for msg in sorted(received_msgs, key=lambda m: (m['date'], m['time'])):
                    f.write(f"[{msg['date']} {msg['time']}] ")
                    
                    if msg['type'] == 'text':
                        f.write(f"{msg['content']}\n")
                    else:
                        media_name = os.path.basename(msg['media_path']) if msg['media_path'] else 'unknown'
                        f.write(f"[{msg['type'].upper()}] {media_name}\n")
                
                # Fichier individuel par contact
                contact_received = os.path.join(
                    self.file_manager.setup_contact_directory(contact)['root'],
                    'messages_recus.txt'
                )
                
                with open(contact_received, 'w', encoding='utf-8') as fc:
                    fc.write(f"MESSAGES REÇUS DE: {contact}\n")
                    fc.write(f"Nombre: {len(received_msgs)}\n")
                    fc.write("="*50 + "\n\n")
                    
                    for msg in sorted(received_msgs, key=lambda m: (m['date'], m['time'])):
                        fc.write(f"[{msg['date']} {msg['time']}] ")
                        
                        if msg['type'] == 'text':
                            fc.write(f"{msg['content']}\n")
                        else:
                            media_name = os.path.basename(msg['media_path']) if msg['media_path'] else 'unknown'
                            fc.write(f"[{msg['type'].upper()}] {media_name}\n")
            
            f.write(f"\n\nTOTAL MESSAGES REÇUS: {total_received}\n")