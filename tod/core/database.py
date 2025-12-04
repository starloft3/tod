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
from .models import Unit, UnitStats, Hex, Base, Faction, Road, Caravan, FactionId


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
        
        The saveunits table stores complete unit data (39 columns) including
        all stats, so no stats lookup is needed.
        """
        table = 'saveunits' if from_saved else 'unitdata'
        cur = db.cursor()
        cur.execute(f"SELECT * FROM {table}")
        unit_id = 0
        for row in cur.fetchall():
            unit = Unit.from_db_row(unit_id, row)
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
        """Load roads from database."""
        cur = db.cursor()
        cur.execute("SELECT * FROM roaddata")
        for row in cur.fetchall():
            road = Road.from_db_row(row)
            # Key by hex_id since roads are stored per-hex with directional connections
            state.roads[road.hex_id] = road
        cur.close()
    
    def _load_caravans(self, db, state: GameState) -> None:
        """Load caravans from database."""
        cur = db.cursor()
        cur.execute("SELECT * FROM savecaravans")
        for row in cur.fetchall():
            caravan = Caravan.from_db_row(row)
            state.caravans.append(caravan)
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
        """Load buildable unit types per faction."""
        cur = db.cursor()
        cur.execute("SELECT * FROM savebuildables")
        for row in cur.fetchall():
            faction_id = int(row[0])
            # Rest of row is boolean flags for each unit type
            state.buildables[faction_id] = [bool(x) for x in row[1:]]
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

