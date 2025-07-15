#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audio Processor OPTIMISÉ - Convertit SEULEMENT ce qui sera transcrit
VERSION OPTIMISÉE avec vérification rapide du cache
"""

import os
import subprocess
import logging
import time
import shutil
import tempfile
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from core import UnifiedRegistry, FileManager, MessageClassifier

logger = logging.getLogger('whatsapp_extractor')

class AudioProcessor:
    """Audio Processor OPTIMISÉ qui lit la config et convertit intelligemment"""
    
    def __init__(self, config, registry: UnifiedRegistry, file_manager: FileManager):
        self.config = config
        self.registry = registry
        self.file_manager = file_manager
        
        # NOUVEAU : Lire la configuration de transcription
        self.transcribe_received = config.getboolean('Processing', 'transcribe_received', fallback=True)
        self.transcribe_sent = config.getboolean('Processing', 'transcribe_sent', fallback=False)
        
        logger.info(f"[AUDIO CONFIG] Transcription - Reçus: {self.transcribe_received}, Envoyés: {self.transcribe_sent}")
        
        # Configuration de conversion
        self.mp3_quality = config.getint('Conversion', 'mp3_quality', fallback=2)
        self.parallel_conversions = 1  # Sécurité
        self.max_retries = 3
        
        # Répertoire temporaire court
        self.temp_dir = "C:\\Temp\\WA" if os.name == 'nt' else "/tmp/wa"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Vérifier FFmpeg
        self.ffmpeg_path = self._get_ffmpeg_path()
        
        # Statistiques détaillées
        self.stats = {
            'found': {'sent': 0, 'received': 0},
            'converted': {'sent': 0, 'received': 0},
            'skipped': {'sent': 0, 'received': 0, 'filtered': 0},
            'errors': {'sent': 0, 'received': 0}
        }
        
        # Logger de debug
        self.debug_log = []
        
        # OPTIMISATION : Créer un cache des fichiers déjà convertis
        self.converted_files_cache = self._build_converted_files_cache()
        logger.info(f"Cache des fichiers convertis créé avec {len(self.converted_files_cache)} entrées")
    
    def _build_converted_files_cache(self):
        """
        Construit un cache des fichiers déjà convertis pour éviter les reconversions
        Parcourt le registre et les dossiers audio_mp3 pour identifier les fichiers déjà traités
        """
        cache = {}
        
        # Méthode 1: Parcourir le registre pour les conversions enregistrées
        for file_hash, file_info in self.registry.data.get('files', {}).items():
            if file_info.get('type') == 'audio' and file_info.get('converted_path'):
                converted_path = file_info.get('converted_path')
                if converted_path and os.path.exists(converted_path):
                    # Extraire le nom de fichier sans extension
                    filename = os.path.basename(converted_path)
                    name_without_ext = os.path.splitext(filename)[0]
                    cache[name_without_ext] = True
                    logger.debug(f"Cache: {name_without_ext} (depuis registre)")
        
        # Méthode 2: Scanner les dossiers audio_mp3 existants
        output_dir = getattr(self.file_manager, 'output_dir', None)
        if output_dir and os.path.exists(output_dir):
            for contact_dir in os.listdir(output_dir):
                contact_path = os.path.join(output_dir, contact_dir)
                if not os.path.isdir(contact_path):
                    continue
                    
                audio_mp3_dir = os.path.join(contact_path, "audio_mp3")
                if os.path.exists(audio_mp3_dir):
                    for mp3_file in os.listdir(audio_mp3_dir):
                        if mp3_file.endswith('.mp3'):
                            # Ajouter au cache (sans extension)
                            name_without_ext = os.path.splitext(mp3_file)[0]
                            cache[name_without_ext] = True
                            logger.debug(f"Cache: {name_without_ext} (depuis dossier)")
        
        logger.info(f"Cache des fichiers convertis construit: {len(cache)} entrées")
        return cache
    
    def _get_ffmpeg_path(self):
        """Trouve FFmpeg de manière robuste"""
        candidates = [
            "ffmpeg",
            "C:\\ffmpeg\\bin\\ffmpeg.exe",
            os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe"),
            "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"
        ]
        
        for candidate in candidates:
            try:
                result = subprocess.run([candidate, "-version"], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"FFmpeg trouvé: {candidate}")
                    return candidate
            except:
                continue
        
        raise Exception("FFmpeg introuvable - Installation requise")
    
    def _should_convert_file(self, direction: str) -> bool:
        """
        NOUVEAU : Détermine si un fichier doit être converti selon la config
        """
        if direction == 'sent' and not self.transcribe_sent:
            return False
        if direction == 'received' and not self.transcribe_received:
            return False
        return True
    
    def _create_safe_filename(self, original_path: str) -> str:
        """Crée un nom de fichier qui PRÉSERVE l'UUID original"""
        import re
        
        # Extraire l'UUID du fichier OPUS
        uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', original_path)
        
        if uuid_match:
            uuid = uuid_match.group(1)
            safe_name = f"audio_{uuid}"
        else:
            base = os.path.splitext(os.path.basename(original_path))[0]
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', base)
            
            if len(safe_name) > 20:
                hash_part = hashlib.md5(base.encode()).hexdigest()[:8]
                safe_name = f"audio_{hash_part}"
            
            if not safe_name:
                safe_name = f"audio_{int(time.time())}"
        
        return safe_name
    
    def _convert_single_file(self, audio_file: str, contact: str, direction: str) -> Optional[str]:
        """Convertit UN fichier avec 100% de fiabilité"""
        
        self._log_debug(f"Conversion de {os.path.basename(audio_file)} ({direction})")
        
        # Nom de fichier sûr avec direction
        safe_name = self._create_safe_filename(audio_file)
        safe_name = f"{direction}_{safe_name}"
        
        # Chemin temporaire COURT
        temp_output = os.path.join(self.temp_dir, f"{safe_name}.mp3")
        
        # Chemin final
        contact_safe = re.sub(r'[^a-zA-Z0-9]', '_', contact)[:20]
        final_dir = os.path.join(self.file_manager.output_dir, contact_safe, "audio_mp3")
        os.makedirs(final_dir, exist_ok=True)
        final_output = os.path.join(final_dir, f"{safe_name}.mp3")
        
        # OPTIMISATION : Vérifier le cache au lieu du disque
        if safe_name in self.converted_files_cache:
            # Vérification plus rapide via le cache
            logger.info(f"Déjà converti (cache): {safe_name}")
            self.stats['skipped'][direction] += 1
            return final_output
            
        # Fallback: vérifier sur le disque et ajouter au cache si trouvé
        if os.path.exists(final_output) and os.path.getsize(final_output) > 1000:
            logger.info(f"Déjà converti (disque): {safe_name}")
            self.converted_files_cache[safe_name] = True
            self.stats['skipped'][direction] += 1
            return final_output
        
        # Vérifier fichier source
        if not os.path.exists(audio_file):
            logger.error(f"Source manquante: {audio_file}")
            self.stats['errors'][direction] += 1
            return None
        
        source_size = os.path.getsize(audio_file)
        if source_size < 100:
            logger.error(f"Fichier trop petit/corrompu: {audio_file}")
            self.stats['skipped'][direction] += 1
            return None
        
        # Tentatives de conversion
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Conversion {safe_name} - Tentative {attempt + 1}")
                
                # Commande FFmpeg
                cmd = [
                    self.ffmpeg_path,
                    "-hide_banner", "-loglevel", "error",
                    "-i", audio_file,
                    "-acodec", "libmp3lame",
                    "-q:a", str(self.mp3_quality),
                    "-ar", "22050",
                    "-ac", "1",
                    "-y",
                    temp_output
                ]
                
                # Exécution
                result = subprocess.run(cmd, capture_output=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(temp_output):
                    output_size = os.path.getsize(temp_output)
                    if output_size > 100:
                        # Déplacer vers destination finale
                        shutil.move(temp_output, final_output)
                        
                        logger.info(f"✓ Converti: {safe_name} ({output_size} bytes)")
                        self.stats['converted'][direction] += 1
                        
                        # Enregistrer dans le registre
                        file_hash = self.registry.get_file_hash(audio_file)
                        if file_hash:
                            self.registry.register_conversion(file_hash, final_output)
                        
                        # Ajouter au cache
                        self.converted_files_cache[safe_name] = True
                        
                        return final_output
                
                # Si échec, nettoyer
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                    
                logger.warning(f"Tentative {attempt + 1} échouée pour {safe_name}")
                time.sleep(1)
                
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout conversion {safe_name}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            except Exception as e:
                logger.error(f"Erreur conversion {safe_name}: {e}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
        
        logger.error(f"✗ Échec définitif: {safe_name}")
        self.stats['errors'][direction] += 1
        return None
    
    def process_all_audio(self, conversations: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """
        OPTIMISÉ : Traite SEULEMENT les audios selon la configuration
        AVEC vérification rapide du cache pour éviter les ralentissements
        """
        
        logger.info("=== TRAITEMENT AUDIO OPTIMISÉ ===")
        logger.info(f"Configuration: Reçus={self.transcribe_received}, Envoyés={self.transcribe_sent}")
        
        results = {}
        total_files = 0
        total_to_convert = 0
        
        # ÉTAPE 1: Compter et filtrer
        for contact, messages in conversations.items():
            for direction in ['sent', 'received']:
                audio_files = self.file_manager.get_audio_files(contact, direction)
                self.stats['found'][direction] += len(audio_files)
                
                # NOUVEAU : Compter combien seront VRAIMENT convertis
                if self._should_convert_file(direction):
                    total_to_convert += len(audio_files)
                else:
                    self.stats['skipped']['filtered'] += len(audio_files)
                
                total_files += len(audio_files)
        
        logger.info(f"Total fichiers audio trouvés: {total_files}")
        logger.info(f"  - Envoyés: {self.stats['found']['sent']}")
        logger.info(f"  - Reçus: {self.stats['found']['received']}")
        logger.info(f"Fichiers à convertir (selon config): {total_to_convert}")
        logger.info(f"Fichiers ignorés (config): {self.stats['skipped']['filtered']}")
        
        # ÉTAPE 2: Traiter SEULEMENT ce qui doit l'être
        for contact, messages in conversations.items():
            logger.info(f"\n=== CONTACT: {contact} ===")
            
            contact_results = {'sent': 0, 'received': 0, 'errors': 0}
            
            for direction in ['sent', 'received']:
                # OPTIMISATION : Skip si pas nécessaire
                if not self._should_convert_file(direction):
                    logger.info(f"Skip {direction} (config: transcribe_{direction}=False)")
                    continue
                
                audio_files = self.file_manager.get_audio_files(contact, direction)
                
                if not audio_files:
                    logger.info(f"Aucun fichier audio {direction}")
                    continue
                
                # OPTIMISATION : Vérifier rapidement le cache d'abord
                files_to_convert = []
                files_already_converted = 0
                
                for audio_file in audio_files:
                    safe_name = self._create_safe_filename(audio_file)
                    safe_name = f"{direction}_{safe_name}"
                    
                    if safe_name in self.converted_files_cache:
                        files_already_converted += 1
                        contact_results[direction] += 1
                    else:
                        files_to_convert.append(audio_file)
                
                if files_already_converted > 0:
                    logger.info(f"Déjà convertis (cache rapide): {files_already_converted} fichiers {direction}")
                    self.stats['skipped'][direction] += files_already_converted
                
                if files_to_convert:
                    logger.info(f"Conversion de {len(files_to_convert)} fichiers {direction} nécessaires")
                    
                    # Convertir seulement ceux qui en ont besoin
                    for i, audio_file in enumerate(files_to_convert):
                        logger.info(f"[{i+1}/{len(files_to_convert)}] {direction.upper()}: {os.path.basename(audio_file)}")
                        
                        result = self._convert_single_file(audio_file, contact, direction)
                        if result:
                            contact_results[direction] += 1
                        else:
                            contact_results['errors'] += 1
                        
                        # Pause seulement pour les conversions réelles
                        time.sleep(0.5)
            
            results[contact] = contact_results
            
            # Log uniquement si quelque chose a été fait
            if contact_results['sent'] > 0 or contact_results['received'] > 0 or contact_results['errors'] > 0:
                logger.info(f"Contact {contact} terminé:")
                logger.info(f"  - Envoyés convertis: {contact_results['sent']}")
                logger.info(f"  - Reçus convertis: {contact_results['received']}")
                logger.info(f"  - Erreurs: {contact_results['errors']}")
        
        # ÉTAPE 3: Sauvegarder le registre
        self.registry.save()
        
        # Statistiques finales
        self._print_final_stats()
        
        return results
    
    def _log_debug(self, message: str):
        """Log de debug détaillé"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_log.append(f"[{timestamp}] {message}")
        logger.debug(f"[AUDIO_DEBUG] {message}")
    
    def _print_final_stats(self):
        """Affiche les statistiques finales OPTIMISÉES"""
        total_found = self.stats['found']['sent'] + self.stats['found']['received']
        total_converted = self.stats['converted']['sent'] + self.stats['converted']['received']
        total_errors = self.stats['errors']['sent'] + self.stats['errors']['received']
        total_filtered = self.stats['skipped']['filtered']
        total_skipped = self.stats['skipped']['sent'] + self.stats['skipped']['received']
        
        # Calculer le taux de succès sur les fichiers TENTÉS seulement
        total_attempted = total_converted + total_errors
        if total_attempted > 0:
            success_rate = (total_converted / total_attempted) * 100
        else:
            success_rate = 100.0  # Si rien tenté, c'est un succès
        
        logger.info(f"\n=== RÉSULTATS FINAUX OPTIMISÉS ===")
        logger.info(f"FICHIERS TROUVÉS: {total_found}")
        logger.info(f"  - Envoyés: {self.stats['found']['sent']}")
        logger.info(f"  - Reçus: {self.stats['found']['received']}")
        
        logger.info(f"\nFILTRAGE PAR CONFIG:")
        logger.info(f"  - Ignorés (config): {total_filtered}")
        logger.info(f"  - Déjà convertis (cache): {total_skipped}")
        logger.info(f"  - À convertir: {total_attempted}")
        
        logger.info(f"\nFICHIERS CONVERTIS: {total_converted}")
        logger.info(f"  - Envoyés: {self.stats['converted']['sent']}")
        logger.info(f"  - Reçus: {self.stats['converted']['received']}")
        
        logger.info(f"\nERREURS: {total_errors}")
        logger.info(f"  - Envoyés: {self.stats['errors']['sent']}")
        logger.info(f"  - Reçus: {self.stats['errors']['received']}")
        
        logger.info(f"\nTAUX DE SUCCÈS: {success_rate:.1f}%")
        
        # Économies réalisées
        time_saved = (total_filtered + total_skipped) * 2  # ~2 secondes par fichier économisées
        if time_saved > 0:
            logger.info(f"\n💡 OPTIMISATION:")
            logger.info(f"  - Fichiers non traités: {total_filtered + total_skipped}")
            logger.info(f"  - Temps économisé: ~{time_saved} secondes ({time_saved/60:.1f} minutes)")
        
        if success_rate < 95 and total_attempted > 0:
            logger.warning(f"⚠ Taux < 95% - Vérifier les erreurs")
        else:
            logger.info(f"✓ Succès!")
        
        # Sauvegarder le log de debug
        self._save_debug_log()
    
    def _save_debug_log(self):
        """Sauvegarde le log de debug détaillé"""
        debug_file = os.path.join(
            self.file_manager.output_dir,
            f"audio_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=== AUDIO PROCESSOR DEBUG LOG (OPTIMISÉ) ===\n")
                f.write(f"Date: {datetime.now()}\n")
                f.write(f"Config: Reçus={self.transcribe_received}, Envoyés={self.transcribe_sent}\n\n")
                f.write("\n".join(self.debug_log))
            logger.info(f"Log de debug sauvegardé: {debug_file}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde debug log: {e}")