"""
Caravan model for Tides of Darkness.

Caravans are STATIC trade routes between two bases that share the same initiative.
Once established, they can be used to send resources bi-directionally via the
"Send Resources" base action. All caravans can transfer any resource type.

Key rules:
- Caravans connect two bases whose factions share the same initiative
- Maximum path length is 15 hexes (including both base hexes)
- Caravans are destroyed if:
  - The two connected bases' factions no longer share the same initiative
    (checked during diplomacy resolution phase)
  - An enemy unit occupies a caravan hex with no friendly units opposing
    (checked after combat resolution)
- Caravans grant vision on the caravan hexes only (not adjacent)
- Caravan type (land/sea) is determined by the terrain of the route traced
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# Maximum caravan path length (including both base hexes)
MAX_CARAVAN_LENGTH = 15


class CaravanTerrainType(Enum):
    """Terrain type of the caravan route."""
    LAND = "land"
    SEA = "sea"


@dataclass
class Caravan:
    """
    A static trade route connecting two bases of the same initiative.
    
    The 'initiative' field stores the initiative value at creation time,
    but validity is checked dynamically against current faction initiatives.
    """
    id: int                               # Unique caravan ID
    origin_base_id: int                   # ID of the origin base
    destination_base_id: int              # ID of the destination base
    initiative: int                       # Initiative value at creation (may be stale)
    path: List[int] = field(default_factory=list)  # Hex IDs from origin to destination (inclusive)
    terrain_type: CaravanTerrainType = CaravanTerrainType.LAND  # Land or sea route
    
    @property
    def is_valid(self) -> bool:
        """Check if caravan has a valid configuration."""
        return (
            self.origin_base_id >= 0 and 
            self.destination_base_id >= 0 and 
            len(self.path) >= 2 and  # At minimum: origin hex + destination hex
            len(self.path) <= MAX_CARAVAN_LENGTH
        )
    
    @property
    def path_length(self) -> int:
        """Get the length of the caravan path (including both base hexes)."""
        return len(self.path)
    
    @property
    def origin_hex(self) -> int:
        """Get the origin base's hex (first in path)."""
        return self.path[0] if self.path else -1
    
    @property
    def destination_hex(self) -> int:
        """Get the destination base's hex (last in path)."""
        return self.path[-1] if self.path else -1
    
    @property
    def intermediate_hexes(self) -> List[int]:
        """Get all hexes between the two bases (excluding base hexes)."""
        if len(self.path) <= 2:
            return []
        return self.path[1:-1]
    
    @property
    def all_hexes(self) -> List[int]:
        """Get all hexes in the caravan route."""
        return self.path.copy()
    
    def contains_hex(self, hex_id: int) -> bool:
        """Check if a hex is part of this caravan route."""
        return hex_id in self.path
    
    def connects_bases(self, base_id_1: int, base_id_2: int) -> bool:
        """Check if this caravan connects the two specified bases (in either direction)."""
        return (
            (self.origin_base_id == base_id_1 and self.destination_base_id == base_id_2) or
            (self.origin_base_id == base_id_2 and self.destination_base_id == base_id_1)
        )
    
    def check_initiative_validity(self, origin_faction_initiative: int, dest_faction_initiative: int) -> bool:
        """
        Check if the caravan is still valid based on current faction initiatives.
        
        The caravan remains valid as long as both bases' factions share the same
        initiative value - even if that value has changed since establishment.
        
        Args:
            origin_faction_initiative: Current initiative of the origin base's faction
            dest_faction_initiative: Current initiative of the destination base's faction
            
        Returns:
            True if both factions still share the same initiative
        """
        return origin_faction_initiative == dest_faction_initiative
    
    @classmethod
    def from_db_row(cls, caravan_id: int, row: tuple) -> 'Caravan':
        """
        Create a Caravan from a database row.
        
        Expected format: (origin_base, destination_base, initiative, hex1, hex2, hex3, ...)
        """
        path = []
        for i in range(3, len(row)):
            if row[i] is not None and row[i] != -1:
                path.append(int(row[i]))
        
        return cls(
            id=caravan_id,
            origin_base_id=int(row[0]),
            destination_base_id=int(row[1]),
            initiative=int(row[2]),
            path=path,
        )
    
    def to_db_tuple(self, max_path_length: int = MAX_CARAVAN_LENGTH) -> tuple:
        """
        Convert to database tuple for INSERT.
        Pads path to max_path_length with -1 values.
        """
        result = [
            self.origin_base_id,
            self.destination_base_id,
            self.initiative,
        ]
        # Add path hexes, padding with -1
        for i in range(max_path_length):
            if i < len(self.path):
                result.append(self.path[i])
            else:
                result.append(-1)
        return tuple(result)
    
    def __repr__(self) -> str:
        return f"Caravan(id={self.id}, bases={self.origin_base_id}↔{self.destination_base_id}, init={self.initiative}, len={len(self.path)})"


@dataclass
class PendingCaravanOrder:
    """
    A pending order to establish a new caravan.
    Stored until resolution phase.
    """
    origin_base_id: int
    destination_base_id: int
    path: List[int]
    lumber_cost: int = 0  # Cost to establish (may vary by path length)
