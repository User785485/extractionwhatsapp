import os
import hashlib
import logging
import json
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('whatsapp_extractor')

def setup_logging(config):
    """Configure le système de journalisation
    
    Version ultra robuste, compatible avec la classe Config personnalisée.
    Utilise une approche défensive avec plusieurs méthodes de fallback.
    
    Args:
        config: Objet de configuration (Config personnalisé ou ConfigParser)
        
    Returns:
        Logger configuré
    """
    # DIAGNOSTIC - Début - Imprimons quelques informations utiles
    print("-" * 60)
    print(f"DEBUG INFO - setup_logging a reçu un objet de type: {type(config).__name__}")
    print(f"DEBUG INFO - Méthodes disponibles: {[m for m in dir(config) if not m.startswith('_')]}")
    print("-" * 60)
    
    # Initialisation du logger rapidement pour pouvoir logger les erreurs
    logger = logging.getLogger('whatsapp_extractor')
    logger.setLevel(logging.DEBUG)
    
    # Nettoyer les handlers existants pour éviter les doublons
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Format des logs - identique dans tous les cas
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console - toujours disponible
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Détermination du répertoire de logs avec une stratégie à toute épreuve
    logs_dir = None
    
    try:
        # STRATÉGIE 1: Utiliser get() directement - pour la classe Config personnalisée
        # La classe Config personnalisée utilise une API différente de ConfigParser
        print("DIAGNOSTIC: Essai de la méthode get() directement")
        for section in ['Paths', 'PATHS', 'paths', 'Path']:
            if logs_dir is not None:
                break
            for key in ['logs_dir', 'logs', 'log_dir', 'log']:
                try:
                    # La classe Config personnalisée utilise probablement get(section, key)
                    potential_dir = config.get(section, key)
                    print(f"DIAGNOSTIC: get('{section}', '{key}') a retourné: {potential_dir}")
                    if potential_dir and isinstance(potential_dir, str) and potential_dir.strip():
                        logs_dir = potential_dir.strip()
                        print(f"DIAGNOSTIC: Valeur valide trouvée: {logs_dir}")
                        break
                except Exception as e:
                    print(f"DIAGNOSTIC: get('{section}', '{key}') a échoué: {str(e)}")
                    continue
    except Exception as e:
        print(f"DIAGNOSTIC: Stratégie 1 a complètement échoué: {str(e)}")
    
    # Si la stratégie 1 échoue, essayer d'autres méthodes
    if logs_dir is None:
        try:
            # STRATÉGIE 2: Accéder à l'attribut config.config si disponible
            print("DIAGNOSTIC: Essai d'accès via config.config")
            if hasattr(config, 'config') and hasattr(config.config, 'get'):
                print("DIAGNOSTIC: config.config.get() détecté")
                try:
                    logs_dir = config.config.get('Paths', 'logs_dir')
                    print(f"DIAGNOSTIC: config.config.get() a retourné: {logs_dir}")
                except Exception as e:
                    print(f"DIAGNOSTIC: config.config.get() a échoué: {str(e)}")
        except Exception as e:
            print(f"DIAGNOSTIC: Stratégie 2 a complètement échoué: {str(e)}")
    
    # Si toujours pas de logs_dir, utiliser la valeur par défaut
    if not logs_dir:
        # Créer un dossier 'logs' dans le répertoire courant
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
        print(f"DIAGNOSTIC: Utilisation du répertoire de logs par défaut: {logs_dir}")
    
    # Normaliser le chemin et s'assurer qu'il existe
    logs_dir = os.path.normpath(os.path.abspath(logs_dir))
    print(f"DIAGNOSTIC: Répertoire de logs final: {logs_dir}")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Nom du fichier log avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f'whatsapp_extractor_{timestamp}.log')
    
    # File handler - maintenant que nous avons un chemin valide
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        print(f"DIAGNOSTIC: Fichier log créé: {log_file}")
    except Exception as e:
        # Si la création du fichier de log échoue, on continue avec juste la console
        print(f"DIAGNOSTIC: Impossible de créer le fichier log: {str(e)}")
    
    return logger

def get_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calcule le hash d'un fichier
    
    Args:
        file_path: Chemin du fichier
        algorithm: Algorithme de hash ('sha256' ou 'md5')
    
    Returns:
        Hash hexadécimal ou None si erreur
    """
    try:
        if algorithm == 'md5':
            hasher = hashlib.md5()
        else:
            hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Erreur calcul hash pour {file_path}: {str(e)}")
        return None

def sanitize_filename(filename: str) -> str:
    """Nettoie un nom de fichier pour le système"""
    # Remplacer les caractères interdits
    forbidden_chars = '<>:"/\\|?*'
    for char in forbidden_chars:
        filename = filename.replace(char, '_')
    
    # Supprimer les espaces multiples
    filename = re.sub(r'\s+', ' ', filename)
    
    # Supprimer les espaces en début/fin
    filename = filename.strip()
    
    # Limiter la longueur
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200] + ext
    
    return filename

def get_file_size(file_path: str) -> int:
    """Obtient la taille d'un fichier en octets"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def format_size(size_bytes: int) -> str:
    """Formate une taille en octets en chaîne lisible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def extract_date_from_filename(filename: str) -> str:
    """
    Extrait une date d'un nom de fichier
    
    Returns:
        Date au format YYYY-MM-DD ou chaîne vide
    """
    # Patterns de date courants
    patterns = [
        r'(\d{4})[_-](\d{2})[_-](\d{2})',  # YYYY-MM-DD ou YYYY_MM_DD
        r'(\d{2})[_-](\d{2})[_-](\d{4})',  # DD-MM-YYYY ou DD_MM_YYYY
        r'(\d{8})',                         # YYYYMMDD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            if len(match.groups()) == 3:
                year, month, day = match.groups()
                if len(year) == 2:
                    year = f"20{year}"
                return f"{year}-{month}-{day}"
            elif len(match.groups()) == 1:
                # Format YYYYMMDD
                date_str = match.group(1)
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    
    return ""

def load_json_file(file_path: str) -> dict:
    """Charge un fichier JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Erreur chargement JSON {file_path}: {str(e)}")
        return {}

def save_json_file(data: dict, file_path: str):
    """Sauvegarde des données en JSON"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Erreur sauvegarde JSON {file_path}: {str(e)}")

def check_disk_space(path: str, required_gb: float = 1.0) -> tuple:
    """
    Vérifie l'espace disque disponible
    
    Returns:
        Tuple (has_enough_space, free_space_gb)
    """
    try:
        import shutil
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024 ** 3)
        return free_gb >= required_gb, free_gb
    except:
        return True, 0.0

def create_backup(file_path: str) -> str:
    """Crée une sauvegarde d'un fichier"""
    if not os.path.exists(file_path):
        return ""
    
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        logger.error(f"Erreur création backup: {str(e)}")
        return ""

# Garder la compatibilité avec l'ancien code
def load_registry(registry_file: str) -> dict:
    """Fonction de compatibilité pour charger un registre"""
    return load_json_file(registry_file)

def save_registry(registry: dict, registry_file: str):
    """Fonction de compatibilité pour sauvegarder un registre"""
    save_json_file(registry, registry_file)