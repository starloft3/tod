"""
GameState - Central container for all game data.

This class replaces the scattered global variables (allunits, allhexes, allbases, etc.)
with a single, well-organized state object.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto

from .models import (
    Unit, UnitStats, Hex, Base, Faction, Road, Caravan, Expansion,
    FactionId, UnitCategory, Terrain, ExpansionType
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


# Mapping from buildables table column index to unit type name
# Legacy code uses FACTION_DATA_GRUNT=1 but accesses [GRUNT-1]=[0]
# So column 0 = Grunt, column 1 = Berserker, etc.
BUILDABLE_COLUMN_TO_UNIT = {
    0: 'Grunt',
    1: 'Berserker',
    2: 'Axethrower',
    3: 'Ogre',
    4: 'Catapult',
    5: 'Death Knight',
    6: 'Wave Rider',
    7: 'Turtle',
    8: 'Juggernaut',
    9: 'Horde Transport',
    10: 'Dragon',
    11: 'Raider',
    12: 'Shaman',
    13: 'Warlock',
    14: 'Footman',
    15: 'Archer',
    16: 'Knight',
    17: 'Ballista',
    18: 'Mage',
    19: 'Destroyer',
    20: 'Submarine',
    21: 'Battleship',
    22: 'Alliance Transport',
    23: 'Gryphon',
    24: 'Dwarf',
    25: 'Swordsman',
    26: 'Wildhammer Shaman',
    27: 'Rogue',
    28: 'Skeleton',
    29: 'Demon',
    30: 'Elemental',
    31: 'Mountaineer',
}


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
    
    # Hexside terrain constants for caravan and trace validation
    # Land caravan hexsides: Clear and Forest (can also use roads)
    LAND_CARAVAN_HEXSIDES = {'C', 'F'}
    # Sea caravan coastal endpoints: Coastal Clear, Coastal Forest, Coastal Mountain 
    SEA_CARAVAN_COASTAL = {'K', 'Q', 'N'}  # K=Coastal Clear, Q=Coastal Forest, N=Coastal Mountain
    # Sea caravan ocean hexsides (middle of path)
    SEA_CARAVAN_OCEAN = {'O'}  # O=Ocean
    # Land trace hexsides (for expansions)
    LAND_TRACE_HEXSIDES = {'C', 'F'}  # Clear and Forest
    # Sea trace hexsides (for coastal expansions)
    SEA_TRACE_HEXSIDES = {'K', 'Q', 'N', 'O'}  # Coastal + Ocean
    
    # Core entity collections - keyed by ID for O(1) lookup
    units: Dict[int, Unit] = field(default_factory=dict)
    hexes: Dict[int, Hex] = field(default_factory=dict)
    bases: Dict[int, Base] = field(default_factory=dict)
    factions: Dict[int, Faction] = field(default_factory=dict)
    roads: Dict[int, Road] = field(default_factory=dict)  # Keyed by hex_id
    caravans: List[Caravan] = field(default_factory=list)
    expansions: Dict[int, Expansion] = field(default_factory=dict)  # Keyed by expansion ID
    
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
    
    # Buildable units per faction: faction_id -> {unit_name -> max_tier}
    # Max tier of -1 means faction cannot build this unit
    # Otherwise it's the maximum veterancy tier achievable (0-4)
    faction_buildables: Dict[int, Dict[str, int]] = field(default_factory=dict)
    
    # Pending base orders - keyed by base_id, list of (action_type, action_data) tuples
    # Orders are stored in sequence order (LIFO for cancellation)
    pending_base_orders: Dict[int, List[dict]] = field(default_factory=dict)
    
    # Constants
    HORDE_FACTIONS: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])
    ALLIANCE_FACTIONS: List[int] = field(default_factory=lambda: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    
    # ==================== Debug Helpers ====================
    
    def _is_infinite_resources(self) -> bool:
        """Check if infinite resources debug mode is enabled."""
        try:
            from .game_config import get_game_config
            return get_game_config().debug.infinite_resources
        except Exception:
            return False
    
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
    
    def has_road_at_hex(self, hex_id: int) -> bool:
        """Check if a hex has any road connection (for fast travel eligibility)."""
        road = self.roads.get(hex_id)
        if not road:
            return False
        # Check if any direction has a road
        return (road.north > 0 or road.northeast > 0 or road.southeast > 0 or
                road.south > 0 or road.southwest > 0 or road.northwest > 0)
    
    def are_hexes_adjacent(self, hex1: int, hex2: int) -> bool:
        """Check if two hexes are adjacent to each other."""
        diff = abs(hex1 - hex2)
        return diff in [1, 38, 39]
    
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
    
    def get_expansion(self, expansion_id: int) -> Optional[Expansion]:
        """Get expansion by ID."""
        return self.expansions.get(expansion_id)
    
    def expansion_at_hex(self, hex_id: int) -> Optional[Expansion]:
        """Get expansion at a specific hex, if any."""
        for exp in self.expansions.values():
            if exp.location == hex_id:
                return exp
        return None
    
    def expansions_for_base(self, base_id: int) -> List[Expansion]:
        """Get all expansions attached to a base."""
        return [exp for exp in self.expansions.values() if exp.base_id == base_id]
    
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
    
    def is_allied(self, faction1, faction2) -> bool:
        """
        Check if two factions are allied (same initiative).
        
        Currently, factions are allied if they share the same initiative.
        TODO: When diplomacy is implemented, this will also check diplomatic status.
        """
        # Handle FactionId enums
        fid1 = faction1.value if hasattr(faction1, 'value') else faction1
        fid2 = faction2.value if hasattr(faction2, 'value') else faction2
        
        f1 = self.factions.get(fid1)
        f2 = self.factions.get(fid2)
        if f1 and f2:
            return f1.initiative == f2.initiative
        return False
    
    def is_enemy(self, faction1, faction2) -> bool:
        """
        Check if two factions are enemies (hostile).
        
        Currently, factions are enemies if they don't share the same initiative.
        TODO: When diplomacy is implemented, this will check actual hostility status,
        as non-allied factions may be neutral rather than hostile.
        """
        return not self.is_allied(faction1, faction2)
    
    def is_hostile(self, faction1, faction2) -> bool:
        """
        Check if two factions are hostile to each other.
        
        For now, this is the same as is_enemy. When diplomacy is implemented,
        this will distinguish between:
        - Allied (same initiative) - can stack, share vision
        - Neutral (different initiative but not at war) - cannot attack
        - Hostile (at war) - triggers combat
        """
        # TODO: Implement actual hostility check when diplomacy is added
        return self.is_enemy(faction1, faction2)
    
    def enemies_at_hex(self, hex_id: int, faction_id) -> List[Unit]:
        """Get all enemy units at a hex."""
        # Handle FactionId enum
        fid = faction_id.value if hasattr(faction_id, 'value') else faction_id
        return [u for u in self.units_at_hex(hex_id) 
                if self.is_enemy(u.faction, fid)]
    
    def hostiles_at_hex(self, hex_id: int, faction_id) -> List[Unit]:
        """Get all hostile units at a hex (triggers combat)."""
        # Handle FactionId enum
        fid = faction_id.value if hasattr(faction_id, 'value') else faction_id
        return [u for u in self.units_at_hex(hex_id) 
                if self.is_hostile(u.faction, fid)]
    
    def allies_at_hex(self, hex_id: int, faction_id) -> List[Unit]:
        """Get all allied units at a hex (including own)."""
        # Handle FactionId enum
        fid = faction_id.value if hasattr(faction_id, 'value') else faction_id
        return [u for u in self.units_at_hex(hex_id)
                if self.is_allied(u.faction, fid)]
    
    def is_combat_hex(self, hex_id: int) -> bool:
        """
        Check if a hex is a combat hex (has living units from 2+ different initiatives).
        
        A combat hex exists when enemy forces are present together.
        """
        units = self.units_at_hex(hex_id)
        if not units:
            return False
        
        # Get unique initiatives present
        initiatives = set()
        for unit in units:
            initiative = self.faction_initiative(unit.faction)
            if initiative >= 0:  # Valid initiative
                initiatives.add(initiative)
        
        return len(initiatives) >= 2
    
    def base_in_combat(self, base_id: int) -> bool:
        """Check if a base is in an active combat hex."""
        base = self.get_base(base_id)
        if not base:
            return False
        return self.is_combat_hex(base.location)
    
    # ==================== Food System ====================
    
    def faction_food_from_bases(self, faction_id: int) -> int:
        """Calculate food provided by a faction's bases (sum of tiers)."""
        bases = self.bases_by_faction(faction_id)
        return sum(base.tier for base in bases)
    
    def faction_food_from_farms(self, faction_id: int) -> int:
        """Calculate food provided by a faction's farms (+1 each)."""
        # Get all bases for this faction
        faction_bases = self.bases_by_faction(faction_id)
        base_ids = {b.id for b in faction_bases}
        
        # Count farms belonging to those bases
        farm_count = 0
        for exp in self.expansions.values():
            if exp.base_id in base_ids and exp.type.value == 'farm':
                farm_count += 1
        
        return farm_count
    
    def faction_food_limit(self, faction_id: int) -> int:
        """Calculate total food limit for a faction."""
        return self.faction_food_from_bases(faction_id) + self.faction_food_from_farms(faction_id)
    
    def faction_unit_count(self, faction_id: int) -> int:
        """Count alive units belonging to a faction."""
        return len(self.units_by_faction(faction_id))
    
    def faction_food_status(self, faction_id: int) -> dict:
        """Get complete food status for a faction."""
        food_from_bases = self.faction_food_from_bases(faction_id)
        food_from_farms = self.faction_food_from_farms(faction_id)
        food_limit = food_from_bases + food_from_farms
        unit_count = self.faction_unit_count(faction_id)
        surplus = food_limit - unit_count
        
        return {
            'faction_id': faction_id,
            'food_from_bases': food_from_bases,
            'food_from_farms': food_from_farms,
            'food_limit': food_limit,
            'unit_count': unit_count,
            'food_surplus': surplus,
            'is_capped': surplus <= 0,
            'can_build': surplus > 0
        }
    
    # ==================== Caravan Management ====================
    
    def get_caravans_for_base(self, base_id: int) -> List:
        """Get all caravans connected to a base (as origin or destination)."""
        return [c for c in self.caravans 
                if c.origin_base_id == base_id or c.destination_base_id == base_id]
    
    def get_caravans_for_faction(self, faction_id: int) -> List:
        """Get all caravans connected to any base owned by a faction."""
        faction_base_ids = {b.id for b in self.bases.values() 
                          if (b.faction.value if hasattr(b.faction, 'value') else b.faction) == faction_id}
        return [c for c in self.caravans 
                if c.origin_base_id in faction_base_ids or c.destination_base_id in faction_base_ids]
    
    def get_caravans_for_initiative(self, initiative: int) -> List:
        """Get all caravans for bases sharing a given initiative."""
        init_base_ids = set()
        for base in self.bases.values():
            faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
            faction = self.get_faction(faction_id)
            if faction and faction.initiative == initiative:
                init_base_ids.add(base.id)
        return [c for c in self.caravans 
                if c.origin_base_id in init_base_ids or c.destination_base_id in init_base_ids]
    
    def caravan_exists_between(self, base_id_1: int, base_id_2: int) -> bool:
        """Check if a caravan already exists between two bases."""
        return any(c.connects_bases(base_id_1, base_id_2) for c in self.caravans)
    
    def get_caravan_between(self, base_id_1: int, base_id_2: int):
        """Get the caravan connecting two bases, if any."""
        for caravan in self.caravans:
            if caravan.connects_bases(base_id_1, base_id_2):
                return caravan
        return None
    
    def check_caravan_initiative_validity(self, caravan) -> bool:
        """
        Check if a caravan is still valid based on current faction initiatives.
        Returns True if both endpoint bases' factions share the same initiative.
        """
        origin_base = self.get_base(caravan.origin_base_id)
        dest_base = self.get_base(caravan.destination_base_id)
        
        if not origin_base or not dest_base:
            return False  # Base was destroyed
        
        origin_faction_id = origin_base.faction.value if hasattr(origin_base.faction, 'value') else origin_base.faction
        dest_faction_id = dest_base.faction.value if hasattr(dest_base.faction, 'value') else dest_base.faction
        
        origin_faction = self.get_faction(origin_faction_id)
        dest_faction = self.get_faction(dest_faction_id)
        
        if not origin_faction or not dest_faction:
            return False
        
        return origin_faction.initiative == dest_faction.initiative
    
    def destroy_invalid_caravans_by_initiative(self) -> List:
        """
        Destroy all caravans whose endpoint bases' factions no longer share initiative.
        Called during diplomacy resolution phase.
        
        Returns list of destroyed caravans.
        """
        destroyed = []
        valid_caravans = []
        
        for caravan in self.caravans:
            if self.check_caravan_initiative_validity(caravan):
                valid_caravans.append(caravan)
            else:
                destroyed.append(caravan)
        
        self.caravans = valid_caravans
        return destroyed
    
    # ==================== Hex Control System ====================
    
    def get_hex_control(self, hex_id: int) -> Optional[int]:
        """
        Get the initiative that controls a hex, if any.
        
        Control is established by:
        - Expansions: The hex where the expansion is built
        - Caravans: All hexes in the caravan path
        
        Returns the initiative number, or None if uncontrolled.
        """
        # Check expansions
        for expansion in self.expansions.values():
            if expansion.location == hex_id:
                owning_base = self.get_base(expansion.base_id)
                if owning_base:
                    faction_id = owning_base.faction.value if hasattr(owning_base.faction, 'value') else owning_base.faction
                    faction = self.get_faction(faction_id)
                    if faction:
                        return faction.initiative
        
        # Check caravans
        for caravan in self.caravans:
            if hex_id in caravan.path:
                # Get initiative from origin base
                origin_base = self.get_base(caravan.origin_base_id)
                if origin_base:
                    faction_id = origin_base.faction.value if hasattr(origin_base.faction, 'value') else origin_base.faction
                    faction = self.get_faction(faction_id)
                    if faction:
                        return faction.initiative
        
        return None
    
    def is_hex_controlled_by_other_initiative(self, hex_id: int, my_initiative: int) -> bool:
        """Check if a hex is controlled by a different initiative."""
        control = self.get_hex_control(hex_id)
        return control is not None and control != my_initiative
    
    def get_controlled_hexes_for_initiative(self, initiative: int) -> set:
        """Get all hexes controlled by a given initiative."""
        controlled = set()
        
        # From expansions
        for expansion in self.expansions.values():
            owning_base = self.get_base(expansion.base_id)
            if owning_base:
                faction_id = owning_base.faction.value if hasattr(owning_base.faction, 'value') else owning_base.faction
                faction = self.get_faction(faction_id)
                if faction and faction.initiative == initiative:
                    controlled.add(expansion.location)
        
        # From caravans
        for caravan in self.caravans:
            origin_base = self.get_base(caravan.origin_base_id)
            if origin_base:
                faction_id = origin_base.faction.value if hasattr(origin_base.faction, 'value') else origin_base.faction
                faction = self.get_faction(faction_id)
                if faction and faction.initiative == initiative:
                    controlled.update(caravan.path)
        
        return controlled
    
    # ==================== Caravan Establishment ====================
    
    # Valid hexsides for land caravan tracing (clear, forest, or road)
    LAND_CARAVAN_HEXSIDES = {'C', 'F'}  # Clear and Forest
    
    # Valid hexsides for sea caravan tracing
    SEA_CARAVAN_COASTAL = {'K'}  # Coastal clear (start/end only)
    SEA_CARAVAN_OCEAN = {'O'}    # Ocean (middle hexes)
    
    def is_base_coastal(self, base_id: int) -> bool:
        """Check if a base is coastal (has at least one coastal hexside)."""
        base = self.get_base(base_id)
        if not base:
            return False
        
        hex_obj = self.get_hex(base.location)
        if not hex_obj:
            return False
        
        # Check all 6 hexsides for coastal terrain
        hexsides = [
            hex_obj.north.terrain if hasattr(hex_obj.north, 'terrain') else '',
            hex_obj.northeast.terrain if hasattr(hex_obj.northeast, 'terrain') else '',
            hex_obj.southeast.terrain if hasattr(hex_obj.southeast, 'terrain') else '',
            hex_obj.south.terrain if hasattr(hex_obj.south, 'terrain') else '',
            hex_obj.southwest.terrain if hasattr(hex_obj.southwest, 'terrain') else '',
            hex_obj.northwest.terrain if hasattr(hex_obj.northwest, 'terrain') else '',
        ]
        
        coastal_terrains = {'K', 'N', 'Q'}  # Coastal clear, mountain, forest
        return any(side in coastal_terrains for side in hexsides)
    
    def get_caravan_terrain_type(self, origin_base_id: int, dest_base_id: int) -> Optional[str]:
        """
        Determine what type of caravan can be established between two bases.
        
        Returns 'land', 'sea', or None if no caravan possible.
        Sea caravans require BOTH bases to be coastal.
        """
        origin_coastal = self.is_base_coastal(origin_base_id)
        dest_coastal = self.is_base_coastal(dest_base_id)
        
        if origin_coastal and dest_coastal:
            return 'sea'  # Can be either, but sea is an option
        else:
            return 'land'  # Must be land
    
    def can_establish_sea_caravan(self, origin_base_id: int, dest_base_id: int) -> bool:
        """Check if a sea caravan can be established (both bases coastal)."""
        return self.is_base_coastal(origin_base_id) and self.is_base_coastal(dest_base_id)
    
    def validate_caravan_hexside(self, from_hex: int, to_hex: int, 
                                  is_sea: bool, is_endpoint: bool) -> tuple:
        """
        Validate if a caravan can be traced through a hexside.
        
        Args:
            from_hex: Source hex
            to_hex: Destination hex
            is_sea: True for sea caravan, False for land
            is_endpoint: True if this is the first or last hexside from a base
            
        Returns:
            (valid: bool, reason: str)
        """
        hexside_terrain = self.get_hexside_terrain(from_hex, to_hex)
        
        if is_sea:
            if is_endpoint:
                # Start/end must be coastal clear
                if hexside_terrain in self.SEA_CARAVAN_COASTAL:
                    return (True, "")
                return (False, f"Sea caravan endpoints must use coastal clear hexsides (got {hexside_terrain})")
            else:
                # Middle must be ocean
                if hexside_terrain in self.SEA_CARAVAN_OCEAN:
                    return (True, "")
                return (False, f"Sea caravan path must use ocean hexsides (got {hexside_terrain})")
        else:
            # Land caravan: clear, forest, or road
            if hexside_terrain in self.LAND_CARAVAN_HEXSIDES:
                return (True, "")
            # Check for road
            if self.has_road_between(from_hex, to_hex):
                return (True, "")
            return (False, f"Land caravan requires clear, forest, or road hexsides (got {hexside_terrain})")
    
    def validate_caravan_path(self, origin_base_id: int, dest_base_id: int, 
                               path: List[int], is_sea: bool) -> dict:
        """
        Validate a complete caravan path.
        
        Args:
            origin_base_id: Origin base ID
            dest_base_id: Destination base ID
            path: List of hex IDs from origin to destination (inclusive)
            is_sea: True for sea caravan, False for land
            
        Returns:
            {'valid': bool, 'error': str, 'cost': {'lumber': int, 'oil': int}}
        """
        from .models.caravan import get_caravan_cost, get_max_caravan_length
        
        max_caravan_length = get_max_caravan_length()
        origin_base = self.get_base(origin_base_id)
        dest_base = self.get_base(dest_base_id)
        
        if not origin_base or not dest_base:
            return {'valid': False, 'error': 'Invalid base ID'}
        
        # Check path length
        if len(path) > max_caravan_length:
            return {'valid': False, 'error': f'Path too long ({len(path)} > {max_caravan_length})'}
        
        if len(path) < 2:
            return {'valid': False, 'error': 'Path must include at least 2 hexes'}
        
        # Check path starts and ends at correct bases
        if path[0] != origin_base.location:
            return {'valid': False, 'error': 'Path must start at origin base hex'}
        if path[-1] != dest_base.location:
            return {'valid': False, 'error': 'Path must end at destination base hex'}
        
        # Check initiative match
        origin_faction_id = origin_base.faction.value if hasattr(origin_base.faction, 'value') else origin_base.faction
        dest_faction_id = dest_base.faction.value if hasattr(dest_base.faction, 'value') else dest_base.faction
        origin_faction = self.get_faction(origin_faction_id)
        dest_faction = self.get_faction(dest_faction_id)
        
        if not origin_faction or not dest_faction:
            return {'valid': False, 'error': 'Invalid faction'}
        
        if origin_faction.initiative != dest_faction.initiative:
            return {'valid': False, 'error': 'Bases must share the same initiative'}
        
        my_initiative = origin_faction.initiative
        
        # Check sea caravan requirements
        if is_sea and not self.can_establish_sea_caravan(origin_base_id, dest_base_id):
            return {'valid': False, 'error': 'Sea caravans require both bases to be coastal'}
        
        # Validate each hexside in the path
        for i in range(len(path) - 1):
            from_hex = path[i]
            to_hex = path[i + 1]
            
            # Check if hexes are adjacent
            direction = self.get_hex_direction(from_hex, to_hex)
            if direction is None:
                return {'valid': False, 'error': f'Hexes {from_hex} and {to_hex} are not adjacent'}
            
            # First and last hexsides are endpoints
            is_endpoint = (i == 0) or (i == len(path) - 2)
            
            valid, reason = self.validate_caravan_hexside(from_hex, to_hex, is_sea, is_endpoint)
            if not valid:
                return {'valid': False, 'error': reason}
        
        # Check each intermediate hex (not bases) for blockers
        for hex_id in path[1:-1]:  # Skip origin and destination bases
            # Check for enemy units
            units_at_hex = self.units_at_hex(hex_id)
            for unit in units_at_hex:
                if not unit.alive:
                    continue
                unit_faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                unit_faction = self.get_faction(unit_faction_id)
                if unit_faction and unit_faction.initiative != my_initiative:
                    return {'valid': False, 'error': f'Enemy units at hex {hex_id}'}
            
            # Check for enemy bases
            for base in self.bases.values():
                if base.location == hex_id:
                    base_faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
                    base_faction = self.get_faction(base_faction_id)
                    if base_faction and base_faction.initiative != my_initiative:
                        return {'valid': False, 'error': f'Enemy base at hex {hex_id}'}
            
            # Check for hex control by other initiative
            if self.is_hex_controlled_by_other_initiative(hex_id, my_initiative):
                return {'valid': False, 'error': f'Hex {hex_id} controlled by another initiative'}
            
            # TODO: Check visibility when vision system is implemented
        
        # Calculate cost
        cost = get_caravan_cost(len(path), is_sea)
        
        return {'valid': True, 'error': '', 'cost': cost}
    
    def get_valid_next_caravan_hexes(self, origin_base_id: int, current_path: List[int], 
                                      is_sea: bool, dest_base_id: Optional[int] = None) -> List[dict]:
        """
        Get valid next hexes for caravan path tracing.
        
        Used by frontend to show valid options in real-time.
        
        Returns list of {'hex_id': int, 'is_destination': bool}
        """
        from .models.caravan import get_max_caravan_length
        
        max_caravan_length = get_max_caravan_length()
        
        if not current_path:
            return []
        
        if len(current_path) >= max_caravan_length:
            return []  # Path already at max length
        
        current_hex = current_path[-1]
        origin_base = self.get_base(origin_base_id)
        if not origin_base:
            return []
        
        origin_faction_id = origin_base.faction.value if hasattr(origin_base.faction, 'value') else origin_base.faction
        origin_faction = self.get_faction(origin_faction_id)
        if not origin_faction:
            return []
        
        my_initiative = origin_faction.initiative
        
        # Get all adjacent hexes
        valid_hexes = []
        for diff in [-1, 1, 38, -38, 39, -39]:
            neighbor = current_hex + diff
            hex_obj = self.get_hex(neighbor)
            if not hex_obj:
                continue
            
            # Don't revisit hexes in path (except destination)
            if neighbor in current_path:
                continue
            
            # Check hexside validity
            is_endpoint = (len(current_path) == 1)  # First move from base
            valid, _ = self.validate_caravan_hexside(current_hex, neighbor, is_sea, is_endpoint)
            if not valid:
                continue
            
            # Check for blockers (enemy units, enemy bases, other initiative control)
            # Skip these checks for the destination base hex
            is_destination = False
            if dest_base_id:
                dest_base = self.get_base(dest_base_id)
                if dest_base and dest_base.location == neighbor:
                    is_destination = True
            
            # Also check if this is ANY valid destination base (same initiative)
            for base in self.bases.values():
                if base.location == neighbor and base.id != origin_base_id:
                    base_faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
                    base_faction = self.get_faction(base_faction_id)
                    if base_faction and base_faction.initiative == my_initiative:
                        is_destination = True
                        break
            
            if not is_destination:
                # Check for enemy units
                units_at_hex = self.units_at_hex(neighbor)
                has_enemy = False
                for unit in units_at_hex:
                    if not unit.alive:
                        continue
                    unit_faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                    unit_faction = self.get_faction(unit_faction_id)
                    if unit_faction and unit_faction.initiative != my_initiative:
                        has_enemy = True
                        break
                if has_enemy:
                    continue
                
                # Check for enemy bases
                enemy_base = False
                for base in self.bases.values():
                    if base.location == neighbor:
                        base_faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
                        base_faction = self.get_faction(base_faction_id)
                        if base_faction and base_faction.initiative != my_initiative:
                            enemy_base = True
                            break
                if enemy_base:
                    continue
                
                # Check hex control
                if self.is_hex_controlled_by_other_initiative(neighbor, my_initiative):
                    continue
            
            valid_hexes.append({
                'hex_id': neighbor,
                'is_destination': is_destination
            })
        
        return valid_hexes
    
    def queue_establish_caravan_order(self, origin_base_id: int, dest_base_id: int,
                                       path: List[int], is_sea: bool) -> dict:
        """
        Queue an order to establish a caravan.
        
        Returns {'success': bool, 'error': str}
        """
        from .models.caravan import get_caravan_cost, CaravanTerrainType
        
        # Validate the path
        validation = self.validate_caravan_path(origin_base_id, dest_base_id, path, is_sea)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        # Check if base can perform action
        origin_base = self.get_base(origin_base_id)
        if not origin_base:
            return {'success': False, 'error': 'Invalid origin base'}
        
        # Check if already ordered this action type
        existing_orders = self.get_base_pending_orders(origin_base_id)
        for order in existing_orders:
            if order.get('type') == 'establish_caravan':
                return {'success': False, 'error': 'Already have a pending caravan order'}
        
        # Check resources (skip if infinite resources)
        cost = validation['cost']
        if not self._is_infinite_resources():
            effective = self.get_effective_resources(origin_base_id)
            if effective['effective']['lumber'] < cost['lumber']:
                return {'success': False, 'error': f"Need {cost['lumber']} lumber (have {effective['effective']['lumber']})"}
            if is_sea and effective['effective']['oil'] < cost['oil']:
                return {'success': False, 'error': f"Need {cost['oil']} oil (have {effective['effective']['oil']})"}
        
        # Queue the order
        terrain_type = CaravanTerrainType.SEA if is_sea else CaravanTerrainType.LAND
        dest_base = self.get_base(dest_base_id)
        order = {
            'type': 'establish_caravan',
            'origin_base_id': origin_base_id,
            'dest_base_id': dest_base_id,
            'dest_base_name': dest_base.name if dest_base else f"Base {dest_base_id}",
            'path': path,
            'terrain_type': terrain_type.value,
            'lumber_cost': cost['lumber'],
            'oil_cost': cost['oil'] if is_sea else 0,
        }
        
        if origin_base_id not in self.pending_base_orders:
            self.pending_base_orders[origin_base_id] = []
        self.pending_base_orders[origin_base_id].append(order)
        
        return {'success': True, 'error': '', 'cost': cost}
    
    # ==================== Send Resources ====================
    
    def get_send_resource_destinations(self, base_id: int) -> List[dict]:
        """
        Get all bases that can receive resources from this base via caravan.
        
        Rules:
        - Must have an existing caravan connection
        - Caravan must NOT have been established this turn (pending order)
        """
        base = self.get_base(base_id)
        if not base:
            return []
        
        # Get all caravans connected to this base
        caravans = self.get_caravans_for_base(base_id)
        
        # Check pending orders for newly-established caravans (can't use same turn)
        pending_caravan_dests = set()
        for order in self.get_base_pending_orders(base_id):
            if order.get('type') == 'establish_caravan':
                pending_caravan_dests.add(order.get('dest_base_id'))
        
        destinations = []
        for caravan in caravans:
            # Determine the other base
            if caravan.origin_base_id == base_id:
                other_base_id = caravan.destination_base_id
            else:
                other_base_id = caravan.origin_base_id
            
            # Skip if this caravan was just established this turn
            if other_base_id in pending_caravan_dests:
                continue
            
            other_base = self.get_base(other_base_id)
            if not other_base:
                continue
            
            destinations.append({
                'base_id': other_base_id,
                'base_name': other_base.name,
                'location': other_base.location,
                'caravan_id': caravan.id,
                'caravan_path_length': len(caravan.path)
            })
        
        return destinations
    
    def can_send_resources(self, base_id: int) -> tuple:
        """
        Check if a base can send resources.
        
        Returns (can_send: bool, reasons: List[str])
        """
        base = self.get_base(base_id)
        if not base:
            return False, ['Base not found']
        
        reasons = []
        
        # Check if base has any resources (considering pending)
        effective = self.get_effective_resources(base_id)
        total_resources = (effective['effective']['gold'] + 
                          effective['effective']['lumber'] + 
                          effective['effective']['oil'])
        if total_resources <= 0:
            reasons.append('No resources available')
        
        # Check if base has caravan connections
        destinations = self.get_send_resource_destinations(base_id)
        if not destinations:
            reasons.append('No caravan connections available')
        
        # Check if base is in combat
        if self.base_in_combat(base_id):
            reasons.append('Base is in combat')
        
        # Check if action already queued
        for order in self.get_base_pending_orders(base_id):
            if order.get('type') == 'send_resources':
                reasons.append('Send Resources already queued')
                break
        
        return len(reasons) == 0, reasons
    
    def validate_send_resources(self, base_id: int, dest_base_id: int, 
                                 gold: int = 0, lumber: int = 0, oil: int = 0) -> dict:
        """
        Validate a Send Resources action.
        
        Returns {'valid': bool, 'error': str}
        """
        base = self.get_base(base_id)
        if not base:
            return {'valid': False, 'error': 'Base not found'}
        
        # Check if destination is valid
        destinations = self.get_send_resource_destinations(base_id)
        valid_dest = next((d for d in destinations if d['base_id'] == dest_base_id), None)
        if not valid_dest:
            return {'valid': False, 'error': 'Invalid destination (no caravan or just established)'}
        
        # Check amounts are valid
        if gold < 0 or lumber < 0 or oil < 0:
            return {'valid': False, 'error': 'Cannot send negative resources'}
        
        if gold == 0 and lumber == 0 and oil == 0:
            return {'valid': False, 'error': 'Must send at least one resource'}
        
        # Check if base has enough resources (considering pending) - skip if infinite resources
        if not self._is_infinite_resources():
            effective = self.get_effective_resources(base_id)
            if effective['effective']['gold'] < gold:
                return {'valid': False, 'error': f"Not enough gold (have {effective['effective']['gold']}, need {gold})"}
            if effective['effective']['lumber'] < lumber:
                return {'valid': False, 'error': f"Not enough lumber (have {effective['effective']['lumber']}, need {lumber})"}
            if effective['effective']['oil'] < oil:
                return {'valid': False, 'error': f"Not enough oil (have {effective['effective']['oil']}, need {oil})"}
        
        return {'valid': True, 'error': '', 'caravan_id': valid_dest['caravan_id']}
    
    def queue_send_resources_order(self, base_id: int, dest_base_id: int,
                                    gold: int = 0, lumber: int = 0, oil: int = 0) -> dict:
        """
        Queue an order to send resources via caravan.
        
        Returns {'success': bool, 'error': str}
        """
        # Validate
        validation = self.validate_send_resources(base_id, dest_base_id, gold, lumber, oil)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        # Get destination info
        dest_base = self.get_base(dest_base_id)
        
        order = {
            'type': 'send_resources',
            'dest_base_id': dest_base_id,
            'dest_base_name': dest_base.name if dest_base else 'Unknown',
            'caravan_id': validation['caravan_id'],
            'gold': gold,
            'lumber': lumber,
            'oil': oil,
        }
        
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {'success': True, 'error': ''}
    
    # ==================== Base Actions ====================
    
    def calculate_harvest_yield(self, base_id: int) -> dict:
        """
        Calculate what resources a base would get from a Harvest action.
        
        Income sources:
        - Base hex: +1 gold per gold mine (HEX_GOLD value)
        - Farm hexes: +1 gold per gold mine
        - Mill hexes: +1 lumber + 1 gold per gold mine
        - Oil rig hexes: +1 oil
        
        Returns dict with gold, lumber, oil yields.
        """
        base = self.get_base(base_id)
        if not base:
            return {'gold': 0, 'lumber': 0, 'oil': 0}
        
        gold = 0
        lumber = 0
        oil = 0
        
        # Base hex contributes gold from mines
        base_hex = self.get_hex(base.location)
        if base_hex:
            gold += base_hex.gold  # HEX_GOLD value (number of gold mines)
        
        # Get all expansions for this base
        expansions = self.expansions_for_base(base_id)
        
        for exp in expansions:
            exp_hex = self.get_hex(exp.location)
            if not exp_hex:
                continue
                
            if exp.type.value == 'farm':
                # Farms: +1 gold per gold mine in the farm's hex
                gold += exp_hex.gold
            elif exp.type.value == 'mill':
                # Mills: +1 lumber, +1 gold per gold mine
                lumber += 1
                gold += exp_hex.gold
            elif exp.type.value == 'rig':
                # Oil rigs: +1 oil
                oil += 1
        
        return {'gold': gold, 'lumber': lumber, 'oil': oil}
    
    def get_base_pending_orders(self, base_id: int) -> List[dict]:
        """Get all pending orders for a base."""
        return self.pending_base_orders.get(base_id, [])
    
    def get_base_actions_used(self, base_id: int) -> int:
        """Count how many actions a base has used this turn."""
        return len(self.get_base_pending_orders(base_id))
    
    def get_base_actions_remaining(self, base_id: int) -> int:
        """Calculate remaining actions for a base (tier - used)."""
        base = self.get_base(base_id)
        if not base:
            return 0
        return max(0, base.tier - self.get_base_actions_used(base_id))
    
    def has_pending_action_type(self, base_id: int, action_type: str) -> bool:
        """Check if base already has a pending action of this type."""
        orders = self.get_base_pending_orders(base_id)
        return any(order.get('type') == action_type for order in orders)
    
    def can_queue_action(self, base_id: int, action_type: str) -> Tuple[bool, str]:
        """
        Check if a base action can be queued.
        
        Returns (can_queue, reason_if_not).
        """
        base = self.get_base(base_id)
        if not base:
            return False, "Base not found"
        
        # Check if base is in combat (no actions allowed during combat)
        if self.base_in_combat(base_id):
            return False, "Base is in combat"
        
        # Check if actions remaining
        if self.get_base_actions_remaining(base_id) <= 0:
            return False, f"No actions remaining (tier {base.tier}, {self.get_base_actions_used(base_id)} used)"
        
        # Check if action type already queued (one of each type per turn)
        if self.has_pending_action_type(base_id, action_type):
            return False, f"Already have a pending {action_type} action"
        
        return True, ""
    
    def queue_harvest_order(self, base_id: int) -> dict:
        """
        Queue a Harvest action for a base.
        
        Returns the order details including expected yield.
        """
        can_queue, reason = self.can_queue_action(base_id, 'harvest')
        if not can_queue:
            return {'success': False, 'error': reason}
        
        # Calculate expected yield
        yield_data = self.calculate_harvest_yield(base_id)
        
        # Create the order
        order = {
            'type': 'harvest',
            'base_id': base_id,
            'expected_gold': yield_data['gold'],
            'expected_lumber': yield_data['lumber'],
            'expected_oil': yield_data['oil']
        }
        
        # Add to pending orders
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {
            'success': True,
            'order': order,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    # ==================== Visibility ====================
    
    def is_hex_visible_to_faction(self, hex_id: int, faction_id: int) -> bool:
        """
        Check if a hex is visible to a faction.
        
        Uses the visible_hexes tracking. If not populated yet, 
        falls back to True (all visible for testing).
        """
        faction_visible = self.visible_hexes.get(faction_id)
        if faction_visible is None or len(faction_visible) == 0:
            # Visibility not yet implemented - allow all for now
            return True
        return hex_id in faction_visible
    
    # ==================== Expand Action ====================
    
    # Valid hexside terrains for expansion tracing
    LAND_TRACE_HEXSIDES = {'C', 'F', 'W'}  # Clear, Forest, Fortification
    SEA_TRACE_HEXSIDES = {'O', 'K'}         # Ocean, Coastal Clear
    
    def get_hex_direction(self, from_hex: int, to_hex: int) -> Optional[int]:
        """
        Get the direction index (0-5) from one hex to an adjacent hex.
        
        Returns None if hexes are not adjacent.
        Direction mapping: 0=N, 1=NE, 2=SE, 3=S, 4=SW, 5=NW
        
        Note: This uses diff = to_hex - from_hex, consistent with has_road_between
        which uses from - to. The mappings are sign-flipped accordingly.
        """
        diff = to_hex - from_hex
        
        # Direction map derived from has_road_between (which uses from - to):
        # has_road: 1=N, -1=S, 39=NW, -39=SE, 38=SW, -38=NE
        # Flipping signs for (to - from):
        direction_map = {
            -1: 0,    # N (to is 1 less = moving to lower ID in same column)
            38: 1,    # NE
            39: 2,    # SE
            1: 3,     # S (to is 1 more = moving to higher ID in same column)
            -38: 4,   # SW
            -39: 5,   # NW
        }
        
        return direction_map.get(diff)
    
    def get_hexside_terrain(self, from_hex: int, to_hex: int) -> str:
        """Get the terrain of the hexside between two adjacent hexes."""
        hex_obj = self.get_hex(from_hex)
        if not hex_obj:
            return ''
        
        direction = self.get_hex_direction(from_hex, to_hex)
        if direction is None:
            return ''
        
        # Map direction index to HexSide
        direction_to_side = {
            0: hex_obj.north,
            1: hex_obj.northeast,
            2: hex_obj.southeast,
            3: hex_obj.south,
            4: hex_obj.southwest,
            5: hex_obj.northwest,
        }
        
        side = direction_to_side.get(direction)
        return side.terrain if side else ''
    
    def find_expansion_trace(self, base_id: int, target_hex: int) -> dict:
        """
        Find a valid trace path from a base to a target hex for expansion.
        
        Rules:
        - Path length must be <= base tier
        - Can be land OR sea trace, but not mixed
        - Land: clear, forest, fortification hexsides
        - Sea: ocean, coastal clear hexsides
        
        Returns dict with:
        - valid: bool
        - path: list of hex IDs (if valid)
        - trace_type: 'land' or 'sea' (if valid)
        - error: str (if invalid)
        """
        base = self.get_base(base_id)
        if not base:
            return {'valid': False, 'error': 'Base not found'}
        
        max_distance = base.tier
        start_hex = base.location
        
        if target_hex == start_hex:
            return {'valid': False, 'error': 'Cannot expand to base location'}
        
        # BFS to find shortest valid path
        # We search separately for land and sea traces
        # Land traces can also use roads (bridges) regardless of terrain
        
        for trace_type, valid_hexsides in [('land', self.LAND_TRACE_HEXSIDES), 
                                            ('sea', self.SEA_TRACE_HEXSIDES)]:
            is_land_trace = (trace_type == 'land')
            result = self._bfs_trace(start_hex, target_hex, max_distance, valid_hexsides, is_land_trace)
            if result['valid']:
                result['trace_type'] = trace_type
                return result
        
        return {'valid': False, 'error': f'No valid trace within {max_distance} hexes'}
    
    def _bfs_trace(self, start: int, target: int, max_dist: int, 
                   valid_hexsides: set, check_roads: bool = False) -> dict:
        """
        BFS search for a valid trace path.
        
        Args:
            start: Starting hex ID
            target: Target hex ID
            max_dist: Maximum trace distance
            valid_hexsides: Set of valid hexside terrain codes
            check_roads: If True, also allow hexsides with roads (for land traces)
        """
        from collections import deque
        
        # Queue: (current_hex, path_so_far)
        queue = deque([(start, [])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            # Check if we've reached the target
            if current == target:
                return {'valid': True, 'path': path}
            
            # Don't expand beyond max distance
            if len(path) >= max_dist:
                continue
            
            # Explore adjacent hexes
            for neighbor in self.adjacent_hexes(current):
                if neighbor in visited:
                    continue
                
                # Check hexside terrain
                hexside_terrain = self.get_hexside_terrain(current, neighbor)
                
                # Hexside is valid if:
                # 1. Terrain is in valid_hexsides, OR
                # 2. For land traces, there's a road (bridge)
                is_valid_terrain = hexside_terrain in valid_hexsides
                has_road = check_roads and self.has_road_between(current, neighbor)
                
                if not is_valid_terrain and not has_road:
                    continue
                
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
        
        return {'valid': False, 'error': 'No path found'}
    
    def get_expansion_type_for_hex(self, hex_id: int) -> Optional[str]:
        """
        Determine what type of expansion can be built on a hex.
        
        Returns 'farm', 'mill', 'rig', or None if invalid.
        """
        hex_obj = self.get_hex(hex_id)
        if not hex_obj:
            return None
        
        terrain = hex_obj.terrain
        
        if terrain == 'C':  # Clear
            return 'farm'
        elif terrain == 'F':  # Forest
            return 'mill'
        elif terrain == 'O' and hex_obj.has_oil:  # Ocean with oil
            return 'rig'
        
        return None
    
    def validate_expand(self, base_id: int, target_hex: int) -> Tuple[bool, str, dict]:
        """
        Validate if an expansion can be built.
        
        Returns (is_valid, error_message, details_dict)
        """
        base = self.get_base(base_id)
        if not base:
            return False, 'Base not found', {}
        
        faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
        
        # Check action can be queued
        can_queue, reason = self.can_queue_action(base_id, 'expand')
        if not can_queue:
            return False, reason, {}
        
        # Check cost (2 lumber) - consider pending resources (skip if infinite resources)
        if not self._is_infinite_resources():
            effective = self.get_effective_resources(base_id)
            if effective['effective']['lumber'] < 2:
                return False, f"Not enough lumber (need 2, have {effective['effective']['lumber']} effective)", {}
        
        # Check target hex exists
        target = self.get_hex(target_hex)
        if not target:
            return False, f'Hex {target_hex} not found', {}
        
        # Check visibility
        if not self.is_hex_visible_to_faction(target_hex, faction_id):
            return False, 'Target hex is not visible', {}
        
        # Check no existing base at target
        if self.base_at_hex(target_hex):
            return False, 'Hex already has a base', {}
        
        # Check no existing expansion at target
        if self.expansion_at_hex(target_hex):
            return False, 'Hex already has an expansion', {}
        
        # Check no enemy units at target
        enemies = self.enemies_at_hex(target_hex, faction_id)
        if enemies:
            return False, 'Enemy units present at target hex', {}
        
        # Check hex not controlled by another initiative
        faction = self.get_faction(faction_id)
        if faction:
            my_initiative = faction.initiative
            if self.is_hex_controlled_by_other_initiative(target_hex, my_initiative):
                return False, 'Hex is controlled by another initiative', {}
        
        # Check valid expansion type for terrain
        exp_type = self.get_expansion_type_for_hex(target_hex)
        if not exp_type:
            terrain = target.terrain
            if terrain == 'O' and not target.has_oil:
                return False, 'Ocean hex has no oil deposit', {}
            return False, f'Cannot build expansion on {terrain} terrain', {}
        
        # Check valid trace path
        trace = self.find_expansion_trace(base_id, target_hex)
        if not trace['valid']:
            return False, trace['error'], {}
        
        return True, '', {
            'expansion_type': exp_type,
            'trace_type': trace['trace_type'],
            'trace_path': trace['path'],
            'cost': {'lumber': 2}
        }
    
    def queue_expand_order(self, base_id: int, target_hex: int) -> dict:
        """
        Queue an Expand action for a base.
        
        Returns the order details.
        """
        is_valid, error, details = self.validate_expand(base_id, target_hex)
        if not is_valid:
            return {'success': False, 'error': error}
        
        # Create the order
        order = {
            'type': 'expand',
            'base_id': base_id,
            'target_hex': target_hex,
            'expansion_type': details['expansion_type'],
            'trace_type': details['trace_type'],
            'trace_path': details['trace_path'],
            'cost_lumber': 2
        }
        
        # Add to pending orders
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {
            'success': True,
            'order': order,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    # ==================== Commerce Action ====================
    
    VALID_RESOURCES = {'gold', 'lumber', 'oil'}
    
    @property
    def commerce_cost(self) -> int:
        """Commerce cost from config."""
        from .game_config import get_game_config
        return get_game_config().economic.commerce_cost
    
    @property
    def commerce_gain(self) -> int:
        """Commerce gain from config."""
        from .game_config import get_game_config
        return get_game_config().economic.commerce_gain
    
    def validate_commerce(self, base_id: int, from_resource: str, to_resource: str) -> Tuple[bool, str]:
        """
        Validate if a commerce action can be performed.
        
        Returns (is_valid, error_message).
        """
        base = self.get_base(base_id)
        if not base:
            return False, 'Base not found'
        
        # Validate resource types
        if from_resource not in self.VALID_RESOURCES:
            return False, f'Invalid source resource: {from_resource}'
        if to_resource not in self.VALID_RESOURCES:
            return False, f'Invalid target resource: {to_resource}'
        if from_resource == to_resource:
            return False, 'Source and target resources must be different'
        
        # Check action can be queued
        can_queue, reason = self.can_queue_action(base_id, 'commerce')
        if not can_queue:
            return False, reason
        
        # Check effective resources (current + pending) - skip if infinite resources
        if not self._is_infinite_resources():
            effective = self.get_effective_resources(base_id)
            if effective['effective'][from_resource] < self.commerce_cost:
                return False, f"Not enough {from_resource} (need {self.commerce_cost}, have {effective['effective'][from_resource]})"
        
        return True, ''
    
    def get_commerce_options(self, base_id: int) -> dict:
        """
        Get available commerce conversion options for a base.
        
        Returns dict with each resource and whether it can be converted (has >= 2 effective).
        """
        base = self.get_base(base_id)
        if not base:
            return {'available': [], 'reason': 'Base not found'}
        
        effective = self.get_effective_resources(base_id)
        if not effective:
            return {'available': [], 'reason': 'Could not calculate resources'}
        
        # Check which resources have >= 2 effective
        available = []
        for resource in self.VALID_RESOURCES:
            if effective['effective'][resource] >= self.commerce_cost:
                # This resource can be converted to either of the other two
                targets = [r for r in self.VALID_RESOURCES if r != resource]
                available.append({
                    'from': resource,
                    'amount': effective['effective'][resource],
                    'targets': targets
                })
        
        # Check if action can be queued at all
        can_queue, reason = self.can_queue_action(base_id, 'commerce')
        
        return {
            'available': available,
            'canQueue': can_queue,
            'queueReason': reason if not can_queue else None,
            'cost': self.commerce_cost,
            'gain': self.commerce_gain
        }
    
    def queue_commerce_order(self, base_id: int, from_resource: str, to_resource: str) -> dict:
        """
        Queue a Commerce action for a base.
        
        Converts 2 of from_resource into 1 of to_resource.
        """
        is_valid, error = self.validate_commerce(base_id, from_resource, to_resource)
        if not is_valid:
            return {'success': False, 'error': error}
        
        # Create the order
        order = {
            'type': 'commerce',
            'base_id': base_id,
            'from_resource': from_resource,
            'to_resource': to_resource,
            'cost': self.commerce_cost,
            'gain': self.commerce_gain
        }
        
        # Add to pending orders
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {
            'success': True,
            'order': order,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    # ==================== Upgrade Base Action ====================
    
    MAX_BASE_TIER = 3
    
    def _get_upgrade_cost(self, target_tier: int) -> dict:
        """Get upgrade cost from config."""
        from .game_config import get_upgrade_cost
        return get_upgrade_cost(target_tier)
    
    def _get_upgrade_harvest_req(self, target_tier: int) -> int:
        """Get upgrade harvest requirement from config."""
        from .game_config import get_upgrade_harvest_requirement
        return get_upgrade_harvest_requirement(target_tier)
    
    def get_upgrade_info(self, base_id: int) -> dict:
        """
        Get detailed upgrade information for a base.
        
        Returns costs, requirements, and whether upgrade is possible.
        """
        base = self.get_base(base_id)
        if not base:
            return {'error': 'Base not found'}
        
        current_tier = base.tier
        target_tier = current_tier + 1
        
        # Check if already at max tier
        if current_tier >= self.MAX_BASE_TIER:
            return {
                'currentTier': current_tier,
                'targetTier': None,
                'canUpgrade': False,
                'reason': f'Already at maximum tier ({self.MAX_BASE_TIER})',
                'cost': None,
                'harvestRequirement': None,
                'currentHarvestYield': None
            }
        
        # Get costs and requirements from config
        cost = self._get_upgrade_cost(target_tier)
        harvest_req = self._get_upgrade_harvest_req(target_tier)
        
        # Calculate current harvest yield
        harvest_yield = self.calculate_harvest_yield(base_id)
        total_yield = harvest_yield['gold'] + harvest_yield['lumber'] + harvest_yield['oil']
        
        # Check effective resources
        effective = self.get_effective_resources(base_id)
        eff_gold = effective['effective']['gold'] if effective else 0
        eff_lumber = effective['effective']['lumber'] if effective else 0
        eff_oil = effective['effective']['oil'] if effective else 0
        
        # Determine if can upgrade
        reasons = []
        
        # Check action availability
        can_queue, queue_reason = self.can_queue_action(base_id, 'upgrade')
        if not can_queue:
            reasons.append(queue_reason)
        
        # Check harvest requirement
        if total_yield < harvest_req:
            reasons.append(f'Harvest yield too low (need {harvest_req}, have {total_yield})')
        
        # Check resource costs (skip if infinite resources)
        if not self._is_infinite_resources():
            if eff_gold < cost.get('gold', 0):
                reasons.append(f"Not enough gold (need {cost['gold']}, have {eff_gold})")
            if eff_lumber < cost.get('lumber', 0):
                reasons.append(f"Not enough lumber (need {cost['lumber']}, have {eff_lumber})")
            if eff_oil < cost.get('oil', 0):
                reasons.append(f"Not enough oil (need {cost['oil']}, have {eff_oil})")
        
        return {
            'currentTier': current_tier,
            'targetTier': target_tier,
            'canUpgrade': len(reasons) == 0,
            'reason': reasons[0] if reasons else None,
            'reasons': reasons,
            'cost': cost,
            'harvestRequirement': harvest_req,
            'currentHarvestYield': total_yield,
            'harvestBreakdown': harvest_yield,
            'effectiveResources': {
                'gold': eff_gold,
                'lumber': eff_lumber,
                'oil': eff_oil
            }
        }
    
    def validate_upgrade(self, base_id: int) -> Tuple[bool, str, dict]:
        """
        Validate if a base can be upgraded.
        
        Returns (is_valid, error_message, details_dict).
        """
        info = self.get_upgrade_info(base_id)
        
        if 'error' in info:
            return False, info['error'], {}
        
        if not info['canUpgrade']:
            return False, info['reason'], info
        
        return True, '', info
    
    def queue_upgrade_order(self, base_id: int) -> dict:
        """
        Queue an Upgrade Base action.
        """
        is_valid, error, info = self.validate_upgrade(base_id)
        if not is_valid:
            return {'success': False, 'error': error, 'info': info}
        
        # Create the order
        order = {
            'type': 'upgrade',
            'base_id': base_id,
            'from_tier': info['currentTier'],
            'to_tier': info['targetTier'],
            'cost_gold': info['cost']['gold'],
            'cost_lumber': info['cost']['lumber'],
            'cost_oil': info['cost']['oil']
        }
        
        # Add to pending orders
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {
            'success': True,
            'order': order,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    # ==================== Rest Unit ====================
    
    def get_units_at_base(self, base_id: int) -> List:
        """Get all living units at a base's location."""
        base = self.get_base(base_id)
        if not base:
            return []
        return [u for u in self.units.values() if u.alive and u.location == base.location]
    
    def get_restable_units_at_base(self, base_id: int) -> List[dict]:
        """
        Get units at base that could potentially be rested.
        Returns list of dicts with unit info and restability status.
        """
        base = self.get_base(base_id)
        if not base:
            return []
        
        units_at_base = self.get_units_at_base(base_id)
        result = []
        
        for unit in units_at_base:
            # Check if unit belongs to same faction as base
            unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            base_faction = base.faction.value if hasattr(base.faction, 'value') else base.faction
            if unit_faction != base_faction:
                result.append({
                    'unit_id': unit.id,
                    'name': unit.name,
                    'hp': unit.hp,
                    'max_hp': unit.max_hp,
                    'can_rest': False,
                    'reason': 'Unit belongs to different faction'
                })
                continue
            
            # Check if unit is at full HP
            if unit.hp >= unit.max_hp:
                result.append({
                    'unit_id': unit.id,
                    'name': unit.name,
                    'hp': unit.hp,
                    'max_hp': unit.max_hp,
                    'can_rest': False,
                    'reason': 'Unit is at full HP'
                })
                continue
            
            # Check if unit has pending movement order
            has_movement = any(
                o.unit_id == unit.id 
                for o in self.orders.values()
            )
            if has_movement:
                result.append({
                    'unit_id': unit.id,
                    'name': unit.name,
                    'hp': unit.hp,
                    'max_hp': unit.max_hp,
                    'can_rest': False,
                    'reason': 'Unit has pending movement order'
                })
                continue
            
            # Check if unit is already being rested by this or another base
            is_rested = self.is_unit_being_rested(unit.id)
            if is_rested:
                result.append({
                    'unit_id': unit.id,
                    'name': unit.name,
                    'hp': unit.hp,
                    'max_hp': unit.max_hp,
                    'can_rest': False,
                    'reason': 'Unit is already being rested'
                })
                continue
            
            # Unit can be rested
            heal_amount = (unit.max_hp + 3) // 4  # Quarter rounded up
            result.append({
                'unit_id': unit.id,
                'name': unit.name,
                'hp': unit.hp,
                'max_hp': unit.max_hp,
                'heal_amount': heal_amount,
                'new_hp': min(unit.hp + heal_amount, unit.max_hp),
                'can_rest': True,
                'reason': ''
            })
        
        return result
    
    def is_unit_being_rested(self, unit_id: int) -> bool:
        """Check if a unit is targeted by any Rest Unit order."""
        for base_id, orders in self.pending_base_orders.items():
            for order in orders:
                if order.get('type') == 'rest' and order.get('unit_id') == unit_id:
                    return True
        return False
    
    def get_rest_order_for_unit(self, unit_id: int) -> Optional[dict]:
        """Get the rest order targeting this unit, if any."""
        for base_id, orders in self.pending_base_orders.items():
            for order in orders:
                if order.get('type') == 'rest' and order.get('unit_id') == unit_id:
                    return {'base_id': base_id, 'order': order}
        return None
    
    def validate_rest_unit(self, base_id: int, unit_id: int) -> Tuple[bool, str, dict]:
        """
        Validate if a Rest Unit action can be queued.
        
        Returns (is_valid, error_message, info_dict)
        """
        base = self.get_base(base_id)
        if not base:
            return False, 'Base not found', {}
        
        # Check if base is in combat
        if self.base_in_combat(base_id):
            return False, 'Base is in combat', {}
        
        # Check if this action type is already queued
        can_queue, error = self.can_queue_action(base_id, 'rest')
        if not can_queue:
            return False, error, {}
        
        # Check gold cost (need 2 gold effective) - skip if infinite resources
        if not self._is_infinite_resources():
            effective = self.get_effective_resources(base_id)
            if effective['effective']['gold'] < 2:
                return False, 'Not enough gold (need 2)', {'effective_gold': effective['effective']['gold']}
        
        # Check unit exists
        unit = self.get_unit(unit_id)
        if not unit or not unit.alive:
            return False, 'Unit not found or dead', {}
        
        # Check unit is at base location
        if unit.location != base.location:
            return False, 'Unit is not at this base', {}
        
        # Check unit belongs to same faction
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        base_faction = base.faction.value if hasattr(base.faction, 'value') else base.faction
        if unit_faction != base_faction:
            return False, 'Unit belongs to different faction', {}
        
        # Check unit HP
        if unit.hp >= unit.max_hp:
            return False, 'Unit is already at full HP', {'hp': unit.hp, 'max_hp': unit.max_hp}
        
        # Check unit doesn't have pending movement
        has_movement = any(o.unit_id == unit_id for o in self.orders.values())
        if has_movement:
            return False, 'Unit has pending movement order (cancel movement first)', {}
        
        # Check unit isn't already being rested
        if self.is_unit_being_rested(unit_id):
            return False, 'Unit is already being rested', {}
        
        # Calculate healing
        heal_amount = (unit.max_hp + 3) // 4  # Quarter rounded up
        new_hp = min(unit.hp + heal_amount, unit.max_hp)
        
        return True, '', {
            'unit_id': unit_id,
            'unit_name': unit.name,
            'current_hp': unit.hp,
            'max_hp': unit.max_hp,
            'heal_amount': heal_amount,
            'new_hp': new_hp,
            'cost_gold': 2
        }
    
    def queue_rest_unit_order(self, base_id: int, unit_id: int) -> dict:
        """
        Queue a Rest Unit action.
        """
        is_valid, error, info = self.validate_rest_unit(base_id, unit_id)
        if not is_valid:
            return {'success': False, 'error': error, 'info': info}
        
        # Create the order
        order = {
            'type': 'rest',
            'base_id': base_id,
            'unit_id': unit_id,
            'unit_name': info['unit_name'],
            'heal_amount': info['heal_amount'],
            'cost_gold': 2
        }
        
        # Add to pending orders
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {
            'success': True,
            'order': order,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    # ==================== BUILD UNIT ====================
    
    def get_pending_build_count(self, faction_id: int) -> int:
        """Count pending Build Unit orders for a faction across all bases."""
        count = 0
        faction_bases = self.bases_by_faction(faction_id)
        for base in faction_bases:
            orders = self.pending_base_orders.get(base.id, [])
            count += sum(1 for o in orders if o.get('type') == 'build_unit')
        return count
    
    def get_faction_effective_food_surplus(self, faction_id: int) -> int:
        """
        Get effective food surplus accounting for pending build orders.
        
        Food surplus = food limit - unit count - pending builds
        """
        status = self.faction_food_status(faction_id)
        pending_builds = self.get_pending_build_count(faction_id)
        return status['food_surplus'] - pending_builds
    
    def get_buildable_units(self, base_id: int) -> List[dict]:
        """
        Get all units that can potentially be built at this base.
        
        Returns list of dicts with unit info, buildability status, and costs.
        """
        base = self.get_base(base_id)
        if not base:
            return []
        
        faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
        
        # Get faction's buildable units
        faction_units = self.faction_buildables.get(faction_id, {})
        if not faction_units:
            return []
        
        # Get effective resources
        effective = self.get_effective_resources(base_id)
        eff_gold = effective['effective']['gold']
        eff_lumber = effective['effective']['lumber']
        eff_oil = effective['effective']['oil']
        
        # Get effective food surplus
        food_surplus = self.get_faction_effective_food_surplus(faction_id)
        
        # Check if already have a build_unit order queued
        has_build_order = self.has_pending_action_type(base_id, 'build_unit')
        
        result = []
        for unit_name, max_tier in faction_units.items():
            # Get unit stats
            stats = self.get_unit_stats(unit_name)
            if not stats:
                continue
            
            # Build info dict
            info = {
                'unit_name': unit_name,
                'max_tier': max_tier,
                'gold_cost': stats.gold_cost,
                'lumber_cost': stats.lumber_cost,
                'oil_cost': stats.oil_cost,
                'min_tier': stats.min_tier,
                'stats': {
                    'max_hp': stats.max_hp,
                    'combat': stats.combat,
                    'category': stats.category.value if hasattr(stats.category, 'value') else stats.category,
                    'unit_type': stats.unit_type.value if hasattr(stats.unit_type, 'value') else stats.unit_type,
                    'movement': stats.movement,
                    'light_armor': stats.light_armor,
                    'heavy_armor': stats.heavy_armor,
                    'natural_armor': stats.natural_armor,
                },
                'can_build': True,
                'reasons': []
            }
            
            # Check base tier
            if base.tier < stats.min_tier:
                info['can_build'] = False
                info['reasons'].append(f'Requires Tier {stats.min_tier} base')
            
            # Check resources (skip if infinite resources)
            if not self._is_infinite_resources():
                if eff_gold < stats.gold_cost:
                    info['can_build'] = False
                    info['reasons'].append(f'Need {stats.gold_cost} gold (have {eff_gold})')
                if eff_lumber < stats.lumber_cost:
                    info['can_build'] = False
                    info['reasons'].append(f'Need {stats.lumber_cost} lumber (have {eff_lumber})')
                if eff_oil < stats.oil_cost:
                    info['can_build'] = False
                    info['reasons'].append(f'Need {stats.oil_cost} oil (have {eff_oil})')
            
            # Check food cap
            if food_surplus <= 0:
                info['can_build'] = False
                info['reasons'].append('Food cap reached')
            
            # Check if already have build order queued at this base
            if has_build_order:
                info['can_build'] = False
                info['reasons'].append('Already have Build Unit queued')
            
            result.append(info)
        
        # Sort by tier requirement, then name
        result.sort(key=lambda x: (x['min_tier'], x['unit_name']))
        return result
    
    def validate_build_unit(self, base_id: int, unit_name: str) -> Tuple[bool, str, dict]:
        """
        Validate if a Build Unit action can be queued.
        
        Returns (is_valid, error_message, info_dict)
        """
        base = self.get_base(base_id)
        if not base:
            return False, 'Base not found', {}
        
        # Check if base is in combat
        if self.base_in_combat(base_id):
            return False, 'Base is in combat', {}
        
        # Check if this action type is already queued
        can_queue, error = self.can_queue_action(base_id, 'build_unit')
        if not can_queue:
            return False, error, {}
        
        faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
        
        # Check if faction can build this unit type
        faction_units = self.faction_buildables.get(faction_id, {})
        if unit_name not in faction_units:
            return False, f'{unit_name} cannot be built by this faction', {}
        
        # Get unit stats
        stats = self.get_unit_stats(unit_name)
        if not stats:
            return False, f'Unit stats not found for {unit_name}', {}
        
        # Check base tier
        if base.tier < stats.min_tier:
            return False, f'Requires Tier {stats.min_tier} base (have Tier {base.tier})', {
                'min_tier': stats.min_tier,
                'base_tier': base.tier
            }
        
        # Check effective resources (skip if infinite resources enabled)
        if not self._is_infinite_resources():
            effective = self.get_effective_resources(base_id)
            eff_gold = effective['effective']['gold']
            eff_lumber = effective['effective']['lumber']
            eff_oil = effective['effective']['oil']
            
            if eff_gold < stats.gold_cost:
                return False, f'Not enough gold (need {stats.gold_cost}, have {eff_gold})', {}
            if eff_lumber < stats.lumber_cost:
                return False, f'Not enough lumber (need {stats.lumber_cost}, have {eff_lumber})', {}
            if eff_oil < stats.oil_cost:
                return False, f'Not enough oil (need {stats.oil_cost}, have {eff_oil})', {}
        
        # Check food cap
        food_surplus = self.get_faction_effective_food_surplus(faction_id)
        if food_surplus <= 0:
            return False, 'Food cap reached - cannot build more units', {
                'food_surplus': food_surplus
            }
        
        return True, '', {
            'unit_name': unit_name,
            'gold_cost': stats.gold_cost,
            'lumber_cost': stats.lumber_cost,
            'oil_cost': stats.oil_cost,
            'max_tier': faction_units[unit_name]
        }
    
    def queue_build_unit_order(self, base_id: int, unit_name: str) -> dict:
        """
        Queue a Build Unit action.
        """
        is_valid, error, info = self.validate_build_unit(base_id, unit_name)
        if not is_valid:
            return {'success': False, 'error': error, 'info': info}
        
        # Create the order
        order = {
            'type': 'build_unit',
            'base_id': base_id,
            'unit_name': unit_name,
            'gold_cost': info['gold_cost'],
            'lumber_cost': info['lumber_cost'],
            'oil_cost': info['oil_cost']
        }
        
        # Add to pending orders
        if base_id not in self.pending_base_orders:
            self.pending_base_orders[base_id] = []
        self.pending_base_orders[base_id].append(order)
        
        return {
            'success': True,
            'order': order,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    def create_unit(self, unit_name: str, faction_id: int, location: int) -> Optional[Unit]:
        """
        Create a new unit and add it to the game state.
        
        Args:
            unit_name: The unit type name (e.g., 'Grunt')
            faction_id: The faction that owns this unit
            location: The hex where the unit appears
        
        Returns the created Unit or None if failed.
        """
        from .models.enums import UnitCategory, UnitType
        
        stats = self.get_unit_stats(unit_name)
        if not stats:
            return None
        
        # Generate new unit ID
        new_id = max(self.units.keys(), default=-1) + 1
        
        # Create the unit with full stats
        unit = Unit(
            id=new_id,
            name=unit_name,
            faction=FactionId(faction_id),
            max_hp=stats.max_hp,
            combat=stats.combat,
            category=stats.category,
            unit_type=stats.unit_type,
            light_armor_max=stats.light_armor,
            heavy_armor=stats.heavy_armor,
            natural_armor=stats.natural_armor,
            movement_max=stats.movement,
            vision=stats.vision,
            stealth=stats.stealth,
            hp=stats.max_hp,  # Full HP
            location=location,
            alive=True,
            tier=0,  # New units start at tier 0
        )
        
        # Add to game state
        self.units[new_id] = unit
        
        return unit
    
    def create_expansion(self, base_id: int, hex_id: int, exp_type: str) -> Optional[Expansion]:
        """
        Create a new expansion and add it to the game state.
        
        Args:
            base_id: The base this expansion belongs to
            hex_id: The hex where the expansion is built
            exp_type: 'farm', 'mill', or 'rig'
        
        Returns the created Expansion or None if failed.
        """
        from .models.orders import ExpansionType
        
        # Determine expansion type enum
        type_map = {
            'farm': ExpansionType.FARM,
            'mill': ExpansionType.LUMBER_MILL,
            'rig': ExpansionType.OIL_RIG
        }
        exp_type_enum = type_map.get(exp_type)
        if not exp_type_enum:
            return None
        
        # Generate new expansion ID
        new_id = max(self.expansions.keys(), default=-1) + 1
        
        # Create the expansion
        expansion = Expansion(
            id=new_id,
            type=exp_type_enum,
            location=hex_id,
            base_id=base_id
        )
        
        # Add to game state
        self.expansions[new_id] = expansion
        
        # Add to base's expansion list
        base = self.get_base(base_id)
        if base:
            base.expansions.append(new_id)
        
        # Update hex data
        hex_obj = self.get_hex(hex_id)
        if hex_obj:
            if exp_type == 'farm':
                hex_obj.farm = base_id
            elif exp_type == 'mill':
                hex_obj.mill = base_id
            elif exp_type == 'rig':
                hex_obj.rig = base_id
        
        return expansion
    
    def cancel_last_base_order(self, base_id: int) -> dict:
        """
        Cancel the last queued order for a base (LIFO).
        
        Returns the cancelled order or error.
        """
        orders = self.pending_base_orders.get(base_id, [])
        if not orders:
            return {'success': False, 'error': 'No pending orders to cancel'}
        
        cancelled = orders.pop()
        return {
            'success': True,
            'cancelled_order': cancelled,
            'actions_remaining': self.get_base_actions_remaining(base_id)
        }
    
    def clear_base_orders(self, base_id: int) -> int:
        """Clear all pending orders for a base. Returns count cleared."""
        count = len(self.pending_base_orders.get(base_id, []))
        self.pending_base_orders[base_id] = []
        return count
    
    def clear_all_base_orders(self) -> int:
        """Clear all pending base orders. Returns total count cleared."""
        total = sum(len(orders) for orders in self.pending_base_orders.values())
        self.pending_base_orders.clear()
        return total
    
    def get_pending_resources(self, base_id: int) -> dict:
        """
        Calculate the pending resource changes from queued orders.
        
        Returns dict with pending gold, lumber, oil (only negative/cost values).
        
        NOTE: As of the simplified base action model:
        - Harvest is automatic (not player-queued), so no pending changes
        - Commerce output is delayed to next turn, so only cost is shown
        - All pending values should be negative (spending resources)
        """
        pending = {'gold': 0, 'lumber': 0, 'oil': 0}
        
        for order in self.get_base_pending_orders(base_id):
            # Harvest is now automatic - skip any legacy harvest orders
            if order['type'] == 'harvest':
                # No longer contributes to pending resources (auto-harvest)
                continue
            elif order['type'] == 'expand':
                # Expand costs 2 lumber
                pending['lumber'] -= 2
            elif order['type'] == 'commerce':
                # Commerce: spend 2 of one resource
                # Output is delayed to next turn, so only show cost
                from_resource = order.get('from_resource')
                if from_resource:
                    pending[from_resource] -= 2
                # NOTE: The gain (+1 to target) happens at resolution,
                # but is only available NEXT turn, so not shown as pending
            elif order['type'] == 'upgrade':
                # Upgrade costs gold, lumber, and oil
                pending['gold'] -= order.get('cost_gold', 0)
                pending['lumber'] -= order.get('cost_lumber', 0)
                pending['oil'] -= order.get('cost_oil', 0)
            elif order['type'] == 'rest':
                # Rest Unit costs 2 gold
                pending['gold'] -= order.get('cost_gold', 2)
            elif order['type'] == 'build_unit':
                # Build Unit costs gold, lumber, and oil
                pending['gold'] -= order.get('gold_cost', 0)
                pending['lumber'] -= order.get('lumber_cost', 0)
                pending['oil'] -= order.get('oil_cost', 0)
            elif order['type'] == 'establish_caravan':
                # Establish Caravan costs lumber (and oil for sea)
                pending['lumber'] -= order.get('lumber_cost', 0)
                pending['oil'] -= order.get('oil_cost', 0)
            elif order['type'] == 'send_resources':
                # Send Resources - resources being sent are unavailable
                pending['gold'] -= order.get('gold', 0)
                pending['lumber'] -= order.get('lumber', 0)
                pending['oil'] -= order.get('oil', 0)
        
        return pending
    
    def get_effective_resources(self, base_id: int) -> dict:
        """
        Get base resources including pending changes.
        
        Returns dict with current, pending, and effective totals.
        """
        base = self.get_base(base_id)
        if not base:
            return None
        
        pending = self.get_pending_resources(base_id)
        
        return {
            'current': {'gold': base.gold, 'lumber': base.lumber, 'oil': base.oil},
            'pending': pending,
            'effective': {
                'gold': base.gold + pending['gold'],
                'lumber': base.lumber + pending['lumber'],
                'oil': base.oil + pending['oil']
            }
        }
    
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

