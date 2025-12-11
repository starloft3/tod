"""
Order endpoints.

Submit and manage orders for units and bases.
Uses the new OrderManager for structured order handling.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from ..dependencies import get_game_state
from tod.core import GameState
from tod.core.order_manager import get_order_manager, OrderManager


router = APIRouter(prefix="/orders", tags=["orders"])


# ============================================================================
# Request Models
# ============================================================================

class MovementOrderRequest(BaseModel):
    """Request to submit a movement order."""
    unitId: int
    path: List[int]  # List of hex IDs to move through
    
    class Config:
        json_schema_extra = {
            "example": {"unitId": 1, "path": [100, 101, 102]}
        }


class RangedfireOrderRequest(BaseModel):
    """Request for ranged fire order."""
    unitId: int
    targetHex: int


class BoardTransportRequest(BaseModel):
    """Request to board a transport."""
    unitId: int
    transportId: int


class BuildBaseRequest(BaseModel):
    """Request for leader to build a base."""
    unitId: int


class BuildUnitRequest(BaseModel):
    """Request to build a unit at a base."""
    baseId: int
    unitType: str
    
    class Config:
        json_schema_extra = {
            "example": {"baseId": 1, "unitType": "Footman"}
        }


class UpgradeBaseRequest(BaseModel):
    """Request to upgrade a base."""
    baseId: int


class HarvestRequest(BaseModel):
    """Request for harvest order."""
    baseId: int


class SendResourcesRequest(BaseModel):
    """Request to send resources between bases."""
    originBase: int
    destinationBase: int
    gold: int = 0
    lumber: int = 0
    oil: int = 0


# ============================================================================
# Response Models
# ============================================================================

class OrderResponse(BaseModel):
    """Standard response for order operations."""
    success: bool
    message: str
    data: Optional[dict] = None


# ============================================================================
# Order Retrieval Endpoints
# ============================================================================

@router.get("")
async def get_all_orders():
    """Get all submitted orders for all factions."""
    order_manager = get_order_manager()
    return order_manager.to_dict()


@router.get("/summary")
async def get_order_summary():
    """Get a summary of all submitted orders."""
    order_manager = get_order_manager()
    return order_manager.get_order_summary()


@router.get("/faction/{faction_id}")
async def get_faction_orders(faction_id: int):
    """Get all orders for a specific faction."""
    order_manager = get_order_manager()
    orders = order_manager.faction_orders.get(faction_id)
    
    if not orders:
        return {
            "factionId": faction_id,
            "totalOrders": 0,
            "orders": {}
        }
    
    return {
        "factionId": faction_id,
        "locked": order_manager.is_faction_locked(faction_id),
        "totalOrders": orders.total_orders,
        "unitOrders": orders.total_unit_orders,
        "baseOrders": orders.total_base_orders,
        "movementOrders": [
            {"unitId": o.unit_id, "path": o.path}
            for o in orders.movement_orders
        ],
        "buildUnitOrders": [
            {"baseId": o.base_id, "unitType": o.unit_type}
            for o in orders.build_unit_orders
        ],
        "upgradeBaseOrders": [
            {"baseId": o.base_id}
            for o in orders.upgrade_base_orders
        ]
    }


# ============================================================================
# Unit Order Submission
# ============================================================================

@router.post("/movement", response_model=OrderResponse)
async def submit_movement_order(
    request: MovementOrderRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """
    Submit a movement order for a unit.
    
    The path is a list of hex IDs the unit should move through.
    The unit will stop if it runs out of movement points or encounters combat.
    """
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_movement(
        faction_id=faction_id,
        unit_id=request.unitId,
        path=request.path,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(
        success=True,
        message=message,
        data={"unitId": request.unitId, "pathLength": len(request.path)}
    )


@router.post("/rangedfire", response_model=OrderResponse)
async def submit_rangedfire_order(
    request: RangedfireOrderRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """Submit a ranged fire order for an interior siege unit."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_rangedfire(
        faction_id=faction_id,
        unit_id=request.unitId,
        target_hex=request.targetHex,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(success=True, message=message)


