"""
Module d'export CSV simplifié et robuste qui fonctionne indépendamment des fichiers fusionnés.
Il collecte directement les messages depuis les dossiers de contacts.
"""

import os
import csv
import re
import logging
import json
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class RobustPhoneNameCSVExporter:
    """
    Exportateur robuste qui génère un fichier CSV avec:
    - Numéro de téléphone
    - Prénom
    - Messages reçus (incluant les transcriptions)
    
    Ne dépend pas des fichiers fusionnés et prend en compte TOUS les contacts.
    """
    
    def __init__(self, config, registry, file_manager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        
        # Gérer le cas où output_directory n'est pas défini dans la config
        self.output_dir = config.get('output_directory', '') if config else ''
        
        # Si toujours pas de répertoire, utiliser le répertoire par défaut
        if not self.output_dir:
            self.output_dir = "C:\\Datalead3webidu13juillet"
            logger.info(f"Répertoire de sortie non défini, utilisation du répertoire par défaut: {self.output_dir}")
        
    def export_all_contacts_csv(self, conversations=None):
        """Génère le CSV simplifié avec TOUS les contacts"""
        logger.info("=== GÉNÉRATION DE L'EXPORT CSV SIMPLIFIÉ ROBUSTE ===")
        
        # Collecter les messages par contact
        contact_messages = self._collect_all_contact_messages()
        total_contacts = len(contact_messages)
        logger.info(f"Nombre total de contacts trouvés: {total_contacts}")
        
        # Collecter les transcriptions disponibles
        transcriptions = self._collect_all_transcriptions()
        
        # Générer le CSV
        self._generate_simplified_csv(contact_messages, transcriptions)
        
        # Optionnellement générer version Excel
        self._generate_excel_version()
        
        return True
    
    def _collect_all_contact_messages(self) -> Dict[str, List[Dict]]:
        """Collecte tous les messages reçus pour chaque contact"""
        contacts_dir = self.output_dir
        contact_messages = {}
        
        # Lister tous les sous-dossiers (contacts)
        try:
            all_items = os.listdir(contacts_dir)
            contacts = [item for item in all_items if os.path.isdir(os.path.join(contacts_dir, item)) 
                        and not item.startswith('.')]
            
            logger.info(f"Nombre de contacts trouvés: {len(contacts)}")
            
            for contact in contacts:
                contact_dir = os.path.join(contacts_dir, contact)
                messages = []
                
                # Chercher les fichiers de messages par ordre de priorité
                message_files = [
                    os.path.join(contact_dir, 'messages_recus_avec_transcriptions.txt'),
                    os.path.join(contact_dir, 'messages_recus.txt'),
                    os.path.join(contact_dir, 'all_messages.txt')
                ]
                
                for message_file in message_files:
                    if os.path.exists(message_file) and os.path.getsize(message_file) > 100:
                        messages = self._parse_messages_file(message_file)
                        if messages:
                            num_messages = len([m for m in messages if m.get('direction') == 'received'])
                            if num_messages > 0:
                                logger.info(f"  - {contact}: {num_messages} messages trouvés")
                            break
                
                # Ajouter ce contact même s'il n'a pas de messages
                contact_messages[contact] = messages
        
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des messages: {str(e)}")
            
        return contact_messages
    
    def _parse_messages_file(self, file_path) -> List[Dict]:
        """Parse un fichier de messages pour extraire les messages reçus avec leurs métadonnées"""
        messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Expressions régulières pour détecter les messages
                message_pattern = r'\[(\d{4}/\d{2}/\d{2}) (\d{2}:\d{2})\] (.+?): (.+?)(?=\[\d{4}/\d{2}/\d{2} \d{2}:\d{2}\]|$)'
                
                # Trouver tous les messages
                matches = re.findall(message_pattern, content, re.DOTALL)
                
                for match in matches:
                    date, time, sender, content = match
                    
                    # Déterminer si c'est un message reçu ou envoyé
                    direction = 'received' if sender != "Vous" else 'sent'
                    
                    # Détecter s'il s'agit d'un audio
                    is_audio = False
                    transcription = None
                    media_path = None
                    
                    if '[AUDIO]' in content:
                        is_audio = True
                        content_parts = content.split('[AUDIO]')
                        content = content_parts[0].strip()
                        
                        # Vérifier si une transcription est déjà présente
                        if len(content_parts) > 1 and content_parts[1]:
                            transcription_match = re.search(r'\[(.*?)\]', content_parts[1])
                            if transcription_match:
                                transcription = transcription_match.group(1)
                    
                    message = {
                        'date': date,
                        'time': time,
                        'sender': sender,
                        'content': content,
                        'direction': direction,
                        'type': 'audio' if is_audio else 'text',
                        'transcription': transcription,
                        'media_path': media_path
                    }
                    
                    messages.append(message)
                
        except Exception as e:
            logger.error(f"Erreur lors du parsing du fichier {file_path}: {str(e)}")
            
        return messages
    
    def _collect_all_transcriptions(self) -> Dict[str, str]:
        """Collecte toutes les transcriptions disponibles"""
        transcriptions = {}
        
        # 1. Traiter les fichiers de mapping JSON (source principale)
        try:
            mappings_dir = os.path.join(self.output_dir, '.transcription_mappings')
            if os.path.exists(mappings_dir) and os.path.isdir(mappings_dir):
                json_files = [f for f in os.listdir(mappings_dir) if f.endswith('_mappings.json')]
                for json_file in json_files:
                    file_path = os.path.join(mappings_dir, json_file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            mapping_data = json.load(f)
                            # Structure: {"audio_file.mp3": {"hash": "...", "transcription": "..."}}
                            for audio_file, data in mapping_data.items():
                                if isinstance(data, dict) and 'transcription' in data:
                                    # Stocker avec plusieurs clés pour faciliter la recherche
                                    transcriptions[audio_file] = data['transcription']
                                    if 'hash' in data:
                                        transcriptions[data['hash']] = data['transcription']
                    except Exception as e:
                        logger.debug(f"Erreur lors du traitement de {json_file}: {str(e)}")
                
                logger.info(f"  - {len(transcriptions)} transcriptions trouvées dans les fichiers de mapping")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des mappings de transcription: {str(e)}")
        
        # 2. Tenter de lire le registre unifié comme objet (version actuelle)
        if hasattr(self.registry, 'get_all_entries'):
            try:
                registry_data = self.registry.get_all_entries()
                if isinstance(registry_data, list):
                    for entry in registry_data:
                        if isinstance(entry, dict) and 'transcription' in entry:
                            # Ajouter avec plusieurs clés
                            file_path = entry.get('file_path', '')
                            if file_path:
                                audio_name = os.path.basename(file_path)
                                transcriptions[audio_name] = entry['transcription']
                            if entry.get('hash'):
                                transcriptions[entry['hash']] = entry['transcription']
                            if entry.get('uuid'):
                                transcriptions[entry['uuid']] = entry['transcription']
                
                logger.info(f"  - {len(transcriptions)} transcriptions après ajout du registre (objet)")
            except Exception as e:
                logger.debug(f"Registre objet non exploitable: {str(e)}")
        
        # 3. Tenter de lire le registre unifié comme fichier JSON (structure différente)
        try:
            registry_file = os.path.join(self.output_dir, '.unified_registry.json')
            if os.path.exists(registry_file):
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry_data = json.load(f)
                    
                    # Structure potentielle: {"version": "...", "contacts": {"contact1": {"files": [...], "stats": {...}}}}
                    if isinstance(registry_data, dict) and 'contacts' in registry_data:
                        contacts_data = registry_data['contacts']
                        for contact, data in contacts_data.items():
                            # Vérifier s'il y a des transcriptions dans les données de contact
                            if 'files' in data:
                                for file_hash in data['files']:
                                    # Chercher dans le registre si ce fichier a une transcription
                                    if file_hash in transcriptions:
                                        logger.debug(f"Transcription trouvée pour le hash {file_hash[:10]}...")
                    
                    logger.info(f"  - {len(transcriptions)} transcriptions après analyse du fichier registre")
        except Exception as e:
            logger.debug(f"Erreur lors de l'analyse du fichier registre: {str(e)}")
        
        # 4. Chercher également dans les fichiers .txt (pour compatibilité)
        try:
            txt_files = [f for f in os.listdir(mappings_dir) if f.endswith('.txt')]
            for txt_file in txt_files:
                file_path = os.path.join(mappings_dir, txt_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            audio_id = txt_file.replace('.txt', '')
                            transcriptions[audio_id] = content
                except Exception:
                    pass
        except Exception:
            pass
        
        logger.info(f"  - Total final: {len(transcriptions)} transcriptions disponibles")
        return transcriptions
    
    def _extract_name_and_phone(self, contact: str) -> Tuple[str, str]:
        """Extrait le numéro de téléphone et le prénom à partir du nom du dossier contact"""
        # Format international ex: _33_6_12_34_56_78
        intl_match = re.match(r'^_(\d+)_(\d+)_(\d+)(?:_(\d+))?(?:_(\d+))?(?:_(\d+))?(?:_(\d+))?(?:_(\d+))?', contact)
        if intl_match:
            groups = [g for g in intl_match.groups() if g]
            if len(groups) >= 2:
                phone = '+' + ''.join(groups)
                # Si le format est déjà avec underscore, le garder tel quel
                return phone, contact
        
        # Format local simple ex: 0612345678_John
        local_match = re.match(r'^(\d+)(?:_(.+))?$', contact)
        if local_match and local_match.group(1):
            phone = local_match.group(1)
            name = local_match.group(2) or contact
            return phone, name
        
        # Format avec préfixe webi ex: John_webi123
        webi_match = re.match(r'^(.+?)_webi\d+$', contact)
        if webi_match:
            name = webi_match.group(1)
            return "Non identifié", name
            
        # Cas par défaut : tout le nom est le prénom, pas de numéro identifié
        return "Non identifié", contact
    
    def _generate_simplified_csv(self, conversations, transcriptions):
        """Génère le CSV simplifié avec uniquement deux colonnes"""
        logger.info("Génération du fichier CSV simplifié à deux colonnes...")
        
        csv_file = os.path.join(self.output_dir, 'contacts_messages_simplifies.csv')
        rows = []
        
        # Inclure TOUS les contacts
        for contact, messages in conversations.items():
            # Filtrer seulement les messages reçus
            received_msgs = [m for m in messages if m.get('direction') == 'received']
            
            # Extraire prénom et numéro
            phone, name = self._extract_name_and_phone(contact)
            
            # Déterminer quelle valeur utiliser pour la colonne A
            # Si le prénom existe, l'utiliser, sinon utiliser le numéro
            contact_identifier = name if name and name != contact else phone
            
            # Préparer tous les messages reçus
            all_messages = []
            
            # Si ce contact a des messages reçus
            if received_msgs:
                for msg in received_msgs:
                    date_time = f"{msg.get('date', 'XXXX-XX-XX')} {msg.get('time', 'XX:XX')}"
                    
                    if msg.get('type') == 'text':
                        all_messages.append(f"[{date_time}] {msg.get('content', '')}")
                    elif msg.get('type') == 'audio':
                        # Essayer de récupérer une transcription
                        transcription = None
                        
                        # 1. Vérifier si déjà intégrée
                        if msg.get('transcription'):
                            transcription = msg.get('transcription')
                        
                        # 2. Sinon chercher par différentes clés
                        else:
                            # Récupérer toutes les clés possibles
                            audio_name = os.path.basename(msg.get('media_path', '')) 
                            audio_hash = msg.get('hash')
                            uuid = msg.get('uuid')
                            
                            # Essayer de trouver par nom de fichier
                            if audio_name and audio_name in transcriptions:
                                transcription = transcriptions[audio_name]
                            # Essayer par hash
                            elif audio_hash and audio_hash in transcriptions:
                                transcription = transcriptions[audio_hash]
                            # Essayer par UUID
                            elif uuid and uuid in transcriptions:
                                transcription = transcriptions[uuid]
                        
                        if transcription:
                            all_messages.append(f"[{date_time}] [AUDIO TRANSCRIT]: {transcription}")
                        else:
                            all_messages.append(f"[{date_time}] [Audio non transcrit]")
            
            # Joindre tous les messages avec un séparateur
            all_texts = " | ".join(all_messages)
            
            row = {
                'Contact': contact_identifier,
                'Messages reçus': all_texts
            }
            
            rows.append(row)
        
        # Écrire le fichier CSV
        if rows:
            fieldnames = ['Contact', 'Messages reçus']
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
                
            logger.info(f"CSV simplifié généré avec {len(rows)} contacts: {csv_file}")
            with_msgs = sum(1 for r in rows if r['Messages reçus'])
            logger.info(f"  - Dont {with_msgs} avec des messages reçus")
            with_audio = sum(1 for r in rows if '[AUDIO TRANSCRIT]' in r['Messages reçus'])
            logger.info(f"  - Dont {with_audio} avec des transcriptions audio")
        else:
            logger.warning("Aucun contact trouvé pour générer le CSV")
            
    def _generate_excel_version(self):
        """Génère une version Excel du fichier CSV si pandas est disponible"""
        csv_file = os.path.join(self.output_dir, 'contacts_messages_simplifies.csv')
        
        if os.path.exists(csv_file):
            try:
                import pandas as pd
                excel_file = csv_file.replace('.csv', '.xlsx')
                df = pd.read_csv(csv_file, encoding='utf-8')
                df.to_excel(excel_file, index=False)
                logger.info(f"Version Excel générée: {excel_file}")
            except Exception as e:
                logger.debug(f"pandas non disponible, pas de version Excel: {str(e)}")
