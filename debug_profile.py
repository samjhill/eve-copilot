#!/usr/bin/env python3
"""
Debug Profile Loading
"""

import yaml
from pathlib import Path

def debug_profile_loading():
    """Debug profile loading."""
    print("Debugging Profile Loading")
    print("=" * 50)
    
    # Test loading the abyssal profile directly
    profile_file = Path("config/profiles/abyssal.yml")
    
    if not profile_file.exists():
        print(f"❌ Profile file not found: {profile_file}")
        return
    
    try:
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = yaml.safe_load(f)
        
        print(f"✅ Profile loaded successfully")
        print(f"Type: {type(profile_data)}")
        print(f"Keys: {list(profile_data.keys()) if isinstance(profile_data, dict) else 'Not a dict'}")
        
        if isinstance(profile_data, dict):
            rules = profile_data.get('rules', {})
            print(f"Rules count: {len(rules)}")
            print(f"Rules type: {type(rules)}")
            
            if rules and isinstance(rules, dict):
                print(f"Rules keys: {list(rules.keys())}")
                
                # Test the specific rule that should trigger for INCOMING_DAMAGE
                for rule_name, rule_data in rules.items():
                    if isinstance(rule_data, dict) and rule_data.get('event_types') == ["INCOMING_DAMAGE"]:
                        print(f"Found INCOMING_DAMAGE rule: {rule_name}")
                        print(f"  Voice prompt: {rule_data.get('voice_prompt')}")
                        print(f"  Enabled: {rule_data.get('enabled')}")
                        print(f"  Conditions: {rule_data.get('conditions', {})}")
        
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_profile_loading()