@router.post("/board-transport", response_model=OrderResponse)
async def submit_board_transport_order(
    request: BoardTransportRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """Submit an order for a unit to board a transport."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_board_transport(
        faction_id=faction_id,
        unit_id=request.unitId,
        transport_id=request.transportId,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(success=True, message=message)


@router.post("/build-base", response_model=OrderResponse)
async def submit_build_base_order(
    request: BuildBaseRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """Submit an order for a leader to build a base."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_build_base(
        faction_id=faction_id,
        unit_id=request.unitId,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(success=True, message=message)


# ============================================================================
# Base Order Submission
# ============================================================================

@router.post("/build-unit", response_model=OrderResponse)
async def submit_build_unit_order(
    request: BuildUnitRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """
    Submit an order to build a unit at a base.
    
    The base must have sufficient resources and meet tier requirements.
    """
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_build_unit(
        faction_id=faction_id,
        base_id=request.baseId,
        unit_type=request.unitType,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(
        success=True,
        message=message,
        data={"baseId": request.baseId, "unitType": request.unitType}
    )


@router.post("/upgrade-base", response_model=OrderResponse)
async def submit_upgrade_base_order(
    request: UpgradeBaseRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """Submit an order to upgrade a base to the next tier."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_upgrade_base(
        faction_id=faction_id,
        base_id=request.baseId,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(success=True, message=message)


@router.post("/harvest", response_model=OrderResponse)
async def submit_harvest_order(
    request: HarvestRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """Submit a harvest order for a base."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_harvest(
        faction_id=faction_id,
        base_id=request.baseId,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(success=True, message=message)


@router.post("/send-resources", response_model=OrderResponse)
async def submit_send_resources_order(
    request: SendResourcesRequest,
    faction_id: int = Query(..., description="Faction ID submitting the order"),
    state: GameState = Depends(get_game_state)
):
    """Submit an order to send resources between bases."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.submit_send_resources(
        faction_id=faction_id,
        origin_base=request.originBase,
        destination_base=request.destinationBase,
        gold=request.gold,
        lumber=request.lumber,
        oil=request.oil,
        state=state
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return OrderResponse(success=True, message=message)


# ============================================================================
# Order Management
# ============================================================================

@router.delete("/movement/{unit_id}", response_model=OrderResponse)
async def cancel_movement_order(
    unit_id: int,
    faction_id: int = Query(..., description="Faction ID"),
):
    """Cancel a movement order for a unit."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.cancel_movement(faction_id, unit_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    
    return OrderResponse(success=True, message=message)


@router.delete("/faction/{faction_id}", response_model=OrderResponse)
async def clear_faction_orders(faction_id: int):
    """Clear all orders for a specific faction."""
    order_manager = get_order_manager()
    
    if order_manager.is_faction_locked(faction_id):
        raise HTTPException(status_code=403, detail=f"Faction {faction_id} orders are locked")
    
    success, message = order_manager.clear_faction_orders(faction_id)
    return OrderResponse(success=True, message=message)


@router.delete("/all", response_model=OrderResponse)
async def clear_all_orders():
    """Clear all orders for all factions."""
    order_manager = get_order_manager()
    success, message = order_manager.clear_all_orders()
    return OrderResponse(success=True, message=message)


# ============================================================================
# Order Locking (for admin/GM use)
# ============================================================================

@router.post("/lock/{faction_id}", response_model=OrderResponse)
async def lock_faction_orders(faction_id: int):
    """Lock a faction's orders (no more changes allowed)."""
    order_manager = get_order_manager()
    success, message = order_manager.lock_faction_orders(faction_id)
    return OrderResponse(success=True, message=message)


@router.post("/unlock/{faction_id}", response_model=OrderResponse)
async def unlock_faction_orders(faction_id: int):
    """Unlock a faction's orders (allow changes again)."""
    order_manager = get_order_manager()
    success, message = order_manager.unlock_faction_orders(faction_id)
    return OrderResponse(success=True, message=message)
