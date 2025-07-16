#!/usr/bin/env python3
"""
Transcription avec clé API intégrée
"""

import sys
import json
from pathlib import Path
import time
from openai import OpenAI

# Configuration de la clé API
API_KEY = "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"

def main():
    print("=" * 60)
    print("TRANSCRIPTION WHATSAPP - CONTACT +33 6 60 15 25 93")
    print("=" * 60)
    
    # Initialiser OpenAI
    client = OpenAI(api_key=API_KEY)
    
    # Charger les données
    output_dir = Path(__file__).parent.parent / "output"
    parsed_file = output_dir / "contact_33660152593_all_messages.json"
    
    with open(parsed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Fichiers audio
    media_base = Path(r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250710235519")
    audio_messages = [msg for msg in data['messages'] if msg['type'] == 'audio_received']
    
    print(f"\nMessages audio trouvés: {len(audio_messages)}")
    print("Test avec les 3 premiers fichiers audio\n")
    
    # Transcrire les 3 premiers
    results = {}
    for i, msg in enumerate(audio_messages[:3]):
        filename = msg['media']['filename']
        audio_path = media_base / filename
        
        if not audio_path.exists():
            print(f"[{i+1}] {filename} - INTROUVABLE")
            continue
            
        print(f"[{i+1}] Transcription de {filename}...")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="fr"
                )
            
            transcription = response.text
            results[filename] = transcription
            msg['transcription'] = transcription
            
            print(f"   ✓ Transcrit: {transcription[:80]}...")
            
        except Exception as e:
            print(f"   ✗ Erreur: {str(e)}")
    
    # Sauvegarder tout
    transcripts_dir = output_dir / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)
    
    # Transcriptions seules
    with open(transcripts_dir / "transcriptions_33660152593.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Données complètes enrichies
    with open(output_dir / "contact_33660152593_final.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Générer CSV
    print("\nGénération du rapport CSV...")
    csv_file = output_dir / "rapport_33660152593.csv"
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("Date,Type,Contenu,Fichier Audio,Transcription\n")
        
        for msg in data['messages']:
            date = msg.get('timestamp', '')
            
            if msg['type'] == 'text_received':
                content = msg.get('content', '').replace('"', '""')
                f.write(f'"{date}","Texte","{content}","",""\n')
            else:
                filename = msg['media']['filename']
                transcription = msg.get('transcription', '').replace('"', '""')
                f.write(f'"{date}","Audio","","{filename}","{transcription}"\n')
    
    # Générer TXT
    print("Génération du rapport TXT...")
    txt_file = output_dir / "rapport_33660152593.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("RAPPORT WHATSAPP - +33 6 60 15 25 93\n")
        f.write("=" * 70 + "\n")
        f.write(f"Total messages: {len(data['messages'])}\n")
        f.write(f"Messages texte: {data['stats']['text_messages']}\n")
        f.write(f"Messages audio: {data['stats']['audio_messages']}\n")
        f.write("=" * 70 + "\n\n")
        
        for msg in data['messages']:
            f.write(f"Date: {msg['timestamp']}\n")
            
            if msg['type'] == 'text_received':
                f.write("Type: Texte\n")
                f.write(f"Message: {msg['content']}\n")
            else:
                f.write("Type: Audio\n")
                f.write(f"Fichier: {msg['media']['filename']}\n")
                if msg.get('transcription'):
                    f.write(f"Transcription: {msg['transcription']}\n")
            
            f.write("-" * 50 + "\n\n")
    
    print(f"\n✓ Rapport CSV: {csv_file}")
    print(f"✓ Rapport TXT: {txt_file}")
    print(f"✓ Données JSON: {output_dir / 'contact_33660152593_final.json'}")
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLET TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)

if __name__ == "__main__":
    main()