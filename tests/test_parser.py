"""
Unit tests for EVE Copilot log parser
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import evetalk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evetalk.parse import LogParser
from evetalk.events import EventType


class TestLogParser:
    """Test cases for LogParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LogParser()
    
    def test_parse_drone_hit(self):
        """Test parsing drone hit events."""
        line = "2025.01.28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik"
        event = self.parser.parse_line(line)
        
        assert event is not None
        assert event.type == EventType.DRONE_HIT
        assert event.subject == "Hobgoblin II"
        assert event.meta["from"] == "Damavik"
        assert event.meta["amount"] == 62
        assert event.meta["damageType"] == "Thermal"
        assert event.raw_line == line
    
    def test_parse_you_scrammed(self):
        """Test parsing 'you are scrambled' events."""
        line = "2025.01.28 14:30:19	You are warp scrambled by Damavik"
        event = self.parser.parse_line(line)
        
        assert event is not None
        assert event.type == EventType.YOU_SCRAMMED
        assert event.subject == "Damavik"
        assert event.meta["effect"] == "warp_scrambled"
        assert event.raw_line == line
    
    def test_parse_reload_required(self):
        """Test parsing reload required events."""
        line = "2025.01.28 14:30:23	Shield Booster requires reload"
        event = self.parser.parse_line(line)
        
        assert event is not None
        assert event.type == EventType.RELOAD_REQUIRED
        assert event.subject == "Shield Booster"
        assert event.meta["action"] == "reload_needed"
        assert event.raw_line == line
    
    def test_parse_incoming_damage(self):
        """Test parsing incoming damage events."""
        line = "2025.01.28 14:30:15	You take 45 Thermal damage from Damavik"
        event = self.parser.parse_line(line)
        
        assert event is not None
        assert event.type == EventType.INCOMING_DAMAGE
        assert event.subject == "Damavik"
        assert event.meta["amount"] == 45
        assert event.meta["damageType"] == "Thermal"
        assert event.raw_line == line
    
    def test_parse_timestamp_formats(self):
        """Test parsing different timestamp formats."""
        # Test EVE format (YYYY.MM.DD HH:MM:SS)
        line1 = "2025.01.28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik"
        event1 = self.parser.parse_line(line1)
        assert event1 is not None
        assert isinstance(event1.timestamp, datetime)
        
        # Test alternative format (YYYY-MM-DD HH:MM:SS)
        line2 = "2025-01-28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik"
        event2 = self.parser.parse_line(line2)
        assert event2 is not None
        assert isinstance(event2.timestamp, datetime)
    
    def test_parse_invalid_line(self):
        """Test parsing invalid or non-matching lines."""
        # Empty line
        assert self.parser.parse_line("") is None
        
        # Non-matching line
        assert self.parser.parse_line("This is not an EVE log line") is None
        
        # Line with wrong format
        assert self.parser.parse_line("Invalid timestamp format") is None
    
    def test_parse_file(self):
        """Test parsing an entire file."""
        # Create a temporary test file
        test_lines = [
            "2025.01.28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik",
            "2025.01.28 14:30:19	You are warp scrambled by Damavik",
            "2025.01.28 14:30:23	Shield Booster requires reload",
            "2025.01.28 14:30:15	You take 45 Thermal damage from Damavik"
        ]
        
        test_file = Path("test_log.txt")
        try:
            with open(test_file, 'w') as f:
                for line in test_lines:
                    f.write(line + '\n')
            
            # Parse the file
            events = self.parser.parse_file(test_file)
            
            # Check results
            assert len(events) == 4
            assert events[0].type == EventType.DRONE_HIT
            assert events[1].type == EventType.YOU_SCRAMMED
            assert events[2].type == EventType.RELOAD_REQUIRED
            assert events[3].type == EventType.INCOMING_DAMAGE
            
        finally:
            # Clean up
            if test_file.exists():
                test_file.unlink()
    
    def test_default_patterns(self):
        """Test that default patterns are loaded when no file exists."""
        # Create parser with non-existent patterns file
        parser = LogParser("non_existent_patterns.yml")
        
        # Should still have default patterns
        assert len(parser.compiled_patterns) > 0
        
        # Test that default patterns work
        line = "2025.01.28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik"
        event = parser.parse_line(line)
        assert event is not None
        assert event.type == EventType.DRONE_HIT


class TestEventCreation:
    """Test event creation from parsed data."""
    
    def test_drone_hit_event_creation(self):
        """Test creating drone hit events from regex matches."""
        from evetalk.parse import LogParser
        
        parser = LogParser()
        line = "2025.01.28 14:30:16	Your Hobgoblin II has taken 62 Thermal damage from Damavik"
        event = parser.parse_line(line)
        
        assert event is not None
        assert event.type == EventType.DRONE_HIT
        assert event.subject == "Hobgoblin II"
        assert event.meta["from"] == "Damavik"
        assert event.meta["amount"] == 62
        assert event.meta["damageType"] == "Thermal"
    
    def test_event_metadata(self):
        """Test that event metadata is correctly extracted."""
        parser = LogParser()
        line = "2025.01.28 14:30:15	You take 45 Thermal damage from Damavik"
        event = parser.parse_line(line)
        
        assert event is not None
        assert event.meta["amount"] == 45
        assert event.meta["damageType"] == "Thermal"
        assert event.meta["from"] == "Damavik"


if __name__ == "__main__":
    pytest.main([__file__])
