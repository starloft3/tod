"""
Unit endpoints.

CRUD operations and queries for game units.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..schemas import UnitSummary, UnitDetail, PaginatedResponse
from ..dependencies import get_game_state
from tod.core import GameState
from tod.core.models import UnitCategory

router = APIRouter(prefix="/units", tags=["units"])


def unit_to_summary(unit) -> UnitSummary:
    """Convert Unit model to UnitSummary schema."""
    return UnitSummary(
        id=unit.id,
        name=unit.name,
        factionId=unit.faction.value,
        hp=unit.hp,
        maxHp=unit.max_hp,
        location=unit.location,
        alive=unit.alive,
        # Movement stats for client-side validation
        movementMax=unit.movement_max,
        movementRemaining=unit.movement_remaining,
        roadMoveRemaining=unit.road_move_remaining,
        unitType=unit.unit_type.value,
        category=unit.category.name.lower()
    )


def unit_to_detail(unit) -> UnitDetail:
    """Convert Unit model to UnitDetail schema."""
    return UnitDetail(
        id=unit.id,
        name=unit.name,
        factionId=unit.faction.value,
        maxHp=unit.max_hp,
        hp=unit.hp,
        combat=unit.combat,
        category=unit.category.name.lower(),
        unitType=unit.unit_type.value,
        lightArmorMax=unit.light_armor_max,
        lightArmorCurrent=unit.light_armor_current,
        heavyArmor=unit.heavy_armor,
        naturalArmor=unit.natural_armor,
        armorBroken=unit.armor_broken,
        movementMax=unit.movement_max,
        movementRemaining=unit.movement_remaining,
        roadMoveRemaining=unit.road_move_remaining,
        roadMoveOnly=unit.road_move_only,
        vision=unit.vision,
        stealth=unit.stealth,
        location=unit.location,
        previousLocation=unit.previous_location,
        tier=unit.tier,
        tier1Ability=unit.tier_1_ability,
        tier2Ability=unit.tier_2_ability,
        tier3Ability=unit.tier_3_ability,
        tier4Ability=unit.tier_4_ability,
        alive=unit.alive,
        fired=unit.fired,
        terrainBonus=unit.terrain_bonus,
        flankBonus=unit.flank_bonus,
        holdBonus=unit.hold_bonus,
        combatStart=unit.combat_start,
        transportSlot1=unit.transport_slot_1,
        transportSlot2=unit.transport_slot_2,
        transportSlot3=unit.transport_slot_3
    )


@router.get("", response_model=List[UnitSummary])
async def list_units(
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId", description="Filter by faction"),
    alive_only: bool = Query(True, alias="aliveOnly", description="Only return alive units"),
    location: Optional[int] = Query(None, description="Filter by hex location"),
    limit: int = Query(500, le=2000, description="Max units to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    List all units with optional filters.
    """
    units = list(state.units.values())
    
    # Apply filters
    if faction_id is not None:
        units = [u for u in units if u.faction.value == faction_id]
    if alive_only:
        units = [u for u in units if u.alive]
    if location is not None:
        units = [u for u in units if u.location == location]
    
    # Paginate
    total = len(units)
    units = units[offset:offset + limit]
    
    return [unit_to_summary(u) for u in units]


@router.get("/{unit_id}", response_model=UnitDetail)
async def get_unit(
    unit_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get detailed information about a specific unit."""
    unit = state.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    return unit_to_detail(unit)


@router.get("/at/{hex_id}", response_model=List[UnitSummary])
async def get_units_at_hex(
    hex_id: int,
    state: GameState = Depends(get_game_state),
    alive_only: bool = Query(True, alias="aliveOnly")
):
    """Get all units at a specific hex."""
    units = state.units_at_hex(hex_id)
    if alive_only:
        units = [u for u in units if u.alive]
    return [unit_to_summary(u) for u in units]


@router.get("/faction/{faction_id}", response_model=List[UnitSummary])
async def get_faction_units(
    faction_id: int,
    state: GameState = Depends(get_game_state),
    alive_only: bool = Query(True, alias="aliveOnly")
):
    """Get all units belonging to a faction."""
    units = state.units_by_faction(faction_id)
    if alive_only:
        units = [u for u in units if u.alive]
    return [unit_to_summary(u) for u in units]


@router.get("/heroes", response_model=List[UnitSummary])
async def get_heroes(
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId"),
    alive_only: bool = Query(True, alias="aliveOnly")
):
    """Get all hero units (units with tier > 0 and special abilities)."""
    heroes = [u for u in state.units.values() 
              if u.tier > 0 and u.tier_1_ability != 'none']
    
    if faction_id is not None:
        heroes = [u for u in heroes if u.faction.value == faction_id]
    if alive_only:
        heroes = [u for u in heroes if u.alive]
    
    return [unit_to_summary(u) for u in heroes]


@router.get("/category/{category}", response_model=List[UnitSummary])
async def get_units_by_category(
    category: str,
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId"),
    alive_only: bool = Query(True, alias="aliveOnly")
):
    """Get units by combat category (melee, ranged, expert, etc.)."""
    try:
        cat = UnitCategory[category.upper()]
    except KeyError:
        valid = [c.name.lower() for c in UnitCategory]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid category '{category}'. Valid: {valid}"
        )
    
    units = [u for u in state.units.values() if u.category == cat]
    
    if faction_id is not None:
        units = [u for u in units if u.faction.value == faction_id]
    if alive_only:
        units = [u for u in units if u.alive]
    
    return [unit_to_summary(u) for u in units]

