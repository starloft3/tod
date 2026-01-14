"""
Game Log System for Tides of Darkness.

Provides structured event logging for combat, movement, base actions,
and other game events. Logs persist with saves and can be filtered/viewed.

The log is designed to feel like dispatches arriving at a general's
command center - military reports from the front lines.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


def _unit_ref(unit: Dict) -> str:
    """Format a unit reference with name and ID for log summaries."""
    name = unit.get('name', 'Unknown')
    unit_id = unit.get('id', '?')
    return f"{name} (ID:{unit_id})"


class LogEventType(Enum):
    """Categories of log events."""
    # Combat
    COMBAT_START = "combat_start"
    COMBAT_ATTACK = "combat_attack"
    COMBAT_DAMAGE = "combat_damage"
    COMBAT_DEATH = "combat_death"
    COMBAT_TIER_UP = "combat_tier_up"
    COMBAT_END = "combat_end"
    
    # Movement
    MOVEMENT = "movement"
    
    # Base Actions
    HARVEST = "harvest"
    COMMERCE = "commerce"
    BUILD_UNIT = "build_unit"
    UPGRADE_BASE = "upgrade_base"
    REST_UNIT = "rest_unit"
    EXPAND = "expand"
    ESTABLISH_CARAVAN = "establish_caravan"
    SEND_RESOURCES = "send_resources"
    
    # Entity Lifecycle
    UNIT_CREATED = "unit_created"
    UNIT_DESTROYED = "unit_destroyed"
    BASE_CAPTURED = "base_captured"
    BASE_DESTROYED = "base_destroyed"
    CARAVAN_DESTROYED = "caravan_destroyed"
    EXPANSION_DESTROYED = "expansion_destroyed"
    
    # Turn Flow
    TURN_START = "turn_start"
    TURN_END = "turn_end"
    ROUND_START = "round_start"
    INITIATIVE_START = "initiative_start"
    
    # Diplomacy
    DIPLOMACY = "diplomacy"
    
    # Debug/Admin
    DEBUG_ACTION = "debug_action"


@dataclass
class LogEntry:
    """
    A single log entry representing a game event.
    
    Designed to be displayable as a "military dispatch" - 
    a report from the field to the commanding general.
    """
    # Identity
    id: int                              # Unique entry ID
    timestamp: str                       # ISO timestamp when logged
    
    # Game Context
    turn_number: int                     # Overall turn number
    round_number: int                    # Which round (1, 2, 3...)
    round_side: str                      # "HORDE" or "ALLIANCE"
    initiative: int                      # Current initiative when logged
    
    # Event Info
    event_type: str                      # LogEventType value
    category: str                        # High-level category for filtering
    
    # Content
    summary: str                         # One-line human-readable summary
    details: Dict[str, Any] = field(default_factory=dict)  # Structured details
    
    # Involved Parties
    faction_id: Optional[int] = None     # Primary faction involved
    faction_name: Optional[str] = None   # Faction name for display
    hex_id: Optional[int] = None         # Location if applicable
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LogEntry':
        """Create from dictionary."""
        return cls(**data)


class GameLog:
    """
    Central game logging system.
    
    Stores all game events and provides methods to add, query, and persist logs.
    """
    
    # Category groupings for filtering
    CATEGORY_COMBAT = "combat"
    CATEGORY_MOVEMENT = "movement"
    CATEGORY_HARVEST = "harvest"
    CATEGORY_ECONOMIC = "economic"
    CATEGORY_ENTITY = "entity"
    CATEGORY_TURN = "turn"
    CATEGORY_DEBUG = "debug"
    
    EVENT_CATEGORIES = {
        LogEventType.COMBAT_START: CATEGORY_COMBAT,
        LogEventType.COMBAT_ATTACK: CATEGORY_COMBAT,
        LogEventType.COMBAT_DAMAGE: CATEGORY_COMBAT,
        LogEventType.COMBAT_DEATH: CATEGORY_COMBAT,
        LogEventType.COMBAT_TIER_UP: CATEGORY_COMBAT,
        LogEventType.COMBAT_END: CATEGORY_COMBAT,
        LogEventType.BASE_DESTROYED: CATEGORY_COMBAT,  # Dramatic combat result!
        LogEventType.MOVEMENT: CATEGORY_MOVEMENT,
        LogEventType.HARVEST: CATEGORY_HARVEST,
        LogEventType.COMMERCE: CATEGORY_ECONOMIC,
        LogEventType.BUILD_UNIT: CATEGORY_ECONOMIC,
        LogEventType.UPGRADE_BASE: CATEGORY_ECONOMIC,
        LogEventType.REST_UNIT: CATEGORY_ECONOMIC,
        LogEventType.EXPAND: CATEGORY_ECONOMIC,
        LogEventType.ESTABLISH_CARAVAN: CATEGORY_ECONOMIC,
        LogEventType.SEND_RESOURCES: CATEGORY_ECONOMIC,
        LogEventType.UNIT_CREATED: CATEGORY_ENTITY,
        LogEventType.UNIT_DESTROYED: CATEGORY_ENTITY,
        LogEventType.BASE_CAPTURED: CATEGORY_ENTITY,
        LogEventType.BASE_DESTROYED: CATEGORY_ENTITY,
        LogEventType.CARAVAN_DESTROYED: CATEGORY_ENTITY,
        LogEventType.EXPANSION_DESTROYED: CATEGORY_ENTITY,
        LogEventType.TURN_START: CATEGORY_TURN,
        LogEventType.TURN_END: CATEGORY_TURN,
        LogEventType.ROUND_START: CATEGORY_TURN,
        LogEventType.INITIATIVE_START: CATEGORY_TURN,
        LogEventType.DIPLOMACY: CATEGORY_ENTITY,  # Diplomacy events are entity-related
        LogEventType.DEBUG_ACTION: CATEGORY_DEBUG,
    }
    
    def __init__(self):
        self.entries: List[LogEntry] = []
        self._next_id: int = 1
        self._current_turn: int = 1
        self._current_round: int = 1
        self._current_side: str = "HORDE"
        self._current_initiative: int = 1
    
    def update_turn_context(self, turn_number: int, round_number: int, 
                            round_side: str, initiative: int):
        """Update the current turn context for new log entries."""
        self._current_turn = turn_number
        self._current_round = round_number
        self._current_side = round_side
        self._current_initiative = initiative
    
    def log(self, event_type: LogEventType, summary: str, 
            details: Dict[str, Any] = None,
            faction_id: int = None, faction_name: str = None,
            hex_id: int = None) -> LogEntry:
        """
        Add a new log entry.
        
        Args:
            event_type: Type of event
            summary: Human-readable one-line summary
            details: Structured data for expandable view
            faction_id: Primary faction involved (if any)
            faction_name: Faction name for display
            hex_id: Location hex (if applicable)
            
        Returns:
            The created LogEntry
        """
        category = self.EVENT_CATEGORIES.get(event_type, self.CATEGORY_DEBUG)
        
        entry = LogEntry(
            id=self._next_id,
            timestamp=datetime.now().isoformat(),
            turn_number=self._current_turn,
            round_number=self._current_round,
            round_side=self._current_side,
            initiative=self._current_initiative,
            event_type=event_type.value,
            category=category,
            summary=summary,
            details=details or {},
            faction_id=faction_id,
            faction_name=faction_name,
            hex_id=hex_id,
        )
        
        self.entries.append(entry)
        self._next_id += 1
        
        # Also log to Python logger for debugging
        logger.info(f"[GameLog] {entry.summary}")
        
        return entry
    
    # ==================== Convenience Logging Methods ====================
    
    def log_combat_start(self, hex_id: int, combatants: List[Dict], 
                         is_continuing: bool = False) -> LogEntry:
        """Log the start of combat at a hex."""
        if is_continuing:
            summary = f"⚔️ Combat continues at hex {hex_id}!"
        else:
            summary = f"⚔️ Combat begins at hex {hex_id}!"
        
        return self.log(
            LogEventType.COMBAT_START,
            summary,
            details={
                "combatants": combatants,
                "combatant_count": len(combatants),
                "is_continuing": is_continuing
            },
            hex_id=hex_id
        )
    
    def log_combat_attack(self, attacker: Dict, defender: Dict, 
                          roll: int, hit: bool, damage: int,
                          modifiers: Dict = None, hits_rolled: int = 0,
                          verbose_data: Dict = None) -> LogEntry:
        """Log a single combat attack with full details."""
        hit_text = "HIT" if hit else "MISS"
        attacks = attacker.get("hp", 1)  # HP = number of attacks
        summary = f"{_unit_ref(attacker)} attacks {_unit_ref(defender)}: {roll}% @ {attacks}HP → {hit_text}"
        if hit:
            summary += f" ({damage} damage)"
        
        details = {
            "attacker": attacker,
            "defender": defender,
            "roll": roll,
            "hit": hit,
            "damage": damage,
            "attacks": attacks,
            "hits_rolled": hits_rolled,
            "modifiers": modifiers or {},
            "hit_threshold": modifiers.get("hit_chance", 50) if modifiers else 50
        }
        
        # Add verbose data if provided
        if verbose_data:
            details["verbose"] = verbose_data
        
        return self.log(
            LogEventType.COMBAT_ATTACK,
            summary,
            details=details,
            faction_id=attacker.get("faction_id"),
            faction_name=attacker.get("faction_name"),
            hex_id=attacker.get("location")
        )
    
    def log_combat_damage(self, unit: Dict, damage: int, 
                          armor_absorbed: Dict, remaining_hp: int) -> LogEntry:
        """Log damage dealt to a unit with armor breakdown."""
        absorbed_text = []
        if armor_absorbed.get("light", 0):
            absorbed_text.append(f"{armor_absorbed['light']} light")
        if armor_absorbed.get("heavy", 0):
            absorbed_text.append(f"{armor_absorbed['heavy']} heavy")
        if armor_absorbed.get("natural", 0):
            absorbed_text.append(f"{armor_absorbed['natural']} natural")
        
        armor_info = f" (armor absorbed: {', '.join(absorbed_text)})" if absorbed_text else ""
        
        return self.log(
            LogEventType.COMBAT_DAMAGE,
            f"{_unit_ref(unit)} takes {damage} damage{armor_info} → {remaining_hp} HP remaining",
            details={
                "unit": unit,
                "damage_raw": damage + sum(armor_absorbed.values()),
                "damage_final": damage,
                "armor_absorbed": armor_absorbed,
                "hp_before": remaining_hp + damage,
                "hp_after": remaining_hp
            },
            faction_id=unit.get("faction_id"),
            faction_name=unit.get("faction_name"),
            hex_id=unit.get("location")
        )
    
    def log_combat_death(self, unit: Dict, killer: Dict = None) -> LogEntry:
        """Log a unit death in combat."""
        if killer:
            summary = f"{_unit_ref(unit)} slain by {_unit_ref(killer)}!"
        else:
            summary = f"{_unit_ref(unit)} has fallen!"
        
        return self.log(
            LogEventType.COMBAT_DEATH,
            summary,
            details={
                "unit": unit,
                "killer": killer
            },
            faction_id=unit.get("faction_id"),
            faction_name=unit.get("faction_name"),
            hex_id=unit.get("location")
        )
    
    def log_combat_tier_up(self, unit: Dict, victim: Dict, 
                           old_tier: int, new_tier: int,
                           hex_id: int = None) -> LogEntry:
        """Log a unit gaining a tier from combat."""
        summary = f"⭐ {_unit_ref(unit)} gains a rank! (Tier {old_tier} → {new_tier})"
        
        return self.log(
            LogEventType.COMBAT_TIER_UP,
            summary,
            details={
                "unit": unit,
                "victim": victim,
                "old_tier": old_tier,
                "new_tier": new_tier
            },
            faction_id=unit.get("faction_id"),
            faction_name=unit.get("faction_name"),
            hex_id=hex_id
        )
    
    def log_combat_end(self, hex_id: int, victor_initiative: int = None,
                       casualties: List[Dict] = None,
                       remaining_combatants: List[Dict] = None) -> LogEntry:
        """Log combat resolution at a hex."""
        if victor_initiative is not None:
            summary = f"Combat at hex {hex_id} concluded. Initiative {victor_initiative} holds the field."
        else:
            summary = f"Combat at hex {hex_id} continues..."
        
        return self.log(
            LogEventType.COMBAT_END,
            summary,
            details={
                "victor_initiative": victor_initiative,
                "casualties": casualties or [],
                "combat_ended": victor_initiative is not None,
                "remaining_combatants": remaining_combatants or []
            },
            hex_id=hex_id
        )
    
    def log_movement(self, unit: Dict, path: List[int], 
                     movement_used: int) -> LogEntry:
        """Log unit movement."""
        start = path[0] if path else "?"
        end = path[-1] if path else "?"
        hex_word = "hex" if movement_used == 1 else "hexes"
        
        return self.log(
            LogEventType.MOVEMENT,
            f"{_unit_ref(unit)} marches from hex {start} to hex {end} ({movement_used} {hex_word})",
            details={
                "unit": unit,
                "path": path,
                "movement_used": movement_used,
                "hexes_traveled": movement_used
            },
            faction_id=unit.get("faction_id"),
            faction_name=unit.get("faction_name"),
            hex_id=end
        )
    
    def log_harvest(self, base: Dict, yields: Dict) -> LogEntry:
        """Log automatic harvest."""
        total = yields.get("gold", 0) + yields.get("lumber", 0) + yields.get("oil", 0)
        return self.log(
            LogEventType.HARVEST,
            f"{base['name']} harvests: +{yields.get('gold', 0)}🪙 +{yields.get('lumber', 0)}🪵 +{yields.get('oil', 0)}🛢️",
            details={
                "base": base,
                "yields": yields,
                "total_yield": total
            },
            faction_id=base.get("faction_id"),
            faction_name=base.get("faction_name"),
            hex_id=base.get("location")
        )
    
    def log_build_unit(self, base: Dict, unit_name: str, cost: Dict, 
                       unit: Dict = None) -> LogEntry:
        """Log unit construction."""
        if unit:
            summary = f"{base['name']} musters {_unit_ref(unit)}"
        else:
            summary = f"{base['name']} musters a {unit_name}"
        
        return self.log(
            LogEventType.BUILD_UNIT,
            summary,
            details={
                "base": base,
                "unit_name": unit_name,
                "unit": unit,
                "cost": cost
            },
            faction_id=base.get("faction_id"),
            faction_name=base.get("faction_name"),
            hex_id=base.get("location")
        )
    
    def log_rest_unit(self, base: Dict, unit: Dict, 
                      heal_amount: int, old_hp: int, new_hp: int) -> LogEntry:
        """Log a unit being healed at a base."""
        return self.log(
            LogEventType.REST_UNIT,
            f"{base['name']} heals {_unit_ref(unit)}: +{heal_amount} HP ({old_hp} → {new_hp})",
            details={
                "base": base,
                "unit": unit,
                "heal_amount": heal_amount,
                "hp_before": old_hp,
                "hp_after": new_hp,
                "gold_cost": 2
            },
            faction_id=base.get("faction_id"),
            faction_name=base.get("faction_name"),
            hex_id=base.get("location")
        )
    
    def log_initiative_start(self, initiative: int, factions: List[str]) -> LogEntry:
        """Log the start of an initiative's turn."""
        faction_list = ", ".join(factions)
        return self.log(
            LogEventType.INITIATIVE_START,
            f"Initiative {initiative} begins: {faction_list}",
            details={
                "initiative": initiative,
                "factions": factions
            }
        )
    
    def log_round_start(self, round_number: int, side: str) -> LogEntry:
        """Log the start of a new round."""
        return self.log(
            LogEventType.ROUND_START,
            f"=== {side} Round {round_number} Begins ===",
            details={
                "round_number": round_number,
                "side": side
            }
        )
    
    def log_base_destroyed(self, base: Dict, destroyer_faction: str = None,
                           hex_id: int = None) -> LogEntry:
        """Log a base being destroyed (razed to ruins)."""
        base_name = base.get("name", "Unknown Base")
        base_id = base.get("id", 0)
        faction_name = base.get("faction_name", "Unknown")
        
        if destroyer_faction:
            summary = f"🔥 {base_name} has been razed by {destroyer_faction}!"
        else:
            summary = f"🔥 {base_name} has been razed to the ground!"
        
        return self.log(
            LogEventType.BASE_DESTROYED,
            summary,
            details={
                "base_id": base_id,
                "base_name": base_name,
                "original_faction": faction_name,
                "destroyer_faction": destroyer_faction,
            },
            faction_name=faction_name,
            hex_id=hex_id
        )
    
    # ==================== Query Methods ====================
    
    def get_entries(self, 
                    category: str = None,
                    event_type: str = None,
                    faction_id: int = None,
                    turn_number: int = None,
                    hex_id: int = None,
                    limit: int = None,
                    offset: int = 0) -> List[LogEntry]:
        """
        Get log entries with optional filtering.
        
        Returns entries in reverse chronological order (newest first).
        """
        filtered = self.entries.copy()
        
        if category:
            filtered = [e for e in filtered if e.category == category]
        
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        
        if faction_id is not None:
            filtered = [e for e in filtered if e.faction_id == faction_id]
        
        if turn_number is not None:
            filtered = [e for e in filtered if e.turn_number == turn_number]
        
        if hex_id is not None:
            filtered = [e for e in filtered if e.hex_id == hex_id]
        
        # Reverse for newest-first
        filtered = list(reversed(filtered))
        
        # Apply pagination
        if offset:
            filtered = filtered[offset:]
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_combat_log_for_hex(self, hex_id: int, turn_number: int = None) -> List[LogEntry]:
        """Get all combat events for a specific hex."""
        return self.get_entries(
            category=self.CATEGORY_COMBAT,
            hex_id=hex_id,
            turn_number=turn_number
        )
    
    def get_entries_by_turn(self, turn_number: int) -> List[LogEntry]:
        """Get all entries for a specific turn."""
        return self.get_entries(turn_number=turn_number)
    
    def get_summary(self) -> Dict:
        """Get a summary of log statistics."""
        by_category = {}
        for entry in self.entries:
            by_category[entry.category] = by_category.get(entry.category, 0) + 1
        
        return {
            "total_entries": len(self.entries),
            "by_category": by_category,
            "turns_logged": len(set(e.turn_number for e in self.entries)),
            "earliest_turn": min((e.turn_number for e in self.entries), default=0),
            "latest_turn": max((e.turn_number for e in self.entries), default=0)
        }
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> dict:
        """Serialize the entire log to a dictionary."""
        return {
            "next_id": self._next_id,
            "current_context": {
                "turn": self._current_turn,
                "round": self._current_round,
                "side": self._current_side,
                "initiative": self._current_initiative
            },
            "entries": [e.to_dict() for e in self.entries]
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GameLog':
        """Deserialize from dictionary."""
        log = cls()
        log._next_id = data.get("next_id", 1)
        
        context = data.get("current_context", {})
        log._current_turn = context.get("turn", 1)
        log._current_round = context.get("round", 1)
        log._current_side = context.get("side", "HORDE")
        log._current_initiative = context.get("initiative", 1)
        
        log.entries = [LogEntry.from_dict(e) for e in data.get("entries", [])]
        
        return log
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GameLog':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def clear(self):
        """Clear all log entries."""
        self.entries.clear()
        self._next_id = 1


# ============================================================================
# Global Instance
# ============================================================================

_game_log: Optional[GameLog] = None


def get_game_log() -> GameLog:
    """Get the global game log instance."""
    global _game_log
    if _game_log is None:
        _game_log = GameLog()
    return _game_log


def reset_game_log():
    """Reset the global game log."""
    global _game_log
    _game_log = GameLog()

