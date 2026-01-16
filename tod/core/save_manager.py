"""
Save Manager for Tides of Darkness.

Handles saving and loading complete game state to/from JSON files.
Saves include metadata (name, notes, timestamp, turn info) for easy identification.
"""
import json
import os
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from .game_state import GameState, TurnState, RoundSide, GamePhase
from .models import (
    Unit, UnitStats, Hex, Base, Faction, Road, Caravan, Expansion,
    FactionId, UnitCategory, UnitType, Terrain, ExpansionType,
    FactionOrders, MovementOrder, RangedfireOrder, BoardTransportOrder,
    BuildBaseOrder, BuildUnitOrder, UpgradeBaseOrder, ExpandOrder,
    HarvestOrder, SendResourcesOrder, EstablishCaravanOrder, CommerceOrder,
    RestUnitOrder, AssistConstructionOrder, GiveBaseOrder, GiveExpansionOrder,
    DestroyBaseOrder
)
from .models.caravan import CaravanTerrainType
from .order_manager import get_order_manager

logger = logging.getLogger(__name__)

# Default saves directory (relative to project root)
SAVES_DIR = Path(__file__).parent.parent.parent / "saves"


@dataclass
class SaveMetadata:
    """Metadata for a save file."""
    name: str                      # User-provided save name
    notes: str = ""                # Optional user notes
    created_at: str = ""           # ISO timestamp when saved
    round_number: int = 0          # Game round at time of save
    round_side: str = ""           # HORDE or ALLIANCE
    initiative: int = 0            # Current initiative at save time
    turn_number: int = 0           # Sequential turn number
    phase: str = ""                # Current game phase
    unit_count: int = 0            # Number of alive units
    base_count: int = 0            # Number of bases
    version: str = "1.0"           # Save format version
    config_modified: bool = False  # Whether config differs from defaults
    config_notes: str = ""         # Summary of config changes if any
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SaveMetadata':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SaveManager:
    """
    Manages saving and loading game state.
    
    Save files are JSON with:
    - metadata: SaveMetadata with name, notes, and game info
    - state: Complete serialized GameState
    """
    
    def __init__(self, saves_dir: Optional[Path] = None):
        self.saves_dir = saves_dir or SAVES_DIR
        self.saves_dir.mkdir(parents=True, exist_ok=True)
    
    def _sanitize_filename(self, name: str) -> str:
        """Convert a save name to a safe filename."""
        # Replace problematic characters
        safe = name.replace(' ', '_').replace('/', '-').replace('\\', '-')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-.')
        return safe[:100]  # Limit length
    
    def _get_save_path(self, name: str) -> Path:
        """Get the full path for a save file."""
        filename = self._sanitize_filename(name) + ".json"
        return self.saves_dir / filename
    
    # ========== Serialization ==========
    
    def _serialize_enum(self, value: Any) -> Any:
        """Convert enum to serializable value."""
        if hasattr(value, 'value'):
            return value.value
        return value
    
    def _serialize_unit(self, unit: Unit) -> dict:
        """Serialize a Unit to dict."""
        return {
            'id': unit.id,
            'name': unit.name,
            'faction': self._serialize_enum(unit.faction),
            'max_hp': unit.max_hp,
            'combat': unit.combat,
            'category': self._serialize_enum(unit.category),
            'unit_type': self._serialize_enum(unit.unit_type),
            'light_armor_max': unit.light_armor_max,
            'heavy_armor': unit.heavy_armor,
            'natural_armor': unit.natural_armor,
            'movement_max': unit.movement_max,
            'vision': unit.vision,
            'stealth': unit.stealth,
            'can_rangedfire': unit.can_rangedfire,
            'hp': unit.hp,
            'location': unit.location,
            'alive': unit.alive,
            'tier': unit.tier,
            'tier_1_ability': unit.tier_1_ability,
            'tier_2_ability': unit.tier_2_ability,
            'tier_3_ability': unit.tier_3_ability,
            'tier_4_ability': unit.tier_4_ability,
            'tier_1_data': unit.tier_1_data,
            'tier_2_data': unit.tier_2_data,
            'tier_3_data': unit.tier_3_data,
            'tier_4_data': unit.tier_4_data,
            'hex_duration': unit.hex_duration,
            'fired': unit.fired,
            'light_armor_current': unit.light_armor_current,
            'armor_broken': unit.armor_broken,
            'terrain_bonus': unit.terrain_bonus,
            'flank_bonus': unit.flank_bonus,
            'hold_bonus': unit.hold_bonus,
            'combat_start': unit.combat_start,
            'movement_remaining': unit.movement_remaining,
            'road_move_remaining': unit.road_move_remaining,
            'road_move_only': unit.road_move_only,
            'previous_location': unit.previous_location,
            'transport_slot_1': unit.transport_slot_1,
            'transport_slot_2': unit.transport_slot_2,
            'transport_slot_3': unit.transport_slot_3,
            'aboard_transport_id': unit.aboard_transport_id,
        }
    
    def _serialize_base(self, base: Base) -> dict:
        """Serialize a Base to dict."""
        return {
            'id': base.id,
            'name': base.name,
            'location': base.location,
            'faction': self._serialize_enum(base.faction),
            'tier': base.tier,
            'gold': base.gold,
            'lumber': base.lumber,
            'oil': base.oil,
            'actions': base.actions,
            'expansions': base.expansions,
        }
    
    def _serialize_faction(self, faction: Faction) -> dict:
        """Serialize a Faction to dict."""
        return {
            'id': self._serialize_enum(faction.id),
            'name': faction.name,
            'is_defeated': faction.is_defeated,
            'initiative': faction.initiative,
            'membership': faction.membership,
            'is_leader': faction.is_leader,
            'leader_vote': faction.leader_vote,
            'alliance_votes': faction.alliance_votes,
            'horde_decision': faction.horde_decision,
            'warchief_decision': faction.warchief_decision,
            'vassal_of': self._serialize_enum(faction.vassal_of) if faction.vassal_of is not None else None,
        }
    
    def _serialize_hex_side(self, side) -> dict:
        """Serialize a HexSide to dict."""
        return {
            'terrain': side.terrain,
            'control': side.control,
        }
    
    def _serialize_hex(self, hex_obj: Hex) -> dict:
        """Serialize a Hex to dict."""
        return {
            'id': hex_obj.id,
            'terrain': self._serialize_enum(hex_obj.terrain),
            'north': self._serialize_hex_side(hex_obj.north),
            'northeast': self._serialize_hex_side(hex_obj.northeast),
            'southeast': self._serialize_hex_side(hex_obj.southeast),
            'south': self._serialize_hex_side(hex_obj.south),
            'southwest': self._serialize_hex_side(hex_obj.southwest),
            'northwest': self._serialize_hex_side(hex_obj.northwest),
            'building': self._serialize_enum(hex_obj.building),
            'has_oil': hex_obj.has_oil,
            'farm': hex_obj.farm,
            'mill': hex_obj.mill,
            'rig': hex_obj.rig,
            'gold': hex_obj.gold,
            'new_combat': hex_obj.new_combat,
            'battle_fought': hex_obj.battle_fought,
            'assisted': hex_obj.assisted,
            'expansion_owner': hex_obj.expansion_owner,
        }
    
    def _serialize_road(self, road: Road) -> dict:
        """Serialize a Road to dict."""
        return {
            'hex_id': road.hex_id,
            'north': road.north,
            'south': road.south,
            'northwest': road.northwest,
            'northeast': road.northeast,
            'southwest': road.southwest,
            'southeast': road.southeast,
        }
    
    def _serialize_caravan(self, caravan: Caravan) -> dict:
        """Serialize a Caravan to dict."""
        return {
            'id': caravan.id,
            'origin_base_id': caravan.origin_base_id,
            'destination_base_id': caravan.destination_base_id,
            'initiative': caravan.initiative,
            'path': caravan.path,
            'terrain_type': self._serialize_enum(caravan.terrain_type),
        }
    
    def _serialize_expansion(self, expansion: Expansion) -> dict:
        """Serialize an Expansion to dict."""
        return {
            'id': expansion.id,
            'type': self._serialize_enum(expansion.type),
            'location': expansion.location,
            'base_id': expansion.base_id,
        }
    
    def _serialize_unit_stats(self, stats: UnitStats) -> dict:
        """Serialize UnitStats to dict."""
        return {
            'name': stats.name,
            'max_hp': stats.max_hp,
            'combat': stats.combat,
            'category': self._serialize_enum(stats.category),
            'unit_type': self._serialize_enum(stats.unit_type),
            'light_armor': stats.light_armor,
            'heavy_armor': stats.heavy_armor,
            'natural_armor': stats.natural_armor,
            'movement': stats.movement,
            'vision': stats.vision,
            'stealth': stats.stealth,
            'gold_cost': stats.gold_cost,
            'lumber_cost': stats.lumber_cost,
            'oil_cost': stats.oil_cost,
            'min_tier': stats.min_tier,
        }
    
    def _serialize_turn_state(self, turn: TurnState) -> dict:
        """Serialize TurnState to dict."""
        return {
            'round_number': turn.round_number,
            'round_side': turn.round_side.value,
            'current_initiative': turn.current_initiative,
            'phase': turn.phase.name,
            'completed_initiatives': list(turn.completed_initiatives),
            'orders_submitted': list(turn.orders_submitted),
        }
    
    def _key_to_str(self, key) -> str:
        """Convert a key to a string, handling enums properly."""
        if hasattr(key, 'value'):
            return str(key.value)
        return str(key)
    
    def serialize_state(self, state: GameState) -> dict:
        """Serialize the entire GameState to a dict."""
        return {
            # Core entities - all keys need _key_to_str for enum handling
            'units': {self._key_to_str(k): self._serialize_unit(v) for k, v in state.units.items()},
            'hexes': {self._key_to_str(k): self._serialize_hex(v) for k, v in state.hexes.items()},
            'bases': {self._key_to_str(k): self._serialize_base(v) for k, v in state.bases.items()},
            'factions': {self._key_to_str(k): self._serialize_faction(v) for k, v in state.factions.items()},
            'roads': {self._key_to_str(k): self._serialize_road(v) for k, v in state.roads.items()},
            'caravans': [self._serialize_caravan(c) for c in state.caravans],
            'expansions': {self._key_to_str(k): self._serialize_expansion(v) for k, v in state.expansions.items()},
            
            # Unit stats (templates) - keys are strings (unit names)
            'unit_stats': {k: self._serialize_unit_stats(v) for k, v in state.unit_stats.items()},
            
            # Turn state
            'turn': self._serialize_turn_state(state.turn),
            
            # Food tracking - keys could be FactionId enums
            'food_surplus': {self._key_to_str(k): v for k, v in state.food_surplus.items()},
            'food_surplus_after': {self._key_to_str(k): v for k, v in state.food_surplus_after.items()},
            
            # Buildables - keys are faction IDs
            'faction_buildables': {
                self._key_to_str(k): v for k, v in state.faction_buildables.items()
            },
            
            # Pending orders - keys are base IDs (integers)
            'pending_base_orders': {
                self._key_to_str(k): v for k, v in state.pending_base_orders.items()
            },
            
            # Vision - keys could be FactionId enums
            'visible_hexes': {
                self._key_to_str(k): list(v) for k, v in state.visible_hexes.items()
            },
            
            # Game log
            'game_log': self._serialize_game_log(),
            
            # Pending orders (from order manager)
            'faction_orders': self._serialize_faction_orders(),
            
            # Combat manager state (active combats with hexside control)
            'combat_manager': self._serialize_combat_manager(),
        }
    
    def _serialize_game_log(self) -> dict:
        """Serialize the game log."""
        from .game_log import get_game_log
        return get_game_log().to_dict()
    
    def _serialize_faction_orders(self) -> dict:
        """Serialize all pending orders from the order manager."""
        order_manager = get_order_manager()
        result = {}
        
        for faction_id, orders in order_manager.faction_orders.items():
            result[self._key_to_str(faction_id)] = self._serialize_orders(orders)
        
        return result
    
    def _serialize_orders(self, orders: FactionOrders) -> dict:
        """Serialize a FactionOrders object."""
        faction_id = orders.faction_id.value if hasattr(orders.faction_id, 'value') else orders.faction_id
        return {
            'faction_id': faction_id,
            # Unit orders
            'movement_orders': [
                {'unit_id': o.unit_id, 'path': o.path} 
                for o in orders.movement_orders
            ],
            'rangedfire_orders': [
                {'unit_id': o.unit_id, 'target_hex': o.target_hex}
                for o in orders.rangedfire_orders
            ],
            'board_transport_orders': [
                {'unit_id': o.unit_id, 'transport_id': o.transport_id}
                for o in orders.board_transport_orders
            ],
            'build_base_orders': [
                {'unit_id': o.unit_id}
                for o in orders.build_base_orders
            ],
            # Base orders
            'build_unit_orders': [
                {'base_id': o.base_id, 'unit_type': o.unit_type}
                for o in orders.build_unit_orders
            ],
            'upgrade_base_orders': [
                {'base_id': o.base_id}
                for o in orders.upgrade_base_orders
            ],
            'expand_orders': [
                {'base_id': o.base_id, 'hex_id': o.hex_id, 'expansion_type': o.expansion_type.value}
                for o in orders.expand_orders
            ],
            'harvest_orders': [
                {'base_id': o.base_id}
                for o in orders.harvest_orders
            ],
            'send_resources_orders': [
                {'origin_base': o.origin_base, 'destination_base': o.destination_base,
                 'gold': o.gold, 'lumber': o.lumber, 'oil': o.oil}
                for o in orders.send_resources_orders
            ],
            'establish_caravan_orders': [
                {'origin_base': o.origin_base, 'destination_base': o.destination_base, 'path': o.path}
                for o in orders.establish_caravan_orders
            ],
            'commerce_orders': [
                {'base_id': o.base_id, 'resource_type': o.resource_type.value}
                for o in orders.commerce_orders
            ],
            'rest_unit_orders': [
                {'base_id': o.base_id, 'unit_id': o.unit_id}
                for o in orders.rest_unit_orders
            ],
            'assist_construction_orders': [
                {'base_id': o.base_id, 'unit_id': o.unit_id}
                for o in orders.assist_construction_orders
            ],
            'give_base_orders': [
                {'base_id': o.base_id, 'recipient_faction': o.recipient_faction}
                for o in orders.give_base_orders
            ],
            'give_expansion_orders': [
                {'expansion_hex': o.expansion_hex, 'recipient_base': o.recipient_base, 'owner_base': o.owner_base}
                for o in orders.give_expansion_orders
            ],
            'destroy_base_orders': [
                {'base_id': o.base_id}
                for o in orders.destroy_base_orders
            ],
        }
    
    def _serialize_combat_manager(self) -> dict:
        """Serialize combat manager state (active combats with hexside control)."""
        from .combat_manager import get_combat_manager
        return get_combat_manager().to_dict()
    
    # ========== Deserialization ==========
    
    def _deserialize_unit(self, data: dict) -> Unit:
        """Deserialize a Unit from dict."""
        return Unit(
            id=data['id'],
            name=data['name'],
            faction=FactionId(data['faction']),
            max_hp=data['max_hp'],
            combat=data['combat'],
            category=UnitCategory(data['category']),
            unit_type=UnitType(data['unit_type']),
            light_armor_max=data['light_armor_max'],
            heavy_armor=data['heavy_armor'],
            natural_armor=data['natural_armor'],
            movement_max=data['movement_max'],
            vision=data['vision'],
            stealth=data.get('stealth', 0),
            can_rangedfire=data.get('can_rangedfire', False),  # __post_init__ will set True for INTERIOR_SIEGE
            hp=data['hp'],
            location=data['location'],
            alive=data['alive'],
            tier=data['tier'],
            tier_1_ability=data.get('tier_1_ability', 'none'),
            tier_2_ability=data.get('tier_2_ability', 'none'),
            tier_3_ability=data.get('tier_3_ability', 'none'),
            tier_4_ability=data.get('tier_4_ability', 'none'),
            tier_1_data=data.get('tier_1_data', 0),
            tier_2_data=data.get('tier_2_data', 0),
            tier_3_data=data.get('tier_3_data', 0),
            tier_4_data=data.get('tier_4_data', 0),
            hex_duration=data.get('hex_duration', 0),
            fired=data.get('fired', False),
            light_armor_current=data.get('light_armor_current', data['light_armor_max']),
            armor_broken=data.get('armor_broken', False),
            terrain_bonus=data.get('terrain_bonus', 0),
            flank_bonus=data.get('flank_bonus', 0),
            hold_bonus=data.get('hold_bonus', 0),
            combat_start=data.get('combat_start', 0),
            movement_remaining=data.get('movement_remaining', data['movement_max']),
            road_move_remaining=data.get('road_move_remaining', 1),
            road_move_only=data.get('road_move_only', True),
            previous_location=data.get('previous_location', 0),
            transport_slot_1=data.get('transport_slot_1', -1),
            transport_slot_2=data.get('transport_slot_2', -1),
            transport_slot_3=data.get('transport_slot_3', -1),
            aboard_transport_id=data.get('aboard_transport_id', -1),
        )
    
    def _deserialize_base(self, data: dict) -> Base:
        """Deserialize a Base from dict."""
        base = Base(
            id=data['id'],
            name=data['name'],
            location=data['location'],
            faction=FactionId(data['faction']),
            tier=data['tier'],
            gold=data['gold'],
            lumber=data['lumber'],
            oil=data['oil'],
            actions=data.get('actions', 0),
        )
        base.expansions = data.get('expansions', [])
        return base
    
    def _deserialize_faction(self, data: dict) -> Faction:
        """Deserialize a Faction from dict."""
        # Handle vassal_of - None means independent
        vassal_of = None
        if data.get('vassal_of') is not None:
            vassal_of = FactionId(data['vassal_of'])
        
        return Faction(
            id=FactionId(data['id']),
            name=data['name'],
            is_defeated=data['is_defeated'],
            initiative=data['initiative'],
            membership=data.get('membership', 0),
            is_leader=data.get('is_leader', False),
            leader_vote=data.get('leader_vote', 0),
            alliance_votes=data.get('alliance_votes', ''),
            horde_decision=data.get('horde_decision', ''),
            warchief_decision=data.get('warchief_decision', 0),
            vassal_of=vassal_of,
        )
    
    def _deserialize_hex_side(self, data: dict):
        """Deserialize a HexSide from dict."""
        from .models.hex import HexSide
        return HexSide(
            terrain=data.get('terrain', ''),
            control=data.get('control', 0),
        )
    
    def _deserialize_hex(self, data: dict) -> Hex:
        """Deserialize a Hex from dict."""
        from .models.hex import HexSide
        from .models.enums import BuildingType
        
        # Handle terrain - could be string or enum value
        terrain = data['terrain']
        if isinstance(terrain, int):
            terrain = Terrain(terrain)
        elif isinstance(terrain, str) and terrain.isdigit():
            terrain = Terrain(int(terrain))
        # else keep as string (legacy format)
        
        # Handle building type
        building = data.get('building', 0)
        if isinstance(building, int):
            building = BuildingType(building) if building in [0, 1, 2, 3] else BuildingType.NONE
        
        hex_obj = Hex(
            id=data['id'],
            terrain=terrain,
            building=building,
            has_oil=data.get('has_oil', False),
            farm=data.get('farm', -1),
            mill=data.get('mill', -1),
            rig=data.get('rig', -1),
            gold=data.get('gold', 0),
            new_combat=data.get('new_combat', False),
            battle_fought=data.get('battle_fought', False),
            assisted=data.get('assisted', False),
            expansion_owner=data.get('expansion_owner', 0),
        )
        
        # Deserialize hex sides if present
        if 'north' in data:
            hex_obj.north = self._deserialize_hex_side(data['north'])
        if 'northeast' in data:
            hex_obj.northeast = self._deserialize_hex_side(data['northeast'])
        if 'southeast' in data:
            hex_obj.southeast = self._deserialize_hex_side(data['southeast'])
        if 'south' in data:
            hex_obj.south = self._deserialize_hex_side(data['south'])
        if 'southwest' in data:
            hex_obj.southwest = self._deserialize_hex_side(data['southwest'])
        if 'northwest' in data:
            hex_obj.northwest = self._deserialize_hex_side(data['northwest'])
        
        return hex_obj
    
    def _deserialize_road(self, data: dict) -> Road:
        """Deserialize a Road from dict."""
        return Road(
            hex_id=data['hex_id'],
            north=data.get('north', 0),
            south=data.get('south', 0),
            northwest=data.get('northwest', 0),
            northeast=data.get('northeast', 0),
            southwest=data.get('southwest', 0),
            southeast=data.get('southeast', 0),
        )
    
    def _deserialize_caravan(self, data: dict) -> Caravan:
        """Deserialize a Caravan from dict."""
        terrain_type = data.get('terrain_type', 'land')
        if isinstance(terrain_type, str):
            terrain_type = CaravanTerrainType(terrain_type)
        return Caravan(
            id=data['id'],
            origin_base_id=data['origin_base_id'],
            destination_base_id=data['destination_base_id'],
            initiative=data['initiative'],
            path=data['path'],
            terrain_type=terrain_type,
        )
    
    def _deserialize_expansion(self, data: dict) -> Expansion:
        """Deserialize an Expansion from dict."""
        exp_type = data['type']
        if isinstance(exp_type, str):
            exp_type = ExpansionType(exp_type)
        return Expansion(
            id=data['id'],
            type=exp_type,
            location=data['location'],
            base_id=data['base_id'],
        )
    
    def _deserialize_unit_stats(self, data: dict) -> UnitStats:
        """Deserialize UnitStats from dict."""
        return UnitStats(
            name=data['name'],
            max_hp=data['max_hp'],
            combat=data['combat'],
            category=UnitCategory(data['category']),
            unit_type=UnitType(data['unit_type']),
            light_armor=data['light_armor'],
            heavy_armor=data['heavy_armor'],
            natural_armor=data['natural_armor'],
            movement=data['movement'],
            vision=data['vision'],
            stealth=data.get('stealth', 0),
            gold_cost=data.get('gold_cost', 0),
            lumber_cost=data.get('lumber_cost', 0),
            oil_cost=data.get('oil_cost', 0),
            min_tier=data.get('min_tier', 1),
        )
    
    def _deserialize_turn_state(self, data: dict) -> TurnState:
        """Deserialize TurnState from dict."""
        turn = TurnState(
            round_number=data['round_number'],
            round_side=RoundSide(data['round_side']),
            current_initiative=data['current_initiative'],
            phase=GamePhase[data['phase']],
        )
        turn.completed_initiatives = set(data.get('completed_initiatives', []))
        turn.orders_submitted = set(data.get('orders_submitted', []))
        return turn
    
    def deserialize_state(self, data: dict, state: GameState) -> None:
        """
        Deserialize data into an existing GameState object.
        
        Modifies the state in-place rather than creating a new one,
        so we preserve any references to the state object.
        """
        # Clear existing collections
        state.units.clear()
        state.hexes.clear()
        state.bases.clear()
        state.factions.clear()
        state.roads.clear()
        state.caravans.clear()
        state.expansions.clear()
        state.unit_stats.clear()
        state.visible_hexes.clear()
        state.food_surplus.clear()
        state.food_surplus_after.clear()
        state.faction_buildables.clear()
        state.pending_base_orders.clear()
        
        # Load units
        for key, unit_data in data.get('units', {}).items():
            unit = self._deserialize_unit(unit_data)
            state.units[int(key)] = unit
        
        # Load hexes
        for key, hex_data in data.get('hexes', {}).items():
            hex_obj = self._deserialize_hex(hex_data)
            state.hexes[int(key)] = hex_obj
        
        # Load bases
        for key, base_data in data.get('bases', {}).items():
            base = self._deserialize_base(base_data)
            state.bases[int(key)] = base
        
        # Load factions
        for key, faction_data in data.get('factions', {}).items():
            faction = self._deserialize_faction(faction_data)
            state.factions[int(key)] = faction
        
        # Load roads
        for key, road_data in data.get('roads', {}).items():
            road = self._deserialize_road(road_data)
            state.roads[int(key)] = road
        
        # Load caravans
        for caravan_data in data.get('caravans', []):
            caravan = self._deserialize_caravan(caravan_data)
            state.caravans.append(caravan)
        
        # Load expansions
        for key, exp_data in data.get('expansions', {}).items():
            expansion = self._deserialize_expansion(exp_data)
            state.expansions[int(key)] = expansion
        
        # Load unit stats
        for name, stats_data in data.get('unit_stats', {}).items():
            stats = self._deserialize_unit_stats(stats_data)
            state.unit_stats[name] = stats
        
        # Load turn state
        if 'turn' in data:
            state.turn = self._deserialize_turn_state(data['turn'])
        
        # Load food tracking
        for key, value in data.get('food_surplus', {}).items():
            state.food_surplus[int(key)] = value
        for key, value in data.get('food_surplus_after', {}).items():
            state.food_surplus_after[int(key)] = value
        
        # Load buildables
        for key, value in data.get('faction_buildables', {}).items():
            state.faction_buildables[int(key)] = value
        
        # Load pending orders
        for key, value in data.get('pending_base_orders', {}).items():
            state.pending_base_orders[int(key)] = value
        
        # Load vision
        for key, hexes in data.get('visible_hexes', {}).items():
            state.visible_hexes[int(key)] = set(hexes)
        
        # Load game log
        if 'game_log' in data:
            self._deserialize_game_log(data['game_log'])
        
        # Load faction orders (with validation)
        if 'faction_orders' in data:
            self._deserialize_faction_orders(data['faction_orders'], state)
        
        # Load combat manager state (active combats with hexside control)
        if 'combat_manager' in data:
            self._deserialize_combat_manager(data['combat_manager'], state)
    
    def _deserialize_combat_manager(self, data: dict, state: GameState) -> None:
        """Deserialize and restore combat manager state."""
        from .combat_manager import CombatManager, set_combat_manager
        combat_mgr = CombatManager.from_dict(data, state)
        set_combat_manager(combat_mgr)
        logger.info(f"Loaded combat manager with {len(combat_mgr.active_combats)} active combats")
    
    def _deserialize_faction_orders(self, data: dict, state: GameState) -> None:
        """Deserialize and restore faction orders with validation."""
        from .models.orders import ExpansionType, ResourceType
        
        order_manager = get_order_manager()
        order_manager.clear_all_orders()  # Start fresh
        
        orders_loaded = 0
        orders_skipped = 0
        
        for faction_id_str, orders_data in data.items():
            faction_id = int(faction_id_str)
            faction_orders = order_manager.get_faction_orders(faction_id)
            
            # Movement orders - validate unit exists and is alive
            for o in orders_data.get('movement_orders', []):
                unit = state.get_unit(o['unit_id'])
                if unit and unit.alive:
                    faction_orders.movement_orders.append(
                        MovementOrder(unit_id=o['unit_id'], path=o['path'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Rangedfire orders
            for o in orders_data.get('rangedfire_orders', []):
                unit = state.get_unit(o['unit_id'])
                if unit and unit.alive:
                    faction_orders.rangedfire_orders.append(
                        RangedfireOrder(unit_id=o['unit_id'], target_hex=o['target_hex'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Board transport orders
            for o in orders_data.get('board_transport_orders', []):
                unit = state.get_unit(o['unit_id'])
                transport = state.get_unit(o['transport_id'])
                if unit and unit.alive and transport and transport.alive:
                    faction_orders.board_transport_orders.append(
                        BoardTransportOrder(unit_id=o['unit_id'], transport_id=o['transport_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Build base orders
            for o in orders_data.get('build_base_orders', []):
                unit = state.get_unit(o['unit_id'])
                if unit and unit.alive:
                    faction_orders.build_base_orders.append(
                        BuildBaseOrder(unit_id=o['unit_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Build unit orders - validate base exists and is not ruins (tier > 0)
            for o in orders_data.get('build_unit_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.build_unit_orders.append(
                        BuildUnitOrder(base_id=o['base_id'], unit_type=o['unit_type'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Upgrade orders
            for o in orders_data.get('upgrade_base_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.upgrade_base_orders.append(
                        UpgradeBaseOrder(base_id=o['base_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Expand orders
            for o in orders_data.get('expand_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.expand_orders.append(
                        ExpandOrder(base_id=o['base_id'], hex_id=o['hex_id'], 
                                   expansion_type=ExpansionType(o['expansion_type']))
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Harvest orders
            for o in orders_data.get('harvest_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.harvest_orders.append(
                        HarvestOrder(base_id=o['base_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Send resources orders
            for o in orders_data.get('send_resources_orders', []):
                origin = state.get_base(o['origin_base'])
                dest = state.get_base(o['destination_base'])
                if origin and origin.tier > 0 and dest and dest.tier > 0:
                    faction_orders.send_resources_orders.append(
                        SendResourcesOrder(
                            origin_base=o['origin_base'], destination_base=o['destination_base'],
                            gold=o['gold'], lumber=o['lumber'], oil=o['oil']
                        )
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Establish caravan orders
            for o in orders_data.get('establish_caravan_orders', []):
                origin = state.get_base(o['origin_base'])
                dest = state.get_base(o['destination_base'])
                if origin and origin.tier > 0 and dest and dest.tier > 0:
                    faction_orders.establish_caravan_orders.append(
                        EstablishCaravanOrder(
                            origin_base=o['origin_base'], destination_base=o['destination_base'],
                            path=o['path']
                        )
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Commerce orders
            for o in orders_data.get('commerce_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.commerce_orders.append(
                        CommerceOrder(base_id=o['base_id'], resource_type=ResourceType(o['resource_type']))
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Rest unit orders
            for o in orders_data.get('rest_unit_orders', []):
                base = state.get_base(o['base_id'])
                unit = state.get_unit(o['unit_id'])
                if base and base.tier > 0 and unit and unit.alive:
                    faction_orders.rest_unit_orders.append(
                        RestUnitOrder(base_id=o['base_id'], unit_id=o['unit_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Assist construction orders
            for o in orders_data.get('assist_construction_orders', []):
                base = state.get_base(o['base_id'])
                unit = state.get_unit(o['unit_id'])
                if base and base.tier > 0 and unit and unit.alive:
                    faction_orders.assist_construction_orders.append(
                        AssistConstructionOrder(base_id=o['base_id'], unit_id=o['unit_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Give base orders
            for o in orders_data.get('give_base_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.give_base_orders.append(
                        GiveBaseOrder(base_id=o['base_id'], recipient_faction=o['recipient_faction'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Give expansion orders
            for o in orders_data.get('give_expansion_orders', []):
                owner_base = state.get_base(o['owner_base'])
                recipient_base = state.get_base(o['recipient_base'])
                if owner_base and owner_base.tier > 0 and recipient_base and recipient_base.tier > 0:
                    faction_orders.give_expansion_orders.append(
                        GiveExpansionOrder(
                            expansion_hex=o['expansion_hex'], 
                            recipient_base=o['recipient_base'],
                            owner_base=o['owner_base']
                        )
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
            
            # Destroy base orders
            for o in orders_data.get('destroy_base_orders', []):
                base = state.get_base(o['base_id'])
                if base and base.tier > 0:
                    faction_orders.destroy_base_orders.append(
                        DestroyBaseOrder(base_id=o['base_id'])
                    )
                    orders_loaded += 1
                else:
                    orders_skipped += 1
        
        logger.info(f"Loaded {orders_loaded} orders, skipped {orders_skipped} invalid orders")
    
    def _deserialize_game_log(self, data: dict) -> None:
        """Deserialize and restore the game log."""
        from .game_log import GameLog, get_game_log
        global _game_log
        
        try:
            # Import and update the global game log
            import tod.core.game_log as game_log_module
            game_log_module._game_log = GameLog.from_dict(data)
            logger.info(f"Loaded game log with {len(game_log_module._game_log.entries)} entries")
        except Exception as e:
            logger.warning(f"Failed to load game log: {e}")
    
    # ========== File Operations ==========
    
    def _get_config_summary(self) -> tuple:
        """
        Check if config differs from defaults and generate summary.
        
        Returns:
            (is_modified: bool, summary: str)
        """
        try:
            from .game_config import get_game_config, GameConfig
            
            current = get_game_config()
            defaults = GameConfig()  # Fresh instance with defaults
            
            current_flat = current.to_flat_dict()
            default_flat = defaults.to_flat_dict()
            
            changes = []
            for key, value in current_flat.items():
                if default_flat.get(key) != value:
                    changes.append(f"{key}={value}")
            
            if changes:
                # Limit to first 5 changes for summary
                summary = ", ".join(changes[:5])
                if len(changes) > 5:
                    summary += f" (+{len(changes) - 5} more)"
                return True, summary
            
            return False, ""
        except Exception as e:
            logger.warning(f"Could not get config summary: {e}")
            return False, ""
    
    def save_game(self, state: GameState, name: str, notes: str = "") -> dict:
        """
        Save the current game state to a file.
        
        Args:
            state: The GameState to save
            name: User-provided name for the save
            notes: Optional notes/description
            
        Returns:
            Dict with success status and file info
        """
        try:
            # Get config status
            config_modified, config_notes = self._get_config_summary()
            
            # Create metadata
            metadata = SaveMetadata(
                name=name,
                notes=notes,
                created_at=datetime.now().isoformat(),
                round_number=state.turn.round_number,
                round_side=state.turn.round_side.value,
                initiative=state.turn.current_initiative,
                turn_number=state.turn.turn_number,
                phase=state.turn.phase.name,
                unit_count=len([u for u in state.units.values() if u.alive]),
                base_count=len(state.bases),
                config_modified=config_modified,
                config_notes=config_notes,
            )
            
            # Serialize state
            state_data = self.serialize_state(state)
            
            # Combine into save file
            save_data = {
                'metadata': metadata.to_dict(),
                'state': state_data
            }
            
            # Write to file
            save_path = self._get_save_path(name)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info(f"Game saved to {save_path}")
            
            return {
                'success': True,
                'message': f'Game saved as "{name}"',
                'filename': save_path.name,
                'path': str(save_path),
                'metadata': metadata.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return {
                'success': False,
                'message': f'Failed to save: {str(e)}'
            }
    
    def load_game(self, state: GameState, name: str) -> dict:
        """
        Load a saved game into the provided GameState.
        
        Args:
            state: The GameState to load into (modified in-place)
            name: Name of the save to load
            
        Returns:
            Dict with success status and loaded metadata
        """
        try:
            save_path = self._get_save_path(name)
            
            if not save_path.exists():
                # Try exact filename match
                for f in self.saves_dir.iterdir():
                    if f.stem == name or f.name == name:
                        save_path = f
                        break
                else:
                    return {
                        'success': False,
                        'message': f'Save "{name}" not found'
                    }
            
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # Extract metadata and state
            metadata = SaveMetadata.from_dict(save_data.get('metadata', {}))
            state_data = save_data.get('state', {})
            
            # Deserialize into state
            self.deserialize_state(state_data, state)
            
            logger.info(f"Game loaded from {save_path}")
            
            return {
                'success': True,
                'message': f'Loaded save "{metadata.name}"',
                'metadata': metadata.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to load game: {e}")
            return {
                'success': False,
                'message': f'Failed to load: {str(e)}'
            }
    
    def list_saves(self) -> List[dict]:
        """
        List all available saves with their metadata.
        
        Returns:
            List of save metadata dicts, sorted by creation time (newest first)
        """
        saves = []
        
        for save_file in self.saves_dir.glob("*.json"):
            try:
                with open(save_file, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                
                metadata = save_data.get('metadata', {})
                metadata['filename'] = save_file.name
                saves.append(metadata)
                
            except Exception as e:
                logger.warning(f"Failed to read save {save_file}: {e}")
                # Include minimal info for broken saves
                saves.append({
                    'name': save_file.stem,
                    'filename': save_file.name,
                    'error': str(e)
                })
        
        # Sort by creation time, newest first
        saves.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return saves
    
    def delete_save(self, name: str) -> dict:
        """
        Delete a save file.
        
        Args:
            name: Name of the save to delete
            
        Returns:
            Dict with success status
        """
        try:
            save_path = self._get_save_path(name)
            
            if not save_path.exists():
                # Try exact filename match
                for f in self.saves_dir.iterdir():
                    if f.stem == name or f.name == name:
                        save_path = f
                        break
                else:
                    return {
                        'success': False,
                        'message': f'Save "{name}" not found'
                    }
            
            save_path.unlink()
            logger.info(f"Deleted save: {save_path}")
            
            return {
                'success': True,
                'message': f'Deleted save "{name}"'
            }
            
        except Exception as e:
            logger.error(f"Failed to delete save: {e}")
            return {
                'success': False,
                'message': f'Failed to delete: {str(e)}'
            }
    
    def get_save_metadata(self, name: str) -> Optional[dict]:
        """Get metadata for a specific save without loading full state."""
        try:
            save_path = self._get_save_path(name)
            if not save_path.exists():
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            metadata = save_data.get('metadata', {})
            metadata['filename'] = save_path.name
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to read save metadata: {e}")
            return None


# Singleton instance
_save_manager: Optional[SaveManager] = None


def get_save_manager() -> SaveManager:
    """Get the global SaveManager instance."""
    global _save_manager
    if _save_manager is None:
        _save_manager = SaveManager()
    return _save_manager

