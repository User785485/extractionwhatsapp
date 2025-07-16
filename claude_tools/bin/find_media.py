#!/usr/bin/env python3
"""
Find and map media files from WhatsApp exports
Intelligent media detection and association
"""

import sys
import json
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
import argparse
from typing import List, Dict, Optional, Tuple
import re

class MediaFinder:
    """Détecteur intelligent de médias WhatsApp"""
    
    # Extensions audio supportées
    AUDIO_EXTENSIONS = {'.opus', '.m4a', '.mp3', '.ogg', '.weba', '.aac', '.wav', '.flac'}
    
    # Extensions image
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Extensions vidéo
    VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.3gp'}
    
    # Patterns de nommage WhatsApp
    WHATSAPP_PATTERNS = {
        'audio': [
            r'PTT-\d{8}-WA\d+',  # Push to talk
            r'AUD-\d{8}-WA\d+',  # Audio messages
            r'AUDIO-\d{4}-\d{2}-\d{2}',
            r'WhatsApp Audio \d{4}-\d{2}-\d{2}',
            r'MSG-\d{8}-\d+',  # Messages vocaux
        ],
        'image': [
            r'IMG-\d{8}-WA\d+',
            r'IMAGE-\d{4}-\d{2}-\d{2}',
            r'WhatsApp Image \d{4}-\d{2}-\d{2}',
        ],
        'video': [
            r'VID-\d{8}-WA\d+',
            r'VIDEO-\d{4}-\d{2}-\d{2}',
            r'WhatsApp Video \d{4}-\d{2}-\d{2}',
        ]
    }
    
    def __init__(self, base_path: Path):
        """
        Args:
            base_path: Chemin de base pour la recherche
        """
        self.base_path = Path(base_path)
        self.media_cache = {}
        
    def find_all_media(self, recursive: bool = True) -> Dict[str, List[Dict]]:
        """Trouver tous les médias dans le dossier"""
        
        results = {
            'audio': [],
            'image': [],
            'video': [],
            'other': []
        }
        
        # Pattern de recherche
        pattern = '**/*' if recursive else '*'
        
        for file_path in self.base_path.glob(pattern):
            if file_path.is_file():
                media_info = self._analyze_file(file_path)
                if media_info:
                    category = media_info['category']
                    results[category].append(media_info)
        
        # Trier par date
        for category in results:
            results[category].sort(key=lambda x: x['modified'], reverse=True)
        
        return results
    
    def find_media_for_contact(self, contact_name: str) -> Dict[str, List[Dict]]:
        """Trouver médias associés à un contact spécifique"""
        
        # Nettoyer le nom du contact
        clean_name = self._clean_contact_name(contact_name)
        
        all_media = self.find_all_media()
        contact_media = {
            'audio': [],
            'image': [],
            'video': [],
            'other': []
        }
        
        # Filtrer par contact
        for category, files in all_media.items():
            for file_info in files:
                if self._match_contact(file_info, clean_name, contact_name):
                    contact_media[category].append(file_info)
        
        return contact_media
    
    def find_audio_files(self, only_voice: bool = True) -> List[Dict]:
        """Trouver spécifiquement les fichiers audio"""
        
        audio_files = []
        
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.AUDIO_EXTENSIONS:
                file_info = self._analyze_file(file_path)
                
                if only_voice and file_info:
                    # Filtrer uniquement les messages vocaux
                    if self._is_voice_message(file_info):
                        audio_files.append(file_info)
                elif file_info:
                    audio_files.append(file_info)
        
        return audio_files
    
    def map_media_to_messages(self, messages: List[Dict], media_folder: Optional[Path] = None) -> List[Dict]:
        """Associer médias aux messages"""
        
        if not media_folder:
            media_folder = self.base_path / 'Media'
        
        # Créer index des médias
        media_index = self._build_media_index(media_folder)
        
        # Enrichir messages avec infos médias
        for msg in messages:
            if msg.get('has_media') and msg.get('media'):
                media_ref = msg['media']
                
                # Essayer de trouver le fichier correspondant
                found_media = self._find_matching_media(media_ref, media_index, msg)
                
                if found_media:
                    msg['media_file'] = found_media
                    msg['media_found'] = True
                else:
                    msg['media_found'] = False
        
        return messages
    
    def _analyze_file(self, file_path: Path) -> Optional[Dict]:
        """Analyser un fichier média"""
        
        try:
            stats = file_path.stat()
            
            # Type MIME
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            # Catégorie
            suffix = file_path.suffix.lower()
            if suffix in self.AUDIO_EXTENSIONS:
                category = 'audio'
            elif suffix in self.IMAGE_EXTENSIONS:
                category = 'image'
            elif suffix in self.VIDEO_EXTENSIONS:
                category = 'video'
            else:
                category = 'other'
            
            # Hash pour identification unique
            file_hash = self._calculate_hash(file_path)
            
            return {
                'path': str(file_path),
                'name': file_path.name,
                'stem': file_path.stem,
                'extension': suffix,
                'category': category,
                'mime_type': mime_type,
                'size': stats.st_size,
                'size_mb': round(stats.st_size / (1024*1024), 2),
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'hash': file_hash,
                'whatsapp_type': self._detect_whatsapp_type(file_path.name),
                'is_voice': self._is_voice_message({'name': file_path.name, 'category': category})
            }
            
        except Exception as e:
            return None
    
    def _calculate_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculer hash MD5 du fichier"""
        
        # Si fichier trop gros, hasher seulement le début
        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read(chunk_size)).hexdigest()[:16]
        
        # Sinon hasher tout
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()[:16]
    
    def _detect_whatsapp_type(self, filename: str) -> Optional[str]:
        """Détecter le type WhatsApp du fichier"""
        
        for media_type, patterns in self.WHATSAPP_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, filename, re.IGNORECASE):
                    return media_type
        return None
    
    def _is_voice_message(self, file_info: Dict) -> bool:
        """Déterminer si c'est un message vocal"""
        
        name = file_info.get('name', '')
        
        # Patterns de messages vocaux
        voice_patterns = [
            r'PTT-',  # Push To Talk
            r'AUD-.*-WA',  # Audio WhatsApp
            r'MSG-.*-\d+',  # Message vocal
            r'voice',
            r'audio.*message',
            r'recording'
        ]
        
        for pattern in voice_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return True
        
        # Vérifier aussi la durée (les messages vocaux sont généralement courts)
        if file_info.get('category') == 'audio' and file_info.get('size_mb', 0) < 5:
            return True
            
        return False
    
    def _clean_contact_name(self, contact: str) -> str:
        """Nettoyer nom de contact pour matching"""
        
        # Enlever caractères spéciaux
        clean = re.sub(r'[^\w\s-]', '', contact)
        # Remplacer espaces par underscores
        clean = clean.replace(' ', '_')
        return clean.lower()
    
    def _match_contact(self, file_info: Dict, clean_contact: str, original_contact: str) -> bool:
        """Vérifier si le fichier correspond au contact"""
        
        file_name = file_info['name'].lower()
        file_path = file_info['path'].lower()
        
        # Matching direct
        if clean_contact in file_name or original_contact.lower() in file_path:
            return True
        
        # Matching partiel (numéro de téléphone)
        phone_match = re.search(r'\+?\d[\d\s-]+', original_contact)
        if phone_match:
            phone = re.sub(r'[\s-]', '', phone_match.group())
            if phone in file_name or phone in file_path:
                return True
        
        return False
    
    def _build_media_index(self, media_folder: Path) -> Dict:
        """Construire index des médias pour recherche rapide"""
        
        index = {
            'by_name': {},
            'by_date': {},
            'by_type': {'audio': [], 'image': [], 'video': [], 'other': []}
        }
        
        if not media_folder.exists():
            return index
        
        for file_path in media_folder.rglob('*'):
            if file_path.is_file():
                info = self._analyze_file(file_path)
                if info:
                    # Index par nom
                    index['by_name'][info['stem']] = info
                    
                    # Index par type
                    index['by_type'][info['category']].append(info)
                    
                    # Index par date (extraire date du nom si possible)
                    date_match = re.search(r'(\d{4})-?(\d{2})-?(\d{2})', info['name'])
                    if date_match:
                        date_key = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                        if date_key not in index['by_date']:
                            index['by_date'][date_key] = []
                        index['by_date'][date_key].append(info)
        
        return index
    
    def _find_matching_media(self, media_ref: Dict, index: Dict, message: Dict) -> Optional[Dict]:
        """Trouver le média correspondant dans l'index"""
        
        # Essayer par nom direct
        if 'text' in media_ref:
            stem = Path(media_ref['text']).stem
            if stem in index['by_name']:
                return index['by_name'][stem]
        
        # Essayer par timestamp du message
        if message.get('timestamp'):
            try:
                msg_date = datetime.fromisoformat(message['timestamp'])
                date_key = msg_date.strftime('%Y-%m-%d')
                
                if date_key in index['by_date']:
                    # Chercher le média le plus proche en temps
                    candidates = index['by_date'][date_key]
                    # Ici on pourrait affiner avec l'heure
                    if candidates:
                        return candidates[0]
            except:
                pass
        
        return None
    
    def generate_report(self, output_path: Optional[Path] = None) -> Dict:
        """Générer rapport complet sur les médias trouvés"""
        
        all_media = self.find_all_media()
        
        report = {
            'scan_date': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'summary': {
                'total_files': sum(len(files) for files in all_media.values()),
                'total_size_mb': sum(sum(f['size_mb'] for f in files) for files in all_media.values()),
                'by_category': {cat: len(files) for cat, files in all_media.items()},
                'voice_messages': sum(1 for files in all_media.values() for f in files if f.get('is_voice'))
            },
            'details': all_media
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report

def main():
    """CLI pour Claude"""
    
    parser = argparse.ArgumentParser(
        description='Find and analyze WhatsApp media files',
        epilog="""
Examples:
  # Find all media in a folder
  python find_media.py /path/to/whatsapp/folder
  
  # Find only audio files
  python find_media.py /path/to/folder --audio-only
  
  # Find media for specific contact
  python find_media.py /path/to/folder --contact "+1 234 567 8900"
  
  # Generate detailed report
  python find_media.py /path/to/folder --report media_report.json
        """
    )
    
    parser.add_argument('path', help='Path to WhatsApp folder')
    parser.add_argument('--audio-only', action='store_true', help='Find only audio files')
    parser.add_argument('--voice-only', action='store_true', help='Find only voice messages')
    parser.add_argument('--contact', help='Find media for specific contact')
    parser.add_argument('--report', help='Generate detailed report (JSON)')
    parser.add_argument('--map-messages', help='JSON file with messages to map media')
    
    args = parser.parse_args()
    
    # Finder
    finder = MediaFinder(Path(args.path))
    
    # Opération demandée
    if args.audio_only or args.voice_only:
        print(f"Searching for {'voice messages' if args.voice_only else 'audio files'}...")
        audio_files = finder.find_audio_files(only_voice=args.voice_only)
        
        print(f"\nFound {len(audio_files)} files:")
        for f in audio_files:
            print(f"  - {f['name']} ({f['size_mb']} MB)")
        
        if args.report:
            with open(args.report, 'w') as f:
                json.dump(audio_files, f, indent=2)
    
    elif args.contact:
        print(f"Searching media for contact: {args.contact}")
        contact_media = finder.find_media_for_contact(args.contact)
        
        for category, files in contact_media.items():
            if files:
                print(f"\n{category.upper()}: {len(files)} files")
                for f in files[:5]:  # Montrer seulement 5 premiers
                    print(f"  - {f['name']}")
    
    elif args.map_messages:
        print("Mapping media to messages...")
        with open(args.map_messages, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        enriched = finder.map_media_to_messages(messages)
        
        found = sum(1 for m in enriched if m.get('media_found'))
        print(f"Mapped {found}/{len(enriched)} messages to media files")
        
        # Sauvegarder résultat enrichi
        output = Path(args.map_messages).stem + '_with_media.json'
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(enriched, f, indent=2)
    
    else:
        # Scan complet
        print(f"Scanning: {args.path}")
        report = finder.generate_report(Path(args.report) if args.report else None)
        
        print(f"\n=== MEDIA SUMMARY ===")
        print(f"Total files: {report['summary']['total_files']}")
        print(f"Total size: {report['summary']['total_size_mb']:.1f} MB")
        print(f"Voice messages: {report['summary']['voice_messages']}")
        
        print(f"\nBy category:")
        for cat, count in report['summary']['by_category'].items():
            print(f"  {cat}: {count}")
        
        if args.report:
            print(f"\nDetailed report saved to: {args.report}")

if __name__ == "__main__":
    main()