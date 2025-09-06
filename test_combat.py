#!/usr/bin/env python3
"""
Test Combat Damage Parsing
"""

import sys
from pathlib import Path

from evetalk.parse import LogParser

def test_combat_lines():
    """Test parsing specific combat damage lines."""
    print("Testing Combat Damage Parsing")
    print("=" * 50)
    
    # Initialize parser
    parser = LogParser("config/patterns/core.yml")
    
    # Test specific combat lines from your log
    test_lines = [
        # Incoming damage
        '[ 2025.08.28 13:20:54 ] (combat) <color=0xffcc0000><b>18</b> <color=0x77ffffff><font size=10>from</font> <b><color=0xffffffff>Striking Damavik</b><font size=10><color=0x77ffffff> - Hits',
        '[ 2025.08.28 13:20:54 ] (combat) <color=0xffcc0000><b>27</b> <color=0x77ffffff><font size=10>from</font> <b><color=0xffffffff>Striking Damavik</b><font size=10><color=0x77ffffff> - Smashes',
        '[ 2025.08.28 13:20:57 ] (combat) <color=0xffcc0000><b>28</b> <color=0x77ffffff><font size=10>from</font> <b><color=0xffffffff>Striking Damavik</b><font size=10><color=0x77ffffff> - Penetrates',
        
        # Outgoing damage
        '[ 2025.08.28 13:20:10 ] (combat) <color=0xff00ffff><b>1051</b> <color=0x77ffffff><font size=10>to</font> <b><color=0xffffffff>Sparkneedle Tessella</b><font size=10><color=0x77ffffff> - Inferno Fury Light Missile - Hits',
        '[ 2025.08.28 13:20:13 ] (combat) <color=0xff00ffff><b>99</b> <color=0x77ffffff><font size=10>to</font> <b><color=0xffffffff>Sparkneedle Tessella</b><font size=10><color=0x77ffffff> - Inferno Fury Light Missile - Hits',
    ]
    
    print(f"Testing {len(test_lines)} combat lines...")
    
    for i, line in enumerate(test_lines, 1):
        print(f"\nLine {i}: {line[:80]}...")
        
        # Try to parse the line
        event = parser.parse_line(line, "test.log")
        if event:
            print(f"  ✅ Parsed: {event.type.value}")
            print(f"  Subject: {event.subject}")
            print(f"  Meta: {event.meta}")
        else:
            print(f"  ❌ No event parsed")
    
    print(f"\n✅ Combat parsing test completed!")

if __name__ == '__main__':
    test_combat_lines()

