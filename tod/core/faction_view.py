"""
Faction View for Tides of Darkness.

Provides filtered game state from a specific faction's perspective.
This is what gets sent to clients - they only see what their faction can see.
"""
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field

from .game_state import GameState
from .vision import compute_visible_hexes
from .models import Unit, Hex, Base, Faction
from .models.enums import FactionId


@dataclass
class FactionView:
    """
    A filtered view of the game state from one faction's perspective.
    
    This contains only the information that faction is allowed to know.
    """
    # The viewing faction
    faction_id: int
    faction: Optional[Faction] = None
    
    # Vision data
    visible_hexes: Set[int] = field(default_factory=set)
    
    # Own assets (full information)
    own_units: Dict[int, Unit] = field(default_factory=dict)
    own_bases: Dict[int, Base] = field(default_factory=dict)
    allied_units: Dict[int, Unit] = field(default_factory=dict)
    allied_bases: Dict[int, Base] = field(default_factory=dict)
    
    # Visible enemy assets (may have limited information)
    visible_enemy_units: Dict[int, Unit] = field(default_factory=dict)
    visible_enemy_bases: Dict[int, Base] = field(default_factory=dict)
    
    # Hex data (only for visible hexes)
    hexes: Dict[int, Hex] = field(default_factory=dict)
    
    # Summary stats
    @property
    def total_visible_units(self) -> int:
        return len(self.own_units) + len(self.allied_units) + len(self.visible_enemy_units)
    
    @property
    def total_visible_bases(self) -> int:
        return len(self.own_bases) + len(self.allied_bases) + len(self.visible_enemy_bases)


def get_faction_view(state: GameState, faction_id: int) -> FactionView:
    """
    Generate a filtered view of the game state for a specific faction.
    
    Args:
        state: The complete game state
        faction_id: The faction ID to generate the view for
    
    Returns:
        FactionView containing only what this faction can see
    """
    view = FactionView(faction_id=faction_id)
    
    # Get the faction object
    faction = state.get_faction(faction_id)
    if not faction:
        return view
    
    view.faction = faction
    faction_initiative = faction.initiative
    
    # Compute visible hexes
    view.visible_hexes = compute_visible_hexes(state, faction_id)
    
    # Determine allied factions (same initiative)
    allied_faction_ids = set()
    for fid, f in state.factions.items():
        if f.initiative == faction_initiative:
            fid_val = fid.value if hasattr(fid, 'value') else fid
            allied_faction_ids.add(fid_val)
    
    # Categorize units
    for unit_id, unit in state.units.items():
        if not unit.alive:
            continue
            
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        
        if unit_faction == faction_id:
            # Own unit - full information, always visible
            view.own_units[unit_id] = unit
        elif unit_faction in allied_faction_ids:
            # Allied unit - full information, always visible
            view.allied_units[unit_id] = unit
        elif unit.location in view.visible_hexes:
            # Enemy unit in visible hex
            # TODO: Filter sensitive information (e.g., exact HP?)
            view.visible_enemy_units[unit_id] = unit
    
    # Categorize bases
    for base_id, base in state.bases.items():
        base_faction = base.faction.value if hasattr(base.faction, 'value') else base.faction
        
        if base_faction == faction_id:
            # Own base - full information
            view.own_bases[base_id] = base
        elif base_faction in allied_faction_ids:
            # Allied base - full information
            view.allied_bases[base_id] = base
        elif base.location in view.visible_hexes:
            # Enemy base in visible hex
            view.visible_enemy_bases[base_id] = base
    
    # Include hex data for visible hexes
    for hex_id in view.visible_hexes:
        if hex_id in state.hexes:
            view.hexes[hex_id] = state.hexes[hex_id]
    
    return view


def get_omniscient_view(state: GameState) -> FactionView:
    """
    Generate an omniscient view of the game state (sees everything).
    
    Used for admin/testing purposes (Alex's sandbox mode).
    """
    view = FactionView(faction_id=-1)  # -1 = omniscient
    
    # All hexes are visible
    view.visible_hexes = set(state.hexes.keys())
    
    # All units (as "own" for full visibility)
    for unit_id, unit in state.units.items():
        if unit.alive:
            view.own_units[unit_id] = unit
    
    # All bases
    for base_id, base in state.bases.items():
        view.own_bases[base_id] = base
    
    # All hexes
    view.hexes = dict(state.hexes)
    
    return view


def faction_view_to_dict(view: FactionView) -> Dict[str, Any]:
    """
    Convert a FactionView to a dictionary for JSON serialization.
    
    This is what gets sent over the API.
    """
    def unit_to_dict(unit: Unit) -> Dict:
        return {
            "id": unit.id,
            "name": unit.name,
            "faction": unit.faction.value if hasattr(unit.faction, 'value') else unit.faction,
            "location": unit.location,
            "hp": unit.hp,
            "maxHp": unit.max_hp,
            "combat": unit.combat,
            "tier": unit.tier,
            "category": unit.category.value if hasattr(unit.category, 'value') else unit.category,
            "unitType": unit.unit_type.value if hasattr(unit.unit_type, 'value') else unit.unit_type,
            "movement": unit.movement_remaining,
            "maxMovement": unit.movement_max,
            "vision": unit.vision,
            "alive": unit.alive,
        }
    
    def base_to_dict(base: Base) -> Dict:
        return {
            "id": base.id,
            "name": base.name,
            "location": base.location,
            "faction": base.faction.value if hasattr(base.faction, 'value') else base.faction,
            "tier": base.tier,
            "gold": base.gold,
            "lumber": base.lumber,
            "oil": base.oil,
        }
    
    def hex_to_dict(hex_obj: Hex) -> Dict:
        return {
            "id": hex_obj.id,
            "terrain": hex_obj.terrain,
            "building": hex_obj.building.value if hasattr(hex_obj.building, 'value') else hex_obj.building,
            "hasOil": hex_obj.has_oil,
            "gold": hex_obj.gold,
        }
    
    result = {
        "factionId": view.faction_id,
        "faction": {
            "id": view.faction.id.value if view.faction and hasattr(view.faction.id, 'value') else (view.faction.id if view.faction else None),
            "name": view.faction.name if view.faction else "Omniscient",
            "initiative": view.faction.initiative if view.faction else -1,
        } if view.faction or view.faction_id == -1 else None,
        "visibleHexes": list(view.visible_hexes),
        "ownUnits": [unit_to_dict(u) for u in view.own_units.values()],
        "alliedUnits": [unit_to_dict(u) for u in view.allied_units.values()],
        "enemyUnits": [unit_to_dict(u) for u in view.visible_enemy_units.values()],
        "ownBases": [base_to_dict(b) for b in view.own_bases.values()],
        "alliedBases": [base_to_dict(b) for b in view.allied_bases.values()],
        "enemyBases": [base_to_dict(b) for b in view.visible_enemy_bases.values()],
        "hexes": [hex_to_dict(h) for h in view.hexes.values()],
        "summary": {
            "visibleHexCount": len(view.visible_hexes),
            "ownUnitCount": len(view.own_units),
            "alliedUnitCount": len(view.allied_units),
            "enemyUnitCount": len(view.visible_enemy_units),
            "ownBaseCount": len(view.own_bases),
            "alliedBaseCount": len(view.allied_bases),
            "enemyBaseCount": len(view.visible_enemy_bases),
        }
    }
    
    return result

