#!/usr/bin/env python3
"""
Extraction des 10 premiers contacts iPhone
Workflow complet avec analyse et rapport
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Se placer dans src
os.chdir(r"C:\Users\Moham\CascadeProjects\whatsapp_extractor_v2\src")
sys.path.insert(0, ".")

print("=== EXTRACTION DES 10 PREMIERS CONTACTS IPHONE ===")
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

def extract_10_contacts():
    """Extraire les données des 10 premiers contacts"""
    
    from parsers.mobiletrans_parser import MobileTransParser
    from exporters.csv_exporter import CSVExporter
    from exporters.json_exporter import JSONExporter
    from exporters.excel_exporter import ExcelExporter
    from utils.advanced_logger import init_logger, ErrorCategory
    
    # Initialiser le logger
    logger = init_logger(Path("../logs"))
    logger.info("Début extraction 10 premiers contacts iPhone")
    
    # Parser
    parser = MobileTransParser()
    
    # Les 10 premiers fichiers du dossier iPhone
    iphone_dir = Path(r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp")
    
    # Obtenir les 10 premiers fichiers HTML
    all_html_files = sorted(list(iphone_dir.glob("*.html")))[:10]
    
    print(f"\n[INFO] {len(all_html_files)} fichiers sélectionnés pour extraction")
    print("-"*60)
    
    # Variables pour collecter toutes les données
    all_messages = []
    contact_stats = {}
    total_messages = 0
    total_media = 0
    message_types = {}
    
    # Traiter chaque fichier
    for idx, file_path in enumerate(all_html_files, 1):
        print(f"\n[{idx}/10] Traitement: {file_path.name}")
        
        try:
            # Valider le fichier
            if not parser.validate_file(file_path):
                print(f"  [SKIP] Fichier non valide")
                logger.log_file_processing(str(file_path), False, "Validation échouée")
                continue
            
            # Parser le fichier
            contact_messages = parser.parse(file_path)
            
            for contact_name, messages in contact_messages.items():
                msg_count = len(messages)
                total_messages += msg_count
                
                # Stats par contact
                contact_stats[contact_name] = {
                    'message_count': msg_count,
                    'file': file_path.name,
                    'sent': 0,
                    'received': 0,
                    'media_count': 0,
                    'first_message': None,
                    'last_message': None
                }
                
                print(f"  [CONTACT] {contact_name}")
                print(f"  [MESSAGES] {msg_count} messages")
                
                # Analyser les messages
                for msg in messages:
                    # Direction
                    direction = msg.direction.value if hasattr(msg.direction, 'value') else str(msg.direction)
                    if direction == 'sent':
                        contact_stats[contact_name]['sent'] += 1
                    else:
                        contact_stats[contact_name]['received'] += 1
                    
                    # Type de message
                    msg_type = msg.media_type.value if hasattr(msg.media_type, 'value') else str(msg.media_type)
                    message_types[msg_type] = message_types.get(msg_type, 0) + 1
                    
                    # Media
                    if msg_type != 'text':
                        total_media += 1
                        contact_stats[contact_name]['media_count'] += 1
                    
                    # Dates
                    if msg.timestamp:
                        if not contact_stats[contact_name]['first_message'] or msg.timestamp < contact_stats[contact_name]['first_message']:
                            contact_stats[contact_name]['first_message'] = msg.timestamp
                        if not contact_stats[contact_name]['last_message'] or msg.timestamp > contact_stats[contact_name]['last_message']:
                            contact_stats[contact_name]['last_message'] = msg.timestamp
                    
                    # Préparer pour export
                    message_data = {
                        'contact_name': contact_name,
                        'message_id': msg.id,
                        'timestamp': msg.timestamp.isoformat() if msg.timestamp else '',
                        'direction': direction,
                        'message_type': msg_type,
                        'content': msg.content,
                        'media_path': str(msg.media_path) if msg.media_path else '',
                        'media_filename': msg.media_filename or '',
                        'file_source': file_path.name
                    }
                    all_messages.append(message_data)
                
                # Afficher un aperçu
                if messages:
                    print(f"    Premier message: {messages[0].content[:50]}...")
                    print(f"    Envoyés: {contact_stats[contact_name]['sent']}, Reçus: {contact_stats[contact_name]['received']}")
                
                logger.log_contact_processing(contact_name, msg_count, True)
                
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            logger.log_file_processing(str(file_path), False, str(e))
    
    # Résumé global
    print("\n" + "="*60)
    print("=== RÉSUMÉ DE L'EXTRACTION ===")
    print(f"Total contacts: {len(contact_stats)}")
    print(f"Total messages: {total_messages}")
    print(f"Total médias: {total_media}")
    
    print("\n[TYPES DE MESSAGES]")
    for msg_type, count in sorted(message_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {msg_type}: {count}")
    
    print("\n[TOP 5 CONTACTS PAR NOMBRE DE MESSAGES]")
    top_contacts = sorted(contact_stats.items(), key=lambda x: x[1]['message_count'], reverse=True)[:5]
    for contact, stats in top_contacts:
        print(f"  {contact}: {stats['message_count']} messages")
    
    # Export des données
    if all_messages:
        print("\n[EXPORT DES DONNÉES]")
        output_dir = Path("../extraction_10_contacts")
        output_dir.mkdir(exist_ok=True)
        
        # Timestamp pour les noms de fichiers
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV
        csv_exporter = CSVExporter()
        csv_file = output_dir / f"10_contacts_{timestamp}.csv"
        if csv_exporter.export(all_messages, csv_file):
            print(f"  [OK] CSV: {csv_file} ({csv_file.stat().st_size:,} bytes)")
            logger.log_export_creation("CSV", str(csv_file), len(all_messages), True)
        
        # JSON
        json_exporter = JSONExporter()
        json_file = output_dir / f"10_contacts_{timestamp}.json"
        if json_exporter.export(all_messages, json_file):
            print(f"  [OK] JSON: {json_file} ({json_file.stat().st_size:,} bytes)")
            logger.log_export_creation("JSON", str(json_file), len(all_messages), True)
        
        # Excel
        excel_exporter = ExcelExporter()
        excel_file = output_dir / f"10_contacts_{timestamp}.xlsx"
        if excel_exporter.export(all_messages, excel_file):
            print(f"  [OK] Excel: {excel_file} ({excel_file.stat().st_size:,} bytes)")
            logger.log_export_creation("Excel", str(excel_file), len(all_messages), True)
        
        # Rapport détaillé
        report_file = output_dir / f"rapport_analyse_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("RAPPORT D'ANALYSE - EXTRACTION 10 CONTACTS IPHONE\n")
            f.write("="*60 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Fichiers analysés: {len(all_html_files)}\n")
            f.write(f"Contacts extraits: {len(contact_stats)}\n")
            f.write(f"Messages totaux: {total_messages}\n")
            f.write(f"Médias totaux: {total_media}\n\n")
            
            f.write("DÉTAILS PAR CONTACT\n")
            f.write("-"*60 + "\n")
            for contact, stats in sorted(contact_stats.items(), key=lambda x: x[1]['message_count'], reverse=True):
                f.write(f"\n{contact}:\n")
                f.write(f"  - Messages: {stats['message_count']}\n")
                f.write(f"  - Envoyés: {stats['sent']}\n")
                f.write(f"  - Reçus: {stats['received']}\n")
                f.write(f"  - Médias: {stats['media_count']}\n")
                if stats['first_message']:
                    f.write(f"  - Premier message: {stats['first_message'].strftime('%Y-%m-%d %H:%M')}\n")
                if stats['last_message']:
                    f.write(f"  - Dernier message: {stats['last_message'].strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"  - Fichier source: {stats['file']}\n")
        
        print(f"  [OK] Rapport: {report_file}")
        
        print(f"\n[SUCCESS] Tous les fichiers ont été sauvegardés dans:")
        print(f"  {output_dir.absolute()}")
    
    # Statistiques du logger
    stats = logger.get_statistics()
    print(f"\n[STATISTIQUES DE SESSION]")
    print(f"  Opérations réussies: {stats['successful_operations']}")
    print(f"  Opérations échouées: {stats['failed_operations']}")
    print(f"  Taux de succès: {stats['success_rate_percent']}%")
    print(f"  Durée: {stats['elapsed_time_seconds']:.2f}s")
    
    logger.close()
    
    return {
        'total_contacts': len(contact_stats),
        'total_messages': total_messages,
        'total_media': total_media,
        'contact_stats': contact_stats,
        'message_types': message_types
    }

if __name__ == "__main__":
    try:
        results = extract_10_contacts()
        print("\n" + "="*60)
        print("[EXTRACTION TERMINÉE AVEC SUCCÈS]")
        print("="*60)
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] {str(e)}")
        import traceback
        traceback.print_exc()