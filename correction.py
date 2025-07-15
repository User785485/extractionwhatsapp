#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour vérifier que Ilhame_webi404 est correctement configuré
et que tout sera bien exporté
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

def clean_text(text):
    """Nettoie le texte pour éviter les problèmes d'encodage"""
    if not text:
        return ""
    # Remplacer les caractères problématiques
    result = ""
    for char in text:
        if ord(char) < 128:
            result += char
        else:
            result += "?"
    return result

def verify_ilhame_status():
    output_dir = r"C:\Datalead3webidu13juillet"
    contact_name = "Ilhame_webi404"
    
    print("="*80)
    print(f"VERIFICATION DU STATUT DE {contact_name}")
    print("="*80)
    print(f"Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    contact_path = Path(output_dir) / contact_name
    
    if not contact_path.exists():
        print(f"[ERREUR] Le dossier {contact_name} n'existe pas!")
        return
    
    print(f"\n[OK] Dossier trouvé: {contact_path}")
    
    # 1. Vérifier conversation.json
    print("\n" + "-"*60)
    print("1. VERIFICATION DE conversation.json")
    print("-"*60)
    
    conv_file = contact_path / "conversation.json"
    if not conv_file.exists():
        print("[ERREUR] conversation.json n'existe pas!")
        return
    
    try:
        with open(conv_file, 'r', encoding='utf-8') as f:
            messages = json.load(f)
        
        print(f"[OK] conversation.json lu avec succès")
        print(f"     Nombre total de messages: {len(messages)}")
        
        # Analyser les messages
        text_messages = []
        audio_messages = []
        
        for i, msg in enumerate(messages):
            if msg.get('direction') == 'received':
                if msg.get('type') == 'text':
                    text_messages.append({
                        'index': i,
                        'content': msg.get('content', ''),
                        'date': msg.get('date', ''),
                        'time': msg.get('time', '')
                    })
                elif msg.get('type') == 'audio':
                    media_path = msg.get('media_path')
                    uuid = None
                    if media_path:
                        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', str(media_path))
                        if uuid_match:
                            uuid = uuid_match.group(1)
                    
                    audio_messages.append({
                        'index': i,
                        'media_path': media_path,
                        'uuid': uuid,
                        'date': msg.get('date', ''),
                        'time': msg.get('time', '')
                    })
        
        print(f"\nMessages RECUS:")
        print(f"  - Texte: {len(text_messages)}")
        print(f"  - Audio: {len(audio_messages)}")
        
        # Afficher les messages texte
        if text_messages:
            print(f"\nMESSAGES TEXTE RECUS:")
            for txt in text_messages:
                clean_content = clean_text(txt['content'])
                print(f"  [{txt['index']}] {txt['date']} {txt['time']}: {clean_content[:50]}...")
        
        # Vérifier les media_path
        print(f"\nSTATUT DES MEDIA_PATH:")
        null_paths = 0
        valid_paths = 0
        
        for audio in audio_messages:
            if audio['media_path'] is None:
                null_paths += 1
                print(f"  [ERREUR] Message {audio['index']}: media_path = NULL")
            elif audio['uuid']:
                valid_paths += 1
                print(f"  [OK] Message {audio['index']}: UUID = {audio['uuid']}")
            else:
                print(f"  [ATTENTION] Message {audio['index']}: media_path sans UUID = {audio['media_path']}")
        
        if null_paths > 0:
            print(f"\n[PROBLEME] {null_paths} audio(s) avec media_path NULL!")
            print("Ces audios ne seront PAS liés aux transcriptions dans l'export!")
        else:
            print(f"\n[PARFAIT] Tous les media_path sont valides!")
            
    except Exception as e:
        print(f"[ERREUR] Lecture conversation.json: {e}")
        return
    
    # 2. Vérifier les fichiers MP3
    print("\n" + "-"*60)
    print("2. VERIFICATION DES FICHIERS MP3")
    print("-"*60)
    
    mp3_dir = contact_path / "audio_mp3"
    mp3_files = []
    
    if mp3_dir.exists():
        mp3_files = list(mp3_dir.glob("received_*.mp3"))
        print(f"[OK] Dossier audio_mp3 trouvé")
        print(f"     Fichiers MP3: {len(mp3_files)}")
        
        # Extraire les UUID
        mp3_uuids = set()
        for mp3 in mp3_files:
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', mp3.name)
            if uuid_match:
                mp3_uuids.add(uuid_match.group(1))
        
        print(f"     UUID uniques: {len(mp3_uuids)}")
    else:
        print("[ERREUR] Dossier audio_mp3 n'existe pas!")
    
    # 3. Vérifier les transcriptions
    print("\n" + "-"*60)
    print("3. VERIFICATION DES TRANSCRIPTIONS")
    print("-"*60)
    
    trans_dir = contact_path / "transcriptions"
    trans_files = []
    
    if trans_dir.exists():
        trans_files = list(trans_dir.glob("received_*.txt"))
        print(f"[OK] Dossier transcriptions trouvé")
        print(f"     Fichiers TXT: {len(trans_files)}")
        
        # Analyser chaque transcription
        trans_uuids = {}
        for txt in trans_files:
            uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', txt.name)
            if uuid_match:
                uuid = uuid_match.group(1)
                
                # Lire le contenu
                try:
                    content = txt.read_text(encoding='utf-8')
                    lines = content.split('\n')
                    
                    # Chercher le séparateur
                    sep_idx = -1
                    for i, line in enumerate(lines):
                        if '=' * 40 in line:
                            sep_idx = i
                            break
                    
                    if sep_idx >= 0 and sep_idx < len(lines) - 1:
                        trans_text = '\n'.join(lines[sep_idx + 1:]).strip()
                        
                        # Vérifier la qualité
                        is_valid = True
                        reason = "OK"
                        
                        if len(trans_text) < 10:
                            is_valid = False
                            reason = "Trop court"
                        elif any(word in trans_text.lower() for word in ['error', 'api', 'failed']):
                            is_valid = False
                            reason = "Contient erreur"
                        
                        trans_uuids[uuid] = {
                            'file': txt.name,
                            'valid': is_valid,
                            'reason': reason,
                            'length': len(trans_text),
                            'preview': clean_text(trans_text[:50]) + '...' if len(trans_text) > 50 else clean_text(trans_text)
                        }
                except Exception as e:
                    trans_uuids[uuid] = {
                        'file': txt.name,
                        'valid': False,
                        'reason': f"Erreur lecture: {e}",
                        'length': 0
                    }
        
        print(f"\nANALYSE DES TRANSCRIPTIONS:")
        valid_count = sum(1 for t in trans_uuids.values() if t['valid'])
        print(f"  - Valides: {valid_count}")
        print(f"  - Invalides: {len(trans_uuids) - valid_count}")
        
        # Afficher les détails
        for uuid, info in trans_uuids.items():
            status = "[OK]" if info['valid'] else "[ERREUR]"
            print(f"\n  {status} {info['file']}")
            print(f"       Taille: {info['length']} caractères")
            if not info['valid']:
                print(f"       Raison: {info['reason']}")
            else:
                print(f"       Aperçu: {info['preview']}")
                
    else:
        print("[ERREUR] Dossier transcriptions n'existe pas!")
    
    # 4. CORRESPONDANCES
    print("\n" + "-"*60)
    print("4. VERIFICATION DES CORRESPONDANCES")
    print("-"*60)
    
    # Comparer les UUID
    if audio_messages and trans_uuids:
        print("\nCORRESPONDANCE Audio dans conversation.json <-> Transcriptions:")
        
        for audio in audio_messages:
            if audio['uuid']:
                if audio['uuid'] in trans_uuids:
                    trans_info = trans_uuids[audio['uuid']]
                    if trans_info['valid']:
                        print(f"  [OK] Audio {audio['index']} -> Transcription valide")
                    else:
                        print(f"  [PROBLEME] Audio {audio['index']} -> Transcription invalide ({trans_info['reason']})")
                else:
                    print(f"  [MANQUANT] Audio {audio['index']} -> Pas de transcription")
            else:
                print(f"  [IMPOSSIBLE] Audio {audio['index']} -> Pas d'UUID dans media_path")
    
    # 5. PREDICTION DE L'EXPORT
    print("\n" + "-"*60)
    print("5. PREDICTION DE L'EXPORT")
    print("-"*60)
    
    print("\nCe qui apparaîtra dans export_simple.csv pour Ilhame_webi404:")
    
    # Simuler ce que fera SimpleExporter
    export_content = []
    
    # D'abord les messages texte
    for txt in text_messages:
        export_content.append(txt['content'])
    
    # Puis les audios avec leurs transcriptions
    for audio in audio_messages:
        if audio['uuid'] and audio['uuid'] in trans_uuids:
            trans_info = trans_uuids[audio['uuid']]
            if trans_info['valid']:
                export_content.append(f"[AUDIO] {clean_text(trans_info['preview'])}")
            else:
                export_content.append("[AUDIO non transcrit]")
        else:
            export_content.append("[AUDIO non transcrit]")
    
    try:
        joined_content = ' '.join(export_content)
        # Assurer que tout est proprement nettoyé
        clean_joined = clean_text(joined_content)
        print(f"\nContenu prévu: {clean_joined[:200]}...")
    except Exception as e:
        print(f"\nErreur lors de l'affichage du contenu prévu: {e}")
        print("Longueur du contenu:", len(export_content), "éléments")
    
    # VERDICT FINAL
    print("\n" + "="*80)
    print("VERDICT FINAL:")
    print("="*80)
    
    all_good = True
    
    if null_paths > 0:
        print("[PROBLEME] Des media_path sont NULL - réparer avec le script fix_missing_media_paths.py")
        all_good = False
    
    invalid_trans = len([t for t in trans_uuids.values() if not t['valid']])
    if invalid_trans > 0:
        print(f"[PROBLEME] {invalid_trans} transcriptions invalides - seront retranscrites")
        all_good = False
    
    if len(mp3_files) != len(trans_files):
        print(f"[ATTENTION] Nombre de MP3 ({len(mp3_files)}) != Nombre de transcriptions ({len(trans_files)})")
        all_good = False
    
    if all_good:
        print("[PARFAIT] Ilhame_webi404 est correctement configuré!")
        print("Tous les messages texte et transcriptions apparaîtront dans l'export!")
    else:
        print("\nDes corrections sont nécessaires pour un export complet.")

if __name__ == "__main__":
    verify_ilhame_status()
    input("\n\nAppuyez sur Entree pour terminer...")