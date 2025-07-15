import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger('whatsapp_extractor')

class UnifiedRegistry:
    """
    Registre unifié qui remplace les 5 registres séparés.
    Une seule source de vérité pour tout l'état de l'application.
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.registry_path = os.path.join(output_dir, '.unified_registry.json')
        self.data = self._load()
        self._cache = {}  # Cache pour les hash
        
    def _load(self) -> Dict:
        """Charge le registre ou crée une structure vide"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Migration si ancienne version
                    if data.get('version', '1.0') < '2.0':
                        logger.info("Migration du registre vers la version 2.0")
                        data = self._migrate_registry(data)
                    return data
            except Exception as e:
                logger.error(f"Erreur chargement registre: {str(e)}")
        
        # Structure par défaut v2.0
        return {
            'version': '2.0',
            'created': datetime.now().isoformat(),
            'contacts': {},      # Info par contact
            'files': {},         # Tous les fichiers par hash de contenu
            'transcriptions': {}, # Mapping hash → texte transcrit
            'super_files': {},   # Info sur les super fichiers créés
            'processing_stats': {
                'total_files': 0,
                'total_transcriptions': 0,
                'last_run': None
            }
        }
    
    def save(self):
        """Sauvegarde atomique du registre"""
        temp_path = f"{self.registry_path}.tmp"
        try:
            # Mise à jour des stats
            self.data['processing_stats']['last_run'] = datetime.now().isoformat()
            
            # Écriture atomique
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            # Remplacement atomique
            if os.path.exists(self.registry_path):
                os.replace(temp_path, self.registry_path)
            else:
                os.rename(temp_path, self.registry_path)
                
            logger.debug("Registre sauvegardé avec succès")
        except Exception as e:
            logger.error(f"Erreur sauvegarde registre: {str(e)}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def get_file_hash(self, file_path: str) -> str:
        """Calcule le hash SHA256 d'un fichier avec cache"""
        # Vérifier le cache
        if file_path in self._cache:
            return self._cache[file_path]
        
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for block in iter(lambda: f.read(65536), b''):
                    sha256.update(block)
            
            file_hash = sha256.hexdigest()
            self._cache[file_path] = file_hash
            return file_hash
        except Exception as e:
            logger.error(f"Erreur calcul hash pour {file_path}: {str(e)}")
            return None
    
    def register_file(self, file_path: str, file_type: str, direction: str, 
                     contact: str, metadata: Dict = None) -> str:
        """
        Enregistre un fichier dans le registre
        
        Args:
            file_path: Chemin du fichier
            file_type: Type (audio, image, video, text)
            direction: Direction (sent, received)
            contact: Nom du contact
            metadata: Métadonnées additionnelles
            
        Returns:
            Hash du fichier
        """
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return None
        
        # Enregistrer le fichier
        self.data['files'][file_hash] = {
            'path': file_path,
            'type': file_type,
            'direction': direction,
            'contact': contact,
            'size': os.path.getsize(file_path),
            'registered_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        # Enregistrer dans le contact
        if contact not in self.data['contacts']:
            self.data['contacts'][contact] = {
                'files': [],
                'stats': {
                    'total_messages': 0,
                    'received_messages': 0,
                    'sent_messages': 0,
                    'audio_files': 0,
                    'transcribed_files': 0
                }
            }
        
        if file_hash not in self.data['contacts'][contact]['files']:
            self.data['contacts'][contact]['files'].append(file_hash)
            
        # Mise à jour des stats
        self.data['contacts'][contact]['stats']['total_messages'] += 1
        if direction == 'received':
            self.data['contacts'][contact]['stats']['received_messages'] += 1
        else:
            self.data['contacts'][contact]['stats']['sent_messages'] += 1
            
        if file_type == 'audio':
            self.data['contacts'][contact]['stats']['audio_files'] += 1
        
        self.data['processing_stats']['total_files'] += 1
        
        logger.debug(f"Fichier enregistré: {os.path.basename(file_path)} ({file_hash[:8]}...)")
        return file_hash
    
    def is_file_processed(self, file_path: str, process_type: str = 'registered') -> bool:
        """Vérifie si un fichier a déjà été traité"""
        file_hash = self.get_file_hash(file_path)
        if not file_hash:
            return False
        
        if file_hash not in self.data['files']:
            return False
        
        file_info = self.data['files'][file_hash]
        
        if process_type == 'registered':
            return True
        elif process_type == 'converted':
            return 'converted_path' in file_info
        elif process_type == 'transcribed':
            return file_hash in self.data['transcriptions']
        
        return False
    
    def register_conversion(self, original_hash: str, converted_path: str):
        """Enregistre une conversion audio"""
        if original_hash in self.data['files']:
            self.data['files'][original_hash]['converted_path'] = converted_path
            self.data['files'][original_hash]['converted_at'] = datetime.now().isoformat()
            logger.debug(f"Conversion enregistrée: {original_hash[:8]}...")
    
    def register_transcription(self, file_hash: str, transcription: str):
        """Enregistre une transcription"""
        self.data['transcriptions'][file_hash] = {
            'text': transcription,
            'transcribed_at': datetime.now().isoformat(),
            'length': len(transcription)
        }
        
        # Mise à jour des stats du contact
        if file_hash in self.data['files']:
            contact = self.data['files'][file_hash]['contact']
            if contact in self.data['contacts']:
                self.data['contacts'][contact]['stats']['transcribed_files'] += 1
        
        self.data['processing_stats']['total_transcriptions'] += 1
        logger.debug(f"Transcription enregistrée: {file_hash[:8]}... ({len(transcription)} caractères)")
    
    def get_transcription(self, file_hash: str) -> Optional[str]:
        """Récupère une transcription par hash"""
        if file_hash in self.data['transcriptions']:
            return self.data['transcriptions'][file_hash]['text']
        return None
    
    def register_super_file(self, contact: str, period: str, direction: str, 
                           file_path: str, source_hashes: List[str]):
        """Enregistre un super fichier créé"""
        key = f"{contact}_{direction}_{period}"
        
        self.data['super_files'][key] = {
            'path': file_path,
            'period': period,
            'direction': direction,
            'contact': contact,
            'source_files': source_hashes,
            'created_at': datetime.now().isoformat(),
            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
        
        logger.debug(f"Super fichier enregistré: {key}")
    
    def get_super_file_info(self, contact: str, period: str, direction: str) -> Optional[Dict]:
        """Récupère les infos d'un super fichier"""
        key = f"{contact}_{direction}_{period}"
        return self.data['super_files'].get(key)
    
    def needs_super_file_update(self, contact: str, period: str, direction: str, 
                               current_files: List[str]) -> bool:
        """Vérifie si un super fichier doit être mis à jour"""
        info = self.get_super_file_info(contact, period, direction)
        if not info:
            return True  # Pas de super fichier, il faut le créer
        
        # Calculer les hash des fichiers actuels
        current_hashes = set()
        for file_path in current_files:
            file_hash = self.get_file_hash(file_path)
            if file_hash:
                current_hashes.add(file_hash)
        
        # Comparer avec les fichiers sources du super fichier
        existing_hashes = set(info['source_files'])
        
        # Si de nouveaux fichiers sont présents, mise à jour nécessaire
        return current_hashes != existing_hashes
    
    def get_files_by_criteria(self, contact: str = None, direction: str = None, 
                             file_type: str = None) -> List[Dict]:
        """Récupère les fichiers selon des critères"""
        results = []
        
        for file_hash, file_info in self.data['files'].items():
            if contact and file_info['contact'] != contact:
                continue
            if direction and file_info['direction'] != direction:
                continue
            if file_type and file_info['type'] != file_type:
                continue
            
            results.append({
                'hash': file_hash,
                **file_info
            })
        
        return results
    
    def get_stats(self) -> Dict:
        """Récupère les statistiques globales"""
        return {
            'global': self.data['processing_stats'],
            'contacts': {
                contact: info['stats'] 
                for contact, info in self.data['contacts'].items()
            }
        }
    
    def _migrate_registry(self, old_data: Dict) -> Dict:
        """Migre un ancien registre vers le nouveau format"""
        # TODO: Implémenter la migration depuis l'ancien format
        logger.warning("Migration non implémentée, création d'un nouveau registre")
        return self._load()  # Retourne une structure vide pour l'instant