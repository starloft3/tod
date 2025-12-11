"""
Vision system for Tides of Darkness.

Calculates which hexes are visible to each faction based on their units and bases.
This module is designed to be expandable for future vision rules (stealth, abilities, etc.)

Current Rules (v1 - simplified):
1. Each unit provides vision from its location, expanding outward by its vision stat
2. Each base provides vision from its location, expanding outward by its tier
3. No terrain blocks vision (may be added later)
4. Allied factions share vision based on initiative
"""
from typing import Set, Dict, List
from .game_state import GameState
from .models.enums import FactionId


def get_adjacent_hexes(hex_id: int) -> List[int]:
    """
    Get all hexes adjacent to the given hex.
    
    Map layout: 29 columns, alternating 39/38 hexes per column.
    Even columns (0, 2, 4...): 39 hexes
    Odd columns (1, 3, 5...): 38 hexes, offset down
    
    For flat-top hexes, adjacency depends on whether we're in an even or odd column.
    """
    # Determine which column this hex is in
    col = 0
    remaining = hex_id
    while remaining >= 0:
        col_size = 39 if col % 2 == 0 else 38
        if remaining < col_size:
            break
        remaining -= col_size
        col += 1
    
    row = remaining
    is_even_col = col % 2 == 0
    
    # Calculate hex IDs for each adjacent hex
    # Column sizes for offset calculation
    prev_col_size = 39 if (col - 1) % 2 == 0 else 38
    curr_col_size = 39 if col % 2 == 0 else 38
    next_col_size = 39 if (col + 1) % 2 == 0 else 38
    
    # Calculate starting hex ID for each column
    def col_start(c):
        """Get the starting hex ID for column c."""
        total = 0
        for i in range(c):
            total += 39 if i % 2 == 0 else 38
        return total
    
    adjacent = []
    
    # North (same column, row - 1)
    if row > 0:
        adjacent.append(hex_id - 1)
    
    # South (same column, row + 1)
    if row < curr_col_size - 1:
        adjacent.append(hex_id + 1)
    
    # For the diagonal neighbors, it depends on even/odd column
    if col > 0:
        prev_start = col_start(col - 1)
        if is_even_col:
            # Even column: NW is same row, SW is row + 1 in prev column
            # Previous column is odd (38 hexes, offset down)
            nw_row = row - 1
            sw_row = row
            if 0 <= nw_row < prev_col_size:
                adjacent.append(prev_start + nw_row)
            if 0 <= sw_row < prev_col_size:
                adjacent.append(prev_start + sw_row)
        else:
            # Odd column: NW is row, SW is row + 1 in prev column
            # Previous column is even (39 hexes)
            nw_row = row
            sw_row = row + 1
            if 0 <= nw_row < prev_col_size:
                adjacent.append(prev_start + nw_row)
            if 0 <= sw_row < prev_col_size:
                adjacent.append(prev_start + sw_row)
    
    if col < 28:  # Max column is 28
        next_start = col_start(col + 1)
        if is_even_col:
            # Even column: NE is same row - 1, SE is same row in next column
            # Next column is odd (38 hexes, offset down)
            ne_row = row - 1
            se_row = row
            if 0 <= ne_row < next_col_size:
                adjacent.append(next_start + ne_row)
            if 0 <= se_row < next_col_size:
                adjacent.append(next_start + se_row)
        else:
            # Odd column: NE is row, SE is row + 1 in next column
            # Next column is even (39 hexes)
            ne_row = row
            se_row = row + 1
            if 0 <= ne_row < next_col_size:
                adjacent.append(next_start + ne_row)
            if 0 <= se_row < next_col_size:
                adjacent.append(next_start + se_row)
    
    # Filter out invalid hex IDs
    return [h for h in adjacent if 0 <= h <= 1116]


def expand_vision(start_hex: int, vision_range: int) -> Set[int]:
    """
    Expand vision outward from a starting hex by the given range.
    
    Args:
        start_hex: The hex ID to start from
        vision_range: How many hexes outward to see (0 = just the start hex)
    
    Returns:
        Set of all visible hex IDs
    """
    if vision_range < 0:
        return set()
    
    visible = {start_hex}
    frontier = {start_hex}
    
    for _ in range(vision_range):
        new_frontier = set()
        for hex_id in frontier:
            for adjacent in get_adjacent_hexes(hex_id):
                if adjacent not in visible:
                    visible.add(adjacent)
                    new_frontier.add(adjacent)
        frontier = new_frontier
    
    return visible


def compute_visible_hexes(state: GameState, faction_id: int) -> Set[int]:
    """
    Compute all hexes visible to a faction.
    
    Args:
        state: The current game state
        faction_id: The faction ID to compute vision for
    
    Returns:
        Set of all hex IDs visible to this faction
    """
    visible = set()
    
    # Get the faction's initiative (for allied vision sharing)
    faction = state.get_faction(faction_id)
    if not faction:
        return visible
    
    faction_initiative = faction.initiative
    
    # Find all factions that share vision (same initiative = allied)
    allied_faction_ids = set()
    for fid, f in state.factions.items():
        if f.initiative == faction_initiative:
            allied_faction_ids.add(fid.value if hasattr(fid, 'value') else fid)
    
    # Add vision from all allied units
    for unit in state.units.values():
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        if unit_faction in allied_faction_ids and unit.alive:
            unit_visible = expand_vision(unit.location, unit.vision)
            visible.update(unit_visible)
    
    # Add vision from all allied bases
    for base in state.bases.values():
        base_faction = base.faction.value if hasattr(base.faction, 'value') else base.faction
        if base_faction in allied_faction_ids:
            # Base vision = tier
            base_visible = expand_vision(base.location, base.tier)
            visible.update(base_visible)
    
    return visible


def compute_all_faction_vision(state: GameState) -> Dict[int, Set[int]]:
    """
    Compute visible hexes for all factions.
    
    Returns:
        Dictionary mapping faction ID to set of visible hex IDs
    """
    vision_map = {}
    for faction_id in state.factions.keys():
        fid = faction_id.value if hasattr(faction_id, 'value') else faction_id
        vision_map[fid] = compute_visible_hexes(state, fid)
    return vision_map


# =============================================================================
# FUTURE EXPANSION HOOKS
# =============================================================================
# These functions are placeholders for future vision rules.

def is_unit_stealthed(unit, observer_faction: int) -> bool:
    """
    Check if a unit is stealthed from the observer's perspective.
    
    Future: Implement stealth detection based on unit abilities,
    proximity, terrain, etc.
    """
    # TODO: Implement stealth logic
    return False


def get_special_vision_sources(state: GameState, faction_id: int) -> Set[int]:
    """
    Get additional visible hexes from special sources.
    
    Future: Scout abilities, watchtowers, spells, etc.
    """
    # TODO: Implement special vision sources
    return set()

