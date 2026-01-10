"""
Reference Data for Tides of Darkness.

This module contains game constants and lookup tables that define core mechanics.
These values are extracted from server.py to make them:
1. Easier to find and understand
2. Easier for Alex to tweak during testing
3. Usable by both the resolution engine and the frontend

IMPORTANT: Changes to these values affect game balance!
"""
from typing import Dict
from .models.enums import Terrain, UnitType, UnitCategory


# =============================================================================
# TERRAIN COMBAT MODIFIERS
# =============================================================================
# These penalties are applied to attackers based on the terrain they're
# attacking through (hexside) or the terrain of the hex.
# Negative values = harder to hit (defender advantage)
# 
# From server.py line 2516

def _get_terrain_combat_modifiers() -> Dict[str, int]:
    """Get terrain combat modifiers from config."""
    from .game_config import get_game_config
    config = get_game_config()
    return {
        Terrain.OCEAN: 0,
        Terrain.CLEAR: config.terrain.plains_terrain_penalty,
        Terrain.FOREST: config.terrain.forest_terrain_penalty,
        Terrain.MOUNTAIN: config.terrain.mountain_terrain_penalty,
        Terrain.SWAMP: config.terrain.swamp_terrain_penalty,
        Terrain.PEAKS: 0,
        Terrain.COASTAL_CLEAR: config.terrain.plains_terrain_penalty,
        Terrain.COASTAL_MOUNTAIN: config.terrain.mountain_terrain_penalty,
        Terrain.COASTAL_FOREST: config.terrain.forest_terrain_penalty,
        Terrain.RIVER: 0,        # Special handling via river_crossing_penalty
        Terrain.FORTIFICATION: 0, # Special handling via fortification_penalty
    }

# Keep static version for backwards compatibility
TERRAIN_COMBAT_MODIFIERS: Dict[str, int] = {
    Terrain.OCEAN: 0, Terrain.CLEAR: 0, Terrain.FOREST: -10,
    Terrain.MOUNTAIN: -20, Terrain.SWAMP: -20, Terrain.PEAKS: 0,
    Terrain.COASTAL_CLEAR: 0, Terrain.COASTAL_MOUNTAIN: 0,
    Terrain.COASTAL_FOREST: 0, Terrain.RIVER: 0, Terrain.FORTIFICATION: 0,
}

# Special terrain penalties - now pulled from config at runtime
def _get_river_crossing_penalty() -> int:
    from .game_config import get_game_config
    return get_game_config().combat.river_crossing_penalty

def _get_fortification_penalty() -> int:
    from .game_config import get_game_config
    return get_game_config().combat.fortification_penalty

def _get_siege_vs_fortification_penalty() -> int:
    from .game_config import get_game_config
    return get_game_config().combat.siege_vs_fortification_penalty


# =============================================================================
# INITIAL DEFENDER MODIFIERS
# =============================================================================
# When a combat starts (new_combat = True), defenders who were already in the
# hex get these modifiers instead of the terrain modifiers.
# This represents the advantage of being dug in.
#
# From server.py line 2517

def _get_initial_defender_modifiers() -> Dict[str, int]:
    """Get initial defender modifiers from config."""
    from .game_config import get_game_config
    config = get_game_config()
    return {
        Terrain.OCEAN: 0,
        Terrain.CLEAR: config.terrain.plains_defender_bonus,
        Terrain.FOREST: config.terrain.forest_defender_bonus,
        Terrain.MOUNTAIN: config.terrain.mountain_defender_bonus,
        Terrain.SWAMP: config.terrain.swamp_defender_bonus,
        Terrain.PEAKS: 0,
        Terrain.COASTAL_CLEAR: config.terrain.plains_defender_bonus,
        Terrain.COASTAL_MOUNTAIN: config.terrain.mountain_defender_bonus,
        Terrain.COASTAL_FOREST: config.terrain.forest_defender_bonus,
        Terrain.RIVER: 0,
        Terrain.FORTIFICATION: 0,
    }

# Keep static version for backwards compatibility
INITIAL_DEFENDER_MODIFIERS: Dict[str, int] = {
    Terrain.OCEAN: 0, Terrain.CLEAR: 0, Terrain.FOREST: 0,
    Terrain.MOUNTAIN: 10, Terrain.SWAMP: -20, Terrain.PEAKS: 0,
    Terrain.COASTAL_CLEAR: 0, Terrain.COASTAL_MOUNTAIN: 0, Terrain.COASTAL_FOREST: 0,
    Terrain.RIVER: 0, Terrain.FORTIFICATION: 0,
}


