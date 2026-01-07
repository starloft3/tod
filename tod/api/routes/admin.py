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


@router.get("/combats")
async def get_active_combats(state: GameState = Depends(get_game_state)):
    """Get all active combat hexes with details."""
    from tod.core.combat_manager import get_combat_manager, init_combat_manager
    
    combat_mgr = init_combat_manager(state)
    combat_mgr.detect_combats()  # Refresh combat detection
    
    combats = []
    for hex_id, combat in combat_mgr.active_combats.items():
        units_at_hex = state.units_at_hex(hex_id)
        
        # Group units by initiative
        by_initiative = {}
        for unit in units_at_hex:
            faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            faction = state.factions.get(faction_id)
            init = faction.initiative if faction else -1
            
            if init not in by_initiative:
                by_initiative[init] = []
            by_initiative[init].append({
                "id": unit.id,
                "name": unit.name,
                "hp": unit.hp,
                "maxHp": unit.max_hp,
                "faction": faction.name if faction else "Unknown",
            })
        
        combats.append({
            "hexId": hex_id,
            "isNew": combat.is_new,
            "roundFought": combat.round_fought_this_alignment,
            "initiatives": list(combat.participating_initiatives),
            "lowestHorde": combat.lowest_horde_initiative,
            "lowestAlliance": combat.lowest_alliance_initiative,
            "unitsByInitiative": by_initiative,
            "totalUnits": len(units_at_hex),
        })
    
    return {
        "timestamp": datetime.now().isoformat(),
        "activeCombats": len(combats),
        "combats": combats
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
    
    # Build combat results summary
    combat_summaries = []
    for cr in result.combat_results:
        combat_summaries.append({
            "hexId": cr.hex_id,
            "wasNewCombat": cr.was_new_combat,
            "totalAttacks": cr.total_attacks,
            "totalDamage": cr.total_damage,
            "unitsKilled": cr.units_killed,
            "combatEnded": cr.combat_ended,
        })
    
    return AdminResponse(
        success=result.success,
        message=result.message,
        data={
            "previousInitiative": old_initiative,
            "factions": faction_names,
            "movementsApplied": result.movements_applied,
            "combatsResolved": result.combats_resolved,
            "unitsKilled": result.units_killed,
            "combatResults": combat_summaries,
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


# ============================================================================
# Save/Load System
# ============================================================================

class SaveRequest(BaseModel):
    """Request body for saving a game."""
    name: str
    notes: str = ""

class LoadRequest(BaseModel):
    """Request body for loading a game."""
    name: str


@router.get("/saves")
async def list_saves():
    """
    List all available save files with metadata.
    
    Returns saves sorted by creation time (newest first).
    """
    from tod.core.save_manager import get_save_manager
    
    save_manager = get_save_manager()
    saves = save_manager.list_saves()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(saves),
        "saves": saves
    }


@router.get("/saves/{save_name}")
async def get_save_info(save_name: str):
    """
    Get metadata for a specific save without loading it.
    """
    from tod.core.save_manager import get_save_manager
    
    save_manager = get_save_manager()
    metadata = save_manager.get_save_metadata(save_name)
    
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Save '{save_name}' not found")
    
    return metadata


@router.post("/save", response_model=AdminResponse)
async def save_game(
    request: SaveRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Save the current game state to a file.
    
    Args:
        name: A name for the save file (will be sanitized for filesystem)
        notes: Optional notes/description for the save
        
    Returns:
        Success status and save metadata
    """
    from tod.core.save_manager import get_save_manager
    
    if not request.name or not request.name.strip():
        return AdminResponse(
            success=False,
            message="Save name is required"
        )
    
    save_manager = get_save_manager()
    result = save_manager.save_game(state, request.name.strip(), request.notes.strip())
    
    return AdminResponse(
        success=result['success'],
        message=result['message'],
        data=result.get('metadata')
    )


@router.post("/load", response_model=AdminResponse)
async def load_game(
    request: LoadRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Load a saved game, replacing current game state.
    
    Args:
        name: Name of the save to load
        
    Returns:
        Success status and loaded save metadata
    """
    from tod.core.save_manager import get_save_manager
    
    if not request.name or not request.name.strip():
        return AdminResponse(
            success=False,
            message="Save name is required"
        )
    
    # Reset order manager before loading
    reset_order_manager()
    
    save_manager = get_save_manager()
    result = save_manager.load_game(state, request.name.strip())
    
    return AdminResponse(
        success=result['success'],
        message=result['message'],
        data=result.get('metadata')
    )


@router.delete("/saves/{save_name}", response_model=AdminResponse)
async def delete_save(save_name: str):
    """
    Delete a save file.
    
    Args:
        save_name: Name of the save to delete
    """
    from tod.core.save_manager import get_save_manager
    
    save_manager = get_save_manager()
    result = save_manager.delete_save(save_name)
    
    return AdminResponse(
        success=result['success'],
        message=result['message']
    )


@router.post("/quicksave", response_model=AdminResponse)
async def quicksave(state: GameState = Depends(get_game_state)):
    """
    Quick save with auto-generated name based on current turn.
    
    Creates a save named like "Quicksave_Horde_R1_Init4"
    """
    from tod.core.save_manager import get_save_manager
    
    # Generate automatic name
    name = f"Quicksave_{state.turn.round_side.value}_R{state.turn.round_number}_Init{state.turn.current_initiative}"
    
    save_manager = get_save_manager()
    result = save_manager.save_game(state, name, "Auto-generated quicksave")
    
    return AdminResponse(
        success=result['success'],
        message=result['message'],
        data=result.get('metadata')
    )


# ============================================================================
# Configuration Management
# ============================================================================

class ConfigUpdateRequest(BaseModel):
    """Request body for updating a config value."""
    key: str
    value: str  # Always passed as string, converted to appropriate type


@router.get("/config")
async def get_config():
    """
    Get the complete game configuration.
    
    Returns all config values organized by section.
    """
    from tod.core.game_config import get_game_config
    
    config = get_game_config()
    return {
        "timestamp": datetime.now().isoformat(),
        "config": config.to_dict(),
        "flat": config.to_flat_dict()
    }


@router.get("/config/{section}")
async def get_config_section(section: str):
    """
    Get a specific configuration section.
    
    Valid sections: combat, economic, caravan, movement, debug
    """
    from tod.core.game_config import get_game_config
    
    config = get_game_config()
    section_obj = getattr(config, section, None)
    
    if section_obj is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Unknown config section: {section}. Valid: combat, economic, caravan, movement, debug"
        )
    
    from dataclasses import asdict
    return {
        "section": section,
        "values": asdict(section_obj)
    }


@router.put("/config", response_model=AdminResponse)
async def update_config(request: ConfigUpdateRequest):
    """
    Update a single config value.
    
    Key format: 'section.name' (e.g., 'combat.min_combat_roll')
    Value is automatically converted to the appropriate type.
    """
    from tod.core.game_config import get_game_config
    
    config = get_game_config()
    
    try:
        old_value = config.get_value(request.key)
        config.set_value(request.key, request.value)
        new_value = config.get_value(request.key)
        
        return AdminResponse(
            success=True,
            message=f"Updated {request.key}: {old_value} → {new_value}",
            data={
                "key": request.key,
                "oldValue": old_value,
                "newValue": new_value
            }
        )
    except ValueError as e:
        return AdminResponse(
            success=False,
            message=str(e)
        )


@router.post("/config/reset", response_model=AdminResponse)
async def reset_config():
    """Reset all config values to defaults."""
    from tod.core.game_config import get_game_config
    
    config = get_game_config()
    config.reset_to_defaults()
    
    return AdminResponse(
        success=True,
        message="Configuration reset to defaults",
        data=config.to_dict()
    )


@router.post("/config/save", response_model=AdminResponse)
async def save_config():
    """Save current configuration to file for persistence across restarts."""
    from tod.core.game_config import get_game_config
    
    config = get_game_config()
    result = config.save_to_file()
    
    return AdminResponse(
        success=result['success'],
        message=f"Config saved to {result.get('path', 'unknown')}" if result['success'] else result.get('error', 'Unknown error')
    )


@router.post("/config/load", response_model=AdminResponse)
async def load_config():
    """Load configuration from file."""
    from tod.core.game_config import get_game_config
    
    config = get_game_config()
    result = config.load_from_file()
    
    return AdminResponse(
        success=result['success'],
        message=f"Config loaded from {result.get('path', 'unknown')}" if result['success'] else result.get('error', 'Unknown error'),
        data=config.to_dict() if result['success'] else None
    )


# ============================================================================
# Object Manipulation - Units
# ============================================================================

class SpawnUnitRequest(BaseModel):
    """Request body for spawning a unit."""
    unit_name: str          # Unit type name (e.g., "Grunt", "Footman")
    faction_id: int         # Faction ID to own the unit
    hex_id: int             # Location to spawn at
    hp: Optional[int] = None  # Starting HP (defaults to max)
    tier: int = 0           # Veterancy tier (0-4)

class ModifyUnitRequest(BaseModel):
    """Request body for modifying a unit."""
    hp: Optional[int] = None
    location: Optional[int] = None
    faction_id: Optional[int] = None
    tier: Optional[int] = None
    alive: Optional[bool] = None


@router.post("/debug/units/spawn", response_model=AdminResponse)
async def spawn_unit(
    request: SpawnUnitRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Spawn a new unit at a specified location.
    
    The unit will be created with stats from the unitstats table.
    """
    from tod.core.models import Unit, FactionId, UnitCategory, UnitType
    
    # Validate faction exists
    faction = state.get_faction(request.faction_id)
    if not faction:
        return AdminResponse(
            success=False,
            message=f"Faction {request.faction_id} not found"
        )
    
    # Validate hex exists
    hex_obj = state.get_hex(request.hex_id)
    if not hex_obj:
        return AdminResponse(
            success=False,
            message=f"Hex {request.hex_id} not found"
        )
    
    # Get unit stats
    stats = state.get_unit_stats(request.unit_name)
    if not stats:
        # List available unit types
        available = list(state.unit_stats.keys()) if hasattr(state, 'unit_stats') else []
        return AdminResponse(
            success=False,
            message=f"Unknown unit type '{request.unit_name}'",
            data={"available_types": available[:20]}  # First 20
        )
    
    # Generate new unit ID (max existing + 1)
    new_id = max(state.units.keys()) + 1 if state.units else 0
    
    # Create the unit
    new_unit = Unit(
        id=new_id,
        name=stats.name,
        faction=FactionId(request.faction_id),
        max_hp=stats.max_hp,
        combat=stats.combat,
        category=stats.category,
        unit_type=stats.unit_type,
        light_armor_max=stats.light_armor,
        heavy_armor=stats.heavy_armor,
        natural_armor=stats.natural_armor,
        movement_max=stats.movement,
        vision=stats.vision,
        stealth=stats.stealth,
        hp=request.hp if request.hp is not None else stats.max_hp,
        location=request.hex_id,
        alive=True,
        tier=min(4, max(0, request.tier)),
    )
    
    # Add to game state
    state.units[new_id] = new_unit
    
    # Recalculate vision for the faction
    from tod.core.vision import compute_visible_hexes
    fid = request.faction_id
    state.visible_hexes[fid] = compute_visible_hexes(state, fid)
    
    return AdminResponse(
        success=True,
        message=f"Spawned {stats.name} (ID: {new_id}) at hex {request.hex_id} for {faction.name}",
        data={
            "unit_id": new_id,
            "unit_name": stats.name,
            "faction": faction.name,
            "location": request.hex_id,
            "hp": new_unit.hp,
            "max_hp": new_unit.max_hp,
            "tier": new_unit.tier
        }
    )


@router.put("/debug/units/{unit_id}", response_model=AdminResponse)
async def modify_unit(
    unit_id: int,
    request: ModifyUnitRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Modify an existing unit's properties.
    
    Only specified fields will be updated.
    """
    from tod.core.models import FactionId
    
    unit = state.get_unit(unit_id)
    if not unit:
        return AdminResponse(
            success=False,
            message=f"Unit {unit_id} not found"
        )
    
    changes = []
    old_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
    
    if request.hp is not None:
        old_hp = unit.hp
        unit.hp = max(0, min(request.hp, unit.max_hp + unit.tier))  # Clamp to 0-effective_max
        if unit.hp == 0:
            unit.alive = False
        changes.append(f"HP: {old_hp} → {unit.hp}")
    
    if request.location is not None:
        hex_obj = state.get_hex(request.location)
        if not hex_obj:
            return AdminResponse(
                success=False,
                message=f"Hex {request.location} not found"
            )
        old_loc = unit.location
        unit.previous_location = unit.location
        unit.location = request.location
        changes.append(f"Location: {old_loc} → {request.location}")
    
    if request.faction_id is not None:
        faction = state.get_faction(request.faction_id)
        if not faction:
            return AdminResponse(
                success=False,
                message=f"Faction {request.faction_id} not found"
            )
        old_faction_name = state.get_faction(old_faction).name if state.get_faction(old_faction) else str(old_faction)
        unit.faction = FactionId(request.faction_id)
        changes.append(f"Faction: {old_faction_name} → {faction.name}")
        # Recalculate vision for both factions
        from tod.core.vision import compute_visible_hexes
        state.visible_hexes[old_faction] = compute_visible_hexes(state, old_faction)
        state.visible_hexes[request.faction_id] = compute_visible_hexes(state, request.faction_id)
    
    if request.tier is not None:
        old_tier = unit.tier
        unit.tier = max(0, min(4, request.tier))
        changes.append(f"Tier: {old_tier} → {unit.tier}")
    
    if request.alive is not None:
        old_alive = unit.alive
        unit.alive = request.alive
        if not request.alive:
            unit.hp = 0
        changes.append(f"Alive: {old_alive} → {request.alive}")
    
    # Recalculate vision if location or faction changed
    if request.location is not None or request.faction_id is not None:
        from tod.core.vision import compute_visible_hexes
        current_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        state.visible_hexes[current_faction] = compute_visible_hexes(state, current_faction)
    
    return AdminResponse(
        success=True,
        message=f"Modified unit {unit_id} ({unit.name}): {', '.join(changes)}" if changes else f"No changes to unit {unit_id}",
        data={
            "unit_id": unit_id,
            "unit_name": unit.name,
            "changes": changes,
            "current_state": {
                "hp": unit.hp,
                "max_hp": unit.max_hp,
                "location": unit.location,
                "faction_id": unit.faction.value if hasattr(unit.faction, 'value') else unit.faction,
                "tier": unit.tier,
                "alive": unit.alive
            }
        }
    )


@router.delete("/debug/units/{unit_id}", response_model=AdminResponse)
async def kill_unit(
    unit_id: int,
    state: GameState = Depends(get_game_state)
):
    """
    Kill a unit (set alive=False, hp=0).
    
    The unit remains in the game state but is marked as dead.
    """
    unit = state.get_unit(unit_id)
    if not unit:
        return AdminResponse(
            success=False,
            message=f"Unit {unit_id} not found"
        )
    
    if not unit.alive:
        return AdminResponse(
            success=False,
            message=f"Unit {unit_id} ({unit.name}) is already dead"
        )
    
    unit.alive = False
    unit.hp = 0
    
    # Recalculate vision
    from tod.core.vision import compute_visible_hexes
    faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
    state.visible_hexes[faction_id] = compute_visible_hexes(state, faction_id)
    
    return AdminResponse(
        success=True,
        message=f"Killed unit {unit_id} ({unit.name})",
        data={
            "unit_id": unit_id,
            "unit_name": unit.name,
            "location": unit.location
        }
    )


@router.post("/debug/units/{unit_id}/resurrect", response_model=AdminResponse)
async def resurrect_unit(
    unit_id: int,
    hp: Optional[int] = None,
    state: GameState = Depends(get_game_state)
):
    """
    Resurrect a dead unit.
    
    Optionally specify HP, defaults to max HP.
    """
    unit = state.get_unit(unit_id)
    if not unit:
        return AdminResponse(
            success=False,
            message=f"Unit {unit_id} not found"
        )
    
    if unit.alive:
        return AdminResponse(
            success=False,
            message=f"Unit {unit_id} ({unit.name}) is already alive"
        )
    
    unit.alive = True
    unit.hp = hp if hp is not None else unit.effective_max_hp
    
    # Recalculate vision
    from tod.core.vision import compute_visible_hexes
    faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
    state.visible_hexes[faction_id] = compute_visible_hexes(state, faction_id)
    
    return AdminResponse(
        success=True,
        message=f"Resurrected unit {unit_id} ({unit.name}) with {unit.hp} HP",
        data={
            "unit_id": unit_id,
            "unit_name": unit.name,
            "location": unit.location,
            "hp": unit.hp
        }
    )


# ============================================================================
# Object Manipulation - Bases
# ============================================================================

class ModifyBaseRequest(BaseModel):
    """Request body for modifying a base."""
    faction_id: Optional[int] = None
    tier: Optional[int] = None
    gold: Optional[int] = None
    lumber: Optional[int] = None
    oil: Optional[int] = None


@router.put("/debug/bases/{base_id}", response_model=AdminResponse)
async def modify_base(
    base_id: int,
    request: ModifyBaseRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Modify a base's properties.
    
    Only specified fields will be updated.
    """
    from tod.core.models import FactionId
    
    base = state.get_base(base_id)
    if not base:
        return AdminResponse(
            success=False,
            message=f"Base {base_id} not found"
        )
    
    changes = []
    
    if request.faction_id is not None:
        faction = state.get_faction(request.faction_id)
        if not faction:
            return AdminResponse(
                success=False,
                message=f"Faction {request.faction_id} not found"
            )
        old_faction = state.get_faction(base.faction.value if hasattr(base.faction, 'value') else base.faction)
        old_name = old_faction.name if old_faction else "Unknown"
        base.faction = FactionId(request.faction_id)
        changes.append(f"Faction: {old_name} → {faction.name}")
    
    if request.tier is not None:
        old_tier = base.tier
        base.tier = max(1, min(3, request.tier))
        changes.append(f"Tier: {old_tier} → {base.tier}")
    
    if request.gold is not None:
        old_gold = base.gold
        base.gold = max(0, request.gold)
        changes.append(f"Gold: {old_gold} → {base.gold}")
    
    if request.lumber is not None:
        old_lumber = base.lumber
        base.lumber = max(0, request.lumber)
        changes.append(f"Lumber: {old_lumber} → {base.lumber}")
    
    if request.oil is not None:
        old_oil = base.oil
        base.oil = max(0, request.oil)
        changes.append(f"Oil: {old_oil} → {base.oil}")
    
    return AdminResponse(
        success=True,
        message=f"Modified base {base_id} ({base.name}): {', '.join(changes)}" if changes else f"No changes to base {base_id}",
        data={
            "base_id": base_id,
            "base_name": base.name,
            "changes": changes,
            "current_state": {
                "tier": base.tier,
                "gold": base.gold,
                "lumber": base.lumber,
                "oil": base.oil,
                "faction_id": base.faction.value if hasattr(base.faction, 'value') else base.faction
            }
        }
    )


@router.post("/debug/bases/{base_id}/add-resources", response_model=AdminResponse)
async def add_base_resources(
    base_id: int,
    gold: int = 0,
    lumber: int = 0,
    oil: int = 0,
    state: GameState = Depends(get_game_state)
):
    """
    Add resources to a base.
    
    Use negative values to remove resources.
    """
    base = state.get_base(base_id)
    if not base:
        return AdminResponse(
            success=False,
            message=f"Base {base_id} not found"
        )
    
    old_resources = {"gold": base.gold, "lumber": base.lumber, "oil": base.oil}
    
    base.gold = max(0, base.gold + gold)
    base.lumber = max(0, base.lumber + lumber)
    base.oil = max(0, base.oil + oil)
    
    return AdminResponse(
        success=True,
        message=f"Updated resources for {base.name}",
        data={
            "base_id": base_id,
            "base_name": base.name,
            "added": {"gold": gold, "lumber": lumber, "oil": oil},
            "before": old_resources,
            "after": {"gold": base.gold, "lumber": base.lumber, "oil": base.oil}
        }
    )


# ============================================================================
# Object Manipulation - Caravans
# ============================================================================

class SpawnCaravanRequest(BaseModel):
    """Request body for spawning a caravan."""
    origin_base_id: int
    dest_base_id: int
    path: list  # List of hex IDs
    terrain_type: str = "LAND"  # LAND or SEA


@router.post("/debug/caravans/spawn", response_model=AdminResponse)
async def spawn_caravan(
    request: SpawnCaravanRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Spawn a caravan between two bases.
    
    Bypasses normal validation and resource costs.
    """
    from tod.core.models import Caravan
    from tod.core.models.caravan import CaravanTerrainType
    
    # Validate bases
    origin = state.get_base(request.origin_base_id)
    dest = state.get_base(request.dest_base_id)
    
    if not origin:
        return AdminResponse(success=False, message=f"Origin base {request.origin_base_id} not found")
    if not dest:
        return AdminResponse(success=False, message=f"Destination base {request.dest_base_id} not found")
    
    # Get initiative from origin faction
    origin_faction = state.get_faction(origin.faction.value if hasattr(origin.faction, 'value') else origin.faction)
    if not origin_faction:
        return AdminResponse(success=False, message="Could not determine initiative")
    
    # Generate new caravan ID
    new_id = max(state.caravans.keys()) + 1 if state.caravans else 1
    
    # Determine terrain type
    terrain = CaravanTerrainType.SEA if request.terrain_type.upper() == "SEA" else CaravanTerrainType.LAND
    
    # Create caravan
    caravan = Caravan(
        id=new_id,
        initiative=origin_faction.initiative,
        origin_base_id=request.origin_base_id,
        destination_base_id=request.dest_base_id,
        path=request.path,
        terrain_type=terrain
    )
    
    state.caravans[new_id] = caravan
    
    return AdminResponse(
        success=True,
        message=f"Spawned {terrain.value} caravan from {origin.name} to {dest.name}",
        data={
            "caravan_id": new_id,
            "origin": origin.name,
            "destination": dest.name,
            "path_length": len(request.path),
            "terrain_type": terrain.value
        }
    )


@router.delete("/debug/caravans/{caravan_id}", response_model=AdminResponse)
async def destroy_caravan(
    caravan_id: int,
    state: GameState = Depends(get_game_state)
):
    """
    Destroy a caravan.
    """
    caravan = state.caravans.get(caravan_id)
    if not caravan:
        return AdminResponse(
            success=False,
            message=f"Caravan {caravan_id} not found"
        )
    
    origin = state.get_base(caravan.origin_base_id)
    dest = state.get_base(caravan.destination_base_id)
    origin_name = origin.name if origin else f"Base {caravan.origin_base_id}"
    dest_name = dest.name if dest else f"Base {caravan.destination_base_id}"
    
    del state.caravans[caravan_id]
    
    return AdminResponse(
        success=True,
        message=f"Destroyed caravan {caravan_id} ({origin_name} ↔ {dest_name})",
        data={"caravan_id": caravan_id}
    )


# ============================================================================
# Object Manipulation - Turn/Phase
# ============================================================================

class SetTurnRequest(BaseModel):
    """Request body for setting turn state."""
    round_number: Optional[int] = None
    round_side: Optional[str] = None  # "HORDE" or "ALLIANCE"
    initiative: Optional[int] = None
    phase: Optional[str] = None  # "PLANNING" or "RESOLUTION"


@router.put("/debug/turn", response_model=AdminResponse)
async def set_turn_state(
    request: SetTurnRequest,
    state: GameState = Depends(get_game_state)
):
    """
    Directly set the turn state.
    
    Use with caution - this bypasses normal turn flow.
    """
    changes = []
    
    if request.round_number is not None:
        old = state.turn.round_number
        state.turn.round_number = max(1, request.round_number)
        changes.append(f"Round: {old} → {state.turn.round_number}")
    
    if request.round_side is not None:
        old = state.turn.round_side.value
        try:
            state.turn.round_side = RoundSide(request.round_side.upper())
            changes.append(f"Side: {old} → {state.turn.round_side.value}")
        except ValueError:
            return AdminResponse(
                success=False,
                message=f"Invalid round_side: {request.round_side}. Use 'HORDE' or 'ALLIANCE'"
            )
    
    if request.initiative is not None:
        old = state.turn.current_initiative
        state.turn.current_initiative = request.initiative
        changes.append(f"Initiative: {old} → {request.initiative}")
        # Clear completed initiatives since we're jumping around
        state.turn.completed_initiatives.clear()
    
    if request.phase is not None:
        old = state.turn.phase.name
        try:
            state.turn.phase = GamePhase[request.phase.upper()]
            changes.append(f"Phase: {old} → {state.turn.phase.name}")
        except KeyError:
            return AdminResponse(
                success=False,
                message=f"Invalid phase: {request.phase}. Use 'PLANNING' or 'RESOLUTION'"
            )
    
    return AdminResponse(
        success=True,
        message=f"Turn state updated: {', '.join(changes)}" if changes else "No changes",
        data={
            "round_number": state.turn.round_number,
            "round_side": state.turn.round_side.value,
            "initiative": state.turn.current_initiative,
            "phase": state.turn.phase.name,
            "turn_number": state.turn.turn_number  # Computed property
        }
    )


@router.get("/debug/unit-types")
async def list_unit_types(state: GameState = Depends(get_game_state)):
    """
    List all available unit types that can be spawned.
    """
    unit_types = []
    for name, stats in state.unit_stats.items():
        unit_types.append({
            "name": name,
            "max_hp": stats.max_hp,
            "combat": stats.combat,
            "category": stats.category.value if hasattr(stats.category, 'value') else stats.category,
            "unit_type": stats.unit_type.value if hasattr(stats.unit_type, 'value') else stats.unit_type,
            "movement": stats.movement,
            "gold_cost": stats.gold_cost,
            "lumber_cost": stats.lumber_cost,
            "oil_cost": stats.oil_cost,
            "min_tier": stats.min_tier
        })
    
    return {
        "count": len(unit_types),
        "unit_types": sorted(unit_types, key=lambda x: x["name"])
    }


@router.get("/debug/factions")
async def list_factions_debug(state: GameState = Depends(get_game_state)):
    """
    List all factions with debug info.
    """
    factions = []
    for fid, faction in state.factions.items():
        unit_count = len([u for u in state.units.values() if u.alive and (u.faction.value if hasattr(u.faction, 'value') else u.faction) == fid])
        base_count = len([b for b in state.bases.values() if (b.faction.value if hasattr(b.faction, 'value') else b.faction) == fid])
        
        factions.append({
            "id": fid,
            "name": faction.name,
            "initiative": faction.initiative,
            "is_horde": state.is_horde_faction(fid),
            "is_defeated": faction.is_defeated,
            "unit_count": unit_count,
            "base_count": base_count
        })
    
    return {
        "count": len(factions),
        "factions": sorted(factions, key=lambda x: (0 if x["is_horde"] else 1, x["initiative"], x["id"]))
    }
