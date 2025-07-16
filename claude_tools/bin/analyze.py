#!/usr/bin/env python3
"""
WhatsApp data analyzer and report generator
Multi-format reports optimized for Claude
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import argparse
from typing import List, Dict, Optional, Any
import re
import statistics

class WhatsAppAnalyzer:
    """Analyseur et générateur de rapports pour données WhatsApp"""
    
    def __init__(self):
        self.emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"   # symbols & pictographs
            "\U0001F680-\U0001F6FF"   # transport & map symbols
            "\U0001F1E0-\U0001F1FF"   # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251]+"
        )
        
    def analyze_messages(self, messages: List[Dict]) -> Dict:
        """Analyser un ensemble de messages"""
        
        if not messages:
            return {'error': 'No messages to analyze'}
        
        # Statistiques de base
        stats = {
            'total_messages': len(messages),
            'date_range': self._get_date_range(messages),
            'contacts': self._analyze_contacts(messages),
            'content': self._analyze_content(messages),
            'media': self._analyze_media(messages),
            'temporal': self._analyze_temporal(messages),
            'transcriptions': self._analyze_transcriptions(messages),
            'patterns': self._analyze_patterns(messages)
        }
        
        return stats
    
    def _get_date_range(self, messages: List[Dict]) -> Dict:
        """Obtenir plage de dates"""
        
        timestamps = []
        for msg in messages:
            if msg.get('timestamp'):
                try:
                    dt = datetime.fromisoformat(msg['timestamp'])
                    timestamps.append(dt)
                except:
                    pass
        
        if not timestamps:
            return {'start': None, 'end': None, 'duration_days': 0}
        
        timestamps.sort()
        
        return {
            'start': timestamps[0].isoformat(),
            'end': timestamps[-1].isoformat(),
            'duration_days': (timestamps[-1] - timestamps[0]).days
        }
    
    def _analyze_contacts(self, messages: List[Dict]) -> Dict:
        """Analyser contacts"""
        
        contact_stats = defaultdict(lambda: {
            'message_count': 0,
            'word_count': 0,
            'media_count': 0,
            'transcription_count': 0,
            'first_message': None,
            'last_message': None
        })
        
        for msg in messages:
            contact = msg.get('contact', 'Unknown')
            stats = contact_stats[contact]
            
            # Compteurs
            stats['message_count'] += 1
            
            if msg.get('content'):
                stats['word_count'] += len(msg['content'].split())
            
            if msg.get('has_media') or msg.get('media'):
                stats['media_count'] += 1
            
            if msg.get('transcription'):
                stats['transcription_count'] += 1
            
            # Dates
            timestamp = msg.get('timestamp')
            if timestamp:
                if not stats['first_message'] or timestamp < stats['first_message']:
                    stats['first_message'] = timestamp
                if not stats['last_message'] or timestamp > stats['last_message']:
                    stats['last_message'] = timestamp
        
        # Top contacts
        sorted_contacts = sorted(
            contact_stats.items(), 
            key=lambda x: x[1]['message_count'], 
            reverse=True
        )
        
        return {
            'total_contacts': len(contact_stats),
            'top_10': [
                {
                    'name': name,
                    **stats,
                    'avg_words_per_message': round(stats['word_count'] / stats['message_count'], 1) if stats['message_count'] else 0
                }
                for name, stats in sorted_contacts[:10]
            ],
            'all': dict(contact_stats)
        }
    
    def _analyze_content(self, messages: List[Dict]) -> Dict:
        """Analyser contenu textuel"""
        
        all_text = []
        word_freq = Counter()
        emoji_freq = Counter()
        message_lengths = []
        
        for msg in messages:
            content = msg.get('content', '')
            if content:
                all_text.append(content)
                message_lengths.append(len(content))
                
                # Mots
                words = content.lower().split()
                word_freq.update(words)
                
                # Emojis
                emojis = self.emoji_pattern.findall(content)
                emoji_freq.update(emojis)
        
        # Statistiques
        total_words = sum(word_freq.values())
        
        return {
            'total_words': total_words,
            'unique_words': len(word_freq),
            'avg_message_length': round(statistics.mean(message_lengths), 1) if message_lengths else 0,
            'top_words': [
                {'word': word, 'count': count}
                for word, count in word_freq.most_common(20)
                if len(word) > 3  # Ignorer mots courts
            ],
            'top_emojis': [
                {'emoji': emoji, 'count': count}
                for emoji, count in emoji_freq.most_common(10)
            ],
            'messages_with_emoji': sum(1 for text in all_text if self.emoji_pattern.search(text)),
            'emoji_percentage': round(
                100 * sum(1 for text in all_text if self.emoji_pattern.search(text)) / len(all_text), 1
            ) if all_text else 0
        }
    
    def _analyze_media(self, messages: List[Dict]) -> Dict:
        """Analyser médias"""
        
        media_types = Counter()
        media_files = []
        
        for msg in messages:
            if msg.get('has_media') or msg.get('media'):
                media_info = msg.get('media', {})
                media_type = media_info.get('type', 'unknown')
                media_types[media_type] += 1
                
                if msg.get('media_file'):
                    media_files.append(msg['media_file'])
        
        return {
            'total_media': sum(media_types.values()),
            'by_type': dict(media_types),
            'media_percentage': round(
                100 * sum(media_types.values()) / len(messages), 1
            ) if messages else 0,
            'unique_files': len(set(media_files))
        }
    
    def _analyze_temporal(self, messages: List[Dict]) -> Dict:
        """Analyser patterns temporels"""
        
        hour_dist = Counter()
        day_dist = Counter()
        month_dist = Counter()
        weekday_dist = Counter()
        
        for msg in messages:
            if msg.get('timestamp'):
                try:
                    dt = datetime.fromisoformat(msg['timestamp'])
                    
                    hour_dist[dt.hour] += 1
                    day_dist[dt.date().isoformat()] += 1
                    month_dist[f"{dt.year}-{dt.month:02d}"] += 1
                    weekday_dist[dt.strftime('%A')] += 1
                    
                except:
                    pass
        
        # Peak times
        peak_hour = hour_dist.most_common(1)[0] if hour_dist else (None, 0)
        peak_day = day_dist.most_common(1)[0] if day_dist else (None, 0)
        
        return {
            'by_hour': dict(hour_dist),
            'by_day': dict(list(day_dist.most_common(30))),  # Top 30 jours
            'by_month': dict(month_dist),
            'by_weekday': dict(weekday_dist),
            'peak_hour': {
                'hour': peak_hour[0],
                'count': peak_hour[1],
                'time_range': f"{peak_hour[0]}:00-{peak_hour[0]}:59" if peak_hour[0] is not None else None
            },
            'peak_day': {
                'date': peak_day[0],
                'count': peak_day[1]
            },
            'messages_per_day': round(
                len(messages) / max((len(day_dist), 1)), 1
            )
        }
    
    def _analyze_transcriptions(self, messages: List[Dict]) -> Dict:
        """Analyser transcriptions audio"""
        
        transcribed = [m for m in messages if m.get('transcription')]
        
        if not transcribed:
            return {
                'total_transcribed': 0,
                'transcription_rate': 0
            }
        
        # Analyser contenu transcrit
        trans_text = ' '.join(m['transcription'] for m in transcribed)
        trans_words = trans_text.split()
        
        # Durée moyenne (estimation basée sur mots)
        avg_words = len(trans_words) / len(transcribed) if transcribed else 0
        estimated_duration = avg_words * 0.4  # ~150 mots/minute
        
        return {
            'total_transcribed': len(transcribed),
            'transcription_rate': round(100 * len(transcribed) / len(messages), 1),
            'total_transcribed_words': len(trans_words),
            'avg_words_per_audio': round(avg_words, 1),
            'estimated_total_duration_minutes': round(estimated_duration * len(transcribed) / 60, 1),
            'languages': self._detect_languages(transcribed)
        }
    
    def _analyze_patterns(self, messages: List[Dict]) -> Dict:
        """Détecter patterns de communication"""
        
        # Questions
        questions = [m for m in messages if '?' in m.get('content', '')]
        
        # Liens
        links = []
        link_pattern = re.compile(r'https?://[^\s]+')
        for msg in messages:
            content = msg.get('content', '')
            found_links = link_pattern.findall(content)
            links.extend(found_links)
        
        # Numéros de téléphone
        phone_pattern = re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}')
        phones = []
        for msg in messages:
            content = msg.get('content', '')
            found_phones = phone_pattern.findall(content)
            phones.extend(found_phones)
        
        return {
            'questions_count': len(questions),
            'questions_percentage': round(100 * len(questions) / len(messages), 1) if messages else 0,
            'links_shared': len(links),
            'unique_links': len(set(links)),
            'phone_numbers_shared': len(phones),
            'unique_phones': len(set(phones))
        }
    
    def _detect_languages(self, messages: List[Dict]) -> Dict:
        """Détecter langues (basique)"""
        
        # Patterns simples pour détecter langues
        lang_patterns = {
            'english': re.compile(r'\b(the|and|is|are|was|were|have|has|will|would)\b', re.I),
            'french': re.compile(r'\b(le|la|les|de|du|des|et|est|sont|avoir|être)\b', re.I),
            'spanish': re.compile(r'\b(el|la|los|las|de|del|y|es|son|estar|tener)\b', re.I),
            'arabic': re.compile(r'[\u0600-\u06FF]+')
        }
        
        lang_counts = Counter()
        
        for msg in messages:
            text = msg.get('transcription', '') or msg.get('content', '')
            if text:
                for lang, pattern in lang_patterns.items():
                    if pattern.search(text):
                        lang_counts[lang] += 1
        
        total = sum(lang_counts.values())
        
        return {
            lang: {
                'count': count,
                'percentage': round(100 * count / total, 1) if total else 0
            }
            for lang, count in lang_counts.items()
        }
    
    def generate_report(self, messages: List[Dict], output_format: str = 'markdown',
                       output_path: Optional[Path] = None) -> str:
        """Générer rapport dans différents formats"""
        
        # Analyser d'abord
        analysis = self.analyze_messages(messages)
        
        if output_format == 'markdown':
            report = self._generate_markdown_report(analysis, messages)
        elif output_format == 'json':
            report = json.dumps(analysis, ensure_ascii=False, indent=2)
        elif output_format == 'csv':
            report = self._generate_csv_report(analysis, messages)
        else:
            report = self._generate_text_report(analysis)
        
        # Sauvegarder si demandé
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
        
        return report
    
    def _generate_markdown_report(self, analysis: Dict, messages: List[Dict]) -> str:
        """Générer rapport Markdown"""
        
        lines = []
        
        # En-tête
        lines.append("# WhatsApp Analysis Report")
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\nTotal messages analyzed: **{analysis['total_messages']}**")
        
        # Date range
        if analysis['date_range']['start']:
            lines.append(f"\n## Date Range")
            lines.append(f"- First message: {analysis['date_range']['start']}")
            lines.append(f"- Last message: {analysis['date_range']['end']}")
            lines.append(f"- Duration: {analysis['date_range']['duration_days']} days")
        
        # Top contacts
        lines.append(f"\n## Top Contacts")
        lines.append(f"Total contacts: **{analysis['contacts']['total_contacts']}**\n")
        
        for i, contact in enumerate(analysis['contacts']['top_10'], 1):
            lines.append(f"{i}. **{contact['name']}**")
            lines.append(f"   - Messages: {contact['message_count']}")
            lines.append(f"   - Words: {contact['word_count']} (avg: {contact['avg_words_per_message']})")
            if contact['media_count']:
                lines.append(f"   - Media: {contact['media_count']}")
            if contact['transcription_count']:
                lines.append(f"   - Audio transcribed: {contact['transcription_count']}")
        
        # Content analysis
        lines.append(f"\n## Content Analysis")
        lines.append(f"- Total words: {analysis['content']['total_words']:,}")
        lines.append(f"- Unique words: {analysis['content']['unique_words']:,}")
        lines.append(f"- Average message length: {analysis['content']['avg_message_length']} chars")
        lines.append(f"- Messages with emoji: {analysis['content']['emoji_percentage']}%")
        
        # Top words
        if analysis['content']['top_words']:
            lines.append(f"\n### Most Frequent Words")
            for word_data in analysis['content']['top_words'][:10]:
                lines.append(f"- {word_data['word']}: {word_data['count']}")
        
        # Top emojis
        if analysis['content']['top_emojis']:
            lines.append(f"\n### Most Used Emojis")
            for emoji_data in analysis['content']['top_emojis']:
                lines.append(f"- {emoji_data['emoji']}: {emoji_data['count']}")
        
        # Media
        if analysis['media']['total_media']:
            lines.append(f"\n## Media Analysis")
            lines.append(f"- Total media: {analysis['media']['total_media']}")
            lines.append(f"- Media percentage: {analysis['media']['media_percentage']}%")
            
            lines.append(f"\n### Media Types")
            for media_type, count in analysis['media']['by_type'].items():
                lines.append(f"- {media_type}: {count}")
        
        # Temporal
        lines.append(f"\n## Temporal Patterns")
        lines.append(f"- Messages per day: {analysis['temporal']['messages_per_day']}")
        if analysis['temporal']['peak_hour']['hour'] is not None:
            lines.append(f"- Peak hour: {analysis['temporal']['peak_hour']['time_range']} ({analysis['temporal']['peak_hour']['count']} messages)")
        if analysis['temporal']['peak_day']['date']:
            lines.append(f"- Most active day: {analysis['temporal']['peak_day']['date']} ({analysis['temporal']['peak_day']['count']} messages)")
        
        # Transcriptions
        if analysis['transcriptions']['total_transcribed']:
            lines.append(f"\n## Audio Transcriptions")
            lines.append(f"- Total transcribed: {analysis['transcriptions']['total_transcribed']}")
            lines.append(f"- Transcription rate: {analysis['transcriptions']['transcription_rate']}%")
            lines.append(f"- Total words transcribed: {analysis['transcriptions']['total_transcribed_words']:,}")
            lines.append(f"- Estimated duration: {analysis['transcriptions']['estimated_total_duration_minutes']} minutes")
        
        # Patterns
        lines.append(f"\n## Communication Patterns")
        lines.append(f"- Questions asked: {analysis['patterns']['questions_count']} ({analysis['patterns']['questions_percentage']}%)")
        lines.append(f"- Links shared: {analysis['patterns']['links_shared']} ({analysis['patterns']['unique_links']} unique)")
        lines.append(f"- Phone numbers shared: {analysis['patterns']['unique_phones']}")
        
        return '\n'.join(lines)
    
    def _generate_csv_report(self, analysis: Dict, messages: List[Dict]) -> str:
        """Générer rapport CSV des messages"""
        
        output = []
        
        # Headers
        headers = ['contact', 'timestamp', 'content', 'has_media', 'media_type', 
                  'transcription', 'word_count']
        output.append(','.join(headers))
        
        # Rows
        for msg in messages:
            row = [
                msg.get('contact', ''),
                msg.get('timestamp', ''),
                f'"{msg.get("content", "").replace(chr(34), chr(34)+chr(34))}"',
                'Yes' if msg.get('has_media') else 'No',
                (msg.get('media') or {}).get('type', ''),
                f'"{msg.get("transcription", "").replace(chr(34), chr(34)+chr(34))}"',
                str(len(msg.get('content', '').split()))
            ]
            output.append(','.join(row))
        
        return '\n'.join(output)
    
    def _generate_text_report(self, analysis: Dict) -> str:
        """Générer rapport texte simple"""
        
        lines = []
        lines.append("=== WHATSAPP ANALYSIS REPORT ===")
        lines.append(f"Generated: {datetime.now()}")
        lines.append(f"\nTotal messages: {analysis['total_messages']}")
        lines.append(f"Total contacts: {analysis['contacts']['total_contacts']}")
        lines.append(f"Date range: {analysis['date_range']['duration_days']} days")
        
        lines.append(f"\nTOP 5 CONTACTS:")
        for i, contact in enumerate(analysis['contacts']['top_10'][:5], 1):
            lines.append(f"{i}. {contact['name']}: {contact['message_count']} messages")
        
        lines.append(f"\nCONTENT STATS:")
        lines.append(f"- Total words: {analysis['content']['total_words']:,}")
        lines.append(f"- Messages with emoji: {analysis['content']['emoji_percentage']}%")
        lines.append(f"- Media files: {analysis['media']['total_media']}")
        
        if analysis['transcriptions']['total_transcribed']:
            lines.append(f"\nTRANSCRIPTIONS:")
            lines.append(f"- Audio transcribed: {analysis['transcriptions']['total_transcribed']}")
            lines.append(f"- Estimated duration: {analysis['transcriptions']['estimated_total_duration_minutes']} min")
        
        return '\n'.join(lines)

def main():
    """CLI pour Claude"""
    
    parser = argparse.ArgumentParser(
        description='Analyze WhatsApp data and generate reports',
        epilog="""
