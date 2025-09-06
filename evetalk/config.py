"""
Configuration management for EVE Copilot
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


class Config:
    """Configuration manager for EVE Copilot."""
    
    def __init__(self, config_path: Union[str, Path]):
        """Initialize configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Raises:
            ConfigError: If configuration is invalid or cannot be loaded
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigError: If file cannot be loaded
        """
        if not self.config_path.exists():
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config file: {e}")
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise ConfigError(f"Failed to load config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'eve_logs_path': self._get_default_eve_logs_path(),
            'speech': {
                'enabled': True,
                'tts_engine': 'edge-tts',
                'voice_rate': 150,
                'voice_volume': 0.8,
                'priority_chime': True,
                'edge_voice': 'en-US-AriaNeural',
                'edge_rate': '+0%',
                'edge_volume': '+0%',
                'gtts_language': 'en',
                'gtts_slow': False
            },
            'profiles': {
                'default': 'general',
                'available': ['general', 'abyssal']
            },
            'logging': {
                'level': 'INFO',
                'file': 'eve_copilot.log'
            },
            'performance': {
                'file_watch_interval': 0.1,
                'max_events_per_second': 100
            }
        }
    
    def _get_default_eve_logs_path(self) -> str:
        """Get default EVE logs path based on OS.
        
        Returns:
            Default logs path for the current OS
        """
        if os.name == 'nt':  # Windows
            return os.path.expanduser(r'%USERPROFILE%\Documents\EVE\logs\Chatlogs')
        else:  # macOS/Linux
            return os.path.expanduser('~/Documents/EVE/logs/Chatlogs')
    
    def _validate_config(self) -> None:
        """Validate configuration values.
        
        Raises:
            ConfigError: If configuration is invalid
        """
        required_keys = ['eve_logs_path', 'speech', 'profiles']
        for key in required_keys:
            if key not in self.config:
                raise ConfigError(f"Missing required config key: {key}")
        
        # Validate EVE logs path
        logs_path = Path(self.config['eve_logs_path'])
        if not logs_path.exists():
            logger.warning(f"EVE logs path does not exist: {logs_path}")
        
        # Validate speech configuration
        speech_config = self.config.get('speech', {})
        if speech_config.get('enabled', True):
            tts_engine = speech_config.get('tts_engine', 'edge-tts')
            if tts_engine not in ['edge-tts', 'gtts', 'pyttsx3']:
                logger.warning(f"Unknown TTS engine: {tts_engine}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key using dot notation.
        
        Args:
            key: Configuration key (supports dot notation like 'speech.enabled')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_eve_logs_path(self) -> Path:
        """Get EVE logs directory path.
        
        Returns:
            Path to EVE logs directory
        """
        return Path(self.config['eve_logs_path'])
    
    def get_speech_config(self) -> Dict[str, Any]:
        """Get speech configuration.
        
        Returns:
            Speech configuration dictionary
        """
        return self.config.get('speech', {})
    
    def get_profiles_config(self) -> Dict[str, Any]:
        """Get profiles configuration.
        
        Returns:
            Profiles configuration dictionary
        """
        return self.config.get('profiles', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        return self.config.get('logging', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration.
        
        Returns:
            Performance configuration dictionary
        """
        return self.config.get('performance', {})
    
    def reload(self) -> None:
        """Reload configuration from file.
        
        Raises:
            ConfigError: If configuration cannot be reloaded
        """
        logger.info("Reloading configuration...")
        self.config = self._load_config()
        self._validate_config()
    
    def is_valid(self) -> bool:
        """Check if configuration is valid.
        
        Returns:
            True if configuration is valid
        """
        try:
            self._validate_config()
            return True
        except ConfigError:
            return False
