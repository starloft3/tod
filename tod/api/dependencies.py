"""
FastAPI dependencies.

Provides shared dependencies for route handlers, including
the game state singleton.
"""
from typing import Optional
from functools import lru_cache

from tod.core import GameState, load_game_state


# Global game state instance
_game_state: Optional[GameState] = None


def get_game_state() -> GameState:
    """
    Dependency that provides the current game state.
    
    The game state is loaded once and cached. Use reload_game_state()
    to refresh from the database.
    """
    global _game_state
    if _game_state is None:
        print("Loading game state from database...")
        _game_state = load_game_state(from_saved=True)
        print(f"Loaded: {len(_game_state.units)} units, {len(_game_state.hexes)} hexes, {len(_game_state.bases)} bases")
    return _game_state


def reload_game_state() -> GameState:
    """
    Reload game state from the database.
    
    This discards any in-memory changes and fetches fresh data.
    """
    global _game_state
    print("Reloading game state from database...")
    _game_state = load_game_state(from_saved=True)
    print(f"Reloaded: {len(_game_state.units)} units, {len(_game_state.hexes)} hexes, {len(_game_state.bases)} bases")
    return _game_state


def save_current_state() -> None:
    """
    Save the current game state to the database.
    """
    global _game_state
    if _game_state is None:
        raise RuntimeError("No game state loaded")
    
    from tod.core import save_game_state
    save_game_state(_game_state)
    print("Game state saved to database")


@lru_cache()
def get_settings():
    """
    Get application settings.
    
    This could be expanded to load from environment variables
    or a config file.
    """
    return {
        "app_name": "Tides of Darkness API",
        "version": "0.1.0",
        "debug": True,
        "cors_origins": [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    }

