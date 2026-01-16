"""
Database layer for loading and saving GameState.

This module provides functions to:
- Load game state from MySQL database
- Save game state to MySQL database
- Handle the transition between legacy table structure and new models
"""
from typing import Optional, Dict, List, Any
from contextlib import contextmanager

import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb

from .game_state import GameState, TurnState, Order, SpecialOrder, EconomicAction, SpecialEvent, GamePhase
from .models import Unit, UnitStats, Hex, Base, Faction, Road, Caravan, FactionId, Expansion, ExpansionType


# Database configuration - these should eventually come from config/env
DEFAULT_DB_CONFIG = {
    'host': 'warcraft.c7a0os00g0wx.us-east-2.rds.amazonaws.com',
    'port': 3306,
    'user': 'wcadmin',
    'passwd': 'sythegar',
    'db': 'warcraft'
}


@contextmanager
def get_db_connection(config: Optional[Dict] = None):
    """
    Context manager for database connections.
    Automatically closes connection when done.
    
    Usage:
        with get_db_connection() as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM units")
    """
    cfg = config or DEFAULT_DB_CONFIG
    db = MySQLdb.connect(
        host=cfg['host'],
        port=cfg.get('port', 3306),
        user=cfg['user'],
        passwd=cfg['passwd'],
        db=cfg['db']
    )
    try:
        yield db
    finally:
        db.close()


