"""
Log file watcher for EVE Copilot - monitors EVE Online log files for changes
"""

import os
import time
import logging
import glob
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime, timedelta

from .config import Config
from .parse import LogParser
from .engine import RulesEngine

logger = logging.getLogger(__name__)


class WatcherError(Exception):
    """Watcher-related errors."""
    pass


class LogFileDetector:
    """Automatically detects the most recent and active EVE log files."""
    
    def __init__(self, config: Config):
        """Initialize log file detector.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.possible_log_dirs = self._get_possible_log_directories()
        self.current_active_file: Optional[Path] = None
        self.last_check_time = 0.0
        self.check_interval = 5.0  # Check every 5 seconds
        
    def _get_possible_log_directories(self) -> List[Path]:
        """Get all possible EVE log directories.
        
        Returns:
            List of possible log directory paths
        """
        directories = []
        
        # Primary configured directory
        primary_dir = Path(self.config.get_eve_logs_path())
        if primary_dir.exists():
            directories.append(primary_dir)
        
        # Common EVE log locations
        common_paths = [
            # macOS
            Path.home() / "Documents" / "EVE" / "logs" / "Gamelogs",
            Path.home() / "Documents" / "EVE" / "logs" / "CombatLogs",
            Path.home() / "Documents" / "EVE" / "logs" / "Chatlogs",
            # Windows
            Path.home() / "Documents" / "EVE" / "logs" / "Gamelogs",
            Path.home() / "Documents" / "EVE" / "logs" / "CombatLogs",
            Path.home() / "Documents" / "EVE" / "logs" / "Chatlogs",
            # Linux
            Path.home() / ".local" / "share" / "EVE" / "logs" / "Gamelogs",
            Path.home() / ".local" / "share" / "EVE" / "logs" / "CombatLogs",
        ]
        
        for path in common_paths:
            if path.exists() and path not in directories:
                directories.append(path)
        
        logger.info(f"Found {len(directories)} possible log directories: {[str(d) for d in directories]}")
        return directories
    
    def find_most_recent_log_file(self) -> Optional[Path]:
        """Find the most recent log file across all directories.
        
        Returns:
            Path to the most recent log file, or None if none found
        """
        most_recent_file = None
        most_recent_time = 0.0
        
        for log_dir in self.possible_log_dirs:
            try:
                # Look for .txt files in the directory
                pattern = str(log_dir / "*.txt")
                log_files = glob.glob(pattern)
                
                for file_path in log_files:
                    try:
                        file_stat = os.stat(file_path)
                        file_time = file_stat.st_mtime
                        
                        # Only consider files modified in the last 24 hours
                        if file_time > time.time() - 86400:
                            if file_time > most_recent_time:
                                most_recent_time = file_time
                                most_recent_file = Path(file_path)
                    except (OSError, IOError) as e:
                        logger.debug(f"Could not stat file {file_path}: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Error scanning directory {log_dir}: {e}")
                continue
        
        if most_recent_file:
            logger.info(f"Most recent log file: {most_recent_file} (modified: {datetime.fromtimestamp(most_recent_time)})")
        
        return most_recent_file
    
    def find_active_log_file(self) -> Optional[Path]:
        """Find the currently active log file (most recently modified).
        
        Returns:
            Path to the active log file, or None if none found
        """
        current_time = time.time()
        
        # Only check periodically to avoid excessive file system calls
        if current_time - self.last_check_time < self.check_interval:
            return self.current_active_file
        
        self.last_check_time = current_time
        
        # Find the most recent file
        recent_file = self.find_most_recent_log_file()
        
        if recent_file and recent_file != self.current_active_file:
            logger.info(f"Active log file changed: {self.current_active_file} -> {recent_file}")
            self.current_active_file = recent_file
        
        return self.current_active_file
    
    def get_all_log_files(self) -> List[Path]:
        """Get all log files from all directories.
        
        Returns:
            List of all log file paths
        """
        all_files = []
        
        for log_dir in self.possible_log_dirs:
            try:
                pattern = str(log_dir / "*.txt")
                log_files = glob.glob(pattern)
                all_files.extend([Path(f) for f in log_files])
            except Exception as e:
                logger.debug(f"Error scanning directory {log_dir}: {e}")
                continue
        
        # Sort by modification time (newest first)
        all_files.sort(key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True)
        
        return all_files
    
    def is_file_active(self, file_path: Path) -> bool:
        """Check if a file is currently active (being written to).
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file appears to be active
        """
        if not file_path.exists():
            return False
        
        try:
            # Check if file was modified in the last 30 seconds
            file_time = file_path.stat().st_mtime
            return time.time() - file_time < 30.0
        except (OSError, IOError):
            return False


class EVELogHandler(FileSystemEventHandler):
    """Handles file system events for EVE log files."""
    
    def __init__(self, parser: LogParser, rules_engine: RulesEngine, 
                 callback: Optional[Callable] = None, watcher: Optional['LogWatcher'] = None):
        """Initialize the log handler.
        
        Args:
            parser: Log parser instance
            rules_engine: Rules engine instance
            callback: Optional callback function for events
            watcher: Optional LogWatcher instance to update events counter
        """
        self.parser = parser
        self.rules_engine = rules_engine
        self.callback = callback
        self.watcher = watcher
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
            
            # Update watcher's events counter
            if self.watcher and events_processed > 0:
                self.watcher.events_processed += events_processed
                logger.debug(f"Processed {events_processed} events from {file_path} (total: {self.watcher.events_processed})")
            
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
        
        # Initialize log file detector
        self.log_detector = LogFileDetector(config)
        
        # Initialize parser
        self.parser = self._init_parser()
        
        # Initialize handler
        self.handler = EVELogHandler(self.parser, self.rules_engine, watcher=self)
        
        # Performance tracking
        self.events_processed = 0
        self.files_monitored = 0
        self.start_time = 0.0
        self.current_file: Optional[Path] = None
        self.last_file_check = 0.0
        self.file_check_interval = 10.0  # Check for new files every 10 seconds
    
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
        """Start watching log files with bulletproof detection."""
        if self.is_running:
            logger.warning("Log watcher is already running")
            return
        
        try:
            # Initialize observer
            self.observer = Observer()
            
            # Watch all possible log directories
            self._setup_directory_watching()
            
            # Start observer
            self.observer.start()
            self.is_running = True
            self.start_time = time.time()
            
            # Find and process the most recent log file
            self._find_and_process_active_file()
            
            logger.info(f"Started bulletproof log watcher - monitoring {len(self.watched_paths)} directories")
            
        except Exception as e:
            logger.error(f"Failed to start log watcher: {e}")
            self.is_running = False
            raise WatcherError(f"Failed to start log watcher: {e}")
    
    def _setup_directory_watching(self) -> None:
        """Set up watching for all possible log directories."""
        for log_dir in self.log_detector.possible_log_dirs:
            try:
                self.observer.schedule(self.handler, str(log_dir), recursive=False)
                self.watched_paths.append(log_dir)
                logger.info(f"Added watch directory: {log_dir}")
            except Exception as e:
                logger.warning(f"Failed to add watch directory {log_dir}: {e}")
    
    def _find_and_process_active_file(self) -> None:
        """Find and process the most recent active log file."""
        try:
            # Find the most recent log file
            recent_file = self.log_detector.find_most_recent_log_file()
            
            if recent_file:
                self.current_file = recent_file
                logger.info(f"Processing most recent log file: {recent_file}")
                
                # Process the entire file
                self._process_entire_file(recent_file)
            else:
                logger.warning("No recent log files found")
                
        except Exception as e:
            logger.error(f"Failed to find and process active file: {e}")
    
    def _process_entire_file(self, file_path: Path) -> None:
        """Process an entire log file.
        
        Args:
            file_path: Path to the log file
        """
        try:
            if not file_path.exists():
                logger.warning(f"Log file does not exist: {file_path}")
                return
            
            # Process the file through the handler
            self.handler._process_entire_file(str(file_path))
            
            # Update tracking
            self.files_monitored += 1
            logger.info(f"Processed entire file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to process entire file {file_path}: {e}")
    
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
    
    def check_for_new_active_file(self) -> None:
        """Periodically check for new active log files."""
        if not self.is_running:
            return
        
        current_time = time.time()
        if current_time - self.last_file_check < self.file_check_interval:
            return
        
        self.last_file_check = current_time
        
        try:
            # Check for new active file
            active_file = self.log_detector.find_active_log_file()
            
            if active_file and active_file != self.current_file:
                logger.info(f"New active log file detected: {active_file}")
                self.current_file = active_file
                self._process_entire_file(active_file)
                
        except Exception as e:
            logger.error(f"Error checking for new active file: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get watcher status information.
        
        Returns:
            Dictionary with watcher status
        """
        uptime = time.time() - self.start_time if self.start_time > 0 else 0
        
        # Check for new active files
        self.check_for_new_active_file()
        
        return {
            'running': self.is_running,
            'watching': 'Active' if self.is_running else 'Stopped',
            'current_file': str(self.current_file) if self.current_file else 'None',
            'files_monitored': self.files_monitored,
            'events_processed': self.events_processed,
            'uptime_seconds': int(uptime),
            'watched_paths': [str(p) for p in self.watched_paths],
            'possible_directories': [str(p) for p in self.log_detector.possible_log_dirs]
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
    
    def force_detect_active_file(self) -> Optional[Path]:
        """Force detection of the current active log file.
        
        Returns:
            Path to the active log file, or None if none found
        """
        try:
            logger.info("Forcing detection of active log file...")
            
            # Reset the check time to force immediate detection
            self.last_file_check = 0.0
            
            # Find the most recent file
            active_file = self.log_detector.find_most_recent_log_file()
            
            if active_file:
                logger.info(f"Detected active log file: {active_file}")
                
                # Process the file if it's different from current
                if active_file != self.current_file:
                    self.current_file = active_file
                    self._process_entire_file(active_file)
                
                return active_file
            else:
                logger.warning("No active log file found")
                return None
                
        except Exception as e:
            logger.error(f"Failed to force detect active file: {e}")
            return None
    
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

