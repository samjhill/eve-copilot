#!/usr/bin/env python3
"""
Test script to verify the fixed configuration works with alert callbacks.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from evetalk.events import GameEvent, EventType
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fixed_config():
    """Test the fixed configuration with alert callbacks."""
    try:
        logger.info("Setting up test with fixed configuration...")
        
        # Load configuration
        config = Config('config/app.yml')
        
        # Initialize speech notifier (disable actual speech)
        speech_notifier = SpeechNotifier(config)
        speech_notifier.enabled = False
        
        # Alert callback to track alerts
        alerts_received = []
        def alert_callback(alert_type, message, priority):
            alerts_received.append((alert_type, message, priority))
            logger.info(f"ALERT RECEIVED: {alert_type} - {message} (priority {priority})")
        
        # Initialize rules engine with alert callback
        rules_engine = RulesEngine(config, speech_notifier, alert_callback)
        
        logger.info(f"Loaded {len(rules_engine.rules)} rules")
        logger.info(f"Active profile: {rules_engine.active_profile}")
        
        # Create test events for different rule types
        test_events = [
            GameEvent(
                type=EventType.INCOMING_DAMAGE,
                subject="Test Damage",
                timestamp=datetime.now(),
                meta={'damage': 100}
            ),
            GameEvent(
                type=EventType.DRONE_HIT,
                subject="Test Drone Hit",
                timestamp=datetime.now(),
                meta={'damage': 50}
            ),
            GameEvent(
                type=EventType.WARP_SCRAMBLE,
                subject="Test Scramble",
                timestamp=datetime.now(),
                meta={}
            ),
        ]
        
        # Process each test event
        for i, event in enumerate(test_events):
            logger.info(f"Processing test event {i+1}: {event.type.value}")
            rules_engine.process_event(event)
        
        logger.info(f"Rules triggered: {rules_engine.rules_triggered}")
        logger.info(f"Alerts sent: {rules_engine.alerts_sent}")
        logger.info(f"Alerts received: {len(alerts_received)}")
        
        for i, (alert_type, message, priority) in enumerate(alerts_received):
            logger.info(f"Alert {i+1}: {alert_type} - {message} (priority {priority})")
        
        return len(alerts_received) > 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    success = test_fixed_config()
    if success:
        print("✅ Fixed configuration test PASSED")
    else:
        print("❌ Fixed configuration test FAILED")
