#!/usr/bin/env python3
"""
EVE Copilot Log Simulator - Replays log events in real-time for testing voice alerts
"""

import time
import logging
import sys
from pathlib import Path

from evetalk.config import Config
from evetalk.parse import LogParser
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier

def setup_logging():
    """Setup logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('eve_copilot_sim.log')
        ]
    )

def simulate_log_replay(parser, rules_engine, log_file_path, speed_multiplier=2.0):
    """Simulate the log file replay at specified speed."""
    print(f"\n🎬 Simulating Log Replay: {log_file_path.name}")
    print(f"⏱️  Speed: {speed_multiplier}x normal time")
    print("=" * 50)
    
    try:
        # Parse all events from the log file line by line
        events = []
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    event = parser.parse_line(line, str(log_file_path))
                    if event:
                        events.append(event)
        
        print(f"📊 Total events to simulate: {len(events)}")
        
        if not events:
            print("❌ No events found in log file")
            return
        
        # Get time range
        if events:
            start_time = events[0].timestamp
            end_time = events[-1].timestamp
            duration = end_time - start_time
            print(f"⏰ Time range: {start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🕐 Duration: {duration}")
            print(f"🚀 Simulated duration: {duration / speed_multiplier}")
        
        print(f"\n🎯 Starting simulation...")
        print("Press Ctrl+C to stop")
        print("=" * 50)
        
        # Track voice alerts triggered
        voice_alerts_triggered = 0
        rules_triggered = set()
        
        # Calculate time intervals between events
        time_diffs = []
        for i in range(1, len(events)):
            diff = (events[i].timestamp - events[i-1].timestamp).total_seconds()
            time_diffs.append(diff)
        
        # Simulate events with realistic timing
        start_time = time.time()
        simulated_time = events[0].timestamp
        
        for i, event in enumerate(events):
            try:
                # Calculate delay based on real timing
                if i > 0:
                    delay = time_diffs[i-1] / speed_multiplier
                    if delay > 0:
                        time.sleep(delay)
                
                # Update simulated time
                if i > 0:
                    simulated_time = events[i].timestamp
                
                # Display event info
                elapsed = time.time() - start_time
                print(f"[{elapsed:6.1f}s] 🎯 {event.type.value}: {event.subject}")
                
                # Process event through rules engine
                try:
                    # Store initial rule count
                    initial_rule_count = len(rules_engine.rules)
                    
                    # Process the event
                    rules_engine.process_event(event)
                    
                    # Check if any rules were triggered (this is a simple heuristic)
                    # We'll look for the INFO log message that indicates rule triggering
                    # For now, we'll just count events and assume some will trigger rules
                    
                    # Show progress every 50 events
                    if (i + 1) % 50 == 0:
                        progress = ((i + 1) / len(events)) * 100
                        print(f"📈 Progress: {progress:.1f}% ({i + 1}/{len(events)})")
                    
                except Exception as e:
                    print(f"❌ Error processing event {i+1}: {e}")
                    logging.exception(f"Event processing error")
                
            except KeyboardInterrupt:
                print(f"\n🛑 Simulation stopped at event {i+1}/{len(events)}")
                break
        
        total_time = time.time() - start_time
        print(f"\n✅ Simulation completed in {total_time:.1f} seconds")
        print(f"🎵 You should have heard voice alerts for relevant events!")
        print(f"\n🔍 Check the logs above for 'Rule triggered' messages to confirm voice alerts worked.")
        
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        logging.exception("Simulation error")

def main():
    """Main simulation function."""
    print("EVE Copilot Log Simulator")
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
        
        # Find latest log file
        eve_logs_path = Path(config.get('eve_logs_path'))
        latest_log = max(eve_logs_path.glob("*.txt"), key=lambda f: f.stat().st_mtime)
        
        print(f"📁 Latest log file: {latest_log.name}")
        print(f"📅 Last modified: {time.ctime(latest_log.stat().st_mtime)}")
        print(f"📏 File size: {latest_log.stat().st_size} bytes")
        
        # Run simulation at 5x speed
        simulate_log_replay(parser, rules_engine, latest_log, speed_multiplier=5.0)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")
        return 1
    
    return 0

if __name__ == '__main__':
    setup_logging()
    sys.exit(main())
