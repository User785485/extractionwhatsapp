import os
import sys
import glob
import json
import csv
from pathlib import Path
from datetime import datetime

# Ajouter src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from parsers.mobiletrans_parser import MobileTransParser

def main():
    # Chemins
    html_dir = r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp"
    media_dir = r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250713161648"
    output_dir = r"C:\Users\Moham\Desktop\DataLeads"
    
    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtenir les 10 premiers fichiers HTML
    html_files = glob.glob(os.path.join(html_dir, '*.html'))[:10]
    print(f"Traitement de {len(html_files)} fichiers...")
    
    # Initialiser le parser
    parser = MobileTransParser()
    
    # Résultats
    all_messages = []
    stats = {
        'total_files': len(html_files),
        'total_messages': 0,
        'text_messages': 0,
        'audio_messages': 0,
        'other_media': 0
    }
    
    # Traiter chaque fichier
    for i, html_file in enumerate(html_files, 1):
        contact_name = Path(html_file).stem
        print(f"\n[{i}/10] {contact_name}")
        
        try:
            # Parser le fichier
            messages_data = parser.parse(Path(html_file))
            
            if messages_data and contact_name in messages_data:
                messages = messages_data[contact_name]
                
                # Filtrer les messages reçus
                received = [m for m in messages if m.get('type') == 'received']
                
                print(f"  - Total: {len(messages)} messages")
                print(f"  - Reçus: {len(received)} messages")
                
                # Ajouter le contact aux messages
                for msg in received:
                    msg['contact'] = contact_name
                    
                    # Compter les types
                    if msg.get('media_type') == 'audio':
                        stats['audio_messages'] += 1
                        # Ajouter le chemin complet du fichier audio
                        if msg.get('media_filename'):
                            msg['audio_path'] = os.path.join(media_dir, msg['media_filename'])
                    elif msg.get('media_type'):
                        stats['other_media'] += 1
                    else:
                        stats['text_messages'] += 1
                
                all_messages.extend(received)
                stats['total_messages'] += len(received)
                
        except Exception as e:
            print(f"  - Erreur: {e}")
    
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ:")
    print(f"- Fichiers traités: {stats['total_files']}")
    print(f"- Messages reçus total: {stats['total_messages']}")
    print(f"  - Texte: {stats['text_messages']}")
    print(f"  - Audio: {stats['audio_messages']}")
    print(f"  - Autres médias: {stats['other_media']}")
    print(f"{'='*60}\n")
    
    # Sauvegarder en CSV
    csv_file = os.path.join(output_dir, '10_premieres_conversations.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        if all_messages:
            # Colonnes simplifiées
            fieldnames = ['Contact', 'Date', 'Type', 'Message', 'Fichier_Audio']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for msg in all_messages:
                row = {
                    'Contact': msg.get('contact', ''),
                    'Date': msg.get('timestamp', ''),
                    'Type': 'Audio' if msg.get('media_type') == 'audio' else 'Texte',
                    'Message': msg.get('content', '[Message audio - voir colonne Fichier_Audio]') if msg.get('media_type') != 'audio' else '[Audio]',
                    'Fichier_Audio': msg.get('audio_path', '') if msg.get('media_type') == 'audio' else ''
                }
                writer.writerow(row)
    
    print(f"CSV sauvegardé: {csv_file}")
    
    # Sauvegarder en TXT
    txt_file = os.path.join(output_dir, '10_premieres_conversations.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("EXTRACTION DES 10 PREMIÈRES CONVERSATIONS WHATSAPP\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date d'extraction: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\nSTATISTIQUES:\n")
        f.write(f"- Fichiers traités: {stats['total_files']}\n")
        f.write(f"- Messages reçus: {stats['total_messages']}\n")
        f.write(f"  - Texte: {stats['text_messages']}\n")
        f.write(f"  - Audio: {stats['audio_messages']}\n")
        f.write(f"  - Autres: {stats['other_media']}\n")
        f.write("=" * 60 + "\n\n")
        
        # Grouper par contact
        contacts = {}
        for msg in all_messages:
            contact = msg.get('contact', 'Unknown')
            if contact not in contacts:
                contacts[contact] = []
            contacts[contact].append(msg)
        
        for contact, messages in contacts.items():
            f.write(f"\nCONTACT: {contact}\n")
            f.write(f"Messages reçus: {len(messages)}\n")
            f.write("-" * 40 + "\n")
            
            # Compter les audios
            audio_count = sum(1 for m in messages if m.get('media_type') == 'audio')
            if audio_count > 0:
                f.write(f"Messages audio: {audio_count}\n")
                f.write("-" * 40 + "\n")
            
            for msg in messages[:10]:  # Limiter à 10 messages par contact dans le TXT
                f.write(f"\nDate: {msg.get('timestamp', 'Unknown')}\n")
                
                if msg.get('media_type') == 'audio':
                    f.write(f"Type: AUDIO\n")
                    f.write(f"Fichier: {msg.get('media_filename', 'unknown')}\n")
                    f.write(f"Emplacement: {msg.get('audio_path', 'non trouvé')}\n")
                else:
                    f.write(f"Message: {msg.get('content', '')}\n")
            
            if len(messages) > 10:
                f.write(f"\n... et {len(messages) - 10} autres messages\n")
            
            f.write("\n" + "=" * 60 + "\n")
    
    print(f"TXT sauvegardé: {txt_file}")
    
    # Sauvegarder les messages audio dans un fichier séparé
    audio_messages = [m for m in all_messages if m.get('media_type') == 'audio']
    if audio_messages:
        audio_file = os.path.join(output_dir, 'messages_audio_a_transcrire.txt')
        with open(audio_file, 'w', encoding='utf-8') as f:
            f.write("MESSAGES AUDIO À TRANSCRIRE\n")
            f.write("=" * 60 + "\n\n")
            
            for i, msg in enumerate(audio_messages, 1):
                f.write(f"{i}. Contact: {msg.get('contact', 'Unknown')}\n")
                f.write(f"   Date: {msg.get('timestamp', 'Unknown')}\n")
                f.write(f"   Fichier: {msg.get('media_filename', 'unknown')}\n")
                f.write(f"   Chemin: {msg.get('audio_path', 'non trouvé')}\n")
                f.write("-" * 40 + "\n")
        
        print(f"\nListe des audios: {audio_file}")
        print(f"Total: {len(audio_messages)} messages audio à transcrire")

if __name__ == "__main__":
    main()