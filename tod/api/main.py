"""
FastAPI application for Tides of Darkness.

This is the main entry point for the API server.

Run with:
    uvicorn tod.api.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .dependencies import get_settings, get_game_state
from .routes import (
    game_router,
    units_router,
    hexes_router,
    bases_router,
    factions_router,
    orders_router,
    admin_router,
    expansions_router,
    caravans_router,
    logs_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Runs on startup and shutdown to initialize/cleanup resources.
    """
    # Startup: Load game state
    print("Starting Tides of Darkness API...")
    state = get_game_state()  # This triggers the initial load
    print(f"Game state loaded: {len(state.units)} units, {len(state.bases)} bases, {len(state.expansions)} expansions")
    
    yield
    
    # Shutdown: Cleanup
    print("Shutting down Tides of Darkness API...")


# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings["app_name"],
    description="""
    # Tides of Darkness API
    
    Backend API for the Tides of Darkness turn-based strategy game.
    
    ## Features
    
    - **Game State**: Get current game status and statistics
    - **Units**: Query and manage military units
    - **Hexes**: Map and terrain information
    - **Bases**: Cities and settlements
    - **Factions**: Faction information and diplomacy
    - **Orders**: Submit movement and economic orders
    
    ## Authentication
    
    Currently no authentication is required. This will be added
    when implementing player-specific endpoints.
    """,
    version=settings["version"],
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game_router)
app.include_router(units_router)
app.include_router(hexes_router)
app.include_router(bases_router)
app.include_router(expansions_router)
app.include_router(caravans_router)
app.include_router(factions_router)
app.include_router(orders_router)
app.include_router(admin_router)
app.include_router(logs_router)


@app.get("/")
async def root():
    """API root - returns basic info."""
    return {
        "name": settings["app_name"],
        "version": settings["version"],
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    state = get_game_state()
    return {
        "status": "healthy",
        "gameLoaded": state is not None,
        "unitCount": len(state.units) if state else 0,
        "hexCount": len(state.hexes) if state else 0
    }


# For direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "tod.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

