"""
Order models for Tides of Darkness.

Orders are instructions submitted by players each turn. There are two categories:
1. Unit Orders - Commands given to individual units (move, attack, board transport)
2. Base Orders - Commands given to bases (build, upgrade, trade, expand)

Orders are collected during the order phase and resolved during turn resolution.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum, auto
from .enums import FactionId


# =============================================================================
# ENUMS
# =============================================================================

class UnitOrderType(Enum):
    """Types of orders that can be given to units."""
    MOVEMENT = auto()
    RANGEDFIRE = auto()
    BOARD_TRANSPORT = auto()
    BUILD_BASE = auto()


class BaseOrderType(Enum):
    """Types of orders that can be given to bases."""
    BUILD_UNIT = auto()
    UPGRADE_BASE = auto()
    EXPAND = auto()
    HARVEST = auto()
    SEND_RESOURCES = auto()
    ESTABLISH_CARAVAN = auto()
    COMMERCE = auto()
    REST_UNIT = auto()
    ASSIST_CONSTRUCTION = auto()
    GIVE_BASE = auto()
    GIVE_EXPANSION = auto()
    DESTROY_BASE = auto()  # May be removed in future


class ExpansionType(Enum):
    """Types of expansion structures."""
    FARM = "farm"
    LUMBER_MILL = "mill"
    OIL_RIG = "rig"


class CaravanType(Enum):
    """Types of caravans/trade routes - terrain-based."""
    LAND = "land"   # Routes traced over land hexsides
    SEA = "sea"     # Routes traced over water hexsides


class ResourceType(Enum):
    """Resource types for commerce/trading."""
    GOLD = 1
    LUMBER = 2
    OIL = 3


# =============================================================================
# UNIT ORDERS
# =============================================================================

@dataclass
class MovementOrder:
    """
    Order for a unit to move along a path of hexes.
    
    The unit will attempt to move through each hex in sequence.
    Movement stops if:
    - The unit runs out of movement points
    - The unit enters a hex with enemies (combat)
    - A hexside limit is exceeded
    - The path becomes invalid
    """
    unit_id: int
    path: List[int] = field(default_factory=list)  # Sequence of destination hex IDs
    
    @property
    def order_type(self) -> UnitOrderType:
        return UnitOrderType.MOVEMENT
    
    @property
    def first_destination(self) -> Optional[int]:
        """Get the first hex in the path."""
        return self.path[0] if self.path else None
    
    def pop_destination(self) -> Optional[int]:
        """Remove and return the first destination."""
        return self.path.pop(0) if self.path else None


@dataclass
class RangedfireOrder:
    """
    Order for an interior siege unit to fire at an adjacent hex.
    
    This converts the unit temporarily to exterior siege for targeting
    purposes, allowing it to bombard an adjacent hex.
    """
    unit_id: int
    target_hex: int
    
    @property
    def order_type(self) -> UnitOrderType:
        return UnitOrderType.RANGEDFIRE


@dataclass
class BoardTransportOrder:
    """
    Order for a ground unit to board a friendly transport.
    
    Requirements:
    - Unit must be ground type
    - Transport must be in same hex
    - Transport must be same faction
    - Transport must have space available
    """
    unit_id: int
    transport_id: int
    
    @property
    def order_type(self) -> UnitOrderType:
        return UnitOrderType.BOARD_TRANSPORT


@dataclass
class BuildBaseOrder:
    """
    Order for a leader unit to establish a new base.
    
    Requirements:
    - Unit must be a leader (hero)
    - Location must not be adjacent to existing base
    - Location must not be in combat
    - Location must be valid terrain for a base
    """
    unit_id: int
    # Base is built at unit's current location
    
    @property
    def order_type(self) -> UnitOrderType:
        return UnitOrderType.BUILD_BASE


# =============================================================================
# BASE ORDERS
# =============================================================================

@dataclass
class BuildUnitOrder:
    """
    Order for a base to construct a new unit.
    
    Requirements:
    - Base must have sufficient resources
    - Base tier must meet unit's minimum tier requirement
    - Base must not be in combat
    """
    base_id: int
    unit_type: str  # Unit type name (e.g., "Grunt", "Footman")
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.BUILD_UNIT


@dataclass
class UpgradeBaseOrder:
    """
    Order to upgrade a base to the next tier.
    
    Requirements:
    - Base must not be at max tier (3)
    - Base must have sufficient resources
    - Base must not be in combat
    """
    base_id: int
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.UPGRADE_BASE


@dataclass
class ExpandOrder:
    """
    Order for a base to build an expansion (farm, mill, or rig).
    
    Requirements:
    - Target hex must be valid for expansion type
    - Target hex must be in faction's visible area
    - Base must have sufficient resources
    """
    base_id: int
    target_hex: int
    expansion_type: ExpansionType
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.EXPAND


@dataclass
class HarvestOrder:
    """
    Order for a base to harvest resources from its expansions.
    
    This collects income from farms, mills, and rigs associated with the base.
    """
    base_id: int
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.HARVEST


@dataclass
class SendResourcesOrder:
    """
    Order to transfer resources from one base to another.
    
    Resources are sent immediately (no travel time like caravans).
    Both bases must be owned by the same faction or allied.
    """
    origin_base: int
    destination_base: int
    gold: int = 0
    lumber: int = 0
    oil: int = 0
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.SEND_RESOURCES
    
    @property
    def total_resources(self) -> int:
        """Total amount of resources being sent."""
        return self.gold + self.lumber + self.oil


@dataclass
class EstablishCaravanOrder:
    """
    Order to establish a recurring trade caravan between bases.
    
    Caravans travel along a path and deliver resources each turn
    until interrupted.
    """
    base_id: int  # Origin base
    destination_base: int
    caravan_type: CaravanType
    path: List[int] = field(default_factory=list)  # Hex path for caravan
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.ESTABLISH_CARAVAN


@dataclass
class CommerceOrder:
    """
    Order to convert one resource type to another at a base.
    
    The exchange rate depends on base tier and other factors.
    """
    base_id: int
    resource_in: ResourceType   # Resource being spent
    resource_out: ResourceType  # Resource being gained
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.COMMERCE


@dataclass
class RestUnitOrder:
    """
    Order for a base to heal/rest a unit.
    
    The unit must be at the base's location.
    Restores HP based on base tier.
    """
    base_id: int
    unit_id: int
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.REST_UNIT


@dataclass
class AssistConstructionOrder:
    """
    Order for a base to assist construction at another location.
    
    Can help build or upgrade a base, or help construct expansions.
    """
    base_id: int
    target_hex: int  # Location being assisted
    target_base: Optional[int] = None  # Specific base if applicable
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.ASSIST_CONSTRUCTION


@dataclass
class GiveBaseOrder:
    """
    Order to transfer ownership of a base to another faction.
    
    Used for diplomatic transfers between allies.
    """
    base_id: int
    recipient_faction: FactionId
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.GIVE_BASE


@dataclass
class GiveExpansionOrder:
    """
    Order to transfer ownership of an expansion to another base.
    
    The expansion (farm/mill/rig) is reassigned to a different base.
    """
    expansion_hex: int   # Hex where the expansion is located
    recipient_base: int  # Base that will receive the expansion
    owner_base: int      # Current owning base
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.GIVE_EXPANSION


@dataclass
class DestroyBaseOrder:
    """
    Order to abandon/destroy a base.
    
    The base is reduced to ruins. May be removed in future versions.
    """
    base_id: int
    
    @property
    def order_type(self) -> BaseOrderType:
        return BaseOrderType.DESTROY_BASE


# =============================================================================
# ORDER COLLECTIONS
# =============================================================================

@dataclass
class FactionOrders:
    """
    All orders submitted by a faction for a turn.
    
    This collects both unit orders and base orders into a single structure
    for easier management and validation.
    """
    faction_id: FactionId
    
    # Unit orders
    movement_orders: List[MovementOrder] = field(default_factory=list)
    rangedfire_orders: List[RangedfireOrder] = field(default_factory=list)
    board_transport_orders: List[BoardTransportOrder] = field(default_factory=list)
    build_base_orders: List[BuildBaseOrder] = field(default_factory=list)
    
    # Base orders
    build_unit_orders: List[BuildUnitOrder] = field(default_factory=list)
    upgrade_base_orders: List[UpgradeBaseOrder] = field(default_factory=list)
    expand_orders: List[ExpandOrder] = field(default_factory=list)
    harvest_orders: List[HarvestOrder] = field(default_factory=list)
    send_resources_orders: List[SendResourcesOrder] = field(default_factory=list)
    establish_caravan_orders: List[EstablishCaravanOrder] = field(default_factory=list)
    commerce_orders: List[CommerceOrder] = field(default_factory=list)
    rest_unit_orders: List[RestUnitOrder] = field(default_factory=list)
    assist_construction_orders: List[AssistConstructionOrder] = field(default_factory=list)
    give_base_orders: List[GiveBaseOrder] = field(default_factory=list)
    give_expansion_orders: List[GiveExpansionOrder] = field(default_factory=list)
    destroy_base_orders: List[DestroyBaseOrder] = field(default_factory=list)
    
    @property
    def total_unit_orders(self) -> int:
        """Count of all unit orders."""
        return (len(self.movement_orders) + len(self.rangedfire_orders) +
                len(self.board_transport_orders) + len(self.build_base_orders))
    
    @property
    def total_base_orders(self) -> int:
        """Count of all base orders."""
        return (len(self.build_unit_orders) + len(self.upgrade_base_orders) +
                len(self.expand_orders) + len(self.harvest_orders) +
                len(self.send_resources_orders) + len(self.establish_caravan_orders) +
                len(self.commerce_orders) + len(self.rest_unit_orders) +
                len(self.assist_construction_orders) + len(self.give_base_orders) +
                len(self.give_expansion_orders) + len(self.destroy_base_orders))
    
    @property
    def total_orders(self) -> int:
        """Total count of all orders."""
        return self.total_unit_orders + self.total_base_orders
    
    def clear(self):
        """Clear all orders."""
        self.movement_orders.clear()
        self.rangedfire_orders.clear()
        self.board_transport_orders.clear()
        self.build_base_orders.clear()
        self.build_unit_orders.clear()
        self.upgrade_base_orders.clear()
        self.expand_orders.clear()
        self.harvest_orders.clear()
        self.send_resources_orders.clear()
        self.establish_caravan_orders.clear()
        self.commerce_orders.clear()
        self.rest_unit_orders.clear()
        self.assist_construction_orders.clear()
        self.give_base_orders.clear()
        self.give_expansion_orders.clear()
        self.destroy_base_orders.clear()


