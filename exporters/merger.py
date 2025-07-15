import os
import re
import json
import logging
from typing import Dict, List, Optional

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class TranscriptionMerger:
    """
    MERGER CORRIGE - Fusionne les transcriptions avec correspondance exacte
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        self.output_dir = config.get('Paths', 'output_dir')
        
        # Charger les correspondances creees par le transcripteur
        self.transcription_mappings = self._load_all_mappings()
        
        # Creer un mapping inverse OPUS -> MP3
        self.opus_to_mp3_mapping = self._build_opus_to_mp3_mapping()
        
        # Creer un mapping UUID -> transcription
        self.uuid_to_transcription = self._build_uuid_mapping()
        
        # Charger les fichiers texte de transcription
        self.text_file_mapping = self._load_transcription_text_files()
    
    def _load_all_mappings(self) -> Dict[str, Dict]:
        """Charge toutes les correspondances fichier -> transcription"""
        mappings = {}
        mapping_dir = os.path.join(self.output_dir, '.transcription_mappings')
        
        if not os.path.exists(mapping_dir):
            logger.warning("Repertoire de correspondances non trouve")
            return mappings
        
        # Charger tous les fichiers de correspondance
        for file in os.listdir(mapping_dir):
            if file.endswith('_mappings.json'):
                contact = file.replace('_mappings.json', '')
                mapping_file = os.path.join(mapping_dir, file)
                
                try:
                    with open(mapping_file, 'r', encoding='utf-8') as f:
                        contact_mappings = json.load(f)
                        mappings[contact] = contact_mappings
                        logger.info(f"Correspondances chargees pour {contact}: {len(contact_mappings)} fichiers")
                except Exception as e:
                    logger.error(f"Erreur chargement correspondances {contact}: {str(e)}")
        
        total_mappings = sum(len(cm) for cm in mappings.values())
        logger.info(f"Total correspondances chargees: {total_mappings}")
        return mappings
    
    def _build_opus_to_mp3_mapping(self) -> Dict[str, str]:
        """Construit un mapping OPUS -> MP3 base sur les conversions"""
        mapping = {}
        
        # Parcourir le registre pour trouver les conversions
        for file_hash, file_info in self.registry.data.get('files', {}).items():
            if file_info.get('type') == 'audio':
                original_path = file_info.get('path', '')
                converted_path = file_info.get('converted_path', '')
                
                if original_path and converted_path:
                    opus_name = os.path.basename(original_path)
                    mp3_name = os.path.basename(converted_path)
                    mapping[opus_name] = mp3_name
                    # Remplacer logger.debug par info pour éviter les erreurs
                    logger.info(f"Mapping OPUS->MP3: {opus_name[:20]}... -> {mp3_name[:20]}...")
        
        logger.info(f"Mapping OPUS->MP3 construit: {len(mapping)} correspondances")
        return mapping
    
    def _build_uuid_mapping(self) -> Dict[str, str]:
        """Construit un mapping UUID -> transcription"""
        uuid_mapping = {}
        
        # Extraire les UUID des fichiers MP3 et chercher leurs transcriptions
        for contact, mappings in self.transcription_mappings.items():
            for mp3_name, data in mappings.items():
                # Extraire l'UUID du nom MP3
                uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', mp3_name)
                if uuid_match:
                    uuid = uuid_match.group(1)
                    transcription = data.get('transcription', '')
                    if transcription:
                        uuid_mapping[uuid] = transcription
                        logger.info(f"UUID mapping ajouté: {uuid[:8]}... -> {len(transcription)} chars")
        
        logger.info(f"Mapping UUID->Transcription construit: {len(uuid_mapping)} correspondances")
        return uuid_mapping
    
    def _load_transcription_text_files(self):
        """Charge les fichiers texte de transcription"""
        text_file_mapping = {}
        
        # Parcourir tous les dossiers de contact
        for contact in os.listdir(self.output_dir):
            contact_dir = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_dir):
                continue
            
            trans_dir = os.path.join(contact_dir, 'transcriptions')
            if not os.path.exists(trans_dir):
                continue
            
            # Charger tous les fichiers de transcription
            for file in os.listdir(trans_dir):
                if file.endswith('.txt'):
                    full_path = os.path.join(trans_dir, file)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Extraire le nom du fichier audio et la transcription
                        file_match = re.search(r'Transcription du fichier: (.*?)\n', content)
                        if file_match:
                            audio_file = file_match.group(1)
                            # Extraire la transcription (apres les 5 premieres lignes)
                            lines = content.split('\n')
                            if len(lines) > 5:
                                transcription = '\n'.join(lines[5:]).strip()
                                
                                # Creer une cle par contact et par fichier
                                if contact not in text_file_mapping:
                                    text_file_mapping[contact] = {}
                                
                                # Stocker la transcription
                                text_file_mapping[contact][audio_file] = transcription
                                
                                # Stocker aussi avec l'extension originale
                                if audio_file.endswith('.mp3'):
                                    opus_name = audio_file.replace('.mp3', '.opus')
                                    text_file_mapping[contact][opus_name] = transcription
                                
                                # Extraire l'UUID pour une association directe
                                uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_file)
                                if uuid_match:
                                    uuid = uuid_match.group(1)
                                    # Stocker avec juste l'UUID pour correspondre aux references dans les conversations
                                    text_file_mapping[contact][uuid + '.opus'] = transcription
                    
                    except Exception as e:
                        logger.error(f"Erreur lecture transcription {file}: {str(e)}")
        
        logger.info(f"Transcriptions chargees depuis fichiers texte: {sum(len(files) for files in text_file_mapping.values())} fichiers")
        return text_file_mapping

    def merge_all_transcriptions(self, minimal_export: bool = False):
        """Fusionne les transcriptions avec correspondance parfaite
        
        Args:
            minimal_export: Si True, fusionne uniquement les fichiers de messages reçus
        """
        logger.info("=== FUSION TRANSCRIPTIONS AVEC CORRESPONDANCE EXACTE ===")
        
        if minimal_export:
            logger.info("Mode export minimal activé - uniquement fusion des messages reçus")
            # Uniquement les fichiers de messages reçus
            self._merge_received_files()
        else:
            # 1. Fichier global
            self._merge_global_file()
            
            # 2. Fichiers par contact
            self._merge_contact_files()
            
            # 3. Fichiers messages recus
            self._merge_received_files()
        
        logger.info("Fusion terminée avec correspondances exactes")
    
    def _merge_global_file(self):
        """Met a jour le fichier global avec les transcriptions"""
        # Essayer plusieurs noms possibles pour le fichier source
        possible_sources = [
            'toutes_conversations.txt',
            'all_conversations.txt'
        ]
        
        source = None
        for filename in possible_sources:
            test_path = os.path.join(self.output_dir, filename)
            if os.path.exists(test_path) and os.path.getsize(test_path) > 100:
                source = test_path
                logger.info(f"Fichier source trouve: {filename}")
                break
        
        if not source:
            logger.error("Aucun fichier source valide trouve pour le merge global!")
            logger.error(f"Fichiers recherches dans {self.output_dir}: {possible_sources}")
            # Creer un fichier vide pour eviter les erreurs
            target = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')
            with open(target, 'w', encoding='utf-8') as f:
                f.write("AUCUNE CONVERSATION TROUVEE\n")
            return
        
        target = os.path.join(self.output_dir, 'toutes_conversations_avec_transcriptions.txt')
        
        try:
            with open(source, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remplacer avec la nouvelle methode
            updated_content = self._replace_audio_references_exact(content)
            
            with open(target, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"Fichier global avec transcriptions cree: {target}")
            
        except Exception as e:
            logger.error(f"Erreur fusion fichier global: {str(e)}")
    def _merge_contact_files(self):
        """Met a jour les fichiers de chaque contact"""
        merged_count = 0
        
        for contact in os.listdir(self.output_dir):
            contact_path = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_path) or contact.startswith('.'):
                continue
            
            # Fichier tous messages
            source = os.path.join(contact_path, 'tous_messages.txt')
            if os.path.exists(source):
                target = os.path.join(contact_path, 'tous_messages_avec_transcriptions.txt')
                
                try:
                    with open(source, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    updated_content = self._replace_audio_references_exact(content, contact)
                    
                    with open(target, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    merged_count += 1
                    
                except Exception as e:
                    logger.error(f"Erreur fusion pour {contact}: {str(e)}")
        
        logger.info(f"Fichiers fusionnes pour {merged_count} contacts")
    
    def _merge_received_files(self):
        """Met a jour les fichiers de messages recus"""
        # Fichier global
        source = os.path.join(self.output_dir, 'messages_recus.txt')
        if os.path.exists(source):
            target = os.path.join(self.output_dir, 'messages_recus_avec_transcriptions.txt')
            
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                updated_content = self._replace_audio_references_exact(content)
                
                with open(target, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                    
            except Exception as e:
                logger.error(f"Erreur fusion messages recus global: {str(e)}")
        
        # Fichiers par contact
        for contact in os.listdir(self.output_dir):
            contact_path = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_path):
                continue
            
            source = os.path.join(contact_path, 'messages_recus.txt')
            if os.path.exists(source):
                target = os.path.join(contact_path, 'messages_recus_avec_transcriptions.txt')
                
                try:
                    with open(source, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    updated_content = self._replace_audio_references_exact(content, contact)
                    
                    with open(target, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                
                except Exception as e:
                    logger.error(f"Erreur fusion messages recus {contact}: {str(e)}")
    
    def _replace_audio_references_exact(self, content: str, specific_contact: str = None) -> str:
        """
        METHODE CORRIGEE: Remplace les references [AUDIO] par les vraies transcriptions
        """
        # Pattern amélioré pour capturer [AUDIO] avec ou sans nom de fichier
        # Capture optionnelle du nom de fichier après [AUDIO]
        pattern = r'\[AUDIO\](?:\s+([^\n\[\]]+))?'
        replacements_made = 0
        
        def replace_func(match):
            nonlocal replacements_made
            
            # Group(1) peut être None si pas de nom de fichier après [AUDIO]
            audio_file = match.group(1) if match.group(1) else None
            
            if not audio_file:
                # Pas de nom de fichier, on ne peut rien faire
                return '[AUDIO]'
            
            audio_file = audio_file.strip()
            
            # Si c'est "unknown" ou vide, on abandonne
            if not audio_file or audio_file.lower() == 'unknown':
                return '[AUDIO]'
            
            # Traiter le cas des fichiers sans extension
            if not audio_file.endswith('.opus') and not audio_file.endswith('.mp3'):
                # Si c'est juste un UUID, lui ajouter l'extension .opus
                uuid_match = re.search(r'^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$', audio_file)
                if uuid_match:
                    audio_file = f"{audio_file}.opus"
                    logger.info(f"Extension ajoutee: {audio_file}")
            
            # Essayer de trouver la transcription avec correspondance exacte
            transcription = self._find_transcription_exact(audio_file, specific_contact)
            
            if transcription and len(transcription.strip()) > 10:
                replacements_made += 1
                logger.info(f"[OK] Transcription trouvee pour {audio_file[:30]}...")
                return f'[AUDIO TRANSCRIT] "{transcription}"'
            else:
                logger.warning(f"[X] Pas de transcription pour {audio_file[:30]}...")
                return f'[AUDIO] {audio_file}'
        
        result = re.sub(pattern, replace_func, content)
        
        if specific_contact:
            logger.info(f"Contact {specific_contact}: {replacements_made} transcriptions ajoutees")
        else:
            logger.info(f"Global: {replacements_made} transcriptions ajoutees")
        
        return result
    
    def _find_transcription_exact(self, audio_reference: str, contact: str = None) -> Optional[str]:
        """
        METHODE AMELIOREE: Trouve la transcription avec plusieurs strategies
        """
        audio_name = audio_reference.strip()
        
        # Log simplifié pour éviter les erreurs
        logger.info(f"Recherche transcription pour: {audio_name[:30]}...")
        
        # STRATEGIE 1: Extraire l'UUID du fichier OPUS
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', audio_name)
        if uuid_match:
            uuid = uuid_match.group(1)
            logger.info(f"UUID extrait: {uuid[:8]}...")
            
            # Chercher directement dans le mapping UUID
            if uuid in self.uuid_to_transcription:
                transcription = self.uuid_to_transcription[uuid]
                logger.info(f"Transcription trouvee par UUID: {uuid[:8]}...")
                return transcription
        
        # STRATEGIE 2: Si c'est un OPUS, trouver le MP3 correspondant
        if audio_name.endswith('.opus'):
            mp3_name = self.opus_to_mp3_mapping.get(audio_name)
            if mp3_name:
                logger.info(f"OPUS->MP3: {audio_name[:20]}... -> {mp3_name[:20]}...")
                
                # Chercher dans les mappings avec le nom MP3
                if contact and contact in self.transcription_mappings:
                    contact_mappings = self.transcription_mappings[contact]
                    if mp3_name in contact_mappings:
                        transcription = contact_mappings[mp3_name].get('transcription', '')
                        if transcription:
                            logger.info(f"Transcription trouvee via mapping MP3: {mp3_name[:20]}...")
                            return transcription
        
        # STRATEGIE 3: Correspondance directe via les mappings
        if contact and contact in self.transcription_mappings:
            contact_mappings = self.transcription_mappings[contact]
            
            # Correspondance exacte du nom
            if audio_name in contact_mappings:
                transcription = contact_mappings[audio_name].get('transcription', '')
                if transcription:
                    logger.info(f"Correspondance exacte trouvee: {audio_name[:20]}...")
                    return transcription
        
        # STRATEGIE 3.5: Correspondance par UUID pur
        if uuid_match:
            uuid = uuid_match.group(1)
            logger.info(f"Recherche par UUID pur: {uuid[:8]}...")
            
            # Parcourir tous les contacts et leurs mappings
            for contact_name, contact_maps in self.transcription_mappings.items():
                for mp3_name, data in contact_maps.items():
                    if uuid in mp3_name:
                        transcription = data.get('transcription', '')
                        if transcription and len(transcription) > 10:
                            logger.info(f"Correspondance par UUID pur trouvée: {uuid[:8]}... dans {mp3_name[:20]}...")
                            return transcription
        
        # STRATEGIE 3.7: Recherche dans les fichiers texte de transcription
        if contact and contact in self.text_file_mapping:
            contact_texts = self.text_file_mapping[contact]
            
            # Recherche exacte par nom de fichier
            if audio_name in contact_texts:
                transcription = contact_texts[audio_name]
                logger.info(f"Transcription trouvee dans fichier texte (nom exact): {audio_name[:20]}...")
                return transcription
            
            # Recherche par UUID seul
            if uuid_match:
                uuid = uuid_match.group(1)
                # Chercher tous les fichiers avec cet UUID
                for file_name, trans in contact_texts.items():
                    if uuid in file_name:
                        logger.info(f"Transcription trouvee dans fichier texte (UUID): {uuid[:8]}...")
                        return trans
        
        # RECHERCHE GLOBALE: Chercher dans TOUS les contacts
        if uuid_match:
            uuid = uuid_match.group(1)
            for other_contact, contact_texts in self.text_file_mapping.items():
                for file_name, trans in contact_texts.items():
                    if uuid in file_name:
                        logger.info(f"Transcription trouvee dans fichier texte (autre contact): {other_contact}")
                        return trans

        # STRATEGIE 4: Recherche par hash dans le registre
        # Chercher tous les fichiers audio du contact
        for file_hash, file_info in self.registry.data.get('files', {}).items():
            if file_info.get('type') == 'audio' and file_info.get('contact') == contact:
                file_path = file_info.get('path', '')
                if audio_name in file_path:
                    # Verifier si ce hash a une transcription
                    trans_data = self.registry.data.get('transcriptions', {}).get(file_hash)
                    if trans_data:
                        transcription = trans_data.get('text', '')
                        if transcription and len(transcription) > 10:
                            logger.info(f"Transcription trouvee par hash fichier OPUS")
                            return transcription
                    
                    # Verifier aussi le hash du MP3 converti
                    converted_path = file_info.get('converted_path', '')
                    if converted_path:
                        mp3_hash = self.registry.get_file_hash(converted_path)
                        if mp3_hash:
                            trans_data = self.registry.data.get('transcriptions', {}).get(mp3_hash)
                            if trans_data:
                                transcription = trans_data.get('text', '')
                                if transcription and len(transcription) > 10:
                                    logger.info(f"Transcription trouvee par hash MP3")
                                    return transcription
        
        # STRATEGIE 5: Recherche dans toutes les transcriptions du contact
        if contact and contact in self.transcription_mappings:
            # Si on n'a pas trouve par nom exact, chercher par pattern
            for mp3_name, data in self.transcription_mappings[contact].items():
                transcription = data.get('transcription', '')
                if transcription and len(transcription) > 10:
                    # Verifier si les fichiers pourraient correspondre
                    if self._files_might_match(audio_name, mp3_name):
                        logger.info(f"Correspondance probable: {audio_name[:20]}... -> {mp3_name[:20]}...")
                        return transcription
        
        return None
    
    def _files_might_match(self, opus_name: str, mp3_name: str) -> bool:
        """Verifie si deux fichiers pourraient correspondre"""
        # Extraire la direction
        opus_direction = 'sent' if 'sent' in opus_name else 'received'
        mp3_direction = 'sent' if 'sent' in mp3_name else 'received'
        
        # Meme direction = potentiellement le meme fichier
        if opus_direction != mp3_direction:
            return False
            
        # Extraire les UUID des deux fichiers
        opus_uuid = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', opus_name)
        mp3_uuid = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', mp3_name)
        
        if opus_uuid and mp3_uuid:
            return opus_uuid.group(1) == mp3_uuid.group(1)
            
        return False