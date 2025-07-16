#!/usr/bin/env python3
"""
Extraction rapide des 10 premiers contacts
"""

import os
import sys
from pathlib import Path

os.chdir(r"C:\Users\Moham\CascadeProjects\whatsapp_extractor_v2\src")
sys.path.insert(0, ".")

print("=== EXTRACTION RAPIDE - 10 PREMIERS CONTACTS ===\n")

from parsers.mobiletrans_parser import MobileTransParser
from exporters.csv_exporter import CSVExporter

# Parser
parser = MobileTransParser()

# Dossier iPhone
iphone_dir = Path(r"C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp")

# Les 10 premiers fichiers
files = sorted(list(iphone_dir.glob("*.html")))[:10]

print(f"[INFO] Extraction de {len(files)} fichiers\n")

# Données globales
all_data = []
summary = []

# Traiter chaque fichier
for i, file in enumerate(files, 1):
    print(f"[{i}/10] {file.name}")
    
    try:
        if parser.validate_file(file):
            contact_msgs = parser.parse(file)
            
            for contact, messages in contact_msgs.items():
                count = len(messages)
                print(f"  -> {contact}: {count} messages")
                
                # Stats
                sent = sum(1 for m in messages if m.direction.value == 'sent')
                received = count - sent
                
                summary.append({
                    'file': file.name,
                    'contact': contact,
                    'total': count,
                    'sent': sent,
                    'received': received
                })
                
                # Ajouter les messages pour export
                for msg in messages:
                    all_data.append({
                        'contact': contact,
                        'timestamp': msg.timestamp.isoformat() if msg.timestamp else '',
                        'direction': msg.direction.value,
                        'type': msg.media_type.value,
                        'content': msg.content[:100] + '...' if len(msg.content) > 100 else msg.content,
                        'file': file.name
                    })
    except Exception as e:
        print(f"  [ERROR] {e}")

# Résumé
print("\n" + "="*60)
print("RÉSUMÉ")
print("="*60)

total_messages = sum(s['total'] for s in summary)
print(f"Total contacts: {len(summary)}")
print(f"Total messages: {total_messages}")

print("\nTOP 5 CONTACTS:")
for s in sorted(summary, key=lambda x: x['total'], reverse=True)[:5]:
    print(f"  {s['contact']}: {s['total']} messages (Envoyes: {s['sent']}, Recus: {s['received']})")

# Export
if all_data:
    output_dir = Path("../10_contacts_results")
    output_dir.mkdir(exist_ok=True)
    
    csv_file = output_dir / "10_contacts.csv"
    csv_exp = CSVExporter()
    
    if csv_exp.export(all_data, csv_file):
        print(f"\n[EXPORT] CSV sauvegardé: {csv_file}")
        print(f"         Taille: {csv_file.stat().st_size:,} bytes")

print("\n[TERMINÉ]")