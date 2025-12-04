# API routes package
"""Route modules for different API endpoints."""
from .game import router as game_router
from .units import router as units_router
from .hexes import router as hexes_router
from .bases import router as bases_router
from .factions import router as factions_router
from .orders import router as orders_router

__all__ = [
    'game_router',
    'units_router', 
    'hexes_router',
    'bases_router',
    'factions_router',
    'orders_router',
]

