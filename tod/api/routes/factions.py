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
    return FactionSummary(
        id=faction.id.value,
        name=faction.name,
        initiative=faction.initiative,
        isDefeated=faction.is_defeated,
        isHorde=faction.is_horde,
        isAlliance=faction.is_alliance
    )


def faction_to_detail(faction) -> FactionDetail:
    """Convert Faction model to FactionDetail schema."""
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
        warchiefDecision=faction.warchief_decision
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
    return faction_to_detail(faction)


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
        "faction": faction_to_detail(faction),
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

