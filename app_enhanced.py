#!/usr/bin/env python3
"""
Enhanced EVE Copilot Application - Phase 1 Improvements
Features: Web Dashboard, Enhanced Event Detection, Performance Optimization, Error Handling
"""

import argparse
import asyncio
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.parse import LogParser
from evetalk.notify import SpeechNotifier
from evetalk.async_watcher import AsyncLogWatcher
from evetalk.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory
from web_dashboard import WebDashboard, create_dashboard_templates

logger = logging.getLogger(__name__)


class EnhancedEveCopilot:
    """Enhanced EVE Copilot with Phase 1 improvements."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize enhanced EVE Copilot.
        
        Args:
            config_path: Path to configuration file
        """
        # Use default config path if none provided
        if config_path is None:
            config_path = "config/app.yml"
        self.config = Config(config_path)
        self.error_handler = ErrorHandler()
        
        # Core components
        self.parser: Optional[LogParser] = None
        self.speech_notifier: Optional[SpeechNotifier] = None
        self.rules_engine: Optional[RulesEngine] = None
        self.log_watcher: Optional[AsyncLogWatcher] = None
        self.web_dashboard: Optional[WebDashboard] = None
        
        # State
        self.running = False
        self.start_time = None
        self.event_callback_lock = threading.Lock()
        
        # Performance metrics
        self.events_processed = 0
        self.rules_triggered = 0
        self.alerts_sent = 0
    
    async def initialize(self):
        """Initialize all components."""
        try:
            logger.info("Initializing enhanced EVE Copilot...")
            
            # Initialize parser
            self.parser = LogParser(self.config.patterns_file)
            logger.info("Log parser initialized")
            
            # Initialize speech notifier
            self.speech_notifier = SpeechNotifier(self.config)
            logger.info("Speech notifier initialized")
            
            # Initialize rules engine
            self.rules_engine = RulesEngine(self.config, self.speech_notifier)
            logger.info("Rules engine initialized")
            
            # Initialize async log watcher
            self.log_watcher = AsyncLogWatcher(
                self.config, 
                self.parser, 
                self._event_callback
            )
            logger.info("Async log watcher initialized")
            
            # Create dashboard templates
            create_dashboard_templates()
            
            # Initialize web dashboard
            self.web_dashboard = WebDashboard(
                self.config,
                self.rules_engine,
                self.log_watcher
            )
            logger.info("Web dashboard initialized")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            self.error_handler.handle_error(
                e, 
                {'component': 'initialization'}, 
                ErrorSeverity.CRITICAL, 
                ErrorCategory.CONFIGURATION
            )
            raise
    
    def _event_callback(self, event):
        """Callback for processing events from log watcher."""
        try:
            with self.event_callback_lock:
                self.events_processed += 1
                
                # Process event through rules engine
                if self.rules_engine:
                    triggered = self.rules_engine.process_event(event)
                    if triggered:
                        self.rules_triggered += 1
                        self.alerts_sent += 1
                        
                        # Add alert to dashboard
                        if self.web_dashboard:
                            self.web_dashboard.add_alert(
                                event.type.value,
                                f"Event: {event.subject}",
                                event.priority
                            )
                
        except Exception as e:
            self.error_handler.handle_error(
                e,
                {'component': 'event_callback', 'event_type': event.type.value},
                ErrorSeverity.MEDIUM,
                ErrorCategory.PARSING
            )
    
    async def start(self):
        """Start the enhanced EVE Copilot."""
        try:
            if self.running:
                logger.warning("EVE Copilot already running")
                return
            
            logger.info("Starting enhanced EVE Copilot...")
            self.running = True
            self.start_time = time.time()
            
            # Start async log watcher
            if self.log_watcher:
                await self.log_watcher.start()
                logger.info("Async log watcher started")
            
            # Start web dashboard in separate thread
            if self.web_dashboard:
                dashboard_thread = threading.Thread(
                    target=self._run_dashboard,
                    daemon=True
                )
                dashboard_thread.start()
                logger.info("Web dashboard started")
            
            logger.info("Enhanced EVE Copilot started successfully")
            logger.info("Web dashboard available at: http://127.0.0.1:5000")
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                {'component': 'startup'},
                ErrorSeverity.CRITICAL,
                ErrorCategory.UNKNOWN
            )
            raise
    
    def _run_dashboard(self):
        """Run the web dashboard in a separate thread."""
        try:
            self.web_dashboard.run(host='127.0.0.1', port=5000, debug=False)
        except Exception as e:
            self.error_handler.handle_error(
                e,
                {'component': 'web_dashboard'},
                ErrorSeverity.HIGH,
                ErrorCategory.NETWORK
            )
    
    async def stop(self):
        """Stop the enhanced EVE Copilot."""
        try:
            if not self.running:
                return
            
            logger.info("Stopping enhanced EVE Copilot...")
            self.running = False
            
            # Stop log watcher
            if self.log_watcher:
                await self.log_watcher.stop()
                logger.info("Async log watcher stopped")
            
            # Stop web dashboard
            if self.web_dashboard:
                # The dashboard will stop when the main thread exits
                logger.info("Web dashboard stopping")
            
            logger.info("Enhanced EVE Copilot stopped")
            
        except Exception as e:
            self.error_handler.handle_error(
                e,
                {'component': 'shutdown'},
                ErrorSeverity.MEDIUM,
                ErrorCategory.UNKNOWN
            )
    
    def get_status(self) -> dict:
        """Get current application status."""
        status = {
            'running': self.running,
            'start_time': self.start_time,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'events_processed': self.events_processed,
            'rules_triggered': self.rules_triggered,
            'alerts_sent': self.alerts_sent,
            'error_stats': self.error_handler.get_error_stats()
        }
        
        # Add component status
        if self.log_watcher:
            status['log_watcher'] = self.log_watcher.get_status()
        
        if self.rules_engine:
            status['rules_engine'] = self.rules_engine.get_status()
        
        return status
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics."""
        metrics = {
            'events_processed': self.events_processed,
            'rules_triggered': self.rules_triggered,
            'alerts_sent': self.alerts_sent,
            'uptime': time.time() - self.start_time if self.start_time else 0
        }
        
        # Add component metrics
        if self.log_watcher:
            watcher_metrics = self.log_watcher.get_performance_metrics()
            metrics.update(watcher_metrics)
        
        return metrics


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Setup file handler
    file_handler = logging.FileHandler('eve_copilot_enhanced.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


async def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Enhanced EVE Copilot - Phase 1 Improvements',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app_enhanced.py                    # Run with default config
  python app_enhanced.py --debug           # Enable debug logging
  python app_enhanced.py --config my.yml   # Use custom config file
  python app_enhanced.py --web-only        # Run only web dashboard
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
        '--web-only',
        action='store_true',
        help='Run only the web dashboard (for testing)'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='Enhanced EVE Copilot v1.0.0'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Enhanced EVE Copilot...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {Path.cwd()}")
    
    try:
        # Create application instance
        app = EnhancedEveCopilot(args.config)
        
        if args.web_only:
            # Web-only mode for testing
            logger.info("Running in web-only mode")
            create_dashboard_templates()
            dashboard = WebDashboard(app.config, None, None)
            dashboard.run(host='127.0.0.1', port=5000, debug=args.debug)
        else:
            # Full application mode
            await app.initialize()
            await app.start()
            
            # Keep running until interrupted
            try:
                while app.running:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
            finally:
                await app.stop()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Enhanced EVE Copilot shutdown complete")


if __name__ == '__main__':
    asyncio.run(main())
