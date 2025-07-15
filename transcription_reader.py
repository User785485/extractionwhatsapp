#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TranscriptionReader - Module optimisé pour la lecture des transcriptions stockées dans des fichiers .txt
"""

import os
import re
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger('whatsapp_extractor')

class TranscriptionReader:
    """Lecteur optimisé pour les transcriptions stockées dans les fichiers .txt"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.cache = {}
        self._build_cache()
        
    def _build_cache(self):
        """Construit un cache complet de toutes les transcriptions"""
        logger.info("Construction du cache de transcriptions...")
        
        for contact_dir in Path(self.output_dir).iterdir():
            if not contact_dir.is_dir() or contact_dir.name.startswith('.'):
                continue
                
            trans_dir = contact_dir / 'transcriptions'
            if not trans_dir.exists():
                continue
                
            contact_name = contact_dir.name
            self.cache[contact_name] = {}
            
            for trans_file in trans_dir.glob('*.txt'):
                try:
                    # Extraire l'UUID
                    uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', trans_file.name)
                    if not uuid_match:
                        continue
                        
                    uuid = uuid_match.group(1)
                    
                    # Lire et parser la transcription
                    transcription = self._read_transcription_file(trans_file)
                    if transcription:
                        self.cache[contact_name][uuid] = transcription
                        
                except Exception as e:
                    logger.error(f"Erreur lecture {trans_file}: {e}")
                    
        total = sum(len(uuids) for uuids in self.cache.values())
        logger.info(f"Cache construit: {len(self.cache)} contacts, {total} transcriptions")
        
    def _read_transcription_file(self, file_path: Path) -> Optional[str]:
        """Lit et extrait la transcription d'un fichier"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Trouver le séparateur
            lines = content.split('\n')
            separator_idx = -1
            
            for i, line in enumerate(lines):
                if '=' * 40 in line:
                    separator_idx = i
                    break
                    
            if separator_idx == -1:
                # Pas de séparateur, prendre tout après les 5 premières lignes
                if len(lines) > 5:
                    return '\n'.join(lines[5:]).strip()
            else:
                # Prendre tout après le séparateur
                if separator_idx < len(lines) - 1:
                    return '\n'.join(lines[separator_idx + 1:]).strip()
                    
        except Exception as e:
            logger.error(f"Erreur lecture fichier {file_path}: {e}")
            
        return None
        
    def get_transcription(self, uuid: str, contact: str = None) -> Optional[str]:
        """Récupère une transcription par UUID"""
        # Si on connait le contact, chercher directement
        if contact and contact in self.cache:
            return self.cache[contact].get(uuid)
            
        # Sinon chercher dans tous les contacts
        for contact_cache in self.cache.values():
            if uuid in contact_cache:
                return contact_cache[uuid]
                
        return None
        
    def get_stats(self) -> Dict:
        """Retourne des statistiques sur les transcriptions"""
        stats = {
            'total_contacts': len(self.cache),
            'total_transcriptions': sum(len(uuids) for uuids in self.cache.values()),
            'contacts': {}
        }
        
        for contact, uuids in self.cache.items():
            stats['contacts'][contact] = len(uuids)
            
        return stats
