"""
Unit models for Tides of Darkness.

Units have two parts:
- UnitStats: The template data for a unit type (e.g., "Grunt" stats)
- Unit: An actual unit instance in the game with current state
"""
from dataclasses import dataclass, field
from typing import Optional, List
from .enums import UnitCategory, UnitType, FactionId


@dataclass
class UnitStats:
    """
    Template stats for a unit type. Loaded from the unitstats database table.
    These values don't change during gameplay - they define what a unit type IS.
    """
    name: str
    max_hp: int
    combat: int                    # Base combat value (damage dealt)
    category: UnitCategory         # Firing order category
    unit_type: UnitType           # Ground/Air/Sea
    light_armor: int              # Light armor points
    heavy_armor: int              # Heavy armor points
    natural_armor: int            # Natural armor points
    movement: int                 # Base movement points
    vision: int                   # Vision range in hexes
    stealth: int = 0              # Stealth capability
    gold_cost: int = 0            # Cost to build
    lumber_cost: int = 0
    oil_cost: int = 0
    min_tier: int = 1             # Minimum base tier to build
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'UnitStats':
        """Create UnitStats from a database row (unitstats table)."""
        return cls(
            name=row[0],
            max_hp=int(row[1]),
            combat=int(row[2]),
            category=UnitCategory(int(row[3])),
            unit_type=UnitType(int(row[4])),
            light_armor=int(row[5]),
            heavy_armor=int(row[6]),
            natural_armor=int(row[7]),
            movement=int(row[8]),
            vision=int(row[9]),
            stealth=int(row[10]) if len(row) > 10 and row[10] is not None else 0,
            gold_cost=int(row[11]) if len(row) > 11 else 0,
            lumber_cost=int(row[12]) if len(row) > 12 else 0,
            oil_cost=int(row[13]) if len(row) > 13 else 0,
            min_tier=int(row[14]) if len(row) > 14 else 1,
        )


