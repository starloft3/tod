"""
Caravan model for Tides of Darkness.

Caravans are trade routes between bases that transfer resources.
They follow a path of hexes and belong to a faction.
"""
from dataclasses import dataclass, field
from typing import List
from .enums import FactionId


class CaravanType:
    """Types of caravans/trade routes."""
    NONE = 'none'
    GOLD = 'gold'
    LUMBER = 'lumber'
    OIL = 'oil'
    MIXED = 'mixed'
    CONSTRUCTION = 'construction'  # Construction assistance


@dataclass
class Caravan:
    """
    A trade caravan moving resources between bases.
    """
    # Route
    origin_base: int                  # ID of the origin base
    destination_base: int             # ID of the destination base
    faction: FactionId                # Owning faction
    
    # Type
    caravan_type: str = CaravanType.NONE
    
    # Path
    path: List[int] = field(default_factory=list)  # List of hex IDs along the route
    
    @property
    def is_active(self) -> bool:
        """Check if caravan is active (has valid route)."""
        return (self.origin_base >= 0 and 
                self.destination_base >= 0 and 
                self.caravan_type != CaravanType.NONE)
    
    @property
    def path_length(self) -> int:
        """Get the length of the caravan path."""
        return len(self.path)
    
    @property
    def current_location(self) -> int:
        """Get current hex (first in path, or -1 if no path)."""
        return self.path[0] if self.path else -1
    
    def advance(self) -> bool:
        """
        Move caravan one hex along path.
        Returns True if caravan reached destination.
        """
        if self.path:
            self.path.pop(0)
        return len(self.path) == 0
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Caravan':
        """Create a Caravan from a database row (savecaravans table)."""
        # First 4 fields are origin, destination, faction, type
        # Remaining fields are path hexes
        path = []
        for i in range(4, len(row)):
            if row[i] is not None:
                path.append(int(row[i]))
        
        return cls(
            origin_base=int(row[0]),
            destination_base=int(row[1]),
            faction=FactionId(int(row[2])),
            caravan_type=str(row[3]) if row[3] else CaravanType.NONE,
            path=path,
        )
    
    def to_db_tuple(self, max_path_length: int = 10) -> tuple:
        """
        Convert to database tuple for INSERT.
        Pads path to max_path_length with None values.
        """
        result = [
            self.origin_base,
            self.destination_base,
            self.faction.value,
            self.caravan_type,
        ]
        # Add path hexes, padding with None
        for i in range(max_path_length):
            if i < len(self.path):
                result.append(self.path[i])
            else:
                result.append(None)
        return tuple(result)


@dataclass
class ConstructionAssist:
    """
    A construction assistance order (similar to caravan but for building).
    """
    origin_base: int
    destination_base: int
    faction: FactionId
    assist_type: str = 'none'
    path: List[int] = field(default_factory=list)
    
    @classmethod
    def from_caravan(cls, caravan: Caravan) -> 'ConstructionAssist':
        """Create from a caravan with construction type."""
        return cls(
            origin_base=caravan.origin_base,
            destination_base=caravan.destination_base,
            faction=caravan.faction,
            assist_type=caravan.caravan_type,
            path=caravan.path.copy(),
        )

