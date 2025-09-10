#!/usr/bin/env python3
"""
Simple script to add test alerts directly to the running dashboard.
"""

import requests
import json
import time

def add_test_alerts():
    """Add test alerts by making requests to the dashboard."""
    base_url = "http://127.0.0.1:8080"
    
    print("Adding test alerts to the dashboard...")
    
    # Test alerts to add
    test_alerts = [
        ("shield_low", "Shield low - 45%", 0),
        ("you_scrammed", "You are scrambled!", 0),
        ("recall_drones", "Recall drones immediately", 1),
        ("cap_low", "Capacitor low - 15%", 1),
        ("incoming_damage", "Incoming damage spike detected", 0),
    ]
    
    # Since we can't directly add alerts via API, let's try to trigger them
    # by making requests that might cause the system to generate alerts
    for i, (alert_type, message, priority) in enumerate(test_alerts):
        print(f"Adding alert {i+1}: {message}")
        
        # Try different approaches to trigger alerts
        try:
            # Method 1: Try to trigger a test speech (which should add an alert)
            response = requests.post(f"{base_url}/api/control", 
                                  json={"action": "test_speech"},
                                  timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Test speech sent")
            else:
                print(f"  ❌ Test speech failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(0.5)
    
    # Check current alerts
    print("\nChecking current alerts...")
    try:
        response = requests.get(f"{base_url}/api/alerts", timeout=5)
        if response.status_code == 200:
            alerts = response.json()
            print(f"📊 Total alerts: {len(alerts)}")
            if alerts:
                for i, alert in enumerate(alerts):
                    print(f"  {i+1}. {alert['message']} (priority {alert['priority']}) - {alert['timestamp']}")
            else:
                print("  No alerts found")
        else:
            print(f"❌ Failed to get alerts: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting alerts: {e}")

if __name__ == '__main__':
    add_test_alerts()
