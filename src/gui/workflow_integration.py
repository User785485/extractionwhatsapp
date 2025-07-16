"""
Integration complète du workflow Claude Tools dans l'interface graphique
Architecture ELO 5000 pour traitement robuste et scalable
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Optional, Callable
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import time

# Ajouter claude_tools au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "claude_tools" / "bin"))

class WorkflowIntegration:
    """Intégration complète du workflow dans la GUI"""
    
    def __init__(self, progress_callback: Optional[Callable] = None, log_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback or (lambda x: None)
        self.log_callback = log_callback or (lambda x: None)
        
        # Chemins
        self.claude_tools_bin = Path(__file__).parent.parent.parent / "claude_tools" / "bin"
        self.output_dir = Path(__file__).parent.parent.parent / "claude_tools" / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.max_workers = 4  # Pour traitement parallèle
        self.batch_size = 10  # Contacts par batch
        
        # État
        self.processing = False
        self.cancel_requested = False
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'with_audio': 0,
            'transcribed': 0,
            'errors': 0
        }
        
    def process_files(self, file_paths: List[str], options: Dict) -> Dict:
        """
        Traite une liste de fichiers ou un dossier complet
        
        Args:
            file_paths: Liste de chemins de fichiers HTML ou un dossier
            options: {
                'transcribe': bool,
                'export_formats': ['csv', 'txt', 'markdown'],
                'language': 'fr',
                'parallel': bool,
                'media_path': str  # Chemin vers les médias
            }
        """
        self.processing = True
        self.cancel_requested = False
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'with_audio': 0,
            'transcribed': 0,
            'errors': 0
        }
        
        try:
            # Résoudre les fichiers
            files_to_process = self._resolve_files(file_paths)
            self.stats['total_files'] = len(files_to_process)
            
            self.log_callback(f"[START] Traitement de {len(files_to_process)} fichiers")
            
            if options.get('parallel') and len(files_to_process) > 5:
                results = self._process_parallel(files_to_process, options)
            else:
                results = self._process_sequential(files_to_process, options)
                
            # Générer rapport final
            self._generate_final_report(results, options)
            
            return {
                'success': True,
                'stats': self.stats,
                'results': results,
                'output_dir': str(self.output_dir)
            }
            
        except Exception as e:
            self.log_callback(f"[ERROR] Erreur workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
        finally:
            self.processing = False
            
    def _resolve_files(self, file_paths: List[str]) -> List[Path]:
        """Résout les chemins en liste de fichiers HTML"""
        resolved = []
        
        for path_str in file_paths:
            path = Path(path_str)
            
            if path.is_file() and path.suffix == '.html':
                resolved.append(path)
            elif path.is_dir():
                # Scanner le dossier
                html_files = list(path.glob("*.html"))
                resolved.extend(html_files)
                self.log_callback(f"[SCAN] {len(html_files)} fichiers HTML trouvés dans {path.name}")
                
        return resolved
        
    def _process_sequential(self, files: List[Path], options: Dict) -> List[Dict]:
        """Traitement séquentiel des fichiers"""
        results = []
        
        for i, file_path in enumerate(files):
            if self.cancel_requested:
                break
                
            self.progress_callback(int((i / len(files)) * 100))
            
            result = self._process_single_file(file_path, options)
            results.append(result)
            
            self.stats['processed'] += 1
            if result.get('has_audio'):
                self.stats['with_audio'] += 1
            if result.get('transcribed'):
                self.stats['transcribed'] += 1
            if not result.get('success'):
                self.stats['errors'] += 1
                
        return results
        
    def _process_parallel(self, files: List[Path], options: Dict) -> List[Dict]:
        """Traitement parallèle avec ThreadPoolExecutor"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumettre les tâches par batch
            futures = []
            
            for i in range(0, len(files), self.batch_size):
                if self.cancel_requested:
                    break
                    
                batch = files[i:i+self.batch_size]
                for file_path in batch:
                    future = executor.submit(self._process_single_file, file_path, options)
                    futures.append((future, file_path))
                    
            # Collecter les résultats
            for i, (future, file_path) in enumerate(futures):
                if self.cancel_requested:
                    break
                    
                try:
                    result = future.result(timeout=300)  # 5min max par fichier
                    results.append(result)
                    
                    # Mise à jour stats
                    self.stats['processed'] += 1
                    if result.get('has_audio'):
                        self.stats['with_audio'] += 1
                    if result.get('transcribed'):
                        self.stats['transcribed'] += 1
                        
                except Exception as e:
                    self.log_callback(f"[ERROR] {file_path.name}: {str(e)}")
                    self.stats['errors'] += 1
                    results.append({
                        'file': str(file_path),
                        'success': False,
                        'error': str(e)
                    })
                    
                self.progress_callback(int((i / len(futures)) * 100))
                
        return results
        
    def _process_single_file(self, file_path: Path, options: Dict) -> Dict:
        """Traite un seul fichier HTML"""
        
        contact_name = file_path.stem
        self.log_callback(f"[PROCESS] {contact_name}")
        
        try:
            # Étape 1: Parser les messages
            parsed_file = self.output_dir / f"{contact_name}_parsed.json"
            cmd = [
                sys.executable,
                str(self.claude_tools_bin / "parse_received.py"),
                str(file_path),
                "-o", str(parsed_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Erreur parsing: {result.stderr}")
                
            # Lire les résultats
            with open(parsed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not data:
                return {
                    'file': str(file_path),
                    'success': False,
                    'error': 'Aucun message trouvé'
                }
                
            contact_data = data[0]
            audio_messages = [
                msg for msg in contact_data['messages'] 
                if msg.get('has_media') and msg.get('media', {}).get('type') == 'audio'
            ]
            
            has_audio = len(audio_messages) > 0
            
            # Si pas d'audio ou pas de transcription demandée
            if not has_audio or not options.get('transcribe'):
                return {
                    'file': str(file_path),
                    'success': True,
                    'has_audio': has_audio,
                    'transcribed': False,
                    'messages_count': contact_data['received_count'],
                    'audio_count': len(audio_messages)
                }
                
            # Étape 2: Localiser et convertir les fichiers audio
            media_path = Path(options.get('media_path', r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250710235519"))
            
            audio_files = []
            for msg in audio_messages:
                filename = msg['media'].get('filename')
                if filename:
                    audio_path = media_path / filename
                    if audio_path.exists():
                        audio_files.append(audio_path)
                        
            if not audio_files:
                return {
                    'file': str(file_path),
                    'success': True,
                    'has_audio': True,
                    'transcribed': False,
                    'error': 'Fichiers audio introuvables'
                }
                
            # Étape 3: Convertir en MP3
            converted_dir = self.output_dir / "converted" / contact_name
            converted_dir.mkdir(parents=True, exist_ok=True)
            
            cmd = [
                sys.executable,
                str(self.claude_tools_bin / "convert_audio.py"),
                *[str(f) for f in audio_files],
                "-o", str(converted_dir),
                "--whisper"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Erreur conversion: {result.stderr}")
                
            # Étape 4: Transcrire
            mp3_files = list(converted_dir.glob("*.mp3"))
            if mp3_files and options.get('transcribe'):
                transcripts_file = self.output_dir / "transcripts" / f"{contact_name}_transcripts.json"
                transcripts_file.parent.mkdir(exist_ok=True)
                
                cmd = [
                    sys.executable,
                    str(self.claude_tools_bin / "transcribe.py"),
                    *[str(f) for f in mp3_files],
                    "-o", str(transcripts_file),
                    "--language", options.get('language', 'fr')
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    # Enrichir les données avec transcriptions
                    with open(transcripts_file, 'r', encoding='utf-8') as f:
                        transcriptions = json.load(f)
                        
                    # Associer transcriptions aux messages
                    for msg in contact_data['messages']:
                        if msg.get('has_media') and msg.get('media', {}).get('type') == 'audio':
                            filename = msg['media'].get('filename')
                            if filename:
                                base_name = Path(filename).stem
                                for trans_file, trans_data in transcriptions.items():
                                    if base_name in trans_file:
                                        msg['transcription'] = trans_data.get('text', '')
                                        break
                                        
            # Étape 5: Exporter dans les formats demandés
            for format_type in options.get('export_formats', ['csv']):
                output_file = self.output_dir / f"{contact_name}.{format_type}"
                
                # Sauvegarder données enrichies temporairement
                temp_file = self.output_dir / f"{contact_name}_enriched.json"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump([contact_data], f, ensure_ascii=False, indent=2)
                    
                cmd = [
                    sys.executable,
                    str(self.claude_tools_bin / "analyze.py"),
                    str(temp_file),
                    "-f", format_type,
                    "-o", str(output_file)
                ]
                
                subprocess.run(cmd, capture_output=True, text=True)
                
            return {
                'file': str(file_path),
                'success': True,
                'has_audio': True,
                'transcribed': True,
                'messages_count': contact_data['received_count'],
                'audio_count': len(audio_messages),
                'transcriptions_count': len([m for m in contact_data['messages'] if m.get('transcription')])
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'success': False,
                'error': str(e)
            }
            
    def _generate_final_report(self, results: List[Dict], options: Dict):
        """Génère un rapport final consolidé"""
        
        # Rapport JSON détaillé
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'stats': self.stats,
            'options': options,
            'results': results
        }
        
        report_file = self.output_dir / f"workflow_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        # Rapport texte résumé
        summary = f"""
RAPPORT DE TRAITEMENT WHATSAPP
==============================
Date: {report['timestamp']}

STATISTIQUES
------------
Fichiers traités: {self.stats['processed']}/{self.stats['total_files']}
Avec audio: {self.stats['with_audio']}
Transcrits: {self.stats['transcribed']}
Erreurs: {self.stats['errors']}

OPTIONS
-------
Transcription: {'Oui' if options.get('transcribe') else 'Non'}
Formats export: {', '.join(options.get('export_formats', []))}
Traitement parallèle: {'Oui' if options.get('parallel') else 'Non'}

RESULTATS
---------
Dossier de sortie: {self.output_dir}
"""
        
        summary_file = self.output_dir / f"summary_{int(time.time())}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
            
        self.log_callback(f"[DONE] Rapport généré: {report_file.name}")
        
    def cancel_processing(self):
        """Annule le traitement en cours"""
        self.cancel_requested = True
        self.log_callback("[CANCEL] Annulation demandée...")