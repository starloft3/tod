# API routes package
"""Route modules for different API endpoints."""
from .game import router as game_router
from .units import router as units_router
from .hexes import router as hexes_router
from .bases import router as bases_router
from .factions import router as factions_router
from .orders import router as orders_router
from .admin import router as admin_router
from .expansions import router as expansions_router
from .caravans import router as caravans_router
from .logs import router as logs_router

__all__ = [
    'game_router',
    'units_router', 
    'hexes_router',
    'bases_router',
    'factions_router',
    'orders_router',
    'admin_router',
    'expansions_router',
    'caravans_router',
    'logs_router',
]

