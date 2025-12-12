"""
Special Combat Cases for Tides of Darkness.

This module handles special combat scenarios:
- Exterior Siege: Units firing into adjacent hexes
- Amphibious Invasions: Transports unloading under fire
- Rangedfire Orders: Pre-combat siege bombardment

Design Philosophy:
- No "ghost units" - exterior siege is handled as a targeting property
- Clean separation from core combat logic
- Modular and easily adjustable
"""
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
import logging

if TYPE_CHECKING:
    from .game_state import GameState
    from .combat_manager import CombatManager

from .models import Unit, Base, UnitCategory, UnitType

logger = logging.getLogger('combat')


# =============================================================================
# AMPHIBIOUS INVASION
# =============================================================================

# Modifiers for units unloading from transports into combat
AMPHIBIOUS_ATTACK_PENALTY = -20  # Unloading units fire at -20%
AMPHIBIOUS_DEFENSE_PENALTY = 10  # Unloading units are hit at +10%


@dataclass
class AmphibiousLanding:
    """
    Tracks an amphibious landing event.
    
    When a transport ends movement in a clear coastal hex with no enemy ships,
    it automatically unloads. If there are enemy ground/air units, combat begins.
    """
    hex_id: int
    transport_id: int
    unloaded_units: List[int] = field(default_factory=list)
    is_contested: bool = False  # True if enemy units present


def check_amphibious_landing(
    transport: Unit, 
    hex_id: int, 
    game_state: 'GameState'
) -> Optional[AmphibiousLanding]:
    """
    Check if a transport should perform an amphibious landing.
    
    Conditions:
    - Transport ends movement in a clear coastal hex
    - No enemy ships present
    - Transport is carrying units
    
    Returns AmphibiousLanding if conditions met, None otherwise.
    """
    # Check if transport
    if not transport.is_transport:
        return None
    
    # Check if carrying units
    carried = transport.transported_units
    if not carried:
        return None
    
    # Check hex terrain
    hex_obj = game_state.get_hex(hex_id)
    if not hex_obj:
        return None
    
    # Must be coastal (has water access) - simplified check
    # In full implementation, check hexside terrain for coastal
    is_coastal = hex_obj.terrain == 'K' or any(
        side.terrain == 'K' 
        for side in [hex_obj.north, hex_obj.northeast, hex_obj.southeast,
                     hex_obj.south, hex_obj.southwest, hex_obj.northwest]
        if side
    )
    
    if not is_coastal:
        return None
    
    # Check for enemy ships
    units_at_hex = game_state.units_at_hex(hex_id)
    transport_initiative = _get_unit_initiative(transport, game_state)
    
    enemy_ships = [
        u for u in units_at_hex
        if u.unit_type == UnitType.SEA 
        and _get_unit_initiative(u, game_state) != transport_initiative
    ]
    
    if enemy_ships:
        return None  # Cannot unload with enemy ships present
    
    # Check for enemy ground/air
    enemy_ground_air = [
        u for u in units_at_hex
        if u.unit_type in (UnitType.GROUND, UnitType.AIR)
        and _get_unit_initiative(u, game_state) != transport_initiative
    ]
    
    landing = AmphibiousLanding(
        hex_id=hex_id,
        transport_id=transport.id,
        unloaded_units=carried,
        is_contested=len(enemy_ground_air) > 0
    )
    
    return landing


def execute_amphibious_landing(
    landing: AmphibiousLanding,
    game_state: 'GameState'
) -> List[Unit]:
    """
    Execute an amphibious landing - unload units from transport.
    
    Returns list of unloaded units.
    """
    transport = game_state.get_unit(landing.transport_id)
    if not transport:
        return []
    
    unloaded = []
    
    for unit_id in landing.unloaded_units:
        unit = game_state.get_unit(unit_id)
        if unit:
            # Move unit to landing hex
            unit.location = landing.hex_id
            unit.previous_location = transport.location  # For attacker classification
            
            # Apply amphibious penalties if contested
            if landing.is_contested:
                apply_amphibious_penalties(unit)
            
            unloaded.append(unit)
            logger.info(f"{unit.name} unloads at hex {landing.hex_id}")
    
    # Clear transport slots
    transport.transport_slot_1 = -1
    transport.transport_slot_2 = -1
    transport.transport_slot_3 = -1
    
    return unloaded


