"""
Unit tests for EVE Copilot events module
"""

import pytest
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import evetalk
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evetalk.events import (
    GameEvent, EventType, create_drone_hit, create_you_scrammed,
    create_reload_required, create_incoming_damage
)


class TestEventType:
    """Test EventType enum."""
    
    def test_event_types_exist(self):
        """Test that all expected event types exist."""
        expected_types = [
            "DRONE_HIT", "DRONE_DESTROYED", "INCOMING_DAMAGE", "OUTGOING_DAMAGE",
            "YOU_SCRAMMED", "YOU_WEBBED", "YOU_NEUTED", "CAP_NEUTRALIZED",
            "RELOAD_REQUIRED", "CHARGES_DEPLETED", "MODULE_ACTIVATED", "MODULE_DEACTIVATED",
            "SHIELD_LOW", "ARMOR_LOW", "CAP_LOW", "OVERHEAT_WARNING"
        ]
        
        for expected_type in expected_types:
            assert hasattr(EventType, expected_type)
            assert getattr(EventType, expected_type).value == expected_type


class TestGameEvent:
    """Test GameEvent class."""
    
    def test_valid_event_creation(self):
        """Test creating a valid GameEvent."""
        timestamp = datetime.now()
        event = GameEvent(
            type=EventType.DRONE_HIT,
            timestamp=timestamp,
            subject="Hobgoblin II",
            meta={"from": "Damavik", "amount": 62},
            raw_line="test line"
        )
        
        assert event.type == EventType.DRONE_HIT
        assert event.timestamp == timestamp
        assert event.subject == "Hobgoblin II"
        assert event.meta["from"] == "Damavik"
        assert event.meta["amount"] == 62
        assert event.raw_line == "test line"
    
    def test_invalid_timestamp(self):
        """Test that invalid timestamp raises error."""
        with pytest.raises(ValueError, match="timestamp must be a datetime object"):
            GameEvent(
                type=EventType.DRONE_HIT,
                timestamp="invalid timestamp",
                subject="test",
                meta={}
            )
    
    def test_invalid_event_type(self):
        """Test that invalid event type raises error."""
        with pytest.raises(ValueError, match="type must be an EventType enum value"):
            GameEvent(
                type="INVALID_TYPE",
                timestamp=datetime.now(),
                subject="test",
                meta={}
            )
    
    def test_default_meta(self):
        """Test that meta defaults to empty dict."""
        event = GameEvent(
            type=EventType.DRONE_HIT,
            timestamp=datetime.now(),
            subject="test"
        )
        
        assert event.meta == {}
        assert event.raw_line is None
        assert event.source_file is None
    
    def test_to_dict(self):
        """Test converting event to dictionary."""
        timestamp = datetime(2025, 1, 28, 14, 30, 16)
        event = GameEvent(
            type=EventType.DRONE_HIT,
            timestamp=timestamp,
            subject="Hobgoblin II",
            meta={"from": "Damavik", "amount": 62},
            raw_line="test line",
            source_file="test.txt"
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["type"] == "DroneHit"
        assert event_dict["ts"] == "2025-01-28T14:30:16"
        assert event_dict["subject"] == "Hobgoblin II"
        assert event_dict["meta"]["from"] == "Damavik"
        assert event_dict["meta"]["amount"] == 62
        assert event_dict["raw_line"] == "test line"
        assert event_dict["source_file"] == "test.txt"
    
    def test_str_representation(self):
        """Test string representation of event."""
        event = GameEvent(
            type=EventType.DRONE_HIT,
            timestamp=datetime.now(),
            subject="Hobgoblin II",
            meta={"from": "Damavik", "amount": 62}
        )
        
        str_repr = str(event)
        assert "DroneHit" in str_repr
        assert "Hobgoblin II" in str_repr
        assert "from=Damavik" in str_repr
        assert "amount=62" in str_repr
    
    def test_repr_representation(self):
        """Test detailed representation of event."""
        event = GameEvent(
            type=EventType.DRONE_HIT,
            timestamp=datetime.now(),
            subject="Hobgoblin II",
            meta={"from": "Damavik"}
        )
        
        repr_str = repr(event)
        assert "GameEvent" in repr_str
        assert "type=EventType.DRONE_HIT" in repr_str
        assert "subject='Hobgoblin II'" in repr_str
        assert "meta={'from': 'Damavik'}" in repr_str


class TestEventFactories:
    """Test event factory functions."""
    
    def test_create_drone_hit(self):
        """Test creating drone hit event."""
        timestamp = datetime.now()
        event = create_drone_hit(
            drone_name="Hobgoblin II",
            damage=62,
            damage_type="Thermal",
            from_entity="Damavik",
            timestamp=timestamp,
            raw_line="test line"
        )
        
        assert event.type == EventType.DRONE_HIT
        assert event.timestamp == timestamp
        assert event.subject == "Hobgoblin II"
        assert event.meta["from"] == "Damavik"
        assert event.meta["amount"] == 62
        assert event.meta["damageType"] == "Thermal"
        assert event.raw_line == "test line"
    
    def test_create_you_scrammed(self):
        """Test creating 'you are scrambled' event."""
        timestamp = datetime.now()
        event = create_you_scrammed(
            entity="Damavik",
            timestamp=timestamp,
            raw_line="test line"
        )
        
        assert event.type == EventType.YOU_SCRAMMED
        assert event.timestamp == timestamp
        assert event.subject == "Damavik"
        assert event.meta["effect"] == "warp_scrambled"
        assert event.raw_line == "test line"
    
    def test_create_reload_required(self):
        """Test creating reload required event."""
        timestamp = datetime.now()
        event = create_reload_required(
            module="Shield Booster",
            timestamp=timestamp,
            raw_line="test line"
        )
        
        assert event.type == EventType.RELOAD_REQUIRED
        assert event.timestamp == timestamp
        assert event.subject == "Shield Booster"
        assert event.meta["action"] == "reload_needed"
        assert event.raw_line == "test line"
    
    def test_create_incoming_damage(self):
        """Test creating incoming damage event."""
        timestamp = datetime.now()
        event = create_incoming_damage(
            amount=45,
            damage_type="Thermal",
            from_entity="Damavik",
            timestamp=timestamp,
            raw_line="test line"
        )
        
        assert event.type == EventType.INCOMING_DAMAGE
        assert event.timestamp == timestamp
        assert event.subject == "Damavik"
        assert event.meta["amount"] == 45
        assert event.meta["damageType"] == "Thermal"
        assert event.raw_line == "test line"
    
    def test_factory_functions_defaults(self):
        """Test that factory functions work with minimal parameters."""
        timestamp = datetime.now()
        
        # Test drone hit with minimal params
        event1 = create_drone_hit(
            drone_name="Hobgoblin II",
            damage=62,
            damage_type="Thermal",
            from_entity="Damavik",
            timestamp=timestamp
        )
        assert event1.raw_line is None
        assert event1.source_file is None
        
        # Test you scrambled with minimal params
        event2 = create_you_scrammed(
            entity="Damavik",
            timestamp=timestamp
        )
        assert event2.raw_line is None
        assert event2.source_file is None


if __name__ == "__main__":
    pytest.main([__file__])
