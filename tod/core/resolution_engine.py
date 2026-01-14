"""
Resolution Engine - Processes orders and advances the game state.

This module handles the resolution phase of each turn:
1. Movement resolution
2. Combat resolution
3. Economic actions (TODO)
4. Turn advancement

The resolution engine orchestrates the full turn lifecycle.
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field
import logging

from .game_state import GameState, GamePhase, RoundSide
from .order_manager import get_order_manager, OrderManager
from .movement import (
    can_move, validate_path, get_hexside_limit,
    collect_hexside_usage, resolve_hexside_conflicts,
    MoveResult
)
from .combat_manager import get_combat_manager, init_combat_manager, CombatManager
from .combat_engine import CombatEngine, CombatRoundResult
from .combat_modifiers import assign_combat_modifiers
from .game_log import get_game_log, LogEventType
from .models import Unit, UnitType

logger = logging.getLogger('resolution')


@dataclass
class ResolutionResult:
    """Result of a turn resolution."""
    success: bool
    message: str
    movements_applied: int = 0
    combats_resolved: int = 0
    units_killed: int = 0
    base_actions_resolved: int = 0
    combat_results: List[CombatRoundResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class ResolutionEngine:
    """
    Handles the resolution of orders and turn advancement.
    
    Resolution phases:
    1. Movement - Units move along their ordered paths
    2. Combat - Battles are fought where enemies meet
    3. Economic - Base actions are processed (TODO)
    4. Cleanup - Turn advances to next initiative
    """
    
    def __init__(self, state: GameState, order_manager: OrderManager = None, 
                 combat_manager: CombatManager = None):
        self.state = state
        self.order_manager = order_manager or get_order_manager()
        self.combat_mgr = combat_manager or init_combat_manager(state)
    
    def _reset_units_for_turn(self, faction_ids: List[int]) -> int:
        """
        Reset per-turn state for all units belonging to the given factions.
        
        This should be called at the START of each initiative's turn to:
        - Restore movement points to maximum
        - Reset road move bonus
        - Reset fired status
        - Restore light armor
        
        Returns the number of units reset.
        """
        units_reset = 0
        for unit in self.state.units.values():
            if not unit.alive:
                continue
            
            unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            if unit_faction in faction_ids:
                unit.reset_for_turn()
                units_reset += 1
        
        return units_reset
    
    def resolve_current_turn(self) -> ResolutionResult:
        """
        Resolve all orders for the current initiative and advance the turn.
        
        This is the main entry point for turn resolution.
        """
        current_init = self.state.turn.current_initiative
        round_side = self.state.turn.round_side.value if hasattr(self.state.turn.round_side, 'value') else str(self.state.turn.round_side)
        
        # Get factions in current initiative
        faction_ids = self.state.factions_in_initiative(current_init)
        faction_id_values = [f.value if hasattr(f, 'value') else int(f) for f in faction_ids]
        
        if not faction_id_values:
            return ResolutionResult(
                success=False,
                message=f"No factions found for initiative {current_init}"
            )
        
        logger.info(f"=== Resolving Initiative {current_init} ({round_side} Round {self.state.turn.round_number}) ===")
        
        # Update game log context
        game_log = get_game_log()
        game_log.update_turn_context(
            turn_number=self.state.turn.turn_number,
            round_number=self.state.turn.round_number,
            round_side=round_side,
            initiative=current_init
        )
        
        # Log initiative start
        faction_names = [self.state.factions[f].name for f in faction_id_values if f in self.state.factions]
        game_log.log_initiative_start(current_init, faction_names)
        
        # Phase 0: Board Transport (BEFORE movement so units can travel with transport)
        boards_resolved = self._resolve_board_transport(faction_id_values)
        logger.info(f"Board transport phase: {boards_resolved} units boarded")
        
        # Phase 1: Movement Resolution
        movements_applied = self._resolve_movement(faction_id_values)
        logger.info(f"Movement phase: {movements_applied} units moved")
        
        # Phase 1a: Fast Travel Resolution (March/Full Sail)
        fast_travel_applied = self._resolve_fast_travel(faction_id_values)
        logger.info(f"Fast travel phase: {fast_travel_applied} units fast traveled")
        movements_applied += fast_travel_applied
        
        # Phase 1b: Unload Transports (auto-unload on non-ocean hexes)
        unloads_resolved = self._resolve_unload_transports()
        logger.info(f"Unload transports phase: {unloads_resolved} units unloaded")
        
        # Phase 1c: Update Initiative (Troll Diplomacy, future diplomacy changes)
        # Must happen BEFORE combat detection so initiative shifts create proper combats
        initiative_updates = self._resolve_update_initiative()
        if initiative_updates:
            logger.info(f"Update Initiative phase: {len(initiative_updates)} changes")
        
        # Detect new/updated combats after movement AND initiative changes
        self.combat_mgr.detect_combats(triggering_initiative=current_init)
        
        # Phase 1d: Ranged Fire Resolution (fires into adjacent combat hexes)
        rangedfire_results = self._resolve_rangedfire(faction_id_values)
        logger.info(f"Ranged fire phase: {len(rangedfire_results)} attacks")
        
        # Phase 2: Combat Resolution
        combat_results = self._resolve_combat(current_init, round_side)
        combats_resolved = len(combat_results)
        units_killed = sum(len(r.units_killed) for r in combat_results)
        logger.info(f"Combat phase: {combats_resolved} combats, {units_killed} casualties")
        
        # Phase 2a: Kill cargo on sunken transports (transports destroyed at sea)
        cargo_killed = self._kill_cargo_on_sunken_transports()
        if cargo_killed > 0:
            logger.info(f"Sunken transport phase: {cargo_killed} cargo units lost at sea")
            units_killed += cargo_killed
        
        # Phase 2b: Post-Combat Destruction (uncontested occupation)
        destruction_results = self._check_uncontested_occupation()
        logger.info(f"Destruction check: {destruction_results['bases_destroyed']} bases, "
                   f"{destruction_results['expansions_destroyed']} expansions, "
                   f"{destruction_results['caravans_destroyed']} caravans destroyed")
        
        # Phase 3: Economic/Base Actions
        base_actions_resolved = self._resolve_base_actions(faction_id_values)
        logger.info(f"Economic phase: {base_actions_resolved} base actions resolved")
        
        # Clear orders for resolved factions
        for fid in faction_id_values:
            self.order_manager.clear_faction_orders(fid)
        
        # Reset units for NEXT turn (movement, road moves, fired status, light armor)
        # This happens at the END of resolution so units are ready for the next planning phase
        units_reset = self._reset_units_for_turn(faction_id_values)
        logger.info(f"Reset {units_reset} units for next turn")
        
        # Advance to next initiative/turn
        self._advance_turn()
        
        return ResolutionResult(
            success=True,
            message=f"Resolved turn for initiative {current_init}. {movements_applied} movements, {combats_resolved} combats, {base_actions_resolved} base actions.",
            movements_applied=movements_applied,
            combats_resolved=combats_resolved,
            units_killed=units_killed,
            base_actions_resolved=base_actions_resolved,
            combat_results=combat_results
        )
    
    # ==================== Transport Resolution ====================
    
    def _resolve_board_transport(self, faction_ids: List[int]) -> int:
        """
        Resolve all board transport orders for the given factions.
        
        This phase happens BEFORE movement so units can board and travel with the transport.
        
        Handles overload resolution:
        - If multiple factions try to board the same transport beyond capacity,
          same-faction units get priority, then random selection.
        
        Returns the number of units that successfully boarded.
        """
        import random
        game_log = get_game_log()
        
        # Collect all board transport orders, grouped by target transport
        transport_orders: Dict[int, List[tuple]] = {}  # transport_id -> [(unit_id, faction_id), ...]
        
        for faction_id in faction_ids:
            faction_orders = self.order_manager.faction_orders.get(faction_id)
            if not faction_orders:
                continue
            
            for order in faction_orders.board_transport_orders:
                if order.transport_id not in transport_orders:
                    transport_orders[order.transport_id] = []
                transport_orders[order.transport_id].append((order.unit_id, faction_id))
        
        if not transport_orders:
            return 0
        
        boards_completed = 0
        
        # Process each transport's boarding requests
        for transport_id, requests in transport_orders.items():
            transport = self.state.get_unit(transport_id)
            if not transport or not transport.alive or not transport.is_transport:
                logger.warning(f"Invalid transport {transport_id} - skipping board orders")
                continue
            
            # How many slots available?
            slots_available = transport.transport_slots_available
            if slots_available <= 0:
                logger.info(f"Transport {transport.name} is full - rejecting {len(requests)} board orders")
                continue
            
            # Get valid boarding units
            valid_requests = []
            transport_faction = transport.faction.value if hasattr(transport.faction, 'value') else transport.faction
            
            for unit_id, faction_id in requests:
                unit = self.state.get_unit(unit_id)
                if not unit or not unit.alive:
                    continue
                if unit.location != transport.location:
                    logger.warning(f"Unit {unit_id} not at transport location - skipping")
                    continue
                if unit.is_aboard_transport:
                    logger.warning(f"Unit {unit_id} already aboard a transport - skipping")
                    continue
                
                unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                valid_requests.append((unit_id, unit_faction))
            
            if not valid_requests:
                continue
            
            # If we have more requests than slots, resolve overload
            if len(valid_requests) > slots_available:
                # Priority 1: Same faction as transport
                same_faction = [(uid, fid) for uid, fid in valid_requests if fid == transport_faction]
                other_faction = [(uid, fid) for uid, fid in valid_requests if fid != transport_faction]
                
                selected = []
                
                # Take same-faction units first (up to slots available)
                for req in same_faction:
                    if len(selected) < slots_available:
                        selected.append(req)
                
                # Fill remaining slots randomly from other factions
                if len(selected) < slots_available and other_faction:
                    random.shuffle(other_faction)
                    for req in other_faction:
                        if len(selected) < slots_available:
                            selected.append(req)
                
                rejected = [req for req in valid_requests if req not in selected]
                if rejected:
                    logger.info(f"Transport overload: {len(rejected)} units rejected for {transport.name}")
                
                valid_requests = selected
            
            # Execute boarding
            for unit_id, _ in valid_requests:
                unit = self.state.get_unit(unit_id)
                if unit and unit.board_transport(transport):
                    boards_completed += 1
                    logger.info(f"{unit.name} boards {transport.name}")
                    
                    # Log the boarding event
                    game_log.log(
                        LogEventType.MOVEMENT,
                        f"{unit.name} (ID:{unit_id}) boards {transport.name}",
                        details={
                            "type": "board_transport",
                            "unit_id": unit_id,
                            "unit_name": unit.name,
                            "transport_id": transport_id,
                            "transport_name": transport.name,
                            "hex_id": transport.location
                        }
                    )
        
        return boards_completed
    
    def _resolve_unload_transports(self) -> int:
        """
        Automatically unload all transports that are NOT in ocean hexes.
        
        This phase happens after movement but before combat detection.
        Transports automatically unload when ending movement on:
        - Clear terrain hex with at least one clear coastal hexside
        
        Units unloading into a hex with enemies get amphibious penalties.
        
        Returns the number of units unloaded.
        """
        from .combat_special import check_amphibious_landing, execute_amphibious_landing
        game_log = get_game_log()
        
        unloads_completed = 0
        
        # Find all transports with cargo that are NOT in ocean hexes
        for unit in self.state.units.values():
            if not unit.alive or not unit.is_transport:
                continue
            
            # Skip if no cargo
            cargo_units = self.state.get_transport_cargo(unit.id)
            if not cargo_units:
                continue
            
            # Skip if in ocean (transport stays at sea)
            if self.state.is_ocean_hex(unit.location):
                continue
            
            # Transport is on land (must have coastal access) - unload!
            hex_obj = self.state.get_hex(unit.location)
            if not hex_obj:
                continue
            
            # Check for enemies (determines amphibious penalties)
            transport_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            transport_init = self.state.faction_initiative(transport_faction)
            units_at_hex = self.state.units_at_hex(unit.location)
            
            has_enemies = any(
                self.state.faction_initiative(
                    u.faction.value if hasattr(u.faction, 'value') else u.faction
                ) != transport_init
                for u in units_at_hex if u.alive and u.id != unit.id
            )
            
            # Unload each cargo unit
            for cargo in cargo_units:
                if cargo.disembark(unit.location, unit):
                    unloads_completed += 1
                    
                    # Apply amphibious penalties if contested landing
                    if has_enemies:
                        from .combat_special import apply_amphibious_penalties
                        apply_amphibious_penalties(cargo)
                        logger.info(f"{cargo.name} unloads from {unit.name} into combat (amphibious landing)")
                    else:
                        logger.info(f"{cargo.name} unloads from {unit.name}")
                    
                    # Log the unload event
                    game_log.log(
                        LogEventType.MOVEMENT,
                        f"{cargo.name} unloads from {unit.name}" + (" (amphibious)" if has_enemies else ""),
                        details={
                            "type": "unload_transport",
                            "unit_id": cargo.id,
                            "unit_name": cargo.name,
                            "transport_id": unit.id,
                            "transport_name": unit.name,
                            "hex_id": unit.location,
                            "amphibious": has_enemies
                        }
                    )
        
        return unloads_completed
    
    def _kill_cargo_on_sunken_transports(self) -> int:
        """
        Kill all cargo units aboard transports that have been destroyed.
        
        This handles the case where a transport is sunk at sea with units aboard.
        Cargo units go down with the ship.
        
        Returns the number of cargo units killed.
        """
        game_log = get_game_log()
        cargo_killed = 0
        
        # Find all units that are aboard a transport
        for unit in self.state.units.values():
            if not unit.alive or not unit.is_aboard_transport:
                continue
            
            # Check if the transport is dead
            transport = self.state.get_unit(unit.aboard_transport_id)
            if not transport or not transport.alive:
                # Transport is dead - unit goes down with it
                unit.hp = 0
                unit.alive = False
                cargo_killed += 1
                
                transport_name = transport.name if transport else f"transport {unit.aboard_transport_id}"
                logger.info(f"{unit.name} goes down with {transport_name}!")
                
                # Log the death
                game_log.log(
                    LogEventType.COMBAT_DEATH,
                    f"{unit.name} lost at sea with {transport_name}",
                    details={
                        "type": "transport_sinking",
                        "unit_id": unit.id,
                        "unit_name": unit.name,
                        "transport_id": unit.aboard_transport_id,
                        "transport_name": transport_name,
                        "cause": "transport_destroyed"
                    }
                )
        
        return cargo_killed
    
    # ==================== Movement Resolution ====================
    
    def _resolve_movement(self, faction_ids: List[int]) -> int:
        """
        Resolve all movement orders for the given factions.
        
        VALIDATED VERSION:
        1. Collect all movement orders
        2. Validate each step of each path
        3. Check hexside limits and resolve conflicts
        4. Apply valid moves step by step
        5. Stop units at combat or when validation fails
        
        Returns the number of movements applied.
        """
        movements_applied = 0
        
        # Collect all movement orders
        all_moves: Dict[int, List[int]] = {}
        for faction_id in faction_ids:
            faction_orders = self.order_manager.faction_orders.get(faction_id)
            if not faction_orders:
                continue
            
            for move_order in faction_orders.movement_orders:
                unit = self.state.get_unit(move_order.unit_id)
                if not unit or not unit.alive or not move_order.path:
                    continue
                all_moves[move_order.unit_id] = move_order.path
        
        if not all_moves:
            return 0
        
        # Collect hexside usage to check for conflicts
        hexside_usage = collect_hexside_usage(all_moves, self.state)
        
        # Resolve conflicts (units that exceed hexside limits)
        failed_moves = resolve_hexside_conflicts(hexside_usage)
        
        # Process each unit's movement
        for unit_id, path in all_moves.items():
            unit = self.state.get_unit(unit_id)
            if not unit:
                continue
            
            old_location = unit.location
            current_location = unit.location
            steps_completed = 0
            stop_reason = None
            
            # Check if this unit failed hexside limit check
            if unit_id in failed_moves:
                max_steps = failed_moves[unit_id]
            else:
                max_steps = len(path)
            
            # Process each step in the path
            for step_idx, next_hex in enumerate(path):
                if step_idx >= max_steps:
                    stop_reason = "hexside limit exceeded"
                    break
                
                # Validate this step
                enemies = self.state.enemies_at_hex(next_hex, 
                    unit.faction.value if hasattr(unit.faction, 'value') else unit.faction)
                is_combat = len(enemies) > 0
                
                validation = can_move(current_location, next_hex, unit, self.state, is_combat)
                
                if not validation.valid:
                    stop_reason = validation.message
                    break
                
                # Move is valid - apply it
                from_hex_before_move = current_location  # Save for road check
                unit.previous_location = current_location
                unit.location = next_hex
                current_location = next_hex
                steps_completed += 1
                
                # If this is a transport, move all cargo units with it
                if unit.is_transport:
                    cargo_units = self.state.get_transport_cargo(unit.id)
                    for cargo in cargo_units:
                        cargo.previous_location = from_hex_before_move
                        cargo.location = next_hex
                
                # Update road_move_only flag: if this hexside has no road, unit can no longer use road bonus
                # (Air units can never use road bonus - they always set road_move_only to False)
                if hasattr(unit, 'road_move_only') and unit.road_move_only:
                    has_road_on_hexside = self.state.has_road_between(from_hex_before_move, next_hex)
                    is_air_unit = hasattr(unit, 'unit_type') and (unit.unit_type == UnitType.AIR or unit.unit_type == 3)
                    if not has_road_on_hexside or is_air_unit:
                        unit.road_move_only = False
                
                # Deduct movement points
                if validation.uses_road_bonus:
                    if hasattr(unit, 'road_move_remaining'):
                        unit.road_move_remaining = max(0, unit.road_move_remaining - 1)
                else:
                    if hasattr(unit, 'movement_remaining'):
                        unit.movement_remaining = max(0, unit.movement_remaining - validation.movement_cost)
                
                # Stop if entering combat
                if validation.enters_combat:
                    stop_reason = "entered combat"
                    break
            
            # Log the result
            game_log = get_game_log()
            if steps_completed > 0:
                movements_applied += 1
                faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                # Build the full path including origin: [old_location, step1, step2, ...]
                full_path = [old_location] + path[:steps_completed]
                game_log.log_movement(
                    unit={
                        "id": unit.id,
                        "name": unit.name,
                        "faction_id": faction_id,
                        "faction_name": self.state.get_faction(faction_id).name if self.state.get_faction(faction_id) else "Unknown",
                        "location": unit.location,
                        "unit_type": unit.unit_type.value if hasattr(unit.unit_type, 'value') else unit.unit_type
                    },
                    path=full_path,
                    movement_used=steps_completed,
                    is_fast_travel=False
                )
                if stop_reason:
                    logger.info(f"  {unit.name}: {old_location} -> {unit.location} ({steps_completed} steps, stopped: {stop_reason})")
                else:
                    logger.info(f"  {unit.name}: {old_location} -> {unit.location} ({steps_completed} steps)")
            else:
                logger.info(f"  {unit.name}: Movement failed - {stop_reason or 'unknown'}")
        
        return movements_applied
    
    def _resolve_fast_travel(self, faction_ids: List[int]) -> int:
        """
        Resolve all fast travel orders (March for land, Full Sail for sea).
        
        Fast travel is simpler than regular movement:
        - No movement point deduction
        - No hexside limit checks
        - But still stops if entering hex with hostiles
        
        Returns the number of fast travel orders applied.
        """
        fast_travel_applied = 0
        game_log = get_game_log()
        
        for faction_id in faction_ids:
            faction_orders = self.order_manager.faction_orders.get(faction_id)
            if not faction_orders:
                continue
            
            for ft_order in faction_orders.fast_travel_orders:
                unit = self.state.get_unit(ft_order.unit_id)
                if not unit or not unit.alive or not ft_order.path:
                    continue
                
                old_location = unit.location
                current_location = unit.location
                steps_completed = 0
                stop_reason = None
                order_type = "Full Sail" if ft_order.is_naval else "March"
                
                # Process each step in the path
                for step_idx, next_hex in enumerate(ft_order.path):
                    # Check for hostile units at destination
                    unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                    enemies = self.state.enemies_at_hex(next_hex, unit_faction)
                    
                    if enemies:
                        stop_reason = "hostile units present"
                        break
                    
                    # Move is valid - apply it
                    from_hex = current_location
                    unit.previous_location = current_location
                    unit.location = next_hex
                    current_location = next_hex
                    steps_completed += 1
                    
                    # If this is a transport, move all cargo units with it
                    if unit.is_transport:
                        cargo_units = self.state.get_transport_cargo(unit.id)
                        for cargo in cargo_units:
                            cargo.previous_location = from_hex
                            cargo.location = next_hex
                
                # Log the result
                if steps_completed > 0:
                    fast_travel_applied += 1
                    full_path = [old_location] + ft_order.path[:steps_completed]
                    game_log.log_movement(
                        unit={
                            "id": unit.id,
                            "name": unit.name,
                            "faction_id": unit_faction,
                            "faction_name": self.state.get_faction(unit_faction).name if self.state.get_faction(unit_faction) else "Unknown",
                            "location": unit.location,
                            "unit_type": unit.unit_type.value if hasattr(unit.unit_type, 'value') else unit.unit_type
                        },
                        path=full_path,
                        movement_used=steps_completed,  # Use actual steps for fast travel too
                        is_fast_travel=True
                    )
                    if stop_reason:
                        logger.info(f"  {unit.name} ({order_type}): {old_location} -> {unit.location} ({steps_completed} steps, stopped: {stop_reason})")
                    else:
                        logger.info(f"  {unit.name} ({order_type}): {old_location} -> {unit.location} ({steps_completed} steps)")
                else:
                    logger.info(f"  {unit.name} ({order_type}): Fast travel failed - {stop_reason or 'unknown'}")
        
        return fast_travel_applied
    
    def _resolve_update_initiative(self) -> List[Dict]:
        """
        Update Initiative Phase - handles diplomatic changes that affect initiative.
        
        Currently handles:
        1. Troll Diplomacy - neutral troll tribes joining Amani
        
        Future:
        2. General Diplomacy - alliance/horde membership changes
        3. Treachery/Betrayal - initiative switches for surprise attacks
        
        Returns list of initiative change events (for logging).
        """
        events = []
        
        # Process Troll Diplomacy
        troll_events = self._resolve_troll_diplomacy()
        events.extend(troll_events)
        
        return events
    
    def _resolve_troll_diplomacy(self) -> List[Dict]:
        """
        Resolve Troll Diplomacy - neutral troll tribes joining Amani.
        
        Triggers:
        1. Alliance Attack: ALLIANCE_FACTIONS unit in neutral troll base/expansion hex
           → Tribe becomes Amani vassal, chieftain survives
        
        2. Zul'jin Alone in Base: Zul'jin (unit 0) alone in neutral troll base
           → Chieftain destroyed (if present), tribe becomes Amani vassal
        
        Note: "Zul'jin alone" means only Amani/Horde units present are Zul'jin
              (neutral troll faction's own units don't count)
        """
        from .models.enums import FactionId, NEUTRAL_TROLL_FACTIONS, ALLIANCE_FACTIONS
        
        events = []
        game_log = get_game_log()
        
        # Get Amani faction for vassal assignments
        amani_faction = self.state.factions.get(FactionId.AMANI.value)
        if not amani_faction:
            return events
        
        # Process each neutral troll faction
        for troll_faction_id in NEUTRAL_TROLL_FACTIONS:
            troll_fid = troll_faction_id.value
            troll_faction = self.state.factions.get(troll_fid)
            
            if not troll_faction:
                continue
            
            # Skip if already a vassal
            if troll_faction.vassal_of is not None:
                continue
            
            # Skip if defeated
            if troll_faction.is_defeated:
                continue
            
            # Find the troll faction's base(s)
            troll_bases = self.state.bases_by_faction(troll_fid)
            
            # Check Trigger 1: Alliance Attack on base or expansion
            alliance_attack = self._check_alliance_attack_on_troll(troll_fid, troll_bases)
            if alliance_attack:
                # Make vassal
                success = self.state.make_vassal(troll_fid, FactionId.AMANI.value)
                if success:
                    # Log the event
                    tribe_name = troll_faction.name
                    game_log.log(
                        LogEventType.DIPLOMACY,
                        f"The {tribe_name} has been attacked by the Alliance and has joined the Amani Empire!",
                        details={
                            "type": "troll_diplomacy",
                            "trigger": "alliance_attack",
                            "troll_faction_id": troll_fid,
                            "troll_faction_name": tribe_name,
                            "new_initiative": amani_faction.initiative
                        }
                    )
                    events.append({
                        "type": "troll_diplomacy",
                        "trigger": "alliance_attack",
                        "faction_id": troll_fid,
                        "faction_name": tribe_name
                    })
                    logger.info(f"  Troll Diplomacy: {tribe_name} joined Amani (Alliance attack)")
                continue  # Already joined, skip other checks
            
            # Check Trigger 2: Zul'jin Alone in Base
            zuljin_event = self._check_zuljin_in_troll_base(troll_fid, troll_bases)
            if zuljin_event:
                # Make vassal
                success = self.state.make_vassal(troll_fid, FactionId.AMANI.value)
                if success:
                    tribe_name = troll_faction.name
                    
                    if zuljin_event.get("chieftain_killed"):
                        # Zul'jin defeated chieftain
                        game_log.log(
                            LogEventType.DIPLOMACY,
                            f"Zul'jin has defeated the chieftain of the {tribe_name} in single combat, and has absorbed them into the Amani Empire.",
                            details={
                                "type": "troll_diplomacy",
                                "trigger": "zuljin_combat",
                                "troll_faction_id": troll_fid,
                                "troll_faction_name": tribe_name,
                                "chieftain_killed": True,
                                "chieftain_id": zuljin_event.get("chieftain_id"),
                                "new_initiative": amani_faction.initiative
                            }
                        )
                        logger.info(f"  Troll Diplomacy: {tribe_name} joined Amani (Zul'jin defeated chieftain)")
                    else:
                        # Chieftain already dead
                        game_log.log(
                            LogEventType.DIPLOMACY,
                            f"Zul'jin has brought the remains of the {tribe_name} into the Amani Empire.",
                            details={
                                "type": "troll_diplomacy",
                                "trigger": "zuljin_absorb",
                                "troll_faction_id": troll_fid,
                                "troll_faction_name": tribe_name,
                                "chieftain_killed": False,
                                "new_initiative": amani_faction.initiative
                            }
                        )
                        logger.info(f"  Troll Diplomacy: {tribe_name} joined Amani (Zul'jin absorbed remains)")
                    
                    events.append({
                        "type": "troll_diplomacy",
                        "trigger": "zuljin",
                        "faction_id": troll_fid,
                        "faction_name": tribe_name,
                        "chieftain_killed": zuljin_event.get("chieftain_killed", False)
                    })
        
        return events
    
    def _check_alliance_attack_on_troll(self, troll_faction_id: int, troll_bases: List) -> bool:
        """
        Check if any ALLIANCE_FACTIONS unit is in a neutral troll base or expansion hex.
        Returns True if an Alliance attack is detected.
        """
        from .models.enums import ALLIANCE_FACTIONS
        
        alliance_faction_ids = [f.value for f in ALLIANCE_FACTIONS]
        
        # Check each troll base
        for base in troll_bases:
            # Skip destroyed bases (tier 0)
            if base.tier == 0:
                continue
            
            # Check for Alliance units at base hex
            units_at_base = self.state.units_at_hex(base.location)
            for unit in units_at_base:
                unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                if unit_faction in alliance_faction_ids:
                    return True
            
            # Check expansions attached to this base
            for exp_id in base.expansions:
                expansion = self.state.get_expansion(exp_id)
                if not expansion:
                    continue
                
                units_at_exp = self.state.units_at_hex(expansion.location)
                for unit in units_at_exp:
                    unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                    if unit_faction in alliance_faction_ids:
                        return True
        
        # Also check expansions that might be orphaned (base destroyed but expansion still exists)
        for expansion in self.state.expansions.values():
            owning_base = self.state.get_base(expansion.base_id)
            if owning_base and owning_base.faction.value == troll_faction_id:
                units_at_exp = self.state.units_at_hex(expansion.location)
                for unit in units_at_exp:
                    unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                    if unit_faction in alliance_faction_ids:
                        return True
        
        return False
    
    def _check_zuljin_in_troll_base(self, troll_faction_id: int, troll_bases: List) -> Optional[Dict]:
        """
        Check if Zul'jin (unit ID 0) is alone in a neutral troll base.
        
        "Alone" means Zul'jin is the only non-troll unit in the hex.
        (Troll faction's own units don't prevent this trigger)
        
        Returns dict with event details if triggered, None otherwise.
        """
        ZULJIN_UNIT_ID = 0
        
        zuljin = self.state.get_unit(ZULJIN_UNIT_ID)
        if not zuljin or not zuljin.alive:
            return None
        
        zuljin_location = zuljin.location
        
        # Check each troll base
        for base in troll_bases:
            # Skip destroyed bases (tier 0) - cannot absorb
            if base.tier == 0:
                continue
            
            # Is Zul'jin at this base?
            if zuljin_location != base.location:
                continue
            
            # Zul'jin is at the base! Check if he's "alone"
            # (only non-troll unit in the hex)
            units_at_hex = self.state.units_at_hex(base.location)
            
            non_troll_units = []
            for unit in units_at_hex:
                unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                # Skip the troll faction's own units
                if unit_faction == troll_faction_id:
                    continue
                non_troll_units.append(unit)
            
            # Check if Zul'jin is the only non-troll unit
            if len(non_troll_units) == 1 and non_troll_units[0].id == ZULJIN_UNIT_ID:
                # Zul'jin is alone! Find and kill the chieftain (Tier 3 unit)
                chieftain = self._find_troll_chieftain(troll_faction_id)
                
                if chieftain and chieftain.alive:
                    # Kill the chieftain
                    chieftain.alive = False
                    chieftain.hp = 0
                    
                    # Log the death
                    game_log = get_game_log()
                    game_log.log_combat_death(
                        unit={
                            "id": chieftain.id,
                            "name": chieftain.name,
                            "faction_id": troll_faction_id,
                            "faction_name": self.state.factions.get(troll_faction_id).name if self.state.factions.get(troll_faction_id) else "Unknown",
                            "location": chieftain.location
                        },
                        killer={
                            "id": ZULJIN_UNIT_ID,
                            "name": zuljin.name,
                            "faction_id": zuljin.faction.value if hasattr(zuljin.faction, 'value') else zuljin.faction,
                            "faction_name": "Amani"
                        }
                    )
                    
                    return {
                        "chieftain_killed": True,
                        "chieftain_id": chieftain.id,
                        "chieftain_name": chieftain.name,
                        "base_id": base.id
                    }
                else:
                    # Chieftain already dead or not found
                    return {
                        "chieftain_killed": False,
                        "base_id": base.id
                    }
        
        return None
    
    def _find_troll_chieftain(self, troll_faction_id: int) -> Optional[Unit]:
        """
        Find the chieftain (Tier 3 unit) of a neutral troll faction.
        Each neutral troll faction should have exactly one Tier 3 unit.
        """
        troll_units = self.state.units_by_faction(troll_faction_id)
        
        for unit in troll_units:
            if unit.alive and unit.tier == 3:
                return unit
        
        return None
    
    def _is_zuljin_alone_at_troll_expansion(self, expansion, units_at_hex: List, expansion_faction_id: int) -> bool:
        """
        Check if Zul'jin is alone at a neutral troll expansion.
        
        Zul'jin alone at a neutral troll expansion does NOT destroy it.
        "Alone" means Zul'jin is the only non-troll unit present.
        
        Returns True if Zul'jin is alone at a neutral troll expansion.
        """
        from .models.enums import NEUTRAL_TROLL_FACTIONS
        
        ZULJIN_UNIT_ID = 0
        
        # Check if expansion belongs to a neutral troll faction
        neutral_troll_faction_ids = [f.value for f in NEUTRAL_TROLL_FACTIONS]
        if expansion_faction_id not in neutral_troll_faction_ids:
            return False
        
        # Check if Zul'jin is present
        zuljin_present = any(u.id == ZULJIN_UNIT_ID for u in units_at_hex if u.alive)
        if not zuljin_present:
            return False
        
        # Check if Zul'jin is the only non-troll unit
        non_troll_units = []
        for unit in units_at_hex:
            if not unit.alive:
                continue
            unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
            # Skip the troll faction's own units
            if unit_faction == expansion_faction_id:
                continue
            non_troll_units.append(unit)
        
        # Zul'jin is "alone" if he's the only non-troll unit
        if len(non_troll_units) == 1 and non_troll_units[0].id == ZULJIN_UNIT_ID:
            return True
        
        return False
    
    def _resolve_rangedfire(self, faction_ids: List[int]) -> List[Dict]:
        """
        Resolve all ranged fire orders for the given factions.
        
        Ranged Fire Rules:
        - Fires during EXTERIOR_SIEGE phase (first)
        - Can only target adjacent combat hexes
        - Unit cannot have moved this turn
        - Unit cannot be in a combat hex itself
        - Takes HEX terrain penalty (not hexside), except:
          - Mountain hexside: worse of hex or hexside (-20%)
          - Fortification hexside: hex penalty + fortification penalty (additive)
        - No flanking bonus
        
        Returns list of attack results.
        """
        from .game_config import get_game_config
        from .vision import get_adjacent_hexes
        
        results = []
        game_log = get_game_log()
        config = get_game_config()
        
        for faction_id in faction_ids:
            faction_orders = self.order_manager.faction_orders.get(faction_id)
            if not faction_orders:
                continue
            
            for rf_order in faction_orders.rangedfire_orders:
                unit = self.state.get_unit(rf_order.unit_id)
                if not unit or not unit.alive:
                    continue
                
                target_hex = rf_order.target_hex
                
                # Validate the target is still a valid combat hex
                if not self.state.is_combat_hex(target_hex):
                    logger.info(f"  {unit.name}: Ranged fire cancelled - hex {target_hex} no longer in combat")
                    continue
                
                # Get enemies in target hex (different initiative)
                unit_faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
                unit_init = self.state.faction_initiative(unit_faction_id)
                
                units_in_target = [u for u in self.state.units_at_hex(target_hex) if u.alive]
                enemies = [
                    u for u in units_in_target
                    if self.state.faction_initiative(u.faction.value if hasattr(u.faction, 'value') else u.faction) != unit_init
                    and u.unit_type in (UnitType.GROUND, UnitType.SEA)  # Siege can hit ground/sea
                ]
                
                if not enemies:
                    logger.info(f"  {unit.name}: Ranged fire cancelled - no valid targets")
                    continue
                
                # Select target (lowest HP first, then random)
                target = min(enemies, key=lambda u: (u.hp, u.id))
                
                # Calculate terrain modifier for ranged fire
                terrain_modifier = self._calculate_rangedfire_terrain(unit, target_hex)
                
                # Set the terrain bonus on the unit temporarily
                unit.terrain_bonus = terrain_modifier
                unit.flank_bonus = 0  # No flanking for ranged fire
                
                # Execute the attack using combat engine logic
                from .combat_engine import CombatEngine
                engine = CombatEngine(self.state, self.combat_mgr)
                attack_result = engine._execute_attack(unit, target)
                
                # Build result data
                result = {
                    "attacker_id": unit.id,
                    "attacker_name": unit.name,
                    "target_id": target.id,
                    "target_name": target.name,
                    "target_hex": target_hex,
                    "damage": attack_result.damage_dealt,
                    "target_killed": attack_result.target_killed,
                    "terrain_modifier": terrain_modifier
                }
                results.append(result)
                
                # Log the attack
                attacker_faction = self.state.get_faction(unit_faction_id)
                target_faction_id = target.faction.value if hasattr(target.faction, 'value') else target.faction
                target_faction = self.state.get_faction(target_faction_id)
                
                hit_text = f"HIT ({attack_result.damage_dealt} damage)" if attack_result.hits_rolled > 0 else "MISS"
                if attack_result.target_killed:
                    hit_text = f"💀 KILL ({attack_result.damage_dealt} damage)"
                
                # Build verbose data if enabled
                verbose_data = None
                if config.debug.verbose_combat_logs:
                    verbose_data = {
                        "individual_rolls": attack_result.individual_rolls,
                        "terrain_detail": {
                            "entry_hexside": "N/A (Ranged Fire)",
                            "hex_terrain": self._get_terrain_name(self.state.get_hex(target_hex).terrain if self.state.get_hex(target_hex) else 'C'),
                            "hex_modifier": terrain_modifier,
                            "did_enter": False,
                            "is_rangedfire": True
                        },
                        "armor_detail": attack_result.armor_detail,
                        "combat_breakdown": {
                            "base_combat": attack_result.base_combat,
                            "terrain_modifier": terrain_modifier,
                            "flank_bonus": 0,
                            "base_bonus": attack_result.base_bonus,
                            "effective_combat": attack_result.effective_combat
                        }
                    }
                
                game_log.log_combat_attack(
                    attacker={
                        "id": unit.id,
                        "name": unit.name,
                        "faction_id": unit_faction_id,
                        "faction_name": attacker_faction.name if attacker_faction else "Unknown"
                    },
                    defender={
                        "id": target.id,
                        "name": target.name,
                        "faction_id": target_faction_id,
                        "faction_name": target_faction.name if target_faction else "Unknown"
                    },
                    roll=attack_result.effective_combat,
                    hit=attack_result.hits_rolled > 0,
                    damage=attack_result.damage_dealt,
                    modifiers={
                        "base_combat": attack_result.base_combat,
                        "terrain": terrain_modifier,
                        "flanking": 0,
                        "base_bonus": attack_result.base_bonus,
                        "is_rangedfire": True
                    },
                    hits_rolled=attack_result.hits_rolled,
                    verbose_data=verbose_data
                )
                
                logger.info(f"  Ranged Fire: {unit.name} -> {target.name} @ hex {target_hex}: {hit_text}")
                
                # Mark unit as fired
                unit.fired = True
        
        return results
    
    def _calculate_rangedfire_terrain(self, attacker: 'Unit', target_hex: int) -> int:
        """
        Calculate terrain modifier for ranged fire.
        
        Rules:
        - Use HEX terrain penalty (not hexside)
        - Exception 1: Mountain hexside = worse of hex or hexside
        - Exception 2: Fortification hexside = hex penalty + fort penalty (additive)
        """
        from .game_config import get_game_config
        from .vision import get_adjacent_hexes
        
        config = get_game_config()
        target_hex_obj = self.state.get_hex(target_hex)
        if not target_hex_obj:
            return 0
        
        # Get hex terrain modifier
        hex_terrain = target_hex_obj.terrain
        terrain_modifiers = {
            'C': config.terrain.plains_terrain_penalty,
            'F': config.terrain.forest_terrain_penalty,
            'M': config.terrain.mountain_terrain_penalty,
            'S': config.terrain.swamp_terrain_penalty,
            'O': 0,
            'K': config.terrain.plains_terrain_penalty,
            'I': 0,
            'N': config.terrain.mountain_terrain_penalty,
            'Q': config.terrain.forest_terrain_penalty,
        }
        hex_modifier = terrain_modifiers.get(hex_terrain, 0)
        
        # Determine hexside terrain between attacker and target
        from .models.enums import Direction
        diff = target_hex - attacker.location
        direction_map = {
            -1: Direction.N, 1: Direction.S,
            -39: Direction.NW, 39: Direction.SE,
            -38: Direction.NE, 38: Direction.SW,
        }
        entry_direction = direction_map.get(diff)
        
        hexside_terrain = 'C'
        if entry_direction:
            # Get the hexside from the attacker's hex perspective
            side = self.state.get_hex(attacker.location)
            if side:
                hexside = side.get_side(entry_direction)
                if hexside:
                    hexside_terrain = hexside.terrain or 'C'
        
        # Check for mountain hexside (M = Mountain, N = Coastal Mountain)
        if hexside_terrain in ('M', 'N'):
            # Worse of hex or hexside (-20% for mountain)
            mountain_penalty = config.terrain.mountain_terrain_penalty
            return min(hex_modifier, mountain_penalty)
        
        # Check for fortification hexside
        if hexside_terrain == 'W':
            # Hex penalty + fortification penalty (additive)
            return hex_modifier + config.combat.fortification_penalty
        
        # Default: just hex terrain
        return hex_modifier
    
    def _get_terrain_name(self, terrain_code: str) -> str:
        """Get human-readable terrain name."""
        names = {
            'C': 'Clear', 'F': 'Forest', 'M': 'Mountain', 'S': 'Swamp',
            'O': 'Ocean', 'K': 'Coastal', 'I': 'Impassable', 'N': 'Coastal Mountain',
            'Q': 'Coastal Forest', 'R': 'River', 'W': 'Fortification'
        }
        return names.get(terrain_code, terrain_code)
    
    def _resolve_combat(self, current_initiative: int, round_side: str) -> List[CombatRoundResult]:
        """
        Resolve all combat that should happen after this initiative's turn.
        
        Combat Timing Rules:
        - Combat resolves after the lowest initiative of the current alignment
          that is involved in the combat.
        - Each combat gets exactly one round per alignment round.
        """
        results = []
        
        # Get combats that should resolve after this initiative
        combat_hexes = self.combat_mgr.get_combats_to_resolve_after_initiative(
            current_initiative, round_side
        )
        
        if not combat_hexes:
            return results
        
        engine = CombatEngine(self.state, self.combat_mgr)
        
        game_log = get_game_log()
        
        for hex_id in combat_hexes:
            combat = self.combat_mgr.get_combat(hex_id)
            if not combat:
                continue
            
            logger.info(f"Resolving combat at hex {hex_id}")
            
            # Check if this is a continuing combat
            is_continuing = not combat.is_new
            
            # Log combat start (or continuation)
            units_at_hex = self.state.units_at_hex(hex_id)
            combatants = [
                {
                    "id": u.id,
                    "name": u.name,
                    "faction_id": u.faction.value if hasattr(u.faction, 'value') else u.faction,
                    "faction_name": self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).name if self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction) else "Unknown",
                    "hp": u.hp,
                    "max_hp": u.max_hp,
                    "initiative": self.state.faction_initiative(u.faction.value if hasattr(u.faction, 'value') else u.faction)
                }
                for u in units_at_hex if u.alive
            ]
            game_log.log_combat_start(hex_id, combatants, is_continuing=is_continuing)
            
            # Assign combat modifiers before resolution, passing triggering initiative
            assign_combat_modifiers(hex_id, combat, self.state, triggering_initiative=current_initiative)
            
            # Resolve the combat round, passing triggering initiative for proper attacker/defender classification
            result = engine.resolve_combat_round(hex_id, triggering_initiative=current_initiative)
            
            # Check if verbose logging is enabled
            from tod.core.game_config import get_game_config
            config = get_game_config()
            verbose_enabled = config.debug.verbose_combat_logs
            
            # Log each attack with full details
            for attack in result.attacks:
                attacker = self.state.get_unit(attack.attacker_id)
                target = self.state.get_unit(attack.target_id)
                
                if attacker and target:
                    attacker_faction_id = attacker.faction.value if hasattr(attacker.faction, 'value') else attacker.faction
                    target_faction_id = target.faction.value if hasattr(target.faction, 'value') else target.faction
                    
                    # Build verbose data if enabled
                    verbose_data = None
                    if verbose_enabled:
                        # Build terrain detail - pass actual terrain modifier to determine if unit entered this round
                        terrain_detail = self._build_terrain_detail(attacker, hex_id, attack.terrain_modifier)
                        
                        verbose_data = {
                            "individual_rolls": attack.individual_rolls,
                            "terrain_detail": terrain_detail,
                            "armor_detail": attack.armor_detail,
                            "combat_breakdown": {
                                "base_combat": attack.base_combat,
                                "flanking": attack.flank_bonus,
                                "terrain": attack.terrain_modifier,
                                "base_bonus": attack.base_bonus,
                                "effective": attack.effective_combat
                            },
                            "target_hp": {
                                "before": attack.target_hp_before,
                                "after": attack.target_hp_after,
                                "max": attack.target_max_hp
                            },
                            "is_simultaneous": attack.is_simultaneous,
                            "simultaneous_with": attack.simultaneous_with
                        }
                    
                    game_log.log_combat_attack(
                        attacker={
                            "id": attacker.id,
                            "name": attacker.name,
                            "faction_id": attacker_faction_id,
                            "faction_name": self.state.get_faction(attacker_faction_id).name if self.state.get_faction(attacker_faction_id) else "Unknown",
                            "hp": attack.attacker_hp,  # HP at time of attack, not current HP
                            "location": attacker.location
                        },
                        defender={
                            "id": target.id,
                            "name": target.name,
                            "faction_id": target_faction_id,
                            "faction_name": self.state.get_faction(target_faction_id).name if self.state.get_faction(target_faction_id) else "Unknown",
                            "hp": target.hp,
                            "location": target.location
                        },
                        roll=attack.effective_combat,  # Using effective combat as the "roll result"
                        hit=attack.hits_rolled > 0,
                        damage=attack.damage_dealt,
                        modifiers={
                            "base_combat": attack.base_combat,
                            "flank_bonus": attack.flank_bonus,
                            "terrain_modifier": attack.terrain_modifier,
                            "base_bonus": attack.base_bonus,
                            "effective_combat": attack.effective_combat,
                            "hits_rolled": attack.hits_rolled
                        },
                        hits_rolled=attack.hits_rolled,
                        verbose_data=verbose_data
                    )
                    
                    # Log death if killed
                    if attack.target_killed:
                        game_log.log_combat_death(
                            unit={
                                "id": target.id,
                                "name": target.name,
                                "faction_id": target_faction_id,
                                "faction_name": self.state.get_faction(target_faction_id).name if self.state.get_faction(target_faction_id) else "Unknown",
                                "location": target.location
                            },
                            killer={
                                "id": attacker.id,
                                "name": attacker.name,
                                "faction_id": attacker_faction_id,
                                "faction_name": self.state.get_faction(attacker_faction_id).name if self.state.get_faction(attacker_faction_id) else "Unknown"
                            }
                        )
                        
                        # Log tier-up AFTER death (for proper ordering in logs)
                        if attack.tier_up_occurred:
                            game_log.log_combat_tier_up(
                                unit={
                                    "id": attacker.id,
                                    "name": attacker.name,
                                    "faction_id": attacker_faction_id,
                                    "faction_name": self.state.get_faction(attacker_faction_id).name if self.state.get_faction(attacker_faction_id) else "Unknown"
                                },
                                victim={
                                    "id": target.id,
                                    "name": target.name,
                                    "tier": target.tier
                                },
                                old_tier=attack.old_tier,
                                new_tier=attack.new_tier,
                                hex_id=hex_id
                            )
            
            # Log combat end - include remaining combatants
            remaining_initiatives = set()
            remaining_combatants = []
            for u in self.state.units_at_hex(hex_id):
                if u.alive:
                    fid = u.faction.value if hasattr(u.faction, 'value') else u.faction
                    remaining_initiatives.add(self.state.faction_initiative(fid))
                    remaining_combatants.append({
                        "id": u.id,
                        "name": u.name,
                        "faction_id": fid,
                        "faction_name": self.state.get_faction(fid).name if self.state.get_faction(fid) else "Unknown",
                        "hp": u.hp,
                        "max_hp": u.max_hp,
                        "initiative": self.state.faction_initiative(fid)
                    })
            
            victor = list(remaining_initiatives)[0] if len(remaining_initiatives) == 1 else None
            game_log.log_combat_end(
                hex_id=hex_id,
                victor_initiative=victor,
                casualties=[{"id": uid, "name": self.state.get_unit(uid).name if self.state.get_unit(uid) else f"Unit {uid}"} for uid in result.units_killed],
                remaining_combatants=remaining_combatants
            )
            
            # Reset units after combat round
            engine.reset_units_after_combat_round(hex_id)
            
            results.append(result)
            
            # If combat ended, clean up
            if result.combat_ended:
                logger.info(f"Combat at hex {hex_id} has ended")
        
        # Re-detect combats (some may have ended)
        self.combat_mgr.detect_combats()
        
        return results
    
    def _build_terrain_detail(self, attacker, hex_id: int, actual_terrain_modifier: int = 0) -> Dict:
        """Build terrain detail for verbose combat logging.
        
        Args:
            attacker: The attacking unit
            hex_id: The combat hex ID
            actual_terrain_modifier: The ACTUAL terrain modifier applied to this attack.
        """
        from tod.core.models.enums import Direction
        
        hex_obj = self.state.get_hex(hex_id)
        if not hex_obj:
            return {"error": "Hex not found"}
        
        # Terrain names for display
        terrain_names = {
            'C': 'Clear', 'F': 'Forest', 'M': 'Mountain', 'S': 'Swamp',
            'O': 'Ocean', 'K': 'Coastal Clear', 'R': 'River', 'W': 'Fortification',
            'I': 'Impassable', 'N': 'Coastal Mountain', 'Q': 'Coastal Forest',
            '': 'Clear'  # Empty string also means Clear
        }
        
        hex_terrain = hex_obj.terrain
        hex_terrain_name = terrain_names.get(hex_terrain, hex_terrain)
        
        # Check if unit actually moved this round (previous_location != current location)
        did_move = (attacker.previous_location is not None and 
                    attacker.previous_location != 0 and 
                    attacker.previous_location != attacker.location)
        
        # If unit didn't move, they're a defender - show "None" for entry hexside
        if not did_move:
            return {
                "entry_hexside": "None",
                "entry_hexside_terrain": None,
                "entry_hexside_modifier": 0,
                "hex_terrain": hex_terrain_name,
                "hex_modifier": 0,
                "did_enter": False
            }
        
        # Unit DID move - calculate which hexside they entered through
        entry_direction = None
        entry_hexside_terrain = None
        entry_hexside_name = "N/A"
        
        # Calculate direction from previous location
        if attacker.previous_location is not None:
            # Calculate direction
            diff = hex_id - attacker.previous_location
            direction_map = {
                -1: Direction.N,
                1: Direction.S,
                -39: Direction.NW,
                39: Direction.SE,
                -38: Direction.NE,
                38: Direction.SW,
            }
            entry_direction = direction_map.get(diff)
            
            if entry_direction:
                # Get hexside terrain (we need to look at the OPPOSITE direction on the hex)
                opposite_dir = entry_direction.opposite()
                hexside = hex_obj.get_side(opposite_dir)
                # Empty string or None means Clear hexside
                raw_terrain = hexside.terrain if hexside else ''
                entry_hexside_terrain = raw_terrain if raw_terrain else 'C'
                # Show the hexside from the combat hex's perspective (where they came FROM)
                entry_hexside_name = opposite_dir.name
        
        # Terrain modifiers for reference - pull from terrain config
        from .game_config import get_game_config
        config = get_game_config()
        terrain_modifiers = {
            '': 0,  # Empty = Clear
            'C': config.terrain.plains_terrain_penalty, 
            'F': config.terrain.forest_terrain_penalty, 
            'M': config.terrain.mountain_terrain_penalty, 
            'S': config.terrain.swamp_terrain_penalty, 
            'O': 0, 
            'K': config.terrain.plains_terrain_penalty,  # Coastal Clear = Plains
            'R': config.combat.river_crossing_penalty,
            'W': config.combat.fortification_penalty,
            'I': 0, 
            'N': config.terrain.mountain_terrain_penalty,  # Coastal Mountain
            'Q': config.terrain.forest_terrain_penalty     # Coastal Forest
        }
        
        hex_modifier = terrain_modifiers.get(hex_terrain, 0)
        
        # Get hexside terrain name and modifier (default to Clear if empty)
        hexside_terrain_name = terrain_names.get(entry_hexside_terrain, 'Clear')
        hexside_modifier = terrain_modifiers.get(entry_hexside_terrain, 0)
        
        return {
            "entry_hexside": entry_hexside_name,
            "entry_hexside_terrain": hexside_terrain_name,
            "entry_hexside_modifier": hexside_modifier,
            "hex_terrain": hex_terrain_name,
            "hex_modifier": hex_modifier,
            "did_enter": entry_direction is not None
        }
    
    def _check_uncontested_occupation(self) -> Dict[str, int]:
        """
        Check for enemy units occupying bases, expansions, or caravan hexes
        without friendly units to oppose them. Destroy uncontested assets.
        
        Called after combat resolution.
        
        Returns dict with counts of destroyed assets.
        """
        results = {
            'bases_destroyed': 0,
            'expansions_destroyed': 0,
            'caravans_destroyed': 0,
            'destroyed_base_names': [],
            'destroyed_expansion_hexes': [],
            'destroyed_caravan_routes': [],
        }
        
        game_log = get_game_log()
        
        # Check each base
        bases_to_destroy = []  # List of (base_id, occupying_units) tuples
        for base_id, base in self.state.bases.items():
            base_faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
            base_initiative = self.state.get_faction(base_faction_id).initiative if self.state.get_faction(base_faction_id) else -1
            
            # Get units at the base hex
            units_at_hex = self.state.units_at_hex(base.location)
            
            # Check if enemies are present with no friendlies
            friendly_present = any(
                (u.faction.value if hasattr(u.faction, 'value') else u.faction) == base_faction_id
                or self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).initiative == base_initiative
                for u in units_at_hex if u.alive
            )
            
            enemy_present = any(
                self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).initiative != base_initiative
                for u in units_at_hex if u.alive
            )
            
            if enemy_present and not friendly_present:
                logger.info(f"  Base {base.name} destroyed by uncontested occupation!")
                bases_to_destroy.append((base_id, units_at_hex))
                results['bases_destroyed'] += 1
                results['destroyed_base_names'].append(base.name)
        
        # Convert destroyed bases to tier 0 ruins (don't delete them!)
        for base_id, occupying_units in bases_to_destroy:
            base = self.state.bases.get(base_id)
            if base:
                # Determine who destroyed it (for logging)
                destroyer_faction_name = None
                if occupying_units:
                    first_enemy = next((u for u in occupying_units if u.alive), None)
                    if first_enemy:
                        enemy_faction = self.state.get_faction(
                            first_enemy.faction.value if hasattr(first_enemy.faction, 'value') else first_enemy.faction
                        )
                        if enemy_faction:
                            destroyer_faction_name = enemy_faction.name
                
                # Log the dramatic destruction!
                original_faction = self.state.get_faction(
                    base.faction.value if hasattr(base.faction, 'value') else base.faction
                )
                game_log.log_base_destroyed(
                    base={
                        "id": base.id,
                        "name": base.name,
                        "faction_name": original_faction.name if original_faction else "Unknown"
                    },
                    destroyer_faction=destroyer_faction_name,
                    hex_id=base.location
                )
                
                # Remove attached expansions
                for exp_id in base.expansions[:]:  # Copy list since we're modifying
                    if exp_id in self.state.expansions:
                        del self.state.expansions[exp_id]
                        results['expansions_destroyed'] += 1
                
                # Convert base to tier 0 ruins
                base.tier = 0
                base.gold = 0
                base.lumber = 0
                base.oil = 0
                base.actions = 0
                base.expansions = []
                # Keep the original name and faction for "Ruins of X" display
        
        # Check each expansion
        expansions_to_remove = []
        for exp_id, expansion in self.state.expansions.items():
            # Get the owning base
            owning_base = self.state.get_base(expansion.base_id)
            if not owning_base or owning_base.tier == 0:
                # Base was destroyed (tier 0 ruins), expansion should be removed too
                expansions_to_remove.append(exp_id)
                continue
            
            base_faction_id = owning_base.faction.value if hasattr(owning_base.faction, 'value') else owning_base.faction
            base_initiative = self.state.get_faction(base_faction_id).initiative if self.state.get_faction(base_faction_id) else -1
            
            # Get units at the expansion hex
            units_at_hex = self.state.units_at_hex(expansion.location)
            
            # Check if enemies are present with no friendlies
            friendly_present = any(
                self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).initiative == base_initiative
                for u in units_at_hex if u.alive
            )
            
            enemy_present = any(
                self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).initiative != base_initiative
                for u in units_at_hex if u.alive
            )
            
            if enemy_present and not friendly_present:
                # SPECIAL CASE: Zul'jin Alone at Neutral Troll Expansion
                # Zul'jin does NOT destroy neutral troll expansions
                if self._is_zuljin_alone_at_troll_expansion(expansion, units_at_hex, base_faction_id):
                    logger.info(f"  Expansion at hex {expansion.location} protected - Zul'jin alone at neutral troll expansion")
                    continue
                
                logger.info(f"  Expansion at hex {expansion.location} destroyed by uncontested occupation!")
                expansions_to_remove.append(exp_id)
                results['expansions_destroyed'] += 1
                results['destroyed_expansion_hexes'].append(expansion.location)
        
        # Remove destroyed expansions
        for exp_id in expansions_to_remove:
            if exp_id in self.state.expansions:
                # Also remove from owning base's expansion list
                expansion = self.state.expansions[exp_id]
                owning_base = self.state.get_base(expansion.base_id)
                if owning_base and exp_id in owning_base.expansions:
                    owning_base.expansions.remove(exp_id)
                del self.state.expansions[exp_id]
        
        # Check each caravan
        caravans_to_remove = []
        for idx, caravan in enumerate(self.state.caravans):
            caravan_initiative = caravan.initiative
            
            # Check each hex in the caravan path
            caravan_destroyed = False
            for hex_id in caravan.path:
                units_at_hex = self.state.units_at_hex(hex_id)
                
                # Check if enemies are present with no friendlies
                friendly_present = any(
                    self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).initiative == caravan_initiative
                    for u in units_at_hex if u.alive
                )
                
                enemy_present = any(
                    self.state.get_faction(u.faction.value if hasattr(u.faction, 'value') else u.faction).initiative != caravan_initiative
                    for u in units_at_hex if u.alive
                )
                
                if enemy_present and not friendly_present:
                    logger.info(f"  Caravan (bases {caravan.origin_base_id}↔{caravan.destination_base_id}) "
                               f"destroyed at hex {hex_id}!")
                    caravan_destroyed = True
                    break
            
            if caravan_destroyed:
                caravans_to_remove.append(idx)
                results['caravans_destroyed'] += 1
                results['destroyed_caravan_routes'].append((caravan.origin_base_id, caravan.destination_base_id))
        
        # Remove destroyed caravans (in reverse order to preserve indices)
        for idx in reversed(caravans_to_remove):
            self.state.caravans.pop(idx)
        
        return results
    
    def _resolve_base_actions(self, faction_ids: List[int]) -> int:
        """
        Resolve all pending base actions for the given factions.
        
        Base actions resolve ONCE per turn, tied to the faction's initiative.
        
        Resolution order:
        1. Auto-Harvest: Automatically collect resources from all bases (free action)
        2. Player-queued actions: Expand, Commerce, Upgrade, Rest, Build
        
        Returns the number of actions resolved.
        """
        actions_resolved = 0
        
        # =====================================================
        # PHASE 1: AUTO-HARVEST (free action for all bases)
        # =====================================================
        for faction_id in faction_ids:
            faction_bases = self.state.bases_by_faction(faction_id)
            
            for base in faction_bases:
                # Skip bases in combat (no actions allowed)
                if self.state.base_in_combat(base.id):
                    logger.debug(f"  {base.name} skipped auto-harvest: in combat")
                    continue
                
                # Calculate and apply harvest
                harvest_yield = self.state.calculate_harvest_yield(base.id)
                
                # Only log if there's actually something harvested
                if harvest_yield['gold'] > 0 or harvest_yield['lumber'] > 0 or harvest_yield['oil'] > 0:
                    base.add_resources(
                        gold=harvest_yield['gold'],
                        lumber=harvest_yield['lumber'],
                        oil=harvest_yield['oil']
                    )
                    
                    # Log to game log
                    game_log = get_game_log()
                    game_log.log_harvest(
                        base={
                            "id": base.id,
                            "name": base.name,
                            "faction_id": faction_id,
                            "faction_name": self.state.get_faction(faction_id).name if self.state.get_faction(faction_id) else "Unknown",
                            "location": base.location
                        },
                        yields=harvest_yield
                    )
                    
                    logger.info(
                        f"  {base.name} auto-harvested: "
                        f"+{harvest_yield['gold']} gold, "
                        f"+{harvest_yield['lumber']} lumber, "
                        f"+{harvest_yield['oil']} oil"
                    )
                    actions_resolved += 1
        
        # =====================================================
        # PHASE 2: PLAYER-QUEUED BASE ACTIONS
        # =====================================================
        for faction_id in faction_ids:
            faction_bases = self.state.bases_by_faction(faction_id)
            
            for base in faction_bases:
                orders = self.state.get_base_pending_orders(base.id)
                if not orders:
                    continue
                
                for order in orders:
                    # Skip legacy harvest orders (auto-harvest handles this now)
                    if order['type'] == 'harvest':
                        logger.debug(f"  {base.name} skipping manual harvest order (auto-harvest applied)")
                        continue
                    
                    elif order['type'] == 'expand':
                        # Re-validate at resolution time
                        target_hex = order['target_hex']
                        exp_type = order['expansion_type']
                        
                        # Check cost
                        if base.lumber < 2:
                            logger.warning(f"  {base.name} expand failed: not enough lumber")
                            continue
                        
                        # Check target still valid (no enemies, no new expansion)
                        faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
                        enemies = self.state.enemies_at_hex(target_hex, faction_id)
                        if enemies:
                            logger.warning(f"  {base.name} expand failed: enemies at target hex {target_hex}")
                            continue
                        
                        if self.state.expansion_at_hex(target_hex):
                            logger.warning(f"  {base.name} expand failed: expansion already at hex {target_hex}")
                            continue
                        
                        # Spend resources
                        base.spend_resources(lumber=2)
                        
                        # Create the expansion
                        expansion = self.state.create_expansion(base.id, target_hex, exp_type)
                        if expansion:
                            logger.info(
                                f"  {base.name} built {exp_type} at hex {target_hex}"
                            )
                            actions_resolved += 1
                        else:
                            logger.warning(f"  {base.name} expand failed: could not create expansion")
                            # Refund lumber
                            base.add_resources(lumber=2)
                    
                    elif order['type'] == 'commerce':
                        # Convert commerce_cost of one resource to commerce_gain of another
                        from .game_config import get_game_config
                        config = get_game_config()
                        commerce_cost = config.economic.commerce_cost
                        commerce_gain = config.economic.commerce_gain
                        
                        from_res = order.get('from_resource')
                        to_res = order.get('to_resource')
                        
                        # Check we have enough of source resource
                        current_from = getattr(base, from_res, 0)
                        if current_from < commerce_cost:
                            logger.warning(f"  {base.name} commerce failed: not enough {from_res}")
                            continue
                        
                        # Spend source, gain target
                        if from_res == 'gold':
                            base.spend_resources(gold=commerce_cost)
                        elif from_res == 'lumber':
                            base.spend_resources(lumber=commerce_cost)
                        elif from_res == 'oil':
                            base.spend_resources(oil=commerce_cost)
                        
                        if to_res == 'gold':
                            base.add_resources(gold=commerce_gain)
                        elif to_res == 'lumber':
                            base.add_resources(lumber=commerce_gain)
                        elif to_res == 'oil':
                            base.add_resources(oil=commerce_gain)
                        
                        logger.info(f"  {base.name} commerce: -{commerce_cost} {from_res} → +{commerce_gain} {to_res}")
                        actions_resolved += 1
                    
                    elif order['type'] == 'upgrade':
                        # Upgrade base tier
                        cost_gold = order.get('cost_gold', 0)
                        cost_lumber = order.get('cost_lumber', 0)
                        cost_oil = order.get('cost_oil', 0)
                        from_tier = order.get('from_tier', base.tier)
                        to_tier = order.get('to_tier', base.tier + 1)
                        
                        # Verify base can afford
                        if not base.can_afford(gold=cost_gold, lumber=cost_lumber, oil=cost_oil):
                            logger.warning(f"  {base.name} upgrade failed: not enough resources")
                            continue
                        
                        # Verify tier is still valid
                        if base.tier != from_tier:
                            logger.warning(f"  {base.name} upgrade failed: tier has changed")
                            continue
                        
                        # Spend resources
                        base.spend_resources(gold=cost_gold, lumber=cost_lumber, oil=cost_oil)
                        
                        # Upgrade tier
                        base.tier = to_tier
                        base.actions = to_tier  # Update available actions
                        
                        logger.info(
                            f"  {base.name} upgraded: Tier {from_tier} → Tier {to_tier} "
                            f"(-{cost_gold}g -{cost_lumber}l -{cost_oil}o)"
                        )
                        actions_resolved += 1
                    
                    elif order['type'] == 'rest':
                        # Rest Unit: heal a unit for gold cost from config
                        from .game_config import get_game_config
                        rest_config = get_game_config()
                        rest_cost = rest_config.economic.rest_cost
                        rest_heal_fraction = rest_config.economic.rest_heal_fraction
                        
                        unit_id = order.get('unit_id')
                        unit = self.state.get_unit(unit_id)
                        
                        if not unit or not unit.alive:
                            logger.warning(f"  {base.name} rest failed: unit not found or dead")
                            continue
                        
                        # Check unit is still at base
                        if unit.location != base.location:
                            logger.warning(f"  {base.name} rest failed: unit {unit.name} no longer at base")
                            continue
                        
                        # Check base can afford
                        if not base.can_afford(gold=rest_cost):
                            logger.warning(f"  {base.name} rest failed: not enough gold")
                            continue
                        
                        # Calculate healing (fraction of max HP rounded up)
                        import math
                        heal_amount = math.ceil(unit.max_hp * rest_heal_fraction)
                        old_hp = unit.hp
                        unit.hp = min(unit.hp + heal_amount, unit.max_hp)
                        actual_heal = unit.hp - old_hp
                        
                        # Spend gold
                        base.spend_resources(gold=rest_cost)
                        
                        # Log to game log
                        game_log = get_game_log()
                        game_log.log_rest_unit(
                            base={
                                "id": base.id,
                                "name": base.name,
                                "faction_id": faction_id,
                                "faction_name": self.state.get_faction(faction_id).name if self.state.get_faction(faction_id) else "Unknown",
                                "location": base.location
                            },
                            unit={
                                "id": unit.id,
                                "name": unit.name,
                                "faction_id": faction_id
                            },
                            heal_amount=actual_heal,
                            old_hp=old_hp,
                            new_hp=unit.hp
                        )
                        
                        logger.info(
                            f"  {base.name} rested {unit.name}: "
                            f"+{actual_heal} HP ({old_hp} → {unit.hp}/{unit.max_hp}) "
                            f"(-2 gold)"
                        )
                        actions_resolved += 1
                    
                    elif order['type'] == 'build_unit':
                        # Build Unit: create a new unit
                        unit_name = order.get('unit_name')
                        gold_cost = order.get('gold_cost', 0)
                        lumber_cost = order.get('lumber_cost', 0)
                        oil_cost = order.get('oil_cost', 0)
                        
                        # Check base can afford
                        if not base.can_afford(gold=gold_cost, lumber=lumber_cost, oil=oil_cost):
                            logger.warning(f"  {base.name} build {unit_name} failed: not enough resources")
                            continue
                        
                        # Check food cap
                        faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
                        food_status = self.state.faction_food_status(faction_id)
                        if food_status['food_surplus'] <= 0:
                            logger.warning(f"  {base.name} build {unit_name} failed: food cap reached")
                            continue
                        
                        # Spend resources
                        base.spend_resources(gold=gold_cost, lumber=lumber_cost, oil=oil_cost)
                        
                        # Create the unit
                        new_unit = self.state.create_unit(unit_name, faction_id, base.location)
                        if new_unit:
                            # Log to game log
                            game_log = get_game_log()
                            game_log.log_build_unit(
                                base={
                                    "id": base.id,
                                    "name": base.name,
                                    "faction_id": faction_id,
                                    "faction_name": self.state.get_faction(faction_id).name if self.state.get_faction(faction_id) else "Unknown",
                                    "location": base.location
                                },
                                unit_name=unit_name,
                                cost={"gold": gold_cost, "lumber": lumber_cost, "oil": oil_cost},
                                unit={
                                    "id": new_unit.id,
                                    "name": new_unit.name,
                                    "faction_id": faction_id
                                }
                            )
                            
                            logger.info(
                                f"  {base.name} built {unit_name} (ID {new_unit.id}) "
                                f"(-{gold_cost}g -{lumber_cost}l -{oil_cost}o)"
                            )
                            actions_resolved += 1
                        else:
                            logger.warning(f"  {base.name} build {unit_name} failed: unit creation error")
                            # Refund resources
                            base.add_resources(gold=gold_cost, lumber=lumber_cost, oil=oil_cost)
                    
                    elif order['type'] == 'establish_caravan':
                        # Establish Caravan: create a new caravan route
                        from .models.caravan import Caravan, CaravanTerrainType
                        
                        dest_base_id = order.get('dest_base_id')
                        path = order.get('path', [])
                        terrain_type_str = order.get('terrain_type', 'land')
                        lumber_cost = order.get('lumber_cost', 0)
                        oil_cost = order.get('oil_cost', 0)
                        
                        # Check base can afford
                        if not base.can_afford(lumber=lumber_cost, oil=oil_cost):
                            logger.warning(f"  {base.name} establish caravan failed: not enough resources")
                            continue
                        
                        # Re-validate the path (conditions may have changed)
                        is_sea = terrain_type_str == 'sea'
                        validation = self.state.validate_caravan_path(base.id, dest_base_id, path, is_sea)
                        if not validation['valid']:
                            logger.warning(f"  {base.name} establish caravan failed: {validation['error']}")
                            continue
                        
                        # Spend resources
                        base.spend_resources(lumber=lumber_cost, oil=oil_cost)
                        
                        # Create the caravan
                        faction_id = base.faction.value if hasattr(base.faction, 'value') else base.faction
                        faction = self.state.get_faction(faction_id)
                        initiative = faction.initiative if faction else 0
                        
                        terrain_type = CaravanTerrainType.SEA if is_sea else CaravanTerrainType.LAND
                        new_caravan = Caravan(
                            id=len(self.state.caravans),
                            origin_base_id=base.id,
                            destination_base_id=dest_base_id,
                            initiative=initiative,
                            path=path,
                            terrain_type=terrain_type
                        )
                        self.state.caravans.append(new_caravan)
                        
                        dest_base = self.state.get_base(dest_base_id)
                        dest_name = dest_base.name if dest_base else f"Base {dest_base_id}"
                        cost_str = f"-{lumber_cost}l" + (f" -{oil_cost}o" if oil_cost else "")
                        logger.info(
                            f"  {base.name} → {dest_name}: caravan established "
                            f"({len(path)} hexes, {terrain_type_str}) ({cost_str})"
                        )
                        actions_resolved += 1
                    
                    elif order['type'] == 'send_resources':
                        # Send Resources: transfer resources via caravan
                        dest_base_id = order.get('dest_base_id')
                        caravan_id = order.get('caravan_id')
                        gold = order.get('gold', 0)
                        lumber = order.get('lumber', 0)
                        oil = order.get('oil', 0)
                        
                        dest_base = self.state.get_base(dest_base_id)
                        dest_name = dest_base.name if dest_base else f"Base {dest_base_id}"
                        
                        # Check if caravan still exists (may have been destroyed in combat)
                        caravan_exists = any(c.id == caravan_id for c in self.state.caravans)
                        
                        if not caravan_exists:
                            # Caravan was destroyed! Resources are LOST
                            base.spend_resources(gold=gold, lumber=lumber, oil=oil)
                            logger.warning(
                                f"  {base.name} → {dest_name}: RESOURCES LOST! "
                                f"Caravan destroyed. ({gold}g {lumber}l {oil}o lost)"
                            )
                            actions_resolved += 1
                            continue
                        
                        # Check base can afford (should be able to, but verify)
                        if not base.can_afford(gold=gold, lumber=lumber, oil=oil):
                            logger.warning(f"  {base.name} send resources failed: not enough resources")
                            continue
                        
                        if not dest_base:
                            # Destination base was destroyed, resources lost
                            base.spend_resources(gold=gold, lumber=lumber, oil=oil)
                            logger.warning(
                                f"  {base.name} → {dest_name}: RESOURCES LOST! "
                                f"Destination destroyed. ({gold}g {lumber}l {oil}o lost)"
                            )
                            actions_resolved += 1
                            continue
                        
                        # Transfer resources
                        base.spend_resources(gold=gold, lumber=lumber, oil=oil)
                        dest_base.add_resources(gold=gold, lumber=lumber, oil=oil)
                        
                        resource_str = []
                        if gold: resource_str.append(f"{gold}g")
                        if lumber: resource_str.append(f"{lumber}l")
                        if oil: resource_str.append(f"{oil}o")
                        
                        logger.info(
                            f"  {base.name} → {dest_name}: sent {' '.join(resource_str)}"
                        )
                        actions_resolved += 1
                
                # Clear this base's pending orders after resolution
                self.state.clear_base_orders(base.id)
        
        return actions_resolved
    
    def resolve_end_of_round_combats(self) -> List[CombatRoundResult]:
        """
        Resolve any combats that haven't been fought this alignment round.
        
        Called at the end of each alignment round to catch combats where
        no participant from the current alignment triggered resolution.
        """
        round_side = self.state.turn.round_side.value if hasattr(self.state.turn.round_side, 'value') else str(self.state.turn.round_side)
        
        combat_hexes = self.combat_mgr.get_combats_for_end_of_round(round_side)
        
        if not combat_hexes:
            return []
        
        results = []
        engine = CombatEngine(self.state, self.combat_mgr)
        
        for hex_id in combat_hexes:
            combat = self.combat_mgr.get_combat(hex_id)
            if not combat:
                continue
            
            logger.info(f"End-of-round combat at hex {hex_id}")
            
            assign_combat_modifiers(hex_id, combat, self.state)
            result = engine.resolve_combat_round(hex_id)
            engine.reset_units_after_combat_round(hex_id)
            results.append(result)
        
        self.combat_mgr.detect_combats()
        
        return results
    
    def _advance_turn(self) -> None:
        """
        Advance to the next initiative or round.
        
        Logic:
        1. Mark current initiative as completed
        2. Find next initiative in the current round side
        3. If all initiatives for this side are done, switch sides
        4. If both sides are done, advance round number
        """
        current_init = self.state.turn.current_initiative
        
        # Mark this initiative as completed
        self.state.turn.completed_initiatives.add(current_init)
        
        # Get all initiatives for the current round side
        round_side = self.state.turn.round_side.value if hasattr(self.state.turn.round_side, 'value') else str(self.state.turn.round_side)
        
        if round_side == "HORDE":
            side_factions = self.state.HORDE_FACTIONS
        else:
            side_factions = self.state.ALLIANCE_FACTIONS
        
        # Get unique initiatives for this side (excluding -1)
        side_initiatives = sorted(set(
            self.state.factions.get(fid).initiative 
            for fid in side_factions 
            if fid in self.state.factions and self.state.factions[fid].initiative >= 0
        ))
        
        # Find remaining initiatives for this side
        remaining = [i for i in side_initiatives if i not in self.state.turn.completed_initiatives]
        
        if remaining:
            # Move to next initiative in this side
            self.state.turn.current_initiative = remaining[0]
            self.state.turn.orders_submitted.clear()
            print(f"  Advanced to initiative {self.state.turn.current_initiative}")
        else:
            # All initiatives for this side are done - switch sides
            self._switch_round_side()
    
    def _switch_round_side(self) -> None:
        """Switch from Horde to Alliance or vice versa, advancing round if needed."""
        current_side = self.state.turn.round_side
        
        # Resolve any end-of-round combats before switching
        end_of_round_results = self.resolve_end_of_round_combats()
        if end_of_round_results:
            logger.info(f"Resolved {len(end_of_round_results)} end-of-round combats")
        
        if current_side == RoundSide.HORDE:
            # Switch to Alliance
            self.state.turn.round_side = RoundSide.ALLIANCE
            self.state.turn.completed_initiatives.clear()
            
            # Reset combat round flags for new alignment round
            self.combat_mgr.reset_for_new_alignment_round()
            
            # Get first Alliance initiative
            alliance_initiatives = sorted(set(
                self.state.factions.get(fid).initiative 
                for fid in self.state.ALLIANCE_FACTIONS 
                if fid in self.state.factions and self.state.factions[fid].initiative >= 0
            ))
            
            if alliance_initiatives:
                self.state.turn.current_initiative = alliance_initiatives[0]
            
            logger.info(f"Switched to Alliance Round {self.state.turn.round_number}")
        else:
            # Switch to Horde and advance round number
            self.state.turn.round_side = RoundSide.HORDE
            self.state.turn.round_number += 1
            self.state.turn.completed_initiatives.clear()
            
            # Reset combat round flags for new alignment round
            self.combat_mgr.reset_for_new_alignment_round()
            
            # Get first Horde initiative
            horde_initiatives = sorted(set(
                self.state.factions.get(fid).initiative 
                for fid in self.state.HORDE_FACTIONS 
                if fid in self.state.factions and self.state.factions[fid].initiative >= 0
            ))
            
            if horde_initiatives:
                self.state.turn.current_initiative = horde_initiatives[0]
            
            logger.info(f"Started Horde Round {self.state.turn.round_number}")
        
        self.state.turn.orders_submitted.clear()
        self.state.turn.phase = GamePhase.PLANNING


# ============================================================================
# Convenience functions
# ============================================================================

def resolve_turn(state: GameState) -> ResolutionResult:
    """Convenience function to resolve the current turn."""
    engine = ResolutionEngine(state)
    return engine.resolve_current_turn()

