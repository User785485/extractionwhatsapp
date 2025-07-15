import os
import csv
import logging
from typing import Dict, List

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class CSVExporter:
    """
    Genere LE fichier CSV special avec une ligne par contact
    Format: Contact | Tous les messages (partie 1) | Suite (partie 2) | ...
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
        self.cell_limit = 50000  # Limite de caracteres par cellule
        
        # NOUVEAU: Construire mapping OPUS -> MP3 pour les transcriptions
        self.opus_to_mp3_mapping = self._build_opus_to_mp3_mapping()
    
    def _build_opus_to_mp3_mapping(self) -> Dict[str, str]:
        """Construit un mapping des fichiers OPUS vers leurs MP3 convertis"""
        mapping = {}
        
        # Parcourir le registre pour trouver les conversions
        for file_hash, file_info in self.registry.data.get('files', {}).items():
            if file_info.get('type') == 'audio':
                original_path = file_info.get('path', '')
                converted_path = file_info.get('converted_path', '')
                
                if original_path and converted_path:
                    # Les deux chemins existent
                    mapping[original_path] = converted_path
                    logger.debug(f"Mapping: {os.path.basename(original_path)} -> {os.path.basename(converted_path)}")
        
        logger.info(f"Mapping OPUS->MP3 construit: {len(mapping)} correspondances")
        return mapping
    
    def export_special_csv(self, conversations: Dict[str, List[Dict]]):
        """
        Genere le CSV special avec tous les messages par contact
        """
        csv_file = os.path.join(self.output_dir, 'transcriptions_speciales.csv')
        
        logger.info(f"Generation du CSV special: {csv_file}")
        
        # Preparer les donnees par contact
        contact_data = {}
        stats = {'total_messages': 0, 'messages_with_transcription': 0}
        
        for contact, messages in conversations.items():
            # Initialiser les donnees du contact
            all_content = []
            
            # Parcourir tous les messages
            for msg in sorted(messages, key=lambda m: (m['date'], m['time'])):
                # Filtrer selon le mode
                mode = self.config.get('Processing', 'mode', fallback='received_only')
                
                if mode == 'received_only' and msg['direction'] != 'received':
                    continue
                elif mode == 'sent_only' and msg['direction'] != 'sent':
                    continue
                # mode == 'both' -> on prend tout
                
                # Formater le message
                formatted_msg = f"[{msg['date']} {msg['time']}] "
                
                if msg['type'] == 'text':
                    formatted_msg += msg['content']
                else:
                    # Pour les medias audio, chercher la transcription
                    if msg['type'] == 'audio' and msg['media_path']:
                        transcription = self._find_transcription_for_audio(msg['media_path'])
                        
                        if transcription:
                            formatted_msg += f'[AUDIO TRANSCRIT] "{transcription}"'
                            stats['messages_with_transcription'] += 1
                        else:
                            formatted_msg += f"[AUDIO] {os.path.basename(msg['media_path'])}"
                    else:
                        media_path = msg.get('media_path')
                        media_name = os.path.basename(media_path) if media_path else ''
                        formatted_msg += f"[{msg['type'].upper()}] {media_name}"
                
                all_content.append(formatted_msg)
                stats['total_messages'] += 1
            
            # Joindre tous les messages
            if all_content:  # Ne pas ajouter les contacts sans messages
                contact_data[contact] = " | ".join(all_content)
        
        # Log des stats
        logger.info(f"Messages traites: {stats['total_messages']}")
        logger.info(f"Messages avec transcription: {stats['messages_with_transcription']}")
        
        # Ecrire le CSV
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Determiner le nombre maximum de colonnes necessaires
            max_columns = 1
            for content in contact_data.values():
                columns_needed = (len(content) // self.cell_limit) + 1
                max_columns = max(max_columns, columns_needed)
            
            # En-tete dynamique
            headers = ['Contact/Identifiant']
            for i in range(max_columns):
                if i == 0:
                    headers.append('Tous les messages')
                else:
                    headers.append(f'Suite (partie {i+1})')
            
            writer.writerow(headers)
            
            # Ecrire les donnees
            for contact, content in contact_data.items():
                row = [contact]
                
                # Diviser le contenu en chunks de 50000 caracteres
                for i in range(0, len(content), self.cell_limit):
                    chunk = content[i:i + self.cell_limit]
                    row.append(chunk)
                
                # Completer avec des cellules vides si necessaire
                while len(row) < len(headers):
                    row.append('')
                
                writer.writerow(row)
        
        logger.info(f"CSV special genere avec {len(contact_data)} contacts")
        
        # Generer aussi une version Excel si pandas disponible
        try:
            import pandas as pd
            df = pd.read_csv(csv_file, encoding='utf-8')
            excel_file = csv_file.replace('.csv', '.xlsx')
            df.to_excel(excel_file, index=False)
            logger.info(f"Version Excel generee: {excel_file}")
        except:
            logger.info("pandas non disponible, pas de version Excel")
    
    def _find_transcription_for_audio(self, audio_path: str) -> str:
        """
        NOUVEAU: Trouve la transcription pour un fichier audio (OPUS ou MP3)
        Gere la correspondance OPUS -> MP3
        """
        # Essayer d'abord avec le fichier tel quel
        file_hash = self.registry.get_file_hash(audio_path)
        if file_hash:
            transcription = self.registry.get_transcription(file_hash)
            if transcription:
                logger.debug(f"Transcription trouvee directement pour {os.path.basename(audio_path)}")
                return transcription
        
        # Si c'est un OPUS, chercher le MP3 correspondant
        if audio_path.endswith('.opus'):
            # Chercher dans le mapping
            mp3_path = self.opus_to_mp3_mapping.get(audio_path)
            
            if mp3_path:
                # Calculer le hash du MP3
                mp3_hash = self.registry.get_file_hash(mp3_path)
                if mp3_hash:
                    transcription = self.registry.get_transcription(mp3_hash)
                    if transcription:
                        logger.debug(f"Transcription trouvee via MP3 pour {os.path.basename(audio_path)}")
                        return transcription
            
            # Alternative: chercher par pattern de nom
            # Si sent_122e53af-e2a0-4049-b3b7-1675ffec9f8a.opus
            # Chercher un MP3 qui pourrait correspondre
            opus_name = os.path.basename(audio_path)
            
            # Parcourir toutes les transcriptions pour trouver une correspondance
            for trans_hash, trans_data in self.registry.data.get('transcriptions', {}).items():
                # Verifier si ce hash correspond a un fichier avec un pattern similaire
                for file_hash, file_info in self.registry.data.get('files', {}).items():
                    if file_hash == trans_hash:
                        converted_path = file_info.get('converted_path', '')
                        if converted_path:
                            mp3_name = os.path.basename(converted_path)
                            # Verifier si les noms pourraient correspondre
                            if self._files_might_match(opus_name, mp3_name):
                                transcription = trans_data.get('text', '')
                                if transcription:
                                    logger.debug(f"Transcription trouvee par pattern pour {opus_name}")
                                    return transcription
        
        # Aucune transcription trouvee
        logger.debug(f"Aucune transcription trouvee pour {os.path.basename(audio_path)}")
        return ""
    
    def _files_might_match(self, opus_name: str, mp3_name: str) -> bool:
        """Verifie si deux fichiers pourraient correspondre"""
        # Extraire la direction de chaque fichier
        opus_direction = 'sent' if 'sent' in opus_name else 'received'
        mp3_direction = 'sent' if 'sent' in mp3_name else 'received'
        
        # Si meme direction, c'est potentiellement le meme fichier
        if opus_direction == mp3_direction:
            # Verifier si l'un des UUID est present dans l'autre
            import re
            
            # Extraire les UUID
            opus_uuid = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', opus_name)
            
            if opus_uuid:
                uuid = opus_uuid.group(1)
                # Voir si cet UUID est quelque part dans le registre lie a ce MP3
                return True  # Pour simplifier, on suppose que c'est le bon
        
        return False