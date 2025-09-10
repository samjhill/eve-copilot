#!/usr/bin/env python3
"""
Test script to verify the alert callback mechanism is working.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from web_dashboard import WebDashboard, create_dashboard_templates
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alert_callback():
    """Test the alert callback mechanism."""
    try:
        logger.info("Setting up test environment...")
        
        # Load configuration
        config = Config('config/app.yml')
        
        # Initialize speech notifier (disable actual speech)
        speech_notifier = SpeechNotifier(config)
        speech_notifier.enabled = False
        
        # Initialize web dashboard
        create_dashboard_templates()
        dashboard = WebDashboard(config, None, None)
        
        # Initialize rules engine with alert callback
        rules_engine = RulesEngine(config, speech_notifier, dashboard.add_alert)
        
        logger.info("Testing alert callback...")
        
        # Test direct alert callback
        rules_engine.alert_callback('test_rule', 'Test alert message', 1)
        logger.info(f"Direct callback test - alerts in dashboard: {len(dashboard.alert_history)}")
        
        # Test via _trigger_rule method
        from evetalk.events import GameEvent, EventType
        from datetime import datetime
        
        # Create a test event
        test_event = GameEvent(
            type=EventType.INCOMING_DAMAGE,
            subject="Test Damage",
            timestamp=datetime.now(),
            meta={'damage': 100}
        )
        
        # Create a test rule
        from evetalk.engine import Rule
        test_rule_config = {
            'name': 'test_damage_rule',
            'enabled': True,
            'event_types': ['INCOMING_DAMAGE'],
            'cooldown_ms': 1000,
            'priority': 1,
            'voice_prompt': 'Test damage detected'
        }
        test_rule = Rule(test_rule_config)
        
        # Add rule to engine
        rules_engine.rules = [test_rule]
        
        # Process the event
        rules_engine.process_event(test_event)
        
        logger.info(f"After processing event - alerts in dashboard: {len(dashboard.alert_history)}")
        logger.info(f"Rules engine alerts_sent: {rules_engine.alerts_sent}")
        
        # Print all alerts
        for i, alert in enumerate(dashboard.alert_history):
            logger.info(f"Alert {i+1}: {alert}")
        
        return len(dashboard.alert_history) > 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    success = test_alert_callback()
    if success:
        print("✅ Alert callback test PASSED")
    else:
        print("❌ Alert callback test FAILED")
