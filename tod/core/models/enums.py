"""
Enumerations and constants for Tides of Darkness.
These replace the magic numbers scattered throughout the legacy code.
"""
from enum import IntEnum, auto


class UnitCategory(IntEnum):
    """Combat category determines firing order and targeting rules."""
    EXTERIOR_SIEGE = 0  # Catapults, Juggernauts - fire first from outside
    RANGED = 1          # Archers, Axethrowers, Mages
    EXPERT = 2          # Special units with unique targeting
    MELEE = 3           # Grunts, Footmen, Knights
    INTERIOR_SIEGE = 4  # Siege from within the hex
    NO_FIRE = 5         # Transports, non-combat units


class UnitType(IntEnum):
    """Movement/terrain type."""
    GROUND = 0
    AIR = 1
    SEA = 2


class Direction(IntEnum):
    """Hex directions for movement and hexside control."""
    N = 0   # North
    NE = 1  # Northeast
    SE = 2  # Southeast
    S = 3   # South
    SW = 4  # Southwest
    NW = 5  # Northwest
    
    def opposite(self) -> 'Direction':
        """Return the opposite direction (180 degrees)."""
        # Each direction is 3 steps away from its opposite in a 6-direction hex
        return Direction((self.value + 3) % 6)


class Terrain(str):
    """
    Terrain type codes used in hex data.
    
    Hex terrains (center of hex): O, C, F, M, S, I
    Hexside terrains (edges): O, C, F, M, S, K, N, Q, R, W, X
    """
    # === Can be HEX terrain (center) AND hexside terrain ===
    OCEAN = 'O'           # Ocean/deep water
    CLEAR = 'C'           # Clear/plains - open terrain
    FOREST = 'F'          # Forest - blocks LOS, movement penalty
    MOUNTAIN = 'M'        # Mountain - high ground, difficult terrain
    SWAMP = 'S'           # Swamp - movement penalty
    
    # === Can ONLY be HEX terrain (not hexside) ===
    PEAKS = 'I'           # Peaks - impassable mountains (hex only)
    
    # === Can ONLY be HEXSIDE terrain (edges between hexes) ===
    COASTAL_CLEAR = 'K'   # Coastal clear - transition land/sea
    COASTAL_MOUNTAIN = 'N' # Coastal mountain - cliffs
    COASTAL_FOREST = 'Q'  # Coastal forest
    RIVER = 'R'           # River - crossing penalty, limits units per turn
    FORTIFICATION = 'W'   # Fortification - defensive bonus
    IMPASSABLE = 'X'      # Impassable - cannot cross (map edge, cliffs)


# Terrain groupings for game logic
HEX_TERRAINS = {Terrain.OCEAN, Terrain.CLEAR, Terrain.FOREST, 
                Terrain.MOUNTAIN, Terrain.SWAMP, Terrain.PEAKS}

HEXSIDE_TERRAINS = {Terrain.OCEAN, Terrain.CLEAR, Terrain.FOREST,
                    Terrain.MOUNTAIN, Terrain.SWAMP, Terrain.COASTAL_CLEAR,
                    Terrain.COASTAL_MOUNTAIN, Terrain.COASTAL_FOREST,
                    Terrain.RIVER, Terrain.FORTIFICATION, Terrain.IMPASSABLE}

WATER_TERRAINS = {Terrain.OCEAN, Terrain.COASTAL_CLEAR, 
                  Terrain.COASTAL_MOUNTAIN, Terrain.COASTAL_FOREST}

LAND_TERRAINS = {Terrain.CLEAR, Terrain.FOREST, Terrain.MOUNTAIN, 
                 Terrain.SWAMP, Terrain.PEAKS}


class BuildingType(IntEnum):
    """Special buildings on hexes."""
    NONE = 0
    RUNESTONE = 1    # Elven runestone - defensive structure
    PORTAL = 2       # Dark portal
    DRAGON_ROOST = 3 # Dragon roost


