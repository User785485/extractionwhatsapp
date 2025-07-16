import os
import re
import csv
import glob
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

def extract_messages_from_html(html_file):
    """Extraire les messages d'un fichier HTML WhatsApp"""
    messages = []
    
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # Nom du contact
    contact_elem = soup.find('h3')
    contact_name = contact_elem.text.strip() if contact_elem else Path(html_file).stem
    
    current_date = None
    
    for element in soup.find_all(['p', 'table']):
        # Date
        if element.name == 'p' and 'class' in element.attrs and 'date' in element.attrs['class']:
            date_match = re.search(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}', element.text)
            if date_match:
                current_date = date_match.group()
        
        # Message texte reçu (triangle-isosceles sans 2)
        elif element.name == 'p' and 'class' in element.attrs and element.attrs['class'] == ['triangle-isosceles']:
            if current_date:
                messages.append({
                    'contact': contact_name,
                    'date': current_date,
                    'type': 'text',
                    'content': element.text.strip()
                })
        
        # Message audio/média reçu (triangle-isosceles-map sans 2)
        elif element.name == 'table' and 'class' in element.attrs and element.attrs['class'] == ['triangle-isosceles-map']:
            if current_date:
                link = element.find('a')
                if link and 'href' in link.attrs:
                    file_name = os.path.basename(link['href'])
                    
                    # Identifier le type
                    if file_name.endswith(('.opus', '.m4a', '.mp3')):
                        msg_type = 'audio'
                    elif file_name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        msg_type = 'image'
                    elif file_name.endswith(('.mp4', '.mov', '.avi')):
                        msg_type = 'video'
                    else:
                        msg_type = 'document'
                    
                    messages.append({
                        'contact': contact_name,
                        'date': current_date,
                        'type': msg_type,
                        'content': f'[{msg_type.upper()}]',
                        'filename': file_name
                    })
    
    return messages

