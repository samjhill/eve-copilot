"""
Event definitions for EVE Copilot - defines game events and their structure
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from datetime import datetime


class EventType(Enum):
    """EVE Online event types that can be detected from logs."""
    
    # Combat events
    INCOMING_DAMAGE = "IncomingDamage"
    OUTGOING_DAMAGE = "OutgoingDamage"
    DRONE_HIT = "DroneHit"
    DRONE_DESTROYED = "DroneDestroyed"
    
    # E-war events
    WARP_SCRAMBLE = "WarpScramble"
    WEB_EFFECT = "WebEffect"
    ENERGY_NEUTRALIZATION = "EnergyNeutralization"
    ROOM_CLEARED_MISS = "RoomClearedMiss"
    
    # Equipment events
    MODULE_ACTIVATION = "ModuleActivation"
    RELOAD_REQUIRED = "ReloadRequired"
    CHARGES_DEPLETED = "ChargesDepleted"
    
    # Status events
    SHIELD_STATUS = "ShieldStatus"
    CAPACITOR_STATUS = "CapacitorStatus"
    
    # Game events
    SPATIAL_PHENOMENA = "SpatialPhenomena"
    WAVE_TRANSITION = "WaveTransition"
    CARGO_APPROACH = "CargoApproach"
    ABYSS_ENTRY = "AbyssEntry"
    
    # Navigation events
    WARP_START = "WarpStart"
    WARP_END = "WarpEnd"
    DOCK_REQUEST = "DockRequest"
    UNDOCK_REQUEST = "UndockRequest"
    DOCKED = "Docked"
    UNDOCKED = "Undocked"
    JUMP_GATE = "JumpGate"
    JUMP_WORMHOLE = "JumpWormhole"
    
    # Fleet events
    FLEET_JOIN = "FleetJoin"
    FLEET_LEAVE = "FleetLeave"
    FLEET_WARP = "FleetWarp"
    FLEET_BROADCAST = "FleetBroadcast"
    
    # Market events
    MARKET_ORDER = "MarketOrder"
    CONTRACT_OFFER = "ContractOffer"
    CONTRACT_ACCEPTED = "ContractAccepted"
    
    # Industry events
    MANUFACTURING_START = "ManufacturingStart"
    MANUFACTURING_COMPLETE = "ManufacturingComplete"
    RESEARCH_START = "ResearchStart"
    RESEARCH_COMPLETE = "ResearchComplete"
    
    # Chat events
    LOCAL_CHAT = "LocalChat"
    FLEET_CHAT = "FleetChat"
    CORP_CHAT = "CorpChat"
    ALLIANCE_CHAT = "AllianceChat"
    
    # Legacy event types (for backward compatibility)
    YOU_SCRAMMED = "YouScrammed"
    YOU_WEBBED = "YouWebbed"
    YOU_NEUTED = "YouNeuted"
    SHIELD_LOW = "ShieldLow"
    CAP_LOW = "CapLow"
    MODULE_ACTIVATED = "ModuleActivated"
    MODULE_DEACTIVATED = "ModuleDeactivated"
    MODULE_LOADING = "ModuleLoading"
    WAVE_TRANSITION_WAIT = "WaveTransitionWait"


@dataclass
class GameEvent:
    """Normalized game event from EVE log parsing."""
    
    type: EventType
    timestamp: datetime
    subject: str
    meta: Dict[str, Any] = field(default_factory=dict)
    raw_line: Optional[str] = None
    source_file: Optional[str] = None
    priority: int = 1  # 0=highest (safety), 1=normal, 2=lowest (info)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp must be a datetime object")
        
        if not isinstance(self.type, EventType):
            raise ValueError("type must be an EventType enum value")
        
        if not isinstance(self.subject, str) or not self.subject.strip():
            raise ValueError("subject must be a non-empty string")
        
        if not isinstance(self.meta, dict):
            raise ValueError("meta must be a dictionary")
        
        if self.priority not in (0, 1, 2):
            raise ValueError("priority must be 0, 1, or 2")
        
        # Set priority based on event type if not specified
        if self.priority == 1:  # Default priority
            self.priority = self._get_default_priority()
    
    def _get_default_priority(self) -> int:
        """Get default priority based on event type.
        
        Returns:
            Priority level (0=highest, 1=normal, 2=lowest)
        """
        high_priority_types = {
            EventType.SHIELD_STATUS,
            EventType.CAPACITOR_STATUS,
            EventType.WARP_SCRAMBLE,
            EventType.INCOMING_DAMAGE
        }
        
        low_priority_types = {
            EventType.MODULE_ACTIVATION,
            EventType.CARGO_APPROACH,
            EventType.WAVE_TRANSITION
        }
        
        if self.type in high_priority_types:
            return 0
        elif self.type in low_priority_types:
            return 2
        else:
            return 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation.
        
        Returns:
            Dictionary representation of the event
        """
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "subject": self.subject,
            "meta": self.meta,
            "raw_line": self.raw_line,
            "source_file": self.source_file,
            "priority": self.priority
        }
    
    def to_json(self) -> Dict[str, Any]:
        """Convert event to JSON-serializable dictionary.
        
        Returns:
            JSON-serializable dictionary
        """
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "subject": self.subject,
            "meta": self.meta,
            "priority": self.priority
        }
    
    def __str__(self) -> str:
        """String representation of the event."""
        meta_str = ", ".join([f"{k}={v}" for k, v in self.meta.items()])
        return f"{self.type.value}({self.subject}, {meta_str})"
    
    def __repr__(self) -> str:
        """Detailed representation of the event."""
        return (f"GameEvent(type={self.type}, subject='{self.subject}', "
                f"priority={self.priority}, meta={self.meta})")
    
    def is_high_priority(self) -> bool:
        """Check if event is high priority.
        
        Returns:
            True if event is high priority
        """
        return self.priority == 0
    
    def is_low_priority(self) -> bool:
        """Check if event is low priority.
        
        Returns:
            True if event is low priority
        """
        return self.priority == 2
    
    def get_meta_value(self, key: str, default: Any = None) -> Any:
        """Get metadata value with optional default.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.meta.get(key, default)
    
    def has_meta_key(self, key: str) -> bool:
        """Check if metadata key exists.
        
        Args:
            key: Metadata key to check
            
        Returns:
            True if key exists
        """
        return key in self.meta


# Event factory functions for common event types
def create_damage_event(event_type: EventType, damage: int, entity: str, 
                       timestamp: datetime, damage_type: str = "Kinetic",
                       raw_line: Optional[str] = None, 
                       source_file: Optional[str] = None) -> GameEvent:
    """Create a damage event.
    
    Args:
        event_type: Type of damage event
        damage: Damage amount
        entity: Target or source entity
        timestamp: Event timestamp
        damage_type: Type of damage
        raw_line: Original log line
        source_file: Source file path
        
    Returns:
        GameEvent instance
    """
    if event_type not in (EventType.INCOMING_DAMAGE, EventType.OUTGOING_DAMAGE):
        raise ValueError("event_type must be INCOMING_DAMAGE or OUTGOING_DAMAGE")
    
    return GameEvent(
        type=event_type,
        timestamp=timestamp,
        subject=entity,
        meta={
            "damage": damage,
            "damage_type": damage_type
        },
        raw_line=raw_line,
        source_file=source_file
    )


def create_drone_event(event_type: EventType, drone_name: str, timestamp: datetime,
                      damage: Optional[int] = None, damage_type: str = "Kinetic",
                      from_entity: Optional[str] = None, raw_line: Optional[str] = None,
                      source_file: Optional[str] = None) -> GameEvent:
    """Create a drone-related event.
    
    Args:
        event_type: Type of drone event
        drone_name: Name of the drone
        timestamp: Event timestamp
        damage: Damage amount (for hit events)
        damage_type: Type of damage
        from_entity: Entity that caused the event
        raw_line: Original log line
        source_file: Source file path
        
    Returns:
        GameEvent instance
    """
    if event_type not in (EventType.DRONE_HIT, EventType.DRONE_DESTROYED):
        raise ValueError("event_type must be DRONE_HIT or DRONE_DESTROYED")
    
    meta = {}
    if damage is not None:
        meta["damage"] = damage
        meta["damage_type"] = damage_type
    if from_entity:
        meta["from_entity"] = from_entity
    
    return GameEvent(
        type=event_type,
        timestamp=timestamp,
        subject=drone_name,
        meta=meta,
        raw_line=raw_line,
        source_file=source_file
    )


def create_status_event(event_type: EventType, value: Union[int, float], 
                       timestamp: datetime, raw_line: Optional[str] = None,
                       source_file: Optional[str] = None) -> GameEvent:
    """Create a status event (shield, capacitor, etc.).
    
    Args:
        event_type: Type of status event
        value: Status value
        timestamp: Event timestamp
        raw_line: Original log line
        source_file: Source file path
        
    Returns:
        GameEvent instance
    """
    if event_type not in (EventType.SHIELD_STATUS, EventType.CAPACITOR_STATUS):
        raise ValueError("event_type must be SHIELD_STATUS or CAPACITOR_STATUS")
    
    # Determine priority based on value
    priority = 1  # Default
    if event_type == EventType.SHIELD_STATUS and value < 30:
        priority = 0  # High priority for low shield
    elif event_type == EventType.CAPACITOR_STATUS and value < 20:
        priority = 0  # High priority for low capacitor
    
    return GameEvent(
        type=event_type,
        timestamp=timestamp,
        subject=f"{event_type.value.replace('_', ' ').title()}",
        meta={
            "value": value,
            "unit": "percent"
        },
        raw_line=raw_line,
        source_file=source_file,
        priority=priority
    )


def create_ewar_event(event_type: EventType, by_entity: str, timestamp: datetime,
                     raw_line: Optional[str] = None, 
                     source_file: Optional[str] = None) -> GameEvent:
    """Create an e-war event.
    
    Args:
        event_type: Type of e-war event
        by_entity: Entity that applied the effect
        timestamp: Event timestamp
        raw_line: Original log line
        source_file: Source file path
        
    Returns:
        GameEvent instance
    """
    ewar_types = {
        EventType.WARP_SCRAMBLE,
        EventType.WEB_EFFECT,
        EventType.ENERGY_NEUTRALIZATION
    }
    
    if event_type not in ewar_types:
        raise ValueError(f"event_type must be one of {ewar_types}")
    
    return GameEvent(
        type=event_type,
        timestamp=timestamp,
        subject=by_entity,
        meta={
            "effect": event_type.value.lower().replace('_', ' ')
        },
        raw_line=raw_line,
        source_file=source_file,
        priority=0  # E-war events are high priority
    )

