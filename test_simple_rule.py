#!/usr/bin/env python3
"""
Test Simple Rule Triggering
"""

import time
import logging
from datetime import datetime

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from evetalk.events import GameEvent, EventType

def setup_logging():
    """Setup logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_simple_rule():
    """Test a simple rule that should definitely trigger."""
    print("Testing Simple Rule Triggering")
    print("=" * 50)
    
    try:
        # Load configuration
        config = Config("config/app.yml")
        print(f"✓ Loaded configuration")
        
        # Initialize components
        speech_notifier = SpeechNotifier(config)
        rules_engine = RulesEngine(config, speech_notifier)
        
        print(f"✓ Active profile: {rules_engine.active_profile}")
        print(f"✓ Rules loaded: {len(rules_engine.rules)}")
        
        # Find the damage_spike_abyssal rule
        damage_rule = None
        for rule in rules_engine.rules:
            if rule.name == "damage_spike_abyssal":
                damage_rule = rule
                break
        
        if damage_rule:
            print(f"✓ Found damage_spike_abyssal rule")
            print(f"  Event types: {damage_rule.event_types}")
            print(f"  Conditions: {damage_rule.conditions}")
            print(f"  Voice prompt: {damage_rule.voice_prompt}")
            print(f"  Enabled: {damage_rule.enabled}")
            print(f"  Cooldown: {damage_rule.cooldown_ms}ms")
            print(f"  Window: {damage_rule.window_ms}ms")
        else:
            print("❌ damage_spike_abyssal rule not found")
            return
        
        # Create a simple INCOMING_DAMAGE event
        test_event = GameEvent(
            type=EventType.INCOMING_DAMAGE,
            timestamp=datetime.now(),
            subject="Test Entity",
            meta={"damage": 100, "damage_type": "Kinetic"}
        )
        
        print(f"\n🎯 Testing with event: {test_event.type.value}")
        print(f"  Subject: {test_event.subject}")
        print(f"  Meta: {test_event.meta}")
        
        # Check if rule should trigger
        current_time = time.time()
        print(f"\n🔍 Rule analysis:")
        print(f"  Can trigger: {damage_rule.can_trigger(current_time)}")
        print(f"  Event type matches: {test_event.type.value in damage_rule.event_types}")
        print(f"  Rule enabled: {damage_rule.enabled}")
        
        # Process the event
        print(f"\n⚙️ Processing event through rules engine...")
        rules_engine.process_event(test_event)
        
        print(f"\n✅ Test completed!")
        print("Check if you heard the voice alert: 'Damage spike'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    setup_logging()
    test_simple_rule()

