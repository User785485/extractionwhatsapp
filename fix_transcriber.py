#!/usr/bin/env python
import os
import re

def fix_transcriber(file_path):
    """
    Modifie le transcriber.py pour utiliser les fichiers MP3 convertis
    au lieu des "super fichiers" qui n'existent pas
    """
    print(f"Modification du fichier: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Renommer la méthode existante pour la préserver
    content = content.replace(
        "def transcribe_all_super_files(self)",
        "def transcribe_all_super_files_original(self)"
    )
    
    # 2. Ajouter la nouvelle méthode qui utilise les fichiers MP3 convertis
    new_method = """
    def transcribe_all_super_files(self) -> Dict[str, int]:
        \"\"\"
        Transcrit tous les fichiers MP3 convertis dans le dossier audio_mp3
        Version corrigée qui n'utilise pas les super fichiers inexistants
        
        Returns:
            Statistiques par contact
        \"\"\"
        if not self.client:
            logger.warning("Client OpenAI non disponible, transcription ignorée")
            return {}
        
        stats = {}
        
        # Parcourir tous les contacts
        for contact in os.listdir(self.file_manager.output_dir):
            contact_path = os.path.join(self.file_manager.output_dir, contact)
            if not os.path.isdir(contact_path) or contact.startswith('.'):
                continue
            
            logger.info(f"Transcription pour {contact}")
            
            # Récupérer les fichiers MP3 convertis (au lieu des super fichiers)
            mp3_files = self.file_manager.get_mp3_files(contact)
            logger.info(f"DIAGNOSTIC: Recherche de fichiers MP3 pour contact {contact}")
            logger.info(f"DIAGNOSTIC: Trouvé {len(mp3_files)} fichiers MP3")
            for mp3_path in mp3_files:
                logger.info(f"DIAGNOSTIC: Fichier MP3 trouvé: {os.path.basename(mp3_path)}")
            transcribed = 0
            
            for mp3_file_path in mp3_files:
                file_name = os.path.basename(mp3_file_path)
                # Déterminer la direction à partir du nom du fichier
                is_received = True  # Par défaut, considérer comme reçu
                
                # Vérifier la direction
                if not self.transcribe_received and is_received:
                    logger.info(f"Transcription ignorée (reçu): {file_name}")
                    continue
                if not self.transcribe_sent and not is_received:
                    logger.info(f"Transcription ignorée (envoyé): {file_name}")
                    continue
                
                # Extrait la période à partir du nom ou utilise le mois courant
                period = self.file_manager.extract_period_from_filename(mp3_file_path)
                
                # Vérifier si déjà transcrit
                file_hash = self.registry.get_file_hash(mp3_file_path)
                if self.registry.get_transcription(file_hash):
                    logger.info(f"Déjà transcrit: {file_name}")
                    transcribed += 1
                    continue
                
                # Transcrire
                transcription = self._transcribe_file(mp3_file_path)
                if transcription:
                    # Enregistrer dans le registre
                    self.registry.register_transcription(file_hash, transcription)
                    
                    # Sauvegarder aussi dans un fichier
                    self._save_transcription_file(contact, period, transcription, mp3_file_path)
                    
                    transcribed += 1
            
            stats[contact] = transcribed
        
        # Sauvegarder le registre
        self.registry.save()
        
        # Créer les fichiers consolidés
        self._create_consolidated_transcriptions()
        
        # Logs diagnostiques pour trouver tous les MP3
        logger.info("DIAGNOSTIC: Exploration du répertoire de sortie pour trouver tous les MP3")
        mp3_count = 0
        for root, dirs, files in os.walk(self.file_manager.output_dir):
            for file in files:
                if file.endswith('.mp3'):
                    mp3_count += 1
                    logger.info(f"DIAGNOSTIC: MP3 existant: {os.path.join(root, file)}")
        logger.info(f"DIAGNOSTIC: Total des fichiers MP3 trouvés: {mp3_count}")
        
        return stats
    """
    
    # Insérer la nouvelle méthode après la méthode renommée
    pattern = r"def transcribe_all_super_files_original\(self\).*?return stats"
    replacement = re.sub(pattern, lambda m: m.group(0) + new_method, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(replacement)
    
    print("Transcriber.py modifié avec succès.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    transcriber_path = os.path.join(base_dir, 'processors', 'transcriber.py')
    
    if os.path.exists(transcriber_path):
        fix_transcriber(transcriber_path)
    else:
        print(f"Fichier transcriber.py non trouvé à l'emplacement: {transcriber_path}")
