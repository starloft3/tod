"""
Movement Validation System for Tides of Darkness.

This module handles all movement-related validation:
- Can a unit move from hex A to hex B?
- What's the hexside limit between two hexes?
- Does a unit have enough movement points?
- Path validation for multi-hex moves

Based on the logic in server.py canMove() and hexsidelimit() functions.
"""
from typing import Tuple, List, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum

from .game_state import GameState
from .models import Unit, Hex
from .models.enums import Terrain, UnitType, UnitCategory
from .reference_data import (
    HEXSIDE_LIMITS, ROAD_BONUS, COASTAL_COMBAT_LIMIT
)


class MoveResult(Enum):
    """Result of a movement validation check."""
    SUCCESS = "success"
    INVALID_HEX = "invalid_hex"
    NOT_ADJACENT = "not_adjacent"
    NO_MOVEMENT_POINTS = "no_movement_points"
    IMPASSABLE_TERRAIN = "impassable_terrain"
    IMPASSABLE_HEXSIDE = "impassable_hexside"
    WRONG_UNIT_TYPE = "wrong_unit_type"
    ENEMY_HEXSIDE = "enemy_hexside"
    SIEGE_RESTRICTION = "siege_restriction"
    CONTINUOUS_MOVE_BLOCKED = "continuous_move_blocked"
    COMBAT_ENTRY_BLOCKED = "combat_entry_blocked"
    ROAD_MOVE_INTO_COMBAT = "road_move_into_combat"


@dataclass
class MoveValidation:
    """Result of validating a move."""
    valid: bool
    result: MoveResult
    message: str
    movement_cost: int = 1  # How many movement points this step costs
    uses_road_bonus: bool = False  # Does this use the road move bonus?
    enters_combat: bool = False  # Will this move trigger combat?


# =============================================================================
# ADJACENCY AND HEXSIDE HELPERS
# =============================================================================

def get_adjacent_hex_offsets() -> List[int]:
    """
    Get the hex ID offsets for adjacent hexes.
    
    The map uses offset coordinates where columns alternate between 38 and 39 hexes.
    Adjacent hex offsets are: +1 (S), -1 (N), +38 (SE/NE), -38 (NW/SW), +39 (SW/SE), -39 (NE/NW)
    """
    return [1, -1, 38, -38, 39, -39]


def are_hexes_adjacent(hex1: int, hex2: int) -> bool:
    """Check if two hexes are adjacent."""
    diff = abs(hex1 - hex2)
    return diff in [1, 38, 39]


def get_direction(from_hex: int, to_hex: int) -> Optional[str]:
    """
    Get the direction from one hex to another.
    Returns: 'N', 'S', 'NE', 'NW', 'SE', 'SW' or None if not adjacent.
    """
    diff = from_hex - to_hex
    
    # This is simplified - actual direction depends on column position
    # For now, we use the offset values
    direction_map = {
        1: 'N',
        -1: 'S',
        39: 'NW',
        -39: 'SE', 
        38: 'NE',
        -38: 'SW'
    }
    
    return direction_map.get(diff)


def get_hexside_terrain(from_hex: int, to_hex: int, state: GameState) -> Optional[str]:
    """
    Get the terrain of the hexside between two adjacent hexes.
    
    Hexside terrain is stored on the hex you're moving FROM, in the direction you're going.
    """
    hex_obj = state.get_hex(from_hex)
    if not hex_obj:
        return None
    
    diff = from_hex - to_hex
    
    # Map offset to hexside attribute
    # Note: The hexside terrain is stored differently - we need to check the hex data
    if diff == 1:  # Moving North
        return hex_obj.north.terrain if hex_obj.north else None
    elif diff == -1:  # Moving South
        return hex_obj.south.terrain if hex_obj.south else None
    elif diff == 39:  # Moving Northwest
        return hex_obj.northwest.terrain if hex_obj.northwest else None
    elif diff == -39:  # Moving Southeast
        return hex_obj.southeast.terrain if hex_obj.southeast else None
    elif diff == 38:  # Moving Southwest (to lower hex ID via SW)
        return hex_obj.southwest.terrain if hex_obj.southwest else None
    elif diff == -38:  # Moving Northeast (to higher hex ID via NE)
        return hex_obj.northeast.terrain if hex_obj.northeast else None
    
    return None


