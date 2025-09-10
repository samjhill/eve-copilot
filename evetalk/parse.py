"""
Log file parser for EVE Copilot - parses EVE Online log files using regex patterns.

This module handles the parsing of EVE Online combat logs, converting raw log lines
into structured GameEvent objects that can be processed by the rules engine.
Supports various event types including damage, energy neutralization, spatial phenomena,
and wave transitions.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import yaml

from .events import GameEvent, EventType

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Parser-related errors."""
    pass


class LogParser:
    """Parses EVE Online log files using regex patterns."""
    
    def __init__(self, patterns_file: Union[str, Path]):
        """Initialize parser with patterns from YAML file.
        
        Args:
            patterns_file: Path to patterns configuration file
            
        Raises:
            ParserError: If patterns cannot be loaded
        """
        self.patterns_file = Path(patterns_file)
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.compiled_patterns: Dict[str, re.Pattern] = {}
        self._load_patterns()
    
    def _load_patterns(self) -> None:
        """Load regex patterns from YAML file.
        
        Raises:
            ParserError: If patterns cannot be loaded
        """
        if not self.patterns_file.exists():
            raise ParserError(f"Patterns file not found: {self.patterns_file}")
        
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                self.patterns = yaml.safe_load(f)
            
            if not self.patterns:
                raise ParserError("Patterns file is empty or invalid")
            
            # Compile regex patterns
            self._compile_patterns()
            
            logger.info(f"Loaded {len(self.compiled_patterns)} patterns from {self.patterns_file}")
            
        except yaml.YAMLError as e:
            raise ParserError(f"Invalid YAML in patterns file: {e}")
        except Exception as e:
            raise ParserError(f"Failed to load patterns: {e}")
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns and validate them."""
        self.compiled_patterns.clear()
        
        for name, pattern_data in self.patterns.items():
            regex_str = pattern_data.get('regex', '')
            if not regex_str:
                logger.warning(f"Pattern '{name}' has no regex")
                continue
            
            try:
                self.compiled_patterns[name] = re.compile(regex_str)
                logger.debug(f"Compiled pattern '{name}': {regex_str}")
            except re.error as e:
                logger.error(f"Invalid regex for pattern '{name}': {e}")
                logger.error(f"Pattern: {regex_str}")
    
    def parse_line(self, raw_line: str, source_file: Optional[str] = None) -> Optional[GameEvent]:
        """Parse a single log line into a GameEvent.
        
        Args:
            raw_line: Raw log line to parse
            source_file: Optional source file name for tracking
            
        Returns:
            GameEvent if parsing successful, None otherwise
        """
        if not raw_line or not raw_line.strip():
            return None
        
        # Try each pattern
        for name, pattern in self.compiled_patterns.items():
            match = pattern.match(raw_line)
            if match:
                try:
                    return self._create_event_from_match(name, match, raw_line, source_file)
                except Exception as e:
                    logger.error(f"Error creating event from pattern '{name}': {e}")
                    logger.error(f"Raw line: {raw_line}")
                    continue
        
        return None
    
    def _create_event_from_match(self, pattern_name: str, match: re.Match, 
                                raw_line: str, source_file: Optional[str]) -> Optional[GameEvent]:
        """Create a GameEvent from a regex match.
        
        Args:
            pattern_name: Name of the pattern that matched
            match: Regex match object
            raw_line: Original raw log line
            source_file: Source file name
            
        Returns:
            GameEvent if creation successful, None otherwise
            
        Raises:
            ParserError: If event creation fails
        """
        pattern_data = self.patterns[pattern_name]
        event_type_str = pattern_data.get('event_type')
        
        if not event_type_str:
            logger.warning(f"Pattern '{pattern_name}' has no event_type")
            return None
        
        try:
            # Parse timestamp
            timestamp = self._parse_timestamp(match, pattern_data)
            if not timestamp:
                return None
            
            # Create event based on type
            event = self._create_event_by_type(
                event_type_str, pattern_data, match, timestamp, raw_line, source_file
            )
            
            if event:
                logger.debug(f"Created event: {event.type.value} from pattern '{pattern_name}'")
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to create event from pattern '{pattern_name}': {e}")
            return None
    
    def _parse_timestamp(self, match: re.Match, pattern_data: Dict[str, Any]) -> Optional[datetime]:
        """Parse timestamp from regex match.
        
        Args:
            match: Regex match object
            pattern_data: Pattern configuration data
            
        Returns:
            Parsed datetime or None if parsing fails
        """
        groups = match.groups()
        if not groups:
            logger.warning("No groups in regex match for timestamp parsing")
            return None
        
        timestamp_str = groups[0]
        if not timestamp_str:
            return None
        
        try:
            # Handle different timestamp formats
            timestamp_str = timestamp_str.strip()
            
            # Try the new EVE format: [ 2025.08.28 12:36:45 ]
            if timestamp_str.startswith('[') and timestamp_str.endswith(']'):
                timestamp_str = timestamp_str.strip('[] ').strip()
            
            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, '%Y.%m.%d %H:%M:%S')
            return timestamp
            
        except ValueError as e:
            logger.error(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None
    
    def _create_event_by_type(self, event_type: str, pattern_data: Dict[str, Any], 
                             match: re.Match, timestamp: datetime, raw_line: str, 
                             source_file: Optional[str]) -> Optional[GameEvent]:
        """Create event based on event type.
        
        Args:
            event_type: Type of event to create
            pattern_data: Pattern configuration data
            match: Regex match object
            timestamp: Parsed timestamp
            raw_line: Original raw log line
            source_file: Source file name
            
        Returns:
            GameEvent if creation successful, None otherwise
        """
        groups = match.groups()
        
        try:
            if event_type == "SPATIAL_PHENOMENA":
                return self._create_spatial_phenomena_event(timestamp, raw_line, source_file)
            elif event_type == "WAVE_TRANSITION_WAIT":
                return self._create_wave_transition_wait_event(timestamp, raw_line, source_file)
            elif event_type == "ABYSS_ENTRY":
                return self._create_abyss_entry_event(timestamp, raw_line, source_file)
            elif event_type == "INCOMING_DAMAGE":
                return self._create_incoming_damage_event(groups, timestamp, raw_line, source_file)
            elif event_type == "OUTGOING_DAMAGE":
                return self._create_outgoing_damage_event(groups, timestamp, raw_line, source_file)
            elif event_type == "DRONE_HIT":
                return self._create_drone_hit_event(groups, timestamp, raw_line, source_file)
            elif event_type == "WARP_SCRAMBLE":
                return self._create_warp_scramble_event(groups, timestamp, raw_line, source_file)
            elif event_type == "WEB_EFFECT":
                return self._create_web_effect_event(groups, timestamp, raw_line, source_file)
            elif event_type == "ENERGY_NEUTRALIZATION":
                return self._create_energy_neutralization_event(groups, timestamp, raw_line, source_file)
            elif event_type == "ROOM_CLEARED_MISS":
                return self._create_room_cleared_miss_event(groups, timestamp, raw_line, source_file)
            elif event_type == "MODULE_ACTIVATION":
                return self._create_module_activation_event(groups, timestamp, raw_line, source_file)
            elif event_type == "RELOAD_REQUIRED":
                return self._create_reload_required_event(groups, timestamp, raw_line, source_file)
            elif event_type == "SHIELD_STATUS":
                return self._create_shield_status_event(groups, timestamp, raw_line, source_file)
            elif event_type == "CAPACITOR_STATUS":
                return self._create_capacitor_status_event(groups, timestamp, raw_line, source_file)
            elif event_type == "MISSILE_RELOAD_COMPLETE":
                return self._create_missile_reload_complete_event(groups, timestamp, raw_line, source_file)
            elif event_type == "MODULE_ACTIVATED":
                return self._create_module_activated_event(groups, timestamp, raw_line, source_file)
            elif event_type == "MODULE_DEACTIVATED":
                return self._create_module_deactivated_event(groups, timestamp, raw_line, source_file)
            elif event_type == "CHARGES_DEPLETED":
                return self._create_charges_depleted_event(groups, timestamp, raw_line, source_file)
            elif event_type == "MODULE_LOADING":
                return self._create_module_loading_event(groups, timestamp, raw_line, source_file)
            elif event_type == "CARGO_APPROACH":
                return self._create_cargo_approach_event(groups, timestamp, raw_line, source_file)
            # Boss events
            elif event_type == "KARYBDIS_TYRANNOS_DETECTED":
                return self._create_karybdis_tyrannos_detected_event(groups, timestamp, raw_line, source_file)
            elif event_type == "KARYBDIS_TYRANNOS_OUTGOING":
                return self._create_karybdis_tyrannos_outgoing_event(groups, timestamp, raw_line, source_file)
            # Navigation events
            elif event_type in ["WARP_START", "WARP_END", "DOCK_REQUEST", "UNDOCK_REQUEST", 
                               "DOCKED", "UNDOCKED", "JUMP_GATE", "JUMP_WORMHOLE"]:
                event_type_enum = EventType(event_type)
                return self._create_navigation_event(event_type_enum, groups, timestamp, raw_line, source_file)
            # Fleet events
            elif event_type in ["FLEET_JOIN", "FLEET_LEAVE", "FLEET_WARP", "FLEET_BROADCAST"]:
                event_type_enum = EventType(event_type)
                return self._create_fleet_event(event_type_enum, groups, timestamp, raw_line, source_file)
            # Chat events
            elif event_type in ["LOCAL_CHAT", "FLEET_CHAT", "CORP_CHAT", "ALLIANCE_CHAT"]:
                event_type_enum = EventType(event_type)
                return self._create_chat_event(event_type_enum, groups, timestamp, raw_line, source_file)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create {event_type} event: {e}")
            return None
    
    def _create_spatial_phenomena_event(self, timestamp: datetime, raw_line: str, 
                                      source_file: Optional[str]) -> GameEvent:
        """Create spatial phenomena event."""
        return GameEvent(
            type=EventType.SPATIAL_PHENOMENA,
            timestamp=timestamp,
            subject="Abyssal Effect",
            meta={"effect": "spatial_phenomena"},
            raw_line=raw_line,
            source_file=source_file
        )

    def _create_abyss_entry_event(self, timestamp: datetime, raw_line: str, 
                                source_file: Optional[str]) -> GameEvent:
        """Create abyss entry event."""
        return GameEvent(
            type=EventType.ABYSS_ENTRY,
            timestamp=timestamp,
            subject="Abyssal Deadspace",
            meta={"effect": "abyss_entry"},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_wave_transition_wait_event(self, timestamp: datetime, raw_line: str,
                                         source_file: Optional[str]) -> GameEvent:
        """Create wave transition wait event."""
        return GameEvent(
            type=EventType.WAVE_TRANSITION_WAIT,
            timestamp=timestamp,
            subject="Wave Transition",
            meta={"effect": "wave_transition"},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_navigation_event(self, event_type: EventType, groups: tuple, timestamp: datetime,
                                raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create navigation event (warp, dock, undock, etc.)."""
        if len(groups) < 1:
            logger.warning(f"Insufficient groups for navigation event: {len(groups)}")
            return None
        
        # Extract destination/station name if available
        destination = groups[1] if len(groups) > 1 else "Unknown"
        
        return GameEvent(
            type=event_type,
            timestamp=timestamp,
            subject=destination,
            meta={"destination": destination},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_fleet_event(self, event_type: EventType, groups: tuple, timestamp: datetime,
                           raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create fleet event."""
        if len(groups) < 1:
            logger.warning(f"Insufficient groups for fleet event: {len(groups)}")
            return None
        
        # Extract destination if available (for fleet warp)
        destination = groups[1] if len(groups) > 1 else None
        
        meta = {}
        if destination:
            meta["destination"] = destination
        
        return GameEvent(
            type=event_type,
            timestamp=timestamp,
            subject="Fleet",
            meta=meta,
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_chat_event(self, event_type: EventType, groups: tuple, timestamp: datetime,
                          raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create chat event."""
        if len(groups) < 3:
            logger.warning(f"Insufficient groups for chat event: {len(groups)}")
            return None
        
        sender = groups[1]
        message = groups[2]
        
        return GameEvent(
            type=event_type,
            timestamp=timestamp,
            subject=sender,
            meta={
                "sender": sender,
                "message": message,
                "channel": event_type.value.lower().replace('_', ' ')
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=2  # Chat events are low priority
        )
    
    def _create_incoming_damage_event(self, groups: tuple, timestamp: datetime, 
                                    raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create incoming damage event."""
        if len(groups) < 4:
            logger.warning(f"Insufficient groups for incoming damage: {len(groups)}")
            return None
        
        damage = int(groups[1]) if groups[1] else 0
        from_entity = groups[2] if len(groups) > 2 else "Unknown"
        damage_type = groups[3] if len(groups) > 3 else "Hits"
        
        return GameEvent(
            type=EventType.INCOMING_DAMAGE,
            timestamp=timestamp,
            subject=from_entity,
            meta={
                "damage": damage,
                "damage_type": damage_type
            },
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_outgoing_damage_event(self, groups: tuple, timestamp: datetime, 
                                    raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create outgoing damage event."""
        if len(groups) < 4:
            logger.warning(f"Insufficient groups for outgoing damage: {len(groups)}")
            return None
        
        damage = int(groups[1]) if groups[1] else 0
        to_entity = groups[2] if len(groups) > 2 else "Unknown"
        damage_type = groups[3] if len(groups) > 3 else "Hits"
        
        return GameEvent(
            type=EventType.OUTGOING_DAMAGE,
            timestamp=timestamp,
            subject=to_entity,
            meta={
                "damage": damage,
                "damage_type": damage_type
            },
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_drone_hit_event(self, groups: tuple, timestamp: datetime, 
                               raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create drone hit event."""
        if len(groups) < 5:
            logger.warning(f"Insufficient groups for drone hit: {len(groups)}")
            return None

        # Handle both old and new pattern formats
        if len(groups) == 5:
            # New pattern: timestamp, damage, target, drone_type, hit_type
            damage = int(groups[1]) if groups[1] else 0
            target = groups[2] if len(groups) > 2 else "Unknown"
            drone_type = groups[3] if len(groups) > 3 else "Unknown Drone"
            hit_type = groups[4] if len(groups) > 4 else "Hits"
            
            return GameEvent(
                type=EventType.DRONE_HIT,
                timestamp=timestamp,
                subject=drone_type,
                meta={
                    "damage": damage,
                    "target": target,
                    "drone_type": drone_type,
                    "hit_type": hit_type,
                    "status": "dealing_damage"
                },
                raw_line=raw_line,
                source_file=source_file,
                priority=1  # Medium priority - tactical reminder
            )
        else:
            # Old pattern: timestamp, drone_name, damage, damage_type, from_entity
            drone_name = groups[1] if len(groups) > 1 else "Unknown"
            damage = int(groups[2]) if len(groups) > 2 and groups[2] else 0
            damage_type = groups[3] if len(groups) > 3 else "Kinetic"
            from_entity = groups[4] if len(groups) > 4 else "Unknown"

            return GameEvent(
                type=EventType.DRONE_HIT,
                timestamp=timestamp,
                subject=drone_name,
                meta={
                    "damage": damage,
                    "damage_type": damage_type,
                    "from_entity": from_entity
                },
                raw_line=raw_line,
                source_file=source_file
            )
    
    def _create_warp_scramble_event(self, groups: tuple, timestamp: datetime, 
                                   raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create warp scramble event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for warp scramble: {len(groups)}")
            return None
        
        by_entity = groups[1] if len(groups) > 1 else "Unknown"
        
        return GameEvent(
            type=EventType.WARP_SCRAMBLE,
            timestamp=timestamp,
            subject=by_entity,
            meta={"effect": "warp_scramble"},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_web_effect_event(self, groups: tuple, timestamp: datetime, 
                                raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create web effect event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for web effect: {len(groups)}")
            return None
        
        by_entity = groups[1] if len(groups) > 1 else "Unknown"
        
        return GameEvent(
            type=EventType.WEB_EFFECT,
            timestamp=timestamp,
            subject=by_entity,
            meta={"effect": "web_effect"},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_energy_neutralization_event(self, groups: tuple, timestamp: datetime, 
                                          raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create energy neutralization event."""
        if len(groups) < 3:
            logger.warning(f"Insufficient groups for energy neutralization: {len(groups)}")
            return None
        
        amount = int(groups[1]) if groups[1] else 0
        from_entity = groups[2] if len(groups) > 2 else "Unknown"
        
        return GameEvent(
            type=EventType.ENERGY_NEUTRALIZATION,
            timestamp=timestamp,
            subject=from_entity,
            meta={"amount": amount, "from_entity": from_entity},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_module_activation_event(self, groups: tuple, timestamp: datetime, 
                                      raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create module activation event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for module activation: {len(groups)}")
            return None
        
        module_name = groups[1] if len(groups) > 1 else "Unknown"
        
        return GameEvent(
            type=EventType.MODULE_ACTIVATION,
            timestamp=timestamp,
            subject=module_name,
            meta={"module": module_name},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_reload_required_event(self, groups: tuple, timestamp: datetime, 
                                    raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create reload required event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for reload required: {len(groups)}")
            return None
        
        weapon_name = groups[1] if len(groups) > 1 else "Unknown"
        
        return GameEvent(
            type=EventType.RELOAD_REQUIRED,
            timestamp=timestamp,
            subject=weapon_name,
            meta={"weapon": weapon_name},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_shield_status_event(self, groups: tuple, timestamp: datetime, 
                                  raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create shield status event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for shield status: {len(groups)}")
            return None
        
        try:
            shield_percent = float(groups[1]) if groups[1] else 100.0
        except ValueError:
            shield_percent = 100.0
        
        return GameEvent(
            type=EventType.SHIELD_STATUS,
            timestamp=timestamp,
            subject="Shield Status",
            meta={"shield": shield_percent},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_capacitor_status_event(self, groups: tuple, timestamp: datetime, 
                                     raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create capacitor status event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for capacitor status: {len(groups)}")
            return None
        
        try:
            capacitor_percent = float(groups[1]) if groups[1] else 100.0
        except ValueError:
            capacitor_percent = 100.0
        
        return GameEvent(
            type=EventType.CAPACITOR_STATUS,
            timestamp=timestamp,
            subject="Capacitor Status",
            meta={"capacitor": capacitor_percent},
            raw_line=raw_line,
            source_file=source_file
        )
    
    def _create_missile_reload_complete_event(self, groups: tuple, timestamp: datetime, 
                                            raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create missile reload complete event."""
        if len(groups) < 5:
            logger.warning(f"Insufficient groups for missile reload complete: {len(groups)}")
            return None
        
        damage = int(groups[1]) if groups[1] else 0
        target = groups[2] if len(groups) > 2 else "Unknown Target"
        missile_type = groups[3] if len(groups) > 3 else "Unknown Missile"
        hit_type = groups[4] if len(groups) > 4 else "Hits"
        
        return GameEvent(
            type=EventType.MISSILE_RELOAD_COMPLETE,
            timestamp=timestamp,
            subject="Missile Launcher",
            meta={
                "damage": damage,
                "target": target,
                "missile_type": missile_type,
                "hit_type": hit_type,
                "status": "reloaded_and_firing"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=1  # Medium priority - tactical reminder
        )
    
    def _create_module_activated_event(self, groups: tuple, timestamp: datetime, 
                                     raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create module activated event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for module activated: {len(groups)}")
            return None
        
        module_name = groups[1] if len(groups) > 1 else "Unknown Module"
        
        return GameEvent(
            type=EventType.MODULE_ACTIVATED,
            timestamp=timestamp,
            subject=module_name,
            meta={
                "module": module_name,
                "status": "activated"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=2  # Low priority - informational
        )
    
    def _create_module_deactivated_event(self, groups: tuple, timestamp: datetime, 
                                       raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create module deactivated event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for module deactivated: {len(groups)}")
            return None
        
        module_name = groups[1] if len(groups) > 1 else "Unknown Module"
        
        return GameEvent(
            type=EventType.MODULE_DEACTIVATED,
            timestamp=timestamp,
            subject=module_name,
            meta={
                "module": module_name,
                "status": "deactivated"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=2  # Low priority - informational
        )
    
    def _create_charges_depleted_event(self, groups: tuple, timestamp: datetime, 
                                     raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create charges depleted event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for charges depleted: {len(groups)}")
            return None
        
        module_name = groups[1] if len(groups) > 1 else "Unknown Module"
        
        return GameEvent(
            type=EventType.CHARGES_DEPLETED,
            timestamp=timestamp,
            subject=module_name,
            meta={
                "module": module_name,
                "status": "charges_depleted"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=1  # Medium priority - tactical reminder
        )
    
    def _create_module_loading_event(self, groups: tuple, timestamp: datetime, 
                                   raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create module loading event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for module loading: {len(groups)}")
            return None
        
        module_name = groups[1] if len(groups) > 1 else "Unknown Module"
        
        return GameEvent(
            type=EventType.MODULE_LOADING,
            timestamp=timestamp,
            subject=module_name,
            meta={
                "module": module_name,
                "status": "loading"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=2  # Low priority - informational
        )
    
    def _create_cargo_approach_event(self, groups: tuple, timestamp: datetime, 
                                   raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create cargo approach event."""
        if len(groups) < 2:
            logger.warning(f"Insufficient groups for cargo approach: {len(groups)}")
            return None
        
        cargo_name = groups[1] if len(groups) > 1 else "Unknown Cargo"
        
        return GameEvent(
            type=EventType.CARGO_APPROACH,
            timestamp=timestamp,
            subject=cargo_name,
            meta={
                "cargo": cargo_name,
                "status": "approaching"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=2  # Low priority - informational
        )
    
    def reload_patterns(self) -> None:
        """Reload patterns from file."""
        try:
            self._load_patterns()
            logger.info("Patterns reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload patterns: {e}")
    
    def _create_karybdis_tyrannos_detected_event(self, groups: tuple, timestamp: datetime, 
                                               raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create Karybdis Tyrannos detected event."""
        if len(groups) < 3:
            logger.warning(f"Insufficient groups for Karybdis Tyrannos detected: {len(groups)}")
            return None
        
        damage = int(groups[1]) if groups[1] else 0
        damage_type = groups[2] if len(groups) > 2 else "Hits"
        
        return GameEvent(
            type=EventType.KARYBDIS_TYRANNOS_DETECTED,
            timestamp=timestamp,
            subject="Karybdis Tyrannos",
            meta={
                "damage": damage,
                "damage_type": damage_type,
                "boss_type": "Karybdis Tyrannos",
                "threat_level": "critical"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=0  # Highest priority - critical boss
        )
    
    def _create_karybdis_tyrannos_outgoing_event(self, groups: tuple, timestamp: datetime, 
                                               raw_line: str, source_file: Optional[str]) -> GameEvent:
        """Create Karybdis Tyrannos outgoing damage event."""
        if len(groups) < 3:
            logger.warning(f"Insufficient groups for Karybdis Tyrannos outgoing: {len(groups)}")
            return None
        
        damage = int(groups[1]) if groups[1] else 0
        damage_type = groups[2] if len(groups) > 2 else "Hits"
        
        return GameEvent(
            type=EventType.KARYBDIS_TYRANNOS_OUTGOING,
            timestamp=timestamp,
            subject="Karybdis Tyrannos",
            meta={
                "damage": damage,
                "damage_type": damage_type,
                "boss_type": "Karybdis Tyrannos",
                "threat_level": "critical"
            },
            raw_line=raw_line,
            source_file=source_file,
            priority=0  # Highest priority - critical boss
        )

    def get_pattern_info(self) -> Dict[str, Any]:
        """Get information about loaded patterns.
        
        Returns:
            Dictionary with pattern information
        """
        return {
            'patterns_file': str(self.patterns_file),
            'total_patterns': len(self.patterns),
            'compiled_patterns': len(self.compiled_patterns),
            'pattern_names': list(self.patterns.keys())
        }

