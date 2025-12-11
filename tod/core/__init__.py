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