Examples:
  # Analyze parsed messages JSON
  python analyze.py messages.json
  
  # Generate markdown report
  python analyze.py messages.json -f markdown -o report.md
  
  # Generate CSV for further analysis
  python analyze.py messages.json -f csv -o messages.csv
  
  # Quick text summary
  python analyze.py messages.json -f text
        """
    )
    
    parser.add_argument('input', help='JSON file with messages data')
    parser.add_argument('-f', '--format', choices=['markdown', 'json', 'csv', 'text'],
                       default='markdown', help='Output format')
    parser.add_argument('-o', '--output', help='Output file')
    parser.add_argument('--contacts', help='Filter by contacts (comma-separated)')
    parser.add_argument('--date-from', help='Filter from date (YYYY-MM-DD)')
    parser.add_argument('--date-to', help='Filter to date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Charger données
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Support différents formats d'entrée
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict) and 'messages' in data:
            messages = data['messages']
        else:
            # Essayer de collecter tous les messages
            messages = []
            for key, value in data.items():
                if isinstance(value, list):
                    messages.extend(value)
        
        print(f"Loaded {len(messages)} messages")
        
    except Exception as e:
        print(f"Error loading input file: {e}")
        return
    
    # Filtrer si demandé
    if args.contacts:
        contacts = [c.strip() for c in args.contacts.split(',')]
        messages = [m for m in messages if m.get('contact') in contacts]
        print(f"Filtered to {len(messages)} messages from specified contacts")
    
    if args.date_from or args.date_to:
        filtered = []
        for msg in messages:
            if msg.get('timestamp'):
                try:
                    dt = datetime.fromisoformat(msg['timestamp'])
                    
                    if args.date_from and dt.date() < datetime.fromisoformat(args.date_from).date():
                        continue
                    if args.date_to and dt.date() > datetime.fromisoformat(args.date_to).date():
                        continue
                        
                    filtered.append(msg)
                except:
                    pass
        
        messages = filtered
        print(f"Filtered to {len(messages)} messages in date range")
    
    # Analyser
    analyzer = WhatsAppAnalyzer()
    
    # Générer rapport
    report = analyzer.generate_report(
        messages,
        output_format=args.format,
        output_path=Path(args.output) if args.output else None
    )
    
    # Afficher si pas de fichier output
    if not args.output:
        print("\n" + report)
    else:
        print(f"\nReport saved to: {args.output}")

if __name__ == "__main__":
    main()