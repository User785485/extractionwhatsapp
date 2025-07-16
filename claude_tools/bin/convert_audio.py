#!/usr/bin/env python3
"""
Universal audio converter for WhatsApp voice messages
Converts opus/m4a/ogg/etc to MP3 for Whisper API
"""

import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import argparse
from typing import List, Dict, Optional, Tuple
import concurrent.futures
import hashlib
import time

class AudioConverter:
    """Convertisseur audio universel optimisé pour Whisper"""
    
    # Formats supportés en entrée
    SUPPORTED_FORMATS = {'.opus', '.m4a', '.ogg', '.weba', '.aac', '.amr', '.3gp', '.wav', '.flac'}
    
    # Configuration FFmpeg optimale pour Whisper
    FFMPEG_PRESETS = {
        'whisper': {
            'codec': 'libmp3lame',
            'bitrate': '128k',
            'sample_rate': '16000',  # Whisper préfère 16kHz
            'channels': '1',  # Mono
            'args': ['-q:a', '2']  # Qualité élevée
        },
        'standard': {
            'codec': 'libmp3lame',
            'bitrate': '192k',
            'sample_rate': '44100',
            'channels': '2',
            'args': []
        },
        'low': {
            'codec': 'libmp3lame',
            'bitrate': '96k',
            'sample_rate': '16000',
            'channels': '1',
            'args': ['-q:a', '5']
        }
    }
    
    def __init__(self, output_dir: Optional[Path] = None, preset: str = 'whisper'):
        """
        Args:
            output_dir: Dossier de sortie (par défaut: même que source)
            preset: Preset de conversion ('whisper', 'standard', 'low')
        """
        self.output_dir = output_dir
        self.preset = self.FFMPEG_PRESETS.get(preset, self.FFMPEG_PRESETS['whisper'])
        self.ffmpeg_path = self._find_ffmpeg()
        self.conversion_cache = {}
        
    def _find_ffmpeg(self) -> str:
        """Trouver FFmpeg sur le système"""
        
        # Essayer ffmpeg dans PATH
        if shutil.which('ffmpeg'):
            return 'ffmpeg'
        
        # Chemins courants Windows
        common_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\ProgramData\chocolatey\bin\ffmpeg.exe'
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        raise RuntimeError("FFmpeg not found! Please install FFmpeg and add to PATH")
    
    def check_ffmpeg(self) -> Dict:
        """Vérifier installation FFmpeg"""
        
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return {
                    'installed': True,
                    'path': self.ffmpeg_path,
                    'version': version_line
                }
            else:
                return {
                    'installed': False,
                    'error': 'FFmpeg found but not working'
                }
                
        except Exception as e:
            return {
                'installed': False,
                'error': str(e)
            }
    
    def convert_file(self, input_path: Path, output_path: Optional[Path] = None, 
                    force: bool = False) -> Dict:
        """Convertir un fichier audio en MP3"""
        
        # Validation
        if not input_path.exists():
            return {'success': False, 'error': 'Input file not found'}
        
        if input_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return {'success': False, 'error': f'Unsupported format: {input_path.suffix}'}
        
        # Déterminer output
        if not output_path:
            if self.output_dir:
                output_path = self.output_dir / f"{input_path.stem}.mp3"
            else:
                output_path = input_path.with_suffix('.mp3')
        
        # Vérifier cache
        if not force and output_path.exists():
            # Vérifier si conversion déjà faite
            input_hash = self._get_file_hash(input_path)
            if self._is_cached(input_hash, output_path):
                return {
                    'success': True,
                    'cached': True,
                    'input': str(input_path),
                    'output': str(output_path),
                    'size': output_path.stat().st_size
                }
        
        # Créer dossier si nécessaire
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Construire commande FFmpeg
        cmd = self._build_ffmpeg_command(input_path, output_path)
        
        # Exécuter conversion
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            if result.returncode == 0 and output_path.exists():
                duration = time.time() - start_time
                
                # Sauvegarder dans cache
                self._save_to_cache(input_path, output_path)
                
                return {
                    'success': True,
                    'cached': False,
                    'input': str(input_path),
                    'output': str(output_path),
                    'size': output_path.stat().st_size,
                    'duration': round(duration, 2),
                    'command': ' '.join(cmd)
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Unknown error',
                    'command': ' '.join(cmd)
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Conversion timeout (>5 minutes)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def convert_batch(self, input_files: List[Path], max_workers: int = 4) -> List[Dict]:
        """Convertir plusieurs fichiers en parallèle"""
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre toutes les conversions
            future_to_file = {
                executor.submit(self.convert_file, file): file 
                for file in input_files
            }
            
            # Collecter résultats
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Progress
                    if result['success']:
                        print(f"✓ Converted: {file.name}")
                    else:
                        print(f"✗ Failed: {file.name} - {result.get('error', 'Unknown')}")
                        
                except Exception as e:
                    results.append({
                        'success': False,
                        'input': str(file),
                        'error': str(e)
                    })
        
        return results
    
    def _build_ffmpeg_command(self, input_path: Path, output_path: Path) -> List[str]:
        """Construire commande FFmpeg optimale"""
        
        cmd = [
            self.ffmpeg_path,
            '-i', str(input_path),
            '-acodec', self.preset['codec'],
            '-ab', self.preset['bitrate'],
            '-ar', self.preset['sample_rate'],
            '-ac', self.preset['channels']
        ]
        
        # Arguments additionnels
        cmd.extend(self.preset.get('args', []))
        
        # Options générales
        cmd.extend([
            '-y',  # Overwrite
            '-loglevel', 'error',  # Moins verbose
            str(output_path)
        ])
        
        return cmd
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Hash rapide du fichier"""
        
        # Pour gros fichiers, hasher seulement début + fin
        size = file_path.stat().st_size
        
        with open(file_path, 'rb') as f:
            if size > 1024 * 1024:  # > 1MB
                # Hash début + taille + fin
                hash_obj = hashlib.md5()
                hash_obj.update(f.read(8192))  # 8KB début
                hash_obj.update(str(size).encode())
                f.seek(-8192, 2)  # 8KB fin
                hash_obj.update(f.read())
                return hash_obj.hexdigest()[:16]
            else:
                return hashlib.md5(f.read()).hexdigest()[:16]
    
    def _is_cached(self, input_hash: str, output_path: Path) -> bool:
        """Vérifier si conversion déjà en cache"""
        
        cache_file = output_path.parent / '.audio_converter_cache.json'
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                    
                output_key = output_path.name
                if output_key in cache and cache[output_key].get('input_hash') == input_hash:
                    # Vérifier que le fichier output existe toujours
                    return output_path.exists()
            except:
                pass
                
        return False
    
    def _save_to_cache(self, input_path: Path, output_path: Path):
        """Sauvegarder info de conversion en cache"""
        
        cache_file = output_path.parent / '.audio_converter_cache.json'
        
        try:
            # Charger cache existant
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            else:
                cache = {}
            
            # Ajouter entrée
            cache[output_path.name] = {
                'input_hash': self._get_file_hash(input_path),
                'input_file': input_path.name,
                'converted_at': datetime.now().isoformat(),
                'preset': self.preset
            }
            
            # Sauvegarder
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
                
        except:
            pass  # Cache optionnel
    
    def prepare_for_whisper(self, input_files: List[Path]) -> Dict:
        """Préparer fichiers pour Whisper API"""
        
        print(f"Preparing {len(input_files)} files for Whisper...")
        
        # Créer dossier whisper_ready
        if self.output_dir:
            whisper_dir = self.output_dir / 'whisper_ready'
        else:
            whisper_dir = Path('whisper_ready')
        
        whisper_dir.mkdir(exist_ok=True)
        
        # Convertir avec preset whisper
        old_output = self.output_dir
        self.output_dir = whisper_dir
        
        results = self.convert_batch(input_files)
        
        self.output_dir = old_output
        
        # Résumé
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        summary = {
            'total': len(input_files),
            'converted': len(successful),
            'failed': len(failed),
            'output_dir': str(whisper_dir),
            'ready_files': [r['output'] for r in successful],
            'errors': [{'file': r.get('input', 'unknown'), 'error': r.get('error', 'unknown')} for r in failed]
        }
        
        # Sauvegarder manifest
        manifest_path = whisper_dir / 'whisper_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ {summary['converted']} files ready for Whisper")
        if summary['failed']:
            print(f"✗ {summary['failed']} files failed")
        print(f"Files saved to: {whisper_dir}")
        
        return summary

def main():
    """CLI pour Claude"""
    
    parser = argparse.ArgumentParser(
        description='Convert WhatsApp audio files to MP3',
        epilog="""
Examples:
  # Convert single file
  python convert_audio.py audio.opus
  
  # Convert all audio in folder
  python convert_audio.py /path/to/media --all
  
  # Prepare for Whisper API
  python convert_audio.py /path/to/media --whisper
  
  # Use different preset
  python convert_audio.py audio.m4a --preset standard
  
  # Batch convert with custom output
  python convert_audio.py *.opus -o converted/
        """
    )
    
    parser.add_argument('input', nargs='+', help='Input file(s) or directory')
    parser.add_argument('-o', '--output', help='Output directory')
    parser.add_argument('--all', action='store_true', help='Convert all audio files in directory')
    parser.add_argument('--whisper', action='store_true', help='Prepare files for Whisper API')
    parser.add_argument('--preset', choices=['whisper', 'standard', 'low'], 
                       default='whisper', help='Conversion preset')
    parser.add_argument('--force', action='store_true', help='Force re-conversion')
    parser.add_argument('--check', action='store_true', help='Check FFmpeg installation')
    parser.add_argument('--workers', type=int, default=4, help='Parallel workers')
    
    args = parser.parse_args()
    
    # Créer convertisseur
    output_dir = Path(args.output) if args.output else None
    converter = AudioConverter(output_dir, args.preset)
    
    # Check FFmpeg
    if args.check:
        info = converter.check_ffmpeg()
        if info['installed']:
            print(f"✓ FFmpeg found: {info['path']}")
            print(f"  Version: {info['version']}")
        else:
            print(f"✗ FFmpeg not found: {info['error']}")
        return
    
    # Collecter fichiers
    input_files = []
    
    for input_item in args.input:
        path = Path(input_item)
        
        if path.is_file():
            input_files.append(path)
        elif path.is_dir():
            if args.all or args.whisper:
                # Chercher tous les fichiers audio
                for ext in AudioConverter.SUPPORTED_FORMATS:
                    input_files.extend(path.rglob(f'*{ext}'))
            else:
                print(f"'{path}' is a directory. Use --all to convert all audio files.")
        else:
            # Essayer comme pattern
            input_files.extend(Path('.').glob(input_item))
    
    if not input_files:
        print("No audio files found!")
        return
    
    print(f"Found {len(input_files)} audio files")
    
    # Mode Whisper
    if args.whisper:
        summary = converter.prepare_for_whisper(input_files)
        
        # Afficher manifest
        print(f"\nManifest saved: {summary['output_dir']}/whisper_manifest.json")
        
    else:
        # Conversion normale
        if len(input_files) == 1:
            # Single file
            result = converter.convert_file(input_files[0], force=args.force)
            
            if result['success']:
                print(f"✓ Converted successfully")
                print(f"  Output: {result['output']}")
                print(f"  Size: {result['size']:,} bytes")
                if not result.get('cached'):
                    print(f"  Time: {result.get('duration', 0)} seconds")
            else:
                print(f"✗ Conversion failed: {result['error']}")
                
        else:
            # Batch
            results = converter.convert_batch(input_files, max_workers=args.workers)
            
            # Résumé
            successful = sum(1 for r in results if r['success'])
            failed = len(results) - successful
            
            print(f"\n=== SUMMARY ===")
            print(f"Total: {len(results)}")
            print(f"Success: {successful}")
            print(f"Failed: {failed}")
            
            if failed:
                print("\nFailed files:")
                for r in results:
                    if not r['success']:
                        print(f"  - {r.get('input', 'unknown')}: {r.get('error', 'unknown')}")

if __name__ == "__main__":
    main()