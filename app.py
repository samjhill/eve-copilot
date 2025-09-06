#!/usr/bin/env python3
"""
EVE Copilot - Main application entry point
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from evetalk.config import Config, ConfigError
from evetalk.ui import TrayUI
from evetalk.watcher import LogWatcher
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier


def setup_logging(debug: bool = False, log_file: Optional[str] = None) -> None:
    """Configure logging based on debug flag and config.
    
    Args:
        debug: Enable debug logging
        log_file: Optional log file path
    """
    level = logging.DEBUG if debug else logging.INFO
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except Exception as e:
            logging.warning(f"Could not create log file {log_file}: {e}")
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )


def load_config(config_path: Optional[str] = None) -> Config:
    """Load and validate configuration.
    
    Args:
        config_path: Optional path to config file
        
    Returns:
        Validated configuration object
        
    Raises:
        ConfigError: If configuration is invalid
        SystemExit: If configuration cannot be loaded
    """
    try:
        config_file = config_path or 'config/app.yml'
        config = Config(config_file)
        
        if not config.is_valid():
            raise ConfigError("Configuration validation failed")
            
        return config
        
    except ConfigError as e:
        logging.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        sys.exit(1)


def initialize_components(config: Config):
    """Initialize application components.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple of (speech_notifier, rules_engine, log_watcher)
        
    Raises:
        Exception: If any component fails to initialize
    """
    try:
        # Initialize speech notifier
        speech_notifier = SpeechNotifier(config)
        logging.info("Speech notifier initialized")
        
        # Initialize rules engine
        rules_engine = RulesEngine(config, speech_notifier)
        logging.info("Rules engine initialized")
        
        # Initialize log watcher
        log_watcher = LogWatcher(config, rules_engine)
        logging.info("Log watcher initialized")
        
        return speech_notifier, rules_engine, log_watcher
        
    except Exception as e:
        logging.error(f"Failed to initialize components: {e}")
        raise


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='EVE Copilot - Log-driven voice assistant for EVE Online',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py                    # Run with default config
  python app.py --debug           # Enable debug logging
  python app.py --config my.yml   # Use custom config file
        """
    )
    parser.add_argument(
        '--debug', 
        action='store_true', 
        help='Enable debug logging'
    )
    parser.add_argument(
        '--config', 
        type=str, 
        help='Path to config file (default: config/app.yml)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='EVE Copilot v0.1.0'
    )
    
    args = parser.parse_args()

    # Setup logging first
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting EVE Copilot...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")

    try:
        # Load configuration
        config = load_config(args.config)
        logger.info(f"Configuration loaded from {config.config_path}")
        
        # Initialize components
        speech_notifier, rules_engine, log_watcher = initialize_components(config)
        
        # Start the UI (this will block until app is closed)
        tray_ui = TrayUI(config, log_watcher, rules_engine)
        logger.info("Starting system tray UI...")
        tray_ui.run()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("EVE Copilot shutdown complete")


if __name__ == '__main__':
    main()