def get_hexside_control(from_hex: int, to_hex: int, state: GameState, 
                        combat_manager: Optional['CombatManager'] = None) -> Optional[int]:
    """
    Get which initiative controls a hexside.
    
    Hexside control ONLY applies to combat hexes.
    For non-combat hexes, returns -1 (no control = anyone can use).
    
    Args:
        from_hex: Hex to check control from
        to_hex: Adjacent hex
        state: Game state
        combat_manager: Optional combat manager for proper control checking
    
    Returns:
        Initiative value controlling the hexside, or -1 for no control
    """
    # If we have a combat manager, use it for proper control
    if combat_manager:
        combat = combat_manager.get_combat(from_hex)
        if not combat:
            return -1  # Not a combat hex = no hexside control
        
        # Get direction and look up control
        diff = from_hex - to_hex
        from .models.enums import Direction
        direction_map = {
            1: Direction.N,
            -1: Direction.S,
            39: Direction.NW,
            -39: Direction.SE,
            38: Direction.SW,  # origin - destination: +38 means moving SW
            -38: Direction.NE  # origin - destination: -38 means moving NE
        }
        direction = direction_map.get(diff)
        if direction:
            return combat.hexside_control.get(direction, -1)
        return -1
    
    # Fallback to legacy behavior (deprecated - should not be used)
    # This is only here for backwards compatibility during transition
    hex_obj = state.get_hex(from_hex)
    if not hex_obj:
        return None
    
    diff = from_hex - to_hex
    
    if diff == 1:  # North
        return hex_obj.north.control if hex_obj.north else -1
    elif diff == -1:  # South
        return hex_obj.south.control if hex_obj.south else -1
    elif diff == 39:  # Northwest
        return hex_obj.northwest.control if hex_obj.northwest else -1
    elif diff == -39:  # Southeast
        return hex_obj.southeast.control if hex_obj.southeast else -1
    elif diff == 38:  # Southwest (to lower hex ID via SW)
        return hex_obj.southwest.control if hex_obj.southwest else -1
    elif diff == -38:  # Northeast (to higher hex ID via NE)
        return hex_obj.northeast.control if hex_obj.northeast else -1
    
    return -1


# Type hint for CombatManager (avoids circular import)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .combat_manager import CombatManager


def has_road(from_hex: int, to_hex: int, state: GameState) -> bool:
    """Check if there's a road between two adjacent hexes."""
    return state.has_road_between(from_hex, to_hex)


# =============================================================================
# TERRAIN PASSABILITY
# =============================================================================

def can_ground_unit_enter(hex_terrain: str, hexside_terrain: str) -> bool:
    """Check if a ground unit can enter a hex via this hexside."""
    passable_hex = hex_terrain in ['C', 'F', 'M', 'S', 'R', 'W']
    passable_side = hexside_terrain in ['C', 'F', 'M', 'S', 'R', 'W', 'K', 'Q', 'I']
    return passable_hex and passable_side


def can_sea_unit_enter(from_terrain: str, to_terrain: str, hexside_terrain: str) -> bool:
    """Check if a sea unit can move between two hexes."""
    # Sea units need ocean on both sides, or coastal hexside
    if from_terrain == 'O' and to_terrain == 'O':
        return True
    if (from_terrain == 'O' or to_terrain == 'O') and hexside_terrain == 'K':
        return True
    return False


def can_air_unit_enter(hex_terrain: str) -> bool:
    """Check if an air unit can enter a hex."""
    # Air can go anywhere except truly impassable
    return hex_terrain != 'I' and hex_terrain != 'X'


def is_rough_terrain_hexside(hexside_terrain: str) -> bool:
    """Check if a hexside is rough terrain (stops continuous movement)."""
    return hexside_terrain in ['M', 'S', 'R', 'W', 'I', 'Q']


# =============================================================================
# HEXSIDE LIMITS
# =============================================================================

