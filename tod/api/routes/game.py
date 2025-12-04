"""
Game state endpoints.

Provides overview and control of the game state.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from ..schemas import (
    GameStateSummary, TurnStateSchema, APIResponse
)
from ..dependencies import get_game_state
from tod.core import GameState, GamePhase

router = APIRouter(prefix="/game", tags=["game"])


@router.get("/status", response_model=GameStateSummary)
async def get_game_status(state: GameState = Depends(get_game_state)):
    """Get current game state summary."""
    alive_count = sum(1 for u in state.units.values() if u.alive)
    
    return GameStateSummary(
        turn=TurnStateSchema(
            turnNumber=state.turn.turn_number,
            currentInitiative=state.turn.current_initiative,
            currentFaction=state.turn.current_faction,
            phase=state.turn.phase.name.lower()
        ),
        unitCount=len(state.units),
        aliveUnitCount=alive_count,
        hexCount=len(state.hexes),
        baseCount=len(state.bases),
        factionCount=len(state.factions),
        roadCount=len(state.roads),
        caravanCount=len(state.caravans)
    )


@router.get("/turn", response_model=TurnStateSchema)
async def get_turn_state(state: GameState = Depends(get_game_state)):
    """Get current turn information."""
    return TurnStateSchema(
        turnNumber=state.turn.turn_number,
        currentInitiative=state.turn.current_initiative,
        currentFaction=state.turn.current_faction,
        phase=state.turn.phase.name.lower()
    )


@router.post("/reload", response_model=APIResponse)
async def reload_game_state():
    """
    Reload game state from database.
    
    This will discard any in-memory changes and reload from the database.
    """
    from ..dependencies import reload_game_state
    try:
        reload_game_state()
        return APIResponse(success=True, message="Game state reloaded from database")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload: {str(e)}")


@router.get("/statistics")
async def get_game_statistics(state: GameState = Depends(get_game_state)):
    """Get detailed game statistics."""
    # Count units by faction
    units_by_faction = {}
    for unit in state.units.values():
        if unit.alive:
            fid = unit.faction.value
            units_by_faction[fid] = units_by_faction.get(fid, 0) + 1
    
    # Count bases by faction
    bases_by_faction = {}
    for base in state.bases.values():
        fid = base.faction.value
        bases_by_faction[fid] = bases_by_faction.get(fid, 0) + 1
    
    # Calculate faction incomes
    incomes = {}
    for fid in state.factions:
        gold, lumber, oil = state.faction_income(fid)
        incomes[fid] = {"gold": gold, "lumber": lumber, "oil": oil}
    
    return {
        "unitsByFaction": units_by_faction,
        "basesByFaction": bases_by_faction,
        "factionIncomes": incomes,
        "totalUnits": len(state.units),
        "aliveUnits": sum(units_by_faction.values()),
        "totalBases": len(state.bases),
        "totalHexes": len(state.hexes),
    }

