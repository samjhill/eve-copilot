#!/usr/bin/env python3
"""
Test script to verify the alert system is working in the web dashboard.
This script will generate some test alerts to populate the Recent Alerts section.
"""

import sys
import time
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.notify import SpeechNotifier
from web_dashboard import WebDashboard, create_dashboard_templates

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alert_system():
    """Test the alert system by generating some test alerts."""
    try:
        logger.info("Setting up test environment...")
        
        # Load configuration
        config = Config('config/app.yml')
        
        # Initialize speech notifier (but disable actual speech)
        speech_notifier = SpeechNotifier(config)
        speech_notifier.enabled = False  # Disable actual speech for testing
        
        # Initialize rules engine
        rules_engine = RulesEngine(config, speech_notifier)
        
        # Create dashboard templates
        create_dashboard_templates()
        
        # Initialize web dashboard
        dashboard = WebDashboard(config, rules_engine, None)
        
        # Connect alert callback
        rules_engine.alert_callback = dashboard.add_alert
        
        logger.info("Generating test alerts...")
        
        # Generate some test alerts
        test_alerts = [
            ("shield_low", "Shield low", 0),
            ("you_scrammed", "You are scrambled", 0),
            ("recall_drones", "Recall drones", 1),
            ("cap_low", "Capacitor low", 1),
            ("incoming_damage_spike", "Incoming damage spike", 0),
            ("reload_required", "Reload now", 1),
            ("you_webbed", "You are webbed", 1),
            ("charges_depleted", "Charges depleted", 1),
        ]
        
        for alert_type, message, priority in test_alerts:
            dashboard.add_alert(alert_type, message, priority)
            logger.info(f"Added test alert: {message}")
            time.sleep(0.5)  # Small delay between alerts
        
        logger.info(f"Generated {len(test_alerts)} test alerts")
        logger.info("Starting web dashboard...")
        logger.info("Open http://127.0.0.1:8080 in your browser to see the alerts")
        logger.info("Press Ctrl+C to stop")
        
        # Start the dashboard
        dashboard.run(host='127.0.0.1', port=8080, debug=False)
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        logger.info("Test completed")

if __name__ == '__main__':
    test_alert_system()
