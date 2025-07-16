#!/usr/bin/env python3
"""
Transcription directe des fichiers OPUS avec Whisper API
"""

import os
import sys
import json
from pathlib import Path
import openai
from typing import Dict, List
import time

def transcribe_opus_files(audio_files: List[Path], api_key: str) -> Dict:
    """Transcrire directement les fichiers OPUS"""
    
    openai.api_key = api_key
    results = {}
    
    for i, audio_path in enumerate(audio_files):
        print(f"\n[{i+1}/{len(audio_files)}] Transcription de {audio_path.name}...")
        
        try:
            # Ouvrir et transcrire le fichier
            with open(audio_path, 'rb') as audio_file:
                response = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="fr",
                    response_format="json"
                )
            
            # Extraire le texte
            transcription = response.text if hasattr(response, 'text') else str(response)
            
            results[audio_path.name] = {
                'text': transcription,
                'file': str(audio_path),
                'timestamp': time.time()
            }
            
            print(f"  ✓ Transcrit: {transcription[:100]}...")
            
        except Exception as e:
            print(f"  ✗ Erreur: {str(e)}")
            results[audio_path.name] = {
                'error': str(e),
                'file': str(audio_path)
            }
    
    return results

def main():
    """Point d'entrée principal"""
    
    # Vérifier la clé API
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERREUR: OPENAI_API_KEY non définie!")
        sys.exit(1)
    
    print("=" * 60)
    print("TRANSCRIPTION DIRECTE DES FICHIERS OPUS")
    print("=" * 60)
    
    # Charger les données du contact
    output_dir = Path(__file__).parent.parent / "output"
    parsed_file = output_dir / "contact_33660152593_all_messages.json"
    
    with open(parsed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extraire les fichiers audio
    media_base = Path(r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250710235519")
    audio_files = []
    
    for msg in data['messages']:
        if msg['type'] == 'audio_received' and msg.get('media'):
            filename = msg['media']['filename']
            audio_path = media_base / filename
            if audio_path.exists():
                audio_files.append(audio_path)
    
    print(f"\nFichiers audio trouvés: {len(audio_files)}")
    
    # Limiter à 5 pour le test
    test_files = audio_files[:5]
    print(f"Test avec {len(test_files)} fichiers")
    
    # Transcrire
    print("\nDémarrage des transcriptions...")
    results = transcribe_opus_files(test_files, api_key)
    
    # Sauvegarder les résultats
    transcripts_file = output_dir / "transcripts" / "33660152593_opus_transcripts.json"
    transcripts_file.parent.mkdir(exist_ok=True)
    
    with open(transcripts_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Transcriptions sauvegardées: {transcripts_file}")
    
    # Enrichir les données originales
    for msg in data['messages']:
        if msg['type'] == 'audio_received' and msg.get('media'):
            filename = msg['media']['filename']
            if filename in results and 'text' in results[filename]:
                msg['transcription'] = results[filename]['text']
    
    # Sauvegarder données enrichies
    enriched_file = output_dir / "contact_33660152593_with_transcriptions.json"
    with open(enriched_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Données enrichies sauvegardées: {enriched_file}")
    
    # Générer rapports CSV et TXT
    print("\nGénération des rapports...")
    
    # CSV
    csv_file = output_dir / "contact_33660152593_final.csv"
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("Date,Type,Contenu,Transcription\n")
        for msg in data['messages']:
            date = msg.get('timestamp', '')
            msg_type = 'Audio' if msg['type'] == 'audio_received' else 'Texte'
            content = msg.get('content', '')
            transcription = msg.get('transcription', '')
            
            # Échapper les guillemets
            content = content.replace('"', '""')
            transcription = transcription.replace('"', '""')
            
            f.write(f'"{date}","{msg_type}","{content}","{transcription}"\n')
    
    print(f"✓ CSV généré: {csv_file}")
    
    # TXT
    txt_file = output_dir / "contact_33660152593_final.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("RAPPORT DE CONVERSATION - +33 6 60 15 25 93\n")
        f.write("=" * 60 + "\n\n")
        
        for msg in data['messages']:
            f.write(f"Date: {msg.get('timestamp', 'N/A')}\n")
            
            if msg['type'] == 'text_received':
                f.write(f"Type: Message texte\n")
                f.write(f"Contenu: {msg.get('content', '')}\n")
            else:
                f.write(f"Type: Message audio\n")
                f.write(f"Fichier: {msg['media']['filename']}\n")
                if msg.get('transcription'):
                    f.write(f"Transcription: {msg['transcription']}\n")
            
            f.write("-" * 40 + "\n\n")
    
    print(f"✓ TXT généré: {txt_file}")
    
    print("\n" + "=" * 60)
    print("WORKFLOW COMPLET TERMINÉ AVEC SUCCÈS!")
    print("=" * 60)

if __name__ == "__main__":
    main()