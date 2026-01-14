"""
Order Manager for Tides of Darkness.

Handles order submission, validation, and storage during the planning phase.
Each faction can submit orders for their units and bases.
"""
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from .models.enums import FactionId
from .models.orders import (
    MovementOrder, RangedfireOrder, BoardTransportOrder, BuildBaseOrder,
    FastTravelOrder,
    BuildUnitOrder, UpgradeBaseOrder, ExpandOrder, HarvestOrder,
    SendResourcesOrder, EstablishCaravanOrder, CommerceOrder, RestUnitOrder,
    AssistConstructionOrder, GiveBaseOrder, GiveExpansionOrder, DestroyBaseOrder,
    FactionOrders
)
from .game_state import GameState


@dataclass
class OrderManager:
    """
    Manages order submission and storage for all factions.
    
    During the planning phase, factions submit orders here.
    During resolution, the resolution engine reads and processes these orders.
    """
    # Orders organized by faction
    faction_orders: Dict[int, FactionOrders] = field(default_factory=dict)
    
    # Track which factions have "locked in" their orders
    locked_factions: Set[int] = field(default_factory=set)
    
    def can_control_unit(self, faction_id: int, unit, state: GameState) -> bool:
        """
        Check if a faction can control a unit.
        
        A faction can control a unit if:
        1. The unit belongs directly to that faction, OR
        2. The unit's faction is a vassal of the controlling faction
        
        This supports both direct ownership and the vassal/sovereign system.
        """
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        
        # Direct ownership
        if unit_faction == faction_id:
            return True
        
        # Check if unit's faction is a vassal of the controlling faction
        unit_faction_obj = state.factions.get(unit_faction)
        if unit_faction_obj and unit_faction_obj.vassal_of is not None:
            sovereign_id = unit_faction_obj.vassal_of.value if hasattr(unit_faction_obj.vassal_of, 'value') else unit_faction_obj.vassal_of
            if sovereign_id == faction_id:
                return True
        
        return False
    
    def get_faction_orders(self, faction_id: int) -> FactionOrders:
        """Get or create FactionOrders for a faction."""
        if faction_id not in self.faction_orders:
            self.faction_orders[faction_id] = FactionOrders(faction_id=FactionId(faction_id))
        return self.faction_orders[faction_id]
    
    # ==================== Unit Order Submission ====================
    
    def submit_movement(self, faction_id: int, unit_id: int, path: List[int], 
                       state: GameState) -> tuple[bool, str]:
        """
        Submit a movement order for a unit.
        
        Returns (success, message)
        """
        # Validate unit exists and can be controlled by faction
        unit = state.get_unit(unit_id)
        if not unit:
            return False, f"Unit {unit_id} not found"
        
        if not self.can_control_unit(faction_id, unit, state):
            return False, f"Unit {unit_id} does not belong to faction {faction_id}"
        
        if not unit.alive:
            return False, f"Unit {unit_id} is not alive"
        
        if not path:
            return False, "Movement path cannot be empty"
        
        # Check if unit is being rested at a base (can't move and rest)
        if state.is_unit_being_rested(unit_id):
            rest_info = state.get_rest_order_for_unit(unit_id)
            if rest_info:
                base = state.get_base(rest_info['base_id'])
                base_name = base.name if base else f"Base {rest_info['base_id']}"
                return False, f"Unit is being rested at {base_name} (cancel Rest Unit order first)"
            return False, "Unit is being rested (cancel Rest Unit order first)"
        
        # Check if unit has a rangedfire order (can't move and fire)
        orders = self.get_faction_orders(faction_id)
        if any(o.unit_id == unit_id for o in orders.rangedfire_orders):
            return False, f"{unit.name} has a Ranged Fire order (cancel it first)"
        
        # Check if unit already has a movement order
        existing = [o for o in orders.movement_orders if o.unit_id == unit_id]
        if existing:
            # Replace existing order
            orders.movement_orders = [o for o in orders.movement_orders if o.unit_id != unit_id]
        
        # Add the order
        order = MovementOrder(unit_id=unit_id, path=path)
        orders.movement_orders.append(order)
        
        return True, f"Movement order submitted for unit {unit_id}: {len(path)} hex path"
    
    def submit_fast_travel(self, faction_id: int, unit_id: int, path: List[int],
                           state: GameState) -> tuple[bool, str]:
        """
        Submit a fast travel order (March for land, Full Sail for sea).
        
        Validation:
        - Unit must exist and be alive
        - Unit must not have ANY other orders
        - Land units: must be on a road hex, all moves must follow roads
        - Naval units: must be on ocean hex, all moves must be to ocean hexes
        - Cannot enter hex with hostile units
        - Path length must not exceed fast_travel_max_hexes config
        """
        from .game_config import get_game_config
        from .models.enums import UnitType
        
        unit = state.get_unit(unit_id)
        if not unit:
            return False, f"Unit {unit_id} not found"
        
        if not self.can_control_unit(faction_id, unit, state):
            return False, f"Unit {unit_id} does not belong to faction {faction_id}"
        
        if not unit.alive:
            return False, f"Unit {unit_id} is not alive"
        
        if not path:
            return False, "Fast travel path cannot be empty"
        
        # Check if unit has ANY other orders (fast travel uses entire turn)
        orders = self.get_faction_orders(faction_id)
        if any(o.unit_id == unit_id for o in orders.movement_orders):
            return False, f"{unit.name} already has a movement order"
        if any(o.unit_id == unit_id for o in orders.rangedfire_orders):
            return False, f"{unit.name} already has a ranged fire order"
        if any(o.unit_id == unit_id for o in orders.fast_travel_orders):
            return False, f"{unit.name} already has a fast travel order"
        if state.is_unit_being_rested(unit_id):
            return False, f"{unit.name} is being rested"
        
        # Check path length
        config = get_game_config()
        max_hexes = config.movement.fast_travel_max_hexes
        if len(path) > max_hexes:
            return False, f"Fast travel path too long ({len(path)} > {max_hexes})"
        
        # Determine if this is naval (Full Sail) or land (March)
        unit_type = unit.unit_type if hasattr(unit, 'unit_type') else UnitType.GROUND
        is_naval = (unit_type == UnitType.SEA or unit_type == 2)  # SEA = 2
        
        # Air units cannot fast travel
        is_air = (unit_type == UnitType.AIR or unit_type == 1)  # AIR = 1
        if is_air:
            return False, f"Air units cannot use fast travel"
        
        # Validate starting position
        start_hex = unit.location
        if is_naval:
            # Naval: must be on ocean hex
            hex_obj = state.get_hex(start_hex)
            if not hex_obj or hex_obj.terrain != 'O':
                return False, f"{unit.name} must be on an ocean hex to use Full Sail"
        else:
            # Land: must be on a hex with a road
            if not state.has_road_at_hex(start_hex):
                return False, f"{unit.name} must be on a road to use March"
        
        # Validate entire path
        current_hex = start_hex
        for i, next_hex in enumerate(path):
            # Check adjacency
            if not state.are_hexes_adjacent(current_hex, next_hex):
                return False, f"Path step {i+1} is not adjacent"
            
            # Check for hostile units
            faction_initiative = state.faction_initiative(unit_faction)
            units_at_dest = state.units_at_hex(next_hex)
            for u in units_at_dest:
                if u.alive:
                    u_faction = u.faction.value if hasattr(u.faction, 'value') else u.faction
                    u_initiative = state.faction_initiative(u_faction)
                    if u_initiative != faction_initiative:
                        return False, f"Cannot fast travel into hex {next_hex} with hostile units"
            
            if is_naval:
                # Naval: destination must be ocean
                hex_obj = state.get_hex(next_hex)
                if not hex_obj or hex_obj.terrain != 'O':
                    return False, f"Full Sail path step {i+1} must be to an ocean hex"
            else:
                # Land: must have road between current and next
                if not state.has_road_between(current_hex, next_hex):
                    return False, f"March path step {i+1} must follow a road"
            
            current_hex = next_hex
        
        # All validations passed - add the order
        order = FastTravelOrder(unit_id=unit_id, path=path, is_naval=is_naval)
        orders.fast_travel_orders.append(order)
        
        order_type = "Full Sail" if is_naval else "March"
        return True, f"{order_type} order submitted for {unit.name}: {len(path)} hex path"
    
    def cancel_fast_travel(self, faction_id: int, unit_id: int) -> tuple[bool, str]:
        """Cancel a fast travel order for a unit."""
        orders = self.get_faction_orders(faction_id)
        
        existing = [o for o in orders.fast_travel_orders if o.unit_id == unit_id]
        if not existing:
            return False, f"No fast travel order found for unit {unit_id}"
        
        orders.fast_travel_orders = [o for o in orders.fast_travel_orders if o.unit_id != unit_id]
        return True, f"Fast travel order cancelled for unit {unit_id}"
    
    def submit_rangedfire(self, faction_id: int, unit_id: int, target_hex: int,
                         state: GameState) -> tuple[bool, str]:
        """
        Submit a ranged fire order for a unit with rangedfire capability.
        
        Validation:
        - Unit must exist and be alive
        - Unit must have can_rangedfire = True
        - Unit must not be in a combat hex
        - Unit must not have a movement order (no moving + firing)
        - Target must be an adjacent hex
        - Target must be a combat hex (enemies present)
        """
        from .vision import get_adjacent_hexes
        
        unit = state.get_unit(unit_id)
        if not unit:
            return False, f"Unit {unit_id} not found"
        
        if not unit.alive:
            return False, f"Unit {unit_id} is dead"
        
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        if unit_faction != faction_id:
            return False, f"Unit {unit_id} does not belong to faction {faction_id}"
        
        # Check unit has rangedfire capability
        if not unit.can_rangedfire:
            return False, f"{unit.name} cannot use Ranged Fire"
        
        # Check unit is not in a combat hex
        if state.is_combat_hex(unit.location):
            return False, f"{unit.name} is in combat and cannot use Ranged Fire"
        
        # Check unit doesn't have a movement order
        orders = self.get_faction_orders(faction_id)
        if any(o.unit_id == unit_id for o in orders.movement_orders):
            return False, f"{unit.name} has a movement order (cancel movement first)"
        
        # Check target is adjacent
        adjacent_hexes = get_adjacent_hexes(unit.location)
        if target_hex not in adjacent_hexes:
            return False, f"Hex {target_hex} is not adjacent to {unit.name}'s location"
        
        # Check target is a combat hex (has enemies to shoot at)
        if not state.is_combat_hex(target_hex):
            return False, f"Hex {target_hex} is not a combat hex"
        
        # Check there are enemies in the target hex (not just allies)
        unit_init = state.faction_initiative(unit_faction)
        units_in_target = state.units_at_hex(target_hex)
        enemies_in_target = [
            u for u in units_in_target if u.alive and 
            state.faction_initiative(u.faction.value if hasattr(u.faction, 'value') else u.faction) != unit_init
        ]
        if not enemies_in_target:
            return False, f"No valid targets in hex {target_hex}"
        
        # Remove existing rangedfire order for this unit if any
        orders.rangedfire_orders = [o for o in orders.rangedfire_orders if o.unit_id != unit_id]
        
        # Add the order
        order = RangedfireOrder(unit_id=unit_id, target_hex=target_hex)
        orders.rangedfire_orders.append(order)
        
        return True, f"Ranged fire order submitted: {unit.name} -> hex {target_hex}"
    
    def submit_board_transport(self, faction_id: int, unit_id: int, transport_id: int,
                               state: GameState) -> tuple[bool, str]:
        """
        Submit an order for a ground unit to board a transport.
        
        Validation:
        - Unit must exist and be alive
        - Unit must be ground type
        - Unit must be controlled by this faction (or vassal)
        - Transport must exist and be a valid transport
        - Transport must be in the same hex as the unit
        - Transport must be friendly (same faction or same initiative)
        - Transport must have available slots (considering pending orders)
        - Unit must not have any other orders (movement, rangedfire, fast travel, build base)
        """
        from .models.enums import UnitType
        
        unit = state.get_unit(unit_id)
        transport = state.get_unit(transport_id)
        
        if not unit:
            return False, f"Unit {unit_id} not found"
        if not transport:
            return False, f"Transport {transport_id} not found"
        
        if not unit.alive:
            return False, f"Unit {unit_id} is not alive"
        if not transport.alive:
            return False, f"Transport {transport_id} is not alive"
        
        # Check unit is controllable by this faction
        if not self.can_control_unit(faction_id, unit, state):
            return False, f"Unit {unit_id} cannot be controlled by faction {faction_id}"
        
        # Unit must be ground type
        if unit.unit_type != UnitType.GROUND:
            return False, f"{unit.name} is not a ground unit (only ground units can board transports)"
        
        # Transport must actually be a transport
        if not transport.is_transport:
            return False, f"{transport.name} is not a transport"
        
        # Must be in same hex
        if unit.location != transport.location:
            return False, f"{unit.name} is not in the same hex as {transport.name}"
        
        # Transport must be friendly (same faction or same initiative)
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        transport_faction = transport.faction.value if hasattr(transport.faction, 'value') else transport.faction
        unit_init = state.faction_initiative(unit_faction)
        transport_init = state.faction_initiative(transport_faction)
        
        if transport_faction != unit_faction and transport_init != unit_init:
            return False, f"Cannot board {transport.name} - not a friendly transport"
        
        # Check unit doesn't have other orders
        orders = self.get_faction_orders(faction_id)
        if any(o.unit_id == unit_id for o in orders.movement_orders):
            return False, f"{unit.name} already has a movement order"
        if any(o.unit_id == unit_id for o in orders.rangedfire_orders):
            return False, f"{unit.name} already has a ranged fire order"
        if any(o.unit_id == unit_id for o in orders.fast_travel_orders):
            return False, f"{unit.name} already has a fast travel order"
        if any(o.unit_id == unit_id for o in orders.build_base_orders):
            return False, f"{unit.name} already has a build base order"
        if any(o.unit_id == unit_id for o in orders.board_transport_orders):
            return False, f"{unit.name} already has a board transport order"
        
        # Check transport has available slots
        # Count currently loaded units + pending board orders for this transport
        currently_loaded = transport.transport_slots_used
        pending_boards = self._count_pending_boards_for_transport(transport_id)
        total_occupied = currently_loaded + pending_boards
        
        if total_occupied >= 2:  # Max 2 slots available
            return False, f"{transport.name} has no available slots (using {total_occupied}/2)"
        
        # All validation passed - add the order
        order = BoardTransportOrder(unit_id=unit_id, transport_id=transport_id)
        orders.board_transport_orders.append(order)
        
        return True, f"Board transport order: {unit.name} -> {transport.name}"
    
    def _count_pending_boards_for_transport(self, transport_id: int) -> int:
        """Count how many pending board transport orders target a specific transport."""
        count = 0
        for faction_orders in self.faction_orders.values():
            for order in faction_orders.board_transport_orders:
                if order.transport_id == transport_id:
                    count += 1
        return count
    
    def submit_build_base(self, faction_id: int, unit_id: int,
                         state: GameState) -> tuple[bool, str]:
        """Submit an order for a leader to build a base."""
        unit = state.get_unit(unit_id)
        if not unit:
            return False, f"Unit {unit_id} not found"
        
        orders = self.get_faction_orders(faction_id)
        order = BuildBaseOrder(unit_id=unit_id)
        orders.build_base_orders.append(order)
        
        return True, f"Build base order submitted for leader {unit_id}"
    
    # ==================== Base Order Submission ====================
    
    def submit_build_unit(self, faction_id: int, base_id: int, unit_type: str,
                         state: GameState) -> tuple[bool, str]:
        """Submit an order to build a unit at a base."""
        base = state.get_base(base_id)
        if not base:
            return False, f"Base {base_id} not found"
        
        base_faction = base.faction.value if hasattr(base.faction, 'value') else base.faction
        if base_faction != faction_id:
            return False, f"Base {base_id} does not belong to faction {faction_id}"
        
        orders = self.get_faction_orders(faction_id)
        order = BuildUnitOrder(base_id=base_id, unit_type=unit_type)
        orders.build_unit_orders.append(order)
        
        return True, f"Build order: {unit_type} at base {base_id}"
    
    def submit_upgrade_base(self, faction_id: int, base_id: int,
                           state: GameState) -> tuple[bool, str]:
        """Submit an order to upgrade a base."""
        base = state.get_base(base_id)
        if not base:
            return False, f"Base {base_id} not found"
        
        orders = self.get_faction_orders(faction_id)
        order = UpgradeBaseOrder(base_id=base_id)
        orders.upgrade_base_orders.append(order)
        
        return True, f"Upgrade order submitted for base {base_id}"
    
    def submit_harvest(self, faction_id: int, base_id: int,
                      state: GameState) -> tuple[bool, str]:
        """Submit a harvest order for a base."""
        base = state.get_base(base_id)
        if not base:
            return False, f"Base {base_id} not found"
        
        orders = self.get_faction_orders(faction_id)
        order = HarvestOrder(base_id=base_id)
        orders.harvest_orders.append(order)
        
        return True, f"Harvest order submitted for base {base_id}"
    
    def submit_send_resources(self, faction_id: int, origin_base: int, 
                             destination_base: int, gold: int, lumber: int, oil: int,
                             state: GameState) -> tuple[bool, str]:
        """Submit an order to send resources between bases."""
        orders = self.get_faction_orders(faction_id)
        order = SendResourcesOrder(
            origin_base=origin_base,
            destination_base=destination_base,
            gold=gold,
            lumber=lumber,
            oil=oil
        )
        orders.send_resources_orders.append(order)
        
        return True, f"Send resources: {gold}g/{lumber}l/{oil}o from base {origin_base} to {destination_base}"
    
    # ==================== Order Management ====================
    
    def cancel_movement(self, faction_id: int, unit_id: int) -> tuple[bool, str]:
        """Cancel a movement order for a unit."""
        orders = self.get_faction_orders(faction_id)
        before = len(orders.movement_orders)
        orders.movement_orders = [o for o in orders.movement_orders if o.unit_id != unit_id]
        after = len(orders.movement_orders)
        
        if before == after:
            return False, f"No movement order found for unit {unit_id}"
        return True, f"Movement order cancelled for unit {unit_id}"
    
    def cancel_rangedfire(self, faction_id: int, unit_id: int) -> tuple[bool, str]:
        """Cancel a ranged fire order for a unit."""
        orders = self.get_faction_orders(faction_id)
        before = len(orders.rangedfire_orders)
        orders.rangedfire_orders = [o for o in orders.rangedfire_orders if o.unit_id != unit_id]
        after = len(orders.rangedfire_orders)
        
        if before == after:
            return False, f"No ranged fire order found for unit {unit_id}"
        return True, f"Ranged fire order cancelled for unit {unit_id}"
    
    def cancel_board_transport(self, faction_id: int, unit_id: int) -> tuple[bool, str]:
        """Cancel a board transport order for a unit."""
        orders = self.get_faction_orders(faction_id)
        before = len(orders.board_transport_orders)
        orders.board_transport_orders = [o for o in orders.board_transport_orders if o.unit_id != unit_id]
        after = len(orders.board_transport_orders)
        
        if before == after:
            return False, f"No board transport order found for unit {unit_id}"
        return True, f"Board transport order cancelled for unit {unit_id}"
    
    def clear_faction_orders(self, faction_id: int) -> tuple[bool, str]:
        """Clear all orders for a faction."""
        orders = self.get_faction_orders(faction_id)
        orders.clear()
        return True, f"All orders cleared for faction {faction_id}"
    
    def clear_all_orders(self) -> tuple[bool, str]:
        """Clear all orders for all factions."""
        self.faction_orders.clear()
        self.locked_factions.clear()
        return True, "All orders cleared"
    
    def lock_faction_orders(self, faction_id: int) -> tuple[bool, str]:
        """Lock in a faction's orders (no more changes)."""
        self.locked_factions.add(faction_id)
        return True, f"Orders locked for faction {faction_id}"
    
    def unlock_faction_orders(self, faction_id: int) -> tuple[bool, str]:
        """Unlock a faction's orders (allow changes again)."""
        self.locked_factions.discard(faction_id)
        return True, f"Orders unlocked for faction {faction_id}"
    
    def is_faction_locked(self, faction_id: int) -> bool:
        """Check if a faction's orders are locked."""
        return faction_id in self.locked_factions
    
    # ==================== Query Methods ====================
    
    def get_all_movement_orders(self) -> List[MovementOrder]:
        """Get all movement orders from all factions."""
        all_orders = []
        for fo in self.faction_orders.values():
            all_orders.extend(fo.movement_orders)
        return all_orders
    
    def get_order_summary(self) -> Dict:
        """Get a summary of all submitted orders."""
        summary = {
            "totalFactions": len(self.faction_orders),
            "lockedFactions": len(self.locked_factions),
            "factions": {}
        }
        
        for faction_id, orders in self.faction_orders.items():
            summary["factions"][faction_id] = {
                "locked": faction_id in self.locked_factions,
                "unitOrders": orders.total_unit_orders,
                "baseOrders": orders.total_base_orders,
                "totalOrders": orders.total_orders,
                "breakdown": {
                    "movement": len(orders.movement_orders),
                    "rangedfire": len(orders.rangedfire_orders),
                    "boardTransport": len(orders.board_transport_orders),
                    "buildBase": len(orders.build_base_orders),
                    "buildUnit": len(orders.build_unit_orders),
                    "upgradeBase": len(orders.upgrade_base_orders),
                    "expand": len(orders.expand_orders),
                    "harvest": len(orders.harvest_orders),
                    "sendResources": len(orders.send_resources_orders),
                    "caravan": len(orders.establish_caravan_orders),
                    "commerce": len(orders.commerce_orders),
                    "restUnit": len(orders.rest_unit_orders),
                }
            }
        
        return summary
    
    def to_dict(self) -> Dict:
        """Convert all orders to a dictionary for API responses."""
        result = {
            "lockedFactions": list(self.locked_factions),
            "factionOrders": {}
        }
        
        for faction_id, orders in self.faction_orders.items():
            result["factionOrders"][faction_id] = {
                "factionId": faction_id,
                "movementOrders": [
                    {"unitId": o.unit_id, "path": o.path}
                    for o in orders.movement_orders
                ],
                "rangedfireOrders": [
                    {"unitId": o.unit_id, "targetHex": o.target_hex}
                    for o in orders.rangedfire_orders
                ],
                "boardTransportOrders": [
                    {"unitId": o.unit_id, "transportId": o.transport_id}
                    for o in orders.board_transport_orders
                ],
                "buildBaseOrders": [
                    {"unitId": o.unit_id}
                    for o in orders.build_base_orders
                ],
                "buildUnitOrders": [
                    {"baseId": o.base_id, "unitType": o.unit_type}
                    for o in orders.build_unit_orders
                ],
                "upgradeBaseOrders": [
                    {"baseId": o.base_id}
                    for o in orders.upgrade_base_orders
                ],
                "harvestOrders": [
                    {"baseId": o.base_id}
                    for o in orders.harvest_orders
                ],
                "sendResourcesOrders": [
                    {
                        "originBase": o.origin_base,
                        "destinationBase": o.destination_base,
                        "gold": o.gold,
                        "lumber": o.lumber,
                        "oil": o.oil
                    }
                    for o in orders.send_resources_orders
                ],
            }
        
        return result


# Global order manager instance
_order_manager: Optional[OrderManager] = None


def get_order_manager() -> OrderManager:
    """Get the global OrderManager instance."""
    global _order_manager
    if _order_manager is None:
        _order_manager = OrderManager()
    return _order_manager


def reset_order_manager():
    """Reset the order manager (clear all orders)."""
    global _order_manager
    _order_manager = OrderManager()