def apply_amphibious_penalties(unit: Unit) -> None:
    """
    Apply combat penalties to a unit landing under fire.
    
    First round only:
    - Attack at -20%
    - Defend at +10% (easier to hit)
    """
    # These are stored in terrain_bonus (attack) and a special flag
    # For simplicity, we apply the attack penalty to terrain_bonus
    unit.terrain_bonus += AMPHIBIOUS_ATTACK_PENALTY
    
    # The defense penalty is trickier - it should make the unit easier to hit
    # We can store this in a temporary field or handle it in damage calculation
    # For now, store it as a negative "hold_bonus" (hacky but functional)
    unit.hold_bonus = AMPHIBIOUS_DEFENSE_PENALTY  # Will be added to attacker's roll
    
    logger.info(f"{unit.name} has amphibious landing penalties: {AMPHIBIOUS_ATTACK_PENALTY}% attack, +{AMPHIBIOUS_DEFENSE_PENALTY}% to be hit")


# =============================================================================
# EXTERIOR SIEGE (RANGEDFIRE)
# =============================================================================

@dataclass
class RangedfireAttack:
    """
    Represents a rangedfire attack from an adjacent hex.
    
    Interior siege units can fire into adjacent hexes before combat resolves.
    This is handled BEFORE the main combat round.
    """
    attacker_id: int
    attacker_hex: int
    target_hex: int
    
    # Calculated during resolution
    targets_hit: List[int] = field(default_factory=list)
    total_damage: int = 0


def get_rangedfire_eligible_units(
    hex_id: int,
    game_state: 'GameState',
    combat_manager: 'CombatManager'
) -> List[Unit]:
    """
    Get units at a hex that can perform rangedfire into adjacent combats.
    
    Conditions:
    - Unit is INTERIOR_SIEGE category
    - Unit has not moved (in same hex as previous location)
    - Unit's hex is NOT a combat hex (can't rangedfire while in combat)
    - Adjacent hex IS a combat hex
    """
    units = game_state.units_at_hex(hex_id)
    eligible = []
    
    # Can't rangedfire from a combat hex
    if combat_manager.is_combat_hex(hex_id):
        return []
    
    for unit in units:
        if unit.category != UnitCategory.INTERIOR_SIEGE:
            continue
        
        # Must not have moved
        if unit.previous_location != unit.location:
            continue
        
        # Check if any adjacent hex is a combat hex
        adjacent = game_state.adjacent_hexes(hex_id)
        has_adjacent_combat = any(
            combat_manager.is_combat_hex(adj) for adj in adjacent
        )
        
        if has_adjacent_combat:
            eligible.append(unit)
    
    return eligible


