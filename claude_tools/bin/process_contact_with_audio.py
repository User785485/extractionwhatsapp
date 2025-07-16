#!/usr/bin/env python3
"""
Script complet pour traiter un contact WhatsApp avec messages audio de A à Z
Utilise tous les outils Claude pour extraction, conversion et transcription
"""

import json
import sys
from pathlib import Path
import subprocess
import os
from typing import List, Dict, Optional

class ContactAudioProcessor:
    def __init__(self, contact_file: str, media_base_path: str):
        self.contact_file = Path(contact_file)
        self.media_base_path = Path(media_base_path)
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Créer sous-dossiers
        self.converted_dir = self.output_dir / "converted"
        self.transcripts_dir = self.output_dir / "transcripts"
        self.converted_dir.mkdir(exist_ok=True)
        self.transcripts_dir.mkdir(exist_ok=True)
        
    def extract_audio_messages(self) -> Dict:
        """Étape 1: Parser le HTML et extraire messages avec audio"""
        print(f"\n[SEARCH] Parsing {self.contact_file.name}...")
        
        # Utiliser l'outil parse_received.py amélioré
        cmd = [
            sys.executable,
            "parse_received.py",
            str(self.contact_file),
            "-o", str(self.output_dir / "parsed_messages.json")
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] Erreur parsing: {result.stderr}")
            return None
            
        # Lire les résultats
        with open(self.output_dir / "parsed_messages.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not data:
            print("[ERROR] Aucun message trouve")
            return None
            
        contact_data = data[0]
        audio_messages = [msg for msg in contact_data['messages'] if msg.get('has_media') and msg.get('media', {}).get('type') == 'audio']
        
        print(f"[OK] {len(audio_messages)} messages audio trouves sur {contact_data['received_count']} messages recus")
        return contact_data
        
    def find_audio_files(self, audio_messages: List[Dict]) -> List[Path]:
        """Étape 2: Localiser les vrais fichiers audio"""
        print(f"\n[SEARCH] Recherche des fichiers audio dans {self.media_base_path}...")
        
        found_files = []
        for msg in audio_messages:
            if not msg.get('media'):
                continue
                
            filename = msg['media'].get('filename')
            if not filename:
                continue
                
            # Chercher le fichier
            audio_path = self.media_base_path / filename
            if audio_path.exists():
                found_files.append(audio_path)
                print(f"[OK] Trouve: {filename}")
            else:
                print(f"[MISSING] Non trouve: {filename}")
                
        return found_files
        
    def convert_to_mp3(self, audio_files: List[Path]) -> List[Path]:
        """Étape 3: Convertir les fichiers audio en MP3"""
        if not audio_files:
            print("[ERROR] Aucun fichier audio a convertir")
            return []
            
        print(f"\n[CONVERT] Conversion de {len(audio_files)} fichiers audio...")
        
        # Construire la commande avec tous les fichiers
        cmd = [
            sys.executable,
            "convert_audio.py",
            *[str(f) for f in audio_files],
            "-o", str(self.converted_dir),
            "--whisper"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] Erreur conversion: {result.stderr}")
            return []
            
        # Lister les fichiers convertis
        converted_files = list(self.converted_dir.glob("*.mp3"))
        print(f"[OK] {len(converted_files)} fichiers convertis")
        return converted_files
        
    def transcribe_audio(self, mp3_files: List[Path]) -> Dict:
        """Étape 4: Transcrire avec Whisper"""
        if not mp3_files:
            print("[ERROR] Aucun fichier MP3 a transcrire")
            return {}
            
        print(f"\n[TRANSCRIBE] Transcription de {len(mp3_files)} fichiers...")
        
        # Vérifier la clé API
        if not os.getenv('OPENAI_API_KEY'):
            print("[ERROR] OPENAI_API_KEY non configuree")
            print("[TIP] Definissez la variable: set OPENAI_API_KEY=sk-proj-...")
            return {}
            
        cmd = [
            sys.executable,
            "transcribe.py",
            *[str(f) for f in mp3_files],
            "-o", str(self.transcripts_dir / "transcriptions.json"),
            "--language", "fr"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERROR] Erreur transcription: {result.stderr}")
            return {}
            
        # Lire les transcriptions
        with open(self.transcripts_dir / "transcriptions.json", 'r', encoding='utf-8') as f:
            transcriptions = json.load(f)
            
        print(f"[OK] {len(transcriptions)} fichiers transcrits")
        return transcriptions
        
    def generate_report(self, contact_data: Dict, transcriptions: Dict):
        """Étape 5: Générer rapports CSV et TXT"""
        print(f"\n[REPORT] Generation des rapports...")
        
        # Enrichir les messages avec transcriptions
        for msg in contact_data['messages']:
            if msg.get('has_media') and msg.get('media', {}).get('type') == 'audio':
                filename = msg['media'].get('filename')
                if filename:
                    # Chercher la transcription correspondante
                    base_name = Path(filename).stem
                    for trans_file, trans_data in transcriptions.items():
                        if base_name in trans_file:
                            msg['transcription'] = trans_data.get('text', '')
                            msg['transcription_duration'] = trans_data.get('duration')
                            break
                            
        # Sauvegarder les données enrichies
        enriched_file = self.output_dir / "messages_with_transcriptions.json"
        with open(enriched_file, 'w', encoding='utf-8') as f:
            json.dump([contact_data], f, ensure_ascii=False, indent=2)
            
        # Générer CSV
        print("[CSV] Generation du CSV...")
        cmd = [
            sys.executable,
            "analyze.py",
            str(enriched_file),
            "-f", "csv",
            "-o", str(self.output_dir / "rapport_final.csv")
        ]
        subprocess.run(cmd)
        
        # Générer TXT
        print("[TXT] Generation du TXT...")
        cmd = [
            sys.executable,
            "analyze.py",
            str(enriched_file),
            "-f", "text",
            "-o", str(self.output_dir / "rapport_final.txt")
        ]
        subprocess.run(cmd)
        
        print(f"[OK] Rapports generes dans {self.output_dir}")
        
    def process(self):
        """Traitement complet du contact"""
        print(f"[START] Traitement complet du contact: {self.contact_file.name}")
        print("=" * 60)
        
        # Étape 1: Parser
        contact_data = self.extract_audio_messages()
        if not contact_data:
            return
            
        audio_messages = [msg for msg in contact_data['messages'] 
                         if msg.get('has_media') and msg.get('media', {}).get('type') == 'audio']
        
        if not audio_messages:
            print("[ERROR] Aucun message audio trouve")
            return
            
        # Étape 2: Localiser fichiers
        audio_files = self.find_audio_files(audio_messages)
        if not audio_files:
            print("[ERROR] Aucun fichier audio localise")
            return
            
        # Étape 3: Convertir
        mp3_files = self.convert_to_mp3(audio_files)
        if not mp3_files:
            print("[ERROR] Echec de la conversion")
            return
            
        # Étape 4: Transcrire
        transcriptions = self.transcribe_audio(mp3_files)
        
        # Étape 5: Générer rapports
        self.generate_report(contact_data, transcriptions)
        
        print("\n[SUCCESS] Traitement termine avec succes!")
        print(f"[OUTPUT] Resultats dans: {self.output_dir}")


def main():
    """Point d'entrée principal"""
    # Contact avec messages audio (exemple trouvé)
    contact_file = r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\Test.html"
    
    # Dossier des médias (corrigé avec le bon timestamp)
    media_path = r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250710235519"
    
    # Vérifier que les chemins existent
    if not Path(contact_file).exists():
        print(f"[X] Fichier contact introuvable: {contact_file}")
        return
        
    if not Path(media_path).exists():
        print(f"[X] Dossier medias introuvable: {media_path}")
        return
        
    # Lancer le traitement
    processor = ContactAudioProcessor(contact_file, media_path)
    processor.process()


if __name__ == "__main__":
    main()