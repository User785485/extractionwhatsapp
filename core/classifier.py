import logging
from typing import Tuple, Optional

logger = logging.getLogger('whatsapp_extractor')

class MessageClassifier:
    """
    Classificateur centralisé pour déterminer la direction des messages.
    Une seule logique utilisée partout dans l'application.
    """
    
    # Mapping des classes CSS vers les directions
    CSS_MAPPING = {
        # Messages REÇUS (fond gris)
        'triangle-isosceles': 'received',
        'triangle-isosceles-map': 'received',
        
        # Messages ENVOYÉS (fond vert/bleu)
        'triangle-isosceles2': 'sent',
        'triangle-isosceles3': 'sent',
        'triangle-isosceles-map2': 'sent',
        'triangle-isosceles-map3': 'sent'
    }
    
    @classmethod
    def classify_by_css(cls, css_class: str) -> str:
        """
        Classifie un message selon sa classe CSS
        
        Args:
            css_class: Classe CSS de l'élément HTML
            
        Returns:
            'sent' ou 'received'
        """
        direction = cls.CSS_MAPPING.get(css_class, None)
        
        if direction:
            logger.debug(f"Classification CSS: {css_class} → {direction}")
            return direction
        
        # Si classe inconnue, essayer de deviner
        if css_class and ('2' in css_class or '3' in css_class):
            logger.warning(f"Classe CSS inconnue '{css_class}', supposée envoyée")
            return 'sent'
        
        logger.warning(f"Classe CSS inconnue '{css_class}', supposée reçue")
        return 'received'
    
    @classmethod
    def classify_by_position(cls, element_str: str) -> str:
        """
        Classification de secours basée sur la position
        
        Args:
            element_str: Représentation string de l'élément HTML
            
        Returns:
            'sent' ou 'received'
        """
        # Les messages envoyés sont généralement décalés à droite
        if 'left:170px' in element_str or 'left:208px' in element_str:
            logger.debug("Classification par position: envoyé (décalé à droite)")
            return 'sent'
        
        logger.debug("Classification par position: reçu (aligné à gauche)")
        return 'received'
    
    @classmethod
    def classify_by_filename(cls, filename: str) -> Optional[str]:
        """
        Classifie selon le préfixe du nom de fichier
        
        Args:
            filename: Nom du fichier
            
        Returns:
            'sent', 'received' ou None si pas de préfixe
        """
        filename_lower = filename.lower()
        
        if filename_lower.startswith('received_'):
            return 'received'
        elif filename_lower.startswith('sent_'):
            return 'sent'
        
        return None
    
    @classmethod
    def classify_by_path(cls, file_path: str) -> Optional[str]:
        """
        Classifie selon le chemin du fichier
        
        Args:
            file_path: Chemin complet du fichier
            
        Returns:
            'sent', 'received' ou None si indéterminé
        """
        path_lower = file_path.lower()
        
        if 'media_recus' in path_lower or 'received' in path_lower:
            return 'received'
        elif 'media_envoyes' in path_lower or 'sent' in path_lower:
            return 'sent'
        
        return None
    
    @classmethod
    def get_file_prefix(cls, direction: str) -> str:
        """
        Retourne le préfixe à utiliser pour un fichier
        
        Args:
            direction: 'sent' ou 'received'
            
        Returns:
            Préfixe approprié
        """
        if direction == 'sent':
            return 'sent_'
        elif direction == 'received':
            return 'received_'
        else:
            logger.warning(f"Direction inconnue '{direction}', utilisation de 'unknown_'")
            return 'unknown_'
    
    @classmethod
    def validate_direction(cls, direction: str) -> bool:
        """Valide qu'une direction est correcte"""
        return direction in ['sent', 'received']
    
    @classmethod
    def classify_message(cls, css_class: str = None, element_str: str = None, 
                        file_path: str = None) -> Tuple[str, str]:
        """
        Méthode principale de classification avec plusieurs stratégies
        
        Args:
            css_class: Classe CSS de l'élément
            element_str: Représentation string de l'élément  
            file_path: Chemin du fichier (pour les médias)
            
        Returns:
            Tuple (direction, méthode_utilisée)
        """
        # 1. Essayer par classe CSS (le plus fiable)
        if css_class:
            direction = cls.classify_by_css(css_class)
            return direction, 'css'
        
        # 2. Essayer par chemin de fichier
        if file_path:
            # D'abord par le nom
            direction = cls.classify_by_filename(os.path.basename(file_path))
            if direction:
                return direction, 'filename'
            
            # Puis par le chemin
            direction = cls.classify_by_path(file_path)
            if direction:
                return direction, 'path'
        
        # 3. Essayer par position (moins fiable)
        if element_str:
            direction = cls.classify_by_position(element_str)
            return direction, 'position'
        
        # 4. Par défaut, considérer comme reçu
        logger.warning("Aucune méthode de classification n'a fonctionné, défaut: received")
        return 'received', 'default'

# Import pour la méthode classify_by_filename
import os