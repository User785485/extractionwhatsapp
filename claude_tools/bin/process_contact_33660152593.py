#!/usr/bin/env python3
"""
Script de traitement complet pour le contact +33 6 60 15 25 93
Workflow complet : extraction, conversion, transcription, rapport
"""

import json
import sys
from pathlib import Path
import subprocess
import os

def main():
    """Traitement complet du contact"""
    
    print("=" * 60)
    print("TRAITEMENT COMPLET DU CONTACT +33 6 60 15 25 93")
    print("=" * 60)
    
    # Configuration
    contact_file = r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+33 6 60 15 25 93.html"
    media_base = r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250710235519"
    output_dir = Path(__file__).parent.parent / "output"
    
    # Étape 1: Parser le fichier (déjà fait)
    print("\n[1] Messages extraits :")
    parsed_file = output_dir / "contact_33660152593_all_messages.json"
    
    with open(parsed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"  - Total messages reçus : {data['received_count']}")
    print(f"  - Messages texte : {data['stats']['text_messages']}")
    print(f"  - Messages audio : {data['stats']['audio_messages']}")
    
    # Extraire les fichiers audio
    audio_files = []
    for msg in data['messages']:
        if msg['type'] == 'audio_received' and msg.get('media'):
            filename = msg['media']['filename']
            audio_path = Path(media_base) / filename
            if audio_path.exists():
                audio_files.append(audio_path)
    
    print(f"\n[2] Fichiers audio localisés : {len(audio_files)}")
    
    if not audio_files:
        print("  Aucun fichier audio trouvé!")
        return
        
    # Limiter à 5 fichiers pour le test
    test_files = audio_files[:5]
    print(f"  Test avec {len(test_files)} fichiers audio")
    
    # Étape 2: Convertir en MP3
    print("\n[3] Conversion en MP3...")
    converted_dir = output_dir / "converted" / "33660152593"
    converted_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "convert_audio.py"),
        *[str(f) for f in test_files],
        "-o", str(converted_dir),
        "--whisper"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [ERROR] Conversion : {result.stderr}")
        return
        
    mp3_files = list(converted_dir.glob("*.mp3"))
    print(f"  [OK] {len(mp3_files)} fichiers convertis")
    
    # Étape 3: Transcrire avec Whisper
    print("\n[4] Transcription avec Whisper API...")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("  [SKIP] OPENAI_API_KEY non définie")
        print("  Pour transcrire, exécutez : set OPENAI_API_KEY=votre_clé")
        return
        
    transcripts_file = output_dir / "transcripts" / "33660152593_transcripts.json"
    transcripts_file.parent.mkdir(exist_ok=True)
    
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "transcribe.py"),
        *[str(f) for f in mp3_files],
        "-o", str(transcripts_file),
        "--language", "fr"
    ]
    
    print("  Transcription en cours...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"  [ERROR] Transcription : {result.stderr}")
        return
        
    # Lire les transcriptions
    with open(transcripts_file, 'r', encoding='utf-8') as f:
        transcriptions = json.load(f)
        
    print(f"  [OK] {len(transcriptions)} fichiers transcrits")
    
    # Enrichir les données avec transcriptions
    for msg in data['messages']:
        if msg['type'] == 'audio_received' and msg.get('media'):
            filename = msg['media']['filename']
            base_name = Path(filename).stem
            
            # Chercher la transcription correspondante
            for trans_file, trans_data in transcriptions.items():
                if base_name in trans_file:
                    msg['transcription'] = trans_data.get('text', '')
                    msg['transcription_duration'] = trans_data.get('duration')
                    break
    
    # Sauvegarder données enrichies
    enriched_file = output_dir / "contact_33660152593_enriched.json"
    with open(enriched_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Étape 4: Générer rapports
    print("\n[5] Génération des rapports...")
    
    # CSV
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "analyze.py"),
        str(enriched_file),
        "-f", "csv",
        "-o", str(output_dir / "contact_33660152593_rapport.csv")
    ]
    subprocess.run(cmd)
    
    # TXT
    cmd = [
        sys.executable,
        str(Path(__file__).parent / "analyze.py"),
        str(enriched_file),
        "-f", "text",
        "-o", str(output_dir / "contact_33660152593_rapport.txt")
    ]
    subprocess.run(cmd)
    
    print("  [OK] Rapports générés")
    
    # Afficher un échantillon des transcriptions
    print("\n[6] Échantillon des transcriptions :")
    print("-" * 40)
    
    count = 0
    for msg in data['messages']:
        if msg.get('transcription') and count < 3:
            print(f"\nDate : {msg['timestamp']}")
            print(f"Audio : {msg['media']['filename']}")
            print(f"Transcription : {msg['transcription'][:200]}...")
            count += 1
    
    print("\n" + "=" * 60)
    print("TRAITEMENT TERMINÉ AVEC SUCCÈS!")
    print(f"Résultats dans : {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()