class DatabaseLoader:
    """Loads game state from the database."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DEFAULT_DB_CONFIG
    
    def load_full_state(self, from_saved: bool = True) -> GameState:
        """
        Load complete game state from database.
        
        Args:
            from_saved: If True, load from save* tables (persisted state).
                       If False, load from current* tables (working state).
        """
        state = GameState()
        
        with get_db_connection(self.config) as db:
            self._load_unit_stats(db, state)
            self._load_units(db, state, from_saved)
            self._load_hexes(db, state, from_saved)
            self._load_bases(db, state, from_saved)
            self._load_expansions(state)  # Extract expansions from hex data
            self._load_factions(db, state, from_saved)
            self._load_roads(db, state)
            self._load_caravans(db, state)
            self._load_turn_state(db, state)
            self._load_orders(db, state)
            self._load_special_events(db, state)
            self._load_buildables(db, state)
            self._load_base_names(db, state)
        
        return state
    
    def _load_unit_stats(self, db, state: GameState) -> None:
        """Load unit type statistics from unitstats table."""
        cur = db.cursor()
        cur.execute("SELECT * FROM unitstats")
        for row in cur.fetchall():
            stats = UnitStats.from_db_row(row)
            state.unit_stats[stats.name] = stats
        cur.close()
    
    def _load_units(self, db, state: GameState, from_saved: bool) -> None:
        """Load units from database.
        
        Two different table schemas:
        - saveunits: Full 39-column format with all runtime state (used for saved games)
        - unitdata: 10-column initial format (NAME, FACTION, HP, LOCATION, TIER, abilities, ALIVE)
                    Must be combined with unitstats to get full unit data
        """
        if from_saved:
            # Load from saveunits (full 39-column format)
            cur = db.cursor()
            cur.execute("SELECT * FROM saveunits")
            unit_id = 0
            for row in cur.fetchall():
                unit = Unit.from_db_row(unit_id, row)
                state.units[unit_id] = unit
                unit_id += 1
            cur.close()
        else:
            # Load from unitdata (10-column initial format) + unitstats
            # Note: unit_stats must be loaded first (done in load_full_state)
            cur = db.cursor()
            cur.execute("SELECT * FROM unitdata")
            unit_id = 0
            for row in cur.fetchall():
                unit_name = row[0]
                # Look up stats by unit name
                stats = state.unit_stats.get(unit_name)
                if stats is None:
                    print(f"WARNING: No stats found for unit '{unit_name}', skipping")
                    continue
                unit = Unit.from_initial_data(unit_id, row, stats)
                state.units[unit_id] = unit
                unit_id += 1
            cur.close()
    
    def _load_hexes(self, db, state: GameState, from_saved: bool) -> None:
        """Load hex map from database."""
        table = 'savehexes' if from_saved else 'hexdata'
        cur = db.cursor()
        cur.execute(f"SELECT * FROM {table}")
        hex_id = 0
        for row in cur.fetchall():
            hex_obj = Hex.from_db_row_no_id(hex_id, row)
            state.hexes[hex_id] = hex_obj
            hex_id += 1
        cur.close()
    
    def _load_bases(self, db, state: GameState, from_saved: bool) -> None:
        """Load bases from database."""
        table = 'savebases' if from_saved else 'basedata'
        cur = db.cursor()
        cur.execute(f"SELECT * FROM {table}")
        base_id = 0
        for row in cur.fetchall():
            base = Base.from_db_row_no_id(base_id, row)
            state.bases[base_id] = base
            base_id += 1
        cur.close()
    
    def _load_expansions(self, state: GameState) -> None:
        """
        Extract expansions from hex data and create proper Expansion objects.
        
        In the legacy data structure, expansions are stored in hexdata as:
        - HEX_FARM, HEX_MILL, HEX_RIG: -1 means no expansion, otherwise the value
          is the hex ID of the base that owns this expansion.
        
        We convert this to a proper Expansion model linked to Base objects.
        """
        # Build lookup: base_hex_id -> base_id
        base_by_hex = {base.location: base.id for base in state.bases.values()}
        
        expansion_id = 0
        for hex_id, hex_obj in state.hexes.items():
            # Check for farm
            if hex_obj.farm >= 0:  # Farm exists (value is owning base's hex ID)
                base_id = base_by_hex.get(hex_obj.farm)
                if base_id is not None:
                    expansion = Expansion(
                        id=expansion_id,
                        type=ExpansionType.FARM,
                        location=hex_id,
                        base_id=base_id
                    )
                    state.expansions[expansion_id] = expansion
                    state.bases[base_id].expansions.append(expansion_id)
                    expansion_id += 1
            
            # Check for mill
            if hex_obj.mill >= 0:  # Mill exists
                base_id = base_by_hex.get(hex_obj.mill)
                if base_id is not None:
                    expansion = Expansion(
                        id=expansion_id,
                        type=ExpansionType.LUMBER_MILL,
                        location=hex_id,
                        base_id=base_id
                    )
                    state.expansions[expansion_id] = expansion
                    state.bases[base_id].expansions.append(expansion_id)
                    expansion_id += 1
            
            # Check for oil rig
            if hex_obj.rig >= 0:  # Rig exists
                base_id = base_by_hex.get(hex_obj.rig)
                if base_id is not None:
                    expansion = Expansion(
                        id=expansion_id,
                        type=ExpansionType.OIL_RIG,
                        location=hex_id,
                        base_id=base_id
                    )
                    state.expansions[expansion_id] = expansion
                    state.bases[base_id].expansions.append(expansion_id)
                    expansion_id += 1
    
    def _load_factions(self, db, state: GameState, from_saved: bool) -> None:
        """Load faction diplomacy data from database."""
        table = 'savediplomacy' if from_saved else 'diplomacydata'
        cur = db.cursor()
        cur.execute(f"SELECT * FROM {table}")
        for row in cur.fetchall():
            faction = Faction.from_db_row(row)
            state.factions[faction.id] = faction
        cur.close()
    
    def _load_roads(self, db, state: GameState) -> None:
        """Load roads from database.
        
        Roads are stored one row per hex, in order by hex_id.
        The first column (ROAD_HEX) is NOT the hex_id - it's a flag.
        The actual hex_id is determined by row position.
        """
        cur = db.cursor()
        cur.execute("SELECT * FROM roaddata")
        hex_id = 0
        for row in cur.fetchall():
            # Row structure: [flag, north, ne, se, s, sw, nw]
            # We use row position as hex_id
            road = Road(
                hex_id=hex_id,
                north=int(row[1]),
                northeast=int(row[2]),
                southeast=int(row[3]),
                south=int(row[4]),
                southwest=int(row[5]),
                northwest=int(row[6])
            )
            state.roads[hex_id] = road
            hex_id += 1
        cur.close()
    
    def _load_caravans(self, db, state: GameState) -> None:
        """Load caravans from database."""
        cur = db.cursor()
        cur.execute("SELECT * FROM savecaravans")
        caravan_id = 0
        for row in cur.fetchall():
            caravan = Caravan.from_db_row(caravan_id, row)
            state.caravans.append(caravan)
            caravan_id += 1
        cur.close()
    
    def _load_turn_state(self, db, state: GameState) -> None:
        """Load current turn/initiative state."""
        cur = db.cursor()
        
        # Load current initiative
        cur.execute("SELECT * FROM currentinitiative")
        row = cur.fetchone()
        if row:
            state.turn.current_initiative = int(row[0])
        
        # Load current faction
        cur.execute("SELECT * FROM currentfaction")
        row = cur.fetchone()
        if row:
            state.turn.current_faction = int(row[0])
        
        cur.close()
    
    def _load_orders(self, db, state: GameState) -> None:
        """Load pending orders."""
        cur = db.cursor()
        
        # Movement orders
        cur.execute("SELECT * FROM orders")
        for row in cur.fetchall():
            state.orders.append(Order.from_db_row(row))
        
        # Special orders
        cur.execute("SELECT * FROM specialorders")
        for row in cur.fetchall():
            state.special_orders.append(SpecialOrder.from_db_row(row))
        
        # Economic actions
        cur.execute("SELECT * FROM economicactions")
        for row in cur.fetchall():
            state.economic_actions.append(EconomicAction.from_db_row(row))
        
        cur.close()
    
    def _load_special_events(self, db, state: GameState) -> None:
        """Load special events."""
        cur = db.cursor()
        cur.execute("SELECT * FROM specialevents")
        for row in cur.fetchall():
            state.special_events.append(SpecialEvent.from_db_row(row))
        cur.close()
    
    def _load_buildables(self, db, state: GameState) -> None:
        """
        Load buildable unit types per faction from the buildables table.
        
        The buildables table has:
        - Rows indexed by faction_id (row 0 = faction 0, etc.)
        - Columns 0-31 are unit types (GRUNT, BERSERKER, etc.)
        - Values: -1 = cannot build, 0-4 = max veterancy tier achievable
        
        Legacy code uses FACTION_DATA_GRUNT=1 but accesses [GRUNT-1]=[0]
        So column 0 = Grunt, column 1 = Berserker, etc.
        """
        from .game_state import BUILDABLE_COLUMN_TO_UNIT
        
        cur = db.cursor()
        cur.execute("SELECT * FROM buildables")
        
        faction_id = 0
        for row in cur.fetchall():
            faction_buildables = {}
            
            # All columns are unit types (no ID column to skip)
            for col_idx, max_tier in enumerate(row):
                unit_name = BUILDABLE_COLUMN_TO_UNIT.get(col_idx)
                if unit_name:
                    max_tier_val = int(max_tier) if max_tier is not None else -1
                    # Only add if faction CAN build this unit (max_tier != -1)
                    if max_tier_val >= 0:
                        faction_buildables[unit_name] = max_tier_val
            
            state.faction_buildables[faction_id] = faction_buildables
            faction_id += 1
        
        cur.close()
    
    def _load_base_names(self, db, state: GameState) -> None:
        """Load available base names."""
        cur = db.cursor()
        cur.execute("SELECT * FROM basenames")
        for row in cur.fetchall():
            state.base_names.append((str(row[0]), int(row[1]), int(row[2])))
        cur.close()


class DatabaseSaver:
    """Saves game state to the database."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or DEFAULT_DB_CONFIG
    
    def save_full_state(self, state: GameState) -> None:
        """Save complete game state to database."""
        with get_db_connection(self.config) as db:
            self._save_units(db, state)
            self._save_hexes(db, state)
            self._save_bases(db, state)
            self._save_factions(db, state)
            self._save_caravans(db, state)
            self._save_turn_state(db, state)
            db.commit()
    
    def _save_units(self, db, state: GameState) -> None:
        """Save units to saveunits table."""
        cur = db.cursor()
        cur.execute("TRUNCATE saveunits")
        
        for unit in state.units.values():
            values = unit.to_db_tuple()
            placeholders = ', '.join(['%s'] * len(values))
            cur.execute(f"INSERT INTO saveunits VALUES ({placeholders})", values)
        
        cur.close()
    
    def _save_hexes(self, db, state: GameState) -> None:
        """Save hexes to savehexes table."""
        cur = db.cursor()
        cur.execute("TRUNCATE savehexes")
        
        for hex_obj in state.hexes.values():
            values = hex_obj.to_db_tuple()
            placeholders = ', '.join(['%s'] * len(values))
            cur.execute(f"INSERT INTO savehexes VALUES ({placeholders})", values)
        
        cur.close()
    
    def _save_bases(self, db, state: GameState) -> None:
        """Save bases to savebases table."""
        cur = db.cursor()
        cur.execute("TRUNCATE savebases")
        
        for base in state.bases.values():
            values = base.to_db_tuple()
            placeholders = ', '.join(['%s'] * len(values))
            cur.execute(f"INSERT INTO savebases VALUES ({placeholders})", values)
        
        cur.close()
    
    def _save_factions(self, db, state: GameState) -> None:
        """Save factions to savediplomacy table."""
        cur = db.cursor()
        cur.execute("TRUNCATE savediplomacy")
        
        for faction in state.factions.values():
            values = faction.to_db_tuple()
            placeholders = ', '.join(['%s'] * len(values))
            cur.execute(f"INSERT INTO savediplomacy VALUES ({placeholders})", values)
        
        cur.close()
    
    def _save_caravans(self, db, state: GameState) -> None:
        """Save caravans to savecaravans table."""
        cur = db.cursor()
        cur.execute("TRUNCATE savecaravans")
        
        for caravan in state.caravans:
            values = caravan.to_db_tuple()
            placeholders = ', '.join(['%s'] * len(values))
            cur.execute(f"INSERT INTO savecaravans VALUES ({placeholders})", values)
        
        cur.close()
    
    def _save_turn_state(self, db, state: GameState) -> None:
        """Save turn state."""
        cur = db.cursor()
        
        # Save current initiative
        cur.execute("TRUNCATE currentinitiative")
        cur.execute("INSERT INTO currentinitiative VALUES (%s)", (state.turn.current_initiative,))
        
        # Save current faction
        cur.execute("TRUNCATE currentfaction")
        cur.execute("INSERT INTO currentfaction VALUES (%s)", (state.turn.current_faction,))
        
        cur.close()


# Convenience functions
def load_game_state(from_saved: bool = True, config: Optional[Dict] = None) -> GameState:
    """Load game state from database."""
    loader = DatabaseLoader(config)
    return loader.load_full_state(from_saved)


def save_game_state(state: GameState, config: Optional[Dict] = None) -> None:
    """Save game state to database."""
    saver = DatabaseSaver(config)
    saver.save_full_state(state)

