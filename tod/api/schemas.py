"""
Pydantic schemas for API responses.

These are separate from the core dataclasses to allow:
- API-specific field naming (camelCase for JS)
- Response filtering (don't expose internal fields)
- Validation on input
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


# ==================== Enums ====================

class GamePhaseSchema(str, Enum):
    SETUP = "setup"
    PLANNING = "planning"
    RESOLUTION = "resolution"
    COMBAT = "combat"
    ECONOMIC = "economic"
    END_TURN = "end_turn"


class UnitCategorySchema(str, Enum):
    MELEE = "melee"
    RANGED = "ranged"
    EXPERT = "expert"
    INTERIOR_SIEGE = "interior_siege"
    EXTERIOR_SIEGE = "exterior_siege"
    NO_FIRE = "no_fire"


class TerrainSchema(str, Enum):
    CLEAR = "C"
    FOREST = "F"
    MOUNTAIN = "M"
    WATER = "O"
    SWAMP = "S"
    IMPASSABLE = "X"


# ==================== Unit Schemas ====================

class UnitSummary(BaseModel):
    """Brief unit info for lists."""
    id: int
    name: str
    faction: int = Field(alias="factionId")
    hp: int
    maxHp: int
    location: int
    alive: bool
    
    class Config:
        populate_by_name = True


class UnitDetail(BaseModel):
    """Full unit details."""
    id: int
    name: str
    factionId: int
    
    # Stats
    maxHp: int
    hp: int
    combat: int
    category: str
    unitType: int
    
    # Armor
    lightArmorMax: int
    lightArmorCurrent: int
    heavyArmor: int
    naturalArmor: int
    armorBroken: bool
    
    # Movement
    movementMax: int
    movementRemaining: int
    roadMoveRemaining: int
    roadMoveOnly: bool
    vision: int
    stealth: int
    
    # Position
    location: int
    previousLocation: int
    
    # Veterancy
    tier: int
    tier1Ability: str
    tier2Ability: str
    tier3Ability: str
    tier4Ability: str
    
    # Combat state
    alive: bool
    fired: bool
    terrainBonus: int
    flankBonus: int
    holdBonus: int
    combatStart: int
    
    # Transport
    transportSlot1: int
    transportSlot2: int
    transportSlot3: int
    
    class Config:
        populate_by_name = True


# ==================== Hex Schemas ====================

class HexSideSchema(BaseModel):
    """Hex edge data."""
    terrain: str
    control: int


class HexSummary(BaseModel):
    """Brief hex info."""
    id: int
    terrain: str
    hasBase: bool = False
    hasUnits: bool = False
    
    class Config:
        populate_by_name = True


class HexDetail(BaseModel):
    """Full hex details."""
    id: int
    terrain: str
    
    # Edges
    north: HexSideSchema
    northeast: HexSideSchema
    southeast: HexSideSchema
    south: HexSideSchema
    southwest: HexSideSchema
    northwest: HexSideSchema
    
    # Structures
    building: int
    hasOil: bool
    farm: int
    mill: int
    rig: int
    gold: int
    
    # Combat state
    newCombat: bool
    battleFought: bool
    assisted: bool
    expansionOwner: int
    
    class Config:
        populate_by_name = True


# ==================== Base Schemas ====================

class BaseSummary(BaseModel):
    """Brief base info."""
    id: int
    name: str
    location: int
    factionId: int
    tier: int
    
    class Config:
        populate_by_name = True


class BaseDetail(BaseModel):
    """Full base details."""
    id: int
    name: str
    location: int
    factionId: int
    tier: int
    gold: int
    lumber: int
    oil: int
    actions: int
    
    class Config:
        populate_by_name = True


# ==================== Faction Schemas ====================

class FactionSummary(BaseModel):
    """Brief faction info."""
    id: int
    name: str
    initiative: int
    isDefeated: bool
    isHorde: bool
    isAlliance: bool
    
    class Config:
        populate_by_name = True


class FactionDetail(BaseModel):
    """Full faction details."""
    id: int
    name: str
    initiative: int
    isDefeated: bool
    membership: int
    isLeader: bool
    leaderVote: int
    allianceVotes: str
    hordeDecision: str
    warchiefDecision: int
    
    class Config:
        populate_by_name = True


# ==================== Game State Schemas ====================

class TurnStateSchema(BaseModel):
    """Current turn information."""
    turnNumber: int
    currentInitiative: int
    currentFaction: int
    phase: str
    activeFactionIds: List[int] = []  # Factions who can submit orders this turn
    roundNumber: int = 1
    roundSide: str = "HORDE"
    
    class Config:
        populate_by_name = True


class GameStateSummary(BaseModel):
    """Overview of the game state."""
    turn: TurnStateSchema
    unitCount: int
    aliveUnitCount: int
    hexCount: int
    baseCount: int
    factionCount: int
    roadCount: int
    caravanCount: int
    
    class Config:
        populate_by_name = True


class VisibleHexesResponse(BaseModel):
    """Response for faction's visible hexes."""
    factionId: int
    initiative: int
    hexIds: List[int]
    
    class Config:
        populate_by_name = True


# ==================== Order Schemas ====================

class OrderCreate(BaseModel):
    """Create a movement order."""
    unitId: int
    orderType: str = "M"  # M = move, A = attack, etc.
    target: int
    secondary: int = 0
    
    class Config:
        populate_by_name = True


class SpecialOrderCreate(BaseModel):
    """Create a special order (spell, ability)."""
    factionId: int
    orderType: str
    source: int
    target: int
    secondary: int = 0
    
    class Config:
        populate_by_name = True


class EconomicActionCreate(BaseModel):
    """Create an economic action."""
    factionId: int
    actionType: str
    baseId: int
    target: str
    quantity: int = 1
    
    class Config:
        populate_by_name = True


# ==================== Response Wrappers ====================

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[Any]
    total: int
    page: int = 1
    pageSize: int = 50
    hasMore: bool = False

