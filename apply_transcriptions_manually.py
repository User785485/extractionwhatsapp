#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour appliquer manuellement les transcriptions aux fichiers CSV/TXT
"""

import os
import json
import csv
import re

def load_transcriptions(output_dir):
    """Charge toutes les transcriptions disponibles"""
    transcriptions = {}
    
    # Charger d'abord le registre unifié pour avoir accès à toutes les transcriptions
    registry_path = os.path.join(output_dir, ".unified_registry.json")
    registry_transcriptions = {}
    
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = json.load(f)
            registry_transcriptions = registry.get('transcriptions', {})
    
    # Pour chaque contact
    for contact in os.listdir(output_dir):
        contact_path = os.path.join(output_dir, contact)
        if not os.path.isdir(contact_path) or contact.startswith('.'):
            continue
            
        trans_dir = os.path.join(contact_path, "transcriptions")
        if not os.path.exists(trans_dir):
            continue
            
        # Charger toutes les transcriptions pour ce contact
        contact_transcriptions = []
        
        # Parcourir les fichiers de transcriptions
        for file in os.listdir(trans_dir):
            if file.endswith('.txt'):
                file_path = os.path.join(trans_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                contact_transcriptions.append(content)
                
        # Extraire le texte utile des transcriptions
        if contact_transcriptions:
            all_text = []
            for trans in contact_transcriptions:
                # Nettoyer le texte
                lines = trans.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('===') and not line.startswith('---') and not line.startswith('[Fichier:') and not line.startswith('Transcription') and not line.startswith('Période'):
                        all_text.append(line.strip())
            
            if all_text:
                transcriptions[contact] = ' '.join(all_text)
    
    return transcriptions

def update_csv_with_transcriptions(csv_path, transcriptions):
    """Met à jour le CSV avec les transcriptions"""
    
    # Lire le CSV existant
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    if not rows:
        return
    
    # Parcourir chaque ligne (sauf l'en-tête)
    for i in range(1, len(rows)):
        contact = rows[i][0]
        
        if contact in transcriptions:
            # Remplacer [AUDIO] par [AUDIO TRANSCRIT] avec le texte
            for j in range(1, len(rows[i])):
                cell_content = rows[i][j]
                
                # Compter les [AUDIO] dans cette cellule
                audio_pattern = r'\[AUDIO\]\s+\S+'
                matches = list(re.finditer(audio_pattern, cell_content))
                
                if matches:
                    # On a des audios à remplacer
                    trans_text = transcriptions[contact]
                    
                    # Pour simplifier, on va remplacer tous les [AUDIO] received par la transcription complète
                    # Dans un cas réel, il faudrait mapper chaque audio à sa partie spécifique
                    
                    # Diviser la transcription en parts égales selon le nombre d'audios
                    num_audios = len(matches)
                    if num_audios > 0:
                        # Approximation : diviser le texte
                        words = trans_text.split()
                        words_per_audio = max(1, len(words) // num_audios)
                        
                        # Remplacer chaque [AUDIO]
                        for idx, match in enumerate(matches):
                            start_idx = idx * words_per_audio
                            end_idx = min(start_idx + words_per_audio, len(words)) if idx < num_audios - 1 else len(words)
                            
                            if start_idx < len(words):
                                audio_trans = ' '.join(words[start_idx:end_idx])
                                
                                # Limiter à 500 caractères par audio
                                if len(audio_trans) > 500:
                                    audio_trans = audio_trans[:497] + "..."
                                
                                replacement = f'[AUDIO TRANSCRIT] "{audio_trans}"'
                                cell_content = cell_content.replace(match.group(0), replacement, 1)
                    
                    rows[i][j] = cell_content
    
    # Sauvegarder le CSV mis à jour
    output_path = csv_path.replace('.csv', '_avec_transcriptions.csv')
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    
    print(f"CSV mis à jour sauvegardé : {output_path}")
    
    # Créer aussi une version Excel
    try:
        import pandas as pd
        df = pd.read_csv(output_path, encoding='utf-8')
        excel_path = output_path.replace('.csv', '.xlsx')
        df.to_excel(excel_path, index=False)
        print(f"Version Excel créée : {excel_path}")
    except Exception as e:
        print(f"Impossible de créer la version Excel: {e}")
        print("Assurez-vous que pandas est installé: pip install pandas openpyxl")

def main():
    output_dir = r"C:\Users\Moham\Desktop\DataLeads"
    csv_path = os.path.join(output_dir, "transcriptions_speciales.csv")
    
    print("=== APPLICATION MANUELLE DES TRANSCRIPTIONS ===\n")
    
    # 1. Charger les transcriptions
    print("Chargement des transcriptions...")
    transcriptions = load_transcriptions(output_dir)
    
    print(f"Transcriptions trouvées pour {len(transcriptions)} contacts:")
    for contact, text in transcriptions.items():
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"  - {contact}: {len(text)} caractères")
        print(f"    Aperçu: {preview}")
    
    # 2. Mettre à jour le CSV
    if os.path.exists(csv_path):
        print(f"\nMise à jour du CSV...")
        update_csv_with_transcriptions(csv_path, transcriptions)
    else:
        print(f"\nERREUR: CSV non trouvé : {csv_path}")

if __name__ == "__main__":
    main()
