"""
GameState - Central container for all game data.

This class replaces the scattered global variables (allunits, allhexes, allbases, etc.)
with a single, well-organized state object.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto

from .models import (
    Unit, UnitStats, Hex, Base, Faction, Road, Caravan,
    FactionId, UnitCategory, Terrain
)


class GamePhase(Enum):
    """Current phase of the game turn."""
    SETUP = auto()              # Initial game setup
    PLANNING = auto()           # Factions submitting orders
    RESOLUTION = auto()         # Orders being resolved
    COMBAT = auto()             # Combat being resolved
    ECONOMIC = auto()           # Economic phase
    END_TURN = auto()           # Turn cleanup


class Initiative(Enum):
    """Major faction initiatives (Horde vs Alliance turn structure)."""
    HORDE = 4
    ALLIANCE = 14


@dataclass
class TurnState:
    """Tracks the current turn and phase state."""
    turn_number: int = 0
    current_initiative: int = -1  # Which initiative group is active
    current_faction: int = -1     # Which faction is submitting orders
    phase: GamePhase = GamePhase.SETUP
    
    # Track which factions have submitted orders (by faction id)
    orders_submitted: Set[int] = field(default_factory=set)
    
    def all_orders_submitted(self, faction_ids: List[int]) -> bool:
        """Check if all factions in the initiative have submitted orders."""
        return all(fid in self.orders_submitted for fid in faction_ids)


@dataclass
class Order:
    """A unit movement or action order."""
    unit_id: int
    order_type: str  # 'M' for move, 'A' for attack, etc.
    target: int      # Target hex or unit
    secondary: int = 0
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Order':
        """Create Order from database row."""
        return cls(
            unit_id=int(row[0]),
            order_type=str(row[1]),
            target=int(row[2]),
            secondary=int(row[3]) if len(row) > 3 else 0
        )


@dataclass 
class SpecialOrder:
    """A special action order (spells, abilities, etc.)."""
    faction_id: int
    order_type: str
    source: int
    target: int
    secondary: int = 0
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'SpecialOrder':
        """Create SpecialOrder from database row."""
        return cls(
            faction_id=int(row[0]),
            order_type=str(row[1]),
            source=int(row[2]),
            target=int(row[3]),
            secondary=int(row[4]) if len(row) > 4 else 0
        )


@dataclass
class EconomicAction:
    """An economic action (build, upgrade, trade, etc.)."""
    faction_id: int
    action_type: str
    base_id: int
    target: str
    quantity: int = 1
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'EconomicAction':
        """Create EconomicAction from database row."""
        return cls(
            faction_id=int(row[0]),
            action_type=str(row[1]),
            base_id=int(row[2]),
            target=str(row[3]),
            quantity=int(row[4]) if len(row) > 4 else 1
        )


@dataclass
class SpecialEvent:
    """A special event that can occur during the game."""
    id: int
    event_type: str
    status: int  # 0 = not triggered, 1 = active, 2 = completed
    trigger_turn: int
    target_faction: int
    description: str = ""
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'SpecialEvent':
        """Create SpecialEvent from database row."""
        return cls(
            id=int(row[0]),
            event_type=str(row[1]),
            status=int(row[2]),
            trigger_turn=int(row[3]),
            target_faction=int(row[4]),
            description=str(row[5]) if len(row) > 5 else ""
        )


@dataclass
class GameState:
    """
    Central container for all game state.
    
    Replaces global variables: allunits, allhexes, allbases, allfactions, 
    allroads, allcaravans, allorders, etc.
    """
    
    # Core entity collections - keyed by ID for O(1) lookup
    units: Dict[int, Unit] = field(default_factory=dict)
    hexes: Dict[int, Hex] = field(default_factory=dict)
    bases: Dict[int, Base] = field(default_factory=dict)
    factions: Dict[int, Faction] = field(default_factory=dict)
    roads: Dict[int, Road] = field(default_factory=dict)  # Keyed by hex_id
    caravans: List[Caravan] = field(default_factory=list)
    
    # Unit stats (templates for creating units)
    unit_stats: Dict[str, UnitStats] = field(default_factory=dict)
    
    # Turn tracking
    turn: TurnState = field(default_factory=TurnState)
    
    # Orders for current turn
    orders: List[Order] = field(default_factory=list)
    special_orders: List[SpecialOrder] = field(default_factory=list)
    economic_actions: List[EconomicAction] = field(default_factory=list)
    
    # Special events
    special_events: List[SpecialEvent] = field(default_factory=list)
    
    # Vision tracking (which hexes each faction can see)
    visible_hexes: Dict[int, Set[int]] = field(default_factory=dict)  # faction_id -> set of hex_ids
    
    # Food tracking
    food_surplus: Dict[int, int] = field(default_factory=dict)  # faction_id -> surplus
    food_surplus_after: Dict[int, int] = field(default_factory=dict)
    
    # Base names pool
    base_names: List[Tuple[str, int, int]] = field(default_factory=list)  # (name, faction_restriction, used)
    
    # Buildable units per faction
    buildables: Dict[int, List[bool]] = field(default_factory=dict)  # faction_id -> list of booleans
    
    # Constants
    HORDE_FACTIONS: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    ALLIANCE_FACTIONS: List[int] = field(default_factory=lambda: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    
    # ==================== Lookup Methods ====================
    
    def get_unit(self, unit_id: int) -> Optional[Unit]:
        """Get unit by ID."""
        return self.units.get(unit_id)
    
    def get_hex(self, hex_id: int) -> Optional[Hex]:
        """Get hex by ID (location number)."""
        return self.hexes.get(hex_id)
    
    def get_base(self, base_id: int) -> Optional[Base]:
        """Get base by ID."""
        return self.bases.get(base_id)
    
    def get_faction(self, faction_id: int) -> Optional[Faction]:
        """Get faction by ID."""
        return self.factions.get(faction_id)
    
    def get_road(self, hex_id: int) -> Optional[Road]:
        """Get road data for a hex."""
        return self.roads.get(hex_id)
    
    def has_road_between(self, hex1: int, hex2: int) -> bool:
        """Check if there's a road connection between two adjacent hexes."""
        road = self.roads.get(hex1)
        if not road:
            return False
        # Determine direction from hex1 to hex2 and check road connection
        diff = hex2 - hex1
        direction_map = {1: 'north', -1: 'south', 38: 'southeast', -38: 'northwest', 39: 'southwest', -39: 'northeast'}
        if diff in direction_map:
            return getattr(road, direction_map[diff], 0) > 0
        return False
    
    def get_unit_stats(self, unit_name: str) -> Optional[UnitStats]:
        """Get stats template for a unit type."""
        return self.unit_stats.get(unit_name)
    
    # ==================== Query Methods ====================
    
    def units_at_hex(self, hex_id: int) -> List[Unit]:
        """Get all units at a specific hex."""
        return [u for u in self.units.values() if u.location == hex_id and u.alive]
    
    def units_by_faction(self, faction_id: int) -> List[Unit]:
        """Get all units belonging to a faction."""
        return [u for u in self.units.values() if u.faction == faction_id and u.alive]
    
    def bases_by_faction(self, faction_id: int) -> List[Base]:
        """Get all bases controlled by a faction."""
        return [b for b in self.bases.values() if b.faction == faction_id]
    
    def base_at_hex(self, hex_id: int) -> Optional[Base]:
        """Get base at a specific hex, if any."""
        for base in self.bases.values():
            if base.location == hex_id:
                return base
        return None
    
    def faction_initiative(self, faction_id: int) -> int:
        """Get the initiative value for a faction."""
        faction = self.factions.get(faction_id)
        return faction.initiative if faction else -1
    
    def factions_in_initiative(self, initiative: int) -> List[int]:
        """Get all faction IDs that share an initiative value."""
        return [fid for fid, f in self.factions.items() if f.initiative == initiative]
    
    def adjacent_hexes(self, hex_id: int) -> List[int]:
        """
        Get IDs of hexes adjacent to the given hex.
        Uses the map geometry: 38 columns, offset rows.
        """
        # Standard hex adjacency offsets for this map
        offsets = [1, -1, 38, -38, 39, -39]
        adjacent = []
        for offset in offsets:
            adj_id = hex_id + offset
            if adj_id in self.hexes:
                # Additional validation could check actual adjacency rules
                adjacent.append(adj_id)
        return adjacent
    
    def is_allied(self, faction1: int, faction2: int) -> bool:
        """Check if two factions are allied (same initiative)."""
        f1 = self.factions.get(faction1)
        f2 = self.factions.get(faction2)
        if f1 and f2:
            return f1.initiative == f2.initiative
        return False
    
    def is_enemy(self, faction1: int, faction2: int) -> bool:
        """Check if two factions are enemies."""
        return not self.is_allied(faction1, faction2)
    
    def enemies_at_hex(self, hex_id: int, faction_id: int) -> List[Unit]:
        """Get all enemy units at a hex."""
        return [u for u in self.units_at_hex(hex_id) 
                if self.is_enemy(u.faction, faction_id)]
    
    def allies_at_hex(self, hex_id: int, faction_id: int) -> List[Unit]:
        """Get all allied units at a hex (including own)."""
        return [u for u in self.units_at_hex(hex_id)
                if self.is_allied(u.faction, faction_id)]
    
    # ==================== Modification Methods ====================
    
    def add_unit(self, unit: Unit) -> None:
        """Add a unit to the game state."""
        self.units[unit.id] = unit
    
    def remove_unit(self, unit_id: int) -> Optional[Unit]:
        """Remove a unit from the game state."""
        return self.units.pop(unit_id, None)
    
    def kill_unit(self, unit_id: int) -> None:
        """Mark a unit as dead (keeps it for battle log purposes)."""
        if unit_id in self.units:
            self.units[unit_id].alive = False
    
    def move_unit(self, unit_id: int, new_hex: int) -> bool:
        """Move a unit to a new hex."""
        unit = self.units.get(unit_id)
        if unit and new_hex in self.hexes:
            unit.location = new_hex
            return True
        return False
    
    def add_base(self, base: Base) -> None:
        """Add a base to the game state."""
        self.bases[base.id] = base
    
    def capture_base(self, base_id: int, new_faction: int) -> bool:
        """Transfer control of a base to a new faction."""
        base = self.bases.get(base_id)
        if base:
            base.faction = new_faction
            return True
        return False
    
    # ==================== Turn Management ====================
    
    def start_new_turn(self) -> None:
        """Begin a new game turn."""
        self.turn.turn_number += 1
        self.turn.phase = GamePhase.PLANNING
        self.turn.orders_submitted.clear()
        self.orders.clear()
        self.special_orders.clear()
        self.economic_actions.clear()
        
        # Reset per-turn unit flags
        for unit in self.units.values():
            unit.reset_for_turn()
    
    def submit_faction_orders(self, faction_id: int) -> None:
        """Mark a faction as having submitted orders."""
        self.turn.orders_submitted.add(faction_id)
    
    def advance_initiative(self) -> int:
        """
        Move to the next initiative. Returns the new initiative value.
        In this game, initiatives cycle through active faction groups.
        """
        # Get all unique initiatives that have non-defeated factions
        active_initiatives = sorted(set(
            f.initiative for f in self.factions.values() 
            if not f.is_defeated and f.initiative >= 0
        ))
        
        if not active_initiatives:
            return -1
            
        current = self.turn.current_initiative
        if current < 0 or current not in active_initiatives:
            # Start with first initiative
            self.turn.current_initiative = active_initiatives[0]
        else:
            # Move to next initiative
            idx = active_initiatives.index(current)
            next_idx = (idx + 1) % len(active_initiatives)
            self.turn.current_initiative = active_initiatives[next_idx]
            
            # If we wrapped around, new turn
            if next_idx == 0:
                self.start_new_turn()
        
        return self.turn.current_initiative
    
    # ==================== Serialization ====================
    
    def to_legacy_format(self) -> dict:
        """
        Convert to legacy global variable format for compatibility.
        Returns dict with: allunits, allhexes, allbases, allfactions, etc.
        """
        # Sort by ID to maintain list index consistency
        sorted_units = sorted(self.units.values(), key=lambda u: u.id)
        sorted_hexes = sorted(self.hexes.values(), key=lambda h: h.id)
        sorted_bases = sorted(self.bases.values(), key=lambda b: b.id)
        sorted_factions = sorted(self.factions.values(), key=lambda f: f.id)
        
        return {
            'allunits': [u.to_legacy_list() for u in sorted_units],
            'allhexes': [h.to_legacy_list() for h in sorted_hexes],
            'allbases': [b.to_legacy_list() for b in sorted_bases],
            'allfactions': [f.initiative for f in sorted_factions],
            'allroads': [r.to_legacy_list() for r in self.roads.values()],
            'allcaravans': self.caravans,  # Already in right format
            'currentinitiative': [self.turn.current_initiative],
        }
    
    @classmethod
    def from_legacy_format(cls, 
                           allunits: list,
                           allhexes: list, 
                           allbases: list,
                           allfactions: list,
                           allroads: list,
                           **kwargs) -> 'GameState':
        """
        Create GameState from legacy global variables.
        This allows gradual migration from the old system.
        """
        state = cls()
        
        # Convert units
        for i, unit_list in enumerate(allunits):
            unit = Unit.from_legacy_list(unit_list)
            unit.id = i  # Ensure ID matches index
            state.units[i] = unit
        
        # Convert hexes
        for i, hex_list in enumerate(allhexes):
            hex_obj = Hex.from_legacy_list(hex_list)
            hex_obj.id = i
            state.hexes[i] = hex_obj
        
        # Convert bases
        for i, base_list in enumerate(allbases):
            base = Base.from_legacy_list(base_list)
            base.id = i
            state.bases[i] = base
        
        # Convert factions - allfactions is just initiative values
        for i, initiative in enumerate(allfactions):
            state.factions[i] = Faction(
                id=i,
                name=f"Faction_{i}",  # Would need lookup for real names
                initiative=initiative
            )
        
        # Convert roads
        for road_list in allroads:
            road = Road.from_legacy_list(road_list)
            state.roads[road.hex_id] = road
        
        # Handle optional kwargs
        if 'currentinitiative' in kwargs:
            state.turn.current_initiative = kwargs['currentinitiative'][0]
        
        return state
    
    # ==================== Statistics ====================
    
    def faction_unit_count(self, faction_id: int) -> int:
        """Count living units for a faction."""
        return len(self.units_by_faction(faction_id))
    
    def faction_base_count(self, faction_id: int) -> int:
        """Count bases controlled by a faction."""
        return len(self.bases_by_faction(faction_id))
    
    def faction_income(self, faction_id: int) -> Tuple[int, int, int]:
        """
        Calculate total stored resources for a faction (gold, lumber, oil).
        
        Note: Actual income calculation would require counting farms, mills,
        and oil rigs connected to bases. This returns stored resources.
        """
        bases = self.bases_by_faction(faction_id)
        gold = sum(b.gold for b in bases)
        lumber = sum(b.lumber for b in bases)
        oil = sum(b.oil for b in bases)
        return gold, lumber, oil
    
    def summary(self) -> str:
        """Generate a summary of the current game state."""
        lines = [
            f"=== Game State Summary ===",
            f"Turn: {self.turn.turn_number}, Phase: {self.turn.phase.name}",
            f"Current Initiative: {self.turn.current_initiative}",
            f"",
            f"Entities:",
            f"  Units: {len(self.units)} ({sum(1 for u in self.units.values() if u.alive)} alive)",
            f"  Hexes: {len(self.hexes)}",
            f"  Bases: {len(self.bases)}",
            f"  Factions: {len(self.factions)}",
            f"  Roads: {len(self.roads)}",
            f"  Caravans: {len(self.caravans)}",
            f"",
            f"Orders pending: {len(self.orders)} movement, {len(self.special_orders)} special, {len(self.economic_actions)} economic",
        ]
        return "\n".join(lines)


# Singleton instance for compatibility during migration
_current_game_state: Optional[GameState] = None


def get_game_state() -> GameState:
    """Get the current game state singleton."""
    global _current_game_state
    if _current_game_state is None:
        _current_game_state = GameState()
    return _current_game_state


def set_game_state(state: GameState) -> None:
    """Set the current game state singleton."""
    global _current_game_state
    _current_game_state = state