def get_hexside_limit(from_hex: int, to_hex: int, state: GameState, 
                      is_combat_move: bool = False) -> int:
    """
    Get the movement limit for a hexside.
    
    Args:
        from_hex: Source hex ID
        to_hex: Destination hex ID
        state: Game state
        is_combat_move: Is this a move into combat?
    
    Returns:
        Number of units that can cross this hexside
    """
    hexside_terrain = get_hexside_terrain(from_hex, to_hex, state)
    
    if hexside_terrain is None:
        return 0
    
    # Get base limit from terrain (using config-aware getter)
    from .reference_data import _get_hexside_limits, _get_coastal_combat_limit, _get_road_bonus
    hexside_limits = _get_hexside_limits()
    limit = hexside_limits.get(hexside_terrain, 0)
    
    # Coastal hexsides have reduced limit in combat
    if hexside_terrain == 'K' and is_combat_move:
        limit = _get_coastal_combat_limit()
    
    # Roads add to limit (but not during combat)
    if not is_combat_move and has_road(from_hex, to_hex, state):
        limit += _get_road_bonus()
    
    return limit


# =============================================================================
# MAIN MOVEMENT VALIDATION
# =============================================================================

def can_move(from_hex: int, to_hex: int, unit: Unit, state: GameState,
             is_combat_move: bool = False) -> MoveValidation:
    """
    Validate if a unit can move from one hex to an adjacent hex.
    
    This is the main validation function that checks all movement rules.
    
    Args:
        from_hex: Current hex ID
        to_hex: Target hex ID
        unit: The unit attempting to move
        state: Current game state
        is_combat_move: Is there combat at the destination?
    
    Returns:
        MoveValidation with result and details
    """
    # Check hexes exist
    from_hex_obj = state.get_hex(from_hex)
    to_hex_obj = state.get_hex(to_hex)
    
    if not from_hex_obj or not to_hex_obj:
        return MoveValidation(
            valid=False,
            result=MoveResult.INVALID_HEX,
            message="Invalid hex ID"
        )
    
    # Check adjacency
    if not are_hexes_adjacent(from_hex, to_hex):
        return MoveValidation(
            valid=False,
            result=MoveResult.NOT_ADJACENT,
            message=f"Hex {to_hex} is not adjacent to hex {from_hex}"
        )
    
    # Get terrain info
    hex_terrain = to_hex_obj.terrain
    hexside_terrain = get_hexside_terrain(from_hex, to_hex, state)
    
    if hexside_terrain is None:
        hexside_terrain = 'C'  # Default to clear if not set
    
    # Determine unit type early - air units have very different rules
    unit_type = unit.unit_type if hasattr(unit, 'unit_type') else UnitType.GROUND
    is_air_unit = (unit_type == UnitType.AIR or unit_type == 1)  # AIR = 1
    
    # Air units: ignore hexside terrain entirely, only check destination hex
    if is_air_unit:
        if not can_air_unit_enter(hex_terrain):
            return MoveValidation(
                valid=False,
                result=MoveResult.IMPASSABLE_TERRAIN,
                message="Air unit cannot enter impassable terrain"
            )
        # Air units don't care about hexside at all - skip all hexside checks
    else:
        # Ground and sea units: check hexside terrain
        # Check for impassable hexside
        if hexside_terrain == 'X' or hexside_terrain == 'N':
            return MoveValidation(
                valid=False,
                result=MoveResult.IMPASSABLE_HEXSIDE,
                message="Cannot cross impassable hexside"
            )
        
        if unit_type == UnitType.GROUND or unit_type == 0:  # Ground units (GROUND = 0)
            if not can_ground_unit_enter(hex_terrain, hexside_terrain):
                return MoveValidation(
                    valid=False,
                    result=MoveResult.WRONG_UNIT_TYPE,
                    message=f"Ground unit cannot enter {hex_terrain} terrain via {hexside_terrain} hexside"
                )
        
        elif unit_type == UnitType.SEA or unit_type == 2:  # Sea units (SEA = 2)
            from_terrain = from_hex_obj.terrain
            if not can_sea_unit_enter(from_terrain, hex_terrain, hexside_terrain):
                return MoveValidation(
                    valid=False,
                    result=MoveResult.WRONG_UNIT_TYPE,
                    message="Sea unit cannot make this move"
                )
    
    # Check movement points
    has_regular_movement = unit.movement_remaining > 0 if hasattr(unit, 'movement_remaining') else True
    
    uses_road_bonus = False
    
    # Air units: simple movement - just check if they have movement points
    # They never use road bonus
    if is_air_unit:
        if not has_regular_movement:
            return MoveValidation(
                valid=False,
                result=MoveResult.NO_MOVEMENT_POINTS,
                message="Air unit has no movement points remaining"
            )
    else:
        # Ground/Sea units: can use road bonus if conditions are met
        has_road_move = unit.road_move_remaining > 0 if hasattr(unit, 'road_move_remaining') else False
        road_exists = has_road(from_hex, to_hex, state)
        # road_move_only means unit has been following roads the entire time - only then can they use road bonus
        still_on_roads = unit.road_move_only if hasattr(unit, 'road_move_only') else True
        
        if not has_regular_movement:
            # Can only use road bonus if: road exists on this hexside, have road moves left, AND have been following roads
            if road_exists and has_road_move and still_on_roads:
                uses_road_bonus = True
            else:
                return MoveValidation(
                    valid=False,
                    result=MoveResult.NO_MOVEMENT_POINTS,
                    message="Unit has no movement points remaining"
                )
    
    # Check: Can't enter combat with road move only
    if is_combat_move and uses_road_bonus:
        return MoveValidation(
            valid=False,
            result=MoveResult.ROAD_MOVE_INTO_COMBAT,
            message="Cannot enter combat using road bonus move"
        )
    
    # NOTE: "Started in combat" check DISABLED for now
    # The combat_start field is combat VALUE (int), not a boolean for whether
    # the unit started in combat. Need to add a proper started_in_combat field.
    # TODO: Re-enable after adding proper started_in_combat boolean field
    # if is_combat_move and hasattr(unit, 'started_in_combat') and unit.started_in_combat:
    #     return MoveValidation(
    #         valid=False,
    #         result=MoveResult.COMBAT_ENTRY_BLOCKED,
    #         message="Unit that started in combat cannot enter new combat"
    #     )
    
    # NOTE: Hexside control check DISABLED for now
    # Hexside control only applies during active combat - will be re-enabled
    # when combat system is implemented. The 'control' field in hex data is 
    # currently just storing initialization values, not active combat state.
    # TODO: Re-enable after combat implementation
    # hexside_control = get_hexside_control(from_hex, to_hex, state)
    # if hexside_control is not None and hexside_control >= 0:
    #     faction = state.get_faction(unit_faction_id)
    #     if faction and faction.initiative != hexside_control:
    #         return MoveValidation(
    #             valid=False,
    #             result=MoveResult.ENEMY_HEXSIDE,
    #             message="Cannot exit through enemy-controlled hexside"
    #         )
    
    # Ground-only checks: siege restrictions and continuous movement
    # Air units ignore all of this
    if not is_air_unit:
        # Get road info for these checks (we already calculated this for non-air units)
        road_exists_for_check = has_road(from_hex, to_hex, state)
        
        # Check interior siege restrictions
        unit_faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        if hasattr(unit, 'category'):
            category = unit.category
            if category == UnitCategory.INTERIOR_SIEGE or category == 4:
                if hexside_terrain not in ['C', 'F'] and not road_exists_for_check:
                    return MoveValidation(
                        valid=False,
                        result=MoveResult.SIEGE_RESTRICTION,
                        message="Interior siege units can only cross Clear/Forest hexsides or roads"
                    )
        
        # Check continuous movement (rough terrain stops further movement)
        if hasattr(unit, 'previous_location') and unit.previous_location != unit.location:
            # Unit has already moved this turn
            if hasattr(unit, 'road_move_only') and not unit.road_move_only:
                prev_hexside = get_hexside_terrain(unit.previous_location, unit.location, state)
                if prev_hexside and is_rough_terrain_hexside(prev_hexside):
                    if not road_exists_for_check:
                        return MoveValidation(
                            valid=False,
                            result=MoveResult.CONTINUOUS_MOVE_BLOCKED,
                            message="Cannot continue movement after crossing rough terrain"
                        )
    else:
        # For air units, just get faction ID for hostile check
        unit_faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
    
    # Check if destination has hostile units (triggers combat)
    # Using hostiles_at_hex instead of enemies_at_hex for future diplomacy support
    # (enemies may be non-hostile if there's a truce/neutral status)
    hostiles_at_dest = state.hostiles_at_hex(to_hex, unit_faction_id)
    enters_combat = len(hostiles_at_dest) > 0
    
    # All checks passed!
    return MoveValidation(
        valid=True,
        result=MoveResult.SUCCESS,
        message="Move is valid",
        movement_cost=1,
        uses_road_bonus=uses_road_bonus,
        enters_combat=enters_combat
    )


