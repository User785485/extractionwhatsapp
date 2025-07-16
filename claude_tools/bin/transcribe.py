#!/usr/bin/env python3
"""
Whisper API interface optimized for Claude
Smart transcription with caching, retry, and error handling
"""

import sys
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime
import argparse
from typing import List, Dict, Optional, Union
import os
from openai import OpenAI
import concurrent.futures

class WhisperTranscriber:
    """Interface Whisper optimisée avec cache et retry"""
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """
        Args:
            api_key: OpenAI API key (or from env)
            cache_dir: Cache directory for transcriptions
        """
        # API Key
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required! Set OPENAI_API_KEY env or pass api_key")
        
        # Client OpenAI
        self.client = OpenAI(api_key=self.api_key)
        
        # Cache
        self.cache_dir = cache_dir or Path('claude_tools/cache/transcriptions')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index = self._load_cache_index()
        
        # Configuration
        self.max_retries = 3
        self.retry_delay = 2  # secondes
        self.max_file_size = 25 * 1024 * 1024  # 25MB limite Whisper
        
    def transcribe_file(self, audio_path: Path, language: Optional[str] = None,
                       force: bool = False) -> Dict:
        """Transcrire un fichier audio"""
        
        # Validation
        if not audio_path.exists():
            return {
                'success': False,
                'error': 'File not found',
                'file': str(audio_path)
            }
        
        # Vérifier taille
        file_size = audio_path.stat().st_size
        if file_size > self.max_file_size:
            return {
                'success': False,
                'error': f'File too large ({file_size / 1024 / 1024:.1f}MB > 25MB)',
                'file': str(audio_path)
            }
        
        # Vérifier cache
        file_hash = self._get_file_hash(audio_path)
        
        if not force:
            cached = self._get_cached_transcription(file_hash, audio_path)
            if cached:
                return {
                    'success': True,
                    'cached': True,
                    'file': str(audio_path),
                    'transcription': cached['transcription'],
                    'language': cached.get('language'),
                    'duration': 0,
                    'from_cache': True
                }
        
        # Transcrire avec retry
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                with open(audio_path, 'rb') as audio_file:
                    # Paramètres Whisper
                    params = {
                        'model': 'whisper-1',
                        'file': audio_file,
                        'response_format': 'verbose_json'
                    }
                    
                    if language:
                        params['language'] = language
                    
                    # Appel API
                    response = self.client.audio.transcriptions.create(**params)
                
                # Succès
                duration = time.time() - start_time
                
                result = {
                    'success': True,
                    'cached': False,
                    'file': str(audio_path),
                    'transcription': response.text,
                    'language': response.language if hasattr(response, 'language') else language,
                    'duration': round(duration, 2),
                    'segments': response.segments if hasattr(response, 'segments') else None,
                    'from_cache': False
                }
                
                # Sauvegarder en cache
                self._save_to_cache(file_hash, audio_path, result)
                
                return result
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Retry avec backoff
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"  Retry {attempt + 1}/{self.max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Échec final
                    return {
                        'success': False,
                        'error': str(e),
                        'file': str(audio_path),
                        'attempts': attempt + 1
                    }
    
    def transcribe_batch(self, audio_files: List[Path], language: Optional[str] = None,
                        max_workers: int = 3) -> List[Dict]:
        """Transcrire plusieurs fichiers en parallèle"""
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre toutes les transcriptions
            future_to_file = {
                executor.submit(self.transcribe_file, file, language): file
                for file in audio_files
            }
            
            # Progress
            completed = 0
            total = len(audio_files)
            
            # Collecter résultats
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                completed += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Status
                    status = "✓" if result['success'] else "✗"
                    cache_info = " (cached)" if result.get('from_cache') else ""
                    print(f"{status} [{completed}/{total}] {file.name}{cache_info}")
                    
                except Exception as e:
                    results.append({
                        'success': False,
                        'file': str(file),
                        'error': str(e)
                    })
                    print(f"✗ [{completed}/{total}] {file.name} - Error")
        
        return results
    
    def transcribe_with_context(self, audio_files: List[Path], 
                               messages_data: List[Dict]) -> List[Dict]:
        """Transcrire en associant aux messages"""
        
        # Créer index des messages par timestamp/contact
        message_index = {}
        for msg in messages_data:
            key = f"{msg.get('contact', 'unknown')}_{msg.get('timestamp', '')}"
            message_index[key] = msg
        
        # Transcrire tous les audios
        transcriptions = self.transcribe_batch(audio_files)
        
        # Associer transcriptions aux messages
        enriched_messages = []
        
        for trans in transcriptions:
            if trans['success']:
                # Essayer de trouver le message correspondant
                # (Ici on pourrait améliorer le matching)
                file_name = Path(trans['file']).stem
                
                # Chercher dans l'index
                matched = False
                for key, msg in message_index.items():
                    if file_name in key or key in file_name:
                        # Match trouvé
                        msg['transcription'] = trans['transcription']
                        msg['audio_file'] = trans['file']
                        msg['transcribed'] = True
                        enriched_messages.append(msg)
                        matched = True
                        break
                
                if not matched:
                    # Créer nouveau message pour transcription orpheline
                    enriched_messages.append({
                        'contact': 'Unknown',
                        'timestamp': datetime.now().isoformat(),
                        'content': f"[Audio: {file_name}]",
                        'transcription': trans['transcription'],
                        'audio_file': trans['file'],
                        'transcribed': True,
                        'orphan': True
                    })
        
        return enriched_messages
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Hash unique du fichier"""
        
        # Hash: taille + début + fin
        size = file_path.stat().st_size
        with open(file_path, 'rb') as f:
            hash_obj = hashlib.sha256()
            hash_obj.update(str(size).encode())
            hash_obj.update(f.read(8192))  # 8KB début
            if size > 16384:
                f.seek(-8192, 2)
                hash_obj.update(f.read())  # 8KB fin
        
        return hash_obj.hexdigest()[:32]
    
    def _load_cache_index(self) -> Dict:
        """Charger index du cache"""
        
        index_file = self.cache_dir / 'cache_index.json'
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache_index(self):
        """Sauvegarder index du cache"""
        
        index_file = self.cache_dir / 'cache_index.json'
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
    
    def _get_cached_transcription(self, file_hash: str, audio_path: Path) -> Optional[Dict]:
        """Récupérer transcription du cache"""
        
        if file_hash in self.cache_index:
            cache_file = self.cache_dir / f"{file_hash}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    # Cache corrompu, supprimer
                    del self.cache_index[file_hash]
        
        return None
    
    def _save_to_cache(self, file_hash: str, audio_path: Path, result: Dict):
        """Sauvegarder transcription en cache"""
        
        # Données à cacher
        cache_data = {
            'file_name': audio_path.name,
            'file_size': audio_path.stat().st_size,
            'transcription': result['transcription'],
            'language': result.get('language'),
            'cached_at': datetime.now().isoformat(),
            'segments': result.get('segments')
        }
        
        # Sauvegarder fichier cache
        cache_file = self.cache_dir / f"{file_hash}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        # Mettre à jour index
        self.cache_index[file_hash] = {
            'file': audio_path.name,
            'size': audio_path.stat().st_size,
            'cached_at': cache_data['cached_at']
        }
        self._save_cache_index()
    
    def get_cache_stats(self) -> Dict:
        """Statistiques du cache"""
        
        total_files = len(self.cache_index)
        total_size = 0
        
        for hash_id, info in self.cache_index.items():
            cache_file = self.cache_dir / f"{hash_id}.json"
            if cache_file.exists():
                total_size += cache_file.stat().st_size
        
        return {
            'cached_files': total_files,
            'cache_size_mb': round(total_size / 1024 / 1024, 2),
            'cache_dir': str(self.cache_dir)
        }
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """Nettoyer le cache"""
        
        cleared = 0
        
        if older_than_days:
            # Nettoyer seulement les anciens
            cutoff_date = datetime.now().timestamp() - (older_than_days * 86400)
            
            for hash_id in list(self.cache_index.keys()):
                cache_file = self.cache_dir / f"{hash_id}.json"
                if cache_file.exists():
                    if cache_file.stat().st_mtime < cutoff_date:
                        cache_file.unlink()
                        del self.cache_index[hash_id]
                        cleared += 1
        else:
            # Tout nettoyer
            for cache_file in self.cache_dir.glob('*.json'):
                if cache_file.name != 'cache_index.json':
                    cache_file.unlink()
                    cleared += 1
            self.cache_index = {}
        
        self._save_cache_index()
        return cleared

def main():
    """CLI pour Claude"""
    
    parser = argparse.ArgumentParser(
        description='Transcribe WhatsApp audio with Whisper API',
        epilog="""
