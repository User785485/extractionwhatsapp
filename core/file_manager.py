import os
import shutil
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger('whatsapp_extractor')

class FileManager:
    """
    Gestionnaire centralisé des fichiers avec organisation claire
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.ensure_directory_structure()
    
    def ensure_directory_structure(self):
        """Crée la structure de base des répertoires"""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'logs'), exist_ok=True)
    
    def setup_contact_directory(self, contact: str) -> Dict[str, str]:
        """
        Crée la structure complète pour un contact
        
        Returns:
            Dictionnaire des chemins créés
        """
        # Nettoyer le nom du contact pour le système de fichiers
        safe_contact = self.sanitize_filename(contact)
        contact_dir = os.path.join(self.output_dir, safe_contact)
        
        # Structure des répertoires
        paths = {
            'root': contact_dir,
            'media_received': os.path.join(contact_dir, 'media_recus'),
            'media_sent': os.path.join(contact_dir, 'media_envoyes'),
            'audio_mp3': os.path.join(contact_dir, 'audio_mp3'),
            'super_files': os.path.join(contact_dir, 'SUPER_FICHIERS'),
            'transcriptions': os.path.join(contact_dir, 'transcriptions'),
            'exports': os.path.join(contact_dir, 'exports')
        }
        
        # Créer tous les répertoires
        for path in paths.values():
            os.makedirs(path, exist_ok=True)
        
        # Créer les sous-répertoires pour chaque type de média
        for media_dir in ['media_received', 'media_sent']:
            for media_type in ['audio', 'images', 'videos', 'documents']:
                sub_path = os.path.join(paths[media_dir], media_type)
                os.makedirs(sub_path, exist_ok=True)
        
        logger.debug(f"Structure créée pour {contact}")
        return paths
    
    def copy_media_file(self, source_path: str, contact: str, media_type: str, 
                       direction: str, prefix: str = None) -> Optional[str]:
        """
        Copie un fichier média avec organisation et préfixe
        
        Args:
            source_path: Chemin source du fichier
            contact: Nom du contact
            media_type: Type de média (audio, image, video, document)
            direction: Direction (sent, received)
            prefix: Préfixe optionnel (sinon utilise sent_/received_)
            
        Returns:
            Chemin de destination ou None si échec
        """
        if not os.path.exists(source_path):
            logger.warning(f"Fichier source introuvable: {source_path}")
            return None
        
        # Déterminer le répertoire de destination
        paths = self.setup_contact_directory(contact)
        if direction == 'sent':
            base_dir = os.path.join(paths['media_sent'], media_type)
        else:
            base_dir = os.path.join(paths['media_received'], media_type)
        
        # Générer le nom de fichier avec préfixe
        original_name = os.path.basename(source_path)
        if not prefix:
            from .classifier import MessageClassifier
            prefix = MessageClassifier.get_file_prefix(direction)
        
        # Ajouter la date si pas déjà présente
        if not any(char.isdigit() for char in original_name[:10]):
            date_str = datetime.now().strftime('%Y-%m-%d_')
            new_name = f"{prefix}{date_str}{original_name}"
        else:
            new_name = f"{prefix}{original_name}"
        
        dest_path = os.path.join(base_dir, new_name)
        
        # Éviter les écrasements
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(new_name)
            counter = 1
            while os.path.exists(dest_path):
                new_name = f"{base}_{counter}{ext}"
                dest_path = os.path.join(base_dir, new_name)
                counter += 1
        
        # Copier le fichier
        try:
            shutil.copy2(source_path, dest_path)
            logger.debug(f"Fichier copié: {original_name} → {new_name}")
            return dest_path
        except Exception as e:
            logger.error(f"Erreur copie fichier: {str(e)}")
            return None
    
    def get_audio_files(self, contact: str, direction: str = None) -> List[str]:
        """
        Récupère tous les fichiers audio d'un contact
        
        Args:
            contact: Nom du contact
            direction: 'sent', 'received' ou None pour tous
            
        Returns:
            Liste des chemins de fichiers audio
        """
        audio_files = []
        paths = self.setup_contact_directory(contact)
        
        # Extensions audio supportées
        audio_extensions = {'.opus', '.mp3', '.ogg', '.m4a', '.wav', '.aac', '.flac'}
        
        # Déterminer les répertoires à scanner
        if direction == 'sent':
            scan_dirs = [os.path.join(paths['media_sent'], 'audio')]
        elif direction == 'received':
            scan_dirs = [os.path.join(paths['media_received'], 'audio')]
        else:
            scan_dirs = [
                os.path.join(paths['media_sent'], 'audio'),
                os.path.join(paths['media_received'], 'audio')
            ]
        
        # Scanner les répertoires
        for scan_dir in scan_dirs:
            if os.path.exists(scan_dir):
                for file in os.listdir(scan_dir):
                    if os.path.splitext(file)[1].lower() in audio_extensions:
                        audio_files.append(os.path.join(scan_dir, file))
        
        # Trier par nom (qui contient la date)
        audio_files.sort()
        
        logger.debug(f"Trouvé {len(audio_files)} fichiers audio pour {contact} ({direction or 'tous'})")
        return audio_files
    
    def get_mp3_files(self, contact: str, direction: str = None) -> List[str]:
        """Récupère les fichiers MP3 convertis"""
        mp3_files = []
        paths = self.setup_contact_directory(contact)
        mp3_dir = paths['audio_mp3']
        
        if os.path.exists(mp3_dir):
            for file in os.listdir(mp3_dir):
                if file.endswith('.mp3'):
                    # Filtrer par direction si spécifiée
                    if direction:
                        from .classifier import MessageClassifier
                        file_direction = MessageClassifier.classify_by_filename(file)
                        if file_direction != direction:
                            continue
                    
                    mp3_files.append(os.path.join(mp3_dir, file))
        
        mp3_files.sort()
        return mp3_files
    
    def get_super_files(self, contact: str, direction: str = None) -> List[Tuple[str, str]]:
        """
        Récupère les super fichiers avec leur période
        
        Returns:
            Liste de tuples (chemin_fichier, période)
        """
        import logging
        logger = logging.getLogger('whatsapp_extractor')
        logger.info("DIAGNOSTIC: get_super_files appelé pour contact %s, direction %s" % (contact, direction))
        super_files = []
        paths = self.setup_contact_directory(contact)
        super_dir = paths['super_files']
        
        if os.path.exists(super_dir):
            for file in os.listdir(super_dir):
                if file.endswith('.mp3'):
                    # Extraire la période du nom
                    # Format attendu: received_2025-04.mp3 ou sent_2025-04.mp3
                    parts = file.replace('.mp3', '').split('_')
                    if len(parts) >= 2:
                        file_direction = parts[0]
                        period = parts[1] if len(parts) > 1 else 'unknown'
                        
                        # Filtrer par direction si spécifiée
                        if direction and file_direction != direction:
                            continue
                        
                        file_path = os.path.join(super_dir, file)
                        super_files.append((file_path, period))
        
        # Trier par période
        super_files.sort(key=lambda x: x[1])
        logger.info("DIAGNOSTIC: get_super_files retourne %d fichiers" % len(super_files))
        for sf_path, period in super_files:
            logger.info("DIAGNOSTIC: Retourne super fichier: %s" % os.path.basename(sf_path))
        return super_files
    
    def sanitize_filename(self, filename: str) -> str:
        """Nettoie nom de fichier pour 100% compatibilite Windows"""
        import re
        import hashlib
        
        # Garder plus de caractères: lettres, chiffres, tirets, espaces
        clean = re.sub(r'[^a-zA-Z0-9\-_ ]', '_', filename)
        
        # AUGMENTER la limite à 100 caractères (au lieu de 20)
        clean = clean[:100].strip()
        
        # Si vide après nettoyage, générer un nom
        if not clean or clean == '_':
            import time
            clean = f"contact_{int(time.time()) % 10000}"
        
        # Retourner le nom sans hash qui écrase tout
        return clean
    
    def extract_period_from_filename(self, filename: str) -> str:
        """
        Extrait la période d'un nom de fichier
        
        Returns:
            Période au format YYYY-MM ou 'unknown'
        """
        import re
        
        # Chercher un pattern de date YYYY-MM
        date_pattern = re.compile(r'(\d{4})[-_](\d{2})')
        match = date_pattern.search(filename)
        
        if match:
            year, month = match.groups()
            return f"{year}-{month}"
        
        # Si pas de date dans le nom, utiliser la date de modification
        try:
            if os.path.exists(filename):
                mtime = os.path.getmtime(filename)
                return datetime.fromtimestamp(mtime).strftime('%Y-%m')
        except:
            pass
        
        return 'unknown'
    
    def group_files_by_period(self, files: List[str]) -> Dict[str, List[str]]:
        """
        Groupe les fichiers par période (mois)
        
        Returns:
            Dictionnaire {période: [fichiers]}
        """
        groups = {}
        
        for file_path in files:
            period = self.extract_period_from_filename(file_path)
            
            if period not in groups:
                groups[period] = []
            groups[period].append(file_path)
        
        # Trier les fichiers dans chaque groupe
        for period in groups:
            groups[period].sort()
        
        return groups
    
    def get_file_info(self, file_path: str) -> Dict:
        """Récupère les informations d'un fichier"""
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'extension': os.path.splitext(file_path)[1].lower()
        }