def validate_path(unit: Unit, path: List[int], state: GameState) -> Tuple[bool, List[MoveValidation], str]:
    """
    Validate an entire movement path for a unit.
    
    Args:
        unit: The unit attempting to move
        path: List of hex IDs to move through (not including starting hex)
        state: Current game state
    
    Returns:
        Tuple of (valid, list of validations for each step, overall message)
    """
    if not path:
        return False, [], "Empty path"
    
    validations = []
    current_hex = unit.location
    movement_remaining = unit.movement_remaining if hasattr(unit, 'movement_remaining') else 99
    road_move_remaining = unit.road_move_remaining if hasattr(unit, 'road_move_remaining') else 0
    
    for i, next_hex in enumerate(path):
        # Check if we're entering combat
        enemies = state.enemies_at_hex(next_hex, unit.faction.value if hasattr(unit.faction, 'value') else unit.faction)
        is_combat_move = len(enemies) > 0
        
        # Temporarily simulate unit state for validation
        # (In a more complete implementation, we'd track state changes)
        validation = can_move(current_hex, next_hex, unit, state, is_combat_move)
        validations.append(validation)
        
        if not validation.valid:
            return False, validations, f"Step {i+1} failed: {validation.message}"
        
        # Check movement points
        if validation.uses_road_bonus:
            if road_move_remaining <= 0:
                return False, validations, f"Step {i+1}: No road movement remaining"
            road_move_remaining -= 1
        else:
            if movement_remaining < validation.movement_cost:
                return False, validations, f"Step {i+1}: Not enough movement points"
            movement_remaining -= validation.movement_cost
        
        # If entering combat, path must end here
        if validation.enters_combat and i < len(path) - 1:
            return False, validations, f"Step {i+1}: Path continues past combat"
        
        current_hex = next_hex
    
    return True, validations, "Path is valid"


