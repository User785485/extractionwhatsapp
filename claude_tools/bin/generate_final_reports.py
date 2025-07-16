#!/usr/bin/env python3
"""
Génération des rapports finaux CSV et TXT
"""

import json
from pathlib import Path
from datetime import datetime

def main():
    print("=" * 60)
    print("GÉNÉRATION DES RAPPORTS FINAUX")
    print("=" * 60)
    
    # Charger les données
    output_dir = Path(__file__).parent.parent / "output"
    parsed_file = output_dir / "contact_33660152593_all_messages.json"
    
    with open(parsed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\nContact: +33 6 60 15 25 93")
    print(f"Total messages: {data['received_count']}")
    print(f"Messages texte: {data['stats']['text_messages']}")
    print(f"Messages audio: {data['stats']['audio_messages']}")
    
    # Générer CSV
    print("\n[1] Génération du fichier CSV...")
    csv_file = output_dir / "rapport_final_33660152593.csv"
    
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        # En-têtes
        f.write("Date;Heure;Type;Contenu;Fichier Audio;Durée (estimée)\n")
        
        for msg in data['messages']:
            # Parser la date/heure
            timestamp = msg.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    date = dt.strftime("%d/%m/%Y")
                    heure = dt.strftime("%H:%M")
                except:
                    date = timestamp.split('T')[0] if 'T' in timestamp else timestamp
                    heure = timestamp.split('T')[1][:5] if 'T' in timestamp else ''
            else:
                date = heure = ''
            
            if msg['type'] == 'text_received':
                content = msg.get('content', '').replace(';', ',').replace('\n', ' ')
                f.write(f"{date};{heure};Message texte;{content};;\n")
            else:
                filename = msg['media']['filename']
                # Estimation durée (entre 30s et 2min pour chaque audio)
                duree = "~1min"
                f.write(f"{date};{heure};Message audio;;{filename};{duree}\n")
    
    print(f"   ✓ CSV créé: {csv_file.name}")
    
    # Générer TXT
    print("\n[2] Génération du fichier TXT...")
    txt_file = output_dir / "rapport_final_33660152593.txt"
    
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("╔" + "═" * 68 + "╗\n")
        f.write("║     RAPPORT COMPLET WHATSAPP - CONTACT +33 6 60 15 25 93          ║\n")
        f.write("╚" + "═" * 68 + "╝\n\n")
        
        f.write(f"Date d'extraction : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"Période analysée  : {data['messages'][0]['timestamp'][:10]} à {data['messages'][-1]['timestamp'][:10]}\n")
        f.write("\n")
        
        f.write("STATISTIQUES\n")
        f.write("-" * 40 + "\n")
        f.write(f"• Messages reçus totaux : {data['received_count']}\n")
        f.write(f"• Messages texte       : {data['stats']['text_messages']}\n")
        f.write(f"• Messages audio       : {data['stats']['audio_messages']}\n")
        f.write(f"• Mots totaux (texte)  : {data['stats']['total_words']}\n")
        f.write("\n")
        
        f.write("DÉTAIL DES MESSAGES\n")
        f.write("=" * 70 + "\n\n")
        
        current_date = None
        
        for msg in data['messages']:
            # Grouper par date
            msg_date = msg['timestamp'][:10] if msg['timestamp'] else ''
            if msg_date != current_date:
                current_date = msg_date
                f.write(f"\n▶ {msg_date}\n")
                f.write("─" * 30 + "\n\n")
            
            # Heure
            time = msg['timestamp'][11:16] if msg['timestamp'] and len(msg['timestamp']) > 11 else ''
            f.write(f"[{time}] ")
            
            if msg['type'] == 'text_received':
                f.write(f"📝 TEXTE: {msg['content']}\n")
            else:
                f.write(f"🎤 AUDIO: {msg['media']['filename']}\n")
                f.write(f"         (Fichier audio non transcrit - clé API requise)\n")
            
            f.write("\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("FIN DU RAPPORT\n")
    
    print(f"   ✓ TXT créé: {txt_file.name}")
    
    # Créer aussi un fichier de synthèse
    print("\n[3] Création du fichier de synthèse...")
    summary_file = output_dir / "synthese_33660152593.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("SYNTHÈSE CONVERSATION WHATSAPP\n")
        f.write("Contact: +33 6 60 15 25 93\n")
        f.write("─" * 40 + "\n\n")
        
        f.write("Cette conversation contient:\n")
        f.write(f"• {data['stats']['text_messages']} messages texte\n")
        f.write(f"• {data['stats']['audio_messages']} messages audio\n\n")
        
        f.write("Messages texte reçus:\n")
        for msg in data['messages']:
            if msg['type'] == 'text_received':
                f.write(f"  - {msg['timestamp'][:10]}: {msg['content']}\n")
        
        f.write("\nFichiers audio reçus:\n")
        audio_count = 0
        for msg in data['messages']:
            if msg['type'] == 'audio_received':
                audio_count += 1
                f.write(f"  {audio_count}. {msg['media']['filename']} ({msg['timestamp'][:16]})\n")
                if audio_count >= 10:
                    f.write(f"  ... et {data['stats']['audio_messages'] - 10} autres fichiers audio\n")
                    break
    
    print(f"   ✓ Synthèse créée: {summary_file.name}")
    
    print("\n" + "=" * 60)
    print("RAPPORTS GÉNÉRÉS AVEC SUCCÈS!")
    print("=" * 60)
    print(f"\nFichiers créés dans: {output_dir}")
    print("  - rapport_final_33660152593.csv")
    print("  - rapport_final_33660152593.txt") 
    print("  - synthese_33660152593.txt")
    print("\nNote: Pour transcrire les messages audio, une clé API OpenAI valide est requise.")

if __name__ == "__main__":
    main()