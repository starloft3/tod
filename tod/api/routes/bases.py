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


def validate_base_can_receive_orders(base, state: GameState) -> None:
    """
    Validate that a base can receive orders on the current turn.
    
    A base can only receive orders if its faction is part of the current initiative.
    Raises HTTPException if validation fails.
    """
    base_faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
    base_faction = state.get_faction(base_faction_id)
    
    if not base_faction:
        raise HTTPException(status_code=400, detail=f"Base faction not found")
    
    current_initiative = state.turn.current_initiative
    
    if base_faction.initiative != current_initiative:
        raise HTTPException(
            status_code=403,
            detail=f"Cannot issue orders to {base.name}: faction {base_faction.name} "
                   f"(initiative {base_faction.initiative}) is not active. "
                   f"Current initiative: {current_initiative}"
        )


def base_to_summary(base) -> BaseSummary:
    """Convert Base model to BaseSummary schema."""
    return BaseSummary(
        id=base.id,
        name=base.name,
        location=base.location,
        factionId=base.faction.value,
        tier=base.tier,
        gold=base.gold,
        lumber=base.lumber,
        oil=base.oil
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
        actions=base.actions,
        expansions=base.expansions
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


# =============================================================================
# BASE ACTIONS / ORDERS
# =============================================================================

@router.get("/{base_id}/orders")
async def get_base_orders(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all pending orders for a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    orders = state.get_base_pending_orders(base_id)
    pending_resources = state.get_pending_resources(base_id)
    in_combat = state.base_in_combat(base_id)
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "tier": base.tier,
        "inCombat": in_combat,
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": state.get_base_actions_remaining(base_id),
        "orders": orders,
        "pendingResources": pending_resources
    }


@router.get("/{base_id}/resources/effective")
async def get_base_effective_resources(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get base resources including pending changes from queued orders."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    resources = state.get_effective_resources(base_id)
    resources['baseId'] = base_id
    resources['baseName'] = base.name
    resources['actionsUsed'] = state.get_base_actions_used(base_id)
    resources['actionsRemaining'] = state.get_base_actions_remaining(base_id)
    
    return resources


@router.get("/{base_id}/harvest/preview")
async def preview_harvest(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Preview what a Harvest action would yield without queuing it."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    yield_data = state.calculate_harvest_yield(base_id)
    can_harvest, reason = state.can_queue_action(base_id, 'harvest')
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "canHarvest": can_harvest,
        "reason": reason if not can_harvest else None,
        "expectedYield": yield_data
    }


@router.post("/{base_id}/orders/harvest")
async def queue_harvest(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """
    DEPRECATED: Harvest is now automatic.
    
    Harvest actions are automatically applied to all bases during the
    base action resolution phase. This endpoint is kept for backwards
    compatibility but does nothing.
    """
    return {
        "deprecated": True,
        "message": "Harvest is now automatic. Resources are collected during turn resolution.",
        "success": True
    }
    
    # Legacy code below - kept for reference but unreachable
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    result = state.queue_harvest_order(base_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    # Return full order state
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "order": result['order'],
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


@router.get("/{base_id}/expand/validate/{target_hex}")
async def validate_expand(
    base_id: int,
    target_hex: int,
    state: GameState = Depends(get_game_state)
):
    """Validate if an expansion can be built at a target hex."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    is_valid, error, details = state.validate_expand(base_id, target_hex)
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "targetHex": target_hex,
        "canExpand": is_valid,
        "reason": error if not is_valid else None,
        "expansionType": details.get('expansion_type'),
        "traceType": details.get('trace_type'),
        "tracePath": details.get('trace_path'),
        "cost": details.get('cost')
    }


@router.get("/{base_id}/expand/targets")
async def get_expandable_hexes(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all hexes where this base can build expansions."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Find all valid expansion targets
    valid_targets = []
    
    # BFS from base location to find all reachable hexes within tier range
    from collections import deque
    
    faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
    max_dist = base.tier
    start_hex = base.location
    
    # Search for land trace targets
    for trace_hexsides, trace_name in [
        (state.LAND_TRACE_HEXSIDES, 'land'),
        (state.SEA_TRACE_HEXSIDES, 'sea')
    ]:
        is_land_trace = (trace_name == 'land')
        queue = deque([(start_hex, 0)])
        visited = {start_hex}
        
        while queue:
            current, dist = queue.popleft()
            
            # Check if this hex is a valid expansion target
            if current != start_hex:
                exp_type = state.get_expansion_type_for_hex(current)
                if exp_type:
                    # Check other requirements
                    if not state.base_at_hex(current) and not state.expansion_at_hex(current):
                        if state.is_hex_visible_to_faction(current, faction_id):
                            enemies = state.enemies_at_hex(current, faction_id)
                            if not enemies:
                                # Check effective resources
                                effective = state.get_effective_resources(base_id)
                                can_afford = effective and effective['effective']['lumber'] >= 2
                                
                                valid_targets.append({
                                    "hexId": current,
                                    "expansionType": exp_type,
                                    "traceType": trace_name,
                                    "distance": dist,
                                    "canAfford": can_afford
                                })
            
            # Don't expand beyond max distance
            if dist >= max_dist:
                continue
            
            # Explore adjacent hexes
            for neighbor in state.adjacent_hexes(current):
                if neighbor in visited:
                    continue
                
                hexside_terrain = state.get_hexside_terrain(current, neighbor)
                
                # For land traces, roads also allow passage
                is_valid_terrain = hexside_terrain in trace_hexsides
                has_road = is_land_trace and state.has_road_between(current, neighbor)
                
                if is_valid_terrain or has_road:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
    
    # Deduplicate (a hex might be reachable by both land and sea)
    seen_hexes = set()
    unique_targets = []
    for target in valid_targets:
        if target['hexId'] not in seen_hexes:
            seen_hexes.add(target['hexId'])
            unique_targets.append(target)
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "tier": base.tier,
        "maxRange": base.tier,
        "lumber": state.get_effective_resources(base_id)['effective']['lumber'],
        "cost": 2,
        "validTargets": unique_targets,
        "totalTargets": len(unique_targets)
    }


@router.post("/{base_id}/orders/expand/{target_hex}")
async def queue_expand(
    base_id: int,
    target_hex: int,
    state: GameState = Depends(get_game_state)
):
    """Queue an Expand action for a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    result = state.queue_expand_order(base_id, target_hex)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "order": result['order'],
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


# =============================================================================
# COMMERCE ACTION
# =============================================================================

@router.get("/{base_id}/commerce/options")
async def get_commerce_options(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get available commerce conversion options for a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    options = state.get_commerce_options(base_id)
    options['baseId'] = base_id
    options['baseName'] = base.name
    
    return options


@router.post("/{base_id}/orders/commerce")
async def queue_commerce(
    base_id: int,
    from_resource: str = Query(..., alias="from", description="Resource to spend (gold, lumber, oil)"),
    to_resource: str = Query(..., alias="to", description="Resource to gain (gold, lumber, oil)"),
    state: GameState = Depends(get_game_state)
):
    """Queue a Commerce action for a base. Converts 2 of one resource into 1 of another."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    result = state.queue_commerce_order(base_id, from_resource, to_resource)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "order": result['order'],
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


# =============================================================================
# UPGRADE BASE ACTION
# =============================================================================

@router.get("/{base_id}/upgrade/info")
async def get_upgrade_info(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get detailed upgrade information for a base including costs and requirements."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    info = state.get_upgrade_info(base_id)
    info['baseId'] = base_id
    info['baseName'] = base.name
    
    return info


@router.post("/{base_id}/orders/upgrade")
async def queue_upgrade(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Queue an Upgrade Base action."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    result = state.queue_upgrade_order(base_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "order": result['order'],
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


# =============================================================================
# REST UNIT ACTION
# =============================================================================

@router.get("/{base_id}/rest/units")
async def get_restable_units(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get units at base that can potentially be rested."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    units = state.get_restable_units_at_base(base_id)
    effective = state.get_effective_resources(base_id)
    can_afford = effective['effective']['gold'] >= 2
    
    # Check if rest action is already queued
    already_queued = state.has_pending_action_type(base_id, 'rest')
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "units": units,
        "canAfford": can_afford,
        "alreadyQueued": already_queued,
        "effectiveGold": effective['effective']['gold'],
        "cost": 2
    }


@router.get("/{base_id}/rest/validate/{unit_id}")
async def validate_rest_unit(
    base_id: int,
    unit_id: int,
    state: GameState = Depends(get_game_state)
):
    """Validate if a specific unit can be rested at this base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    is_valid, error, info = state.validate_rest_unit(base_id, unit_id)
    
    return {
        "baseId": base_id,
        "unitId": unit_id,
        "canRest": is_valid,
        "reason": error if not is_valid else "",
        "info": info
    }


@router.post("/{base_id}/orders/rest/{unit_id}")
async def queue_rest_unit(
    base_id: int,
    unit_id: int,
    state: GameState = Depends(get_game_state)
):
    """Queue a Rest Unit action."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    result = state.queue_rest_unit_order(base_id, unit_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "order": result['order'],
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


# =============================================================================
# BUILD UNIT ACTION
# =============================================================================

@router.get("/{base_id}/build/units")
async def get_buildable_units(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all units that can be built at this base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    units = state.get_buildable_units(base_id)
    
    # Get faction food info
    faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
    food_status = state.faction_food_status(faction_id)
    pending_builds = state.get_pending_build_count(faction_id)
    
    # Check if already have a build order queued
    already_queued = state.has_pending_action_type(base_id, 'build_unit')
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "baseTier": base.tier,
        "units": units,
        "alreadyQueued": already_queued,
        "food": {
            "limit": food_status['food_limit'],
            "unitCount": food_status['unit_count'],
            "surplus": food_status['food_surplus'],
            "pendingBuilds": pending_builds,
            "effectiveSurplus": food_status['food_surplus'] - pending_builds,
            "canBuild": (food_status['food_surplus'] - pending_builds) > 0
        }
    }


@router.get("/{base_id}/build/validate/{unit_name}")
async def validate_build_unit(
    base_id: int,
    unit_name: str,
    state: GameState = Depends(get_game_state)
):
    """Validate if a specific unit can be built at this base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # URL decode the unit name (spaces become %20 or +)
    import urllib.parse
    decoded_name = urllib.parse.unquote(unit_name)
    
    is_valid, error, info = state.validate_build_unit(base_id, decoded_name)
    
    return {
        "baseId": base_id,
        "unitName": decoded_name,
        "canBuild": is_valid,
        "reason": error if not is_valid else "",
        "info": info
    }


@router.post("/{base_id}/orders/build/{unit_name}")
async def queue_build_unit(
    base_id: int,
    unit_name: str,
    state: GameState = Depends(get_game_state)
):
    """Queue a Build Unit action."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    # URL decode the unit name
    import urllib.parse
    decoded_name = urllib.parse.unquote(unit_name)
    
    result = state.queue_build_unit_order(base_id, decoded_name)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "order": result['order'],
        "actionsUsed": state.get_base_actions_used(base_id),
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


@router.delete("/{base_id}/orders/last")
async def cancel_last_order(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Cancel the last queued order for a base (LIFO)."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    result = state.cancel_last_base_order(base_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "cancelledOrder": result['cancelled_order'],
        "actionsRemaining": result['actions_remaining'],
        "pendingResources": pending_resources,
        "remainingOrders": state.get_base_pending_orders(base_id)
    }


@router.delete("/{base_id}/orders")
async def clear_base_orders(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Clear all pending orders for a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    count = state.clear_base_orders(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "ordersCleared": count,
        "actionsRemaining": state.get_base_actions_remaining(base_id)
    }


# ==================== Caravan Establishment ====================

@router.get("/{base_id}/caravan/targets")
async def get_caravan_targets(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """
    Get all valid destination bases for a caravan from this base.
    Returns bases that share the same initiative.
    """
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
    faction = state.get_faction(faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    
    my_initiative = faction.initiative
    
    # Find all bases with same initiative (excluding self)
    targets = []
    for other_base in state.bases.values():
        if other_base.id == base_id:
            continue
        
        other_faction_id = other_base.faction.value if hasattr(other_base.faction, 'value') else other_base.faction
        other_faction = state.get_faction(other_faction_id)
        if other_faction and other_faction.initiative == my_initiative:
            # Check if caravan already exists
            has_caravan = state.caravan_exists_between(base_id, other_base.id)
            
            # Check if sea caravan is possible
            can_sea = state.can_establish_sea_caravan(base_id, other_base.id)
            
            targets.append({
                "baseId": other_base.id,
                "baseName": other_base.name,
                "location": other_base.location,
                "factionId": other_faction_id,
                "hasExistingCaravan": has_caravan,
                "canSeaCaravan": can_sea
            })
    
    return {
        "originBaseId": base_id,
        "originBaseName": base.name,
        "initiative": my_initiative,
        "targets": targets
    }


@router.get("/{base_id}/caravan/next-hexes")
async def get_valid_next_caravan_hexes(
    base_id: int,
    current_path: str = Query(..., description="Comma-separated hex IDs of current path"),
    is_sea: Optional[bool] = Query(None, alias="isSea", description="Is this a sea caravan? null = both types"),
    dest_base_id: Optional[int] = Query(None, alias="destBaseId", description="Target base ID if known"),
    state: GameState = Depends(get_game_state)
):
    """
    Get valid next hexes for caravan path tracing.
    Used for real-time path building in the UI.
    
    If is_sea is None, returns both land and sea options (for first step when type undecided).
    """
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Parse current path
    try:
        path = [int(h.strip()) for h in current_path.split(",") if h.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path format")
    
    if not path:
        # Start from base
        path = [base.location]
    
    # If is_sea is None (undecided), get both land and sea options
    if is_sea is None:
        land_hexes = state.get_valid_next_caravan_hexes(base_id, path, False, dest_base_id)
        sea_hexes = state.get_valid_next_caravan_hexes(base_id, path, True, dest_base_id)
        
        # Merge and mark terrain type
        hex_map = {}
        for h in land_hexes:
            hex_map[h['hex_id']] = {**h, 'terrain_type': 'land'}
        for h in sea_hexes:
            if h['hex_id'] in hex_map:
                hex_map[h['hex_id']]['terrain_type'] = 'both'
            else:
                hex_map[h['hex_id']] = {**h, 'terrain_type': 'sea'}
        
        valid_hexes = list(hex_map.values())
    else:
        valid_hexes = state.get_valid_next_caravan_hexes(base_id, path, is_sea, dest_base_id)
        terrain_type = 'sea' if is_sea else 'land'
        for h in valid_hexes:
            h['terrain_type'] = terrain_type
    
    # Calculate current cost tier (use land cost if undecided)
    from tod.core.models.caravan import get_caravan_cost
    current_cost = get_caravan_cost(len(path), is_sea or False)
    
    return {
        "currentPath": path,
        "pathLength": len(path),
        "currentCost": current_cost,
        "validNextHexes": valid_hexes
    }


@router.post("/{base_id}/caravan/validate")
async def validate_caravan_path(
    base_id: int,
    dest_base_id: int = Query(..., alias="destBaseId"),
    path: str = Query(..., description="Comma-separated hex IDs"),
    is_sea: bool = Query(False, alias="isSea"),
    state: GameState = Depends(get_game_state)
):
    """Validate a complete caravan path before queueing."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Parse path
    try:
        path_list = [int(h.strip()) for h in path.split(",") if h.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path format")
    
    validation = state.validate_caravan_path(base_id, dest_base_id, path_list, is_sea)
    
    return {
        "valid": validation['valid'],
        "error": validation.get('error', ''),
        "cost": validation.get('cost', {'lumber': 0, 'oil': 0}),
        "pathLength": len(path_list)
    }


@router.post("/{base_id}/orders/caravan")
async def queue_establish_caravan(
    base_id: int,
    dest_base_id: int = Query(..., alias="destBaseId"),
    path: str = Query(..., description="Comma-separated hex IDs"),
    is_sea: bool = Query(False, alias="isSea"),
    state: GameState = Depends(get_game_state)
):
    """Queue an order to establish a caravan."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    # Parse path
    try:
        path_list = [int(h.strip()) for h in path.split(",") if h.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path format")
    
    result = state.queue_establish_caravan_order(base_id, dest_base_id, path_list, is_sea)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    dest_base = state.get_base(dest_base_id)
    dest_name = dest_base.name if dest_base else f"Base {dest_base_id}"
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "destBaseId": dest_base_id,
        "destBaseName": dest_name,
        "pathLength": len(path_list),
        "cost": result['cost'],
        "isSea": is_sea,
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }


@router.get("/{base_id}/caravans")
async def get_base_caravans(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all caravans connected to a base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    caravans = state.get_caravans_for_base(base_id)
    
    result = []
    for caravan in caravans:
        origin_base = state.get_base(caravan.origin_base_id)
        dest_base = state.get_base(caravan.destination_base_id)
        
        result.append({
            "id": caravan.id,
            "originBaseId": caravan.origin_base_id,
            "originBaseName": origin_base.name if origin_base else "Unknown",
            "destBaseId": caravan.destination_base_id,
            "destBaseName": dest_base.name if dest_base else "Unknown",
            "pathLength": len(caravan.path),
            "path": caravan.path,
            "terrainType": caravan.terrain_type.value,
            "initiative": caravan.initiative
        })
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "caravans": result
    }


# ==================== Send Resources ====================

@router.get("/{base_id}/send/destinations")
async def get_send_destinations(
    base_id: int,
    state: GameState = Depends(get_game_state)
):
    """Get all bases that can receive resources via caravan from this base."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    destinations = state.get_send_resource_destinations(base_id)
    can_send, reasons = state.can_send_resources(base_id)
    
    # Get effective resources
    effective = state.get_effective_resources(base_id)
    
    return {
        "baseId": base_id,
        "baseName": base.name,
        "canSend": can_send,
        "reasons": reasons,
        "destinations": destinations,
        "availableResources": effective['effective'] if effective else {'gold': 0, 'lumber': 0, 'oil': 0}
    }


@router.post("/{base_id}/orders/send")
async def queue_send_resources(
    base_id: int,
    dest_base_id: int = Query(..., alias="destBaseId"),
    gold: int = Query(0, ge=0),
    lumber: int = Query(0, ge=0),
    oil: int = Query(0, ge=0),
    state: GameState = Depends(get_game_state)
):
    """Queue an order to send resources via caravan."""
    base = state.get_base(base_id)
    if not base:
        raise HTTPException(status_code=404, detail=f"Base {base_id} not found")
    
    # Validate initiative
    validate_base_can_receive_orders(base, state)
    
    result = state.queue_send_resources_order(base_id, dest_base_id, gold, lumber, oil)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    dest_base = state.get_base(dest_base_id)
    dest_name = dest_base.name if dest_base else f"Base {dest_base_id}"
    
    pending_resources = state.get_pending_resources(base_id)
    
    return {
        "success": True,
        "baseId": base_id,
        "baseName": base.name,
        "destBaseId": dest_base_id,
        "destBaseName": dest_name,
        "sent": {"gold": gold, "lumber": lumber, "oil": oil},
        "pendingResources": pending_resources,
        "allOrders": state.get_base_pending_orders(base_id)
    }

