"""
Game Configuration for Tides of Darkness.

Centralizes all tweakable game constants into a single, editable configuration.
Values can be modified at runtime via the admin API and optionally persisted.

This replaces scattered constants throughout the codebase with a single source
of truth that's easy to find, modify, and experiment with.
"""
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Default config file location
CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "game_config.json"


@dataclass
class CombatConfig:
    """Combat-related configuration."""
    
    # Combat roll bounds (effectiveness clamped to these)
    min_combat_roll: int = 10
    max_combat_roll: int = 90
    
    # Veterancy bonuses per tier
    veterancy_combat_bonus: int = 5  # +5 combat per tier
    veterancy_hp_bonus: int = 1      # +1 max HP per tier
    max_veterancy_tier: int = 4
    
    # Flanking
    flanking_bonus_increment: int = 10  # Each flanking force gets +10
    
    # Terrain penalties
    river_crossing_penalty: int = -15
    fortification_penalty: int = -25
    siege_vs_fortification_penalty: int = -10
    disembark_into_combat_penalty: int = -15
    
    # Base combat bonuses by tier
    base_tier_1_bonus: int = 0
    base_tier_2_bonus: int = 5
    base_tier_3_bonus: int = 10


@dataclass
class EconomicConfig:
    """Economic/base action configuration."""
    
    # Commerce
    commerce_cost: int = 2           # Resources spent
    commerce_gain: int = 1           # Resources gained (next turn)
    
    # Base upgrades
    upgrade_tier_2_gold: int = 3
    upgrade_tier_2_lumber: int = 3
    upgrade_tier_2_harvest_req: int = 2  # Min total harvest yield required
    
    upgrade_tier_3_gold: int = 6
    upgrade_tier_3_lumber: int = 6
    upgrade_tier_3_oil: int = 3
    upgrade_tier_3_harvest_req: int = 4
    
    # Rest action
    rest_cost: int = 2               # Gold cost
    rest_heal_fraction: float = 0.25  # Heal 25% of max HP (rounded up)
    
    # Expansion costs
    expand_farm_lumber: int = 3
    expand_farm_oil: int = 0
    expand_mill_lumber: int = 3
    expand_mill_oil: int = 0
    expand_rig_lumber: int = 3
    expand_rig_oil: int = 2
    
    # Food
    food_per_unit: int = 1
    food_per_base_tier: int = 1      # Base contributes tier to food cap
    food_per_farm: int = 1


@dataclass
class CaravanConfig:
    """Caravan configuration."""
    
    max_caravan_length: int = 15     # Including both base hexes
    
    # Land caravan costs (lumber only)
    land_1_5_lumber: int = 2
    land_6_10_lumber: int = 3
    land_11_15_lumber: int = 4
    
    # Sea caravan costs (lumber + oil)
    sea_1_5_lumber: int = 2
    sea_1_5_oil: int = 2
    sea_6_10_lumber: int = 3
    sea_6_10_oil: int = 3
    sea_11_15_lumber: int = 4
    sea_11_15_oil: int = 4


@dataclass
class MovementConfig:
    """Movement configuration."""
    
    # Road bonus
    road_hexside_bonus: int = 1      # Extra units can cross if road present
    
    # Coastal combat limit
    coastal_combat_limit: int = 1    # Reduced hexside limit during combat
    
    # Fast travel (March / Full Sail)
    fast_travel_max_hexes: int = 10  # Maximum hexes a unit can fast travel
    
    # Hexside limits by terrain (base values)
    hexside_clear: int = 4
    hexside_forest: int = 2
    hexside_mountain: int = 1
    hexside_swamp: int = 1
    hexside_river: int = 1
    hexside_fortification: int = 1
    hexside_ocean: int = 1000        # Effectively unlimited for ships


@dataclass
class TerrainConfig:
    """Terrain combat modifiers configuration."""
    
    # Terrain penalties for attackers (negative = harder to hit)
    # These apply to units attacking INTO a hex with this terrain
    plains_terrain_penalty: int = 0      # Clear terrain
    forest_terrain_penalty: int = -10
    mountain_terrain_penalty: int = -20
    swamp_terrain_penalty: int = -20
    
    # Initial defender bonuses (first round of new combat)
    # Defenders who were already in position get these modifiers instead
    plains_defender_bonus: int = 0
    forest_defender_bonus: int = 0       # No penalty for entrenched defenders
    mountain_defender_bonus: int = 10    # Defenders get +10% in mountains!
    swamp_defender_bonus: int = -20      # Swamp is bad for everyone


