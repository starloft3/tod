# Core game logic module
"""Core game logic package."""
from .models import *
from .game_state import (
    GameState, GamePhase, TurnState, Initiative,
    Order, SpecialOrder, EconomicAction, SpecialEvent,
    get_game_state, set_game_state
)
from .database import (
    load_game_state, save_game_state,
    DatabaseLoader, DatabaseSaver,
    get_db_connection, DEFAULT_DB_CONFIG
)
from . import reference_data
from .vision import compute_visible_hexes, expand_vision, get_adjacent_hexes
from .faction_view import get_faction_view, get_omniscient_view, FactionView
from .combat_manager import (
    CombatManager, ActiveCombat, CombatType,
    get_combat_manager, set_combat_manager, init_combat_manager
)
from .combat_engine import (
    CombatEngine, FiringCategory, AttackResult, CombatRoundResult,
    resolve_combat, resolve_all_pending_combats, resolve_end_of_round_combats
)
