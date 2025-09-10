#!/usr/bin/env python3
"""
Directly test adding alerts to the web dashboard.
"""

import requests
import json
import time

def test_direct_alerts():
    """Test adding alerts directly to the dashboard."""
    base_url = "http://127.0.0.1:8080"
    
    print("Testing direct alert addition...")
    
    # First, let's check if the dashboard is running
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Dashboard is running - Status: {status['status']}")
        else:
            print(f"❌ Dashboard not responding: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to dashboard: {e}")
        return
    
    # Try to trigger test speech multiple times
    for i in range(3):
        print(f"\nSending test speech {i+1}...")
        try:
            response = requests.post(f"{base_url}/api/control", 
                                  json={"action": "test_speech"},
                                  timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test speech {i+1}: {result['message']}")
            else:
                print(f"❌ Test speech {i+1} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error sending test speech {i+1}: {e}")
        
        time.sleep(1)
    
    # Check alerts after all test speeches
    print("\nChecking alerts...")
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
    test_direct_alerts()
