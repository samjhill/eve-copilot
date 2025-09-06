#!/usr/bin/env python3
"""
Real-time EVE log monitor using tail-like approach
Reads new lines as they're added to the log file
"""

import time
import os
import sys
import signal
import logging
from pathlib import Path
from typing import Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from evetalk.parse import LogParser
from process_lock import ensure_single_instance

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TailMonitor:
    """Monitor log file for new lines using tail-like approach."""
    
    def __init__(self, log_file: Path, parser: LogParser, rules_engine: RulesEngine):
        self.log_file = log_file
        self.parser = parser
        self.rules_engine = rules_engine
        self.file_position = 0
        self.running = True
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal, stopping monitor...")
        self.running = False
    
    def _get_file_size(self) -> int:
        """Get current file size."""
        try:
            return self.log_file.stat().st_size
        except (OSError, FileNotFoundError):
            return 0
    
    def _read_new_lines(self) -> list[str]:
        """Read new lines from the file since last position."""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # Seek to last known position
                f.seek(self.file_position)
                
                # Read all new content
                new_content = f.read()
                
                # Update position
                self.file_position = f.tell()
                
                # Split into lines and filter out empty ones
                lines = [line.strip() for line in new_content.split('\n') if line.strip()]
                return lines
                
        except (OSError, FileNotFoundError) as e:
            logger.error(f"Error reading log file: {e}")
            return []
    
    def monitor(self):
        """Main monitoring loop."""
        logger.info(f"Starting tail monitor for {self.log_file.name}")
        
        # Initialize file position to end of file
        self.file_position = self._get_file_size()
        logger.info(f"Starting from position {self.file_position}")
        
        while self.running:
            try:
                # Read new lines
                new_lines = self._read_new_lines()
                
                if new_lines:
                    logger.info(f"Processing {len(new_lines)} new lines")
                    
                    # Process each new line
                    for line in new_lines:
                        if not self.running:
                            break
                            
                        # Parse the line
                        event = self.parser.parse_line(line, str(self.log_file))
                        
                        if event:
                            logger.info(f"Parsed event: {event.type.value} - {event.subject}")
                            # Process the event through rules engine
                            try:
                                self.rules_engine.process_event(event)
                            except Exception as e:
                                logger.error(f"Error processing event: {e}")
                        else:
                            # Log unparsed lines for debugging
                            if "combat" in line.lower() and "from" in line.lower():
                                logger.warning(f"Failed to parse combat line: {line[:100]}...")
                
                # Sleep briefly before checking again
                time.sleep(0.1)  # 100ms check interval
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)  # Wait before retrying
        
        logger.info("Tail monitor stopped")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EVE Copilot Real-time Tail Monitor")
    parser.add_argument("--force", action="store_true", 
                       help="Force kill existing processes and start")
    args = parser.parse_args()
    
    print("EVE Copilot Real-time Tail Monitor")
    print("=" * 50)
    
    # Ensure only one instance is running
    lock = ensure_single_instance(force_kill=args.force)
    if not lock:
        print("❌ Another instance is already running. Use --force to kill it.")
        return 1
    
    print("🎮 Ready to monitor EVE Online logs in real-time!")
    print("🚀 Start your abyss run and you'll hear voice alerts!")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Load configuration
        config = Config("config/app.yml")
        print(f"✓ Loaded configuration")
        
        # Initialize components
        speech_notifier = SpeechNotifier(config)
        rules_engine = RulesEngine(config, speech_notifier)
        parser = LogParser("config/patterns/core.yml")
        
        print(f"✓ Active profile: {rules_engine.active_profile}")
        print(f"✓ TTS Engine: {config.get('speech.tts_engine')}")
        
        # Find the most recent log file
        eve_logs_path = Path(config.get('eve_logs_path', '~/Documents/EVE/logs/Gamelogs')).expanduser()
        
        if not eve_logs_path.exists():
            print(f"❌ EVE logs directory not found: {eve_logs_path}")
            return 1
        
        # Get the most recent log file
        log_files = list(eve_logs_path.glob("*.txt"))
        if not log_files:
            print(f"❌ No log files found in {eve_logs_path}")
            return 1
        
        # Sort by modification time, most recent first
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_log = log_files[0]
        
        print(f"📁 Monitoring: {latest_log.name}")
        print(f"📁 File size: {latest_log.stat().st_size} bytes")
        
        # Start monitoring
        monitor = TailMonitor(latest_log, parser, rules_engine)
        monitor.monitor()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        if 'lock' in locals():
            lock.release()

if __name__ == "__main__":
    sys.exit(main())
