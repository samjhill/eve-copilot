"""
Log file watcher for EVE Copilot - monitors EVE Online log files for changes
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import Config
from .parse import LogParser
from .engine import RulesEngine

logger = logging.getLogger(__name__)


class WatcherError(Exception):
    """Watcher-related errors."""
    pass


class EVELogHandler(FileSystemEventHandler):
    """Handles file system events for EVE log files."""
    
    def __init__(self, parser: LogParser, rules_engine: RulesEngine, 
                 callback: Optional[Callable] = None):
        """Initialize the log handler.
        
        Args:
            parser: Log parser instance
            rules_engine: Rules engine instance
            callback: Optional callback function for events
        """
        self.parser = parser
        self.rules_engine = rules_engine
        self.callback = callback
        self.last_processed_positions: Dict[str, int] = {}
        self.processed_files: set[str] = set()
        
    def on_modified(self, event) -> None:
        """Handle file modification events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
            
        if not event.src_path.endswith('.txt'):
            return
            
        try:
            self._process_file_changes(event.src_path)
        except Exception as e:
            logger.error(f"Error processing file changes in {event.src_path}: {e}")
    
    def _process_file_changes(self, file_path: str) -> None:
        """Process changes in a log file.
        
        Args:
            file_path: Path to the log file
        """
        try:
            current_size = os.path.getsize(file_path)
            last_position = self.last_processed_positions.get(file_path, 0)
            
            if current_size < last_position:
                # File was truncated, reset position
                last_position = 0
                logger.debug(f"File {file_path} was truncated, resetting position")
                
            if current_size == last_position:
                # No new content
                return
                
            # Read new content
            new_lines = self._read_new_lines(file_path, last_position)
            if not new_lines:
                return
                
            # Process new lines
            events_processed = self._process_lines(new_lines, file_path)
            
            # Update position
            self.last_processed_positions[file_path] = current_size
            
            if events_processed > 0:
                logger.debug(f"Processed {events_processed} events from {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def _read_new_lines(self, file_path: str, last_position: int) -> List[str]:
        """Read new lines from a file.
        
        Args:
            file_path: Path to the file
            last_position: Last processed position
            
        Returns:
            List of new lines
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_position)
                new_lines = f.readlines()
                return [line.strip() for line in new_lines if line.strip()]
        except Exception as e:
            logger.error(f"Failed to read new lines from {file_path}: {e}")
            return []
    
    def _process_lines(self, lines: List[str], file_path: str) -> int:
        """Process a list of log lines.
        
        Args:
            lines: List of log lines to process
            file_path: Source file path
            
        Returns:
            Number of events processed
        """
        events_processed = 0
        
        for line in lines:
            try:
                event = self.parser.parse_line(line, file_path)
                if event:
                    logger.debug(f"Parsed event: {event.type.value} from {file_path}")
                    self.rules_engine.process_event(event)
                    events_processed += 1
                    
                    if self.callback:
                        self.callback(event)
                        
            except Exception as e:
                logger.error(f"Error processing line '{line[:50]}...': {e}")
                continue
        
        return events_processed
    
    def on_created(self, event) -> None:
        """Handle file creation events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
            
        if event.src_path.endswith('.txt'):
            logger.info(f"New log file detected: {event.src_path}")
            # Process the entire new file
            self._process_entire_file(event.src_path)
    
    def _process_entire_file(self, file_path: str) -> None:
        """Process an entire log file (for new files).
        
        Args:
            file_path: Path to the new log file
        """
        try:
            # Mark file as processed
            self.processed_files.add(file_path)
            
            # Read and process all lines
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            events_processed = self._process_lines(lines, file_path)
            
            # Update position to end of file
            self.last_processed_positions[file_path] = os.path.getsize(file_path)
            
            logger.info(f"Processed {events_processed} events from new file {file_path}")
            
        except Exception as e:
            logger.error(f"Error processing entire file {file_path}: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get handler status information.
        
        Returns:
            Dictionary with handler status
        """
        return {
            'files_processed': len(self.processed_files),
            'files_monitored': len(self.last_processed_positions),
            'last_positions': self.last_processed_positions.copy()
        }


class LogWatcher:
    """Watches EVE log directories for changes and processes new log entries."""
    
    def __init__(self, config: Config, rules_engine: RulesEngine):
        """Initialize log watcher.
        
        Args:
            config: Application configuration
            rules_engine: Rules engine instance
        """
        self.config = config
        self.rules_engine = rules_engine
        self.observer: Optional[Observer] = None
        self.handler: Optional[EVELogHandler] = None
        self.watched_paths: List[Path] = []
        self.is_running = False
        
        # Initialize parser
        self.parser = self._init_parser()
        
        # Initialize handler
        self.handler = EVELogHandler(self.parser, self.rules_engine)
        
        # Performance tracking
        self.events_processed = 0
        self.files_monitored = 0
        self.start_time = 0.0
    
    def _init_parser(self) -> LogParser:
        """Initialize log parser.
        
        Returns:
            Initialized LogParser instance
            
        Raises:
            WatcherError: If parser cannot be initialized
        """
        try:
            patterns_file = Path("config/patterns/core.yml")
            if not patterns_file.exists():
                raise WatcherError(f"Patterns file not found: {patterns_file}")
            
            parser = LogParser(patterns_file)
            logger.info("Log parser initialized successfully")
            return parser
            
        except Exception as e:
            logger.error(f"Failed to initialize log parser: {e}")
            raise WatcherError(f"Failed to initialize log parser: {e}")
    
    def start(self) -> None:
        """Start watching log files."""
        if self.is_running:
            logger.warning("Log watcher is already running")
            return
        
        try:
            # Get EVE logs path
            eve_logs_path = self.config.get_eve_logs_path()
            if not eve_logs_path.exists():
                logger.warning(f"EVE logs path does not exist: {eve_logs_path}")
                return
            
            # Initialize observer
            self.observer = Observer()
            
            # Add watch for EVE logs directory
            self.observer.schedule(self.handler, str(eve_logs_path), recursive=False)
            self.watched_paths.append(eve_logs_path)
            
            # Start observer
            self.observer.start()
            self.is_running = True
            self.start_time = time.time()
            
            # Process existing files
            self._process_existing_files(eve_logs_path)
            
            logger.info(f"Started watching EVE logs directory: {eve_logs_path}")
            
        except Exception as e:
            logger.error(f"Failed to start log watcher: {e}")
            self.is_running = False
            raise WatcherError(f"Failed to start log watcher: {e}")
    
    def _process_existing_files(self, logs_path: Path) -> None:
        """Process existing log files in the directory.
        
        Args:
            logs_path: Path to logs directory
        """
        try:
            log_files = list(logs_path.glob("*.txt"))
            self.files_monitored = len(log_files)
            
            for log_file in log_files:
                try:
                    self.handler._process_entire_file(str(log_file))
                except Exception as e:
                    logger.error(f"Failed to process existing file {log_file}: {e}")
            
            logger.info(f"Processed {len(log_files)} existing log files")
            
        except Exception as e:
            logger.error(f"Failed to process existing files: {e}")
    
    def stop(self) -> None:
        """Stop watching log files."""
        if not self.is_running:
            logger.warning("Log watcher is not running")
            return
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.is_running = False
            logger.info("Log watcher stopped")
            
        except Exception as e:
            logger.error(f"Error stopping log watcher: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get watcher status information.
        
        Returns:
            Dictionary with watcher status
        """
        uptime = time.time() - self.start_time if self.start_time > 0 else 0
        
        return {
            'running': self.is_running,
            'watching': 'Active' if self.is_running else 'Stopped',
            'files_monitored': self.files_monitored,
            'events_processed': self.events_processed,
            'uptime_seconds': int(uptime),
            'watched_paths': [str(p) for p in self.watched_paths]
        }
    
    def get_watched_paths(self) -> List[Path]:
        """Get list of watched paths.
        
        Returns:
            List of watched paths
        """
        return self.watched_paths.copy()
    
    def add_watch_path(self, path: Path) -> bool:
        """Add a new path to watch.
        
        Args:
            path: Path to add to watch list
            
        Returns:
            True if path was added successfully
        """
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return False
        
        try:
            if self.observer and self.is_running:
                self.observer.schedule(self.handler, str(path), recursive=False)
                self.watched_paths.append(path)
                logger.info(f"Added watch path: {path}")
                return True
            else:
                logger.warning("Cannot add watch path - observer not running")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add watch path {path}: {e}")
            return False
    
    def remove_watch_path(self, path: Path) -> bool:
        """Remove a path from watch list.
        
        Args:
            path: Path to remove from watch list
            
        Returns:
            True if path was removed successfully
        """
        try:
            if path in self.watched_paths:
                self.watched_paths.remove(path)
                logger.info(f"Removed watch path: {path}")
                return True
            else:
                logger.warning(f"Path not in watch list: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove watch path {path}: {e}")
            return False
    
    def reload_config(self) -> None:
        """Reload configuration and restart if necessary."""
        try:
            if self.is_running:
                logger.info("Reloading log watcher configuration...")
                self.stop()
                time.sleep(0.5)  # Brief pause
                self.start()
            else:
                logger.info("Log watcher not running, configuration will be loaded on start")
                
        except Exception as e:
            logger.error(f"Failed to reload log watcher configuration: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the log watcher."""
        try:
            self.stop()
            logger.info("Log watcher shutdown complete")
        except Exception as e:
            logger.error(f"Error during log watcher shutdown: {e}")

