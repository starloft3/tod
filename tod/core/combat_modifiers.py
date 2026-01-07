"""
Combat Modifier Calculations for Tides of Darkness.

This module calculates and assigns combat modifiers to units before combat resolution:
- Flanking bonuses (attacking from multiple directions)
- Terrain modifiers (hex terrain, hexside terrain)
- Initial defender bonuses (first round of combat)

These modifiers are assigned to units BEFORE the combat round resolves.
"""
from dataclasses import dataclass
from typing import Dict, List, Set, Optional, TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from .game_state import GameState
    from .combat_manager import CombatManager, ActiveCombat

from .models import Unit, UnitType, UnitCategory
from .models.enums import Direction


# =============================================================================
# TERRAIN MODIFIER TABLES
# =============================================================================

# General terrain modifiers (penalties for attackers)
# Negative values = harder to hit (defender advantage)
TERRAIN_MODIFIERS: Dict[str, int] = {
    'O': 0,    # Ocean
    'C': 0,    # Clear
    'F': -10,  # Forest
    'M': -20,  # Mountain
    'S': -20,  # Swamp
    'I': 0,    # Impassable (peaks)
    'K': 0,    # Coastal Clear
    'N': 0,    # Coastal Mountain
    'Q': 0,    # Coastal Forest
    'R': 0,    # River (special: adds -15)
    'W': 0,    # Fortification (special: adds -25)
}

# Initial defender bonuses (first round of new combat)
# Defenders already in position get better modifiers
INITIAL_DEFENDER_MODIFIERS: Dict[str, int] = {
    'O': 0,    # Ocean
    'C': 0,    # Clear
    'F': 0,    # Forest (no penalty for entrenched defenders)
    'M': 0,    # Mountain (no penalty for entrenched defenders)
    'S': -20,  # Swamp (bad for everyone)
    'I': 0,    # Impassable
    'K': 0,    # Coastal Clear
    'N': 0,    # Coastal Mountain
    'Q': 0,    # Coastal Forest
    'R': 0,    # River
    'W': 0,    # Fortification
}

# Special hexside modifiers (added to hex terrain)
RIVER_PENALTY = -15
FORTIFICATION_PENALTY = -25

# Siege vs fortified positions penalty
SIEGE_VS_FORTIFICATION_PENALTY = -10


# =============================================================================
# FLANKING CALCULATIONS
# =============================================================================

@dataclass
class Force:
    """A group of units entering from the same direction."""
    direction: Direction
    units: List[Unit]
    total_hp: int = 0
    
    def __post_init__(self):
        self.total_hp = sum(u.hp for u in self.units)


def calculate_flanking_bonuses(
    combat: 'ActiveCombat',
    attackers: List[Unit],
    is_new_combat: bool,
    game_state: 'GameState'
) -> None:
    """
    Calculate and assign flanking bonuses to attacking units.
    
    New Combat Rules:
    - Attackers entering through multiple hexsides get flanking
    - Forces ranked by total HP (descending)
    - Main force (highest HP): +0%
    - Second force: +10%
    - Third force: +20%, etc.
    
    Continuing Combat Rules:
    - Forces attacking through enemy-controlled hexsides get flanking
    - First force: +10%
    - Second force: +20%, etc.
    """
    if not attackers:
        return
    
    # Group attackers by entry direction
    forces = _group_attackers_by_direction(attackers, combat.hex_id)
    
    if not forces:
        return
    
    if is_new_combat:
        _assign_new_combat_flanking(forces)
    else:
        _assign_continuing_combat_flanking(forces, combat, game_state)


def _group_attackers_by_direction(attackers: List[Unit], combat_hex: int) -> List[Force]:
    """Group attackers by the direction they entered from."""
    by_direction: Dict[Direction, List[Unit]] = defaultdict(list)
    
    for unit in attackers:
        direction = _get_entry_direction(combat_hex, unit.previous_location)
        if direction:
            by_direction[direction].append(unit)
    
    forces = [Force(direction=d, units=units) for d, units in by_direction.items()]
    return forces


def _get_entry_direction(to_hex: int, from_hex: int) -> Optional[Direction]:
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


