"""
Base model for Tides of Darkness.

Bases are cities/settlements that:
- Are controlled by factions
- Have tiers (1-3) determining what can be built
- Store resources (gold, lumber, oil)
- Can perform actions each turn
- Have attached expansions (farms, mills, oil rigs)
"""
from dataclasses import dataclass, field
from typing import Optional, List
from .enums import FactionId


@dataclass
class Base:
    """
    A base (city/settlement) on the map.
    """
    # Identity
    id: int                          # Base ID (index in allbases)
    name: str                        # Base name (e.g., "Lordaeron")
    location: int                    # Hex ID where base is located
    
    # Ownership
    faction: FactionId               # Controlling faction
    
    # Development
    tier: int = 1                    # Base tier (1-3), determines buildable units
    
    # Resources
    gold: int = 0                    # Stored gold
    lumber: int = 0                  # Stored lumber
    oil: int = 0                     # Stored oil
    
    # State
    actions: int = 0                 # Actions available this turn (or alive flag)
    
    # Expansions (list of expansion IDs attached to this base)
    expansions: List[int] = field(default_factory=list)
    
    @property
    def is_capital(self) -> bool:
        """Check if this is a tier 3 (capital) base."""
        return self.tier >= 3
    
    @property
    def can_build_tier2(self) -> bool:
        """Check if this base can build tier 2 units."""
        return self.tier >= 2
    
    @property
    def can_build_tier3(self) -> bool:
        """Check if this base can build tier 3 units."""
        return self.tier >= 3
    
    def add_resources(self, gold: int = 0, lumber: int = 0, oil: int = 0):
        """Add resources to this base."""
        self.gold += gold
        self.lumber += lumber
        self.oil += oil
    
    def spend_resources(self, gold: int = 0, lumber: int = 0, oil: int = 0) -> bool:
        """
        Attempt to spend resources. Returns True if successful.
        Does not modify resources if insufficient.
        
        If debug.infinite_resources is enabled, always succeeds without
        actually deducting resources.
        """
        # Check for infinite resources debug mode
        try:
            from tod.core.game_config import get_game_config
            if get_game_config().debug.infinite_resources:
                return True  # Pretend we spent, but don't deduct
        except Exception:
            pass  # Config not available, use normal logic
        
        if self.gold >= gold and self.lumber >= lumber and self.oil >= oil:
            self.gold -= gold
            self.lumber -= lumber
            self.oil -= oil
            return True
        return False
    
    def can_afford(self, gold: int = 0, lumber: int = 0, oil: int = 0) -> bool:
        """
        Check if base has enough resources.
        
        If debug.infinite_resources is enabled, always returns True.
        """
        # Check for infinite resources debug mode
        try:
            from tod.core.game_config import get_game_config
            if get_game_config().debug.infinite_resources:
                return True
        except Exception:
            pass  # Config not available, use normal logic
        
        return self.gold >= gold and self.lumber >= lumber and self.oil >= oil
    
    @classmethod
    def from_legacy_list(cls, base_id: int, data: list) -> 'Base':
        """Create a Base from the legacy allbases[x] list format."""
        return cls(
            id=base_id,
            name=data[0],               # BASE_NAME
            location=int(data[1]),      # BASE_LOCATION
            faction=FactionId(int(data[2])),  # BASE_FACTION
            tier=int(data[3]),          # BASE_TIER
            gold=int(data[4]),          # BASE_GOLD
            lumber=int(data[5]),        # BASE_LUMBER
            oil=int(data[6]),           # BASE_OIL
            actions=int(data[7]) if len(data) > 7 else 0,  # BASE_ACTIONS
        )
    
    def to_legacy_list(self) -> list:
        """Convert back to legacy list format for compatibility."""
        return [
            self.name,                   # 0: BASE_NAME
            self.location,               # 1: BASE_LOCATION
            self.faction.value,          # 2: BASE_FACTION
            self.tier,                   # 3: BASE_TIER
            self.gold,                   # 4: BASE_GOLD
            self.lumber,                 # 5: BASE_LUMBER
            self.oil,                    # 6: BASE_OIL
            self.actions,                # 7: BASE_ACTIONS
        ]
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Base':
        """Create a Base from a database row (basedata/savebases table) with ID in row."""
        # Database row includes ID as first column
        return cls(
            id=int(row[0]),
            name=str(row[1]),
            location=int(row[2]),
            faction=FactionId(int(row[3])),
            tier=int(row[4]),
            gold=int(row[5]),
            lumber=int(row[6]),
            oil=int(row[7]),
            actions=int(row[8]) if len(row) > 8 else 0,
        )
    
    @classmethod
    def from_db_row_no_id(cls, base_id: int, row: tuple) -> 'Base':
        """Create a Base from a database row where ID is derived from row order."""
        return cls(
            id=base_id,
            name=str(row[0]),
            location=int(row[1]),
            faction=FactionId(int(row[2])),
            tier=int(row[3]),
            gold=int(row[4]),
            lumber=int(row[5]),
            oil=int(row[6]),
            actions=int(row[7]) if len(row) > 7 else 0,
        )
    
    def to_db_tuple(self) -> tuple:
        """Convert to database tuple for INSERT (no ID - derived from order)."""
        return (
            self.name,
            self.location,
            self.faction.value,
            self.tier,
            self.gold,
            self.lumber,
            self.oil,
            self.actions,
        )

