"""
Rules engine for EVE Copilot - processes events and triggers notifications
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import yaml
from pathlib import Path

from .events import GameEvent, EventType
from .notify import SpeechNotifier

logger = logging.getLogger(__name__)


class RuleError(Exception):
    """Rule-related errors."""
    pass


class Rule:
    """Individual rule for event processing."""
    
    def __init__(self, rule_config: Dict[str, Any]):
        """Initialize rule from configuration.
        
        Args:
            rule_config: Rule configuration dictionary
        """
        self.name = rule_config.get('name', 'unnamed')
        self.enabled = rule_config.get('enabled', True)
        self.event_types = rule_config.get('event_types', [])
        self.conditions = rule_config.get('conditions', {})
        self.thresholds = rule_config.get('thresholds', {})
        self.cooldown_ms = rule_config.get('cooldown_ms', 5000)
        self.window_ms = rule_config.get('window_ms', 3000)
        self.priority = rule_config.get('priority', 1)
        self.voice_prompt = rule_config.get('voice_prompt', '')
        
        # Internal state
        self.last_triggered = 0.0
        self.event_history: List[tuple[GameEvent, float]] = []
        self.trigger_count = 0
    
    def can_trigger(self, current_time: float) -> bool:
        """Check if rule can be triggered based on cooldown.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            True if rule can be triggered
        """
        return (current_time - self.last_triggered) >= (self.cooldown_ms / 1000.0)
    
    def add_event(self, event: GameEvent, current_time: float) -> None:
        """Add event to rule's event history.
        
        Args:
            event: Game event to add
            current_time: Current timestamp
        """
        # Add event with timestamp
        self.event_history.append((event, current_time))
        
        # Clean old events outside window
        cutoff_time = current_time - (self.window_ms / 1000.0)
        self.event_history = [(e, t) for e, t in self.event_history if t >= cutoff_time]
    
    def should_trigger(self, event: GameEvent, current_time: float) -> bool:
        """Determine if rule should trigger based on event and conditions.
        
        Args:
            event: Game event to check
            current_time: Current timestamp
            
        Returns:
            True if rule should trigger
        """
        if not self.enabled:
            return False
        
        if not self.can_trigger(current_time):
            return False
        
        # Check if event type matches
        if self.event_types and event.type.value not in self.event_types:
            return False
        
        # Add event to history
        self.add_event(event, current_time)
        
        # Check conditions
        return self._check_conditions(current_time)
    
    def _check_conditions(self, current_time: float) -> bool:
        """Check if rule conditions are met.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            True if conditions are met
        """
        if not self.conditions:
            return True
        
        # Check event count threshold
        if 'min_events' in self.conditions:
            min_events = self.conditions['min_events']
            if len(self.event_history) < min_events:
                return False
        
        # Check damage threshold (sum within current window)
        if 'min_damage' in self.conditions:
            total_damage = self._calculate_total_damage()
            if total_damage < int(self.conditions['min_damage']):
                return False
        
        # Check sustained damage (sum within window must meet or exceed threshold)
        if 'sustained_damage' in self.conditions:
            total_damage = self._calculate_total_damage()
            if total_damage < int(self.conditions['sustained_damage']):
                return False

        # Check shield threshold
        if 'shield_threshold' in self.conditions:
            try:
                shield_value = self._get_shield_value()
                if shield_value is None:
                    return False
                threshold = float(self.conditions['shield_threshold'])
                if shield_value > threshold:
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid shield threshold: {self.conditions['shield_threshold']}")
                return False
        
        # Check capacitor threshold
        if 'capacitor_threshold' in self.conditions:
            try:
                capacitor_value = self._get_capacitor_value()
                if capacitor_value is None:
                    return False
                threshold = float(self.conditions['capacitor_threshold'])
                if capacitor_value > threshold:
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid capacitor threshold: {self.conditions['capacitor_threshold']}")
                return False
        
        # Check time since abyss entry
        if 'time_since_abyss' in self.conditions:
            try:
                required_time = int(self.conditions['time_since_abyss'])
                if not self._check_time_since_abyss(required_time, current_time):
                    return False
            except (ValueError, TypeError):
                logger.warning(f"Invalid time_since_abyss: {self.conditions['time_since_abyss']}")
                return False
        
        return True
    
    def _calculate_total_damage(self) -> int:
        """Calculate total damage from event history.
        
        Returns:
            Total damage amount
        """
        total = 0
        for event, _ in self.event_history:
            damage = event.meta.get('damage')
            if damage is not None:
                total += int(damage)
            else:
                # Fallback to amount if damage not available
                amount = event.meta.get('amount', 0)
                total += int(amount)
        return total
    
    def _get_shield_value(self) -> Optional[float]:
        """Get shield value from recent events.
        
        Returns:
            Shield value or None if not found
        """
        for event, _ in reversed(self.event_history):
            shield = event.meta.get('shield')
            if shield is not None:
                return float(shield)
        return None
    
    def _get_capacitor_value(self) -> Optional[float]:
        """Get capacitor value from recent events.
        
        Returns:
            Capacitor value or None if not found
        """
        for event, _ in reversed(self.event_history):
            capacitor = event.meta.get('capacitor')
            if capacitor is not None:
                return float(capacitor)
        return None
    
    def _check_time_since_abyss(self, required_time: int, current_time: float) -> bool:
        """Check if enough time has passed since abyss entry.
        
        Args:
            required_time: Required time in seconds
            current_time: Current timestamp
            
        Returns:
            True if enough time has passed
        """
        # Look for recent abyss entry events (within last 30 minutes)
        for event, timestamp in self.event_history:
            event_age = current_time - timestamp
            if (event_age <= 1800 and  # Only consider events from last 30 minutes
                event.type.value == "SpatialPhenomena" and
                event.meta.get('effect') == 'spatial_phenomena'):
                time_elapsed = current_time - timestamp
                return time_elapsed >= required_time
        return False
    
    def trigger(self, current_time: float) -> None:
        """Mark rule as triggered.
        
        Args:
            current_time: Current timestamp
        """
        self.last_triggered = current_time
        self.trigger_count += 1
        logger.debug(f"Rule '{self.name}' triggered (count: {self.trigger_count})")
    
    def get_status(self) -> Dict[str, Any]:
        """Get rule status information.
        
        Returns:
            Dictionary with rule status
        """
        return {
            'name': self.name,
            'enabled': self.enabled,
            'trigger_count': self.trigger_count,
            'last_triggered': self.last_triggered,
            'event_history_size': len(self.event_history),
            'can_trigger': self.can_trigger(time.time())
        }


class RulesEngine:
    """Rules engine that processes events and triggers notifications."""
    
    def __init__(self, config, speech_notifier: SpeechNotifier):
        """Initialize rules engine.
        
        Args:
            config: Application configuration
            speech_notifier: Speech notification system
        """
        self.config = config
        self.speech_notifier = speech_notifier
        self.rules: List[Rule] = []
        self.profiles: Dict[str, Dict[str, Any]] = {}
        
        # Load rules and profiles
        self._load_profiles()
        self._load_rules()
        
        # Performance tracking
        self.events_processed = 0
        self.rules_triggered = 0
        self.last_performance_reset = time.time()
    
    def _load_profiles(self) -> None:
        """Load event profiles from configuration."""
        try:
            profiles_config = self.config.get_profiles_config()
            default_profile = profiles_config.get('default', 'general')
            available_profiles = profiles_config.get('available', ['general'])
            
            # Load profile files
            for profile_name in available_profiles:
                profile_file = Path(f"config/profiles/{profile_name}.yml")
                if profile_file.exists():
                    try:
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile_data = yaml.safe_load(f)
                            self.profiles[profile_name] = profile_data
                            logger.info(f"Loaded profile: {profile_name}")
                    except Exception as e:
                        logger.error(f"Failed to load profile {profile_name}: {e}")
                else:
                    logger.warning(f"Profile file not found: {profile_file}")
            
            # Set default profile
            if default_profile in self.profiles:
                self.active_profile = default_profile
                logger.info(f"Active profile: {default_profile}")
            else:
                self.active_profile = list(self.profiles.keys())[0] if self.profiles else None
                logger.warning(f"Default profile '{default_profile}' not found, using: {self.active_profile}")
                
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            self.profiles = {}
            self.active_profile = None
    
    def _load_rules(self) -> None:
        """Load rules from active profile."""
        if not self.active_profile or self.active_profile not in self.profiles:
            logger.warning("No active profile, no rules loaded")
            return
        
        try:
            profile_data = self.profiles[self.active_profile]
            rules_data = profile_data.get('rules', {})
            
            self.rules.clear()
            if isinstance(rules_data, dict):
                # Handle dictionary format: {rule_name: rule_config}
                for rule_name, rule_config in rules_data.items():
                    try:
                        # Add the rule name to the config if not present
                        if isinstance(rule_config, dict) and 'name' not in rule_config:
                            rule_config['name'] = rule_name
                        rule = Rule(rule_config)
                        self.rules.append(rule)
                        logger.debug(f"Loaded rule: {rule.name}")
                    except Exception as e:
                        logger.error(f"Failed to load rule {rule_name}: {e}")
            elif isinstance(rules_data, list):
                # Handle list format: [rule_config, rule_config, ...]
                for rule_config in rules_data:
                    try:
                        rule = Rule(rule_config)
                        self.rules.append(rule)
                        logger.debug(f"Loaded rule: {rule.name}")
                    except Exception as e:
                        logger.error(f"Failed to load rule {rule_config.get('name', 'unnamed')}: {e}")
            else:
                logger.error(f"Unexpected rules data type: {type(rules_data)}")
            
            logger.info(f"Loaded {len(self.rules)} rules from profile '{self.active_profile}'")
            
        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
    
    def process_event(self, event: GameEvent) -> None:
        """Process a game event through all rules.
        
        Args:
            event: Game event to process
        """
        if not self.rules:
            return
        
        current_time = time.time()
        self.events_processed += 1
        
        # Only process events from the last 30 minutes to avoid old log data
        # Note: EVE logs use GMT timezone, so we need a larger window
        event_age = current_time - event.timestamp.timestamp()
        if event_age > 1800:  # 30 minutes = 1800 seconds (accounts for timezone differences)
            logger.debug(f"Skipping old event: {event.type.value} from {event_age:.1f}s ago")
            return
        
        # Check performance limits
        if self._should_throttle_events(current_time):
            logger.debug("Event processing throttled due to performance limits")
            return
        
        # Process event through all rules
        for rule in self.rules:
            try:
                if rule.should_trigger(event, current_time):
                    self._trigger_rule(rule, event, current_time)
            except Exception as e:
                logger.error(f"Error processing rule '{rule.name}': {e}")
    
    def _should_throttle_events(self, current_time: float) -> bool:
        """Check if events should be throttled for performance.
        
        Args:
            current_time: Current timestamp
            
        Returns:
            True if events should be throttled
        """
        performance_config = self.config.get_performance_config()
        max_events_per_second = performance_config.get('max_events_per_second', 100)
        
        # Reset counter if more than 1 second has passed
        if current_time - self.last_performance_reset >= 1.0:
            self.events_processed = 0
            self.last_performance_reset = current_time
        
        return self.events_processed >= max_events_per_second
    
    def _trigger_rule(self, rule: Rule, event: GameEvent, current_time: float) -> None:
        """Trigger a rule and send notification.
        
        Args:
            rule: Rule to trigger
            event: Game event that triggered the rule
            current_time: Current timestamp
        """
        try:
            # Mark rule as triggered
            rule.trigger(current_time)
            self.rules_triggered += 1
            
            # Send speech notification
            if rule.voice_prompt:
                # Process dynamic voice prompts
                voice_prompt = self._process_voice_prompt(rule, event)
                
                self.speech_notifier.speak(
                    voice_prompt, 
                    priority=rule.priority, 
                    event=event
                )
                logger.info(f"Rule '{rule.name}' triggered: {voice_prompt}")
            else:
                logger.debug(f"Rule '{rule.name}' triggered (no voice prompt)")
                
        except Exception as e:
            logger.error(f"Failed to trigger rule '{rule.name}': {e}")
    
    def _process_voice_prompt(self, rule: Rule, event: GameEvent) -> str:
        """Process voice prompt with dynamic substitutions.
        
        Args:
            rule: Rule that was triggered
            event: Event that triggered the rule
            
        Returns:
            Processed voice prompt string
        """
        voice_prompt = rule.voice_prompt
        
        # Handle target recommendation
        if '{target_name}' in voice_prompt:
            target_name = self._get_recommended_target(rule, event)
            voice_prompt = voice_prompt.replace('{target_name}', target_name)
        
        return voice_prompt
    
    def _get_recommended_target(self, rule: Rule, event: GameEvent) -> str:
        """Get recommended target based on damage analysis.
        
        Args:
            rule: Rule that was triggered
            event: Event that triggered the rule
            
        Returns:
            Recommended target name
        """
        import time
        current_time = time.time()
        
        # Analyze damage from VERY recent events (last 10 seconds)
        # This ensures we only recommend currently active threats
        enemy_damage = {}
        
        for event, timestamp in rule.event_history:
            # Only consider events from the last 10 seconds
            event_age = current_time - timestamp
            if event_age > 10:  # 10 seconds = only very recent damage
                continue
                
            if event.type.value == "IncomingDamage":
                from_entity = event.subject  # Enemy name is stored in subject field
                damage = event.meta.get('damage', 0)
                
                # Skip if no valid enemy name or damage
                if from_entity == 'Unknown' or not from_entity or damage <= 0:
                    continue
                    
                if from_entity not in enemy_damage:
                    enemy_damage[from_entity] = 0
                enemy_damage[from_entity] += int(damage)
        
        if not enemy_damage:
            # If no valid recent damage events found, return a generic message
            return "No targets detected"
        
        # Find enemy with highest total damage in recent window
        best_target = max(enemy_damage.items(), key=lambda x: x[1])
        target_name = best_target[0]
        
        # Apply EVE Abyssal enemy priority rules
        target_name = self._apply_abyssal_priority(target_name)
        
        return target_name
    
    def _apply_abyssal_priority(self, target_name: str) -> str:
        """Apply EVE Abyssal enemy priority rules.
        
        Args:
            target_name: Original target name
            
        Returns:
            Prioritized target name
        """
        # EVE Abyssal enemy priority (most dangerous first)
        priority_keywords = {
            # Triglavian enemies (highest priority)
            'Damavik': 'Damavik (Triglavian)',
            'Kikimora': 'Kikimora (Triglavian)', 
            'Tessella': 'Tessella (Triglavian)',
            'Devoted': 'Devoted (Triglavian)',
            'Torchbearer': 'Torchbearer (Triglavian)',
            'Hunter': 'Hunter (Triglavian)',
            'Knight': 'Knight (Triglavian)',
            
            # Drifter enemies (medium priority)
            'Drifter': 'Drifter',
            'Drifter Battleship': 'Drifter Battleship',
            'Drifter Cruiser': 'Drifter Cruiser',
            
            # Other enemies (lower priority)
            'Rogue': 'Rogue',
            'Pirate': 'Pirate',
            'Sansha': 'Sansha',
            'Blood': 'Blood Raider',
            'Angel': 'Angel Cartel'
        }
        
        # Check for priority keywords in target name
        for keyword, priority_name in priority_keywords.items():
            if keyword.lower() in target_name.lower():
                return priority_name
        
        # Default to original name if no priority match
        return target_name
    
    def switch_profile(self, profile_name: str) -> bool:
        """Switch to a different event profile.
        
        Args:
            profile_name: Name of profile to switch to
            
        Returns:
            True if profile switch was successful
        """
        if profile_name not in self.profiles:
            logger.warning(f"Profile '{profile_name}' not found")
            return False
        
        try:
            self.active_profile = profile_name
            self._load_rules()
            logger.info(f"Switched to profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to profile '{profile_name}': {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get rules engine status information.
        
        Returns:
            Dictionary with engine status
        """
        return {
            'active_profile': self.active_profile,
            'available_profiles': list(self.profiles.keys()),
            'rules_count': len(self.rules),
            'enabled_rules': len([r for r in self.rules if r.enabled]),
            'events_processed': self.events_processed,
            'rules_triggered': self.rules_triggered,
            'performance_throttled': self._should_throttle_events(time.time())
        }
    
    def get_rule_status(self) -> List[Dict[str, Any]]:
        """Get status of all rules.
        
        Returns:
            List of rule status dictionaries
        """
        return [rule.get_status() for rule in self.rules]
    
    def reload_config(self) -> None:
        """Reload configuration and rules."""
        try:
            self._load_profiles()
            self._load_rules()
            logger.info("Rules engine configuration reloaded")
        except Exception as e:
            logger.error(f"Failed to reload rules engine configuration: {e}")
    
    def shutdown(self) -> None:
        """Shutdown the rules engine."""
        logger.info("Rules engine shutdown complete")
