"""
Base endpoints.

CRUD operations and queries for game bases/cities.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..schemas import BaseSummary, BaseDetail
from ..dependencies import get_game_state
from tod.core import GameState

router = APIRouter(prefix="/bases", tags=["bases"])


def base_to_summary(base) -> BaseSummary:
    """Convert Base model to BaseSummary schema."""
    return BaseSummary(
        id=base.id,
        name=base.name,
        location=base.location,
        factionId=base.faction.value,
        tier=base.tier
    )


def base_to_detail(base) -> BaseDetail:
    """Convert Base model to BaseDetail schema."""
    return BaseDetail(
        id=base.id,
        name=base.name,
        location=base.location,
        factionId=base.faction.value,
        tier=base.tier,
        gold=base.gold,
        lumber=base.lumber,
        oil=base.oil,
        actions=base.actions
    )


@router.get("", response_model=List[BaseSummary])
async def list_bases(
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId", description="Filter by faction"),
    tier: Optional[int] = Query(None, ge=0, le=3, description="Filter by tier"),
    limit: int = Query(100, le=200),
    offset: int = Query(0, ge=0)
):
    """List all bases with optional filters."""
    bases = list(state.bases.values())
    
    if faction_id is not None:
        bases = [b for b in bases if b.faction.value == faction_id]
    if tier is not None:
        bases = [b for b in bases if b.tier == tier]
    
    bases = bases[offset:offset + limit]
    return [base_to_summary(b) for b in bases]


@router.get("/{base_id}", response_model=BaseDetail)
async def get_base(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get detailed information about a specific base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    return base_to_detail(base)


@router.get("/at/{hex_id}", response_model=Optional[BaseDetail])
async def get_base_at_hex(
    hex_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get the base at a specific hex, if any."""
    base = state.base_at_hex(hex_id)
    if not base:
        return None
    return base_to_detail(base)


@router.get("/faction/{faction_id}", response_model=List[BaseSummary])
async def get_faction_bases(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all bases belonging to a faction."""
    bases = state.bases_by_faction(faction_id)
    return [base_to_summary(b) for b in bases]


@router.get("/faction/{faction_id}/resources")
async def get_faction_resources(
    faction_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get total resources stored across all faction bases."""
    bases = state.bases_by_faction(faction_id)
    
    total_gold = sum(b.gold for b in bases)
    total_lumber = sum(b.lumber for b in bases)
    total_oil = sum(b.oil for b in bases)
    
    # Calculate income (this is simplified - actual income depends on farms/mills/rigs)
    gold_income, lumber_income, oil_income = state.faction_income(faction_id)
    
    return {
        "factionId": faction_id,
        "stored": {
            "gold": total_gold,
            "lumber": total_lumber,
            "oil": total_oil
        },
        "income": {
            "gold": gold_income,
            "lumber": lumber_income,
            "oil": oil_income
        },
        "baseCount": len(bases),
        "totalTier": sum(b.tier for b in bases)
    }


@router.get("/capitals", response_model=List[BaseSummary])
async def get_capitals(
    state: GameState = Depends(get_game_state),
    faction_id: Optional[int] = Query(None, alias="factionId")
):
    """Get all capital cities (tier 3 bases)."""
    capitals = [b for b in state.bases.values() if b.tier >= 3]
    
    if faction_id is not None:
        capitals = [b for b in capitals if b.faction.value == faction_id]
    
    return [base_to_summary(b) for b in capitals]

