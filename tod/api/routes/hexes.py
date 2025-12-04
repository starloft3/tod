"""
Hex/Map endpoints.

Queries for map hexes and terrain.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..schemas import HexSummary, HexDetail, HexSideSchema, VisibleHexesResponse
from ..dependencies import get_game_state
from tod.core import GameState

router = APIRouter(prefix="/hexes", tags=["hexes"])


def hex_to_summary(hex_obj, state: GameState) -> HexSummary:
    """Convert Hex model to HexSummary schema."""
    has_base = state.base_at_hex(hex_obj.id) is not None
    has_units = len(state.units_at_hex(hex_obj.id)) > 0
    
    return HexSummary(
        id=hex_obj.id,
        terrain=hex_obj.terrain,
        hasBase=has_base,
        hasUnits=has_units
    )


def hex_to_detail(hex_obj) -> HexDetail:
    """Convert Hex model to HexDetail schema."""
    return HexDetail(
        id=hex_obj.id,
        terrain=hex_obj.terrain,
        north=HexSideSchema(terrain=hex_obj.north.terrain, control=hex_obj.north.control),
        northeast=HexSideSchema(terrain=hex_obj.northeast.terrain, control=hex_obj.northeast.control),
        southeast=HexSideSchema(terrain=hex_obj.southeast.terrain, control=hex_obj.southeast.control),
        south=HexSideSchema(terrain=hex_obj.south.terrain, control=hex_obj.south.control),
        southwest=HexSideSchema(terrain=hex_obj.southwest.terrain, control=hex_obj.southwest.control),
        northwest=HexSideSchema(terrain=hex_obj.northwest.terrain, control=hex_obj.northwest.control),
        building=hex_obj.building.value,
        hasOil=hex_obj.has_oil,
        farm=hex_obj.farm,
        mill=hex_obj.mill,
        rig=hex_obj.rig,
        gold=hex_obj.gold,
        newCombat=hex_obj.new_combat,
        battleFought=hex_obj.battle_fought,
        assisted=hex_obj.assisted,
        expansionOwner=hex_obj.expansion_owner
    )


@router.get("", response_model=List[HexSummary])
async def list_hexes(
    state: GameState = Depends(get_game_state),
    terrain: Optional[str] = Query(None, description="Filter by terrain type (C, F, M, O, S, X)"),
    has_base: Optional[bool] = Query(None, alias="hasBase", description="Filter by has base"),
    has_units: Optional[bool] = Query(None, alias="hasUnits", description="Filter by has units"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """List hexes with optional filters."""
    hexes = list(state.hexes.values())
    
    if terrain:
        hexes = [h for h in hexes if h.terrain == terrain.upper()]
    
    # These filters are expensive, apply after terrain filter
    if has_base is not None:
        hexes = [h for h in hexes if (state.base_at_hex(h.id) is not None) == has_base]
    
    if has_units is not None:
        hexes = [h for h in hexes if (len(state.units_at_hex(h.id)) > 0) == has_units]
    
    hexes = hexes[offset:offset + limit]
    return [hex_to_summary(h, state) for h in hexes]


@router.get("/{hex_id}", response_model=HexDetail)
async def get_hex(
    hex_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get detailed information about a specific hex."""
    hex_obj = state.get_hex(hex_id)
    if not hex_obj:
        raise HTTPException(status_code=404, detail=f"Hex {hex_id} not found")
    return hex_to_detail(hex_obj)


@router.get("/{hex_id}/adjacent", response_model=List[HexSummary])
async def get_adjacent_hexes(
    hex_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get hexes adjacent to a specific hex."""
    if hex_id not in state.hexes:
        raise HTTPException(status_code=404, detail=f"Hex {hex_id} not found")
    
    adjacent_ids = state.adjacent_hexes(hex_id)
    adjacent = [state.hexes[aid] for aid in adjacent_ids if aid in state.hexes]
    
    return [hex_to_summary(h, state) for h in adjacent]


@router.get("/visible/{faction_id}", response_model=VisibleHexesResponse)
async def get_visible_hexes(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """
    Get hexes visible to a faction based on their units and bases.
    
    This is a simplified version - the full vision calculation
    accounts for terrain blocking line of sight.
    """
    faction = state.get_faction(faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction {faction_id} not found")
    
    visible = set()
    
    # Add hexes visible from units
    for unit in state.units_by_faction(faction_id):
        if not unit.alive:
            continue
        visible.add(unit.location)
        # Simple visibility - adjacent hexes based on vision range
        # Full implementation would account for terrain blocking
        for adj_id in state.adjacent_hexes(unit.location):
            visible.add(adj_id)
    
    # Add hexes visible from bases
    for base in state.bases_by_faction(faction_id):
        visible.add(base.location)
        for adj_id in state.adjacent_hexes(base.location):
            visible.add(adj_id)
    
    return VisibleHexesResponse(
        factionId=faction_id,
        initiative=faction.initiative,
        hexIds=sorted(list(visible))
    )


@router.get("/terrain/{terrain_type}", response_model=List[int])
async def get_hexes_by_terrain(
    terrain_type: str,
    state: GameState = Depends(get_game_state)
):
    """Get all hex IDs with a specific terrain type."""
    terrain = terrain_type.upper()
    valid_terrains = ['C', 'F', 'M', 'O', 'S', 'X', 'N', 'Q', 'W']
    
    if terrain not in valid_terrains:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid terrain type '{terrain}'. Valid: {valid_terrains}"
        )
    
    return [h.id for h in state.hexes.values() if h.terrain == terrain]


@router.get("/with-bases", response_model=List[HexSummary])
async def get_hexes_with_bases(
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId")
):
    """Get all hexes that contain bases."""
    base_hexes = set()
    
    for base in state.bases.values():
        if faction_id is None or base.faction.value == faction_id:
            base_hexes.add(base.location)
    
    hexes = [state.hexes[hid] for hid in base_hexes if hid in state.hexes]
    return [hex_to_summary(h, state) for h in hexes]

