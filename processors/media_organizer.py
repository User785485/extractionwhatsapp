import os
import logging
from typing import Optional

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class MediaOrganizer:
    """
    Organise les fichiers médias avec une structure claire
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        
        # Logs de diagnostic pour identifier le problème de configuration
        logger.debug(f"[DIAGNOSTIC] MediaOrganizer init - Type de config: {type(config).__name__}")
        logger.debug(f"[DIAGNOSTIC] MediaOrganizer init - config.sections(): {config.sections() if hasattr(config, 'sections') else 'pas de méthode sections'}")
        
        # Récupérer le chemin media_dir avec traçabilité
        try:
            self.media_dir = config.get('Paths', 'media_dir')
            logger.debug(f"[DIAGNOSTIC] MediaOrganizer init - media_dir: {self.media_dir if self.media_dir is not None else 'NONE'}")
        except Exception as e:
            logger.error(f"[DIAGNOSTIC] Erreur lors de la récupération de media_dir: {str(e)}")
            self.media_dir = None
    
    def organize_media_file(self, original_path: str, filename: str, 
                           contact: str, media_type: str, direction: str) -> Optional[str]:
        """
        Organise un fichier média dans la bonne structure
        
        Args:
            original_path: Chemin original du fichier
            filename: Nom du fichier
            contact: Nom du contact
            media_type: Type de média (audio, images, videos, documents)
            direction: Direction (sent, received)
            
        Returns:
            Nouveau chemin ou None si échec
        """
        # MODIFICATION: Ignorer complètement les médias envoyés
        if direction == 'sent':
            logger.debug(f"Média envoyé ignoré: {filename} (contact: {contact})")
            return None
            
        # Chercher le fichier dans différents emplacements
        source_path = self._find_media_file(original_path, filename)
        
        if not source_path:
            logger.warning(f"Média introuvable: {filename}")
            self._create_missing_placeholder(contact, media_type, direction, filename)
            return None
        
        # Copier avec organisation (uniquement pour les médias reçus)
        new_path = self.file_manager.copy_media_file(
            source_path, contact, media_type, direction
        )
        
        if new_path:
            logger.info(f"Média organisé: {filename} → {os.path.basename(new_path)}")
        
        return new_path
    
    def _find_media_file(self, original_path: str, filename: str) -> Optional[str]:
        """Cherche un fichier média dans plusieurs emplacements"""
        # Log pour identifier l'état de media_dir
        logger.debug(f"[DIAGNOSTIC] _find_media_file - media_dir: {self.media_dir if self.media_dir is not None else 'NONE'}")
        logger.debug(f"[DIAGNOSTIC] _find_media_file - original_path: {original_path}")
        logger.debug(f"[DIAGNOSTIC] _find_media_file - filename: {filename}")
        
        # Liste des chemins possibles avec gestion de None
        possible_paths = [
            original_path,  # Chemin exact depuis le HTML
        ]
        
        # Ajouter le chemin du répertoire média principal seulement s'il est défini
        if self.media_dir is not None:
            possible_paths.append(os.path.join(self.media_dir, filename))  # Répertoire média principal
        else:
            logger.warning(f"[DIAGNOSTIC] media_dir est None, impossible de chercher dans le répertoire média principal")
        
        # Ajouter les sous-répertoires possibles si media_dir est défini
        if self.media_dir is not None:
            for subdir in ['videos', 'images', 'audio', 'documents']:
                possible_paths.append(os.path.join(self.media_dir, subdir, filename))
        
        # Tester chaque chemin
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _create_missing_placeholder(self, contact: str, media_type: str, 
                                   direction: str, filename: str):
        """Crée un fichier placeholder pour un média manquant"""
        paths = self.file_manager.setup_contact_directory(contact)
        
        if direction == 'sent':
            base_dir = os.path.join(paths['media_sent'], media_type)
        else:
            base_dir = os.path.join(paths['media_received'], media_type)
        
        placeholder_file = os.path.join(base_dir, f"{filename}.missing")
        
        try:
            with open(placeholder_file, 'w', encoding='utf-8') as f:
                f.write(f"Fichier média manquant: {filename}\n")
                f.write(f"Type: {media_type}\n")
                f.write(f"Direction: {direction}\n")
                f.write(f"Contact: {contact}\n")
        except Exception as e:
            logger.error(f"Erreur création placeholder: {str(e)}")
            
    def organize_media(self, conversations, media_dir):
        """Organise tous les fichiers médias mentionnés dans les conversations
        
        Args:
            conversations: Dictionnaire des conversations par contact
            media_dir: Répertoire contenant les fichiers médias
        """
        # Utiliser le media_dir passé en argument s'il existe
        # Sinon, utiliser celui de l'objet (défini dans le constructeur)
        if media_dir and os.path.exists(media_dir):
            self.media_dir = media_dir
            logger.debug(f"[DIAGNOSTIC] organize_media - Nouveau media_dir: {self.media_dir}")
        
        if not self.media_dir or not os.path.exists(self.media_dir):
            logger.error(f"Répertoire média introuvable: {self.media_dir}")
            return
            
        logger.info(f"Organisation des fichiers médias depuis: {self.media_dir}")
        count = {'total': 0, 'success': 0, 'missing': 0}
        
        # Parcourir toutes les conversations
        for contact, messages in conversations.items():
            for message in messages:
                # Traiter les médias attachés
                attachments = message.get('attachments', [])
                for attachment in attachments:
                    count['total'] += 1
                    
                    filename = attachment.get('filename')
                    if not filename:
                        continue
                        
                    # Déterminer le type de média
                    media_type = 'documents'  # Par défaut
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        media_type = 'images'
                    elif ext in ['.mp4', '.avi', '.mov', '.webm']:
                        media_type = 'videos'
                    elif ext in ['.mp3', '.ogg', '.wav', '.opus', '.m4a']:
                        media_type = 'audio'
                    
                    # Organiser selon la direction
                    direction = message.get('direction', 'received')
                    original_path = attachment.get('path', '')
                    
                    result = self.organize_media_file(original_path, filename, contact, media_type, direction)
                    
                    if result:
                        count['success'] += 1
                    else:
                        count['missing'] += 1
                        
        # Résumé
        logger.info(f"Organisation médias terminée: {count['success']}/{count['total']} fichiers traités")
        if count['missing'] > 0:
            logger.warning(f"Fichiers médias non trouvés: {count['missing']}")
            logger.warning(f"Placeholders créés dans le répertoire de sortie")
            
        # Mise à jour du registre
        self.registry.save()