# =============================================================================
# HEXSIDE MOVEMENT LIMITS
# =============================================================================
# Maximum number of units that can cross a hexside per movement phase.
# This is one of the most important tactical constraints in the game.
#
# From server.py line 2743-2788

# Hexside limits - now pulled dynamically from config
def _get_hexside_limits() -> Dict[str, int]:
    """Get hexside limits from config."""
    from .game_config import get_game_config
    config = get_game_config()
    return {
        Terrain.IMPASSABLE: 0,
        Terrain.OCEAN: config.movement.hexside_ocean,
        Terrain.CLEAR: config.movement.hexside_clear,
        Terrain.FOREST: config.movement.hexside_forest,
        Terrain.MOUNTAIN: config.movement.hexside_mountain,
        Terrain.SWAMP: config.movement.hexside_swamp,
        Terrain.RIVER: config.movement.hexside_river,
        Terrain.FORTIFICATION: config.movement.hexside_fortification,
        Terrain.PEAKS: 1,  # Only air can cross anyway
        Terrain.COASTAL_CLEAR: 2,  # Reduced to 1 during combat
        Terrain.COASTAL_FOREST: 1,
        Terrain.COASTAL_MOUNTAIN: 0,  # Impassable cliffs
    }

# Keep HEXSIDE_LIMITS as static fallback for backwards compatibility
HEXSIDE_LIMITS: Dict[str, int] = {
    Terrain.IMPASSABLE: 0,
    Terrain.OCEAN: 1000,
    Terrain.CLEAR: 4,
    Terrain.FOREST: 2,
    Terrain.MOUNTAIN: 1,
    Terrain.SWAMP: 1,
    Terrain.RIVER: 1,
    Terrain.FORTIFICATION: 1,
    Terrain.PEAKS: 1,
    Terrain.COASTAL_CLEAR: 2,
    Terrain.COASTAL_FOREST: 1,
    Terrain.COASTAL_MOUNTAIN: 0,
}

def _get_coastal_combat_limit() -> int:
    """Get coastal combat limit from config."""
    from .game_config import get_game_config
    return get_game_config().movement.coastal_combat_limit

def _get_road_bonus() -> int:
    """Get road bonus from config."""
    from .game_config import get_game_config
    return get_game_config().movement.road_hexside_bonus

# Keep as static fallbacks
COASTAL_COMBAT_LIMIT = 1
ROAD_BONUS = 1


# =============================================================================
# BASE COMBAT BONUSES
# =============================================================================
# Units fighting in a hex with a friendly base get a combat bonus.
#
# From server.py line 3017-3024

BASE_COMBAT_BONUS: Dict[int, int] = {
    1: 0,   # Tier 1 base: no bonus
    2: 5,   # Tier 2 base: +5 combat
    3: 10,  # Tier 3 base (capital): +10 combat
}


# =============================================================================
# COMBAT ROLL BOUNDS
# =============================================================================
# Combat effectiveness is clamped to these values.
# Even the weakest unit has a 10% chance to hit.
# Even the strongest can't exceed 90%.
#
# From server.py line 3026-3029

MIN_COMBAT_ROLL = 10
MAX_COMBAT_ROLL = 90


# =============================================================================
# VETERANCY BONUSES
# =============================================================================
# Per-tier bonuses for veteran units.
#
# From server.py line 378-380, 3126-3129

VETERANCY_COMBAT_BONUS = 5   # +5 combat per tier
VETERANCY_HP_BONUS = 1       # +1 max HP per tier
MAX_VETERANCY_TIER = 4       # Maximum tier a unit can reach


# =============================================================================
# FLANKING BONUSES
# =============================================================================
# When multiple forces attack from different directions, later forces get
# increasing flanking bonuses.
#
# From server.py line 2482

FLANKING_BONUS_INCREMENT = 10  # Each subsequent flanking force gets +10


# =============================================================================
# TRANSPORT DISEMBARK PENALTY
# =============================================================================
# Units disembarking from transports into combat get this terrain penalty.
#
# From server.py line 2143, 2958

DISEMBARK_INTO_COMBAT_PENALTY = -15


# =============================================================================
# MOVEMENT RULES
# =============================================================================
# Ground units need clear/forest hexsides to continue moving after the first
# move, unless they stay on roads (UNIT_ROAD_MOVE_ONLY).
# Air units can move anywhere except Peaks.
# Sea units can only move in Ocean hexes or through Coastal hexsides.

# Terrain types where ground units can enter
GROUND_PASSABLE_TERRAIN = {
    Terrain.CLEAR, Terrain.FOREST, Terrain.MOUNTAIN, 
    Terrain.SWAMP, Terrain.RIVER, Terrain.FORTIFICATION
}