Examples:
  # Transcribe single file
  python transcribe.py audio.mp3
  
  # Transcribe all MP3 in folder
  python transcribe.py /path/to/audio/*.mp3
  
  # Specify language
  python transcribe.py audio.mp3 --language fr
  
  # Force re-transcription (ignore cache)
  python transcribe.py audio.mp3 --force
  
  # View cache statistics
  python transcribe.py --cache-stats
  
  # Clear old cache
  python transcribe.py --clear-cache 30
        """
    )
    
    parser.add_argument('files', nargs='*', help='Audio files to transcribe')
    parser.add_argument('--language', help='Language code (fr, en, es, etc.)')
    parser.add_argument('--force', action='store_true', help='Force re-transcription')
    parser.add_argument('--output', help='Output JSON file')
    parser.add_argument('--api-key', help='OpenAI API key')
    parser.add_argument('--cache-dir', help='Cache directory')
    parser.add_argument('--cache-stats', action='store_true', help='Show cache statistics')
    parser.add_argument('--clear-cache', type=int, metavar='DAYS', 
                       help='Clear cache older than N days (0 = all)')
    parser.add_argument('--workers', type=int, default=3, help='Parallel workers')
    
    args = parser.parse_args()
    
    # Créer transcriber
    try:
        transcriber = WhisperTranscriber(
            api_key=args.api_key,
            cache_dir=Path(args.cache_dir) if args.cache_dir else None
        )
    except ValueError as e:
        print(f"Error: {e}")
        print("Set OPENAI_API_KEY environment variable or use --api-key")
        return
    
    # Cache operations
    if args.cache_stats:
        stats = transcriber.get_cache_stats()
        print("=== CACHE STATISTICS ===")
        print(f"Cached files: {stats['cached_files']}")
        print(f"Cache size: {stats['cache_size_mb']} MB")
        print(f"Cache location: {stats['cache_dir']}")
        return
    
    if args.clear_cache is not None:
        cleared = transcriber.clear_cache(args.clear_cache if args.clear_cache > 0 else None)
        print(f"Cleared {cleared} cached files")
        return
    
    # Vérifier fichiers
    if not args.files:
        parser.print_help()
        return
    
    # Collecter fichiers
    audio_files = []
    for pattern in args.files:
        path = Path(pattern)
        if path.is_file():
            audio_files.append(path)
        else:
            # Glob pattern
            audio_files.extend(Path('.').glob(pattern))
    
    if not audio_files:
        print("No audio files found!")
        return
    
    print(f"Transcribing {len(audio_files)} files...")
    
    # Transcrire
    if len(audio_files) == 1:
        # Single file
        result = transcriber.transcribe_file(audio_files[0], args.language, args.force)
        
        if result['success']:
            print(f"\n✓ Transcription successful")
            if result.get('from_cache'):
                print("  (from cache)")
            else:
                print(f"  Duration: {result['duration']}s")
            print(f"\nTranscription:\n{result['transcription']}")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\nSaved to: {args.output}")
        else:
            print(f"\n✗ Transcription failed: {result['error']}")
    
    else:
        # Batch
        results = transcriber.transcribe_batch(audio_files, args.language, args.workers)
        
        # Summary
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        cached = [r for r in successful if r.get('from_cache')]
        
        print(f"\n=== SUMMARY ===")
        print(f"Total: {len(results)}")
        print(f"Success: {len(successful)} ({len(cached)} from cache)")
        print(f"Failed: {len(failed)}")
        
        if failed:
            print("\nFailed files:")
            for r in failed:
                print(f"  - {Path(r['file']).name}: {r.get('error', 'Unknown error')}")
        
        # Sauvegarder résultats
        if args.output:
            # Format pour export
            export_data = []
            for r in results:
                if r['success']:
                    export_data.append({
                        'file': r['file'],
                        'transcription': r['transcription'],
                        'language': r.get('language'),
                        'cached': r.get('from_cache', False)
                    })
            
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"\nResults saved to: {args.output}")

if __name__ == "__main__":
    main()