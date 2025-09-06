"""
Async log file watcher for EVE Copilot - high-performance log monitoring
"""

import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Set
import aiofiles
import psutil

from .events import GameEvent
from .parse import LogParser

logger = logging.getLogger(__name__)


class AsyncLogWatcher:
    """High-performance async log file watcher."""
    
    def __init__(self, config, parser: LogParser, event_callback: Callable[[GameEvent], None]):
        """Initialize async log watcher.
        
        Args:
            config: Application configuration
            parser: Log parser instance
            event_callback: Callback function for new events
        """
        self.config = config
        self.parser = parser
        self.event_callback = event_callback
        
        # State
        self.running = False
        self.watched_files: Dict[str, int] = {}  # file_path -> last_position
        self.file_handles: Dict[str, Any] = {}  # file_path -> file_handle
        self.last_activity = None
        
        # Performance metrics
        self.events_processed = 0
        self.files_monitored = 0
        self.start_time = None
        self.last_file_check = 0
        
        # Event batching
        self.event_batch: List[GameEvent] = []
        self.batch_size = 10
        self.batch_timeout = 0.1  # 100ms
        
        # Performance limits
        self.max_events_per_second = config.performance.get('max_events_per_second', 100)
        self.file_check_interval = config.performance.get('file_watch_interval', 0.1)
        
        # Background tasks
        self.tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the async log watcher."""
        if self.running:
            logger.warning("Async watcher already running")
            return
        
        try:
            self.running = True
            self.start_time = time.time()
            self.last_activity = datetime.now()
            
            logger.info("Starting async log watcher...")
            
            # Start background tasks
            self.tasks.add(asyncio.create_task(self._file_monitor_loop()))
            self.tasks.add(asyncio.create_task(self._event_batch_processor()))
            self.tasks.add(asyncio.create_task(self._performance_monitor()))
            
            logger.info("Async log watcher started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start async watcher: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the async log watcher."""
        if not self.running:
            return
        
        try:
            logger.info("Stopping async log watcher...")
            self.running = False
            
            # Signal shutdown
            self._shutdown_event.set()
            
            # Cancel all tasks
            for task in self.tasks:
                task.cancel()
            
            # Wait for tasks to complete
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Close file handles
            for file_handle in self.file_handles.values():
                if hasattr(file_handle, 'close'):
                    await file_handle.close()
            
            self.file_handles.clear()
            self.watched_files.clear()
            self.tasks.clear()
            
            logger.info("Async log watcher stopped")
            
        except Exception as e:
            logger.error(f"Error stopping async watcher: {e}")
    
    async def _file_monitor_loop(self):
        """Main file monitoring loop."""
        while self.running:
            try:
                await self._check_for_new_files()
                await self._process_existing_files()
                await asyncio.sleep(self.file_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in file monitor loop: {e}")
                await asyncio.sleep(1)
    
    async def _check_for_new_files(self):
        """Check for new log files to monitor."""
        try:
            logs_path = Path(self.config.eve_logs_path)
            if not logs_path.exists():
                return
            
            # Find all .txt files
            log_files = list(logs_path.glob("*.txt"))
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Monitor the most recent file
            if log_files:
                newest_file = str(log_files[0])
                if newest_file not in self.watched_files:
                    await self._add_file_to_watch(newest_file)
            
            # Remove old files from monitoring
            current_files = {str(f) for f in log_files}
            files_to_remove = set(self.watched_files.keys()) - current_files
            
            for file_path in files_to_remove:
                await self._remove_file_from_watch(file_path)
                
        except Exception as e:
            logger.error(f"Error checking for new files: {e}")
    
    async def _add_file_to_watch(self, file_path: str):
        """Add a file to watch list."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return
            
            # Get file size for initial position
            file_size = file_path_obj.stat().st_size
            
            # Start from the end of the file (only new content)
            self.watched_files[file_path] = file_size
            self.files_monitored += 1
            
            logger.info(f"Added file to watch: {file_path} (size: {file_size})")
            
        except Exception as e:
            logger.error(f"Error adding file to watch {file_path}: {e}")
    
    async def _remove_file_from_watch(self, file_path: str):
        """Remove a file from watch list."""
        try:
            if file_path in self.watched_files:
                del self.watched_files[file_path]
                self.files_monitored -= 1
                
                # Close file handle if open
                if file_path in self.file_handles:
                    file_handle = self.file_handles[file_path]
                    if hasattr(file_handle, 'close'):
                        await file_handle.close()
                    del self.file_handles[file_path]
                
                logger.info(f"Removed file from watch: {file_path}")
                
        except Exception as e:
            logger.error(f"Error removing file from watch {file_path}: {e}")
    
    async def _process_existing_files(self):
        """Process all watched files for new content."""
        for file_path in list(self.watched_files.keys()):
            try:
                await self._process_file(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
    
    async def _process_file(self, file_path: str):
        """Process a single file for new content."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                await self._remove_file_from_watch(file_path)
                return
            
            current_size = file_path_obj.stat().st_size
            last_position = self.watched_files[file_path]
            
            # No new content
            if current_size <= last_position:
                return
            
            # Read new content
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                await f.seek(last_position)
                new_content = await f.read()
            
            if not new_content.strip():
                self.watched_files[file_path] = current_size
                return
            
            # Process new lines
            lines = new_content.splitlines()
            for line in lines:
                if line.strip():
                    await self._process_line(line, file_path)
            
            # Update position
            self.watched_files[file_path] = current_size
            self.last_activity = datetime.now()
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    async def _process_line(self, line: str, source_file: str):
        """Process a single log line."""
        try:
            # Parse the line
            event = self.parser.parse_line(line, source_file)
            if event:
                # Add to batch instead of processing immediately
                self.event_batch.append(event)
                self.events_processed += 1
                
                # Process batch if it's full
                if len(self.event_batch) >= self.batch_size:
                    await self._process_event_batch()
                    
        except Exception as e:
            logger.error(f"Error processing line: {e}")
    
    async def _event_batch_processor(self):
        """Process event batches periodically."""
        while self.running:
            try:
                await asyncio.sleep(self.batch_timeout)
                
                if self.event_batch:
                    await self._process_event_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
    
    async def _process_event_batch(self):
        """Process the current event batch."""
        if not self.event_batch:
            return
        
        try:
            # Process events in batch
            for event in self.event_batch:
                try:
                    self.event_callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback: {e}")
            
            # Clear batch
            self.event_batch.clear()
            
        except Exception as e:
            logger.error(f"Error processing event batch: {e}")
    
    async def _performance_monitor(self):
        """Monitor performance and apply throttling."""
        while self.running:
            try:
                await asyncio.sleep(1)  # Check every second
                
                # Calculate events per second
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    if elapsed > 0:
                        events_per_second = self.events_processed / elapsed
                        
                        # Throttle if too many events
                        if events_per_second > self.max_events_per_second:
                            logger.warning(f"High event rate: {events_per_second:.1f} events/sec, throttling...")
                            await asyncio.sleep(0.1)  # Brief pause
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitor: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status."""
        return {
            'running': self.running,
            'files_monitored': self.files_monitored,
            'events_processed': self.events_processed,
            'watching': self.running and len(self.watched_files) > 0,
            'current_file': max(self.watched_files.keys(), key=lambda f: self.watched_files[f]) if self.watched_files else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'uptime': time.time() - self.start_time if self.start_time else 0,
            'batch_size': len(self.event_batch)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        if not self.start_time:
            return {}
        
        elapsed = time.time() - self.start_time
        events_per_second = self.events_processed / elapsed if elapsed > 0 else 0
        
        # Get system metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        return {
            'events_processed': self.events_processed,
            'events_per_second': events_per_second,
            'files_monitored': self.files_monitored,
            'memory_usage_mb': memory_mb,
            'cpu_usage_percent': cpu_percent,
            'uptime_seconds': elapsed,
            'batch_size': len(self.event_batch)
        }
