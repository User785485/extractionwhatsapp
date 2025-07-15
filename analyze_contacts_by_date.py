import os
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from collections import defaultdict
import configparser

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%Y-%m-%d %H:%M:%S - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_whatsapp_date(date_str):
    """Convertit une date du format WhatsApp en objet datetime"""
    try:
        # Format WhatsApp: 2024/11/26 11:43
        return datetime.strptime(date_str.strip(), '%Y/%m/%d %H:%M')
    except:
        return None

def is_received_message(css_class, element_str):
    """Détermine si un message est reçu basé sur la classe CSS"""
    # Classes pour messages reçus
    received_classes = ['triangle-isosceles', 'triangle-isosceles-map']
    # Classes pour messages envoyés
    sent_classes = ['triangle-isosceles2', 'triangle-isosceles3', 
                    'triangle-isosceles-map2', 'triangle-isosceles-map3']
    
    if css_class in received_classes:
        return True
    elif css_class in sent_classes:
        return False
    else:
        # Si classe inconnue, analyser le contenu
        if 'left:-176px' in element_str or 'left:-170px' in element_str:
            return True
        elif 'left:208px' in element_str or 'left:170px' in element_str:
            return False
    
    return None

def extract_contact_name(soup):
    """Extrait le nom du contact depuis le HTML"""
    # Essayer le h3
    h3_tag = soup.find('h3')
    if h3_tag and h3_tag.text.strip():
        return h3_tag.text.strip()
    
    # Essayer le titre
    title_tag = soup.find('title')
    if title_tag:
        title = title_tag.text.replace("'s WhatsApp Business", "").replace("'s WhatsApp", "").replace("iPhone's WhatsApp", "")
        return title.strip()
    
    return None

def analyze_html_file(file_path):
    """Analyse un fichier HTML et retourne les infos du contact"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        contact_name = extract_contact_name(soup)
        if not contact_name:
            return None
        
        # Extraire tous les messages avec dates
        date_headers = soup.find_all('p', class_='date')
        
        last_received_date = None
        received_count = 0
        total_messages = 0
        
        for date_header in date_headers:
            # Extraire la date
            date_text = date_header.find('font', color='#b4b4b4')
            if not date_text:
                continue
            
            # Parser la date
            date_match = re.search(r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2})', date_text.text)
            if not date_match:
                continue
            
            message_date = parse_whatsapp_date(date_match.group(1))
            if not message_date:
                continue
            
            # Trouver le message suivant
            next_element = date_header.find_next_sibling(['p', 'table'])
            if not next_element:
                continue
            
            # Déterminer la direction
            css_class = next_element.get('class', [''])[0]
            is_received = is_received_message(css_class, str(next_element))
            
            if is_received is not None:
                total_messages += 1
                if is_received:
                    received_count += 1
                    last_received_date = message_date
        
        return {
            'name': contact_name,
            'file': os.path.basename(file_path),
            'last_received': last_received_date,
            'received_count': received_count,
            'total_messages': total_messages
        }
        
    except Exception as e:
        logger.error(f"Erreur analyse {file_path}: {e}")
        return None

def main():
    # Demander la date de référence
    print("Entrez la date de référence (format: JJ/MM/AAAA HH:MM)")
    print("Exemple: 22/06/2025 22:07")
    date_ref_str = input("Date de référence: ")
    
    try:
        date_reference = datetime.strptime(date_ref_str, '%d/%m/%Y %H:%M')
        logger.info(f"Date de référence: {date_reference}")
    except Exception as e:
        logger.error(f"Erreur format date: {e}")
        print("Format de date invalide. Utilisez JJ/MM/AAAA HH:MM")
        return

    # Lire la configuration
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        html_dir = config.get('Paths', 'html_dir')
    except:
        html_dir = r'C:\Users\Moham\Downloads\iPhone_20250604173341\WhatsApp'
        logger.warning(f"Utilisation du chemin par défaut: {html_dir}")

    # Analyser tous les fichiers HTML
    logger.info(f"Analyse du dossier: {html_dir}")

    contacts_after_date = []
    contacts_before_date = []
    contacts_no_received = []

    if os.path.exists(html_dir):
        html_files = [f for f in os.listdir(html_dir) if f.endswith('.html')]
        logger.info(f"Fichiers HTML trouvés: {len(html_files)}")
        
        for i, html_file in enumerate(html_files):
            if i % 50 == 0:
                logger.info(f"Progression: {i}/{len(html_files)}")
            
            file_path = os.path.join(html_dir, html_file)
            result = analyze_html_file(file_path)
            
            if result:
                if result['last_received']:
                    if result['last_received'] > date_reference:
                        contacts_after_date.append(result)
                    else:
                        contacts_before_date.append(result)
                else:
                    contacts_no_received.append(result)
    else:
        logger.error(f"Dossier introuvable: {html_dir}")
        return

    # Afficher les résultats
    print("\n" + "="*60)
    print(f"RÉSULTATS DE L'ANALYSE - Date référence: {date_reference}")
    print("="*60)

    print(f"\n📊 STATISTIQUES GLOBALES:")
    print(f"  - Total contacts analysés: {len(html_files)}")
    print(f"  - Contacts avec messages reçus APRÈS {date_ref_str}: {len(contacts_after_date)}")
    print(f"  - Contacts avec messages reçus AVANT: {len(contacts_before_date)}")
    print(f"  - Contacts sans messages reçus: {len(contacts_no_received)}")

    # Trier par date du dernier message reçu
    contacts_after_date.sort(key=lambda x: x['last_received'], reverse=True)

    print(f"\n✅ CONTACTS AVEC MESSAGES REÇUS APRÈS {date_ref_str}:")
    print("-"*60)
    for i, contact in enumerate(contacts_after_date[:20], 1):  # Afficher les 20 premiers
        print(f"{i}. {contact['name']}")
        print(f"   Fichier: {contact['file']}")
        print(f"   Dernier reçu: {contact['last_received']}")
        print(f"   Messages reçus: {contact['received_count']}/{contact['total_messages']}")
        print()

    if len(contacts_after_date) > 20:
        print(f"... et {len(contacts_after_date) - 20} autres contacts")

    # Sauvegarder la liste complète
    output_file = f"contacts_apres_{date_reference.strftime('%Y%m%d_%H%M')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'date_reference': date_ref_str,
            'contacts_count': len(contacts_after_date),
            'contacts': contacts_after_date
        }, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n💾 Liste complète sauvegardée dans: {output_file}")

    # Créer aussi un fichier texte simple avec juste les noms
    txt_file = f"contacts_apres_{date_reference.strftime('%Y%m%d_%H%M')}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(f"Contacts avec messages reçus après {date_ref_str}\n")
        f.write("="*60 + "\n\n")
        for contact in contacts_after_date:
            f.write(f"{contact['name']}\n")

    print(f"📄 Liste simple sauvegardée dans: {txt_file}")

if __name__ == "__main__":
    main()
