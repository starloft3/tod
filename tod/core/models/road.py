"""
Road model for Tides of Darkness.

Roads connect hexes and allow faster movement.
Each road entry defines connectivity from one hex to its neighbors.
"""
from dataclasses import dataclass
from typing import Dict, List
from .enums import Direction


@dataclass
class Road:
    """
    Road connectivity data for a hex.
    
    A road value > 0 indicates a road connection in that direction.
    The value may indicate road type or quality.
    """
    hex_id: int                      # The hex this road data is for
    
    # Road connections to each direction (0 = no road, >0 = road exists)
    north: int = 0
    northeast: int = 0
    southeast: int = 0
    south: int = 0
    southwest: int = 0
    northwest: int = 0
    
    @property
    def connections(self) -> Dict[Direction, int]:
        """Get all road connections as a dictionary."""
        return {
            Direction.N: self.north,
            Direction.NE: self.northeast,
            Direction.SE: self.southeast,
            Direction.S: self.south,
            Direction.SW: self.southwest,
            Direction.NW: self.northwest,
        }
    
    def has_road(self, direction: Direction) -> bool:
        """Check if there's a road in the given direction."""
        return self.connections[direction] > 0
    
    @property
    def connected_directions(self) -> List[Direction]:
        """Get list of directions with road connections."""
        return [d for d, v in self.connections.items() if v > 0]
    
    @property
    def is_junction(self) -> bool:
        """Check if this hex is a road junction (3+ connections)."""
        return len(self.connected_directions) >= 3
    
    @classmethod
    def from_legacy_list(cls, data: list) -> 'Road':
        """Create a Road from the legacy allroads[x] list format."""
        return cls(
            hex_id=int(data[0]),        # ROAD_HEX
            north=int(data[1]),         # ROAD_N
            northeast=int(data[2]),     # ROAD_NE
            southeast=int(data[3]),     # ROAD_SE
            south=int(data[4]),         # ROAD_S
            southwest=int(data[5]),     # ROAD_SW
            northwest=int(data[6]),     # ROAD_NW
        )
    
    def to_legacy_list(self) -> list:
        """Convert back to legacy list format for compatibility."""
        return [
            self.hex_id,                 # 0: ROAD_HEX
            self.north,                  # 1: ROAD_N
            self.northeast,              # 2: ROAD_NE
            self.southeast,              # 3: ROAD_SE
            self.south,                  # 4: ROAD_S
            self.southwest,              # 5: ROAD_SW
            self.northwest,              # 6: ROAD_NW
        ]
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Road':
        """Create a Road from a database row (roaddata table)."""
        return cls(
            hex_id=int(row[0]),
            north=int(row[1]),
            northeast=int(row[2]),
            southeast=int(row[3]),
            south=int(row[4]),
            southwest=int(row[5]),
            northwest=int(row[6]),
        )

