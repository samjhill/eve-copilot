#!/usr/bin/env python3
"""
Test directly adding alerts to the dashboard without going through the API.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from evetalk.config import Config
from web_dashboard import WebDashboard, create_dashboard_templates
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_dashboard():
    """Test directly adding alerts to the dashboard."""
    try:
        logger.info("Setting up test dashboard...")
        
        # Load configuration
        config = Config('config/app.yml')
        
        # Create dashboard templates
        create_dashboard_templates()
        
        # Initialize web dashboard
        dashboard = WebDashboard(config, None, None)
        
        logger.info(f"Initial alerts: {len(dashboard.alert_history)}")
        
        # Add test alerts directly
        test_alerts = [
            ("shield_low", "Shield low - 45%", 0),
            ("you_scrammed", "You are scrambled!", 0),
            ("recall_drones", "Recall drones immediately", 1),
            ("cap_low", "Capacitor low - 15%", 1),
            ("incoming_damage", "Incoming damage spike detected", 0),
        ]
        
        for alert_type, message, priority in test_alerts:
            dashboard.add_alert(alert_type, message, priority)
            logger.info(f"Added alert: {message}")
        
        logger.info(f"Final alerts: {len(dashboard.alert_history)}")
        
        # Print all alerts
        for i, alert in enumerate(dashboard.alert_history):
            logger.info(f"Alert {i+1}: {alert['message']} (priority {alert['priority']})")
        
        return len(dashboard.alert_history) > 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    success = test_direct_dashboard()
    if success:
        print("✅ Direct dashboard test PASSED")
    else:
        print("❌ Direct dashboard test FAILED")
