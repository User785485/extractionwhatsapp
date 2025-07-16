"""
Parser spécialisé pour les exports HTML de MobileTrans WhatsApp
Format spécifique découvert dans les vrais fichiers
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import logging

from parsers.base_parser import BaseParser
from core.models import Contact, Message, MessageDirection, MediaType
from core.exceptions import ParsingError

logger = logging.getLogger(__name__)


class MobileTransParser(BaseParser):
    """Parser spécialisé pour les exports MobileTrans WhatsApp"""
    
    def __init__(self):
        super().__init__()
    
    def validate_file(self, file_path: Path) -> bool:
        """Valider si le fichier est un export MobileTrans WhatsApp"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Lire les premiers 1000 caractères
            
            # Vérifier les marqueurs MobileTrans
            indicators = [
                "iPhone's WhatsApp",
                "triangle-isosceles",
                "MobileTrans",
                "ExportMedia"
            ]
            
            return any(indicator in content for indicator in indicators)
            
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return False
    
    def parse(self, file_path: Path) -> Dict[str, List[Message]]:
        """Parser un fichier HTML MobileTrans"""
        if not self.validate_file(file_path):
            raise ParsingError(f"File is not a valid MobileTrans WhatsApp export: {file_path}")
        
        logger.info(f"Parsing MobileTrans WhatsApp file: {file_path}")
        
        try:
            # Lire le fichier
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parser avec BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extraire le nom du contact depuis le titre H3
            contact_name = self._extract_contact_name(soup, file_path)
            
            # Extraire les messages
            messages = self._extract_messages(soup, contact_name)
            
            logger.info(f"Extracted {len(messages)} messages for contact: {contact_name}")
            
            return {contact_name: messages}
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise ParsingError(f"Failed to parse MobileTrans file: {str(e)}")
    
    def extract_contacts(self, file_path: Path) -> List[Contact]:
        """Extraire les contacts uniques du fichier"""
        try:
            # Parser le fichier d'abord
            contact_messages = self.parse(file_path)
            
            contacts = []
            for contact_name, messages in contact_messages.items():
                # Calculer les statistiques
                total_messages = len(messages)
                sent_count = sum(1 for msg in messages if msg.direction == MessageDirection.SENT)
                received_count = sum(1 for msg in messages if msg.direction == MessageDirection.RECEIVED)
                
                # Dates de premier et dernier message
                if messages:
                    sorted_messages = sorted(messages, key=lambda m: m.timestamp or datetime.min)
                    first_date = sorted_messages[0].timestamp
                    last_date = sorted_messages[-1].timestamp
                else:
                    first_date = None
                    last_date = None
                
                # Détecter le numéro de téléphone depuis le nom du fichier
                phone_number = ""
                filename = file_path.stem
                phone_match = re.search(r'[\+\d\s\(\)\-]+', filename)
                if phone_match:
                    phone_number = phone_match.group().strip()
                
                # Créer l'objet Contact
                contact = Contact(
                    phone_number=phone_number,
                    display_name=contact_name,
                    message_count=total_messages,
                    sent_count=sent_count,
                    received_count=received_count,
                    first_message_date=first_date,
                    last_message_date=last_date,
                    media_count=self._count_media_types(messages)
                )
                
                contacts.append(contact)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error extracting contacts from {file_path}: {e}")
            return []
    
    def _count_media_types(self, messages: List[Message]) -> Dict[str, int]:
        """Compter les types de médias dans les messages"""
        media_counts = {}
        
        for message in messages:
            media_type = message.media_type.value
            media_counts[media_type] = media_counts.get(media_type, 0) + 1
        
        return media_counts
    
    def _extract_contact_name(self, soup: BeautifulSoup, file_path: Path) -> str:
        """Extraire le nom du contact"""
        # Essayer d'abord depuis le H3
        h3_element = soup.find('h3')
        if h3_element:
            contact_name = h3_element.get_text(strip=True)
            if contact_name:
                return contact_name
        
        # Fallback: utiliser le nom du fichier
        return file_path.stem
    
    def _extract_messages(self, soup: BeautifulSoup, contact_name: str) -> List[Message]:
        """Extraire les messages du HTML"""
        messages = []
        
        # Trouver tous les éléments de message et de date
        content_div = soup.find('div', class_='content')
        if not content_div:
            logger.warning("No content div found")
            return messages
        
        # Parser les éléments séquentiellement
        current_date = None
        
        for element in content_div.find_all(['p']):
            # Vérifier si c'est une date
            if self._is_date_element(element):
                current_date = self._parse_date_element(element)
                continue
            
            # Vérifier si c'est un message
            message = self._parse_message_element(element, contact_name, current_date)
            if message:
                messages.append(message)
        
        return messages
    
    def _is_date_element(self, element) -> bool:
        """Vérifier si l'élément est une date"""
        if not element.get('class'):
            return False
        
        classes = element.get('class', [])
        if 'date' in classes:
            return True
        
        # Vérifier le contenu pour des patterns de date
        text = element.get_text(strip=True)
        if re.match(r'\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}', text):
            return True
        
        return False
    
    def _parse_date_element(self, element) -> Optional[datetime]:
        """Parser un élément de date"""
        try:
            text = element.get_text(strip=True)
            
            # Pattern: 2025/03/17 16:29
            date_match = re.search(r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})', text)
            if date_match:
                date_str = date_match.group(1)
                return datetime.strptime(date_str, '%Y/%m/%d %H:%M')
            
            return None
            
        except Exception as e:
            logger.debug(f"Error parsing date element: {e}")
            return None
    
    def _parse_message_element(self, element, contact_name: str, current_date: Optional[datetime]) -> Optional[Message]:
        """Parser un élément de message"""
        try:
            classes = element.get('class', [])
            
            # Vérifier si c'est un message
            message_classes = [
                'triangle-isosceles',    # Messages reçus
                'triangle-isosceles2',   # Messages envoyés (vert)
                'triangle-isosceles3',   # Messages envoyés (bleu)
                'triangle-isosceles-map', # Messages avec carte (reçus)
                'triangle-isosceles-map2', # Messages avec carte (envoyés)
                'triangle-isosceles-map3', # Messages avec carte (envoyés)
            ]
            
            if not any(cls in classes for cls in message_classes):
                return None
            
            # Déterminer la direction
            direction = self._determine_direction(classes)
            
            # Extraire le contenu
            content = self._extract_message_content(element)
            
            if not content:
                return None
            
            # Déterminer le type de média
            media_type, media_info = self._detect_media_type(content, element)
            
            # Créer l'objet message
            message = Message(
                id=self._generate_message_id(content, current_date),
                direction=direction,
                content=content,
                timestamp=current_date,
                media_type=media_type,
                media_path=media_info.get('path') if media_info else None,
                media_filename=media_info.get('filename') if media_info else None,
                metadata={
                    'contact_name': contact_name,
                    'classes': classes,
                    'media_info': media_info
                }
            )
            
            return message
            
        except Exception as e:
            logger.debug(f"Error parsing message element: {e}")
            return None
    
    def _determine_direction(self, classes: List[str]) -> MessageDirection:
        """Déterminer la direction du message basée sur les classes CSS"""
        # Messages reçus (gris)
        if any(cls in classes for cls in ['triangle-isosceles', 'triangle-isosceles-map']):
            return MessageDirection.RECEIVED
        
        # Messages envoyés (vert/bleu)
        if any(cls in classes for cls in ['triangle-isosceles2', 'triangle-isosceles3', 
                                         'triangle-isosceles-map2', 'triangle-isosceles-map3']):
            return MessageDirection.SENT
        
        return MessageDirection.UNKNOWN
    
    def _extract_message_content(self, element) -> str:
        """Extraire le contenu du message"""
        # Obtenir tout le texte, en excluant les images
        content = element.get_text(strip=True)
        
        # Nettoyer le contenu
        content = content.replace('\n', ' ').replace('\r', '').strip()
        
        return content
    
    def _detect_media_type(self, content: str, element) -> Tuple[MediaType, Optional[Dict[str, str]]]:
        """Détecter le type de média dans le message"""
        media_info = None
        
        # Vérifier les images dans l'élément
        images = element.find_all_next('img', limit=3)  # Chercher images suivantes
        if images:
            for img in images:
                src = img.get('src', '')
                if 'ExportMedia' in src:
                    media_info = {
                        'type': 'image',
                        'path': src,
                        'filename': Path(src).name if src else None
                    }
                    return MediaType.IMAGE, media_info
        
        # Détecter par le contenu textuel
        content_lower = content.lower()
        
        # Messages audio
        if any(indicator in content_lower for indicator in ['audio', 'voice', 'vocal', '🎵', '🎤']):
            return MediaType.AUDIO, {'type': 'audio', 'detected_from': 'content'}
        
        # Messages vidéo
        if any(indicator in content_lower for indicator in ['video', 'vidéo', '🎥', '📹']):
            return MediaType.VIDEO, {'type': 'video', 'detected_from': 'content'}
        
        # Documents
        if any(indicator in content_lower for indicator in ['document', 'fichier', 'pdf', 'doc', '📄', '📁']):
            return MediaType.DOCUMENT, {'type': 'document', 'detected_from': 'content'}
        
        # Messages avec emojis ou stickers
        if any(indicator in content for indicator in ['👍', '❤️', '😀', '😂']):
            if len(content) <= 10:  # Probablement un sticker/emoji seul
                return MediaType.STICKER, {'type': 'sticker', 'detected_from': 'emoji'}
        
        return MediaType.TEXT, media_info
    
    def _generate_message_id(self, content: str, timestamp: Optional[datetime]) -> str:
        """Générer un ID unique pour le message"""
        import hashlib
        
        # Créer un ID basé sur le contenu et le timestamp
        id_source = f"{content}_{timestamp.isoformat() if timestamp else 'no_time'}"
        return hashlib.md5(id_source.encode('utf-8')).hexdigest()[:12]


# Alias pour la compatibilité
WhatsAppMobileTransParser = MobileTransParser