def _assign_new_combat_flanking(forces: List[Force]) -> None:
    """
    Assign flanking for new combat.
    Forces ranked by HP, main force gets 0, subsequent +10 each.
    """
    if len(forces) <= 1:
        # Only one attack direction - no flanking
        return
    
    # Sort by total HP descending
    sorted_forces = sorted(forces, key=lambda f: f.total_hp, reverse=True)
    
    # Assign bonuses
    bonus = 0
    for force in sorted_forces:
        for unit in force.units:
            unit.flank_bonus = bonus
        bonus += 10  # Next force gets +10 more


def _assign_continuing_combat_flanking(
    forces: List[Force], 
    combat: 'ActiveCombat',
    game_state: 'GameState'
) -> None:
    """
    Assign flanking for continuing combat.
    Only forces entering through enemy hexsides get flanking (+10, +20, etc.)
    """
    # Filter to forces entering through enemy hexsides
    flanking_forces = []
    
    for force in forces:
        if force.units:
            unit_initiative = _get_unit_initiative(force.units[0], game_state)
            hexside_control = combat.hexside_control.get(force.direction, -1)
            
            # Enemy hexside = controlled by different initiative
            if hexside_control >= 0 and hexside_control != unit_initiative:
                flanking_forces.append(force)
    
    if not flanking_forces:
        return
    
    # Sort by HP and assign bonuses starting at +10
    sorted_forces = sorted(flanking_forces, key=lambda f: f.total_hp, reverse=True)
    
    bonus = 10
    for force in sorted_forces:
        for unit in force.units:
            unit.flank_bonus = bonus
        bonus += 10


# =============================================================================
# TERRAIN MODIFIER CALCULATIONS
# =============================================================================

def calculate_terrain_modifiers(
    hex_id: int,
    defenders: List[Unit],
    attackers: List[Unit],
    is_new_combat: bool,
    game_state: 'GameState'
) -> None:
    """
    Calculate and assign terrain modifiers to all units in combat.
    
    New Combat:
    - Defenders: Initial defender bonus (hex terrain)
    - Attackers: Worse of (hex terrain OR hexside terrain)
        - Exception: River/Fortification = hex + hexside (additive)
    - Air units: Always use hex terrain only
    
    Continuing Combat:
    - All units already in combat: Hex terrain modifier
    - New arrivals: Treated as attackers (worse of hex/hexside)
    """
    hex_obj = game_state.get_hex(hex_id)
    if not hex_obj:
        return
    
    hex_terrain = hex_obj.terrain
    
    # Assign modifiers to defenders
    for unit in defenders:
        if is_new_combat:
            # Initial defender bonus
            unit.terrain_bonus = INITIAL_DEFENDER_MODIFIERS.get(hex_terrain, 0)
        else:
            # Continuing: just hex terrain
            unit.terrain_bonus = TERRAIN_MODIFIERS.get(hex_terrain, 0)
    
    # Assign modifiers to attackers
    for unit in attackers:
        _assign_attacker_terrain_modifier(unit, hex_obj, game_state)


def _assign_attacker_terrain_modifier(
    unit: Unit, 
    hex_obj,  # Hex type
    game_state: 'GameState'
) -> None:
    """
    Assign terrain modifier to an attacking unit.
    
    Rules:
    - Air units: Hex terrain only
    - Exterior siege: Hex terrain, but -10 extra vs fortification/mountain/coastal mountain
    - Normal: Worse of hex or hexside, except River/Fort which are additive
    """
    hex_terrain = hex_obj.terrain
    
    # Get hexside terrain from entry direction
    entry_direction = _get_entry_direction(hex_obj.id, unit.previous_location)
    hexside_terrain = _get_hexside_terrain(hex_obj, entry_direction) if entry_direction else 'C'
    
    hex_modifier = TERRAIN_MODIFIERS.get(hex_terrain, 0)
    hexside_modifier = TERRAIN_MODIFIERS.get(hexside_terrain, 0)
    
    # Air units ignore hexside
    if unit.unit_type == UnitType.AIR:
        unit.terrain_bonus = hex_modifier
        return
    
    # Exterior siege special handling
    if unit.category == UnitCategory.EXTERIOR_SIEGE:
        unit.terrain_bonus = hex_modifier
        if hexside_terrain in ('W', 'M', 'N'):
            unit.terrain_bonus += SIEGE_VS_FORTIFICATION_PENALTY
        return
    
    # River or Fortification: additive
    if hexside_terrain == 'R':
        unit.terrain_bonus = hex_modifier + RIVER_PENALTY
        return
    
    if hexside_terrain == 'W':
        unit.terrain_bonus = hex_modifier + FORTIFICATION_PENALTY
        return
    
    # Normal case: worse of hex or hexside
    unit.terrain_bonus = min(hex_modifier, hexside_modifier)


