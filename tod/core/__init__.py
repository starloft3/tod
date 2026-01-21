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
from .combat_modifiers import (
    assign_combat_modifiers, clear_combat_modifiers,
    calculate_flanking_bonuses, calculate_terrain_modifiers,
    TERRAIN_MODIFIERS, INITIAL_DEFENDER_MODIFIERS,
    get_river_penalty, get_fortification_penalty,
    get_siege_vs_fortification_penalty, get_flanking_bonus_increment
)
from .combat_special import (
    AmphibiousLanding, RangedfireAttack,
    check_amphibious_landing, execute_amphibious_landing,
    apply_amphibious_penalties,
    get_rangedfire_eligible_units, execute_rangedfire,
    AMPHIBIOUS_ATTACK_PENALTY, AMPHIBIOUS_DEFENSE_PENALTY
)