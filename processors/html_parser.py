import os
import re
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from core import MessageClassifier, UnifiedRegistry, FileManager
from processors.media_organizer import MediaOrganizer

logger = logging.getLogger('whatsapp_extractor')

class HTMLParser:
    """
    Parser HTML optimisé avec classification immédiate
    Basé sur extractor.py mais corrigé et simplifié
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.classifier = MessageClassifier()
        
        # Récupération robuste des chemins
        self.html_dir = None
        self.media_dir = None
        self.output_dir = None
        
        # Stratégie 1: Utiliser get_paths() si disponible
        if hasattr(config, 'get_paths'):
            try:
                paths = config.get_paths()
                self.html_dir = paths.get('html_dir')
                self.media_dir = paths.get('media_dir')
                self.output_dir = paths.get('output_dir')
                logger.debug("Chemins récupérés via get_paths() dans HTMLParser")
            except Exception as e:
                logger.debug(f"Erreur lors de l'utilisation de get_paths() dans HTMLParser: {e}")
        
        # Stratégie 2: Essayer toutes les variations de casse
        for path_name, current_value in [
            ('html_dir', self.html_dir),
            ('media_dir', self.media_dir),
            ('output_dir', self.output_dir)
        ]:
            if not current_value:
                for section in ['PATHS', 'Paths', 'paths']:
                    try:
                        path_value = config.get(section, path_name)
                        if path_value:
                            if path_name == 'html_dir':
                                self.html_dir = path_value
                            elif path_name == 'media_dir':
                                self.media_dir = path_value
                            elif path_name == 'output_dir':
                                self.output_dir = path_value
                            logger.debug(f"{path_name} récupéré via section '{section}' dans HTMLParser")
                            break
                    except Exception:
                        continue
        
        # Vérification finale
        if not self.html_dir:
            logger.error("ERREUR: html_dir est None dans HTMLParser!")
        if not self.media_dir:
            logger.error("ERREUR: media_dir est None dans HTMLParser!")
        if not self.output_dir:
            logger.error("ERREUR: output_dir est None dans HTMLParser!")
    
    def parse_all_conversations(self, incremental: bool = True) -> Dict[str, List[Dict]]:
        """
        Parse tous les fichiers HTML et retourne les conversations
        
        Args:
            incremental: Si True, ne traite que les fichiers modifiés
            
        Returns:
            Dict {contact: [messages]}
        """
        conversations = {}
        html_files = self._get_html_files()
        
        if not html_files:
            logger.warning(f"Aucun fichier HTML trouvé dans {self.html_dir}")
            return conversations
        
        logger.info(f"Fichiers HTML trouvés: {len(html_files)}")
        
        for i, html_file in enumerate(html_files):
            # Vérifier si déjà traité en mode incrémental
            file_hash = self.registry.get_file_hash(html_file)
            
            if incremental and self.registry.is_file_processed(html_file, 'registered'):
                # Vérifier si le fichier a changé
                stored_info = self.registry.data['files'].get(file_hash, {})
                if stored_info.get('source_hash') == file_hash:
                    logger.info(f"Fichier déjà traité et inchangé: {os.path.basename(html_file)}")
                    
                    # Charger les conversations depuis le cache
                    contact = stored_info.get('contact')
                    if contact:
                        cached_msgs = self._load_cached_conversation(contact)
                        if cached_msgs:
                            conversations[contact] = cached_msgs
                            continue
            
            # Parser le fichier
            logger.info(f"Traitement [{i+1}/{len(html_files)}]: {os.path.basename(html_file)}")
            contact, messages = self.parse_html_file(html_file)
            
            if contact and messages:
                conversations[contact] = messages
                
                # Enregistrer dans le registre
                self.registry.register_file(
                    html_file, 
                    'html', 
                    'source',
                    contact,
                    {'source_hash': file_hash, 'message_count': len(messages)}
                )
        
        # Sauvegarder le registre
        self.registry.save()
        
        return conversations
    
    def parse_html_file(self, html_file: str) -> Tuple[str, List[Dict]]:
        """
        Parse un fichier HTML individuel
        
        Returns:
            Tuple (nom_contact, liste_messages)
        """
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extraire le nom du contact
            contact_name = self._extract_contact_name(soup)
            if not contact_name:
                logger.warning(f"Impossible d'extraire le nom du contact de {html_file}")
                return None, []
            
            logger.info(f"Contact extrait: {contact_name}")
            
            # Créer la structure pour ce contact
            paths = self.file_manager.setup_contact_directory(contact_name)
            
            # Extraire les messages
            messages = self._extract_messages(soup, contact_name)
            
            # Sauvegarder la conversation en JSON pour cache
            self._save_conversation_json(contact_name, messages)
            
            # Créer le fichier texte de conversation
            self._create_conversation_text(contact_name, messages)
            
            return contact_name, messages
            
        except Exception as e:
            logger.error(f"Erreur parsing {html_file}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None, []
    
    def _extract_contact_name(self, soup: BeautifulSoup) -> str:
        """Extrait le nom du contact depuis le HTML"""
        # Essayer d'abord le h3
        h3_tag = soup.find('h3')
        if h3_tag and h3_tag.text.strip():
            return self.file_manager.sanitize_filename(h3_tag.text.strip())
        
        # Sinon essayer le titre
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.replace("'s WhatsApp Business", "").replace("'s WhatsApp", "")
            return self.file_manager.sanitize_filename(title.strip())
        
        return "Contact_Inconnu"
    
    def _extract_messages(self, soup: BeautifulSoup, contact_name: str) -> List[Dict]:
        """Extrait tous les messages du HTML"""
        messages = []
        
        # Trouver tous les blocs de date
        date_headers = soup.find_all('p', class_='date')
        
        for date_header in date_headers:
            # Extraire la date
            date_text = date_header.find('font', color='#b4b4b4')
            if not date_text:
                continue
            
            # Parser la date (format: 2025/04/13 21:06)
            date_match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2})', date_text.text)
            if not date_match:
                continue
            
            full_date = date_match.group(1)
            date_parts = full_date.split(' ')
            message_date = date_parts[0]
            message_time = date_parts[1] if len(date_parts) > 1 else "00:00"
            
            # Trouver le message suivant cette date
            next_element = date_header.find_next_sibling(['p', 'table'])
            if not next_element:
                continue
            
            # Classifier le message
            css_class = next_element.get('class', [''])[0]
            direction, method = self.classifier.classify_message(
                css_class=css_class,
                element_str=str(next_element)
            )
            
            logger.debug(f"Message classifié: {css_class} → {direction} (méthode: {method})")
            
            # Extraire le contenu selon le type d'élément
            if next_element.name == 'p':
                # Message texte
                message = self._extract_text_message(
                    next_element, message_date, message_time, direction
                )
            else:  # table
                # Message avec média
                message = self._extract_media_message(
                    next_element, message_date, message_time, direction, contact_name
                )
            
            if message:
                messages.append(message)
                
                # Enregistrer dans le registre si c'est un média
                if message['type'] != 'text' and message['media_path']:
                    self.registry.register_file(
                        message['media_path'],
                        message['type'],
                        direction,
                        contact_name,
                        {
                            'original_name': message.get('original_name', ''),
                            'date': message_date,
                            'time': message_time
                        }
                    )
        
        return messages
    
    def _extract_text_message(self, element, date: str, time: str, direction: str) -> Dict:
        """Extrait un message texte"""
        # Chercher le contenu
        font_tag = element.find('font')
        if font_tag:
            content = font_tag.text
        else:
            content = element.text
        
        return {
            'date': date,
            'time': time,
            'direction': direction,
            'type': 'text',
            'content': content.strip() if content else '',
            'media_path': None
        }
    
    def _extract_media_message(self, element, date: str, time: str, 
                              direction: str, contact_name: str) -> Dict:
        """Extrait un message avec média"""
        # Initialisation du message avec les métadonnées de base
        message = {
            'date': date,
            'time': time,
            'direction': direction,
            'type': 'unknown',  # Sera mis à jour plus tard
            'content': '',
            'media_path': None
        }
        
        # Extraction du chemin du média
        media_element = element.find('a', href=True)
        original_path = media_element['href'] if media_element else ''
        
        # Si un média est trouvé
        if original_path:
            filename = os.path.basename(original_path)
            message['original_name'] = filename
            
            # Déterminer le type de média
            ext = os.path.splitext(filename)[1].lower()
            message['type'] = self._get_media_type(ext)
            
            # Logs de diagnostic pour l'objet config et le chemin media_dir
            logger.debug(f"[DIAGNOSTIC] HTMLParser avant MediaOrganizer - Type de config: {type(self.config).__name__}")
            if hasattr(self.config, 'sections'):
                logger.debug(f"[DIAGNOSTIC] HTMLParser avant MediaOrganizer - config.sections(): {self.config.sections()}")
            try:
                media_dir_value = self.config.get('Paths', 'media_dir') if hasattr(self.config, 'get') else None
                logger.debug(f"[DIAGNOSTIC] HTMLParser avant MediaOrganizer - media_dir dans config: {media_dir_value if media_dir_value else 'NONE'}")
            except Exception as e:
                logger.error(f"[DIAGNOSTIC] HTMLParser - Erreur accès media_dir: {str(e)}")
            
            # Copier le média avec organisation
            media_organizer = MediaOrganizer(self.config, self.registry, self.file_manager)
            logger.debug(f"[DIAGNOSTIC] HTMLParser - MediaOrganizer créé avec media_dir={media_organizer.media_dir if hasattr(media_organizer, 'media_dir') else 'NONE'}")
            new_path = media_organizer.organize_media_file(
                original_path, filename, contact_name, message['type'], direction
            )
            
            if new_path:
                message['media_path'] = new_path
            else:
                logger.warning(f"Média non trouvé: {filename}")
        
        # Extraire le texte de description si présent
        td_tag = element.find('td', width='150')
        if td_tag:
            message['content'] = td_tag.text.strip()
        
        return message
    
    def _get_media_type(self, extension: str) -> str:
        """Détermine le type de média selon l'extension"""
        ext = extension.lower()
        
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff']:
            return 'images'
        elif ext in ['.mp4', '.avi', '.mov', '.webm', '.mkv', '.3gp', '.flv']:
            return 'videos'
        elif ext in ['.opus', '.mp3', '.ogg', '.m4a', '.wav', '.aac', '.flac']:
            return 'audio'
        else:
            return 'documents'
    
    def _get_html_files(self) -> List[str]:
        """Récupère la liste des fichiers HTML à traiter"""
        html_files = []
        
        if os.path.exists(self.html_dir):
            for file in os.listdir(self.html_dir):
                if file.endswith('.html'):
                    html_files.append(os.path.join(self.html_dir, file))
        
        html_files = sorted(html_files)
        
        # Appliquer la limite si définie
        if hasattr(self, 'test_limit') and self.test_limit:
            logger.info(f"Mode test: limitation à {self.test_limit} fichiers HTML")
            html_files = html_files[:self.test_limit]
        
        return html_files
    
    def _save_conversation_json(self, contact: str, messages: List[Dict]):
        """Sauvegarde la conversation en JSON pour cache"""
        import json
        
        contact_dir = os.path.join(self.output_dir, self.file_manager.sanitize_filename(contact))
        json_file = os.path.join(contact_dir, 'conversation.json')
        
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Erreur sauvegarde JSON pour {contact}: {str(e)}")
    
    def _load_cached_conversation(self, contact: str) -> List[Dict]:
        """Charge une conversation depuis le cache JSON"""
        import json
        
        contact_dir = os.path.join(self.output_dir, self.file_manager.sanitize_filename(contact))
        json_file = os.path.join(contact_dir, 'conversation.json')
        
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return []
    
    def _create_conversation_text(self, contact: str, messages: List[Dict]):
        """Crée un fichier texte de la conversation"""
        contact_dir = os.path.join(self.output_dir, self.file_manager.sanitize_filename(contact))
        text_file = os.path.join(contact_dir, f"{contact}_conversation.txt")
        
        try:
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"===== CONVERSATION AVEC {contact} =====\n\n")
                
                current_date = None
                for msg in sorted(messages, key=lambda m: (m['date'], m['time'])):
                    # Séparateur de date
                    if current_date != msg['date']:
                        current_date = msg['date']
                        f.write(f"\n[{current_date}]\n{'=' * (len(current_date) + 2)}\n\n")
                    
                    # Direction
                    direction_symbol = "→" if msg['direction'] == 'sent' else "←"
                    
                    # Contenu
                    content = msg['content']
                    if msg['type'] != 'text' and msg['media_path']:
                        content += f" [Média: {os.path.basename(msg['media_path'])}]"
                    
                    f.write(f"{msg['time']} {direction_symbol} {content}\n")
                    
        except Exception as e:
            logger.error(f"Erreur création fichier conversation: {str(e)}")