#!/usr/bin/env python3
"""
Simple EVE Copilot Monitor - Command-line version for macOS
"""

import time
import logging
import sys
import argparse
from pathlib import Path

from evetalk.config import Config
from evetalk.parse import LogParser
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from process_lock import ensure_single_instance

def setup_logging():
    """Setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('eve_copilot_simple.log')
        ]
    )

def test_active_log(parser, rules_engine, active_log_path):
    """Test the active log file to see what events are detected."""
    print(f"\n🔍 Testing Active Log: {active_log_path.name}")
    print("=" * 60)
    
    try:
        # Parse the entire active log file
        events = []
        with open(active_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                event = parser.parse_line(line.strip())
                if event:
                    events.append(event)
        print(f"📊 Total events found: {len(events)}")
        
        if not events:
            print("❌ No events detected! This suggests a parsing issue.")
            return False
        
        # Group events by type
        event_counts = {}
        for event in events:
            event_type = event.type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        print("\n📈 Event Breakdown:")
        for event_type, count in sorted(event_counts.items()):
            print(f"  {event_type}: {count}")
        
        # Test processing each event to see what voice commands activate
        print(f"\n🎯 Testing Voice Commands for Each Event:")
        print("-" * 60)
        
        voice_commands_triggered = set()
        
        for i, event in enumerate(events[:20]):  # Test first 20 events
            print(f"\nEvent {i+1}: {event.type.value}")
            print(f"  Subject: {event.subject}")
            print(f"  Meta: {event.meta}")
            
            # Process the event to trigger voice commands
            try:
                rules_engine.process_event(event)
                print(f"  ✅ Processed - Voice command should have triggered")
                voice_commands_triggered.add(event.type.value)
            except Exception as e:
                print(f"  ❌ Error processing: {e}")
        
        if len(events) > 20:
            print(f"\n... and {len(events) - 20} more events")
        
        print(f"\n🎵 Voice Commands Triggered: {len(voice_commands_triggered)}")
        for cmd in sorted(voice_commands_triggered):
            print(f"  ✓ {cmd}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing active log: {e}")
        logging.exception("Error testing active log")
        return False

def main():
    """Main monitoring function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="EVE Copilot Simple Monitor")
    parser.add_argument("--force", action="store_true", 
                       help="Force kill existing processes and start")
    args = parser.parse_args()
    
    print("EVE Copilot Simple Monitor - Active Log Test")
    print("=" * 60)
    
    # Ensure only one instance is running
    lock = ensure_single_instance(force_kill=args.force)
    if not lock:
        print("❌ Another instance is already running. Use --force to kill it.")
        return 1
    
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
            return
        
        print(f"✓ EVE logs path exists")
        
        # Find the latest active log file
        log_files = list(eve_logs_path.glob("*.txt"))
        if not log_files:
            print("❌ No log files found!")
            return
        
        # Sort by modification time to find the latest
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
        print(f"📁 Latest log file: {latest_log.name}")
        print(f"📅 Last modified: {time.ctime(latest_log.stat().st_mtime)}")
        print(f"📏 File size: {latest_log.stat().st_size} bytes")
        
        # Test the active log file
        if not test_active_log(parser, rules_engine, latest_log):
            print("\n❌ Active log test failed!")
            return
        
        print(f"\n✅ Active log test completed successfully!")
        print("\nNow you should have heard voice alerts for the events detected.")
        print("If you didn't hear anything, check:")
        print("  1. Your system volume")
        print("  2. TTS engine configuration")
        print("  3. Event parsing patterns")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")
        return 1
    
    return 0

if __name__ == '__main__':
    setup_logging()
    sys.exit(main())
