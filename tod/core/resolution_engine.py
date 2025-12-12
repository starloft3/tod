"""
Resolution Engine - Processes orders and advances the game state.

This module handles the resolution phase of each turn:
1. Movement resolution
2. Combat resolution (TODO)
3. Economic actions (TODO)
4. Turn advancement

For now, we start with bare-bones movement: just apply moves without validation.
"""
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

from .game_state import GameState, GamePhase
from .order_manager import get_order_manager, OrderManager
from .movement import (
    can_move, validate_path, get_hexside_limit,
    collect_hexside_usage, resolve_hexside_conflicts,
    MoveResult
)


@dataclass
class ResolutionResult:
    """Result of a turn resolution."""
    success: bool
    message: str
    movements_applied: int = 0
    combats_triggered: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ResolutionEngine:
    """
    Handles the resolution of orders and turn advancement.
    
    Resolution phases:
    1. Movement - Units move along their ordered paths
    2. Combat - Battles are fought where enemies meet (TODO)
    3. Economic - Base actions are processed (TODO)
    4. Cleanup - Turn advances to next initiative
    """
    
    def __init__(self, state: GameState, order_manager: OrderManager = None):
        self.state = state
        self.order_manager = order_manager or get_order_manager()
    
    def resolve_current_turn(self) -> ResolutionResult:
        """
        Resolve all orders for the current initiative and advance the turn.
        
        This is the main entry point for turn resolution.
        """
        current_init = self.state.turn.current_initiative
        
        # Get factions in current initiative
        faction_ids = self.state.factions_in_initiative(current_init)
        faction_id_values = [f.value if hasattr(f, 'value') else int(f) for f in faction_ids]
        
        if not faction_id_values:
            return ResolutionResult(
                success=False,
                message=f"No factions found for initiative {current_init}"
            )
        
        # Phase 1: Movement Resolution
        movements_applied = self._resolve_movement(faction_id_values)
        
        # Phase 2: Combat Resolution (TODO)
        # combats = self._resolve_combat()
        
        # Phase 3: Economic Actions (TODO)
        # self._resolve_economic(faction_id_values)
        
        # Clear orders for resolved factions
        for fid in faction_id_values:
            self.order_manager.clear_faction_orders(fid)
        
        # Advance to next initiative/turn
        self._advance_turn()
        
        return ResolutionResult(
            success=True,
            message=f"Resolved turn for initiative {current_init}. {movements_applied} movements applied.",
            movements_applied=movements_applied,
            combats_triggered=0
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
        from .game_state import RoundSide
        
        current_side = self.state.turn.round_side
        
        if current_side == RoundSide.HORDE:
            # Switch to Alliance
            self.state.turn.round_side = RoundSide.ALLIANCE
            self.state.turn.completed_initiatives.clear()
            
            # Get first Alliance initiative
            alliance_initiatives = sorted(set(
                self.state.factions.get(fid).initiative 
                for fid in self.state.ALLIANCE_FACTIONS 
                if fid in self.state.factions and self.state.factions[fid].initiative >= 0
            ))
            
            if alliance_initiatives:
                self.state.turn.current_initiative = alliance_initiatives[0]
            
            print(f"  Switched to Alliance Round {self.state.turn.round_number}")
        else:
            # Switch to Horde and advance round number
            self.state.turn.round_side = RoundSide.HORDE
            self.state.turn.round_number += 1
            self.state.turn.completed_initiatives.clear()
            
            # Get first Horde initiative
            horde_initiatives = sorted(set(
                self.state.factions.get(fid).initiative 
                for fid in self.state.HORDE_FACTIONS 
                if fid in self.state.factions and self.state.factions[fid].initiative >= 0
            ))
            
            if horde_initiatives:
                self.state.turn.current_initiative = horde_initiatives[0]
            
            print(f"  Started Horde Round {self.state.turn.round_number}")
        
        self.state.turn.orders_submitted.clear()
        self.state.turn.phase = GamePhase.PLANNING


# ============================================================================
# Convenience functions
# ============================================================================

def resolve_turn(state: GameState) -> ResolutionResult:
    """Convenience function to resolve the current turn."""
    engine = ResolutionEngine(state)
    return engine.resolve_current_turn()

