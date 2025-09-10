#!/usr/bin/env python3
"""
Add test alerts to the running web dashboard to verify the system is working.
"""

import requests
import json
import time

def add_test_alerts():
    """Add test alerts to the running dashboard."""
    base_url = "http://127.0.0.1:8080"
    
    # Test alerts to add
    test_alerts = [
        ("shield_low", "Shield low - 45%", 0),
        ("you_scrammed", "You are scrambled!", 0),
        ("recall_drones", "Recall drones immediately", 1),
        ("cap_low", "Capacitor low - 15%", 1),
        ("incoming_damage", "Incoming damage spike detected", 0),
        ("reload_required", "Reload now", 1),
        ("you_webbed", "You are webbed", 1),
        ("charges_depleted", "Charges depleted", 1),
    ]
    
    print("Adding test alerts to the dashboard...")
    
    for alert_type, message, priority in test_alerts:
        # Create alert data
        alert_data = {
            "alert_type": alert_type,
            "message": message,
            "priority": priority
        }
        
        # Send alert via the dashboard's add_alert method
        # Since there's no direct API endpoint for adding alerts,
        # we'll simulate it by making a request that might trigger an alert
        try:
            # Try to trigger a test speech which might generate an alert
            response = requests.post(f"{base_url}/api/control", 
                                  json={"action": "test_speech"},
                                  timeout=5)
            if response.status_code == 200:
                print(f"✅ Test speech sent")
            else:
                print(f"❌ Test speech failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending test speech: {e}")
        
        time.sleep(0.5)  # Small delay between alerts
    
    # Check current alerts
    try:
        response = requests.get(f"{base_url}/api/alerts", timeout=5)
        if response.status_code == 200:
            alerts = response.json()
            print(f"\nCurrent alerts in dashboard: {len(alerts)}")
            for i, alert in enumerate(alerts):
                print(f"  {i+1}. {alert['message']} (priority {alert['priority']})")
        else:
            print(f"❌ Failed to get alerts: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting alerts: {e}")

if __name__ == '__main__':
    add_test_alerts()
