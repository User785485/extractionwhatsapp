import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Modifier temporairement la limite dans le parseur
from processors.html_parser import HTMLParser
original_parse_all = HTMLParser.parse_all_conversations

def limited_parse_all(self, incremental=True):
    """Version limitée qui traite seulement 30 messages/contacts"""
    conversations = {}
    html_files = self._get_html_files()
    
    if not html_files:
        return conversations
    
    # LIMITE À 30 FICHIERS MAXIMUM
    html_files = html_files[:30]
    print(f"MODE TEST: Traitement limité à {len(html_files)} fichiers HTML")
    
    for i, html_file in enumerate(html_files):
        print(f"Traitement [{i+1}/{len(html_files)}]: {os.path.basename(html_file)}")
        contact, messages = self.parse_html_file(html_file)
        
        if contact and messages:
            # LIMITE À 30 MESSAGES PAR CONTACT
            messages = messages[:30]
            conversations[contact] = messages
            print(f"  → {contact}: {len(messages)} messages (limités)")
    
    self.registry.save()
    return conversations

# Remplacer la méthode
HTMLParser.parse_all_conversations = limited_parse_all

# Lancer le main normal
print("\n" + "="*60)
print("DÉMARRAGE EN MODE TEST (30 premiers)")
print("="*60 + "\n")

from main import main
sys.exit(main())
