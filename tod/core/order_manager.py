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
        # Validate unit exists and belongs to faction
        unit = state.get_unit(unit_id)
        if not unit:
            return False, f"Unit {unit_id} not found"
        
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        if unit_faction != faction_id:
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
        
        # Check if unit already has a movement order
        orders = self.get_faction_orders(faction_id)
        existing = [o for o in orders.movement_orders if o.unit_id == unit_id]
        if existing:
            # Replace existing order
            orders.movement_orders = [o for o in orders.movement_orders if o.unit_id != unit_id]
        
        # Add the order
        order = MovementOrder(unit_id=unit_id, path=path)
        orders.movement_orders.append(order)
        
        return True, f"Movement order submitted for unit {unit_id}: {len(path)} hex path"
    
    def submit_rangedfire(self, faction_id: int, unit_id: int, target_hex: int,
                         state: GameState) -> tuple[bool, str]:
        """Submit a ranged fire order for an interior siege unit."""
        unit = state.get_unit(unit_id)
        if not unit:
            return False, f"Unit {unit_id} not found"
        
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        if unit_faction != faction_id:
            return False, f"Unit {unit_id} does not belong to faction {faction_id}"
        
        orders = self.get_faction_orders(faction_id)
        order = RangedfireOrder(unit_id=unit_id, target_hex=target_hex)
        orders.rangedfire_orders.append(order)
        
        return True, f"Ranged fire order submitted for unit {unit_id} -> hex {target_hex}"
    
    def submit_board_transport(self, faction_id: int, unit_id: int, transport_id: int,
                               state: GameState) -> tuple[bool, str]:
        """Submit an order to board a transport."""
        unit = state.get_unit(unit_id)
        transport = state.get_unit(transport_id)
        
        if not unit:
            return False, f"Unit {unit_id} not found"
        if not transport:
            return False, f"Transport {transport_id} not found"
        
        orders = self.get_faction_orders(faction_id)
        order = BoardTransportOrder(unit_id=unit_id, transport_id=transport_id)
        orders.board_transport_orders.append(order)
        
        return True, f"Board transport order: unit {unit_id} -> transport {transport_id}"
    
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