# =============================================================================
# HEXSIDE CONFLICT RESOLUTION
# =============================================================================

@dataclass
class HexsideUsage:
    """Track units crossing a specific hexside."""
    from_hex: int
    to_hex: int
    limit: int
    unit_moves: List[Tuple[int, int]]  # List of (unit_id, order_index)


def collect_hexside_usage(all_moves: Dict[int, List[int]], state: GameState) -> Dict[Tuple[int, int], HexsideUsage]:
    """
    Collect all movements crossing each hexside.
    
    Args:
        all_moves: Dict of unit_id -> path
        state: Game state
    
    Returns:
        Dict mapping (from_hex, to_hex) -> HexsideUsage
    """
    hexside_usage: Dict[Tuple[int, int], HexsideUsage] = {}
    
    for unit_id, path in all_moves.items():
        unit = state.get_unit(unit_id)
        if not unit:
            continue
        
        current_hex = unit.location
        
        for step_idx, next_hex in enumerate(path):
            # Normalize hexside key (smaller hex first)
            key = (min(current_hex, next_hex), max(current_hex, next_hex))
            
            if key not in hexside_usage:
                limit = get_hexside_limit(current_hex, next_hex, state)
                hexside_usage[key] = HexsideUsage(
                    from_hex=current_hex,
                    to_hex=next_hex,
                    limit=limit,
                    unit_moves=[]
                )
            
            hexside_usage[key].unit_moves.append((unit_id, step_idx))
            current_hex = next_hex
    
    return hexside_usage


def resolve_hexside_conflicts(hexside_usage: Dict[Tuple[int, int], HexsideUsage]) -> Dict[int, int]:
    """
    Resolve conflicts when too many units try to cross a hexside.
    
    For hexsides over capacity, randomly select which units fail.
    
    Args:
        hexside_usage: Dict of hexside -> usage info
    
    Returns:
        Dict of unit_id -> step_index where movement failed (units not in dict succeeded)
    """
    import random
    
    failed_moves: Dict[int, int] = {}
    
    for key, usage in hexside_usage.items():
        if len(usage.unit_moves) <= usage.limit:
            continue  # No conflict
        
        # Too many units - randomly pick losers
        moves = usage.unit_moves.copy()
        random.shuffle(moves)
        
        # First `limit` units succeed, rest fail
        losers = moves[usage.limit:]
        
        for unit_id, step_idx in losers:
            # Record the earliest failure for each unit
            if unit_id not in failed_moves or step_idx < failed_moves[unit_id]:
                failed_moves[unit_id] = step_idx
    
    return failed_moves

