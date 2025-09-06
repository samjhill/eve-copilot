#!/usr/bin/env python3
"""
Debug TTS System - Test voice alerts step by step
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
        level=logging.DEBUG,  # Use DEBUG level to see all details
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('eve_copilot_debug.log')
        ]
    )

def test_tts_directly(speech_notifier):
    """Test TTS directly without the rules engine."""
    print("\n🔊 Testing TTS Directly")
    print("=" * 40)
    
    test_messages = [
        "Testing TTS system",
        "Damage spike detected",
        "Shield low",
        "You are scrambled"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: '{message}'")
        try:
            speech_notifier.speak(message, priority=0)
            print(f"   ✅ TTS command sent")
            time.sleep(2)  # Wait for speech to complete
        except Exception as e:
            print(f"   ❌ TTS error: {e}")

def test_rules_engine(rules_engine, parser):
    """Test the rules engine with sample events."""
    print("\n⚙️ Testing Rules Engine")
    print("=" * 40)
    
    # Create a test event that should trigger a voice alert
    from evetalk.events import create_incoming_damage
    from datetime import datetime
    
    test_event = create_incoming_damage(100, "Kinetic", "Test Entity", datetime.now())
    print(f"Test event: {test_event}")
    
    try:
        print("Processing event through rules engine...")
        rules_engine.process_event(test_event)
        print("✅ Event processed successfully")
    except Exception as e:
        print(f"❌ Error processing event: {e}")
        logging.exception("Rules engine error")

def test_single_log_event(parser, rules_engine, log_file_path):
    """Test processing a single event from the log."""
    print(f"\n📝 Testing Single Log Event")
    print("=" * 40)
    
    try:
        # Parse just the first few lines
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[:10]  # First 10 lines
        
        print(f"Testing {len(lines)} log lines...")
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            print(f"\nLine {i+1}: {line[:100]}...")
            
            # Try to parse the line
            event = parser.parse_line(line, str(log_file_path))
            if event:
                print(f"  ✅ Parsed: {event.type.value}")
                print(f"  Subject: {event.subject}")
                
                # Try to process it
                try:
                    rules_engine.process_event(event)
                    print(f"  🎵 Voice alert should have triggered!")
                except Exception as e:
                    print(f"  ❌ Rules engine error: {e}")
            else:
                print(f"  ❌ No event parsed")
                
    except Exception as e:
        print(f"❌ Error testing log event: {e}")
        logging.exception("Log event test error")

def main():
    """Main debug function."""
    print("EVE Copilot TTS Debug")
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
        print(f"✓ Speech enabled: {config.get('speech.enabled')}")
        
        # Test 1: Direct TTS
        test_tts_directly(speech_notifier)
        
        # Test 2: Rules Engine
        test_rules_engine(rules_engine, parser)
        
        # Test 3: Single log event
        eve_logs_path = Path(config.get('eve_logs_path'))
        latest_log = max(eve_logs_path.glob("*.txt"), key=lambda f: f.stat().st_mtime)
        test_single_log_event(parser, rules_engine, latest_log)
        
        print(f"\n🔍 Debug completed!")
        print("Check the output above to see where the issue is.")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")
        return 1
    
    return 0

if __name__ == '__main__':
    setup_logging()
    sys.exit(main())
