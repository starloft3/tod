"""
Hex model for Tides of Darkness.

The game map is made of hexagonal tiles. Each hex has:
- A center terrain type
- Six edge terrains (for rivers, cliffs, etc.)
- Buildings, resources, and combat state
"""
from dataclasses import dataclass, field
from typing import Optional, Dict
from .enums import Terrain, Direction, BuildingType, FactionId


@dataclass
class HexSide:
    """
    Represents one side/edge of a hex.
    Used for terrain features like rivers that exist between hexes,
    and for tracking control during combat.
    """
    terrain: str = ''                # Edge terrain type (empty = no special terrain)
    control: int = 0                  # Faction controlling this hexside (0 = contested)


@dataclass
class Hex:
    """
    A single hex tile on the game map.
    """
    # Identity
    id: int                           # Hex ID (0-1100+, based on position)
    
    # Terrain
    terrain: str                      # Center terrain type
    
    # Edge terrains (rivers, cliffs, coastal, etc.)
    north: HexSide = field(default_factory=HexSide)
    northeast: HexSide = field(default_factory=HexSide)
    southeast: HexSide = field(default_factory=HexSide)
    south: HexSide = field(default_factory=HexSide)
    southwest: HexSide = field(default_factory=HexSide)
    northwest: HexSide = field(default_factory=HexSide)
    
    # Structures
    building: BuildingType = BuildingType.NONE  # Special building (runestone, portal, etc.)
    
    # Resources
    has_oil: bool = False             # Oil deposit present
    farm: int = -1                    # Associated base ID if farm exists (-1 = none)
    mill: int = -1                    # Associated base ID if lumber mill exists
    rig: int = -1                     # Associated base ID if oil rig exists
    gold: int = 0                     # Gold mine value
    
    # Combat State
    new_combat: bool = False          # Is this the first round of combat here?
    battle_fought: bool = False       # Was a battle fought here this turn?
    assisted: bool = False            # Is this hex receiving assistance?
    expansion_owner: int = 0          # Faction ID that owns any expansion here
    
    @property
    def sides(self) -> Dict[Direction, HexSide]:
        """Get all hex sides as a dictionary."""
        return {
            Direction.N: self.north,
            Direction.NE: self.northeast,
            Direction.SE: self.southeast,
            Direction.S: self.south,
            Direction.SW: self.southwest,
            Direction.NW: self.northwest,
        }
    
    def get_side(self, direction: Direction) -> HexSide:
        """Get hex side by direction."""
        return self.sides[direction]
    
    @property
    def is_water(self) -> bool:
        """Check if this is a water hex."""
        return self.terrain == Terrain.OCEAN
    
    @property
    def is_land(self) -> bool:
        """Check if this is a land hex."""
        return self.terrain in [Terrain.CLEAR, Terrain.FOREST, Terrain.MOUNTAIN, 
                                Terrain.SWAMP, Terrain.PEAKS]
    
    @property
    def is_passable(self) -> bool:
        """Check if units can enter this hex (Peaks are impassable for ground units)."""
        return self.terrain != Terrain.PEAKS
    
    @property
    def has_resources(self) -> bool:
        """Check if this hex has any resource structures."""
        return self.farm >= 0 or self.mill >= 0 or self.rig >= 0 or self.gold > 0
    
    def reset_combat_state(self):
        """Reset combat-related state for new turn."""
        self.new_combat = True
        self.battle_fought = False
        # Note: Hexside control is now managed by CombatManager (combat-only)
        # The HexSide.control field is legacy and should not be used
    
    @classmethod
    def from_legacy_list(cls, hex_id: int, data: list) -> 'Hex':
        """
        Create a Hex from the legacy allhexes[x] list format.
        """
        return cls(
            id=hex_id,
            terrain=data[0],  # HEX_TERRAIN
            north=HexSide(terrain=data[1], control=data[15] if len(data) > 15 else 0),
            northeast=HexSide(terrain=data[2], control=data[16] if len(data) > 16 else 0),
            southeast=HexSide(terrain=data[3], control=data[17] if len(data) > 17 else 0),
            south=HexSide(terrain=data[4], control=data[18] if len(data) > 18 else 0),
            southwest=HexSide(terrain=data[5], control=data[19] if len(data) > 19 else 0),
            northwest=HexSide(terrain=data[6], control=data[20] if len(data) > 20 else 0),
            building=BuildingType(data[7]) if data[7] in [0, 1, 2, 3] else BuildingType.NONE,
            has_oil=bool(data[8]) if len(data) > 8 else False,
            farm=data[9] if len(data) > 9 else -1,
            mill=data[10] if len(data) > 10 else -1,
            rig=data[11] if len(data) > 11 else -1,
            gold=data[12] if len(data) > 12 else 0,
            new_combat=bool(data[13]) if len(data) > 13 else False,
            battle_fought=bool(data[14]) if len(data) > 14 else False,
            assisted=bool(data[21]) if len(data) > 21 else False,
            expansion_owner=data[22] if len(data) > 22 else 0,
        )
    
    def to_legacy_list(self) -> list:
        """Convert back to legacy list format for compatibility."""
        return [
            self.terrain,                  # 0: HEX_TERRAIN
            self.north.terrain,            # 1: HEX_N_TERRAIN
            self.northeast.terrain,        # 2: HEX_NE_TERRAIN
            self.southeast.terrain,        # 3: HEX_SE_TERRAIN
            self.south.terrain,            # 4: HEX_S_TERRAIN
            self.southwest.terrain,        # 5: HEX_SW_TERRAIN
            self.northwest.terrain,        # 6: HEX_NW_TERRAIN
            self.building.value,           # 7: HEX_BUILDING
            1 if self.has_oil else 0,      # 8: HEX_OIL
            self.farm,                     # 9: HEX_FARM
            self.mill,                     # 10: HEX_MILL
            self.rig,                      # 11: HEX_RIG
            self.gold,                     # 12: HEX_GOLD
            1 if self.new_combat else 0,   # 13: HEX_NEW_COMBAT
            1 if self.battle_fought else 0,# 14: HEX_BATTLE_FOUGHT
            self.north.control,            # 15: HEX_N_CONTROL
            self.northeast.control,        # 16: HEX_NE_CONTROL
            self.southeast.control,        # 17: HEX_SE_CONTROL
            self.south.control,            # 18: HEX_S_CONTROL
            self.southwest.control,        # 19: HEX_SW_CONTROL
            self.northwest.control,        # 20: HEX_NW_CONTROL
            1 if self.assisted else 0,     # 21: HEX_ASSISTED
            self.expansion_owner,          # 22: HEX_EXPANSION_OWNER
        ]
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Hex':
        """
        Create a Hex from a database row (savehexes/hexdata table).
        Row[0] is the hex ID, rest matches legacy format.
        """
        hex_id = int(row[0])
        return cls.from_legacy_list(hex_id, list(row[1:]))
    
    @classmethod
    def from_db_row_no_id(cls, hex_id: int, row: tuple) -> 'Hex':
        """
        Create a Hex from a database row where ID is not in the row.
        ID is derived from row order in the database.
        """
        return cls.from_legacy_list(hex_id, list(row))
    
    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion (no ID - derived from order)."""
        return tuple(self.to_legacy_list())

