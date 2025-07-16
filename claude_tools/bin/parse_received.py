#!/usr/bin/env python3
"""
Parse WhatsApp HTML - Extract ONLY received messages
Optimized for Claude's workflow
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
import argparse

class ReceivedMessageParser:
    """Parser spécialisé pour messages reçus uniquement"""
    
    def __init__(self):
        self.supported_formats = {
            'mobiletrans': self._parse_mobiletrans,
            'whatsapp_web': self._parse_whatsapp_web,
            'auto': self._auto_detect_and_parse
        }
        
    def parse_file(self, file_path: Path, format_type: str = 'auto') -> Dict:
        """Parse un fichier HTML et retourne UNIQUEMENT les messages reçus"""
        
        if not file_path.exists():
            return {'error': f'File not found: {file_path}'}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Utiliser le bon parser
            parser_func = self.supported_formats.get(format_type, self._auto_detect_and_parse)
            return parser_func(soup, file_path)
            
        except Exception as e:
            return {'error': f'Parse error: {str(e)}', 'file': str(file_path)}
    
    def _auto_detect_and_parse(self, soup: BeautifulSoup, file_path: Path) -> Dict:
        """Détection automatique du format"""
        
        # Détection MobileTrans
        if soup.find('div', class_='chat-box'):
            return self._parse_mobiletrans(soup, file_path)
            
        # Détection WhatsApp Web Export
        if soup.find('div', class_='message-in'):
            return self._parse_whatsapp_web(soup, file_path)
            
        # Format inconnu - essayer MobileTrans par défaut
        return self._parse_mobiletrans(soup, file_path)
    
    def _parse_mobiletrans(self, soup: BeautifulSoup, file_path: Path) -> Dict:
        """Parser pour format MobileTrans"""
        
        # Extraire le nom du contact
        contact_name = file_path.stem
        
        # Chercher les messages reçus (triangles à gauche)
        received_messages = []
        
        # Messages avec classe triangle-isosceles (sans suffixe = reçus)
        left_messages = soup.find_all('p', class_='triangle-isosceles')
        
        for msg_div in left_messages:
            message_data = self._extract_message_data(msg_div, 'mobiletrans')
            if message_data:
                received_messages.append(message_data)
        
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
    
    def _parse_whatsapp_web(self, soup: BeautifulSoup, file_path: Path) -> Dict:
        """Parser pour format WhatsApp Web"""
        
        contact_name = file_path.stem
        received_messages = []
        
        # Messages entrants
        incoming = soup.find_all('div', class_='message-in')
        
        for msg_div in incoming:
            message_data = self._extract_message_data(msg_div, 'whatsapp_web')
            if message_data:
                received_messages.append(message_data)
        
        stats = self._calculate_stats(received_messages)
        
        return {
            'contact': contact_name,
            'file': str(file_path),
            'format': 'whatsapp_web',
            'received_count': len(received_messages),
            'messages': received_messages,
            'stats': stats,
            'parsed_at': datetime.now().isoformat()
        }
    
    def _extract_message_data(self, msg_div, format_type: str) -> Optional[Dict]:
        """Extraire les données d'un message"""
        
        try:
            # Pour ce format, chercher timestamp dans le parent ou éléments précédents
            timestamp = None
            
            # Le timestamp est souvent dans un <p class='date'> précédent
            current = msg_div.previous_sibling
            while current and timestamp is None:
                if hasattr(current, 'get') and current.get('class') == ['date']:
                    date_text = current.get_text(strip=True)
                    timestamp = self._parse_timestamp(date_text)
                    break
                current = current.previous_sibling
            
            # Contenu directement dans le <p>
            content = msg_div.get_text(strip=True)
            
            # Détection média
            media_info = self._detect_media(msg_div)
            
            if not content and not media_info:
                return None
                
            return {
                'timestamp': timestamp,
                'content': content,
                'has_media': bool(media_info),
                'media': media_info,
                'raw_html': str(msg_div)[:200] + '...'  # Pour debug
            }
            
        except Exception as e:
            return None
    
    def _detect_media(self, msg_div) -> Optional[Dict]:
        """Détecter les médias dans le message"""
        
        media_info = None
        
        # Pour ce format MobileTrans, chercher dans le message suivant s'il y a une table
        next_sibling = msg_div.find_next_sibling()
        if next_sibling and next_sibling.name == 'table' and 'triangle-isosceles-map' in str(next_sibling.get('class', [])):
            # C'est une table de média
            link = next_sibling.find('a')
            if link and link.get('href'):
                href = link['href']
                filename = href.split('/')[-1] if '/' in href else href.split('\\')[-1]
                
                # Déterminer le type
                if any(ext in filename.lower() for ext in ['.opus', '.m4a', '.mp3', '.ogg', '.weba', '.aac']):
                    media_type = 'audio'
                elif any(ext in filename.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    media_type = 'image'
                elif any(ext in filename.lower() for ext in ['.mp4', '.avi', '.mov', '.mkv']):
                    media_type = 'video'
                else:
                    media_type = 'file'
                
                media_info = {
                    'type': media_type,
                    'href': href,
                    'filename': filename,
                    'text': link.get_text(strip=True) or filename
                }
        
        # Recherche standard si pas trouvé
        if not media_info:
            # Recherche d'images
            img = msg_div.find('img')
            if img and img.get('src') and 'icon' not in img.get('src', '').lower():
                media_info = {
                    'type': 'image',
                    'src': img['src'],
                    'alt': img.get('alt', '')
                }
            
            # Recherche de liens vers médias
            if not media_info:
                for a in msg_div.find_all('a'):
                    href = a.get('href', '')
                    if any(ext in href.lower() for ext in ['.opus', '.m4a', '.mp3', '.ogg', '.jpg', '.png', '.mp4']):
                        media_info = {
                            'type': 'link',
                            'href': href,
                            'text': a.get_text(strip=True)
                        }
                        break
        
        return media_info
    
    def _parse_timestamp(self, time_str: str) -> Optional[str]:
        """Parser les timestamps avec formats multiples"""
        
        # Nettoyer le texte (enlever tirets décoratifs)
        clean_time = time_str.replace('-', '').strip()
        
        formats = [
            '%Y/%m/%d %H:%M',   # Format 2025/03/17 16:29
            '%Y-%m-%d %H:%M',
            '%d/%m/%Y %H:%M',
            '%m/%d/%Y %H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y, %H:%M',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_time.strip(), fmt)
                return dt.isoformat()
            except:
                continue
                
        return clean_time  # Retourner tel quel si parsing échoue
    
    def _calculate_stats(self, messages: List[Dict]) -> Dict:
        """Calculer statistiques sur les messages"""
        
        if not messages:
            return {}
            
        stats = {
            'total': len(messages),
            'with_media': sum(1 for m in messages if m.get('has_media')),
            'text_only': sum(1 for m in messages if not m.get('has_media')),
            'media_types': {}
        }
        
        # Compter types de médias
        for msg in messages:
            if msg.get('media'):
                media_type = msg['media'].get('type', 'unknown')
                stats['media_types'][media_type] = stats['media_types'].get(media_type, 0) + 1
        
        # Analyser contenu
        all_text = ' '.join(m.get('content', '') for m in messages)
        words = all_text.split()
        
        stats['total_words'] = len(words)
        stats['avg_words_per_message'] = round(len(words) / len(messages), 2) if messages else 0
        
        return stats

def main():
    """CLI pour Claude"""
    
    parser = argparse.ArgumentParser(
        description='Extract ONLY received WhatsApp messages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse single file
  python parse_received.py /path/to/chat.html
  
  # Parse with specific format
  python parse_received.py /path/to/chat.html --format mobiletrans
  
  # Parse multiple files
  python parse_received.py /path/to/chats/*.html -o results.json
  
  # Pretty print results
  python parse_received.py /path/to/chat.html --pretty
        """
    )
    
    parser.add_argument('files', nargs='+', help='HTML files to parse')
    parser.add_argument('-f', '--format', choices=['auto', 'mobiletrans', 'whatsapp_web'], 
                       default='auto', help='HTML format (default: auto-detect)')
    parser.add_argument('-o', '--output', help='Output file (JSON)')
    parser.add_argument('--pretty', action='store_true', help='Pretty print output')
    parser.add_argument('--stats-only', action='store_true', help='Show only statistics')
    
    args = parser.parse_args()
    
    # Parser
    msg_parser = ReceivedMessageParser()
    
    # Résultats
    all_results = []
    total_messages = 0
    
    # Traiter chaque fichier
    for file_pattern in args.files:
        file_path = Path(file_pattern)
        
        if file_path.is_file():
            files = [file_path]
        else:
            # Glob pattern
            files = list(Path('.').glob(file_pattern))
        
        for file in files:
            print(f"\nParsing: {file}")
            result = msg_parser.parse_file(file, args.format)
            
            if 'error' in result:
                print(f"  ERROR: {result['error']}")
            else:
                count = result.get('received_count', 0)
                total_messages += count
                print(f"  Found: {count} received messages")
                
                if args.stats_only and result.get('stats'):
                    print(f"  Stats: {json.dumps(result['stats'], indent=2)}")
                
                all_results.append(result)
    
    # Sauvegarder résultats
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2 if args.pretty else None)
        print(f"\nResults saved to: {output_path}")
    
    # Résumé
    print(f"\n=== SUMMARY ===")
    print(f"Files processed: {len(all_results)}")
    print(f"Total received messages: {total_messages}")
    
    # Pretty print si demandé
    if args.pretty and not args.output:
        print("\n=== RESULTS ===")
        print(json.dumps(all_results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()