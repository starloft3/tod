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


class RoundSide(Enum):
    """Which side's round it is."""
    HORDE = "HORDE"
    ALLIANCE = "ALLIANCE"


@dataclass
class TurnState:
    """
    Tracks the current turn and phase state.
    
    Structure:
    - Rounds alternate: Horde Round 1 → Alliance Round 1 → Horde Round 2 → ...
    - Within a round, turns happen per initiative (ascending order)
    - All factions on the same initiative act together
    """
    round_number: int = 1
    round_side: RoundSide = RoundSide.HORDE
    current_initiative: int = -1  # Which initiative group is active (-1 = none yet)
    phase: GamePhase = GamePhase.SETUP
    
    # Track which initiatives have completed this round
    completed_initiatives: Set[int] = field(default_factory=set)
    
    # Track which factions have submitted orders this turn (by faction id)
    orders_submitted: Set[int] = field(default_factory=set)
    
    @property
    def turn_number(self) -> int:
        """Calculate overall turn number from round and side."""
        # Each full round (Horde + Alliance) = 2 "sides"
        # Turn number is a sequential count for display purposes
        base = (self.round_number - 1) * 2
        if self.round_side == RoundSide.ALLIANCE:
            base += 1
        return base + 1
    
    def all_orders_submitted(self, faction_ids: List[int]) -> bool:
        """Check if all factions in the initiative have submitted orders."""
        return all(fid in self.orders_submitted for fid in faction_ids)
    
    def reset_for_new_turn(self):
        """Reset state for a new initiative turn."""
        self.orders_submitted.clear()
        self.phase = GamePhase.PLANNING
    
    def reset_for_new_round(self, side: RoundSide):
        """Reset state for a new round."""
        self.round_side = side
        self.completed_initiatives.clear()
        self.orders_submitted.clear()
        self.current_initiative = -1
        self.phase = GamePhase.PLANNING


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
        # Using (from - to) to match server.py HasRoad() convention
        diff = hex1 - hex2
        direction_map = {
            1: 'north',      # Moving to lower ID = north
            -1: 'south',     # Moving to higher ID = south
            39: 'northwest',
            -39: 'southeast',
            38: 'southwest',
            -38: 'northeast'
        }
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
    
    def is_horde_faction(self, faction_id: int) -> bool:
        """Check if a faction is Horde (by ID)."""
        # Faction IDs 0-6 are Horde
        # Note: Alterac (ID 10) can defect to Horde via diplomacy - check initiative
        if faction_id in self.HORDE_FACTIONS:
            return True
        # Check for Alterac defection: if Alterac shares initiative with a Horde faction
        faction = self.factions.get(faction_id)
        if faction and faction_id == 10:  # Alterac
            for horde_id in self.HORDE_FACTIONS:
                horde_faction = self.factions.get(horde_id)
                if horde_faction and faction.initiative == horde_faction.initiative:
                    return True
        return False
    
    def is_alliance_faction(self, faction_id: int) -> bool:
        """Check if a faction is Alliance."""
        return not self.is_horde_faction(faction_id)
    
    def get_horde_initiatives(self) -> List[int]:
        """Get all active Horde initiatives in ascending order (excluding -1)."""
        initiatives = set()
        for fid, faction in self.factions.items():
            if (not faction.is_defeated and 
                faction.initiative >= 0 and 
                self.is_horde_faction(fid)):
                initiatives.add(faction.initiative)
        return sorted(initiatives)
    
    def get_alliance_initiatives(self) -> List[int]:
        """Get all active Alliance initiatives in ascending order (excluding -1)."""
        initiatives = set()
        for fid, faction in self.factions.items():
            if (not faction.is_defeated and 
                faction.initiative >= 0 and 
                self.is_alliance_faction(fid)):
                initiatives.add(faction.initiative)
        return sorted(initiatives)
    
    def get_current_round_initiatives(self) -> List[int]:
        """Get initiatives for the current round side."""
        if self.turn.round_side == RoundSide.HORDE:
            return self.get_horde_initiatives()
        else:
            return self.get_alliance_initiatives()
    
    def get_next_initiative(self) -> Optional[int]:
        """
        Get the next initiative to process in the current round.
        Returns None if the round is complete.
        """
        initiatives = self.get_current_round_initiatives()
        remaining = [i for i in initiatives if i not in self.turn.completed_initiatives]
        return remaining[0] if remaining else None
    
    def is_round_complete(self) -> bool:
        """Check if all initiatives in the current round have completed."""
        return self.get_next_initiative() is None
    
    def start_initiative_turn(self, initiative: int) -> None:
        """Begin a new initiative turn within the current round."""
        self.turn.current_initiative = initiative
        self.turn.orders_submitted.clear()
        self.turn.phase = GamePhase.PLANNING
        self.orders.clear()
        self.special_orders.clear()
        self.economic_actions.clear()
    
    def complete_initiative_turn(self) -> None:
        """Mark the current initiative as completed."""
        if self.turn.current_initiative >= 0:
            self.turn.completed_initiatives.add(self.turn.current_initiative)
    
    def advance_to_next_initiative(self) -> dict:
        """
        Advance to the next initiative. Handles round transitions.
        
        Returns dict with status info:
        - 'action': 'next_initiative' | 'end_round' | 'end_game_round'
        - 'initiative': new initiative value (if applicable)
        - 'round_side': current round side
        - 'round_number': current round number
        """
        # Mark current initiative as complete
        self.complete_initiative_turn()
        
        # Check if round is complete
        if self.is_round_complete():
            # End of round - switch sides
            if self.turn.round_side == RoundSide.HORDE:
                # Horde round complete, start Alliance round
                self.turn.reset_for_new_round(RoundSide.ALLIANCE)
                next_init = self.get_next_initiative()
                if next_init is not None:
                    self.start_initiative_turn(next_init)
                    return {
                        'action': 'end_round',
                        'message': f'Horde Round {self.turn.round_number} complete. Starting Alliance Round.',
                        'initiative': next_init,
                        'round_side': 'ALLIANCE',
                        'round_number': self.turn.round_number
                    }
            else:
                # Alliance round complete, start new Horde round
                self.turn.round_number += 1
                self.turn.reset_for_new_round(RoundSide.HORDE)
                next_init = self.get_next_initiative()
                if next_init is not None:
                    self.start_initiative_turn(next_init)
                    return {
                        'action': 'end_game_round',
                        'message': f'Alliance Round {self.turn.round_number - 1} complete. Starting Horde Round {self.turn.round_number}.',
                        'initiative': next_init,
                        'round_side': 'HORDE',
                        'round_number': self.turn.round_number
                    }
        else:
            # More initiatives in this round
            next_init = self.get_next_initiative()
            if next_init is not None:
                self.start_initiative_turn(next_init)
                return {
                    'action': 'next_initiative',
                    'message': f'Advancing to initiative {next_init}',
                    'initiative': next_init,
                    'round_side': self.turn.round_side.value,
                    'round_number': self.turn.round_number
                }
        
        # Should not reach here, but just in case
        return {
            'action': 'error',
            'message': 'No more initiatives available'
        }
    
    def start_new_game(self) -> dict:
        """
        Initialize state for a brand new game.
        Starts with Horde Round 1, first Horde initiative (Amani).
        """
        self.turn.round_number = 1
        self.turn.round_side = RoundSide.HORDE
        self.turn.completed_initiatives.clear()
        self.turn.orders_submitted.clear()
        self.turn.phase = GamePhase.SETUP
        
        # Get first Horde initiative
        horde_inits = self.get_horde_initiatives()
        if horde_inits:
            first_init = horde_inits[0]
            self.start_initiative_turn(first_init)
            factions = self.factions_in_initiative(first_init)
            faction_names = [self.factions[f].name for f in factions if f in self.factions]
            return {
                'success': True,
                'message': f'New game started. Horde Round 1, Initiative {first_init}.',
                'round_number': 1,
                'round_side': 'HORDE',
                'initiative': first_init,
                'factions': faction_names
            }
        
        return {
            'success': False,
            'message': 'No active Horde factions found'
        }
    
    def submit_faction_orders(self, faction_id: int) -> None:
        """Mark a faction as having submitted orders."""
        self.turn.orders_submitted.add(faction_id)
    
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

