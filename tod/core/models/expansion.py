"""
Expansion model for Tides of Darkness.

Expansions are structures built near bases that allow resource collection:
- Farms: Built in Clear terrain, +1 food, harvest gold from mines
- Mills: Built in Forest terrain, harvest lumber + gold from mines
- Oil Rigs: Built in Ocean terrain with oil, harvest oil

Expansions belong to a base and are destroyed if:
- The base is destroyed
- They are alone with enemy units at end of combat round
"""
from dataclasses import dataclass
from .orders import ExpansionType


@dataclass
class Expansion:
    """
    A resource expansion attached to a base.
    """
    # Identity
    id: int                          # Unique expansion ID
    type: ExpansionType              # FARM, LUMBER_MILL, or OIL_RIG
    
    # Location
    location: int                    # Hex ID where expansion is built
    
    # Ownership
    base_id: int                     # ID of the base this expansion belongs to
    
    @property
    def type_name(self) -> str:
        """Human-readable type name."""
        names = {
            ExpansionType.FARM: 'Farm',
            ExpansionType.LUMBER_MILL: 'Lumber Mill',
            ExpansionType.OIL_RIG: 'Oil Rig'
        }
        return names.get(self.type, 'Unknown')
    
    @property
    def required_terrain(self) -> str:
        """The terrain type required for this expansion type."""
        from .enums import Terrain
        terrains = {
            ExpansionType.FARM: Terrain.CLEAR,
            ExpansionType.LUMBER_MILL: Terrain.FOREST,
            ExpansionType.OIL_RIG: Terrain.OCEAN
        }
        return terrains.get(self.type, '')
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'type': self.type.value,
            'typeName': self.type_name,
            'location': self.location,
            'baseId': self.base_id
        }
    
    @classmethod
    def from_hex_data(cls, expansion_id: int, exp_type: ExpansionType, 
                      hex_id: int, base_id: int) -> 'Expansion':
        """Create an Expansion from hex data parsing."""
        return cls(
            id=expansion_id,
            type=exp_type,
            location=hex_id,
            base_id=base_id
        )