@dataclass
class DebugConfig:
    """Debug/testing flags."""
    
    # Combat
    instant_kill_mode: bool = False  # Any hit kills target instantly (bypasses armor)
    no_damage_mode: bool = False     # Attacks happen but no HP is deducted
    
    # Resources
    infinite_resources: bool = False
    
    # Logging
    verbose_combat_logs: bool = True   # Default True for testing


@dataclass
class GameConfig:
    """
    Complete game configuration.
    
    Centralizes all tweakable values for easy modification and testing.
    """
    combat: CombatConfig = field(default_factory=CombatConfig)
    economic: EconomicConfig = field(default_factory=EconomicConfig)
    caravan: CaravanConfig = field(default_factory=CaravanConfig)
    movement: MovementConfig = field(default_factory=MovementConfig)
    terrain: TerrainConfig = field(default_factory=TerrainConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)
    
    def to_dict(self) -> dict:
        """Convert config to nested dictionary."""
        return {
            'combat': asdict(self.combat),
            'economic': asdict(self.economic),
            'caravan': asdict(self.caravan),
            'movement': asdict(self.movement),
            'terrain': asdict(self.terrain),
            'debug': asdict(self.debug),
        }
    
    def to_flat_dict(self) -> Dict[str, Any]:
        """Convert to flat dictionary with dotted keys (e.g., 'combat.min_combat_roll')."""
        result = {}
        for section_name, section_data in self.to_dict().items():
            for key, value in section_data.items():
                result[f"{section_name}.{key}"] = value
        return result
    
    def get_value(self, key: str) -> Any:
        """
        Get a config value by dotted key (e.g., 'combat.min_combat_roll').
        """
        if '.' not in key:
            raise ValueError(f"Key must be in format 'section.name': {key}")
        
        section, name = key.split('.', 1)
        section_obj = getattr(self, section, None)
        if section_obj is None:
            raise ValueError(f"Unknown config section: {section}")
        
        if not hasattr(section_obj, name):
            raise ValueError(f"Unknown config key in {section}: {name}")
        
        return getattr(section_obj, name)
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a config value by dotted key (e.g., 'combat.min_combat_roll').
        
        Automatically converts value to the appropriate type.
        """
        if '.' not in key:
            raise ValueError(f"Key must be in format 'section.name': {key}")
        
        section, name = key.split('.', 1)
        section_obj = getattr(self, section, None)
        if section_obj is None:
            raise ValueError(f"Unknown config section: {section}")
        
        if not hasattr(section_obj, name):
            raise ValueError(f"Unknown config key in {section}: {name}")
        
        # Get current value to determine type
        current = getattr(section_obj, name)
        
        # Convert value to appropriate type
        if isinstance(current, bool):
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = bool(value)
        elif isinstance(current, int):
            value = int(value)
        elif isinstance(current, float):
            value = float(value)
        
        setattr(section_obj, name, value)
        logger.info(f"Config updated: {key} = {value}")
    
    def reset_to_defaults(self) -> None:
        """Reset all config values to defaults."""
        self.combat = CombatConfig()
        self.economic = EconomicConfig()
        self.caravan = CaravanConfig()
        self.movement = MovementConfig()
        self.terrain = TerrainConfig()
        self.debug = DebugConfig()
        logger.info("Config reset to defaults")
    
    def save_to_file(self, path: Optional[Path] = None) -> dict:
        """
        Save configuration to JSON file.
        
        Returns dict with success status.
        """
        try:
            save_path = path or CONFIG_FILE
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            
            logger.info(f"Config saved to {save_path}")
            return {'success': True, 'path': str(save_path)}
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_from_file(self, path: Optional[Path] = None) -> dict:
        """
        Load configuration from JSON file.
        
        Returns dict with success status.
        """
        try:
            load_path = path or CONFIG_FILE
            if not load_path.exists():
                return {'success': False, 'error': f'Config file not found: {load_path}'}
            
            with open(load_path, 'r') as f:
                data = json.load(f)
            
            # Apply each section
            if 'combat' in data:
                for k, v in data['combat'].items():
                    if hasattr(self.combat, k):
                        setattr(self.combat, k, v)
            
            if 'economic' in data:
                for k, v in data['economic'].items():
                    if hasattr(self.economic, k):
                        setattr(self.economic, k, v)
            
            if 'caravan' in data:
                for k, v in data['caravan'].items():
                    if hasattr(self.caravan, k):
                        setattr(self.caravan, k, v)
            
            if 'movement' in data:
                for k, v in data['movement'].items():
                    if hasattr(self.movement, k):
                        setattr(self.movement, k, v)
            
            if 'terrain' in data:
                for k, v in data['terrain'].items():
                    if hasattr(self.terrain, k):
                        setattr(self.terrain, k, v)
            
            if 'debug' in data:
                for k, v in data['debug'].items():
                    if hasattr(self.debug, k):
                        setattr(self.debug, k, v)
            
            logger.info(f"Config loaded from {load_path}")
            return {'success': True, 'path': str(load_path)}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GameConfig':
        """Create GameConfig from dictionary."""
        config = cls()
        
        if 'combat' in data:
            config.combat = CombatConfig(**data['combat'])
        if 'economic' in data:
            config.economic = EconomicConfig(**data['economic'])
        if 'caravan' in data:
            config.caravan = CaravanConfig(**data['caravan'])
        if 'movement' in data:
            config.movement = MovementConfig(**data['movement'])
        if 'terrain' in data:
            config.terrain = TerrainConfig(**data['terrain'])
        if 'debug' in data:
            config.debug = DebugConfig(**data['debug'])
        
        return config


# ============================================================================
# Singleton Instance
# ============================================================================

_game_config: Optional[GameConfig] = None


def get_game_config() -> GameConfig:
    """Get the global GameConfig instance."""
    global _game_config
    if _game_config is None:
        _game_config = GameConfig()
        
        # Try to load saved config if exists
        if CONFIG_FILE.exists():
            result = _game_config.load_from_file()
            if result['success']:
                logger.info("Loaded saved game configuration")
    
    return _game_config


def reset_game_config() -> None:
    """Reset the global GameConfig to defaults."""
    global _game_config
    if _game_config is not None:
        _game_config.reset_to_defaults()
    else:
        _game_config = GameConfig()


# ============================================================================
# Helper Functions for Compatibility
# ============================================================================

def get_base_combat_bonus(base_tier: int) -> int:
    """Get combat bonus for fighting at a friendly base of given tier."""
    config = get_game_config()
    bonuses = {
        1: config.combat.base_tier_1_bonus,
        2: config.combat.base_tier_2_bonus,
        3: config.combat.base_tier_3_bonus,
    }
    return bonuses.get(base_tier, 0)


def get_upgrade_cost(target_tier: int) -> dict:
    """Get the resource cost for upgrading to a tier."""
    config = get_game_config()
    if target_tier == 2:
        return {
            'gold': config.economic.upgrade_tier_2_gold,
            'lumber': config.economic.upgrade_tier_2_lumber,
            'oil': 0
        }
    elif target_tier == 3:
        return {
            'gold': config.economic.upgrade_tier_3_gold,
            'lumber': config.economic.upgrade_tier_3_lumber,
            'oil': config.economic.upgrade_tier_3_oil
        }
    return {'gold': 0, 'lumber': 0, 'oil': 0}


def get_upgrade_harvest_requirement(target_tier: int) -> int:
    """Get minimum harvest yield required to upgrade to a tier."""
    config = get_game_config()
    if target_tier == 2:
        return config.economic.upgrade_tier_2_harvest_req
    elif target_tier == 3:
        return config.economic.upgrade_tier_3_harvest_req
    return 0


def get_caravan_cost(path_length: int, is_sea: bool) -> dict:
    """Calculate caravan establishment cost based on length and type."""
    config = get_game_config()
    
    if path_length <= 5:
        if is_sea:
            return {'lumber': config.caravan.sea_1_5_lumber, 'oil': config.caravan.sea_1_5_oil}
        return {'lumber': config.caravan.land_1_5_lumber, 'oil': 0}
    elif path_length <= 10:
        if is_sea:
            return {'lumber': config.caravan.sea_6_10_lumber, 'oil': config.caravan.sea_6_10_oil}
        return {'lumber': config.caravan.land_6_10_lumber, 'oil': 0}
    else:  # 11-15
        if is_sea:
            return {'lumber': config.caravan.sea_11_15_lumber, 'oil': config.caravan.sea_11_15_oil}
        return {'lumber': config.caravan.land_11_15_lumber, 'oil': 0}


def clamp_combat_roll(roll: int) -> int:
    """Clamp a combat roll to valid bounds."""
    config = get_game_config()
    return max(config.combat.min_combat_roll, min(config.combat.max_combat_roll, roll))

