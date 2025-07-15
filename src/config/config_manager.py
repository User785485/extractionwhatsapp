"""Configuration manager with support for multiple sources"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import configparser
from copy import deepcopy

from .schemas import AppConfig, PathConfig, TranscriptionConfig, FilterConfig, ExportConfig, ProcessingConfig
from .defaults import DEFAULT_CONFIG, LEGACY_CONFIG_MAPPING


class ConfigManager:
    """Manages application configuration from multiple sources"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else None
        self._config_dict: Dict[str, Any] = {}
        self._config: Optional[AppConfig] = None
        
    def load(self) -> AppConfig:
        """Load configuration from all sources"""
        # Start with defaults
        self._config_dict = deepcopy(DEFAULT_CONFIG)
        
        # Load from file if specified
        if self.config_path and self.config_path.exists():
            file_config = self._load_from_file(self.config_path)
            self._merge_config(file_config)
        else:
            # Try to find config file
            for config_file in ['config.yaml', 'config.yml', 'config.json', 'config.ini']:
                if Path(config_file).exists():
                    file_config = self._load_from_file(Path(config_file))
                    self._merge_config(file_config)
                    break
        
        # Override with environment variables
        self._load_from_env()
        
        # Create and validate config object
        self._config = self._create_config_object()
        return self._config
    
    def _load_from_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file based on extension"""
        if path.suffix in ['.yaml', '.yml']:
            return self._load_yaml(path)
        elif path.suffix == '.json':
            return self._load_json(path)
        elif path.suffix == '.ini':
            return self._load_ini(path)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")
    
    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration"""
        try:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_ini(self, path: Path) -> Dict[str, Any]:
        """Load INI configuration with legacy support"""
        parser = configparser.ConfigParser(interpolation=None)
        parser.read(path, encoding='utf-8')
        
        config = {}
        for section in parser.sections():
            # Map legacy section names
            mapped_section = LEGACY_CONFIG_MAPPING.get(section, section).lower()
            
            if mapped_section not in config:
                config[mapped_section] = {}
            
            for key, value in parser.items(section):
                # Map legacy field names
                mapped_key = LEGACY_CONFIG_MAPPING.get(key, key).lower()
                
                # Try to parse value types
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif '.' in value and all(part.isdigit() for part in value.split('.', 1)):
                    value = float(value)
                
                config[mapped_section][mapped_key] = value
        
        return config
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Map of env var prefixes to config sections
        env_mapping = {
            'WE_PATH_': 'paths',
            'WE_TRANSCRIPTION_': 'transcription',
            'WE_FILTER_': 'filters',
            'WE_EXPORT_': 'export',
            'WE_PROCESSING_': 'processing'
        }
        
        for env_var, value in os.environ.items():
            for prefix, section in env_mapping.items():
                if env_var.startswith(prefix):
                    key = env_var[len(prefix):].lower()
                    
                    # Parse value types
                    if value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    elif '.' in value and all(part.isdigit() for part in value.split('.', 1)):
                        value = float(value)
                    
                    if section not in self._config_dict:
                        self._config_dict[section] = {}
                    self._config_dict[section][key] = value
        
        # Special handling for OPENAI_API_KEY
        if 'OPENAI_API_KEY' in os.environ:
            if 'transcription' not in self._config_dict:
                self._config_dict['transcription'] = {}
            self._config_dict['transcription']['api_key'] = os.environ['OPENAI_API_KEY']
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration into existing"""
        for key, value in new_config.items():
            if isinstance(value, dict) and key in self._config_dict:
                self._config_dict[key].update(value)
            else:
                self._config_dict[key] = value
    
    def _create_config_object(self) -> AppConfig:
        """Create validated config object from dictionary"""
        # Create sub-configs
        paths = PathConfig(**self._config_dict.get('paths', {}))
        transcription = TranscriptionConfig(**self._config_dict.get('transcription', {}))
        filters = FilterConfig(**self._config_dict.get('filters', {}))
        export = ExportConfig(**self._config_dict.get('export', {}))
        processing = ProcessingConfig(**self._config_dict.get('processing', {}))
        
        # Create main config
        return AppConfig(
            paths=paths,
            transcription=transcription,
            filters=filters,
            export=export,
            processing=processing
        )
    
    def save(self, path: Optional[Path] = None, format: str = 'yaml'):
        """Save current configuration to file"""
        save_path = path or self.config_path
        if not save_path:
            save_path = Path(f'config.{format}')
        
        config_dict = self.to_dict()
        
        if format in ['yaml', 'yml']:
            self._save_yaml(save_path, config_dict)
        elif format == 'json':
            self._save_json(save_path, config_dict)
        else:
            raise ValueError(f"Unsupported save format: {format}")
    
    def _save_yaml(self, path: Path, config: Dict[str, Any]):
        """Save configuration as YAML"""
        try:
            import yaml
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
        except ImportError:
            raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
    
    def _save_json(self, path: Path, config: Dict[str, Any]):
        """Save configuration as JSON"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config object to dictionary"""
        if not self._config:
            return self._config_dict
        
        return {
            'paths': {
                'whatsapp_export_path': str(self._config.paths.whatsapp_export_path),
                'media_output_dir': str(self._config.paths.media_output_dir),
                'export_output_dir': str(self._config.paths.export_output_dir),
                'transcription_cache_dir': str(self._config.paths.transcription_cache_dir),
                'database_path': str(self._config.paths.database_path)
            },
            'transcription': self._config.transcription.dict(exclude={'api_key'}),
            'filters': self._config.filters.dict(),
            'export': self._config.export.dict(),
            'processing': self._config.processing.dict()
        }
    
    @property
    def config(self) -> AppConfig:
        """Get current configuration"""
        if not self._config:
            self._config = self.load()
        return self._config
    
    def migrate_legacy_config(self, legacy_path: Path, output_path: Optional[Path] = None):
        """Migrate legacy INI config to new format"""
        legacy_config = self._load_ini(legacy_path)
        self._config_dict = deepcopy(DEFAULT_CONFIG)
        self._merge_config(legacy_config)
        
        # Save as YAML by default
        output_path = output_path or Path('config.yaml')
        self.save(output_path, format='yaml')
        
        print(f"[OK] Legacy config migrated to: {output_path}")
        return self._create_config_object()