#!/usr/bin/env python3
"""
Real-time EVE Copilot Monitor - Continuous monitoring for live gameplay
"""

import time
import logging
import sys
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from evetalk.config import Config
from evetalk.parse import LogParser
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from process_lock import ensure_single_instance

class EVELogHandler(FileSystemEventHandler):
    """Handle EVE log file changes."""
    
    def __init__(self, parser, rules_engine):
        self.parser = parser
        self.rules_engine = rules_engine
        self.processed_files = set()
        
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix != '.txt':
            return
            
        # Process the file every time it's modified for real-time monitoring
        # This ensures we catch new events as they're added to the log
            
        self.processed_files.add(str(file_path))
        
        try:
            # Process the log file
            events = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    event = self.parser.parse_line(line.strip())
                    if event:
                        events.append(event)
            
            if events:
                print(f"📁 Processing {file_path.name}: {len(events)} events")
                
                # Process each event through the rules engine
                for event in events:
                    try:
                        self.rules_engine.process_event(event)
                    except Exception as e:
                        logging.error(f"Error processing event: {e}")
                        
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")

def setup_logging():
    """Setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('eve_copilot_realtime.log')
        ]
    )

def main():
    """Main monitoring function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="EVE Copilot Real-time Monitor")
    parser.add_argument("--force", action="store_true", 
                       help="Force kill existing processes and start")
    args = parser.parse_args()
    
    print("EVE Copilot Real-time Monitor")
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
        print(f"✓ Watching: {config.get('eve_logs_path')}")
        
        # Get EVE logs path
        eve_logs_path = Path(config.get('eve_logs_path'))
        if not eve_logs_path.exists():
            print(f"❌ EVE logs path does not exist: {eve_logs_path}")
            return 1
        
        print(f"✓ EVE logs path exists")
        
        # Process the most recent log file on startup
        log_files = list(eve_logs_path.glob("*.txt"))
        if log_files:
            # Sort by modification time, most recent first
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_log = log_files[0]
            print(f"📁 Processing latest log file: {latest_log.name}")
            
            # Process the latest log file
            events = []
            with open(latest_log, 'r', encoding='utf-8') as f:
                for line in f:
                    event = parser.parse_line(line.strip())
                    if event:
                        events.append(event)
            
            if events:
                print(f"📁 Processing {latest_log.name}: {len(events)} events")
                
                # Process each event through the rules engine
                for event in events:
                    try:
                        rules_engine.process_event(event)
                    except Exception as e:
                        logging.error(f"Error processing event: {e}")
            else:
                print(f"📁 No events found in {latest_log.name}")
        else:
            print(f"📁 No log files found in {eve_logs_path}")
        
        # Set up file watcher
        event_handler = EVELogHandler(parser, rules_engine)
        observer = Observer()
        observer.schedule(event_handler, str(eve_logs_path), recursive=False)
        
        # Start watching
        observer.start()
        print(f"👀 Started watching for new log files...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping monitor...")
            observer.stop()
        
        observer.join()
        print(f"✅ Monitor stopped")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")
        return 1
    
    return 0

if __name__ == '__main__':
    setup_logging()
    sys.exit(main())
