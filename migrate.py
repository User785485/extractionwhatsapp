import os
import json
import logging
import shutil
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Set

from config import Config
from core import UnifiedRegistry
from utils.common import setup_logging, load_json_file, get_file_hash

logger = logging.getLogger('whatsapp_extractor')

class Migrator:
    """
    Migration des anciennes données vers le nouveau système unifié
    Fusionne les 5 registres en 1 seul
    
    Modes de fonctionnement:
    - Normal: Migration complète avec sauvegarde
    - Dry-run: Simulation sans modification des fichiers réels
    - Contact-limit: Limite le nombre de contacts à traiter
    """
    
    def __init__(self, config_file='config.ini', dry_run=False, contact_limit=None):
        self.config = Config(config_file)
        setup_logging(self.config)
        
        self.output_dir = self.config.get('Paths', 'output_dir')
        self.dry_run = dry_run
        self.contact_limit = contact_limit
        
        # En mode simulation, on crée un registre temporaire qui ne sera pas sauvegardé
        if dry_run:
            logger.info("MODE SIMULATION: Aucune modification ne sera enregistrée")
            self.registry_path = os.path.join(self.output_dir, 'temp_simulation_registry.json')
        else:
            self.registry_path = None
            
        # En mode simulation, nous devons modifier le chemin du registre dans l'instance après création
        self.new_registry = UnifiedRegistry(self.output_dir)
        if self.dry_run:
            # Remplacer le chemin du registre pour le mode simulation
            self.new_registry.registry_path = self.registry_path
        
        # Contacts traités (pour la limite)
        self.processed_contacts = set()
        
        # Statistiques de migration
        self.stats = {
            'html_files': 0,
            'audio_files': 0,
            'conversions': 0,
            'transcriptions': 0,
            'super_files': 0,
            'errors': 0,
            'skipped_contacts': 0
        }
    
    def migrate_all(self, backup=True):
        """
        Lance la migration complète
        
        Args:
            backup: Si True, crée une sauvegarde avant migration
            
        En mode dry-run, aucune sauvegarde n'est créée
        En mode contact-limit, seuls les X premiers contacts sont migrés
        """
        mode_info = ""
        if self.dry_run:
            mode_info = " [MODE SIMULATION]"
            backup = False  # Pas de sauvegarde en mode simulation
            
        if self.contact_limit:
            mode_info += f" [LIMITE: {self.contact_limit} CONTACTS]"
            
        logger.info("="*60)
        logger.info(f"MIGRATION DES ANCIENNES DONNÉES VERS LE SYSTÈME UNIFIÉ{mode_info}")
        logger.info("="*60)
        
        # Créer une sauvegarde si demandé et si on n'est pas en mode simulation
        if backup and not self.dry_run:
            self._create_backup()
        
        # Vérifier l'existence des anciens registres
        old_registries = self._find_old_registries()
        if not old_registries:
            logger.warning("Aucun ancien registre trouvé. Rien à migrer.")
            return
        
        logger.info(f"Registres trouvés: {', '.join(old_registries.keys())}")
        
        # Migration dans l'ordre logique
        # 1. D'abord les fichiers HTML (extraction_registry)
        if 'extraction' in old_registries:
            self._migrate_extraction_registry(old_registries['extraction'])
        
        # 2. Puis les conversions audio
        if 'audio_conversion' in old_registries:
            self._migrate_audio_registry(old_registries['audio_conversion'])
        
        # 3. Les super fichiers
        if 'super_files' in old_registries:
            self._migrate_super_files_registry(old_registries['super_files'])
        
        # 4. Enfin les transcriptions
        if 'transcription' in old_registries:
            self._migrate_transcription_registry(old_registries['transcription'])
        
        # 5. Migrer aussi les fichiers avec mauvais préfixes
        self._fix_file_prefixes()
        
        # Sauvegarder le nouveau registre sauf en mode simulation
        if not self.dry_run:
            self.new_registry.save()
        else:
            # En mode simulation, on génère un rapport de compatibilité
            self._generate_compatibility_report()
        
        # Afficher le résumé
        self._show_migration_summary()
    
    def _find_old_registries(self) -> Dict[str, str]:
        """Trouve tous les anciens registres"""
        registries = {}
        
        registry_files = {
            'extraction': 'extraction_registry.json',
            'audio_conversion': 'audio_conversion_registry.json',
            'transcription': 'transcription_registry.json',
            'super_files': 'super_files_registry.json'
        }
        
        for key, filename in registry_files.items():
            file_path = os.path.join(self.output_dir, filename)
            if os.path.exists(file_path):
                registries[key] = file_path
        
        return registries
    
    def _create_backup(self):
        """Crée une sauvegarde complète avant migration"""
        backup_dir = os.path.join(
            self.output_dir, 
            f'backup_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        logger.info(f"Création de la sauvegarde dans: {backup_dir}")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Sauvegarder tous les registres existants
        for file in os.listdir(self.output_dir):
            if file.endswith('_registry.json'):
                src = os.path.join(self.output_dir, file)
                dst = os.path.join(backup_dir, file)
                shutil.copy2(src, dst)
                logger.info(f"  ✓ Sauvegardé: {file}")
    
    def _migrate_extraction_registry(self, registry_path: str):
        """Migre le registre d'extraction HTML"""
        logger.info("\n--- Migration extraction_registry.json ---")
        old_data = load_json_file(registry_path)
        
        for html_file, info in old_data.items():
            try:
                contact_name = info.get('contact_name', 'Unknown')
                
                # Vérifier la limite de contacts
                if contact_name != 'Unknown':
                    # Si on a atteint la limite de contacts, on ignore ce fichier
                    if self.contact_limit and len(self.processed_contacts) >= self.contact_limit:
                        if contact_name not in self.processed_contacts:
                            self.stats['skipped_contacts'] += 1
                            continue
                    
                    # Ajouter à la liste des contacts traités
                    self.processed_contacts.add(contact_name)
                
                file_hash = info.get('hash')
                
                # Enregistrer dans le nouveau registre
                if file_hash:
                    self.new_registry.register_file(
                        html_file,
                        'html',
                        'source',
                        contact_name,
                        {
                            'original_hash': file_hash,
                            'timestamp': info.get('timestamp'),
                            'migrated_from': 'extraction_registry'
                        }
                    )
                    self.stats['html_files'] += 1
                    
            except Exception as e:
                logger.error(f"Erreur migration HTML {html_file}: {str(e)}")
                self.stats['errors'] += 1
        
        logger.info(f"  ✓ {self.stats['html_files']} fichiers HTML migrés")
    
    def _migrate_audio_registry(self, registry_path: str):
        """Migre le registre de conversion audio"""
        logger.info("\n--- Migration audio_conversion_registry.json ---")
        old_data = load_json_file(registry_path)
        
        for audio_file, info in old_data.items():
            try:
                # Extraire les informations
                contact = self._extract_contact_from_path(audio_file)
                direction = self._determine_direction(audio_file)
                file_hash = info.get('hash')
                
                if not file_hash:
                    # Calculer le hash si absent
                    file_hash = get_file_hash(audio_file)
                
                if file_hash and os.path.exists(audio_file):
                    # Enregistrer le fichier audio
                    self.new_registry.register_file(
                        audio_file,
                        'audio',
                        direction,
                        contact,
                        {
                            'original_info': info,
                            'migrated_from': 'audio_conversion_registry'
                        }
                    )
                    self.stats['audio_files'] += 1
                    
                    # Enregistrer la conversion si présente
                    if 'output' in info and os.path.exists(info['output']):
                        self.new_registry.register_conversion(file_hash, info['output'])
                        self.stats['conversions'] += 1
                        
            except Exception as e:
                logger.error(f"Erreur migration audio {audio_file}: {str(e)}")
                self.stats['errors'] += 1
        
        logger.info(f"  ✓ {self.stats['audio_files']} fichiers audio migrés")
        logger.info(f"  ✓ {self.stats['conversions']} conversions migrées")
    
    def _migrate_transcription_registry(self, registry_path: str):
        """Migre le registre de transcription"""
        logger.info("\n--- Migration transcription_registry.json ---")
        old_data = load_json_file(registry_path)
        
        for audio_file, info in old_data.items():
            try:
                file_hash = info.get('hash')
                if not file_hash:
                    file_hash = get_file_hash(audio_file)
                
                if not file_hash:
                    continue
                
                # Chercher le fichier de transcription
                trans_file = self._find_transcription_file(audio_file)
                
                if trans_file and os.path.exists(trans_file):
                    with open(trans_file, 'r', encoding='utf-8') as f:
                        transcription = f.read().strip()
                    
                    if transcription and self._is_valid_transcription(transcription):
                        self.new_registry.register_transcription(file_hash, transcription)
                        self.stats['transcriptions'] += 1
                        
            except Exception as e:
                logger.error(f"Erreur migration transcription {audio_file}: {str(e)}")
                self.stats['errors'] += 1
        
        logger.info(f"  ✓ {self.stats['transcriptions']} transcriptions migrées")
    
    def _migrate_super_files_registry(self, registry_path: str):
        """Migre le registre des super fichiers"""
        logger.info("\n--- Migration super_files_registry.json ---")
        old_data = load_json_file(registry_path)
        
        for key, info in old_data.items():
            try:
                # Parser la clé pour extraire les informations
                parts = key.split('_')
                
                # Déterminer contact, direction et période
                contact = None
                direction = None
                period = None
                
                # Logique de parsing améliorée
                if 'received' in key:
                    direction = 'received'
                elif 'sent' in key:
                    direction = 'sent'
                
                # Extraire le contact (premier élément avant received/sent)
                for i, part in enumerate(parts):
                    if part in ['received', 'sent'] and i > 0:
                        contact = '_'.join(parts[:i])
                        # La période est après la direction
                        if i + 1 < len(parts):
                            period = parts[i + 1]
                        break
                
                if not contact:
                    contact = parts[0] if parts else 'unknown'
                
                if not period:
                    # Essayer d'extraire une date
                    import re
                    date_match = re.search(r'\d{4}-\d{2}', key)
                    period = date_match.group(0) if date_match else 'unknown'
                
                # Construire le chemin du super fichier
                if 'filename' in info:
                    super_path = os.path.join(
                        self.output_dir, contact, 'SUPER_FICHIERS', info['filename']
                    )
                elif 'path' in info:
                    super_path = info['path']
                else:
                    continue
                
                # Récupérer les fichiers sources
                source_hashes = []
                if 'source_files' in info:
                    source_hashes = info['source_files']
                elif 'files_hash' in info:
                    # Ancien format - essayer de reconstruire
                    source_hashes = [info['files_hash']]
                
                # Enregistrer le super fichier
                self.new_registry.register_super_file(
                    contact,
                    period,
                    direction or 'unknown',
                    super_path,
                    source_hashes
                )
                self.stats['super_files'] += 1
                
            except Exception as e:
                logger.error(f"Erreur migration super fichier {key}: {str(e)}")
                self.stats['errors'] += 1
        
        logger.info(f"  ✓ {self.stats['super_files']} super fichiers migrés")
    
    def _fix_file_prefixes(self):
        """Corrige les préfixes des fichiers mal nommés"""
        logger.info("\n--- Correction des préfixes de fichiers ---")
        
        fixed_count = 0
        
        # Parcourir tous les contacts
        for contact in os.listdir(self.output_dir):
            contact_path = os.path.join(self.output_dir, contact)
            if not os.path.isdir(contact_path) or contact.startswith('.'):
                continue
            
            # Vérifier les fichiers audio
            for media_dir in ['media_recus', 'media_envoyes']:
                audio_dir = os.path.join(contact_path, media_dir, 'audio')
                if not os.path.exists(audio_dir):
                    continue
                
                expected_prefix = 'received_' if media_dir == 'media_recus' else 'sent_'
                
                for file in os.listdir(audio_dir):
                    if not file.startswith(expected_prefix):
                        old_path = os.path.join(audio_dir, file)
                        new_name = f"{expected_prefix}{file}"
                        new_path = os.path.join(audio_dir, new_name)
                        
                        try:
                            os.rename(old_path, new_path)
                            logger.info(f"  ✓ Renommé: {file} → {new_name}")
                            fixed_count += 1
                        except Exception as e:
                            logger.error(f"  ✗ Erreur renommage {file}: {str(e)}")
        
        if fixed_count > 0:
            logger.info(f"  ✓ {fixed_count} fichiers renommés")
    
    def _extract_contact_from_path(self, file_path):
        """Extrait le nom du contact depuis le chemin du fichier"""
        parts = file_path.split(os.path.sep)
        for part in parts:
            if part.startswith('+') or '@' in part:
                # Vérifier si on a atteint la limite de contacts
                if self.contact_limit and len(self.processed_contacts) >= self.contact_limit:
                    if part not in self.processed_contacts:
                        self.stats['skipped_contacts'] += 1
                        return None
                
                # Ajouter à la liste des contacts traités
                self.processed_contacts.add(part)
                return part
                
        return 'Unknown'
    
    def _determine_direction(self, file_path: str) -> str:
        """Détermine la direction d'un message depuis son chemin"""
        path_lower = file_path.lower()
        
        # Vérifier le nom du fichier d'abord
        filename = os.path.basename(file_path).lower()
        if filename.startswith('received_'):
            return 'received'
        elif filename.startswith('sent_'):
            return 'sent'
        
        # Puis le chemin
        if 'media_recus' in path_lower:
            return 'received'
        elif 'media_envoyes' in path_lower:
            return 'sent'
        
        return 'unknown'
    
    def _find_transcription_file(self, audio_file: str) -> Optional[str]:
        """Trouve le fichier de transcription correspondant"""
        contact = self._extract_contact_from_path(audio_file)
        if not contact:  # Si contact ignoré à cause de la limite
            return None
            
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        
        # Chemins possibles pour la transcription
        possible_paths = [
            os.path.join(self.output_dir, contact, 'transcriptions', f"{base_name}.txt"),
            os.path.join(self.output_dir, contact, 'transcriptions', f"{base_name}_transcription.txt"),
            os.path.join(self.output_dir, contact, 'transcriptions', f"{base_name}_complete.txt")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _is_valid_transcription(self, text: str) -> bool:
        """Vérifie si une transcription est valide"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Mots-clés indiquant une erreur
        error_keywords = ['error', 'erreur', 'quota', 'api', 'openai', 
                         'exceeded', 'dépassé', 'limit', 'insufficient']
        
        text_lower = text.lower()
        return not any(keyword in text_lower for keyword in error_keywords)
    
    def _generate_compatibility_report(self):
        """Génère un rapport de compatibilité en mode simulation"""
        os.makedirs('logs', exist_ok=True)
        report_path = os.path.join('logs', f"migration_compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        compatibility_report = {
            'timestamp': datetime.now().isoformat(),
            'contacts_processed': list(self.processed_contacts),
            'contact_count': len(self.processed_contacts),
            'stats': self.stats,
            'recommendations': [],
            'potential_issues': [],
        }
        
        # Analyser les statistiques pour formuler des recommandations
        if self.stats['errors'] > 0:
            compatibility_report['potential_issues'].append({
                'severity': 'HIGH',
                'message': f"Des erreurs ({self.stats['errors']}) ont été détectées pendant la simulation",
                'recommendation': "Vérifiez les logs pour identifier et corriger ces erreurs avant de procéder à la migration réelle."
            })
        
        if self.stats['conversions'] < self.stats['audio_files']:
            compatibility_report['potential_issues'].append({
                'severity': 'MEDIUM',
                'message': f"Certains fichiers audio n'ont pas de conversion associée ({self.stats['audio_files'] - self.stats['conversions']})",
                'recommendation': "Ces fichiers devront être reconvertis après la migration."
            })
        
        # Recommandations sur les doublons basées sur l'analyse précédente
        compatibility_report['recommendations'].append({
            'priority': 'HIGH',
            'message': "Effectuez une analyse complète des doublons AVANT la migration réelle",
            'details': "Cela permettra d'identifier les fichiers qui peuvent être supprimés en toute sécurité."
        })
            
        # Sauvegarder le rapport
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(compatibility_report, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Rapport de compatibilité généré: {report_path}")
        return report_path
        
    def _show_migration_summary(self):
        """Affiche le résumé de la migration"""
        mode_info = ""
        if self.dry_run:
            mode_info = " (SIMULATION)"
            
        logger.info("\n" + "="*60)
        logger.info(f"RÉSUMÉ DE LA MIGRATION{mode_info}")
        logger.info("="*60)
        logger.info(f"Contacts traités:          {len(self.processed_contacts)}")
        if self.contact_limit:
            logger.info(f"Contacts ignorés:          {self.stats['skipped_contacts']}")
        logger.info(f"Fichiers HTML migrés:      {self.stats['html_files']}")
        logger.info(f"Fichiers audio migrés:     {self.stats['audio_files']}")
        logger.info(f"Conversions migrées:       {self.stats['conversions']}")
        logger.info(f"Transcriptions migrées:    {self.stats['transcriptions']}")
        logger.info(f"Super fichiers migrés:     {self.stats['super_files']}")
        logger.info(f"Erreurs rencontrées:       {self.stats['errors']}")
        logger.info("="*60)
        
        # En mode de production, ajouter des informations supplémentaires
        if not self.dry_run:
            logger.info("\nMigration terminée avec succès !")
            logger.info(f"Nouveau registre unifié : {self.new_registry.registry_path}")
        else:
            logger.info("\nSimulation terminée - aucune modification n'a été apportée aux fichiers réels")
            logger.info("Consultez le rapport de compatibilité pour les détails.")


def main():
    """Point d'entrée du script de migration"""
    try:
        # Analyser les arguments de ligne de commande
        parser = argparse.ArgumentParser(description='Migration des données WhatsApp Extractor V2')
        parser.add_argument('--dry-run', action='store_true', help='Mode simulation sans modification des fichiers réels')
        parser.add_argument('--contact-limit', type=int, help='Limiter le nombre de contacts à traiter (pour tests)')
        args = parser.parse_args()
        
        # Créer l'instance avec les options
        migrator = Migrator(dry_run=args.dry_run, contact_limit=args.contact_limit)
        migrator.migrate_all(backup=not args.dry_run)  # Pas de backup en mode simulation
        
        return 0
    except Exception as e:
        logger.critical(f"Erreur fatale lors de la migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())