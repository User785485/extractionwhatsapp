import os
import json
import logging
from datetime import datetime
from collections import defaultdict

from config import Config
from core import UnifiedRegistry, FileManager
from utils import setup_logging, format_size

logger = logging.getLogger('whatsapp_extractor')

class Diagnostic:
    """Outils de diagnostic pour vérifier l'intégrité"""
    
    def __init__(self, config_file='config.ini'):
        self.config = Config(config_file)
        setup_logging(self.config)
        
        output_dir = self.config.get('Paths', 'output_dir')
        self.registry = UnifiedRegistry(output_dir)
        self.file_manager = FileManager(output_dir)
    
    def run_full_diagnostic(self):
        """Lance un diagnostic complet"""
        logger.info("="*60)
        logger.info("DIAGNOSTIC COMPLET DU SYSTÈME")
        logger.info("="*60)
        
        # 1. Vérifier le registre
        self._check_registry_integrity()
        
        # 2. Vérifier les fichiers
        self._check_files_consistency()
        
        # 3. Vérifier les transcriptions
        self._check_transcriptions()
        
        # 4. Statistiques
        self._show_statistics()
        
        # 5. Recommandations
        self._show_recommendations()
    
    def _check_registry_integrity(self):
        """Vérifie l'intégrité du registre"""
        logger.info("\n--- VÉRIFICATION DU REGISTRE ---")
        
        issues = []
        
        # Vérifier la version
        version = self.registry.data.get('version', 'unknown')
        logger.info(f"Version du registre: {version}")
        
        # Vérifier les fichiers référencés
        missing_files = 0
        for file_hash, file_info in self.registry.data['files'].items():
            if 'path' in file_info and not os.path.exists(file_info['path']):
                missing_files += 1
                issues.append(f"Fichier manquant: {file_info['path']}")
        
        logger.info(f"Fichiers dans le registre: {len(self.registry.data['files'])}")
        logger.info(f"Fichiers manquants: {missing_files}")
        
        # Vérifier les doublons
        paths_seen = defaultdict(list)
        for file_hash, file_info in self.registry.data['files'].items():
            if 'path' in file_info:
                paths_seen[file_info['path']].append(file_hash)
        
        duplicates = {path: hashes for path, hashes in paths_seen.items() if len(hashes) > 1}
        if duplicates:
            logger.warning(f"Doublons détectés: {len(duplicates)} fichiers")
            for path, hashes in list(duplicates.items())[:5]:  # Montrer 5 exemples
                logger.warning(f"  - {path}: {len(hashes)} entrées")
        
        return issues
    
    def _check_files_consistency(self):
        """Vérifie la cohérence des fichiers"""
        logger.info("\n--- VÉRIFICATION DES FICHIERS ---")
        
        # Compter les fichiers par type et direction
        stats = defaultdict(lambda: defaultdict(int))
        
        for file_hash, file_info in self.registry.data['files'].items():
            file_type = file_info.get('type', 'unknown')
            direction = file_info.get('direction', 'unknown')
            stats[file_type][direction] += 1
        
        # Afficher les stats
        for file_type, directions in stats.items():
            logger.info(f"\n{file_type.upper()}:")
            for direction, count in directions.items():
                logger.info(f"  - {direction}: {count} fichiers")
        
        # Vérifier les préfixes
        incorrect_prefixes = 0
        for file_hash, file_info in self.registry.data['files'].items():
            if 'path' in file_info and 'direction' in file_info:
                filename = os.path.basename(file_info['path'])
                expected_prefix = f"{file_info['direction']}_"
                
                if not filename.startswith(expected_prefix) and file_info['type'] == 'audio':
                    incorrect_prefixes += 1
        
        if incorrect_prefixes > 0:
            logger.warning(f"Fichiers audio avec préfixe incorrect: {incorrect_prefixes}")
    
    def _check_transcriptions(self):
        """Vérifie les transcriptions"""
        logger.info("\n--- VÉRIFICATION DES TRANSCRIPTIONS ---")
        
        total_audio = sum(1 for f in self.registry.data['files'].values() 
                         if f.get('type') == 'audio')
        total_transcribed = len(self.registry.data['transcriptions'])
        
        logger.info(f"Fichiers audio: {total_audio}")
        logger.info(f"Transcriptions: {total_transcribed}")
        
        if total_audio > 0:
            percentage = (total_transcribed / total_audio) * 100
            logger.info(f"Taux de transcription: {percentage:.1f}%")
        
        # Vérifier les transcriptions vides ou erreurs
        empty_trans = 0
        error_trans = 0
        
        for trans_info in self.registry.data['transcriptions'].values():
            text = trans_info.get('text', '')
            if not text or len(text.strip()) == 0:
                empty_trans += 1
            elif any(word in text.lower() for word in ['error', 'erreur', 'api']):
                error_trans += 1
        
        if empty_trans > 0:
            logger.warning(f"Transcriptions vides: {empty_trans}")
        if error_trans > 0:
            logger.warning(f"Transcriptions avec erreurs: {error_trans}")
    
    def _show_statistics(self):
        """Affiche les statistiques globales"""
        logger.info("\n--- STATISTIQUES GLOBALES ---")
        
        # Par contact
        logger.info(f"\nContacts: {len(self.registry.data['contacts'])}")
        
        for contact, info in self.registry.data['contacts'].items():
            stats = info.get('stats', {})
            logger.info(f"\n{contact}:")
            logger.info(f"  - Total messages: {stats.get('total_messages', 0)}")
            logger.info(f"  - Messages reçus: {stats.get('received_messages', 0)}")
            logger.info(f"  - Messages envoyés: {stats.get('sent_messages', 0)}")
            logger.info(f"  - Fichiers audio: {stats.get('audio_files', 0)}")
            logger.info(f"  - Transcrits: {stats.get('transcribed_files', 0)}")
    
    def _show_recommendations(self):
        """Affiche des recommandations"""
        logger.info("\n--- RECOMMANDATIONS ---")
        
        recommendations = []
        
        # Vérifier le mode
        mode = self.config.get('Processing', 'mode', fallback='received_only')
        if mode == 'both':
            recommendations.append("Mode 'both' actif - coûts de transcription doublés")
        
        # Vérifier les transcriptions manquantes
        audio_files = [f for f in self.registry.data['files'].values() 
                      if f.get('type') == 'audio']
        transcribed = len(self.registry.data['transcriptions'])
        
        if audio_files and transcribed < len(audio_files):
            missing = len(audio_files) - transcribed
            recommendations.append(f"{missing} fichiers audio non transcrits")
        
        # Afficher les recommandations
        if recommendations:
            for rec in recommendations:
                logger.info(f"  ⚠️  {rec}")
        else:
            logger.info("  ✓ Aucun problème détecté")

def main():
    """Point d'entrée du diagnostic"""
    diag = Diagnostic()
    diag.run_full_diagnostic()

if __name__ == "__main__":
    main()