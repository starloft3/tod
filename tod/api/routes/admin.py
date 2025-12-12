"""
Admin endpoints for game management.

These endpoints are for game masters/admins to:
- View game state and orders
- Trigger turn resolution
- Manage game phases
- Debug and test
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from ..dependencies import get_game_state
from tod.core import GameState
from tod.core.game_state import GamePhase, RoundSide
from tod.core.order_manager import get_order_manager, reset_order_manager
from tod.core.resolution_engine import ResolutionEngine


router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Response Models
# ============================================================================

class AdminResponse(BaseModel):
    """Standard admin operation response."""
    success: bool
    message: str
    timestamp: str = None
    data: Optional[dict] = None
    
    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)


# ============================================================================
# Game Status
# ============================================================================

@router.get("/status")
async def get_admin_status(state: GameState = Depends(get_game_state)):
    """
    Get comprehensive admin view of game status.
    
    Includes turn state, order summary, and entity counts.
    """
    order_manager = get_order_manager()
    order_summary = order_manager.get_order_summary()
    
    # Get factions in current initiative
    current_factions = state.factions_in_initiative(state.turn.current_initiative)
    current_faction_names = [
        state.factions[f].name for f in current_factions if f in state.factions
    ]
    
    return {
        "timestamp": datetime.now().isoformat(),
        "turn": {
            "roundNumber": state.turn.round_number,
            "roundSide": state.turn.round_side.value,
            "turnNumber": state.turn.turn_number,  # Sequential turn count
            "phase": state.turn.phase.name,
            "currentInitiative": state.turn.current_initiative,
            "currentFactions": current_faction_names,
            "completedInitiatives": list(state.turn.completed_initiatives),
            "remainingInitiatives": [
                i for i in state.get_current_round_initiatives() 
                if i not in state.turn.completed_initiatives
            ],
        },
        "initiatives": {
            "horde": state.get_horde_initiatives(),
            "alliance": state.get_alliance_initiatives(),
        },
        "entities": {
            "units": len([u for u in state.units.values() if u.alive]),
            "deadUnits": len([u for u in state.units.values() if not u.alive]),
            "bases": len(state.bases),
            "factions": len(state.factions),
            "hexes": len(state.hexes),
        },
        "orders": order_summary,
        "factionStatus": {
            fid: {
                "name": f.name,
                "initiative": f.initiative,
                "isDefeated": f.is_defeated,
                "isHorde": state.is_horde_faction(fid),
                "ordersSubmitted": fid in order_manager.locked_factions,
                "orderCount": order_manager.faction_orders.get(fid, None) and 
                             order_manager.faction_orders[fid].total_orders or 0
            }
            for fid, f in state.factions.items()
            if f.initiative >= 0  # Exclude -1 initiative factions
        }
    }


@router.get("/orders")
async def get_all_orders_admin():
    """Get detailed view of all submitted orders."""
    order_manager = get_order_manager()
    return {
        "timestamp": datetime.now().isoformat(),
        "summary": order_manager.get_order_summary(),
        "orders": order_manager.to_dict()
    }


# ============================================================================
# Game Initialization
# ============================================================================

@router.post("/new-game", response_model=AdminResponse)
async def start_new_game(state: GameState = Depends(get_game_state)):
    """
    Initialize a brand new game.
    
    Starts with Horde Round 1, first Horde initiative (typically Amani).
    """
    reset_order_manager()
    result = state.start_new_game()
    
    return AdminResponse(
        success=result.get('success', False),
        message=result.get('message', 'Unknown error'),
        data={
            "roundNumber": result.get('round_number'),
            "roundSide": result.get('round_side'),
            "initiative": result.get('initiative'),
            "factions": result.get('factions', [])
        }
    )


# ============================================================================
# Phase Management
# ============================================================================

@router.post("/phase/planning", response_model=AdminResponse)
async def start_planning_phase(state: GameState = Depends(get_game_state)):
    """
    Start/restart the planning phase for the current initiative.
    
    Clears orders and allows factions to submit new orders.
    """
    state.turn.phase = GamePhase.PLANNING
    state.turn.orders_submitted.clear()
    reset_order_manager()
    
    current_factions = state.factions_in_initiative(state.turn.current_initiative)
    faction_names = [state.factions[f].name for f in current_factions if f in state.factions]
    
    return AdminResponse(
        success=True,
        message=f"Planning phase started for initiative {state.turn.current_initiative}",
        data={
            "phase": GamePhase.PLANNING.name,
            "roundNumber": state.turn.round_number,
            "roundSide": state.turn.round_side.value,
            "initiative": state.turn.current_initiative,
            "factions": faction_names
        }
    )


@router.post("/phase/lock-orders", response_model=AdminResponse)
async def lock_all_orders(state: GameState = Depends(get_game_state)):
    """
    Lock all faction orders for the current initiative.
    
    No more order changes allowed after this.
    """
    order_manager = get_order_manager()
    
    # Lock orders for factions in the current initiative
    current_factions = state.factions_in_initiative(state.turn.current_initiative)
    for faction_id in current_factions:
        order_manager.lock_faction_orders(faction_id)
    
    return AdminResponse(
        success=True,
        message=f"Locked orders for {len(current_factions)} faction(s)",
        data={"lockedFactions": list(order_manager.locked_factions)}
    )


@router.post("/phase/resolution", response_model=AdminResponse)
async def start_resolution_phase(state: GameState = Depends(get_game_state)):
    """
    Start the resolution phase.
    
    Locks all orders and prepares for turn resolution.
    """
    if state.turn.phase != GamePhase.PLANNING:
        return AdminResponse(
            success=False,
            message=f"Cannot start resolution from phase {state.turn.phase.name}"
        )
    
    state.turn.phase = GamePhase.RESOLUTION
    
    # Lock all orders for current initiative
    order_manager = get_order_manager()
    current_factions = state.factions_in_initiative(state.turn.current_initiative)
    for faction_id in current_factions:
        order_manager.lock_faction_orders(faction_id)
    
    return AdminResponse(
        success=True,
        message="Resolution phase started",
        data={
            "phase": GamePhase.RESOLUTION.name,
            "initiative": state.turn.current_initiative,
            "totalOrders": sum(
                fo.total_orders for fo in order_manager.faction_orders.values()
            )
        }
    )


# ============================================================================
# Turn Resolution
# ============================================================================

@router.post("/resolve-turn", response_model=AdminResponse)
async def resolve_current_turn(state: GameState = Depends(get_game_state)):
    """
    Resolve the current initiative's turn.
    
    Processes all orders (movement, combat, economic) and advances to the next initiative.
    Uses the ResolutionEngine for actual game logic.
    """
    order_manager = get_order_manager()
    
    # Store pre-resolution state for reporting
    old_initiative = state.turn.current_initiative
    current_factions = state.factions_in_initiative(old_initiative)
    faction_names = [state.factions[f].name for f in current_factions if f in state.factions]
    
    # Build pre-resolution log
    resolution_log = []
    for faction_id in current_factions:
        orders = order_manager.faction_orders.get(faction_id)
        if not orders:
            continue
            
        faction_obj = state.factions.get(faction_id)
        faction_name = faction_obj.name if faction_obj else f"Faction {faction_id}"
        
        for mo in orders.movement_orders:
            unit = state.get_unit(mo.unit_id)
            unit_name = unit.name if unit else f"Unit {mo.unit_id}"
            old_location = unit.location if unit else "?"
            resolution_log.append({
                "type": "movement",
                "faction": faction_name,
                "unit": unit_name,
                "unitId": mo.unit_id,
                "from": old_location,
                "to": mo.path[-1] if mo.path else "?",
                "path": mo.path,
            })
    
    # Run the resolution engine!
    engine = ResolutionEngine(state, order_manager)
    result = engine.resolve_current_turn()
    
    return AdminResponse(
        success=result.success,
        message=result.message,
        data={
            "previousInitiative": old_initiative,
            "factions": faction_names,
            "movementsApplied": result.movements_applied,
            "combatsTriggered": result.combats_triggered,
            "newRoundNumber": state.turn.round_number,
            "newRoundSide": state.turn.round_side.value,
            "newInitiative": state.turn.current_initiative,
            "resolutionLog": resolution_log
        }
    )


@router.post("/advance-initiative", response_model=AdminResponse)
async def advance_initiative_without_resolution(state: GameState = Depends(get_game_state)):
    """
    Skip to the next initiative without resolving orders.
    
    Use this for testing or skipping turns.
    """
    old_init = state.turn.current_initiative
    result = state.advance_to_next_initiative()
    reset_order_manager()
    
    return AdminResponse(
        success=True,
        message=f"Skipped initiative {old_init}. {result.get('message', '')}",
        data={
            "previousInitiative": old_init,
            "action": result.get('action'),
            "newInitiative": result.get('initiative'),
            "roundNumber": result.get('round_number'),
            "roundSide": result.get('round_side')
        }
    )


# ============================================================================
# Debug Endpoints
# ============================================================================

@router.post("/reset-orders", response_model=AdminResponse)
async def reset_all_orders():
    """Reset/clear all orders."""
    reset_order_manager()
    return AdminResponse(
        success=True,
        message="All orders have been cleared"
    )


@router.get("/debug/initiatives")
async def debug_initiatives(state: GameState = Depends(get_game_state)):
    """Get detailed breakdown of initiatives."""
    horde_inits = state.get_horde_initiatives()
    alliance_inits = state.get_alliance_initiatives()
    
    result = {
        "horde": {},
        "alliance": {}
    }
    
    for init in horde_inits:
        factions = state.factions_in_initiative(init)
        result["horde"][init] = [
            {"id": fid, "name": state.factions[fid].name}
            for fid in factions if fid in state.factions
        ]
    
    for init in alliance_inits:
        factions = state.factions_in_initiative(init)
        result["alliance"][init] = [
            {"id": fid, "name": state.factions[fid].name}
            for fid in factions if fid in state.factions
        ]
    
    return result


@router.get("/debug/unit/{unit_id}")
async def debug_unit(unit_id: int, state: GameState = Depends(get_game_state)):
    """Get detailed debug info for a unit."""
    unit = state.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    
    # Get any orders for this unit
    order_manager = get_order_manager()
    unit_orders = []
    for faction_id, orders in order_manager.faction_orders.items():
        for mo in orders.movement_orders:
            if mo.unit_id == unit_id:
                unit_orders.append({"type": "movement", "path": mo.path})
    
    return {
        "unit": {
            "id": unit.id,
            "name": unit.name,
            "faction": unit.faction,
            "location": unit.location,
            "hp": unit.hp,
            "maxHp": unit.max_hp,
            "movement": unit.movement,
            "attack": unit.attack,
            "defense": unit.defense,
            "alive": unit.alive,
        },
        "orders": unit_orders,
        "hexInfo": state.get_hex(unit.location).__dict__ if state.get_hex(unit.location) else None
    }


@router.get("/debug/base/{base_id}")
async def debug_base(base_id: int, state: GameState = Depends(get_game_state)):
    """Get detailed debug info for a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Get units at this base
    units_at_base = state.units_at_hex(base.location)
    
    return {
        "base": {
            "id": base.id,
            "name": base.name,
            "faction": base.faction,
            "location": base.location,
            "tier": base.tier,
            "gold": base.gold,
            "lumber": base.lumber,
            "oil": base.oil,
        },
        "units": [{"id": u.id, "name": u.name} for u in units_at_base],
        "hexInfo": state.get_hex(base.location).__dict__ if state.get_hex(base.location) else None
    }
