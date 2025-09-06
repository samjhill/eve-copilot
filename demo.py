#!/usr/bin/env python3
"""
Demo script for EVE Copilot - shows how to use the system programmatically
"""

import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_parser():
    """Demonstrate the log parser functionality."""
    print("\n=== Testing Log Parser ===")
    
    from evetalk.parse import LogParser
    from evetalk.events import EventType
    
    # Create parser
    parser = LogParser("config/patterns/core.yml")
    
    # Test lines
    test_lines = [
        "2025.01.28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik",
        "2025.01.28 14:30:19	You are warp scrambled by Damavik",
        "2025.01.28 14:30:23	Shield Booster requires reload",
        "2025.01.28 14:30:15	You take 45 Thermal damage from Damavik",
        "This is not a valid EVE log line"
    ]
    
    print(f"Testing {len(test_lines)} log lines...")
    
    for i, line in enumerate(test_lines, 1):
        print(f"\nLine {i}: {line}")
        event = parser.parse_line(line)
        
        if event:
            print(f"  ✓ Parsed: {event.type.value}")
            print(f"  Subject: {event.subject}")
            print(f"  Meta: {event.meta}")
        else:
            print("  ✗ No event parsed")
    
    print(f"\nParser has {len(parser.compiled_patterns)} compiled patterns")


def demo_events():
    """Demonstrate the event system."""
    print("\n=== Testing Event System ===")
    
    from evetalk.events import (
        create_drone_hit, create_you_scrammed, 
        create_reload_required, create_incoming_damage
    )
    from datetime import datetime
    
    # Create sample events
    timestamp = datetime.now()
    
    events = [
        create_drone_hit("Hobgoblin II", 62, "Thermal", "Damavik", timestamp),
        create_you_scrammed("Damavik", timestamp),
        create_reload_required("Shield Booster", timestamp),
        create_incoming_damage(45, "Thermal", "Damavik", timestamp)
    ]
    
    print(f"Created {len(events)} sample events:")
    
    for event in events:
        print(f"\n  {event.type.value}: {event.subject}")
        print(f"    Meta: {event.meta}")
        print(f"    Dict: {event.to_dict()}")


def demo_rules_engine():
    """Demonstrate the rules engine functionality."""
    print("\n=== Testing Rules Engine ===")
    
    from evetalk.config import Config
    from evetalk.notify import SpeechNotifier
    from evetalk.engine import RulesEngine
    from evetalk.events import create_incoming_damage
    from datetime import datetime
    
    try:
        # Create mock config
        config = Config("config/app.yml.example")
        
        # Create speech notifier (will be disabled if TTS not available)
        speech_notifier = SpeechNotifier(config)
        
        # Create rules engine
        rules_engine = RulesEngine(config, speech_notifier)
        
        print(f"Active profile: {rules_engine.get_active_profile()}")
        print(f"Available profiles: {rules_engine.get_available_profiles()}")
        print(f"Active rules: {len(rules_engine.rules)}")
        
        # Show profile info
        for profile_name in rules_engine.get_available_profiles():
            profile_info = rules_engine.get_profile_info(profile_name)
            if profile_info:
                print(f"\nProfile: {profile_info['name']}")
                print(f"  Description: {profile_info['description']}")
                print(f"  Rules: {profile_info['rule_count']}")
        
        # Test processing an event
        print("\nTesting event processing...")
        test_event = create_incoming_damage(100, "Thermal", "Test Entity", datetime.now())
        print(f"Processing event: {test_event}")
        
        # Process the event
        rules_engine.process_event(test_event)
        
        print("Event processed successfully")
        
    except Exception as e:
        print(f"Error testing rules engine: {e}")


def demo_file_parsing():
    """Demonstrate parsing a sample log file."""
    print("\n=== Testing File Parsing ===")
    
    from evetalk.parse import LogParser
    
    sample_file = Path("sample_logs/sample_chatlog.txt")
    
    if sample_file.exists():
        print(f"Parsing sample log file: {sample_file}")
        
        parser = LogParser("config/patterns/core.yml")
        events = parser.parse_file(sample_file)
        
        print(f"Parsed {len(events)} events from sample file:")
        
        # Group events by type
        event_counts = {}
        for event in events:
            event_type = event.type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        for event_type, count in event_counts.items():
            print(f"  {event_type}: {count}")
        
        # Show first few events
        print("\nFirst 3 events:")
        for i, event in enumerate(events[:3]):
            print(f"  {i+1}. {event}")
    
    else:
        print(f"Sample log file not found: {sample_file}")


def main():
    """Run all demos."""
    print("EVE Copilot Demo")
    print("=" * 50)
    
    try:
        # Test individual components
        demo_parser()
        demo_events()
        demo_rules_engine()
        demo_file_parsing()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nTo run the full application:")
        print("  python app.py")
        print("\nTo run tests:")
        print("  python run_tests.py")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo error")


if __name__ == "__main__":
    main()
