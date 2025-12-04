"""
Order endpoints.

Submit and manage orders for units and economic actions.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..schemas import (
    OrderCreate, SpecialOrderCreate, EconomicActionCreate, APIResponse
)
from ..dependencies import get_game_state
from tod.core import GameState
from tod.core.game_state import Order, SpecialOrder, EconomicAction

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
async def list_orders(state: GameState = Depends(get_game_state)):
    """Get all pending orders."""
    return {
        "movement": [
            {"unitId": o.unit_id, "orderType": o.order_type, 
             "target": o.target, "secondary": o.secondary}
            for o in state.orders
        ],
        "special": [
            {"factionId": o.faction_id, "orderType": o.order_type,
             "source": o.source, "target": o.target, "secondary": o.secondary}
            for o in state.special_orders
        ],
        "economic": [
            {"factionId": o.faction_id, "actionType": o.action_type,
             "baseId": o.base_id, "target": o.target, "quantity": o.quantity}
            for o in state.economic_actions
        ],
        "totals": {
            "movement": len(state.orders),
            "special": len(state.special_orders),
            "economic": len(state.economic_actions)
        }
    }


@router.post("/movement", response_model=APIResponse)
async def submit_movement_order(
    order: OrderCreate,
    state: GameState = Depends(get_game_state)
):
    """
    Submit a movement order for a unit.
    
    Order types:
    - M: Move
    - A: Attack
    - H: Hold
    - R: Retreat
    """
    # Validate unit exists
    unit = state.get_unit(order.unitId)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit {order.unitId} not found")
    
    if not unit.alive:
        raise HTTPException(status_code=400, detail=f"Unit {order.unitId} is dead")
    
    # Validate target hex exists
    if order.target not in state.hexes:
        raise HTTPException(status_code=400, detail=f"Target hex {order.target} not found")
    
    # Create and add order
    new_order = Order(
        unit_id=order.unitId,
        order_type=order.orderType,
        target=order.target,
        secondary=order.secondary
    )
    state.orders.append(new_order)
    
    return APIResponse(
        success=True,
        message=f"Movement order submitted for unit {unit.name}",
        data={"unitId": order.unitId, "target": order.target}
    )


@router.post("/special", response_model=APIResponse)
async def submit_special_order(
    order: SpecialOrderCreate,
    state: GameState = Depends(get_game_state)
):
    """Submit a special order (spell, ability, etc.)."""
    # Validate faction
    faction = state.get_faction(order.factionId)
    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction {order.factionId} not found")
    
    new_order = SpecialOrder(
        faction_id=order.factionId,
        order_type=order.orderType,
        source=order.source,
        target=order.target,
        secondary=order.secondary
    )
    state.special_orders.append(new_order)
    
    return APIResponse(
        success=True,
        message=f"Special order '{order.orderType}' submitted",
        data={"factionId": order.factionId, "orderType": order.orderType}
    )


@router.post("/economic", response_model=APIResponse)
async def submit_economic_action(
    action: EconomicActionCreate,
    state: GameState = Depends(get_game_state)
):
    """
    Submit an economic action.
    
    Action types:
    - BUILD: Build a unit
    - UPGRADE: Upgrade a base
    - EXPAND: Build a new structure
    """
    # Validate faction and base
    faction = state.get_faction(action.factionId)
    if not faction:
        raise HTTPException(status_code=404, detail=f"Faction {action.factionId} not found")
    
    base = state.get_base(action.baseId)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {action.baseId} not found")
    
    if base.faction.value != action.factionId:
        raise HTTPException(
            status_code=403, 
            detail=f"Base {action.baseId} does not belong to faction {action.factionId}"
        )
    
    new_action = EconomicAction(
        faction_id=action.factionId,
        action_type=action.actionType,
        base_id=action.baseId,
        target=action.target,
        quantity=action.quantity
    )
    state.economic_actions.append(new_action)
    
    return APIResponse(
        success=True,
        message=f"Economic action '{action.actionType}' submitted at {base.name}",
        data={"baseId": action.baseId, "action": action.actionType}
    )


@router.delete("/movement/{unit_id}", response_model=APIResponse)
async def cancel_movement_order(
    unit_id: int,
    state: GameState = Depends(get_game_state)
):
    """Cancel all movement orders for a unit."""
    initial_count = len(state.orders)
    state.orders = [o for o in state.orders if o.unit_id != unit_id]
    removed = initial_count - len(state.orders)
    
    if removed == 0:
        raise HTTPException(status_code=404, detail=f"No orders found for unit {unit_id}")
    
    return APIResponse(
        success=True,
        message=f"Cancelled {removed} order(s) for unit {unit_id}"
    )


@router.delete("/all", response_model=APIResponse)
async def clear_all_orders(
    state: GameState = Depends(get_game_state),
    faction_id: int = None
):
    """
    Clear all orders. 
    If faction_id is provided, only clear orders for that faction.
    """
    if faction_id is not None:
        # Clear orders for specific faction
        state.orders = [o for o in state.orders 
                       if state.get_unit(o.unit_id).faction.value != faction_id]
        state.special_orders = [o for o in state.special_orders 
                               if o.faction_id != faction_id]
        state.economic_actions = [a for a in state.economic_actions 
                                 if a.faction_id != faction_id]
        return APIResponse(success=True, message=f"Cleared orders for faction {faction_id}")
    else:
        state.orders.clear()
        state.special_orders.clear()
        state.economic_actions.clear()
        return APIResponse(success=True, message="Cleared all orders")