def _get_hexside_terrain(hex_obj, entry_direction: Direction) -> str:
    """
    Get the terrain of the hexside a unit entered through.
    
    IMPORTANT: entry_direction is the direction the unit was MOVING (e.g., N if they
    moved northward into the hex). To find the actual hexside they crossed, we need
    to look at the OPPOSITE direction on the destination hex.
    
    Example: Unit moves from hex 422 (south) to hex 421 (north).
    - entry_direction = N (they moved northward)
    - The hexside they crossed is the SOUTH side of hex 421
    - So we look at hex_421.south, not hex_421.north
    """
    # Reverse the direction to get the hexside the unit actually crossed
    opposite_direction = {
        Direction.N: Direction.S,
        Direction.S: Direction.N,
        Direction.NE: Direction.SW,
        Direction.SW: Direction.NE,
        Direction.SE: Direction.NW,
        Direction.NW: Direction.SE,
    }
    
    actual_hexside = opposite_direction.get(entry_direction)
    if not actual_hexside:
        return 'C'
    
    side = hex_obj.get_side(actual_hexside)
    return side.terrain if side and side.terrain else 'C'


def _get_unit_initiative(unit: Unit, game_state: 'GameState') -> int:
    """Get the initiative value for a unit's faction."""
    faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
    faction = game_state.factions.get(faction_id)
    return faction.initiative if faction else -1


# =============================================================================
# MAIN MODIFIER ASSIGNMENT
# =============================================================================

def assign_combat_modifiers(
    hex_id: int,
    combat: 'ActiveCombat',
    game_state: 'GameState',
    triggering_initiative: int = -1
) -> None:
    """
    Assign all combat modifiers to units at a hex before combat resolution.
    
    This should be called before resolve_combat_round().
    
    Args:
        hex_id: The hex where combat is occurring
        combat: The ActiveCombat object
        game_state: The current game state
        triggering_initiative: The initiative that just moved and triggered combat.
                               Used for new combat to determine attackers vs defenders.
    
    Assigns:
    - Flanking bonuses
    - Terrain modifiers
    """
    units = game_state.units_at_hex(hex_id)
    
    is_new = combat.is_new
    
    # Classify units - use initiative for new combat, previous_location for continuing
    if is_new and triggering_initiative >= 0:
        # NEW COMBAT: Use initiative to determine attackers vs defenders
        attackers = [u for u in units if game_state.faction_initiative(
            u.faction.value if hasattr(u.faction, 'value') else u.faction
        ) == triggering_initiative]
        defenders = [u for u in units if game_state.faction_initiative(
            u.faction.value if hasattr(u.faction, 'value') else u.faction
        ) != triggering_initiative]
    else:
        # CONTINUING COMBAT: Use previous_location logic
        defenders = [u for u in units if u.previous_location == u.location]
        attackers = [u for u in units if u.previous_location != u.location]
    
    # Calculate and assign flanking
    calculate_flanking_bonuses(combat, attackers, is_new, game_state)
    
    # Calculate and assign terrain
    calculate_terrain_modifiers(hex_id, defenders, attackers, is_new, game_state)


def clear_combat_modifiers(units: List[Unit]) -> None:
    """Clear all combat modifiers from units."""
    for unit in units:
        unit.flank_bonus = 0
        unit.terrain_bonus = 0
        unit.hold_bonus = 0






