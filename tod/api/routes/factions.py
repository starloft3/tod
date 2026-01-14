"""
Faction endpoints.

Information about factions and their diplomatic state.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..schemas import FactionSummary, FactionDetail
from ..dependencies import get_game_state
from tod.core import GameState
from tod.core.models.enums import HORDE_FACTIONS, ALLIANCE_FACTIONS

router = APIRouter(prefix="/factions", tags=["factions"])


def faction_to_summary(faction) -> FactionSummary:
    """Convert Faction model to FactionSummary schema."""
    # Get vassalOf value (None if independent)
    vassal_of = None
    if faction.vassal_of is not None:
        vassal_of = faction.vassal_of.value if hasattr(faction.vassal_of, 'value') else faction.vassal_of
    
    return FactionSummary(
        id=faction.id.value,
        name=faction.name,
        initiative=faction.initiative,
        isDefeated=faction.is_defeated,
        isHorde=faction.is_horde,
        isAlliance=faction.is_alliance,
        color=faction.color_hex,
        vassalOf=vassal_of
    )


def faction_to_detail(faction, state=None) -> FactionDetail:
    """Convert Faction model to FactionDetail schema."""
    # Get vassalOf value (None if independent)
    vassal_of = None
    if faction.vassal_of is not None:
        vassal_of = faction.vassal_of.value if hasattr(faction.vassal_of, 'value') else faction.vassal_of
    
    # Get list of vassal faction IDs
    vassal_ids = []
    if state:
        vassals = state.get_vassals(faction.id.value)
        vassal_ids = [v.id.value for v in vassals]
    
    return FactionDetail(
        id=faction.id.value,
        name=faction.name,
        initiative=faction.initiative,
        isDefeated=faction.is_defeated,
        membership=faction.membership,
        isLeader=faction.is_leader,
        leaderVote=faction.leader_vote,
        allianceVotes=faction.alliance_votes,
        hordeDecision=faction.horde_decision,
        warchiefDecision=faction.warchief_decision,
        color=faction.color_hex,
        colorRgb=list(faction.color),
        vassalOf=vassal_of,
        vassals=vassal_ids
    )


@router.get("", response_model=List[FactionSummary])
async def list_factions(
    state: GameState = Depends(get_game_state),
    horde_only: bool = Query(False, alias="hordeOnly"),
    alliance_only: bool = Query(False, alias="allianceOnly"),
    active_only: bool = Query(False, alias="activeOnly", description="Exclude defeated factions")
):
    """List all factions with optional filters."""
    factions = list(state.factions.values())
    
    if horde_only:
        factions = [f for f in factions if f.is_horde]
    elif alliance_only:
        factions = [f for f in factions if f.is_alliance]
    
    if active_only:
        factions = [f for f in factions if not f.is_defeated]
    
    return [faction_to_summary(f) for f in factions]


# Static routes MUST come before dynamic /{faction_id} routes
@router.get("/horde", response_model=List[FactionSummary])
async def get_horde_factions(
    state: GameState = Depends(get_game_state),
    active_only: bool = Query(False, alias="activeOnly")
):
    """Get all Horde factions."""
    factions = [state.factions[fid] for fid in HORDE_FACTIONS 
                if fid in state.factions]
    
    if active_only:
        factions = [f for f in factions if not f.is_defeated]
    
    return [faction_to_summary(f) for f in factions]


@router.get("/alliance", response_model=List[FactionSummary])
async def get_alliance_factions(
    state: GameState = Depends(get_game_state),
    active_only: bool = Query(False, alias="activeOnly")
):
    """Get all Alliance factions."""
    factions = [state.factions[fid] for fid in ALLIANCE_FACTIONS 
                if fid in state.factions]
    
    if active_only:
        factions = [f for f in factions if not f.is_defeated]
    
    return [faction_to_summary(f) for f in factions]


@router.get("/initiative/{initiative}", response_model=List[FactionSummary])
async def get_factions_by_initiative(
    initiative: int,
    state: GameState = Depends(get_game_state)
):
    """Get all factions with a specific initiative value."""
    factions = state.factions_in_initiative(initiative)
    return [faction_to_summary(state.factions[fid]) for fid in factions]


# Dynamic routes with path parameters come LAST
@router.get("/{faction_id}", response_model=FactionDetail)
async def get_faction(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get detailed information about a specific faction."""
    faction = state.get_faction(faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction {faction_id} not found")
    return faction_to_detail(faction, state)


@router.get("/{faction_id}/summary")
async def get_faction_summary(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get a comprehensive summary of a faction's status."""
    faction = state.get_faction(faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction {faction_id} not found")
    
    units = state.units_by_faction(faction_id)
    alive_units = [u for u in units if u.alive]
    bases = state.bases_by_faction(faction_id)
    
    gold_income, lumber_income, oil_income = state.faction_income(faction_id)
    
    # Find allies (same initiative)
    allies = [f for f in state.factions.values() 
              if f.initiative == faction.initiative and f.id != faction.id]
    
    return {
        "faction": faction_to_detail(faction, state),
        "military": {
            "totalUnits": len(units),
            "aliveUnits": len(alive_units),
            "heroes": len([u for u in alive_units if u.tier > 0]),
        },
        "economy": {
            "bases": len(bases),
            "capitals": len([b for b in bases if b.tier >= 3]),
            "totalGold": sum(b.gold for b in bases),
            "totalLumber": sum(b.lumber for b in bases),
            "totalOil": sum(b.oil for b in bases),
            "goldIncome": gold_income,
            "lumberIncome": lumber_income,
            "oilIncome": oil_income,
        },
        "diplomacy": {
            "allies": [faction_to_summary(a) for a in allies],
            "isHorde": faction.is_horde,
            "isAlliance": faction.is_alliance,
        }
    }


@router.get("/{faction_id}/food")
async def get_faction_food(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get food status for a faction (unit cap system)."""
    faction = state.get_faction(faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction {faction_id} not found")
    
    food_status = state.faction_food_status(faction_id)
    
    return {
        "factionId": faction_id,
        "factionName": faction.name,
        "foodFromBases": food_status['food_from_bases'],
        "foodFromFarms": food_status['food_from_farms'],
        "foodLimit": food_status['food_limit'],
        "unitCount": food_status['unit_count'],
        "foodSurplus": food_status['food_surplus'],
        "isCapped": food_status['is_capped'],
        "canBuild": food_status['can_build']
    }


@router.get("/food/all")
async def get_all_factions_food(
    state: GameState = Depends(get_game_state),
    active_only: bool = Query(True, alias="activeOnly")
):
    """Get food status for all factions (admin view)."""
    factions = list(state.factions.values())
    
    if active_only:
        factions = [f for f in factions if f.is_active]
    
    result = []
    for faction in factions:
        food_status = state.faction_food_status(faction.id.value)
        result.append({
            "factionId": faction.id.value,
            "factionName": faction.name,
            "color": faction.color_hex,
            "foodLimit": food_status['food_limit'],
            "unitCount": food_status['unit_count'],
            "foodSurplus": food_status['food_surplus'],
            "isCapped": food_status['is_capped']
        })
    
    # Sort by faction ID
    result.sort(key=lambda x: x['factionId'])
    
    return result

