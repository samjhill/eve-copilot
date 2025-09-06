"""
System tray UI for EVE Copilot
"""

import threading
import logging
from typing import Optional, Dict, Any
import pystray
from PIL import Image, ImageDraw

from .config import Config

logger = logging.getLogger(__name__)


class UIError(Exception):
    """UI-related errors."""
    pass


class TrayUI:
    """System tray user interface for EVE Copilot."""
    
    def __init__(self, config: Config, log_watcher, rules_engine):
        """Initialize tray UI.
        
        Args:
            config: Application configuration
            log_watcher: Log file watcher
            rules_engine: Rules engine
        """
        self.config = config
        self.log_watcher = log_watcher
        self.rules_engine = rules_engine
        self.icon: Optional[pystray.Icon] = None
        self._running = False
        
        # Create system tray icon
        self._create_tray_icon()
        
        # Start background services
        self._start_services()
    
    def _create_tray_icon(self) -> None:
        """Create the system tray icon."""
        try:
            # Create a simple icon
            icon_image = self._create_icon_image()
            
            # Create tray menu
            menu = self._create_tray_menu()
            
            # Create the icon
            self.icon = pystray.Icon(
                "eve_copilot",
                icon_image,
                "EVE Copilot",
                menu
            )
            
            logger.info("System tray icon created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create system tray icon: {e}")
            raise UIError(f"Failed to create system tray icon: {e}")
    
    def _create_tray_menu(self) -> pystray.Menu:
        """Create the system tray menu.
        
        Returns:
            Configured tray menu
        """
        return pystray.Menu(
            pystray.MenuItem("Status", self._show_status),
            pystray.MenuItem("Settings", self._show_settings),
            pystray.MenuItem("Test Speech", self._test_speech),
            pystray.MenuItem("Reload Config", self._reload_config),
            pystray.MenuItem("Start Watching", self._start_watching),
            pystray.MenuItem("Stop Watching", self._stop_watching),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._exit_app)
        )
    
    def _create_icon_image(self, size: int = 64) -> Image.Image:
        """Create a simple icon image.
        
        Args:
            size: Icon size in pixels
            
        Returns:
            PIL Image object for the icon
        """
        # Create a simple blue circle with "EC" text
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw blue circle
        margin = 4
        draw.ellipse([margin, margin, size - margin, size - margin], 
                    fill=(0, 100, 200, 255), outline=(0, 80, 160, 255), width=2)
        
        # Draw "EC" text
        try:
            # Try to use a default font
            draw.text((size//4, size//4), "EC", fill=(255, 255, 255, 255))
        except Exception:
            # Fallback to simple text
            draw.text((size//4, size//4), "EC", fill=(255, 255, 255, 255))
        
        return image
    
    def _start_services(self) -> None:
        """Start background services."""
        try:
            # Start log watcher in a separate thread
            watcher_thread = threading.Thread(target=self._start_watcher_thread, daemon=True)
            watcher_thread.start()
            logger.info("Background services started")
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
    
    def _start_watcher_thread(self) -> None:
        """Start log watcher in background thread."""
        try:
            self.log_watcher.start()
        except Exception as e:
            logger.error(f"Failed to start log watcher: {e}")
    
    def run(self) -> None:
        """Run the system tray application."""
        if not self.icon:
            raise UIError("System tray icon not initialized")
        
        try:
            self._running = True
            logger.info("Starting system tray UI...")
            self.icon.run()
        except Exception as e:
            logger.error(f"Failed to run system tray: {e}")
            raise
        finally:
            self._running = False
    
    def _show_status(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Show application status."""
        try:
            # Get status from components
            watcher_status = self.log_watcher.get_status() if hasattr(self.log_watcher, 'get_status') else {}
            engine_status = self.rules_engine.get_status() if hasattr(self.rules_engine, 'get_status') else {}
            
            # Format status message
            status_msg = f"""
EVE Copilot Status

Log Watcher:
- Watching: {watcher_status.get('watching', 'Unknown')}
- Files monitored: {watcher_status.get('files_monitored', 0)}
- Events processed: {watcher_status.get('events_processed', 0)}

Rules Engine:
- Active profile: {engine_status.get('active_profile', 'Unknown')}
- Rules loaded: {engine_status.get('rules_count', 0)}
- Rules triggered: {engine_status.get('rules_triggered', 0)}
            """.strip()
            
            # For now, just log the status
            # In a real implementation, you might show a dialog or notification
            logger.info("Status requested by user")
            logger.info(status_msg)
            
        except Exception as e:
            logger.error(f"Failed to show status: {e}")
    
    def _show_settings(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Show settings dialog."""
        try:
            logger.info("Settings requested by user")
            # In a real implementation, this would open a settings dialog
            # For now, just log the request
        except Exception as e:
            logger.error(f"Failed to show settings: {e}")
    
    def _test_speech(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Test speech output."""
        try:
            logger.info("Speech test requested by user")
            # Test speech notification
            if hasattr(self.rules_engine, 'speech_notifier'):
                self.rules_engine.speech_notifier.speak("EVE Copilot speech test successful", priority=2)
            else:
                logger.warning("Speech notifier not available")
        except Exception as e:
            logger.error(f"Failed to test speech: {e}")
    
    def _reload_config(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Reload configuration."""
        try:
            logger.info("Configuration reload requested by user")
            
            # Reload main config
            self.config.reload()
            
            # Reload rules engine config
            if hasattr(self.rules_engine, 'reload_config'):
                self.rules_engine.reload_config()
            
            logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    def _start_watching(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Start log file watching."""
        try:
            logger.info("Start watching requested by user")
            if hasattr(self.log_watcher, 'start'):
                self.log_watcher.start()
            else:
                logger.warning("Log watcher start method not available")
        except Exception as e:
            logger.error(f"Failed to start watching: {e}")
    
    def _stop_watching(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Stop log file watching."""
        try:
            logger.info("Stop watching requested by user")
            if hasattr(self.log_watcher, 'stop'):
                self.log_watcher.stop()
            else:
                logger.warning("Log watcher stop method not available")
        except Exception as e:
            logger.error(f"Failed to stop watching: {e}")
    
    def _exit_app(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Exit the application."""
        try:
            logger.info("Exit requested by user")
            self.shutdown()
            icon.stop()
        except Exception as e:
            logger.error(f"Failed to exit application: {e}")
            # Force exit
            icon.stop()
    
    def shutdown(self) -> None:
        """Shutdown the UI and cleanup resources."""
        try:
            self._running = False
            
            # Stop log watcher
            if hasattr(self.log_watcher, 'stop'):
                self.log_watcher.stop()
            
            # Shutdown rules engine
            if hasattr(self.rules_engine, 'shutdown'):
                self.rules_engine.shutdown()
            
            # Shutdown speech notifier
            if hasattr(self.rules_engine, 'speech_notifier'):
                self.rules_engine.speech_notifier.shutdown()
            
            logger.info("UI shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during UI shutdown: {e}")
    
    def is_running(self) -> bool:
        """Check if the UI is running.
        
        Returns:
            True if UI is running
        """
        return self._running
    
    def get_status(self) -> Dict[str, Any]:
        """Get UI status information.
        
        Returns:
            Dictionary with UI status
        """
        return {
            'running': self._running,
            'icon_created': self.icon is not None,
            'services_started': hasattr(self, '_services_started')
        }
