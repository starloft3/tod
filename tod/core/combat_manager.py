"""
Combat Manager for Tides of Darkness.

Tracks and manages all active combats in the game. This module handles:
- Detection of combat hexes (2+ initiatives present)
- Combat state tracking (new vs continuing, round fought status)
- Hexside control (ONLY for active combat hexes)
- Combat timing rules (when to resolve based on initiative)

Design Principle: Hexside control is a COMBAT-ONLY mechanic.
Non-combat hexes have no hexside control state.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Tuple, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .game_state import GameState
    from .models import Unit

from .models.enums import Direction


class CombatType(Enum):
    """Type of combat based on unit composition."""
    GROUND_ONLY = "ground_only"
    SEA_ONLY = "sea_only"
    AIR_ONLY = "air_only"
    GROUND_VS_SEA = "ground_vs_sea"  # Mixed - special targeting rules
    MIXED_FULL = "mixed_full"  # Both sides have ground AND sea


@dataclass
class ActiveCombat:
    """
    Tracks state for an active combat hex.
    
    This is created when a combat hex is detected and destroyed when
    combat ends (only one initiative remains).
    """
    hex_id: int
    
    # Combat state
    is_new: bool = True  # First round of combat (not yet resolved)
    round_fought_this_alignment: bool = False  # Has combat round happened this Horde/Alliance round?
    
    # Hexside control: direction -> initiative value controlling that hexside
    # Only populated for active combat hexes
    hexside_control: Dict[Direction, int] = field(default_factory=dict)
    
    # Participating initiatives (for timing calculations)
    participating_initiatives: Set[int] = field(default_factory=set)
    
    # Track which initiative triggered combat (lowest among participants)
    lowest_horde_initiative: int = -1
    lowest_alliance_initiative: int = -1
    
    def get_controlled_hexsides(self, initiative: int) -> List[Direction]:
        """Get all hexsides controlled by a specific initiative."""
        return [d for d, ctrl in self.hexside_control.items() if ctrl == initiative]
    
    def can_exit_through(self, direction: Direction, unit_initiative: int) -> bool:
        """Check if a unit can exit through a specific hexside."""
        if direction not in self.hexside_control:
            return True  # Uncontrolled = anyone can use
        return self.hexside_control[direction] == unit_initiative
    
    def set_hexside_control(self, direction: Direction, initiative: int) -> None:
        """Set control of a hexside."""
        self.hexside_control[direction] = initiative
    
    def mark_round_fought(self) -> None:
        """Mark that a combat round has been fought this alignment round."""
        self.round_fought_this_alignment = True
        self.is_new = False  # After first round, combat is no longer "new"
    
    def reset_for_new_alignment_round(self) -> None:
        """Reset the round-fought flag for a new alignment round."""
        self.round_fought_this_alignment = False


@dataclass
class CombatManager:
    """
    Manages all active combats in the game.
    
    Responsibilities:
    - Detect and track combat hexes
    - Manage hexside control (combat-only)
    - Determine combat timing (when rounds resolve)
    - Provide interface for combat resolution
    """
    
    # Active combats keyed by hex_id
    active_combats: Dict[int, ActiveCombat] = field(default_factory=dict)
    
    # Reference to game state (set during initialization)
    _game_state: Optional['GameState'] = field(default=None, repr=False)
    
    def set_game_state(self, state: 'GameState') -> None:
        """Set reference to game state."""
        self._game_state = state
    
    # ==================== Combat Detection ====================
    
    def detect_combats(self) -> List[int]:
        """
        Scan all hexes and detect/update combat hexes.
        Returns list of hex IDs with active combat.
        
        A combat exists when 2+ different initiatives have living units in the same hex.
        """
        if not self._game_state:
            return []
        
        state = self._game_state
        combat_hexes = []
        
        # Find all hexes with units
        hex_units: Dict[int, List['Unit']] = {}
        for unit in state.units.values():
            if unit.alive:
                if unit.location not in hex_units:
                    hex_units[unit.location] = []
                hex_units[unit.location].append(unit)
        
        # Check each hex for multiple initiatives
        for hex_id, units in hex_units.items():
            initiatives = self._get_initiatives_at_hex(units)
            
            if len(initiatives) >= 2:
                # This is a combat hex
                combat_hexes.append(hex_id)
                
                if hex_id not in self.active_combats:
                    # New combat - create tracking
                    self._create_combat(hex_id, units, initiatives)
                else:
                    # Existing combat - update participants
                    self.active_combats[hex_id].participating_initiatives = initiatives
            else:
                # Not a combat hex (anymore)
                if hex_id in self.active_combats:
                    self._end_combat(hex_id)
        
        return combat_hexes
    
    def _get_initiatives_at_hex(self, units: List['Unit']) -> Set[int]:
        """Get set of initiatives present in a list of units."""
        if not self._game_state:
            return set()
        
        initiatives = set()
        for unit in units:
            faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            faction = self._game_state.factions.get(faction_id)
            if faction:
                initiatives.add(faction.initiative)
        return initiatives
    
    def _create_combat(self, hex_id: int, units: List['Unit'], initiatives: Set[int]) -> ActiveCombat:
        """Create a new active combat."""
        combat = ActiveCombat(
            hex_id=hex_id,
            is_new=True,
            participating_initiatives=initiatives
        )
        
        # Initialize hexside control
        self._initialize_hexside_control(combat, units)
        
        # Calculate lowest initiatives for timing
        self._update_lowest_initiatives(combat)
        
        self.active_combats[hex_id] = combat
        return combat
    
    def _initialize_hexside_control(self, combat: ActiveCombat, units: List['Unit']) -> None:
        """
        Initialize hexside control for a new combat.
        
        Rules:
        - Attackers control hexsides they entered through
        - Defenders control all other hexsides
        """
        if not self._game_state:
            return
        
        # Find defenders (units already in hex) and attackers (just arrived)
        defenders: List['Unit'] = []
        attackers: List['Unit'] = []
        
        for unit in units:
            if unit.previous_location == unit.location:
                defenders.append(unit)
            else:
                attackers.append(unit)
        
        # Get defender initiative (should all be same initiative if they were peacefully coexisting)
        defender_initiative = -1
        if defenders:
            faction_id = defenders[0].faction.value if hasattr(defenders[0].faction, 'value') else defenders[0].faction
            faction = self._game_state.factions.get(faction_id)
            if faction:
                defender_initiative = faction.initiative
        
        # Start with defenders controlling all hexsides
        for direction in Direction:
            if defender_initiative >= 0:
                combat.hexside_control[direction] = defender_initiative
        
        # Attackers claim hexsides they entered through
        for attacker in attackers:
            direction = self._get_entry_direction(combat.hex_id, attacker.previous_location)
            if direction:
                faction_id = attacker.faction.value if hasattr(attacker.faction, 'value') else attacker.faction
                faction = self._game_state.factions.get(faction_id)
                if faction:
                    combat.hexside_control[direction] = faction.initiative
    
    def _get_entry_direction(self, to_hex: int, from_hex: int) -> Optional[Direction]:
        """Determine which direction a unit entered from."""
        diff = to_hex - from_hex
        direction_map = {
            -1: Direction.N,
            1: Direction.S,
            -39: Direction.NW,
            39: Direction.SE,
            -38: Direction.NE,
            38: Direction.SW,
        }
        return direction_map.get(diff)
    
    def _update_lowest_initiatives(self, combat: ActiveCombat) -> None:
        """Update the lowest Horde and Alliance initiatives in a combat."""
        if not self._game_state:
            return
        
        horde_inits = []
        alliance_inits = []
        
        for init in combat.participating_initiatives:
            # Find a faction with this initiative to check alignment
            for faction in self._game_state.factions.values():
                if faction.initiative == init:
                    faction_id = faction.id
                    if self._game_state.is_horde_faction(faction_id):
                        horde_inits.append(init)
                    else:
                        alliance_inits.append(init)
                    break
        
        combat.lowest_horde_initiative = min(horde_inits) if horde_inits else -1
        combat.lowest_alliance_initiative = min(alliance_inits) if alliance_inits else -1
    
    def _end_combat(self, hex_id: int) -> None:
        """End a combat (only one initiative remains)."""
        if hex_id in self.active_combats:
            del self.active_combats[hex_id]
    
    # ==================== Combat Timing ====================
    
    def get_combats_to_resolve_after_initiative(
        self, 
        initiative: int, 
        round_side: str
    ) -> List[int]:
        """
        Get combat hexes that should resolve after the given initiative's turn.
        
        Rules:
        - Combat resolves after the lowest initiative of the current alignment
          that is involved in the combat.
        - Each combat gets exactly one round per alignment round.
        """
        combats_to_resolve = []
        
        for hex_id, combat in self.active_combats.items():
            # Skip if already fought this alignment round
            if combat.round_fought_this_alignment:
                continue
            
            # Check if this initiative triggers the combat
            if round_side == "HORDE":
                if combat.lowest_horde_initiative == initiative:
                    combats_to_resolve.append(hex_id)
            else:  # ALLIANCE
                if combat.lowest_alliance_initiative == initiative:
                    combats_to_resolve.append(hex_id)
        
        return combats_to_resolve
    
    def get_combats_for_end_of_round(self, round_side: str) -> List[int]:
        """
        Get combat hexes that need resolution at end of alignment round.
        
        This catches combats where no faction of the current alignment is involved.
        """
        combats_to_resolve = []
        
        for hex_id, combat in self.active_combats.items():
            if combat.round_fought_this_alignment:
                continue
            
            # Check if there's no participant from this alignment
            if round_side == "HORDE" and combat.lowest_horde_initiative < 0:
                combats_to_resolve.append(hex_id)
            elif round_side == "ALLIANCE" and combat.lowest_alliance_initiative < 0:
                combats_to_resolve.append(hex_id)
        
        return combats_to_resolve
    
    def reset_for_new_alignment_round(self) -> None:
        """Reset all combats for a new alignment round."""
        for combat in self.active_combats.values():
            combat.reset_for_new_alignment_round()
    
    # ==================== Combat State Queries ====================
    
    def is_combat_hex(self, hex_id: int) -> bool:
        """Check if a hex is currently a combat hex."""
        return hex_id in self.active_combats
    
    def get_combat(self, hex_id: int) -> Optional[ActiveCombat]:
        """Get the active combat at a hex, if any."""
        return self.active_combats.get(hex_id)
    
    def is_new_combat(self, hex_id: int) -> bool:
        """Check if a combat is new (first round not yet fought)."""
        combat = self.active_combats.get(hex_id)
        return combat.is_new if combat else False
    
    def get_hexside_control(self, hex_id: int, direction: Direction) -> int:
        """
        Get the initiative controlling a hexside.
        Returns -1 if not a combat hex or hexside uncontrolled.
        """
        combat = self.active_combats.get(hex_id)
        if not combat:
            return -1
        return combat.hexside_control.get(direction, -1)
    
    def can_unit_exit(self, hex_id: int, direction: Direction, unit: 'Unit') -> bool:
        """
        Check if a unit can exit a combat hex through a specific hexside.
        
        Returns True if:
        - Hex is not a combat hex (no restrictions)
        - Unit's initiative controls that hexside
        """
        if hex_id not in self.active_combats:
            return True  # Not a combat hex, no restrictions
        
        combat = self.active_combats[hex_id]
        
        if not self._game_state:
            return False
        
        faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        faction = self._game_state.factions.get(faction_id)
        if not faction:
            return False
        
        return combat.can_exit_through(direction, faction.initiative)
    
    # ==================== Combat Classification ====================
    
    def get_combat_type(self, hex_id: int) -> CombatType:
        """
        Determine the type of combat based on unit composition.
        
        Used for mixed combat rules (sea vs ground targeting).
        """
        if not self._game_state or hex_id not in self.active_combats:
            return CombatType.GROUND_ONLY
        
        combat = self.active_combats[hex_id]
        units = self._game_state.units_at_hex(hex_id)
        
        # Group units by initiative and type
        init_types: Dict[int, Set[str]] = {}
        
        for unit in units:
            faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            faction = self._game_state.factions.get(faction_id)
            if not faction:
                continue
            
            init = faction.initiative
            if init not in init_types:
                init_types[init] = set()
            
            # Classify by unit type
            unit_type = unit.unit_type.value if hasattr(unit.unit_type, 'value') else unit.unit_type
            if unit_type == 0:  # TYPE_GROUND
                init_types[init].add('ground')
            elif unit_type == 1:  # TYPE_AIR
                init_types[init].add('air')
            elif unit_type == 2:  # TYPE_SEA
                init_types[init].add('sea')
        
        # Analyze composition
        has_ground = any('ground' in types for types in init_types.values())
        has_sea = any('sea' in types for types in init_types.values())
        has_air = any('air' in types for types in init_types.values())
        
        # Check if both sides have both ground and sea
        sides_with_both = sum(1 for types in init_types.values() 
                              if 'ground' in types and 'sea' in types)
        
        if sides_with_both >= 2:
            return CombatType.MIXED_FULL
        
        if has_ground and has_sea:
            return CombatType.GROUND_VS_SEA
        
        if has_sea and not has_ground:
            return CombatType.SEA_ONLY
        
        if has_air and not has_ground and not has_sea:
            return CombatType.AIR_ONLY
        
        return CombatType.GROUND_ONLY
    
    # ==================== Unit Classification ====================
    
    def get_defenders(self, hex_id: int) -> List['Unit']:
        """Get units that were already in the hex (defenders)."""
        if not self._game_state:
            return []
        
        units = self._game_state.units_at_hex(hex_id)
        return [u for u in units if u.previous_location == u.location]
    
    def get_attackers(self, hex_id: int) -> List['Unit']:
        """Get units that just entered the hex (attackers)."""
        if not self._game_state:
            return []
        
        units = self._game_state.units_at_hex(hex_id)
        return [u for u in units if u.previous_location != u.location]
    
    def get_units_by_initiative(self, hex_id: int) -> Dict[int, List['Unit']]:
        """Group units at a hex by their initiative."""
        if not self._game_state:
            return {}
        
        units = self._game_state.units_at_hex(hex_id)
        by_initiative: Dict[int, List['Unit']] = {}
        
        for unit in units:
            faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            faction = self._game_state.factions.get(faction_id)
            if not faction:
                continue
            
            init = faction.initiative
            if init not in by_initiative:
                by_initiative[init] = []
            by_initiative[init].append(unit)
        
        return by_initiative
    
    # ==================== Hexside Control Updates ====================
    
    def claim_hexside(self, hex_id: int, direction: Direction, unit: 'Unit') -> bool:
        """
        Claim a hexside when a unit enters a combat hex.
        
        Returns True if successful.
        """
        if hex_id not in self.active_combats:
            return False
        
        if not self._game_state:
            return False
        
        faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        faction = self._game_state.factions.get(faction_id)
        if not faction:
            return False
        
        combat = self.active_combats[hex_id]
        combat.set_hexside_control(direction, faction.initiative)
        
        # Update participating initiatives
        combat.participating_initiatives.add(faction.initiative)
        self._update_lowest_initiatives(combat)
        
        return True
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> dict:
        """Serialize combat manager state."""
        return {
            'active_combats': {
                hex_id: {
                    'hex_id': combat.hex_id,
                    'is_new': combat.is_new,
                    'round_fought': combat.round_fought_this_alignment,
                    'hexside_control': {d.value: i for d, i in combat.hexside_control.items()},
                    'initiatives': list(combat.participating_initiatives),
                    'lowest_horde': combat.lowest_horde_initiative,
                    'lowest_alliance': combat.lowest_alliance_initiative,
                }
                for hex_id, combat in self.active_combats.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict, game_state: 'GameState') -> 'CombatManager':
        """Deserialize combat manager state."""
        manager = cls()
        manager.set_game_state(game_state)
        
        for hex_id_str, combat_data in data.get('active_combats', {}).items():
            hex_id = int(hex_id_str)
            combat = ActiveCombat(
                hex_id=hex_id,
                is_new=combat_data['is_new'],
                round_fought_this_alignment=combat_data['round_fought'],
                hexside_control={
                    Direction(int(d)): i 
                    for d, i in combat_data['hexside_control'].items()
                },
                participating_initiatives=set(combat_data['initiatives']),
                lowest_horde_initiative=combat_data['lowest_horde'],
                lowest_alliance_initiative=combat_data['lowest_alliance'],
            )
            manager.active_combats[hex_id] = combat
        
        return manager


# ==================== Module-level singleton ====================

_combat_manager: Optional[CombatManager] = None


def get_combat_manager() -> CombatManager:
    """Get the combat manager singleton."""
    global _combat_manager
    if _combat_manager is None:
        _combat_manager = CombatManager()
    return _combat_manager


def set_combat_manager(manager: CombatManager) -> None:
    """Set the combat manager singleton."""
    global _combat_manager
    _combat_manager = manager


def init_combat_manager(game_state: 'GameState') -> CombatManager:
    """Initialize combat manager with game state reference."""
    manager = get_combat_manager()
    manager.set_game_state(game_state)
    return manager

