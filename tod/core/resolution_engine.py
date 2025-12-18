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
        
        # Phase 1: Movement Resolution
        movements_applied = self._resolve_movement(faction_id_values)
        logger.info(f"Movement phase: {movements_applied} units moved")
        
        # Detect new/updated combats after movement
        self.combat_mgr.detect_combats()
        
        # Phase 2: Combat Resolution
        combat_results = self._resolve_combat(current_init, round_side)
        combats_resolved = len(combat_results)
        units_killed = sum(len(r.units_killed) for r in combat_results)
        logger.info(f"Combat phase: {combats_resolved} combats, {units_killed} casualties")
        
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
                unit.previous_location = current_location
                unit.location = next_hex
                current_location = next_hex
                steps_completed += 1
                
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
            if steps_completed > 0:
                movements_applied += 1
                if stop_reason:
                    print(f"  {unit.name}: {old_location} -> {unit.location} ({steps_completed} steps, stopped: {stop_reason})")
                else:
                    print(f"  {unit.name}: {old_location} -> {unit.location} ({steps_completed} steps)")
            else:
                print(f"  {unit.name}: Movement failed - {stop_reason or 'unknown'}")
        
        return movements_applied
    
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
        
        for hex_id in combat_hexes:
            combat = self.combat_mgr.get_combat(hex_id)
            if not combat:
                continue
            
            logger.info(f"Resolving combat at hex {hex_id}")
            
            # Assign combat modifiers before resolution
            assign_combat_modifiers(hex_id, combat, self.state)
            
            # Resolve the combat round
            result = engine.resolve_combat_round(hex_id)
            
            # Reset units after combat round
            engine.reset_units_after_combat_round(hex_id)
            
            results.append(result)
            
            # If combat ended, clean up
            if result.combat_ended:
                logger.info(f"Combat at hex {hex_id} has ended")
        
        # Re-detect combats (some may have ended)
        self.combat_mgr.detect_combats()
        
        return results
    
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
        
        # Check each base
        bases_to_remove = []
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
                bases_to_remove.append(base_id)
                results['bases_destroyed'] += 1
                results['destroyed_base_names'].append(base.name)
        
        # Remove destroyed bases (and their expansions)
        for base_id in bases_to_remove:
            base = self.state.bases.get(base_id)
            if base:
                # Remove attached expansions
                for exp_id in base.expansions:
                    if exp_id in self.state.expansions:
                        del self.state.expansions[exp_id]
                        results['expansions_destroyed'] += 1
                del self.state.bases[base_id]
        
        # Check each expansion
        expansions_to_remove = []
        for exp_id, expansion in self.state.expansions.items():
            # Get the owning base
            owning_base = self.state.get_base(expansion.base_id)
            if not owning_base:
                # Base was destroyed, expansion should be too
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
                        # Convert 2 of one resource to 1 of another
                        from_res = order.get('from_resource')
                        to_res = order.get('to_resource')
                        
                        # Check we have enough of source resource
                        current_from = getattr(base, from_res, 0)
                        if current_from < 2:
                            logger.warning(f"  {base.name} commerce failed: not enough {from_res}")
                            continue
                        
                        # Spend source, gain target
                        if from_res == 'gold':
                            base.spend_resources(gold=2)
                        elif from_res == 'lumber':
                            base.spend_resources(lumber=2)
                        elif from_res == 'oil':
                            base.spend_resources(oil=2)
                        
                        if to_res == 'gold':
                            base.add_resources(gold=1)
                        elif to_res == 'lumber':
                            base.add_resources(lumber=1)
                        elif to_res == 'oil':
                            base.add_resources(oil=1)
                        
                        logger.info(f"  {base.name} commerce: -2 {from_res} → +1 {to_res}")
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
                        # Rest Unit: heal a unit for 2 gold
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
                        if not base.can_afford(gold=2):
                            logger.warning(f"  {base.name} rest failed: not enough gold")
                            continue
                        
                        # Calculate healing (1/4 max HP rounded up)
                        heal_amount = (unit.max_hp + 3) // 4
                        old_hp = unit.hp
                        unit.hp = min(unit.hp + heal_amount, unit.max_hp)
                        actual_heal = unit.hp - old_hp
                        
                        # Spend gold
                        base.spend_resources(gold=2)
                        
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
                        if food_status['surplus'] <= 0:
                            logger.warning(f"  {base.name} build {unit_name} failed: food cap reached")
                            continue
                        
                        # Spend resources
                        base.spend_resources(gold=gold_cost, lumber=lumber_cost, oil=oil_cost)
                        
                        # Create the unit
                        new_unit = self.state.create_unit(unit_name, faction_id, base.location)
                        if new_unit:
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