class FactionId(IntEnum):
    """All factions in the game."""
    # Horde Core (0-6)
    AMANI = 0
    BLEEDING_HOLLOW = 1
    BLACK_TOOTH_GRIN = 2
    DRAGONMAW = 3
    STORMREAVER = 4
    TWILIGHTS_HAMMER = 5
    BLACKROCK = 6
    
    # Alliance Core (7-16)
    SILVERMOON = 7
    AERIE_PEAK = 8
    IRONFORGE = 9
    DALARAN = 10
    KUL_TIRAS = 11
    STROMGARDE = 12
    AZEROTH = 13
    LORDAERON = 14
    GILNEAS = 15
    ALTERAC = 16
    
    # Minor/Special Factions (17-31)
    DARK_IRON = 17
    BURNING_BLADE = 18
    FROSTWOLF = 19
    DALARAN_REBEL = 20
    GILNEAS_REBEL = 21
    FIRETREE = 22
    SMOLDERTHORN = 23
    SHADOWPINE = 24
    SHADOWGLEN = 25
    REVANTUSK = 26
    MOSSFLAYER = 27
    WITHERBARK = 28
    VILEBRANCH = 29
    DRAGON = 30
    DEMON = 31


# Faction groupings for game logic
HORDE_FACTIONS = [
    FactionId.AMANI, FactionId.BLEEDING_HOLLOW, FactionId.BLACK_TOOTH_GRIN,
    FactionId.DRAGONMAW, FactionId.STORMREAVER, FactionId.TWILIGHTS_HAMMER,
    FactionId.BLACKROCK
]

ALLIANCE_FACTIONS = [
    FactionId.SILVERMOON, FactionId.AERIE_PEAK, FactionId.IRONFORGE,
    FactionId.DALARAN, FactionId.KUL_TIRAS, FactionId.STROMGARDE,
    FactionId.AZEROTH, FactionId.LORDAERON, FactionId.GILNEAS, FactionId.ALTERAC
]

NEUTRAL_TROLL_FACTIONS = [
    FactionId.FIRETREE, FactionId.SMOLDERTHORN,
    FactionId.SHADOWPINE, FactionId.SHADOWGLEN, FactionId.REVANTUSK,
    FactionId.MOSSFLAYER, FactionId.WITHERBARK, FactionId.VILEBRANCH
]


# Faction name lookup
FACTION_NAMES = {
    FactionId.AMANI: 'Amani',
    FactionId.BLEEDING_HOLLOW: 'Bleeding Hollow',
    FactionId.BLACK_TOOTH_GRIN: 'Black Tooth Grin',
    FactionId.DRAGONMAW: 'Dragonmaw',
    FactionId.STORMREAVER: 'Stormreaver',
    FactionId.TWILIGHTS_HAMMER: "Twilight's Hammer",
    FactionId.BLACKROCK: 'Blackrock',
    FactionId.SILVERMOON: 'Silvermoon',
    FactionId.AERIE_PEAK: 'Aerie Peak',
    FactionId.IRONFORGE: 'Ironforge',
    FactionId.DALARAN: 'Dalaran',
    FactionId.KUL_TIRAS: 'Kul Tiras',
    FactionId.STROMGARDE: 'Stromgarde',
    FactionId.AZEROTH: 'Azeroth',
    FactionId.LORDAERON: 'Lordaeron',
    FactionId.GILNEAS: 'Gilneas',
    FactionId.ALTERAC: 'Alterac',
    FactionId.DARK_IRON: 'Dark Iron',
    FactionId.BURNING_BLADE: 'Burning Blade',
    FactionId.FROSTWOLF: 'Frostwolf',
    FactionId.DALARAN_REBEL: 'Dalaran Rebel',
    FactionId.GILNEAS_REBEL: 'Gilnean Rebel',
    FactionId.FIRETREE: 'Firetree',
    FactionId.SMOLDERTHORN: 'Smolderthorn',
    FactionId.SHADOWPINE: 'Shadowpine',
    FactionId.SHADOWGLEN: 'Shadowglen',
    FactionId.REVANTUSK: 'Revantusk',
    FactionId.MOSSFLAYER: 'Mossflayer',
    FactionId.WITHERBARK: 'Witherbark',
    FactionId.VILEBRANCH: 'Vilebranch',
    FactionId.DRAGON: 'Dragon',
    FactionId.DEMON: 'Demon',
}

