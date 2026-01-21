"""
Expansion endpoints.

CRUD operations and queries for base expansions (farms, mills, oil rigs).
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..schemas import ExpansionSummary, ExpansionDetail
from ..dependencies import get_game_state
from tod.core import GameState

router = APIRouter(prefix="/expansions", tags=["expansions"])


def expansion_to_summary(expansion) -> ExpansionSummary:
    """Convert Expansion model to ExpansionSummary schema."""
    return ExpansionSummary(
        id=expansion.id,
        type=expansion.type.value,  # "farm", "mill", "rig"
        typeName=expansion.type_name,
        location=expansion.location,
        baseId=expansion.base_id
    )


def expansion_to_detail(expansion, state: GameState) -> ExpansionDetail:
    """Convert Expansion model to ExpansionDetail schema with additional data."""
    base = state.get_base(expansion.base_id)
    hex_obj = state.get_hex(expansion.location)
    
    return ExpansionDetail(
        id=expansion.id,
        type=expansion.type.value,
        typeName=expansion.type_name,
        location=expansion.location,
        baseId=expansion.base_id,
        baseName=base.name if base else "Unknown",
        factionId=base.faction.value if base else 0,
        goldMines=hex_obj.gold if hex_obj else 0
    )


@router.get("", response_model=List[ExpansionSummary])
async def list_expansions(
    state: GameState = Depends(get_game_state),
    base_id: Optional[int] = Query(None, alias="baseId", description="Filter by base"),
    faction_id: Optional[int] = Query(None, alias="factionId", description="Filter by faction"),
    expansion_type: Optional[str] = Query(None, alias="type", description="Filter by type (farm/mill/rig)"),
    limit: int = Query(200, le=500),
    offset: int = Query(0, ge=0)
):
    """List all expansions with optional filters."""
    expansions = list(state.expansions.values())
    
    if base_id is not None:
        expansions = [e for e in expansions if e.base_id == base_id]
    
    if faction_id is not None:
        # Need to look up base to check faction
        expansions = [e for e in expansions 
                     if state.get_base(e.base_id) and 
                     state.get_base(e.base_id).faction.value == faction_id]
    
    if expansion_type is not None:
        expansions = [e for e in expansions if e.type.value == expansion_type]
    
    expansions = expansions[offset:offset + limit]
    return [expansion_to_summary(e) for e in expansions]


@router.get("/count")
async def count_expansions(
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId")
):
    """Get counts of expansions by type."""
    expansions = list(state.expansions.values())
    
    if faction_id is not None:
        expansions = [e for e in expansions 
                     if state.get_base(e.base_id) and 
                     state.get_base(e.base_id).faction.value == faction_id]
    
    # Count by type
    from tod.core.models import ExpansionType
    farms = len([e for e in expansions if e.type == ExpansionType.FARM])
    mills = len([e for e in expansions if e.type == ExpansionType.LUMBER_MILL])
    rigs = len([e for e in expansions if e.type == ExpansionType.OIL_RIG])
    
    return {
        "total": len(expansions),
        "farms": farms,
        "mills": mills,
        "oilRigs": rigs
    }


@router.get("/{expansion_id}", response_model=ExpansionDetail)
async def get_expansion(
    expansion_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get detailed information about a specific expansion."""
    expansion = state.get_expansion(expansion_id)
    if not expansion:
        raise HTTPException(status_code=404, detail=f"Expansion {expansion_id} not found")
    return expansion_to_detail(expansion, state)


@router.get("/at/{hex_id}", response_model=Optional[ExpansionDetail])
async def get_expansion_at_hex(
    hex_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get the expansion at a specific hex, if any."""
    expansion = state.expansion_at_hex(hex_id)
    if not expansion:
        return None
    return expansion_to_detail(expansion, state)


@router.get("/base/{base_id}", response_model=List[ExpansionSummary])
async def get_base_expansions(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all expansions belonging to a base."""
    expansions = state.expansions_for_base(base_id)
    return [expansion_to_summary(e) for e in expansions]


@router.get("/faction/{faction_id}", response_model=List[ExpansionSummary])
async def get_faction_expansions(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all expansions belonging to a faction's bases."""
    expansions = [e for e in state.expansions.values() 
                 if state.get_base(e.base_id) and 
                 state.get_base(e.base_id).faction.value == faction_id]
    return [expansion_to_summary(e) for e in expansions]






