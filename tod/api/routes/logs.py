"""
Game Log API endpoints.

Provides access to the game event log for both admin and player views.
"""
from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime

from tod.core.game_log import get_game_log, LogEventType


router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def get_logs(
    category: Optional[str] = Query(None, description="Filter by category: combat, movement, harvest, economic, entity, turn, debug"),
    event_type: Optional[str] = Query(None, description="Filter by specific event type"),
    faction_id: Optional[int] = Query(None, description="Filter by faction"),
    turn: Optional[int] = Query(None, description="Filter by turn number"),
    hex_id: Optional[int] = Query(None, description="Filter by hex"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get game log entries with optional filtering.
    
    Returns entries in reverse chronological order (newest first).
    """
    game_log = get_game_log()
    
    entries = game_log.get_entries(
        category=category,
        event_type=event_type,
        faction_id=faction_id,
        turn_number=turn,
        hex_id=hex_id,
        limit=limit,
        offset=offset
    )
    
    return {
        "timestamp": datetime.now().isoformat(),
        "count": len(entries),
        "total": len(game_log.entries),
        "filters": {
            "category": category,
            "event_type": event_type,
            "faction_id": faction_id,
            "turn": turn,
            "hex_id": hex_id
        },
        "entries": [e.to_dict() for e in entries]
    }


@router.get("/summary")
async def get_log_summary():
    """
    Get a summary of log statistics.
    """
    game_log = get_game_log()
    summary = game_log.get_summary()
    
    return {
        "timestamp": datetime.now().isoformat(),
        **summary
    }


@router.get("/categories")
async def get_log_categories():
    """
    Get available log categories and event types.
    """
    categories = {
        "combat": {
            "name": "Combat",
            "icon": "⚔️",
            "color": "#b83030",
            "event_types": [
                LogEventType.COMBAT_START.value,
                LogEventType.COMBAT_ATTACK.value,
                LogEventType.COMBAT_DAMAGE.value,
                LogEventType.COMBAT_DEATH.value,
                LogEventType.COMBAT_END.value,
            ]
        },
        "movement": {
            "name": "Movement",
            "icon": "🚶",
            "color": "#3080b8",
            "event_types": [
                LogEventType.MOVEMENT.value,
            ]
        },
        "harvest": {
            "name": "Harvests",
            "icon": "🌾",
            "color": "#7cb342",
            "event_types": [
                LogEventType.HARVEST.value,
            ]
        },
        "economic": {
            "name": "Economic",
            "icon": "🪙",
            "color": "#b8a030",
            "event_types": [
                LogEventType.COMMERCE.value,
                LogEventType.BUILD_UNIT.value,
                LogEventType.UPGRADE_BASE.value,
                LogEventType.REST_UNIT.value,
                LogEventType.EXPAND.value,
                LogEventType.ESTABLISH_CARAVAN.value,
                LogEventType.SEND_RESOURCES.value,
            ]
        },
        "entity": {
            "name": "Entity",
            "icon": "📜",
            "color": "#808080",
            "event_types": [
                LogEventType.UNIT_CREATED.value,
                LogEventType.UNIT_DESTROYED.value,
                LogEventType.BASE_CAPTURED.value,
                LogEventType.BASE_DESTROYED.value,
                LogEventType.CARAVAN_DESTROYED.value,
                LogEventType.EXPANSION_DESTROYED.value,
            ]
        },
        "diplomacy": {
            "name": "Diplomacy",
            "icon": "🤝",
            "color": "#9b59b6",
            "event_types": [
                LogEventType.DIPLOMACY.value,
            ]
        },
        "turn": {
            "name": "Turn",
            "icon": "⏱️",
            "color": "#30b880",
            "event_types": [
                LogEventType.TURN_START.value,
                LogEventType.TURN_END.value,
                LogEventType.ROUND_START.value,
                LogEventType.INITIATIVE_START.value,
            ]
        },
        "debug": {
            "name": "Debug",
            "icon": "🔧",
            "color": "#9b4dca",
            "event_types": [
                LogEventType.DEBUG_ACTION.value,
            ]
        }
    }
    
    return {
        "categories": categories
    }


@router.get("/turn/{turn_number}")
async def get_logs_by_turn(turn_number: int):
    """
    Get all log entries for a specific turn.
    """
    game_log = get_game_log()
    entries = game_log.get_entries_by_turn(turn_number)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "turn_number": turn_number,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries]
    }


@router.get("/combat/{hex_id}")
async def get_combat_log(
    hex_id: int,
    turn: Optional[int] = Query(None, description="Filter by turn number")
):
    """
    Get combat log entries for a specific hex.
    """
    game_log = get_game_log()
    entries = game_log.get_combat_log_for_hex(hex_id, turn_number=turn)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "hex_id": hex_id,
        "turn": turn,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries]
    }


@router.delete("")
async def clear_logs():
    """
    Clear all log entries. (Admin only)
    """
    game_log = get_game_log()
    count = len(game_log.entries)
    game_log.clear()
    
    return {
        "success": True,
        "message": f"Cleared {count} log entries",
        "timestamp": datetime.now().isoformat()
    }

