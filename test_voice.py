#!/usr/bin/env python3
"""
Test Voice System - Verify TTS and Rules Engine
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
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('voice_test.log')
        ]
    )

def test_tts_directly(speech_notifier):
    """Test TTS directly."""
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
            time.sleep(3)  # Wait longer for speech to complete
        except Exception as e:
            print(f"   ❌ TTS error: {e}")

def test_rules_engine_with_voice(rules_engine, parser):
    """Test the rules engine with voice alerts."""
    print("\n⚙️ Testing Rules Engine with Voice")
    print("=" * 40)
    
    # Create test events that should trigger voice alerts
    from evetalk.events import GameEvent, EventType
    from datetime import datetime
    
    test_events = [
        GameEvent(
            type=EventType.INCOMING_DAMAGE,
            timestamp=datetime.now(),
            subject="Test Entity",
            meta={"damage": 100, "damage_type": "Kinetic"}
        ),
        GameEvent(
            type=EventType.SPATIAL_PHENOMENA,
            timestamp=datetime.now(),
            subject="Abyssal Effect",
            meta={"effect": "spatial_phenomena"}
        )
    ]
    
    for i, event in enumerate(test_events, 1):
        print(f"\n{i}. Processing event: {event.type.value}")
        print(f"   Subject: {event.subject}")
        print(f"   Meta: {event.meta}")
        
        try:
            print("   Processing through rules engine...")
            rules_engine.process_event(event)
            print("   ✅ Event processed successfully")
            print("   🎵 Voice alert should have triggered!")
            time.sleep(2)  # Wait for voice alert
        except Exception as e:
            print(f"   ❌ Error processing event: {e}")
            logging.exception("Rules engine error")

def test_actual_log_events_with_voice(parser, rules_engine, log_file_path):
    """Test processing actual log events with voice alerts."""
    print(f"\n📝 Testing Actual Log Events with Voice")
    print("=" * 40)
    
    try:
        # Find some combat events in the log
        combat_lines = []
        with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if 'Inferno Fury Light Missile - Hits' in line or 'Striking Damavik' in line:
                    combat_lines.append(line)
                    if len(combat_lines) >= 5:  # Test with 5 combat events
                        break
        
        print(f"Testing {len(combat_lines)} combat log lines...")
        
        for i, line in enumerate(combat_lines):
            print(f"\nLine {i+1}: {line[:80]}...")
            
            # Parse the line
            event = parser.parse_line(line, str(log_file_path))
            if event:
                print(f"  ✅ Parsed: {event.type.value}")
                print(f"  Subject: {event.subject}")
                print(f"  Meta: {event.meta}")
                
                # Process it through rules engine
                try:
                    print(f"  🎯 Processing through rules engine...")
                    rules_engine.process_event(event)
                    print(f"  🎵 Voice alert should have triggered!")
                    time.sleep(2)  # Wait for voice alert
                except Exception as e:
                    print(f"  ❌ Rules engine error: {e}")
            else:
                print(f"  ❌ No event parsed")
                
    except Exception as e:
        print(f"❌ Error testing log events: {e}")
        logging.exception("Log event test error")

def main():
    """Main test function."""
    print("EVE Copilot Voice System Test")
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
        
        # Test 2: Rules Engine with Voice
        test_rules_engine_with_voice(rules_engine, parser)
        
        # Test 3: Actual log events with voice
        eve_logs_path = Path(config.get('eve_logs_path'))
        latest_log = max(eve_logs_path.glob("*.txt"), key=lambda f: f.stat().st_mtime)
        test_actual_log_events_with_voice(parser, rules_engine, latest_log)
        
        print(f"\n🔍 Voice test completed!")
        print("Check if you heard any voice alerts during the tests.")
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.exception("Fatal error")
        return 1
    
    return 0

if __name__ == '__main__':
    setup_logging()
    sys.exit(main())