def main():
    # Chemins
    html_dir = r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp"
    media_dir = r"C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250713161648"
    output_dir = r"C:\Users\Moham\Desktop\DataLeads"
    
    # Créer le dossier de sortie
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtenir les 10 premiers fichiers HTML
    html_files = sorted(glob.glob(os.path.join(html_dir, '*.html')))[:10]
    print(f"Extraction des {len(html_files)} premières conversations WhatsApp\n")
    
    # Résultats
    all_messages = []
    stats = {
        'total_files': len(html_files),
        'total_messages': 0,
        'text_messages': 0,
        'audio_messages': 0,
        'image_messages': 0,
        'video_messages': 0,
        'document_messages': 0
    }
    
    # Traiter chaque fichier
    for i, html_file in enumerate(html_files, 1):
        contact_name = Path(html_file).stem
        print(f"[{i:2d}/10] {contact_name}")
        
        try:
            messages = extract_messages_from_html(html_file)
            
            if messages:
                print(f"        -> {len(messages)} messages reçus")
                
                # Compter par type
                for msg in messages:
                    if msg['type'] == 'text':
                        stats['text_messages'] += 1
                    elif msg['type'] == 'audio':
                        stats['audio_messages'] += 1
                        # Ajouter le chemin complet
                        msg['audio_path'] = os.path.join(media_dir, msg['filename'])
                    elif msg['type'] == 'image':
                        stats['image_messages'] += 1
                    elif msg['type'] == 'video':
                        stats['video_messages'] += 1
                    else:
                        stats['document_messages'] += 1
                
                all_messages.extend(messages)
                stats['total_messages'] += len(messages)
            else:
                print(f"        -> Aucun message reçu")
                
        except Exception as e:
            print(f"        -> Erreur: {e}")
    
    print(f"\n{'='*60}")
    print(f"RÉSUMÉ DE L'EXTRACTION:")
    print(f"- Conversations traitées: {stats['total_files']}")
    print(f"- Messages reçus total: {stats['total_messages']}")
    print(f"  - Texte: {stats['text_messages']}")
    print(f"  - Audio: {stats['audio_messages']}")
    print(f"  - Images: {stats['image_messages']}")
    print(f"  - Vidéos: {stats['video_messages']}")
    print(f"  - Documents: {stats['document_messages']}")
    print(f"{'='*60}\n")
    
    # Sauvegarder en CSV
    csv_file = os.path.join(output_dir, '10_premieres_conversations_extraites.csv')
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        if all_messages:
            fieldnames = ['Contact', 'Date', 'Type', 'Message', 'Fichier']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for msg in all_messages:
                row = {
                    'Contact': msg['contact'],
                    'Date': msg['date'],
                    'Type': msg['type'].upper(),
                    'Message': msg['content'] if msg['type'] == 'text' else f"[{msg['type'].upper()}]",
                    'Fichier': msg.get('filename', '')
                }
                writer.writerow(row)
    
    print(f"[OK] CSV créé: {csv_file}")
    
    # Rapport détaillé en TXT
    txt_file = os.path.join(output_dir, '10_premieres_conversations_rapport.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("RAPPORT D'EXTRACTION - 10 PREMIÈRES CONVERSATIONS WHATSAPP\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date d'extraction: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Dossier source: {html_dir}\n")
        f.write(f"Dossier média: {media_dir}\n\n")
        
        f.write("STATISTIQUES GLOBALES:\n")
        f.write("-" * 30 + "\n")
        f.write(f"Conversations analysées: {stats['total_files']}\n")
        f.write(f"Total messages reçus: {stats['total_messages']}\n")
        f.write(f"  - Messages texte: {stats['text_messages']}\n")
        f.write(f"  - Messages audio: {stats['audio_messages']}\n")
        f.write(f"  - Images: {stats['image_messages']}\n")
        f.write(f"  - Vidéos: {stats['video_messages']}\n")
        f.write(f"  - Documents: {stats['document_messages']}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        # Détails par contact
        contacts = {}
        for msg in all_messages:
            contact = msg['contact']
            if contact not in contacts:
                contacts[contact] = {
                    'messages': [],
                    'audio_count': 0,
                    'text_count': 0,
                    'media_count': 0
                }
            
            contacts[contact]['messages'].append(msg)
            if msg['type'] == 'audio':
                contacts[contact]['audio_count'] += 1
            elif msg['type'] == 'text':
                contacts[contact]['text_count'] += 1
            else:
                contacts[contact]['media_count'] += 1
        
        # Top 10 contacts par nombre de messages
        sorted_contacts = sorted(contacts.items(), key=lambda x: len(x[1]['messages']), reverse=True)
        
        f.write("TOP 10 CONTACTS (par nombre de messages reçus):\n")
        f.write("-" * 50 + "\n")
        for i, (contact, data) in enumerate(sorted_contacts[:10], 1):
            total = len(data['messages'])
            f.write(f"{i:2d}. {contact}: {total} messages\n")
            f.write(f"    - Texte: {data['text_count']}\n")
            f.write(f"    - Audio: {data['audio_count']}\n")
            f.write(f"    - Autres médias: {data['media_count']}\n\n")
        
        # Messages audio à transcrire
        audio_messages = [m for m in all_messages if m['type'] == 'audio']
        if audio_messages:
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"MESSAGES AUDIO À TRANSCRIRE ({len(audio_messages)} total):\n")
            f.write("-" * 50 + "\n\n")
            
            for i, msg in enumerate(audio_messages, 1):
                f.write(f"{i}. Contact: {msg['contact']}\n")
                f.write(f"   Date: {msg['date']}\n")
                f.write(f"   Fichier: {msg['filename']}\n")
                f.write(f"   Chemin complet: {msg.get('audio_path', 'N/A')}\n")
                
                # Vérifier si le fichier existe
                if 'audio_path' in msg and os.path.exists(msg['audio_path']):
                    size = os.path.getsize(msg['audio_path']) / 1024
                    f.write(f"   Taille: {size:.1f} KB\n")
                    f.write(f"   Status: [OK] Fichier trouvé\n")
                else:
                    f.write(f"   Status: [X] Fichier non trouvé\n")
                
                f.write("\n")
    
    print(f"[OK] Rapport créé: {txt_file}")
    
    # Liste des audios uniquement
    if audio_messages:
        audio_list_file = os.path.join(output_dir, 'liste_audio_a_transcrire.csv')
        with open(audio_list_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Contact', 'Date', 'Fichier', 'Chemin_Complet', 'Existe'])
            writer.writeheader()
            
            for msg in audio_messages:
                exists = 'OUI' if 'audio_path' in msg and os.path.exists(msg['audio_path']) else 'NON'
                writer.writerow({
                    'Contact': msg['contact'],
                    'Date': msg['date'],
                    'Fichier': msg['filename'],
                    'Chemin_Complet': msg.get('audio_path', ''),
                    'Existe': exists
                })
        
        print(f"[OK] Liste audio créée: {audio_list_file}")
        print(f"\n-> {len(audio_messages)} messages audio trouvés")
        existing = sum(1 for m in audio_messages if 'audio_path' in m and os.path.exists(m['audio_path']))
        print(f"-> {existing} fichiers audio existants sur le disque")

if __name__ == "__main__":
    main()