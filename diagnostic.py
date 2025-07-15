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
        
        # 4. Vérifier la sanitization des noms et l'accès au registre
        self._check_sanitization_and_registry()
        
        # 5. Statistiques
        self._show_statistics()
        
        # 6. Recommandations
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
    
    def _check_sanitization_and_registry(self):
        """Vérifie la sanitization des noms et l'accès au registre"""
        logger.info("\n--- VÉRIFICATION DES AMÉLIORATIONS ---")
        
        # 1. Vérifier la sanitization des noms de contacts
        from core.file_manager import FileManager
        import re
        import os
        
        # Tests de sanitization
        test_contacts = [
            "Contact avec un nom très long qui dépasse largement la limite précédente de 20 caractères",
            "06 12 34 56 78 - Jean Dupont (Cousin)",
            "♥♦♣♠ Émojis et Caractères Spéciaux ☺☻☹",
            "Contact@with.email-address",
            "Client_2025-06_22_numéro_important"  
        ]
        
        logger.info("1. Test de sanitization des noms:")
        for test in test_contacts:
            sanitized = self.file_manager.sanitize_filename(test)
            logger.info(f"  Original: '{test}'")
            logger.info(f"  Sanitizé: '{sanitized}'")
            logger.info(f"  Longueur: {len(sanitized)} caractères")
            
            # Vérifier qu'on ne retourne pas "contact_hash"
            if sanitized.startswith("contact_") and len(sanitized) < 20:
                logger.error(f"  ⚠️ PROBLÈME: Format contact_hash détecté!")
            else:
                logger.info(f"  ✓ OK: Format long conservé")
        
        # 2. Tester l'accès aux données du registre
        logger.info("\n2. Test d'accès au registre:")
        
        # Compter les contacts dans le registre
        registry_contacts = set()
        
        # Parcourir les fichiers audio
        for file_hash, file_info in self.registry.data.get('files', {}).items():
            if file_info.get('type') == 'audio' and file_info.get('contact'):
                registry_contacts.add(file_info.get('contact'))
        
        # Compter les transcriptions par contact
        trans_by_contact = {}
        for file_hash, trans_info in self.registry.data.get('transcriptions', {}).items():
            # Retrouver le fichier d'origine
            file_info = self.registry.data.get('files', {}).get(file_hash, {})
            if file_info and 'contact' in file_info:
                contact = file_info.get('contact')
                if contact not in trans_by_contact:
                    trans_by_contact[contact] = 0
                trans_by_contact[contact] += 1
        
        # Afficher les stats
        logger.info(f"Contacts trouvés dans le registre: {len(registry_contacts)}")
        logger.info(f"Contacts avec transcriptions: {len(trans_by_contact)}")
        
        # Afficher le top 5 des contacts avec le plus de transcriptions
        if trans_by_contact:
            logger.info("\nTop 5 des contacts avec le plus de transcriptions:")
            sorted_contacts = sorted(trans_by_contact.items(), key=lambda x: x[1], reverse=True)[:5]
            for contact, count in sorted_contacts:
                logger.info(f"  - {contact}: {count} transcriptions")
                
        # Vérifier s'il existe des collisions (contact_hash)
        collision_pattern = re.compile(r"contact_[0-9a-f]{8}")
        collisions = [c for c in registry_contacts if collision_pattern.match(c)]
        
        if collisions:
            logger.error(f"⚠️ PROBLÈME: {len(collisions)} contacts avec format contact_hash détectés!")
            logger.error("Ces contacts risquent de se chevaucher et perdre des données!")
            # Afficher quelques exemples
            for c in collisions[:5]:
                logger.error(f"  - {c}")
        else:
            logger.info("✓ Aucune collision de type contact_hash détectée")
        
        # Vérifier si le registre contient bien des données
        if not self.registry.data.get('transcriptions'):
            logger.warning("⚠️ Le registre ne contient pas de transcriptions!")
        else:
            logger.info(f"✓ Le registre contient {len(self.registry.data.get('transcriptions', {}))} transcriptions")

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
            
        # Nouvelles recommandations
        from pathlib import Path
        import re
        
        # Vérifier les noms de dossiers avec contact_hash
        output_dir = self.config.get('Paths', 'output_dir')
        all_dirs = [d for d in Path(output_dir).iterdir() if d.is_dir() and not d.name.startswith('.')]
        collision_pattern = re.compile(r"contact_[0-9a-f]{8}")
        hash_dirs = [d for d in all_dirs if collision_pattern.match(d.name)]
        
        if hash_dirs:
            recommendations.append(f"{len(hash_dirs)} dossiers avec format contact_hash existent déjà")
            recommendations.append("Envisager de regénérer ces dossiers avec le nouveau format")
        
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