#!/usr/bin/env python3
"""
Parser amélioré pour WhatsApp HTML - Détecte TOUS les messages y compris audio autonomes
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import argparse

class AdvancedMessageParser:
    """Parser avancé pour tous types de messages WhatsApp"""
    
    def __init__(self):
        self.messages = []
        self.current_timestamp = None
        
    def parse_file(self, file_path: Path) -> Dict:
        """Parse un fichier HTML complet"""
        
        if not file_path.exists():
            return {'error': f'File not found: {file_path}'}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            return self._parse_mobiletrans_format(soup, file_path)
            
        except Exception as e:
            return {'error': f'Parse error: {str(e)}', 'file': str(file_path)}
    
    def _parse_mobiletrans_format(self, soup: BeautifulSoup, file_path: Path) -> Dict:
        """Parser pour format MobileTrans avec audio autonomes"""
        
        contact_name = file_path.stem
        received_messages = []
        
        # Parcourir tous les éléments dans l'ordre
        content_div = soup.find('div', class_='content')
        if not content_div:
            return {'error': 'No content div found'}
            
        current_timestamp = None
        
        # Parcourir tous les enfants directs
        for element in content_div.find_all(recursive=False):
            
            # Capturer le timestamp
            if element.name == 'p' and 'date' in element.get('class', []):
                date_text = element.get_text(strip=True)
                current_timestamp = self._parse_timestamp(date_text)
                
            # Message texte reçu (triangle-isosceles sans suffixe)
            elif element.name == 'p' and element.get('class') == ['triangle-isosceles']:
                content = element.get_text(strip=True)
                if content:
                    received_messages.append({
                        'timestamp': current_timestamp,
                        'content': content,
                        'has_media': False,
                        'media': None,
                        'type': 'text_received',
                        'raw_html': str(element)[:200] + '...'
                    })
                    
            # Table avec audio reçu (triangle-isosceles-map sans suffixe)
            elif element.name == 'table' and element.get('class') == ['triangle-isosceles-map']:
                media_info = self._extract_media_from_table(element)
                if media_info:
                    received_messages.append({
                        'timestamp': current_timestamp,
                        'content': '',  # Pas de texte pour audio autonome
                        'has_media': True,
                        'media': media_info,
                        'type': 'audio_received',
                        'raw_html': str(element)[:200] + '...'
                    })
                    
        # Statistiques
        stats = self._calculate_stats(received_messages)
        
        return {
            'contact': contact_name,
            'file': str(file_path),
            'format': 'mobiletrans',
            'received_count': len(received_messages),
            'messages': received_messages,
            'stats': stats,
            'parsed_at': datetime.now().isoformat()
        }
    
    def _extract_media_from_table(self, table_element) -> Optional[Dict]:
        """Extraire les infos média d'une table"""
        
        try:
            # Chercher le lien
            link = table_element.find('a')
            if link and link.get('href'):
                href = link['href']
                
                # Extraire le nom du fichier
                filename = href.split('\\')[-1] if '\\' in href else href.split('/')[-1]
                
                # Texte affiché (peut être différent du nom de fichier)
                display_text = table_element.find('font')
                if display_text:
                    display_text = display_text.get_text(strip=True)
                else:
                    display_text = filename
                    
                # Déterminer le type
                if any(ext in filename.lower() for ext in ['.opus', '.m4a', '.mp3', '.ogg', '.weba', '.aac']):
                    media_type = 'audio'
                elif any(ext in filename.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    media_type = 'image'
                elif any(ext in filename.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv']):
                    media_type = 'video'
                else:
                    media_type = 'file'
                    
                return {
                    'type': media_type,
                    'href': href,
                    'filename': filename,
                    'display_text': display_text
                }
                
        except Exception as e:
            print(f"Error extracting media: {e}")
            
        return None
    
    def _parse_timestamp(self, time_str: str) -> Optional[str]:
        """Parser les timestamps"""
        
        # Nettoyer le texte
        clean_time = re.sub(r'-+', '', time_str).strip()
        
        formats = [
            '%Y/%m/%d %H:%M',
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M',
            '%m/%d/%Y %H:%M',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_time, fmt)
                return dt.isoformat()
            except:
                continue
                
        return clean_time
    
    def _calculate_stats(self, messages: List[Dict]) -> Dict:
        """Calculer statistiques détaillées"""
        
        if not messages:
            return {}
            
        stats = {
            'total': len(messages),
            'text_only': sum(1 for m in messages if not m.get('has_media')),
            'with_media': sum(1 for m in messages if m.get('has_media')),
            'audio_messages': sum(1 for m in messages if m.get('type') == 'audio_received'),
            'text_messages': sum(1 for m in messages if m.get('type') == 'text_received'),
            'media_types': {}
        }
        
        # Compter types de médias
        for msg in messages:
            if msg.get('media'):
                media_type = msg['media'].get('type', 'unknown')
                stats['media_types'][media_type] = stats['media_types'].get(media_type, 0) + 1
        
        # Analyser contenu texte
        text_messages = [m for m in messages if m.get('content')]
        if text_messages:
            all_text = ' '.join(m.get('content', '') for m in text_messages)
            words = all_text.split()
            stats['total_words'] = len(words)
            stats['avg_words_per_text_message'] = round(len(words) / len(text_messages), 2)
        else:
            stats['total_words'] = 0
            stats['avg_words_per_text_message'] = 0
            
        return stats

def main():
    """CLI principal"""
    
    parser = argparse.ArgumentParser(
        description='Extract ALL received WhatsApp messages including standalone audio'
    )
    
    parser.add_argument('file', help='HTML file to parse')
    parser.add_argument('-o', '--output', help='Output file (JSON)')
    parser.add_argument('--pretty', action='store_true', help='Pretty print output')
    
    args = parser.parse_args()
    
    # Parser
    msg_parser = AdvancedMessageParser()
    
    # Traiter le fichier
    file_path = Path(args.file)
    print(f"\nParsing: {file_path}")
    
    result = msg_parser.parse_file(file_path)
    
    if 'error' in result:
        print(f"  ERROR: {result['error']}")
        sys.exit(1)
    else:
        total = result.get('received_count', 0)
        audio = result['stats'].get('audio_messages', 0)
        text = result['stats'].get('text_messages', 0)
        
        print(f"  Found: {total} received messages")
        print(f"    - Text messages: {text}")
        print(f"    - Audio messages: {audio}")
        
    # Sauvegarder résultats
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2 if args.pretty else None)
        print(f"\nResults saved to: {output_path}")
    
    # Afficher si pas de sortie
    if not args.output or args.pretty:
        print("\n=== RESULTS ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()