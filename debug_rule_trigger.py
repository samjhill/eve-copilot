#!/usr/bin/env python3
"""
Debug script to understand why rules aren't triggering alerts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from evetalk.config import Config
from evetalk.engine import RulesEngine, Rule
from evetalk.notify import SpeechNotifier
from evetalk.events import GameEvent, EventType
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_rule_trigger():
    """Debug why rules aren't triggering alerts."""
    try:
        logger.info("Setting up debug environment...")
        
        # Load configuration
        config = Config('config/app.yml')
        
        # Initialize speech notifier (disable actual speech)
        speech_notifier = SpeechNotifier(config)
        speech_notifier.enabled = False
        
        # Initialize rules engine with alert callback
        alert_callback = lambda alert_type, message, priority: logger.info(f"ALERT: {alert_type} - {message} (priority {priority})")
        rules_engine = RulesEngine(config, speech_notifier, alert_callback)
        
        # Create a simple test rule
        test_rule_config = {
            'name': 'test_damage_rule',
            'enabled': True,
            'event_types': ['IncomingDamage'],  # Use the enum value, not the enum name
            'cooldown_ms': 1000,
            'priority': 1,
            'voice_prompt': 'Test damage detected'
        }
        test_rule = Rule(test_rule_config)
        
        # Add rule to engine
        rules_engine.rules = [test_rule]
        
        # Create a test event
        test_event = GameEvent(
            type=EventType.INCOMING_DAMAGE,
            subject="Test Damage",
            timestamp=datetime.now(),
            meta={'damage': 100}
        )
        
        logger.info(f"Test rule: {test_rule.name}")
        logger.info(f"Test rule enabled: {test_rule.enabled}")
        logger.info(f"Test rule event_types: {test_rule.event_types}")
        logger.info(f"Test rule voice_prompt: {test_rule.voice_prompt}")
        logger.info(f"Test event type: {test_event.type.value}")
        
        # Check if rule should trigger
        current_time = 1000.0  # Some arbitrary time
        should_trigger = test_rule.should_trigger(test_event, current_time)
        logger.info(f"Rule should trigger: {should_trigger}")
        
        # Check if rule can trigger
        can_trigger = test_rule.can_trigger(current_time)
        logger.info(f"Rule can trigger: {can_trigger}")
        
        # Process the event
        logger.info("Processing event...")
        rules_engine.process_event(test_event)
        
        logger.info(f"Rules triggered: {rules_engine.rules_triggered}")
        logger.info(f"Alerts sent: {rules_engine.alerts_sent}")
        
        return True
        
    except Exception as e:
        logger.error(f"Debug failed: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    debug_rule_trigger()
