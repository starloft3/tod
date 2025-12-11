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
from tod.core.game_state import GamePhase
from tod.core.order_manager import get_order_manager, reset_order_manager


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
    
    return {
        "timestamp": datetime.now().isoformat(),
        "turn": {
            "number": state.turn.turn_number,
            "phase": state.turn.phase.name,
            "currentInitiative": state.turn.current_initiative,
            "currentFaction": state.turn.current_faction,
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
                "ordersSubmitted": fid in order_manager.locked_factions,
                "orderCount": order_manager.faction_orders.get(fid, None) and 
                             order_manager.faction_orders[fid].total_orders or 0
            }
            for fid, f in state.factions.items()
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
# Phase Management
# ============================================================================

@router.post("/phase/planning", response_model=AdminResponse)
async def start_planning_phase(state: GameState = Depends(get_game_state)):
    """
    Start the planning phase.
    
    Factions can now submit orders.
    """
    state.turn.phase = GamePhase.PLANNING
    reset_order_manager()  # Clear any old orders
    
    return AdminResponse(
        success=True,
        message=f"Planning phase started for turn {state.turn.turn_number}",
        data={"phase": GamePhase.PLANNING.name}
    )


@router.post("/phase/lock-orders", response_model=AdminResponse)
async def lock_all_orders():
    """
    Lock all faction orders.
    
    No more order changes allowed. Prepares for resolution.
    """
    order_manager = get_order_manager()
    
    for faction_id in order_manager.faction_orders.keys():
        order_manager.lock_faction_orders(faction_id)
    
    return AdminResponse(
        success=True,
        message=f"Locked orders for {len(order_manager.locked_factions)} factions",
        data={"lockedFactions": list(order_manager.locked_factions)}
    )


@router.post("/phase/resolution", response_model=AdminResponse)
async def start_resolution_phase(state: GameState = Depends(get_game_state)):
    """
    Start the resolution phase.
    
    This transitions the game from planning to resolution.
    Orders will be processed in the next step.
    """
    if state.turn.phase != GamePhase.PLANNING:
        return AdminResponse(
            success=False,
            message=f"Cannot start resolution from phase {state.turn.phase.name}"
        )
    
    state.turn.phase = GamePhase.RESOLUTION
    
    # Lock all orders
    order_manager = get_order_manager()
    for faction_id in order_manager.faction_orders.keys():
        order_manager.lock_faction_orders(faction_id)
    
    return AdminResponse(
        success=True,
        message="Resolution phase started",
        data={
            "phase": GamePhase.RESOLUTION.name,
            "totalOrders": sum(
                fo.total_orders for fo in order_manager.faction_orders.values()
            )
        }
    )


# ============================================================================
# Turn Resolution
# ============================================================================

@router.post("/resolve-turn", response_model=AdminResponse)
async def resolve_turn(state: GameState = Depends(get_game_state)):
    """
    Resolve the current turn.
    
    This is a placeholder that will eventually:
    1. Process all movement orders (resolving hexside limits)
    2. Detect and resolve combats
    3. Process ranged fire
    4. Process economic actions
    5. Advance to next turn
    
    For now, it just advances the turn number.
    """
    order_manager = get_order_manager()
    order_count = sum(fo.total_orders for fo in order_manager.faction_orders.values())
    
    # Store the turn number before resolution
    old_turn = state.turn.turn_number
    
    # TODO: Actual turn resolution logic here
    # For now, we just log what would happen
    resolution_log = []
    
    # Log movement orders
    for faction_id, orders in order_manager.faction_orders.items():
        faction_name = state.factions.get(faction_id, {})
        if hasattr(faction_name, 'name'):
            faction_name = faction_name.name
        else:
            faction_name = f"Faction {faction_id}"
            
        for mo in orders.movement_orders:
            unit = state.get_unit(mo.unit_id)
            unit_name = unit.name if unit else f"Unit {mo.unit_id}"
            resolution_log.append({
                "type": "movement",
                "faction": faction_name,
                "unit": unit_name,
                "path": mo.path,
                "status": "pending"
            })
        
        for bo in orders.build_unit_orders:
            base = state.get_base(bo.base_id)
            base_name = base.name if base else f"Base {bo.base_id}"
            resolution_log.append({
                "type": "build_unit",
                "faction": faction_name,
                "base": base_name,
                "unitType": bo.unit_type,
                "status": "pending"
            })
    
    # Advance turn
    state.turn.turn_number += 1
    state.turn.phase = GamePhase.PLANNING
    
    # Clear orders for next turn
    reset_order_manager()
    
    return AdminResponse(
        success=True,
        message=f"Turn {old_turn} resolved. Now turn {state.turn.turn_number}.",
        data={
            "previousTurn": old_turn,
            "newTurn": state.turn.turn_number,
            "ordersProcessed": order_count,
            "resolutionLog": resolution_log[:20]  # Limit log size
        }
    )


@router.post("/advance-turn", response_model=AdminResponse)
async def advance_turn(state: GameState = Depends(get_game_state)):
    """
    Simple turn advancement without resolution.
    
    Use this for testing or skipping turns.
    """
    old_turn = state.turn.turn_number
    state.turn.turn_number += 1
    reset_order_manager()
    
    return AdminResponse(
        success=True,
        message=f"Advanced from turn {old_turn} to {state.turn.turn_number}",
        data={"previousTurn": old_turn, "newTurn": state.turn.turn_number}
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

