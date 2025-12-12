"""
Combat Engine for Tides of Darkness.

This module implements the core combat resolution logic:
- Firing order (categories, defender/attacker or simultaneous)
- Attacker and target selection
- canHit rules (what can attack what)
- Damage calculation (combat + modifiers → d100 rolls)
- Armor system (light → heavy → natural)

Design Philosophy:
- New combat: Defenders fire first (prepared positions)
- Continuing combat: Simultaneous fire (chaotic melee)
- Categories always trump everything else in firing order
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, TYPE_CHECKING
from enum import IntEnum
from random import randint
import logging

if TYPE_CHECKING:
    from .game_state import GameState
    from .combat_manager import CombatManager, ActiveCombat

from .models import Unit, UnitCategory, UnitType, FactionId


# Set up logging for battle log
logger = logging.getLogger('combat')


class FiringCategory(IntEnum):
    """
    Firing order categories.
    Units fire in strict category order - ALL exterior siege before ANY ranged, etc.
    """
    EXTERIOR_SIEGE = 0  # Ranged fire from adjacent hex
    RANGED = 1          # Archers, ranged ships, dragons
    EXPERT = 2          # Reserved for veterancy abilities
    MELEE = 3           # Infantry, cavalry
    INTERIOR_SIEGE = 4  # Siege weapons in the combat hex
    NO_FIRE = 5         # Transports, captured units (never attack)


@dataclass
class AttackResult:
    """Result of a single attack."""
    attacker_id: int
    target_id: int
    hits_rolled: int          # Raw hits from d100 rolls
    damage_dealt: int         # After armor
    target_killed: bool
    effective_combat: int     # Combat value used (for logging)
    
    # Breakdown for battle log
    base_combat: int = 0
    flank_bonus: int = 0
    terrain_modifier: int = 0
    base_bonus: int = 0


@dataclass
class CombatRoundResult:
    """Result of a full combat round."""
    hex_id: int
    was_new_combat: bool
    attacks: List[AttackResult] = field(default_factory=list)
    units_killed: List[int] = field(default_factory=list)
    combat_ended: bool = False  # True if only one initiative remains
    
    @property
    def total_attacks(self) -> int:
        return len(self.attacks)
    
    @property
    def total_damage(self) -> int:
        return sum(a.damage_dealt for a in self.attacks)


class CombatEngine:
    """
    Core combat resolution engine.
    
    Usage:
        engine = CombatEngine(game_state, combat_manager)
        result = engine.resolve_combat_round(hex_id)
    """
    
    def __init__(self, game_state: 'GameState', combat_manager: 'CombatManager'):
        self.state = game_state
        self.combat_mgr = combat_manager
    
    # ==================== Main Resolution ====================
    
    def resolve_combat_round(self, hex_id: int) -> CombatRoundResult:
        """
        Resolve a single round of combat at a hex.
        
        This is the main entry point for combat resolution.
        """
        combat = self.combat_mgr.get_combat(hex_id)
        if not combat:
            logger.warning(f"No active combat at hex {hex_id}")
            return CombatRoundResult(hex_id=hex_id, was_new_combat=False)
        
        was_new = combat.is_new
        result = CombatRoundResult(hex_id=hex_id, was_new_combat=was_new)
        
        logger.info(f"=== Combat Round at Hex {hex_id} ({'NEW' if was_new else 'CONTINUING'}) ===")
        
        # Get all living units at this hex
        units = self.state.units_at_hex(hex_id)
        if len(units) < 2:
            logger.info("Combat ended - fewer than 2 units remain")
            result.combat_ended = True
            combat.mark_round_fought()
            return result
        
        # Classify units
        defenders = [u for u in units if u.previous_location == u.location]
        attackers = [u for u in units if u.previous_location != u.location]
        
        logger.info(f"Defenders: {len(defenders)}, Attackers: {len(attackers)}")
        
        # Resolve by category
        for category in FiringCategory:
            if category == FiringCategory.NO_FIRE:
                continue  # These units never fire
            
            category_attacks = self._resolve_category(
                hex_id, category, defenders, attackers, was_new, units
            )
            result.attacks.extend(category_attacks)
            
            # Track kills
            for attack in category_attacks:
                if attack.target_killed and attack.target_id not in result.units_killed:
                    result.units_killed.append(attack.target_id)
        
        # Mark combat round as fought
        combat.mark_round_fought()
        
        # Check if combat ended (only one initiative remains)
        remaining_initiatives = self._count_initiatives(hex_id)
        if remaining_initiatives < 2:
            result.combat_ended = True
            logger.info("Combat ended - only one initiative remains")
        
        logger.info(f"Round complete: {result.total_attacks} attacks, {len(result.units_killed)} units killed")
        
        return result
    
    def _resolve_category(
        self, 
        hex_id: int,
        category: FiringCategory,
        defenders: List[Unit],
        attackers: List[Unit],
        is_new: bool,
        all_units: List[Unit]
    ) -> List[AttackResult]:
        """Resolve all attacks for a single category."""
        attacks = []
        
        # Get units in this category
        def_in_cat = [u for u in defenders if u.category.value == category.value and u.hp > 0]
        atk_in_cat = [u for u in attackers if u.category.value == category.value and u.hp > 0]
        
        if not def_in_cat and not atk_in_cat:
            return attacks
        
        logger.debug(f"Category {category.name}: {len(def_in_cat)} defenders, {len(atk_in_cat)} attackers")
        
        if is_new:
            # NEW COMBAT: Defenders fire all, then attackers fire all
            attacks.extend(self._resolve_group_sequential(def_in_cat, all_units, "Defender"))
            attacks.extend(self._resolve_group_sequential(atk_in_cat, all_units, "Attacker"))
        else:
            # CONTINUING COMBAT: Simultaneous fire by HP tier
            all_in_cat = def_in_cat + atk_in_cat
            attacks.extend(self._resolve_simultaneous(all_in_cat, all_units))
        
        return attacks
    
    def _resolve_group_sequential(
        self, 
        group: List[Unit], 
        all_units: List[Unit],
        group_name: str
    ) -> List[AttackResult]:
        """
        Resolve attacks for a group sequentially (new combat).
        Highest HP fires first, damage applied immediately.
        """
        attacks = []
        
        # Sort by HP descending for firing order
        firing_order = sorted(group, key=lambda u: u.hp, reverse=True)
        
        for attacker in firing_order:
            if attacker.hp <= 0 or attacker.fired:
                continue
            
            # Find target
            target = self._choose_target(attacker, all_units)
            if not target:
                continue
            
            # Execute attack
            attack_result = self._execute_attack(attacker, target)
            attacks.append(attack_result)
            
            logger.info(
                f"{group_name} {attacker.name} (HP:{attacker.hp}) attacks "
                f"{target.name} (HP:{target.hp}) -> {attack_result.damage_dealt} damage"
            )
        
        return attacks
    
    def _resolve_simultaneous(
        self, 
        units_in_category: List[Unit],
        all_units: List[Unit]
    ) -> List[AttackResult]:
        """
        Resolve attacks simultaneously (continuing combat).
        
        All factions pick highest HP, calculate damage, THEN apply all at once.
        Repeat for next HP tier until all have fired.
        """
        attacks = []
        
        # Group by initiative
        by_initiative = self._group_by_initiative(units_in_category)
        
        # Keep firing until everyone has fired
        while True:
            # Collect attacks for this sub-round
            sub_round_attacks: List[Tuple[Unit, Unit, int]] = []  # (attacker, target, damage)
            
            any_fired = False
            for initiative, init_units in by_initiative.items():
                # Pick highest HP unfired unit
                attacker = self._choose_attacker(init_units, all_units)
                if not attacker:
                    continue
                
                target = self._choose_target(attacker, all_units)
                if not target:
                    attacker.fired = True  # Mark fired even with no target
                    continue
                
                # Calculate damage but don't apply yet
                hits, effective_combat, breakdown = self._calculate_damage(attacker, target)
                sub_round_attacks.append((attacker, target, hits, effective_combat, breakdown))
                attacker.fired = True
                any_fired = True
            
            if not any_fired:
                break
            
            # Apply all damage simultaneously
            for attacker, target, hits, effective_combat, breakdown in sub_round_attacks:
                damage = self._apply_damage(target, hits)
                
                attack_result = AttackResult(
                    attacker_id=attacker.id,
                    target_id=target.id,
                    hits_rolled=hits,
                    damage_dealt=damage,
                    target_killed=target.hp <= 0,
                    effective_combat=effective_combat,
                    base_combat=breakdown['base'],
                    flank_bonus=breakdown['flank'],
                    terrain_modifier=breakdown['terrain'],
                    base_bonus=breakdown['base_bonus']
                )
                attacks.append(attack_result)
                
                logger.info(
                    f"{attacker.name} attacks {target.name} -> "
                    f"{hits} hits, {damage} damage (simultaneous)"
                )
        
        return attacks
    
    # ==================== Selection Logic ====================
    
    def _choose_attacker(self, units: List[Unit], all_units: List[Unit]) -> Optional[Unit]:
        """
        Choose the next attacker from a group.
        
        Rules:
        - Has not fired this round
        - Has HP > 0
        - Has valid targets
        - Pick highest HP
        - Ties broken randomly
        """
        candidates = []
        highest_hp = 0
        
        for unit in units:
            if unit.fired or unit.hp <= 0:
                continue
            
            # Check if has valid targets
            if not self._has_valid_targets(unit, all_units):
                continue
            
            if unit.hp > highest_hp:
                candidates = [unit]
                highest_hp = unit.hp
            elif unit.hp == highest_hp:
                candidates.append(unit)
        
        if not candidates:
            return None
        
        # Random tiebreaker
        return candidates[randint(0, len(candidates) - 1)]
    
    def _choose_target(self, attacker: Unit, all_units: List[Unit]) -> Optional[Unit]:
        """
        Choose a target for an attacker.
        
        Rules:
        - Must be enemy (different initiative)
        - Must be hittable (canHit rules)
        - Must be alive
        - Pick highest HP
        - Ties broken randomly
        """
        attacker_initiative = self._get_unit_initiative(attacker)
        
        candidates = []
        highest_hp = 0
        
        for unit in all_units:
            if unit.hp <= 0:
                continue
            
            # Must be enemy
            target_initiative = self._get_unit_initiative(unit)
            if target_initiative == attacker_initiative:
                continue
            
            # Must be hittable
            if not self._can_hit(attacker, unit):
                continue
            
            if unit.hp > highest_hp:
                candidates = [unit]
                highest_hp = unit.hp
            elif unit.hp == highest_hp:
                candidates.append(unit)
        
        if not candidates:
            return None
        
        return candidates[randint(0, len(candidates) - 1)]
    
    def _has_valid_targets(self, attacker: Unit, all_units: List[Unit]) -> bool:
        """Check if an attacker has any valid targets."""
        attacker_initiative = self._get_unit_initiative(attacker)
        
        for unit in all_units:
            if unit.hp <= 0:
                continue
            target_initiative = self._get_unit_initiative(unit)
            if target_initiative != attacker_initiative and self._can_hit(attacker, unit):
                return True
        return False
    
    # ==================== Can Hit Rules ====================
    
    def _can_hit(self, attacker: Unit, target: Unit) -> bool:
        """
        Determine if an attacker can hit a target.
        
        Rules by attacker category and type:
        - Siege (ext/int): Can hit Ground, Sea
        - Ranged Ground: Can hit Ground, Air
        - Ranged Sea: Can hit Sea, Air
        - Ranged Air: Can hit EVERYTHING
        - Melee: Can hit Ground only
        
        Note: EXTERIOR_SIEGE units cannot be targeted (they're "ghosts")
        """
        # Exterior siege cannot be targeted
        if target.category == UnitCategory.EXTERIOR_SIEGE:
            return False
        
        attacker_cat = attacker.category
        attacker_type = attacker.unit_type
        target_type = target.unit_type
        
        # Siege weapons (exterior and interior) can hit ground and sea
        if attacker_cat in (UnitCategory.EXTERIOR_SIEGE, UnitCategory.INTERIOR_SIEGE):
            return target_type in (UnitType.GROUND, UnitType.SEA)
        
        # Ranged units
        if attacker_cat == UnitCategory.RANGED:
            if attacker_type == UnitType.GROUND:
                return target_type in (UnitType.GROUND, UnitType.AIR)
            elif attacker_type == UnitType.SEA:
                return target_type in (UnitType.SEA, UnitType.AIR)
            elif attacker_type == UnitType.AIR:
                return True  # Air ranged can hit everything
        
        # Expert category (for now, treat like ranged)
        if attacker_cat == UnitCategory.EXPERT:
            if attacker_type == UnitType.GROUND:
                return target_type in (UnitType.GROUND, UnitType.AIR)
            elif attacker_type == UnitType.AIR:
                return True
        
        # Melee can only hit ground
        if attacker_cat == UnitCategory.MELEE:
            return target_type == UnitType.GROUND
        
        return False
    
    # ==================== Damage Calculation ====================
    
    def _execute_attack(self, attacker: Unit, target: Unit) -> AttackResult:
        """Execute an attack and apply damage immediately."""
        hits, effective_combat, breakdown = self._calculate_damage(attacker, target)
        damage = self._apply_damage(target, hits)
        
        attacker.fired = True
        
        # Clear one-time bonuses after attacking
        attacker.flank_bonus = 0
        attacker.terrain_bonus = 0
        attacker.hold_bonus = 0
        
        return AttackResult(
            attacker_id=attacker.id,
            target_id=target.id,
            hits_rolled=hits,
            damage_dealt=damage,
            target_killed=target.hp <= 0,
            effective_combat=effective_combat,
            base_combat=breakdown['base'],
            flank_bonus=breakdown['flank'],
            terrain_modifier=breakdown['terrain'],
            base_bonus=breakdown['base_bonus']
        )
    
    def _calculate_damage(self, attacker: Unit, target: Unit) -> Tuple[int, int, dict]:
        """
        Calculate damage from an attack.
        
        Returns: (hits_rolled, effective_combat, breakdown_dict)
        
        Formula:
            Effective Combat = COMBAT + FLANK + TERRAIN + BASE_BONUS
            Clamped to [10, 90]
            Roll d100 for each attacker HP
            Each roll ≤ effective_combat = 1 hit
        """
        # Base combat (includes veterancy via effective_combat property)
        base = attacker.effective_combat
        
        # Modifiers
        flank = attacker.flank_bonus
        terrain = attacker.terrain_bonus
        
        # Base bonus (fighting near friendly base)
        base_bonus = self._get_base_combat_bonus(attacker)
        
        # Air targets ignore terrain
        if target.unit_type == UnitType.AIR:
            terrain = 0
        
        # Calculate effective combat
        effective = base + flank + terrain + base_bonus
        
        # Clamp to 10-90
        effective = max(10, min(90, effective))
        
        breakdown = {
            'base': base,
            'flank': flank,
            'terrain': terrain,
            'base_bonus': base_bonus
        }
        
        # Roll for hits
        hits = 0
        for _ in range(attacker.hp):
            roll = randint(1, 100)
            if roll <= effective:
                hits += 1
        
        logger.debug(
            f"Damage calc: {attacker.name} combat={effective} "
            f"(base={base}, flank={flank}, terrain={terrain}, base_bonus={base_bonus}), "
            f"HP={attacker.hp}, hits={hits}"
        )
        
        return hits, effective, breakdown
    
    def _get_base_combat_bonus(self, unit: Unit) -> int:
        """
        Get combat bonus from fighting near a friendly base.
        
        Default implementation: Only units whose faction matches base faction get bonus.
        (Alternate versions can be implemented per spec)
        """
        base = self.state.base_at_hex(unit.location)
        if not base:
            return 0
        
        # Check faction match
        unit_faction = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        base_faction = base.faction.value if hasattr(base.faction, 'value') else base.faction
        
        if unit_faction != base_faction:
            return 0
        
        # Tier-based bonus
        tier = base.tier if hasattr(base, 'tier') else 1
        if tier == 1:
            return 0
        elif tier == 2:
            return 5
        elif tier >= 3:
            return 10
        
        return 0
    
    # ==================== Armor System ====================
    
    def _apply_damage(self, target: Unit, hits: int) -> int:
        """
        Apply damage to a target, passing through armor layers.
        
        Returns actual HP damage dealt.
        
        Armor layers (in order):
        1. Light Armor - ablative, consumed 1:1
        2. Heavy Armor - threshold, blocks if hits ≤ value, breaks if exceeded
        3. Natural Armor - permanent DR, always subtracts
        """
        if hits <= 0:
            return 0
        
        remaining = hits
        original_hits = hits
        
        # Layer 1: Light Armor (ablative)
        if target.light_armor_current > 0:
            absorbed = min(remaining, target.light_armor_current)
            target.light_armor_current -= absorbed
            remaining -= absorbed
            
            if absorbed > 0:
                logger.debug(f"Light armor absorbed {absorbed} hits, {target.light_armor_current} remaining")
        
        if remaining <= 0:
            return 0
        
        # Layer 2: Heavy Armor (threshold)
        if not target.armor_broken and target.heavy_armor > 0:
            if remaining <= target.heavy_armor:
                # Attack didn't penetrate
                logger.debug(f"Heavy armor ({target.heavy_armor}) blocked {remaining} hits")
                return 0
            else:
                # Armor broken, reduce damage by armor value
                target.armor_broken = True
                remaining -= target.heavy_armor
                logger.debug(f"Heavy armor broken! {remaining} hits penetrate")
        
        if remaining <= 0:
            return 0
        
        # Layer 3: Natural Armor (permanent DR)
        if target.natural_armor > 0:
            remaining -= target.natural_armor
            if remaining < 0:
                remaining = 0
            logger.debug(f"Natural armor reduced damage to {remaining}")
        
        if remaining <= 0:
            return 0
        
        # Apply final damage
        actual_damage = min(remaining, target.hp)  # Can't overkill
        target.hp -= actual_damage
        
        if target.hp <= 0:
            target.hp = 0
            target.alive = False
            logger.info(f"{target.name} has been killed!")
        
        return actual_damage
    
    # ==================== Helper Methods ====================
    
    def _get_unit_initiative(self, unit: Unit) -> int:
        """Get the initiative value for a unit's faction."""
        faction_id = unit.faction.value if hasattr(unit.faction, 'value') else unit.faction
        faction = self.state.factions.get(faction_id)
        return faction.initiative if faction else -1
    
    def _group_by_initiative(self, units: List[Unit]) -> Dict[int, List[Unit]]:
        """Group units by their initiative."""
        by_init: Dict[int, List[Unit]] = {}
        for unit in units:
            init = self._get_unit_initiative(unit)
            if init not in by_init:
                by_init[init] = []
            by_init[init].append(unit)
        return by_init
    
    def _count_initiatives(self, hex_id: int) -> int:
        """Count how many different initiatives have living units at a hex."""
        units = self.state.units_at_hex(hex_id)
        initiatives = set()
        for unit in units:
            if unit.hp > 0:
                initiatives.add(self._get_unit_initiative(unit))
        return len(initiatives)
    
    # ==================== Post-Combat Reset ====================
    
    def reset_units_after_combat_round(self, hex_id: int) -> None:
        """
        Reset unit state after a combat round.
        
        Resets:
        - fired flag
        - light_armor_current (restored to max)
        - armor_broken flag
        """
        units = self.state.units_at_hex(hex_id)
        for unit in units:
            unit.fired = False
            unit.light_armor_current = unit.light_armor_max
            unit.armor_broken = False
    
    def reset_all_units_for_new_turn(self) -> None:
        """Reset all units for a new turn (called at turn start)."""
        for unit in self.state.units.values():
            if unit.alive:
                unit.reset_for_turn()


# ==================== Convenience Functions ====================

def resolve_combat(game_state: 'GameState', combat_manager: 'CombatManager', hex_id: int) -> CombatRoundResult:
    """Convenience function to resolve a combat round."""
    engine = CombatEngine(game_state, combat_manager)
    result = engine.resolve_combat_round(hex_id)
    engine.reset_units_after_combat_round(hex_id)
    return result


def resolve_all_pending_combats(
    game_state: 'GameState', 
    combat_manager: 'CombatManager',
    initiative: int,
    round_side: str
) -> List[CombatRoundResult]:
    """
    Resolve all combats that should fire after the given initiative turn.
    
    Returns list of combat results.
    """
    results = []
    
    # Get combats to resolve
    combat_hexes = combat_manager.get_combats_to_resolve_after_initiative(initiative, round_side)
    
    engine = CombatEngine(game_state, combat_manager)
    
    for hex_id in combat_hexes:
        result = engine.resolve_combat_round(hex_id)
        engine.reset_units_after_combat_round(hex_id)
        results.append(result)
    
    return results


def resolve_end_of_round_combats(
    game_state: 'GameState',
    combat_manager: 'CombatManager', 
    round_side: str
) -> List[CombatRoundResult]:
    """
    Resolve combats at end of alignment round (catch-all for combats
    where no participant from current alignment triggered resolution).
    """
    results = []
    
    combat_hexes = combat_manager.get_combats_for_end_of_round(round_side)
    
    engine = CombatEngine(game_state, combat_manager)
    
    for hex_id in combat_hexes:
        result = engine.resolve_combat_round(hex_id)
        engine.reset_units_after_combat_round(hex_id)
        results.append(result)
    
    return results