@dataclass
class Unit:
    """
    A unit instance in the game. Has both static stats (from UnitStats)
    and dynamic state that changes during gameplay.
    """
    # Identity
    id: int                        # Unique unit ID (index in allunits list)
    name: str                      # Unit type name (e.g., "Grunt")
    faction: FactionId             # Owning faction
    
    # Stats (copied from UnitStats, but can be modified by veterancy)
    max_hp: int
    combat: int
    category: UnitCategory
    unit_type: UnitType
    light_armor_max: int           # Maximum light armor
    heavy_armor: int
    natural_armor: int
    movement_max: int
    vision: int
    stealth: int = 0
    
    # Current State
    hp: int = 0                    # Current hit points
    location: int = 0              # Current hex ID
    alive: bool = True
    
    # Veterancy
    tier: int = 0                  # Veterancy tier (0-4)
    tier_1_ability: str = 'none'   # Name of tier 1 ability
    tier_2_ability: str = 'none'
    tier_3_ability: str = 'none'
    tier_4_ability: str = 'none'
    tier_1_data: int = 0           # Additional data for tier 1 ability
    tier_2_data: int = 0
    tier_3_data: int = 0
    tier_4_data: int = 0
    
    # Combat State (reset each combat/turn)
    hex_duration: int = 0          # Turns spent in current hex
    fired: bool = False            # Has attacked this combat round
    light_armor_current: int = 0   # Current light armor (regenerates)
    armor_broken: bool = False     # Armor broken this combat
    terrain_bonus: int = 0         # Terrain defensive bonus
    flank_bonus: int = 0           # Flanking attack bonus
    hold_bonus: int = 0            # Holding position bonus
    combat_start: int = 0          # Combat value at start of battle
    
    # Movement State
    movement_remaining: int = 0    # Movement points left this turn
    road_move_remaining: int = 0   # Road movement points left
    road_move_only: bool = False   # Can only move on roads
    previous_location: int = 0     # Last hex (for retreat calculation)
    
    # Transport
    transport_slot_1: int = -1     # Unit ID in transport slot 1 (-1 = empty)
    transport_slot_2: int = -1
    transport_slot_3: int = -1
    
    def __post_init__(self):
        """Initialize derived values after creation."""
        if self.hp == 0:
            self.hp = self.max_hp
        if self.light_armor_current == 0:
            self.light_armor_current = self.light_armor_max
        if self.movement_remaining == 0:
            self.movement_remaining = self.movement_max
    
    @property
    def is_transport(self) -> bool:
        """Check if this unit can carry other units."""
        return self.category == UnitCategory.NO_FIRE and self.name in [
            'Horde Transport', 'Alliance Transport'
        ]
    
    @property
    def is_hero(self) -> bool:
        """Check if this unit is a hero (unique named character)."""
        # Heroes have names that aren't standard unit types
        standard_units = {
            'Grunt', 'Berserker', 'Axethrower', 'Ogre', 'Catapult', 'Death Knight',
            'Wave Rider', 'Turtle', 'Juggernaut', 'Horde Transport', 'Dragon',
            'Raider', 'Shaman', 'Warlock', 'Footman', 'Archer', 'Knight', 'Ballista',
            'Mage', 'Destroyer', 'Submarine', 'Battleship', 'Alliance Transport',
            'Gryphon', 'Dwarf', 'Swordsman', 'Wildhammer Shaman', 'Rogue',
            'Skeleton', 'Demon', 'Elemental', 'Mountaineer'
        }
        return self.name not in standard_units
    
    @property
    def effective_combat(self) -> int:
        """
        Combat value including veterancy bonus.
        
        Note: The database (saveunits) already has the tier bonus pre-computed
        into the combat field (done by legacy server.py lines 378-380), so we
        just return self.combat directly. DO NOT add tier bonus again here.
        """
        if self.category == UnitCategory.NO_FIRE:
            return 0
        return self.combat
    
    @property
    def effective_max_hp(self) -> int:
        """
        Max HP including veterancy bonus.
        
        Note: The database (saveunits) already has the tier bonus pre-computed
        into max_hp (done by legacy server.py line 378), so we just return
        self.max_hp directly. DO NOT add tier bonus again here.
        """
        return self.max_hp
    
    @property
    def transported_units(self) -> List[int]:
        """List of unit IDs being transported."""
        return [uid for uid in [self.transport_slot_1, self.transport_slot_2, 
                                self.transport_slot_3] if uid >= 0]
    
    def reset_for_turn(self):
        """Reset per-turn state at the start of a new turn."""
        self.movement_remaining = self.movement_max
        self.road_move_remaining = 1  # Always 1 bonus road move
        self.road_move_only = True    # Start in road-move-only mode
        self.fired = False
        self.light_armor_current = self.light_armor_max
    
    def reset_for_combat(self):
        """Reset combat state at the start of a new battle."""
        self.fired = False
        self.armor_broken = False
        self.terrain_bonus = 0
        self.flank_bonus = 0
        self.hold_bonus = 0
        self.combat_start = self.effective_combat
    
    def tier_up(self, combat_bonus: int = 5, hp_bonus: int = 1) -> bool:
        """
        Increase this unit's veterancy tier by 1.
        
        Since combat and max_hp have tier bonuses baked in (from legacy database),
        we must explicitly increase those values when tiering up.
        
        Args:
            combat_bonus: Combat increase per tier (default 5)
            hp_bonus: Max HP increase per tier (default 1)
        
        Returns:
            True if tier-up succeeded, False if already at max tier (4)
        """
        if self.tier >= 4:
            return False
        
        self.tier += 1
        
        # Increase combat (NO_FIRE units don't get combat bonus)
        if self.category != UnitCategory.NO_FIRE:
            self.combat += combat_bonus
        
        # Increase max HP and heal for the bonus
        self.max_hp += hp_bonus
        self.hp = min(self.hp + hp_bonus, self.max_hp)  # Heal for the bonus HP gained
        
        return True
    
    @classmethod
    def from_legacy_list(cls, unit_id: int, data: list, stats: Optional['UnitStats'] = None) -> 'Unit':
        """
        Create a Unit from the legacy allunits[x] list format.
        This is for migration from the old system.
        
        Note: stats parameter is ignored - all data comes from the list.
        Kept for API compatibility.
        """
        return cls(
            id=unit_id,
            name=data[0],  # UNIT_NAME
            faction=FactionId(data[11]),  # UNIT_FACTION
            max_hp=data[1],  # UNIT_MAX_HIT_POINTS
            combat=data[2],  # UNIT_COMBAT
            category=UnitCategory(data[3]),  # UNIT_CATEGORY
            unit_type=UnitType(data[4]),  # UNIT_TYPE
            light_armor_max=data[5],  # UNIT_LIGHT_MAX
            heavy_armor=data[6],  # UNIT_HEAVY
            natural_armor=data[7],  # UNIT_NATURAL
            movement_max=data[8],  # UNIT_MOVEMENT_MAX
            vision=data[9],  # UNIT_VISION
            stealth=data[10],  # UNIT_STEALTH
            hp=data[12],  # UNIT_HIT_POINTS
            location=data[13],  # UNIT_LOCATION
            tier=data[14],  # UNIT_TIER
            tier_1_ability=data[15] if data[15] else 'none',  # UNIT_TIER_1
            tier_2_ability=data[16] if data[16] else 'none',  # UNIT_TIER_2
            tier_3_ability=data[17] if data[17] else 'none',  # UNIT_TIER_3
            tier_4_ability=data[18] if data[18] else 'none',  # UNIT_TIER_4
            alive=bool(data[19]),  # UNIT_ALIVE
            hex_duration=data[20],  # UNIT_HEX_DURATION
            fired=bool(data[21]),  # UNIT_FIRED
            light_armor_current=data[22],  # UNIT_LIGHT_CURRENT
            armor_broken=bool(data[23]),  # UNIT_ARMORBROKEN
            terrain_bonus=data[24],  # UNIT_TERRAIN
            flank_bonus=data[25],  # UNIT_FLANK
            movement_remaining=data[26],  # UNIT_MOVEMENT_REMAINING
            road_move_remaining=data[27],  # UNIT_ROAD_MOVE_REMAINING
            road_move_only=bool(data[28]),  # UNIT_ROAD_MOVE_ONLY
            previous_location=data[29],  # UNIT_PREVIOUS_LOCATION
            hold_bonus=data[30],  # UNIT_HOLD_BONUS
            combat_start=data[31],  # UNIT_COMBAT_START
            tier_1_data=data[32] if len(data) > 32 else 0,
            tier_2_data=data[33] if len(data) > 33 else 0,
            tier_3_data=data[34] if len(data) > 34 else 0,
            tier_4_data=data[35] if len(data) > 35 else 0,
            transport_slot_1=data[36] if len(data) > 36 else -1,
            transport_slot_2=data[37] if len(data) > 37 else -1,
            transport_slot_3=data[38] if len(data) > 38 else -1,
        )
    
    def to_legacy_list(self) -> list:
        """Convert back to legacy list format for compatibility."""
        return [
            self.name,                    # 0: UNIT_NAME
            self.max_hp,                  # 1: UNIT_MAX_HIT_POINTS
            self.combat,                  # 2: UNIT_COMBAT
            self.category.value,          # 3: UNIT_CATEGORY
            self.unit_type.value,         # 4: UNIT_TYPE
            self.light_armor_max,         # 5: UNIT_LIGHT_MAX
            self.heavy_armor,             # 6: UNIT_HEAVY
            self.natural_armor,           # 7: UNIT_NATURAL
            self.movement_max,            # 8: UNIT_MOVEMENT_MAX
            self.vision,                  # 9: UNIT_VISION
            self.stealth,                 # 10: UNIT_STEALTH
            self.faction.value,           # 11: UNIT_FACTION
            self.hp,                      # 12: UNIT_HIT_POINTS
            self.location,                # 13: UNIT_LOCATION
            self.tier,                    # 14: UNIT_TIER
            self.tier_1_ability,          # 15: UNIT_TIER_1
            self.tier_2_ability,          # 16: UNIT_TIER_2
            self.tier_3_ability,          # 17: UNIT_TIER_3
            self.tier_4_ability,          # 18: UNIT_TIER_4
            1 if self.alive else 0,       # 19: UNIT_ALIVE
            self.hex_duration,            # 20: UNIT_HEX_DURATION
            1 if self.fired else 0,       # 21: UNIT_FIRED
            self.light_armor_current,     # 22: UNIT_LIGHT_CURRENT
            1 if self.armor_broken else 0,# 23: UNIT_ARMORBROKEN
            self.terrain_bonus,           # 24: UNIT_TERRAIN
            self.flank_bonus,             # 25: UNIT_FLANK
            self.movement_remaining,      # 26: UNIT_MOVEMENT_REMAINING
            self.road_move_remaining,     # 27: UNIT_ROAD_MOVE_REMAINING
            1 if self.road_move_only else 0, # 28: UNIT_ROAD_MOVE_ONLY
            self.previous_location,       # 29: UNIT_PREVIOUS_LOCATION
            self.hold_bonus,              # 30: UNIT_HOLD_BONUS
            self.combat_start,            # 31: UNIT_COMBAT_START
            self.tier_1_data,             # 32: UNIT_TIER_1_DATA
            self.tier_2_data,             # 33: UNIT_TIER_2_DATA
            self.tier_3_data,             # 34: UNIT_TIER_3_DATA
            self.tier_4_data,             # 35: UNIT_TIER_4_DATA
            self.transport_slot_1,        # 36: UNIT_TRANSPORT_ONE
            self.transport_slot_2,        # 37: UNIT_TRANSPORT_TWO
            self.transport_slot_3,        # 38: UNIT_TRANSPORT_THREE
        ]
    
    @classmethod
    def from_db_row(cls, unit_id: int, row: tuple, stats: Optional['UnitStats'] = None) -> 'Unit':
        """
        Create a Unit from a database row (saveunits/unitdata table).
        
        The saveunits table stores the FULL unit data (39 columns) in legacy format:
        NAME, MAX_HP, COMBAT, CATEGORY, TYPE, LIGHT, HEAVY, NATURAL, MOVEMENT,
        VISION, STEALTH, FACTION, HP, LOCATION, TIER, TIER_1/2/3/4, ALIVE,
        and runtime state columns.
        
        Stats parameter is optional since saveunits includes all stats.
        """
        # Database row is in legacy list format
        return cls.from_legacy_list(unit_id, list(row), stats)
    
    def to_db_tuple(self) -> tuple:
        """
        Convert to tuple for database insertion into saveunits.
        Matches the saveunits table structure.
        """
        return (
            self.name,
            self.faction.value,
            self.hp,
            self.location,
            self.tier,
            self.tier_1_ability,
            self.tier_2_ability,
            self.tier_3_ability,
            self.tier_4_ability,
            1 if self.alive else 0,
            self.hex_duration,
            1 if self.fired else 0,
            self.light_armor_current,
            1 if self.armor_broken else 0,
            self.terrain_bonus,
            self.flank_bonus,
            self.movement_remaining,
            self.road_move_remaining,
            1 if self.road_move_only else 0,
            self.previous_location,
            self.hold_bonus,
            self.combat_start,
            self.tier_1_data,
            self.tier_2_data,
            self.tier_3_data,
            self.tier_4_data,
            self.transport_slot_1,
            self.transport_slot_2,
            self.transport_slot_3,
        )