def execute_rangedfire(
    attacker: Unit,
    target_hex: int,
    game_state: 'GameState',
    combat_manager: 'CombatManager'
) -> Optional[RangedfireAttack]:
    """
    Execute a rangedfire attack into an adjacent hex.
    
    The attacker fires as EXTERIOR_SIEGE (fires first in combat order).
    Damage is calculated and applied.
    
    Returns RangedfireAttack with results, or None if invalid.
    """
    # Validate
    if attacker.category != UnitCategory.INTERIOR_SIEGE:
        return None
    
    if not combat_manager.is_combat_hex(target_hex):
        return None
    
    # Check adjacency
    adjacent = game_state.adjacent_hexes(attacker.location)
    if target_hex not in adjacent:
        return None
    
    # Can only rangedfire once per turn
    if attacker.fired:
        return None
    
    result = RangedfireAttack(
        attacker_id=attacker.id,
        attacker_hex=attacker.location,
        target_hex=target_hex
    )
    
    # Get valid targets at the target hex
    targets = game_state.units_at_hex(target_hex)
    attacker_init = _get_unit_initiative(attacker, game_state)
    
    valid_targets = [
        t for t in targets
        if t.hp > 0
        and _get_unit_initiative(t, game_state) != attacker_init
        and t.unit_type in (UnitType.GROUND, UnitType.SEA)  # Siege can hit ground/sea
        and t.category != UnitCategory.EXTERIOR_SIEGE  # Can't hit "ghosts"
    ]
    
    if not valid_targets:
        return None
    
    # Fire at the highest HP target
    valid_targets.sort(key=lambda u: u.hp, reverse=True)
    target = valid_targets[0]
    
    # Calculate and apply damage (simplified - full version uses combat engine)
    from .combat_engine import CombatEngine
    
    # Temporarily mark attacker as exterior siege for this attack
    original_category = attacker.category
    attacker.category = UnitCategory.EXTERIOR_SIEGE
    
    # Get terrain modifier for exterior siege
    hex_obj = game_state.get_hex(target_hex)
    hexside_terrain = _get_hexside_terrain_between(attacker.location, target_hex, game_state)
    
    # Exterior siege gets hex terrain, but -10 vs fort/mountain/coastal mountain
    terrain_mod = 0
    if hexside_terrain in ('W', 'M', 'N'):
        terrain_mod = -10
    
    attacker.terrain_bonus = terrain_mod
    
    # Simple damage calc
    effective_combat = max(10, min(90, attacker.effective_combat + terrain_mod))
    hits = sum(1 for _ in range(attacker.hp) if _roll_d100() <= effective_combat)
    
    if hits > 0:
        damage = _apply_armor(target, hits)
        result.targets_hit.append(target.id)
        result.total_damage = damage
        logger.info(f"Rangedfire: {attacker.name} hits {target.name} for {damage} damage")
    
    # Restore and mark fired
    attacker.category = original_category
    attacker.fired = True
    
    return result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_unit_initiative(unit: Unit, game_state: 'GameState') -> int:
    """Get the initiative value for a unit's faction."""
    faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
    faction = game_state.factions.get(faction_id)
    return faction.initiative if faction else -1


def _get_hexside_terrain_between(from_hex: int, to_hex: int, game_state: 'GameState') -> str:
    """Get the terrain of the hexside between two hexes."""
    hex_obj = game_state.get_hex(from_hex)
    if not hex_obj:
        return 'C'
    
    diff = from_hex - to_hex
    
    if diff == 1:
        return hex_obj.north.terrain if hex_obj.north else 'C'
    elif diff == -1:
        return hex_obj.south.terrain if hex_obj.south else 'C'
    elif diff == 39:
        return hex_obj.northwest.terrain if hex_obj.northwest else 'C'
    elif diff == -39:
        return hex_obj.southeast.terrain if hex_obj.southeast else 'C'
    elif diff == 38:
        return hex_obj.northeast.terrain if hex_obj.northeast else 'C'
    elif diff == -38:
        return hex_obj.southwest.terrain if hex_obj.southwest else 'C'
    
    return 'C'


def _roll_d100() -> int:
    """Roll a d100."""
    from random import randint
    return randint(1, 100)


def _apply_armor(target: Unit, hits: int) -> int:
    """
    Apply damage through armor (simplified version).
    Returns actual damage dealt.
    """
    if hits <= 0:
        return 0
    
    remaining = hits
    
    # Light armor
    if target.light_armor_current > 0:
        absorbed = min(remaining, target.light_armor_current)
        target.light_armor_current -= absorbed
        remaining -= absorbed
    
    if remaining <= 0:
        return 0
    
    # Heavy armor
    if not target.armor_broken and target.heavy_armor > 0:
        if remaining <= target.heavy_armor:
            return 0
        target.armor_broken = True
        remaining -= target.heavy_armor
    
    if remaining <= 0:
        return 0
    
    # Natural armor
    remaining -= target.natural_armor
    if remaining < 0:
        remaining = 0
    
    # Apply damage
    actual = min(remaining, target.hp)
    target.hp -= actual
    
    if target.hp <= 0:
        target.hp = 0
        target.alive = False
    
    return actual

