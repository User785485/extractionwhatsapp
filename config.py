import os
import configparser
import json
from pathlib import Path

class Config:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        # Desactiver l'interpolation pour eviter les problemes avec les formats de date
        self.config = configparser.ConfigParser(interpolation=None)
        
        # Configuration par defaut avec les chemins specifiques
        self.config['Paths'] = {
            'html_dir': r'C:\Users\Moham\Downloads\iPhone_20250604173341\WhatsApp',
            'media_dir': r'C:\ProgramData\Wondershare\MobileTrans\ExportMedia\20250605021808',
            'output_dir': r'C:\Users\Moham\Desktop\DataLeads',
            'logs_dir': 'logs'
        }
        
        self.config['API'] = {
            'openai_key': '',
            'max_retries': '3',
            'retry_delay': '5',
            'file_size_limit': '25000000'  # 25 Mo
        }
        
        self.config['Conversion'] = {
            'mp3_quality': '2',
            'chunk_size': '25000000',  # 25 Mo
            'parallel_conversions': '4',
            'skip_ffmpeg_check': 'False'
        }
        
        self.config['Transcription'] = {
            'parallel_transcriptions': '2',
            'chunk_duration': '600'  # 10 minutes
        }
        
        # La configuration est deja initialisee avec interpolation=None
        # Ne pas reinitialiser le ConfigParser ici pour conserver les valeurs par defaut
        
        self.config['Processing'] = {
            'mode': 'both',  # CHANGE: both au lieu de received_only
            'transcribe_received': 'True',
            'transcribe_sent': 'False',  # CHANGE: True au lieu de False
            'create_superfiles': 'True',
            'max_transcriptions': '100',
            'date_format': '%Y/%m/%d'
        }
        
        self.config['User'] = {
            'last_mode': 'incremental'
        }
        
        # Charger la configuration existante
        self.load()
    
    def load(self):
        """Charge la configuration depuis le fichier"""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding='utf-8')
                # Expansion des variables d'environnement
                for section in self.config.sections():
                    for key, value in self.config[section].items():
                        if '%USERPROFILE%' in value:
                            self.config[section][key] = value.replace('%USERPROFILE%', os.path.expanduser('~'))
                        if '%USERNAME%' in value:
                            self.config[section][key] = value.replace('%USERNAME%', os.getenv('USERNAME', 'User'))
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {str(e)}")
    
    def save(self):
        """Sauvegarde la configuration dans le fichier"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {str(e)}")
    
    def get(self, section, option, fallback=None):
        """Recupere une valeur de configuration"""
        return self.config.get(section, option, fallback=fallback)
    
    def getint(self, section, option, fallback=None):
        """Recupere une valeur entiere de configuration"""
        return self.config.getint(section, option, fallback=fallback)
    
    def getfloat(self, section, option, fallback=None):
        """Recupere une valeur flottante de configuration"""
        return self.config.getfloat(section, option, fallback=fallback)
    
    def getboolean(self, section, option, fallback=None):
        """Recupere une valeur booleenne de configuration"""
        return self.config.getboolean(section, option, fallback=fallback)
    
    def set(self, section, option, value):
        """Definit une valeur de configuration"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config[section][option] = str(value)
    
    def save_user_preference(self, key, value):
        """Sauvegarde une preference utilisateur"""
        self.set('User', key, value)
        self.save()
    
    def get_paths(self):
        """Recupere tous les chemins configures"""
        return {
            'html_dir': self.get('Paths', 'html_dir'),
            'media_dir': self.get('Paths', 'media_dir'),
            'output_dir': self.get('Paths', 'output_dir'),
            'logs_dir': self.get('Paths', 'logs_dir')
        }
    
    def validate_paths(self):
        """Valide que les chemins existent"""
        paths = self.get_paths()
        issues = []
        
        # Verifier que les repertoires sources existent
        if not os.path.exists(paths['html_dir']):
            issues.append(f"Repertoire HTML introuvable: {paths['html_dir']}")
        
        if not os.path.exists(paths['media_dir']):
            issues.append(f"Repertoire media introuvable: {paths['media_dir']}")
        
        # Creer les repertoires de sortie s'ils n'existent pas
        for key in ['output_dir', 'logs_dir']:
            if not os.path.exists(paths[key]):
                try:
                    os.makedirs(paths[key], exist_ok=True)
                except Exception as e:
                    issues.append(f"Impossible de creer {key}: {paths[key]} - {str(e)}")
        
        return issues
    
    def get_processing_mode(self):
        """Retourne le mode de traitement actuel"""
        return self.get('Processing', 'mode', fallback='both')  # CHANGE: both par defaut
    
    def should_transcribe_received(self):
        """Determine si on doit transcrire les messages recus"""
        return self.getboolean('Processing', 'transcribe_received', fallback=True)
    
    def should_transcribe_sent(self):
        """Determine si on doit transcrire les messages envoyes"""
        return self.getboolean('Processing', 'transcribe_sent', fallback=True)  # CHANGE: True par defaut