# Hexside terrain that allows ground movement
GROUND_PASSABLE_HEXSIDES = {
    Terrain.CLEAR, Terrain.FOREST, Terrain.MOUNTAIN,
    Terrain.SWAMP, Terrain.RIVER, Terrain.FORTIFICATION
}

# Hexsides that interior siege can cross (without roads)
SIEGE_PASSABLE_HEXSIDES = {Terrain.CLEAR, Terrain.FOREST}


# =============================================================================
# SPECIAL LOCATION HEXES
# =============================================================================
# Certain factions have home territories with special rules.
#
# From server.py line 180-182

ALTERAC_HOME_HEXES = [476, 514, 553, 554, 555, 591, 592, 593, 630, 631, 668]

GILNEAS_HOME_HEXES = [
    20, 21, 58, 59, 60, 61, 62, 96, 97, 98, 99, 100, 101,
    134, 135, 136, 137, 138, 139, 140, 172, 173, 174, 175, 176, 177, 178, 179,
    210, 211, 212, 213, 214, 215, 216, 217, 253, 254, 255
]

SILVERMOON_HOME_HEXES = [
    463, 464, 502, 503, 504, 540, 695, 696, 699, 700, 701, 734, 736, 738, 739,
    773, 774, 775, 776, 777, 778, 811, 812, 813, 814, 815, 816,
    849, 850, 851, 852, 853, 854, 887, 888, 889, 890, 891,
    926, 927, 928, 929, 966, 967, 968, 1006
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_terrain_modifier(hex_terrain: str, hexside_terrain: str, 
                         is_air: bool = False, 
                         is_exterior_siege: bool = False,
                         is_initial_defender: bool = False) -> int:
    """
    Calculate the terrain combat modifier for a unit.
    
    Args:
        hex_terrain: The terrain of the hex where combat is happening
        hexside_terrain: The terrain of the hexside the unit entered through
        is_air: True if the unit is an air unit (ignores hexside terrain)
        is_exterior_siege: True if exterior siege (special rules)
        is_initial_defender: True if unit was in hex when combat started
    
    Returns:
        Combat modifier (negative = harder to hit)
    """
    # Get dynamic modifiers from config
    terrain_mods = _get_terrain_combat_modifiers()
    defender_mods = _get_initial_defender_modifiers()
    
    # Initial defenders get special treatment
    if is_initial_defender:
        return defender_mods.get(hex_terrain, 0)
    
    # Air units only care about hex terrain
    if is_air:
        return terrain_mods.get(hex_terrain, 0)
    
    # Get base modifiers
    hex_mod = terrain_mods.get(hex_terrain, 0)
    hexside_mod = terrain_mods.get(hexside_terrain, 0)
    
    # Use the worse (more negative) of hex or hexside terrain
    result = min(hex_mod, hexside_mod)
    
    # Special hexside penalties
    if hexside_terrain == Terrain.RIVER:
        result = hex_mod + _get_river_crossing_penalty()
    elif hexside_terrain == Terrain.FORTIFICATION:
        result = hex_mod + _get_fortification_penalty()
    
    # Exterior siege special rules
    if is_exterior_siege:
        result = hex_mod  # Ignore hexside terrain...
        if hexside_terrain in {Terrain.FORTIFICATION, Terrain.MOUNTAIN, 
                               Terrain.COASTAL_MOUNTAIN}:
            result += _get_siege_vs_fortification_penalty()  # ...except these
    
    return result


def get_hexside_limit(hexside_terrain: str, has_road: bool = False, 
                      is_combat_move: bool = False) -> int:
    """
    Get the maximum number of units that can cross a hexside.
    
    Args:
        hexside_terrain: The terrain code of the hexside
        has_road: Whether there's a road across this hexside
        is_combat_move: Whether units are moving into combat
    
    Returns:
        Maximum units that can cross
    """
    hexside_limits = _get_hexside_limits()
    base_limit = hexside_limits.get(hexside_terrain, 0)
    
    # Coastal is reduced during combat
    if hexside_terrain == Terrain.COASTAL_CLEAR and is_combat_move:
        base_limit = _get_coastal_combat_limit()
    
    # Roads add capacity (peacetime only)
    if has_road and not is_combat_move:
        base_limit += _get_road_bonus()
    
    return base_limit


def get_base_combat_bonus(base_tier: int) -> int:
    """Get the combat bonus for fighting at a friendly base."""
    return BASE_COMBAT_BONUS.get(base_tier, 0)


def clamp_combat_roll(roll: int) -> int:
    """Clamp a combat roll to valid bounds."""
    return max(MIN_COMBAT_ROLL, min(MAX_COMBAT_ROLL, roll))


