"""
Faction model for Tides of Darkness.

Factions represent the playable nations/tribes in the game.
Handles diplomacy, initiative, and alliance membership.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from .enums import FactionId, FACTION_NAMES, HORDE_FACTIONS, ALLIANCE_FACTIONS


@dataclass
class Faction:
    """
    A faction in the game with its diplomatic state.
    """
    # Identity
    id: FactionId
    name: str = ''
    
    # Game State
    is_defeated: bool = False
    initiative: int = -1              # Turn order (-1 = not active)
    
    # Alliance Membership
    membership: int = 0               # 0=none, 1=Alliance member, 2=Horde member
    is_leader: bool = False           # Is this faction the leader of their coalition?
    
    # Diplomacy Orders
    leader_vote: int = 0              # Who this faction votes for as leader
    alliance_votes: str = ''          # Comma-separated faction IDs to include in Alliance
    horde_decision: str = ''          # Horde diplomatic decision (H, S, or faction IDs)
    warchief_decision: int = 0        # Warchief-related decision
    
    def __post_init__(self):
        """Set name from faction ID if not provided."""
        if not self.name and self.id in FACTION_NAMES:
            self.name = FACTION_NAMES[self.id]
    
    @property
    def is_horde(self) -> bool:
        """Check if this faction is part of the Horde."""
        return self.id in HORDE_FACTIONS or self.membership == 2
    
    @property
    def is_alliance(self) -> bool:
        """Check if this faction is part of the Alliance."""
        return self.id in ALLIANCE_FACTIONS or self.membership == 1
    
    @property
    def is_active(self) -> bool:
        """Check if this faction is active in the game."""
        return not self.is_defeated and self.initiative >= 0
    
    @property
    def alliance_vote_list(self) -> List[int]:
        """Get list of faction IDs this faction voted to include in Alliance."""
        if not self.alliance_votes or self.alliance_votes in ['J', 'L', '']:
            return []
        return [int(x.strip()) for x in self.alliance_votes.split(',') if x.strip().isdigit()]
    
    @property
    def is_requesting_alliance(self) -> bool:
        """Check if faction is requesting to join Alliance."""
        return self.alliance_votes == 'J'
    
    @property
    def is_leaving_alliance(self) -> bool:
        """Check if faction is leaving the Alliance."""
        return self.alliance_votes == 'L'
    
    def clear_diplomacy_orders(self):
        """Clear all diplomacy orders for new turn."""
        self.leader_vote = 0
        self.alliance_votes = ''
        self.horde_decision = ''
        self.warchief_decision = 0
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Faction':
        """Create a Faction from a database row (savediplomacy table)."""
        return cls(
            id=FactionId(int(row[0])),
            name=str(row[1]),
            is_defeated=bool(row[2]),
            initiative=int(row[3]),
            membership=int(row[4]),
            is_leader=bool(row[5]),
            leader_vote=int(row[6]),
            alliance_votes=str(row[7]) if row[7] else '',
            horde_decision=str(row[8]) if row[8] else '',
            warchief_decision=int(row[9]) if row[9] else 0,
        )
    
    def to_db_tuple(self) -> tuple:
        """Convert to database tuple for INSERT/UPDATE."""
        return (
            self.id.value,
            self.name,
            1 if self.is_defeated else 0,
            self.initiative,
            self.membership,
            1 if self.is_leader else 0,
            self.leader_vote,
            self.alliance_votes,
            self.horde_decision,
            self.warchief_decision,
        )

