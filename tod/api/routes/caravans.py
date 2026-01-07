"""
Caravan endpoints.

CRUD operations and queries for game caravans/trade routes.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from ..dependencies import get_game_state
from tod.core import GameState

router = APIRouter(prefix="/caravans", tags=["caravans"])


def caravan_to_dict(caravan, state: GameState) -> dict:
    """Convert Caravan model to dict for API response."""
    origin_base = state.get_base(caravan.origin_base_id)
    dest_base = state.get_base(caravan.destination_base_id)
    
    return {
        "id": caravan.id,
        "originBaseId": caravan.origin_base_id,
        "originBaseName": origin_base.name if origin_base else "Unknown",
        "originLocation": origin_base.location if origin_base else -1,
        "destBaseId": caravan.destination_base_id,
        "destBaseName": dest_base.name if dest_base else "Unknown",
        "destLocation": dest_base.location if dest_base else -1,
        "pathLength": len(caravan.path),
        "path": caravan.path,
        "terrainType": caravan.terrain_type.value if hasattr(caravan.terrain_type, 'value') else str(caravan.terrain_type),
        "initiative": caravan.initiative
    }


@router.get("")
async def list_caravans(
    state: GameState = Depends(get_game_state),
    initiative: Optional[int] = Query(None, description="Filter by initiative"),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """List all caravans."""
    caravans = state.caravans
    
    if initiative is not None:
        caravans = [c for c in caravans if c.initiative == initiative]
    
    caravans = caravans[offset:offset + limit]
    
    return {
        "caravans": [caravan_to_dict(c, state) for c in caravans],
        "total": len(state.caravans)
    }


@router.get("/{caravan_id}")
async def get_caravan(
    caravan_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get a specific caravan by ID."""
    if caravan_id < 0 or caravan_id >= len(state.caravans):
        raise HTTPException(status_code=404, detail=f"Caravan {caravan_id} not found")
    
    caravan = state.caravans[caravan_id]
    return caravan_to_dict(caravan, state)


@router.get("/initiative/{initiative}")
async def get_caravans_by_initiative(
    initiative: int,
    state: GameState = Depends(get_game_state)
):
    """Get all caravans for a specific initiative."""
    caravans = state.get_caravans_for_initiative(initiative)
    
    return {
        "initiative": initiative,
        "caravans": [caravan_to_dict(c, state) for c in caravans],
        "count": len(caravans)
    }


@router.get("/base/{base_id}")
async def get_caravans_for_base(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all caravans connected to a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    caravans = state.get_caravans_for_base(base_id)
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "caravans": [caravan_to_dict(c, state) for c in caravans],
        "count": len(caravans)
    }


@router.get("/count")
async def count_caravans(
    state: GameState = Depends(get_game_state),
    initiative: Optional[int] = Query(None, description="Filter by initiative")
):
    """Get total caravan count."""
    if initiative is not None:
        count = len([c for c in state.caravans if c.initiative == initiative])
    else:
        count = len(state.caravans)
    
    return {"count": count}


