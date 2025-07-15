#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script correctif pour résoudre les problèmes d'export CSV
Ce script modifie l'exportateur PhoneNameCSVExporter pour qu'il fonctionne
même si les fichiers fusionnés sont vides ou manquants.
"""

import os
import sys
import re
import csv
import configparser
import logging
from collections import defaultdict
from typing import Dict, List, Optional

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("fix_export")

class ExportFixer:
    def __init__(self, output_dir=None):
        """Initialise le correcteur avec le répertoire de sortie"""
        config = configparser.ConfigParser()
        
        try:
            config.read('config.ini')
            self.output_dir = config.get('Paths', 'output_dir')
        except Exception:
            # Fallback
            self.output_dir = output_dir or os.path.join(os.path.expanduser('~'), 'Desktop', 'DataLeads')
        
        logger.info(f"Répertoire cible: {self.output_dir}")
    
    def fix_phone_name_csv_export(self):
        """Génère l'export CSV simplifié directement à partir des données brutes"""
        logger.info("Génération de l'export CSV simplifié (contacts_messages_simplifies.csv)")
        
        # 1. Collecter les données directement des fichiers de messages par contact
        conversations = self._collect_contact_messages()
        
        # 2. Collecter les transcriptions disponibles
        transcriptions = self._collect_transcriptions()
        
        # 3. Générer le CSV simplifié
        self._generate_simplified_csv(conversations, transcriptions)
        
    def _collect_contact_messages(self):
        """Collecte les messages de tous les contacts directement depuis les fichiers"""
        logger.info("Collecte des messages par contact...")
        conversations = defaultdict(list)
        
        # Parcourir tous les dossiers de contacts
        contact_dirs = [d for d in os.listdir(self.output_dir) 
                       if os.path.isdir(os.path.join(self.output_dir, d))
                       and not d.startswith('.')]
        
        logger.info(f"Nombre de contacts trouvés: {len(contact_dirs)}")
        
        for contact in contact_dirs:
            contact_path = os.path.join(self.output_dir, contact)
            
            # D'abord essayer le fichier avec transcriptions
            message_files = [
                os.path.join(contact_path, 'messages_recus_avec_transcriptions.txt'),
                os.path.join(contact_path, 'messages_recus.txt'),
                os.path.join(contact_path, 'all_messages.txt')
            ]
            
            for msg_file in message_files:
                if os.path.exists(msg_file) and os.path.getsize(msg_file) > 0:
                    messages = self._parse_message_file(msg_file, contact)
                    if messages:
                        conversations[contact].extend(messages)
                        logger.info(f"  - {contact}: {len(messages)} messages trouvés")
                    break
        
        return dict(conversations)
    
    def _parse_message_file(self, file_path, contact):
        """Parse un fichier de messages pour extraire les données"""
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Pattern pour les messages
            pattern = r'\[([\d/]+)\s+([\d:]+)\]\s+(.+?):\s+(.*?)(?=\n\[|\Z)'
            matches = re.findall(pattern, content, re.DOTALL)
            
            for match in matches:
                date, time, direction, text = match
                
                # Déterminer si c'est reçu ou envoyé
                is_received = not any(x in direction.lower() for x in ['vous', 'you', 'me', 'moi'])
                
                if is_received:  # On ne garde que les messages reçus
                    # Rechercher une transcription dans le texte
                    has_audio = '[AUDIO]' in text
                    transcription = None
                    
                    trans_match = re.search(r'\[TRANSCRIPTION:\s*(.*?)\s*\]', text)
                    if trans_match:
                        transcription = trans_match.group(1)
                        text = text.replace(f'[AUDIO] [TRANSCRIPTION: {transcription}]', transcription)
                    elif has_audio:
                        # Marquer pour récupération ultérieure
                        text = text.replace('[AUDIO]', '[Audio non transcrit]')
                    
                    message = {
                        'date': date,
                        'time': time,
                        'direction': 'received',
                        'content': text.strip(),
                        'contact': contact,
                        'type': 'audio' if has_audio else 'text',
                        'transcription': transcription
                    }
                    messages.append(message)
        
        except Exception as e:
            logger.error(f"Erreur parsing {file_path}: {str(e)}")
            
        return messages
    
    def _collect_transcriptions(self):
        """Collecte toutes les transcriptions disponibles du registre et des fichiers texte"""
        logger.info("Collecte des transcriptions disponibles...")
        transcriptions = {}
        
        # 1. Essayer de charger le registre unifié
        registry_file = os.path.join(self.output_dir, '.unified_registry.json')
        if os.path.exists(registry_file):
            try:
                import json
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                    
                for hash_key, trans_data in registry.get('transcriptions', {}).items():
                    audio_path = trans_data.get('audio_path', '')
                    text = trans_data.get('text', '')
                    
                    if audio_path and text:
                        audio_name = os.path.basename(audio_path)
                        transcriptions[audio_name] = text
                        
                logger.info(f"  - {len(transcriptions)} transcriptions trouvées dans le registre")
            except Exception as e:
                logger.error(f"Erreur chargement registre: {str(e)}")
        
        # 2. Chercher les fichiers texte de transcription
        for contact in os.listdir(self.output_dir):
            contact_path = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_path):
                continue
                
            trans_dir = os.path.join(contact_path, 'transcriptions')
            if not os.path.exists(trans_dir):
                continue
                
            for file_name in os.listdir(trans_dir):
                if file_name.endswith('.txt'):
                    try:
                        with open(os.path.join(trans_dir, file_name), 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extraire l'audio associé et la transcription
                        audio_line = None
                        for line in content.split('\n'):
                            if line.startswith('Audio:'):
                                audio_line = line.replace('Audio:', '').strip()
                                break
                        
                        if audio_line:
                            # Extraire la transcription (après la ligne 5)
                            lines = content.split('\n')
                            if len(lines) > 5:
                                trans_text = '\n'.join(lines[5:]).strip()
                                if trans_text:
                                    # Si on a un nom de fichier complet, on garde juste le basename
                                    if os.path.sep in audio_line:
                                        audio_line = os.path.basename(audio_line)
                                    transcriptions[audio_line] = trans_text
                    except Exception as e:
                        logger.error(f"Erreur lecture transcription {file_name}: {str(e)}")
        
        logger.info(f"  - Total: {len(transcriptions)} transcriptions trouvées")
        return transcriptions
    
    def _generate_simplified_csv(self, conversations, transcriptions):
        """Génère le CSV simplifié avec les colonnes numéro, prénom et messages"""
        logger.info("Génération du fichier CSV simplifié...")
        
        csv_file = os.path.join(self.output_dir, 'contacts_messages_simplifies.csv')
        rows = []
        
        # Garder TOUS les contacts, même ceux sans messages
        contacts_with_messages = conversations.copy()  # Inclure tous les contacts, même sans messages
        
        for contact, messages in contacts_with_messages.items():
            # Filtrer seulement les messages reçus (par sécurité)
            received_msgs = [m for m in messages if m.get('direction') == 'received']
            
            # Extraire prénom et numéro
            phone, name = self._extract_name_and_phone(contact)
            
            # Préparer tous les messages reçus
            all_messages = []
            
            # Si ce contact a des messages reçus
            if received_msgs:
                for msg in received_msgs:
                    date_time = f"{msg.get('date', 'XXXX-XX-XX')} {msg.get('time', 'XX:XX')}"
                    
                    if msg.get('type') == 'text':
                        all_messages.append(f"[{date_time}] {msg.get('content', '')}")
                    elif msg.get('type') == 'audio':
                        # Essayer de récupérer une transcription déjà intégrée
                        transcription = msg.get('transcription')
                        
                        # Si pas trouvée, chercher dans notre collection
                        if not transcription and msg.get('media_path'):
                            audio_name = os.path.basename(msg.get('media_path'))
                            audio_hash = msg.get('hash')
                            uuid = msg.get('uuid')
                            
                            if audio_hash and audio_hash in transcriptions:
                                transcription = transcriptions[audio_hash]
                            elif uuid and uuid in transcriptions:
                                transcription = transcriptions[uuid]
                            elif audio_name and audio_name in transcriptions:
                                transcription = transcriptions[audio_name]
                        
                        if transcription:
                            all_messages.append(f"[{date_time}] [AUDIO TRANSCRIT]: {transcription}")
                        else:
                            all_messages.append(f"[{date_time}] [Audio non transcrit]")
            else:
                # Pas de messages pour ce contact, mais on le garde quand même
                all_messages = []  # Liste vide
            
            # Joindre tous les messages avec un séparateur
            all_texts = " | ".join(all_messages)
            
            # Créer la ligne
            row = {
                'Numéro de téléphone': phone if phone else "Non identifié",
                'Prénom': name if name else contact,
                'Messages reçus': all_texts
            }
            
            rows.append(row)
        
        # Écrire le fichier CSV
        if rows:
            fieldnames = ['Numéro de téléphone', 'Prénom', 'Messages reçus']
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
            logger.info(f"CSV simplifié généré avec TOUS les {len(rows)} contacts: {csv_file}")
            if len(rows) < len(conversations):
                logger.warning(f"ATTENTION: Certains contacts n'ont pas été exportés ({len(conversations) - len(rows)} manquants)")
            logger.info(f"  - Dont {sum(1 for r in rows if r['Messages reçus'])} avec des messages reçus")
            
            # Créer version Excel si possible
            try:
                import pandas as pd
                excel_file = csv_file.replace('.csv', '.xlsx')
                df = pd.read_csv(csv_file, encoding='utf-8')
                df.to_excel(excel_file, index=False)
                logger.info(f"Version Excel générée: {excel_file}")
            except Exception as e:
                logger.debug(f"pandas non disponible, pas de version Excel: {str(e)}")
        else:
            logger.warning("Aucun message reçu trouvé pour générer le CSV")
    
    def _extract_name_and_phone(self, contact):
        """Extrait le numéro de téléphone et le prénom d'un nom de contact"""
        # Pattern pour numéros internationaux (commence par + suivi de chiffres)
        international_pattern = re.compile(r'(\+\d+(?:\s*\d+)*)')
        # Pattern pour numéros locaux (commence par 0 suivi de chiffres)
        local_pattern = re.compile(r'(0\d+(?:\s*\d+)*)')
        # Pattern pour groupes de chiffres (au moins 6 chiffres consécutifs)
        digits_pattern = re.compile(r'(\d{6,})')
        
        # 1. Essayer le pattern international
        match = international_pattern.search(contact)
        if match:
            phone = match.group(1).strip()
            # Le nom est tout ce qui reste après avoir enlevé le téléphone
            name = contact.replace(phone, '').strip()
            return phone, name if name else None
            
        # 2. Essayer le pattern local
        match = local_pattern.search(contact)
        if match:
            phone = match.group(1).strip()
            name = contact.replace(phone, '').strip()
            return phone, name if name else None
            
        # 3. Chercher des groupes de chiffres
        match = digits_pattern.search(contact)
        if match:
            phone = match.group(1).strip()
            name = contact.replace(phone, '').strip()
            return phone, name if name else None
            
        # 4. Vérifier si le contact sanitizé contient beaucoup de '_'
        # ce qui pourrait indiquer un numéro sanitizé
        if contact.count('_') > 5 and any(c.isdigit() for c in contact):
            # Probablement un numéro sanitizé (comme _33_6_...)
            return contact, None
            
        # Si aucun motif ne correspond, supposer que c'est un nom
        return None, contact


if __name__ == "__main__":
    logger.info("=== CORRECTION DE L'EXPORT CSV SIMPLIFIÉ ===")
    
    fixer = ExportFixer()
    fixer.fix_phone_name_csv_export()
    
    logger.info("=== TERMINÉ ===")
    logger.info("Lancez 'python diagnostic_export.py' pour vérifier que tout est maintenant correct.")
