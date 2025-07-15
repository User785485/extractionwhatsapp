import os
import time
import logging
import openai
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
import json

from core import UnifiedRegistry, FileManager

logger = logging.getLogger('whatsapp_extractor')

class Transcriber:
    """
    Transcripteur OPTIMISÉ - Ne traite QUE les fichiers nécessaires
    """
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        
        # Configuration API
        self.api_key = config.get('API', 'openai_key', fallback=None)
        if not self.api_key:
            logger.error("[ERREUR] PAS DE CLÉ API OPENAI - TRANSCRIPTION IMPOSSIBLE")
            self.client = None
            return
        
        # Initialiser le client OpenAI
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            logger.info("[OK] Client OpenAI initialisé avec succès")
        except Exception as e:
            logger.error(f"[ERREUR] Erreur initialisation OpenAI: {str(e)}")
            self.client = None
        
        # Paramètres
        self.max_retries = config.getint('API', 'max_retries', fallback=5)
        self.retry_delay = config.getint('API', 'retry_delay', fallback=10)
        self.file_size_limit = 25 * 1024 * 1024  # 25 MB limite OpenAI
        
        # Mode force désactivé par défaut
        self.force_mode = False
        
        # Configuration de transcription
        self.transcribe_received = config.getboolean('Processing', 'transcribe_received', fallback=True)
        self.transcribe_sent = config.getboolean('Processing', 'transcribe_sent', fallback=False)
        
        logger.info(f"[CONFIG] Transcription - Reçus: {self.transcribe_received}, Envoyés: {self.transcribe_sent}")
        
        # Stats détaillées
        self.debug_stats = {
            'mp3_found': 0,
            'mp3_filtered': 0,
            'already_transcribed': 0,
            'transcribed_now': 0,
            'errors': 0,
            'api_calls': 0
        }
        
        # Log de debug
        self.debug_log = []
    
    def _log_debug(self, message: str):
        """Log de debug ultra-détaillé"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        self.debug_log.append(log_entry)
        logger.debug(f"[TRANSCRIBER_DEBUG] {message}")
    
    def _should_process_file(self, filename: str) -> bool:
        """
        OPTIMISATION : Détermine si un fichier doit être traité
        """
        filename_lower = filename.lower()
        
        # Déterminer la direction depuis le nom
        if filename_lower.startswith('received_') or 'received' in filename_lower:
            return self.transcribe_received
        elif filename_lower.startswith('sent_') or 'sent' in filename_lower:
            return self.transcribe_sent
        
        # Par défaut, ne pas traiter
        return False
    
    def transcribe_all_super_files(self) -> Dict[str, int]:
        """
        MÉTHODE OPTIMISÉE : Ne scanne et transcrit QUE les fichiers nécessaires
        """
        if not self.client:
            logger.error("[ERREUR] Client OpenAI non disponible")
            return {}
        
        self._log_debug("=== DÉBUT TRANSCRIPTION OPTIMISÉE ===")
        logger.info("=== DÉBUT TRANSCRIPTION OPTIMISÉE ===")
        
        logger.info(f"[CONFIG] Mode de transcription:")
        logger.info(f"  - Transcrire les audios REÇUS: {self.transcribe_received}")
        logger.info(f"  - Transcrire les audios ENVOYÉS: {self.transcribe_sent}")
        
        stats = {}
        mp3_files_to_process = []
        
        # ÉTAPE 1: Scanner avec FILTRAGE IMMÉDIAT
        logger.info("Scan optimisé des fichiers MP3...")
        
        for item in os.listdir(self.file_manager.output_dir):
            item_path = os.path.join(self.file_manager.output_dir, item)
            
            if not os.path.isdir(item_path) or item.startswith('.'):
                continue
            
            contact = item
            mp3_dir = os.path.join(item_path, 'audio_mp3')
            
            if os.path.exists(mp3_dir):
                for mp3_file in os.listdir(mp3_dir):
                    if not mp3_file.endswith('.mp3'):
                        continue
                    
                    self.debug_stats['mp3_found'] += 1
                    
                    # OPTIMISATION : Filtrer IMMÉDIATEMENT
                    if not self._should_process_file(mp3_file):
                        self._log_debug(f"Filtré: {mp3_file} (config)")
                        self.debug_stats['mp3_filtered'] += 1
                        continue
                    
                    # Ce fichier doit être traité
                    mp3_path = os.path.join(mp3_dir, mp3_file)
                    mp3_files_to_process.append({
                        'path': mp3_path,
                        'contact': contact,
                        'filename': mp3_file,
                        'direction': self._get_direction_from_filename(mp3_file)
                    })
        
        # Stats après filtrage
        logger.info(f"[OPTIMISATION] Résultats du scan:")
        logger.info(f"  - MP3 trouvés: {self.debug_stats['mp3_found']}")
        logger.info(f"  - MP3 filtrés (config): {self.debug_stats['mp3_filtered']}")
        logger.info(f"  - MP3 à traiter: {len(mp3_files_to_process)}")
        
        if self.debug_stats['mp3_filtered'] > 0:
            time_saved = self.debug_stats['mp3_filtered'] * 0.5  # ~0.5s par vérification
            logger.info(f"  - Temps économisé: ~{time_saved:.1f} secondes")
        
        # Afficher la liste des fichiers à traiter
        for mp3_info in mp3_files_to_process:
            logger.info(f"  → {mp3_info['contact']}/{mp3_info['filename']}")
        
        # ÉTAPE 2: Transcrire SEULEMENT les fichiers filtrés
        for idx, mp3_info in enumerate(mp3_files_to_process):
            mp3_path = mp3_info['path']
            contact = mp3_info['contact']
            filename = mp3_info['filename']
            
            logger.info(f"\n[TRANSCRIPTION] [{idx+1}/{len(mp3_files_to_process)}] {contact}/{filename}")
            self._log_debug(f"Traitement fichier {idx+1}/{len(mp3_files_to_process)}: {filename}")
            
            # Vérifier la taille
            if not os.path.exists(mp3_path):
                logger.error(f"[ERREUR] Fichier introuvable: {mp3_path}")
                self.debug_stats['errors'] += 1
                continue
            
            file_size = os.path.getsize(mp3_path)
            if file_size < 1000:
                logger.warning(f"[ATTENTION] Fichier trop petit: {filename} ({file_size} bytes)")
                self.debug_stats['errors'] += 1
                continue
            
            # Calculer le hash
            file_hash = self.registry.get_file_hash(mp3_path)
            if not file_hash:
                logger.error(f"[ERREUR] Impossible de calculer le hash pour {filename}")
                self.debug_stats['errors'] += 1
                continue
            
            # Vérifier si déjà transcrit
            if not self.force_mode:
                existing_transcription = self._check_real_transcription(file_hash)
                if existing_transcription:
                    logger.info(f"[OK] Transcription existante pour {filename}")
                    self.debug_stats['already_transcribed'] += 1
                    
                    if contact not in stats:
                        stats[contact] = 0
                    stats[contact] += 1
                    continue
            
            # TRANSCRIRE
            logger.info(f"[API] Transcription en cours: {filename}")
            transcription = self._transcribe_file_with_api(mp3_path)
            
            if transcription and len(transcription.strip()) > 10:
                logger.info(f"[SUCCÈS] {filename} ({len(transcription)} caractères)")
                
                # Enregistrer
                self.registry.register_transcription(file_hash, transcription)
                self._create_file_transcription_mapping(mp3_path, file_hash, transcription, contact)
                self._save_transcription_file(contact, filename, transcription, mp3_path)
                
                self.debug_stats['transcribed_now'] += 1
                
                if contact not in stats:
                    stats[contact] = 0
                stats[contact] += 1
            else:
                logger.error(f"[ÉCHEC] {filename}")
                self.debug_stats['errors'] += 1
        
        # Sauvegarder le registre
        self.registry.save()
        
        # Statistiques finales
        self._print_final_stats(stats)
        
        # Sauvegarder le log de debug
        self._save_debug_log()
        
        return stats
    
    def _get_direction_from_filename(self, filename: str) -> str:
        """Détermine la direction depuis le nom du fichier"""
        filename_lower = filename.lower()
        
        if filename_lower.startswith('sent_') or 'sent' in filename_lower:
            return 'sent'
        elif filename_lower.startswith('received_') or 'received' in filename_lower:
            return 'received'
        
        return 'unknown'
    
    def _check_real_transcription(self, file_hash: str) -> Optional[str]:
        """Vérifie si une transcription VALIDE existe"""
        transcription_data = self.registry.data['transcriptions'].get(file_hash)
        
        if not transcription_data:
            return None
        
        text = transcription_data.get('text', '')
        
        # Vérifications strictes
        if len(text.strip()) < 10:
            return None
        
        # Vérifier que ce n'est pas une erreur
        error_keywords = ['error', 'erreur', 'failed', 'api', 'quota', 'limit', 'insufficient']
        if any(word in text.lower() for word in error_keywords):
            return None
        
        # Vérifier que ce n'est pas un placeholder
        if text.startswith('Transcription non disponible'):
            return None
        
        return text
    
    def _transcribe_file_with_api(self, audio_file: str) -> Optional[str]:
        """Transcrit un fichier avec l'API OpenAI"""
        file_size = os.path.getsize(audio_file)
        
        if file_size > self.file_size_limit:
            logger.warning(f"[ATTENTION] Fichier trop gros: {audio_file} ({file_size / 1024 / 1024:.1f} MB)")
            return None
        
        base_name = os.path.basename(audio_file)
        
        for attempt in range(self.max_retries):
            try:
                self._log_debug(f"Appel API tentative {attempt + 1}/{self.max_retries}")
                logger.info(f"[API] Tentative {attempt + 1}/{self.max_retries}: {base_name}")
                
                self.debug_stats['api_calls'] += 1
                
                with open(audio_file, 'rb') as audio:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio,
                        language="fr",
                        response_format="text"
                    )
                
                if isinstance(response, str):
                    transcription = response.strip()
                else:
                    transcription = response.text.strip()
                
                if len(transcription) > 5:
                    logger.info(f"[SUCCÈS API] {base_name} ({len(transcription)} caractères)")
                    return transcription
                else:
                    logger.warning(f"[ATTENTION] Transcription trop courte: {base_name}")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[ERREUR API] {base_name}: {error_msg}")
                
                if "api key" in error_msg.lower() or "401" in error_msg:
                    logger.error("[ERREUR] CLÉ API INVALIDE")
                    return None
                
                if "rate limit" in error_msg.lower():
                    wait_time = self.retry_delay * 2
                    logger.warning(f"[RATE LIMIT] Attente {wait_time}s")
                    time.sleep(wait_time)
                elif attempt < self.max_retries - 1:
                    logger.info(f"[RETRY] Nouvel essai dans {self.retry_delay} secondes...")
                    time.sleep(self.retry_delay)
        
        logger.error(f"[ÉCHEC DÉFINITIF] {base_name}")
        return None
    
    def _create_file_transcription_mapping(self, mp3_file: str, file_hash: str, 
                                         transcription: str, contact: str):
        """Crée une correspondance fichier -> transcription"""
        mapping_dir = os.path.join(self.file_manager.output_dir, '.transcription_mappings')
        os.makedirs(mapping_dir, exist_ok=True)
        
        mapping_file = os.path.join(mapping_dir, f"{contact}_mappings.json")
        
        # Charger les correspondances existantes
        mappings = {}
        if os.path.exists(mapping_file):
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    mappings = json.load(f)
            except:
                mappings = {}
        
        # Ajouter cette correspondance
        base_name = os.path.basename(mp3_file)
        mappings[base_name] = {
            'hash': file_hash,
            'transcription': transcription,
            'file_path': mp3_file,
            'timestamp': datetime.now().isoformat()
        }
        
        # Sauvegarder
        try:
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
            self._log_debug(f"Mapping sauvegardé pour {base_name}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde mapping: {str(e)}")
    
    def _save_transcription_file(self, contact: str, filename: str, 
                                transcription: str, source_file: str):
        """Sauvegarde la transcription dans un fichier texte"""
        paths = self.file_manager.setup_contact_directory(contact)
        trans_dir = paths['transcriptions']
        
        base_name = os.path.splitext(filename)[0]
        trans_file = os.path.join(trans_dir, f"{base_name}.txt")
        
        try:
            with open(trans_file, 'w', encoding='utf-8') as f:
                f.write(f"Transcription du fichier: {filename}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Taille originale: {os.path.getsize(source_file)} bytes\n")
                f.write("=" * 50 + "\n\n")
                f.write(transcription)
            
            self._log_debug(f"Transcription sauvegardée: {trans_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde transcription: {str(e)}")
    
    def _print_final_stats(self, contact_stats: Dict[str, int]):
        """Affiche les statistiques finales OPTIMISÉES"""
        total_contacts = len(contact_stats)
        total_transcribed = sum(contact_stats.values())
        
        logger.info(f"\n{'='*60}")
        logger.info(f"[STATS] RÉSULTATS TRANSCRIPTION OPTIMISÉE")
        logger.info(f"{'='*60}")
        logger.info(f"Fichiers MP3 trouvés:        {self.debug_stats['mp3_found']}")
        logger.info(f"Filtrés (config):            {self.debug_stats['mp3_filtered']}")
        logger.info(f"À traiter:                   {self.debug_stats['mp3_found'] - self.debug_stats['mp3_filtered']}")
        logger.info(f"Déjà transcrits:             {self.debug_stats['already_transcribed']}")
        logger.info(f"Transcrits maintenant:       {self.debug_stats['transcribed_now']}")
        logger.info(f"Erreurs:                     {self.debug_stats['errors']}")
        logger.info(f"Appels API effectués:        {self.debug_stats['api_calls']}")
        logger.info(f"{'='*60}")
        
        # Calcul du taux de succès sur les fichiers TENTÉS
        total_attempted = (self.debug_stats['mp3_found'] - self.debug_stats['mp3_filtered'])
        if total_attempted > 0:
            success_rate = ((self.debug_stats['already_transcribed'] + self.debug_stats['transcribed_now']) 
                          / total_attempted) * 100
            logger.info(f"Taux de succès:              {success_rate:.1f}%")
            
            if success_rate < 95:
                logger.warning("[ATTENTION] Taux < 95% - Vérifiez les erreurs")
            else:
                logger.info("[SUCCÈS] Taux > 95%")
        
        # Optimisations réalisées
        if self.debug_stats['mp3_filtered'] > 0:
            logger.info(f"\n💡 OPTIMISATION RÉALISÉE:")
            logger.info(f"  - Fichiers non vérifiés: {self.debug_stats['mp3_filtered']}")
            logger.info(f"  - Temps économisé: ~{self.debug_stats['mp3_filtered'] * 0.5:.1f} secondes")
        
        # Détails par contact
        if contact_stats:
            logger.info(f"\nDétails par contact:")
            for contact, count in sorted(contact_stats.items()):
                logger.info(f"  - {contact}: {count} transcriptions")
    
    def _save_debug_log(self):
        """Sauvegarde le log de debug détaillé"""
        debug_file = os.path.join(
            self.file_manager.output_dir,
            f"transcriber_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=== TRANSCRIBER DEBUG LOG (OPTIMISÉ) ===\n")
                f.write(f"Date: {datetime.now()}\n")
                f.write(f"Mode: {'FORCE' if self.force_mode else 'NORMAL'}\n")
                f.write(f"API Key: {'SET' if self.api_key else 'MISSING'}\n")
                f.write(f"Transcribe Received: {self.transcribe_received}\n")
                f.write(f"Transcribe Sent: {self.transcribe_sent}\n\n")
                f.write("=== STATISTIQUES ===\n")
                for key, value in self.debug_stats.items():
                    f.write(f"{key}: {value}\n")
                f.write("\n=== LOG DÉTAILLÉ ===\n")
                f.write("\n".join(self.debug_log))
            
            logger.info(f"[LOG] Log de debug sauvegardé: {debug_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde debug log: {e}")