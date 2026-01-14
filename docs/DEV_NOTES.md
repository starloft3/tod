# Development Notes

This document provides context for AI agents and developers working on this codebase.

---

## Session: January 13, 2026 (Remote Workstation Setup)

### Bugs Fixed

#### 1. Road Bonus Bug (Falsy Zero Pattern)
**Problem:** Ground units weren't receiving road bonuses for standard Move orders after Fast Travel was implemented.

**Root Cause:** JavaScript "falsy zero" bug. Ground units have `unitType = 0`, which is falsy in JS:
```javascript
// BAD - 0 || 1 evaluates to 1 (AIR), not 0 (GROUND)
const unitType = unit.unitType || unit.unit_type || 1

// GOOD - ?? only falls through on null/undefined
const unitType = unit.unitType ?? unit.unit_type ?? 0
```

**Files Fixed:**
- `frontend/src/views/Map.vue` (line ~863)
- `frontend/src/utils/movementValidation.js` (line ~452)

**⚠️ PATTERN TO WATCH:** Any time you see `|| 1` or `|| 0` for unit types, it's likely a bug waiting to happen. Always use `??` for numeric defaults that could legitimately be 0.

---

#### 2. Conflicting Orders UI Bug
**Problem:** After submitting a March order, Move/Ranged Fire buttons didn't disappear, allowing conflicting orders.

**Fix:** Added `&& !hasFastTravelOrder(selectedUnitDetail)` to the `v-if` conditions for order buttons in `Map.vue` (line ~3522).

---

#### 3. Fast Travel Click Redirection Bug
**Problem:** Clicking on bases/units while in March mode would select them instead of adding the hex to the path.

**Fix:** Added `(fastTravelMode.value && fastTravelUnit.value)` to `isHexTargetingMode` computed property in `Map.vue` (line ~1416).

---

#### 4. Fast Travel Hexside Limits Bug
**Problem:** March orders weren't respecting hexside limits at all.

**Fix (multi-part):**
1. Added `isAirUnitById` helper to skip air units in hexside counting
2. Added hexside limit validation to `addToFastTravelPath()` 
3. Added `startLocation` to fastTravelOrders for accurate counting
4. Updated `countHexsideUsageInOrders` to handle both Move and March orders

---

#### 5. Sea Caravan Destination Selection Bug
**Problem:** Sea caravans couldn't select destination bases via coastal hexsides.

**Root Cause:** `is_endpoint` flag in backend's `validate_caravan_hexside` was only true for the START of a caravan, not the END. Coastal hexsides (K, Q) are only valid at endpoints.

**Backend Fix (`tod/core/game_state.py`):**
- Moved destination base detection earlier in `get_valid_next_caravan_hexes`
- Set `is_endpoint = (len(current_path) == 1) or is_destination`

**Frontend Fix (`Map.vue`):**
- Added fallback in `handleCaravanHexClick` to manually check coastal adjacency to destination bases
- Added `areHexesAdjacentForCaravan` and `isCoastalHexside` helpers

---

## Architecture Quick Reference

### Unit Types
```python
# Python (backend)
class UnitType(Enum):
    GROUND = 0
    AIR = 1
    SEA = 2
```

### Hexside Terrain Codes
| Code | Terrain | Base Limit | With Road |
|------|---------|------------|-----------|
| C | Clear | 4 | 5 |
| R | River | 1 | 2 |
| S | Sea | ∞ | - |
| M | Mountain | 0 | 1 |
| F | Forest | 2 | 3 |
| K | Coastal Clear | 0* | - |
| Q | Coastal Forest | 0* | - |

*Coastal hexsides only valid at caravan endpoints

### Key Frontend State
- `movementMode` / `movementPath` - Standard Move order
- `fastTravelMode` / `fastTravelPath` - March/Full Sail order
- `caravanMode` / `caravanPath` - Establish Caravan action
- `submittedOrders` - All orders queued for turn submission

---

## Session: January 14, 2026 (Troll Diplomacy Implementation)

### New Feature: Vassal/Sovereign System

**Concept:** Factions can now be "vassals" of other factions. A vassal faction:
- Is fully controlled by their sovereign's player
- Retains their identity (name, banners, faction ID)
- Has their initiative merged with the sovereign
- Orders stored under vassal's faction ID (for logging/history)

**Data Model:**
```python
class Faction:
    vassal_of: Optional[FactionId] = None  # Sovereign faction (None = independent)
```

**Helper Methods (GameState):**
- `get_sovereign(faction_id)` → Returns the commanding faction
- `get_vassals(faction_id)` → Returns list of vassals
- `get_all_controlled_factions(faction_id)` → Sovereign + all vassals
- `make_vassal(vassal_id, sovereign_id)` → Establishes vassal relationship

**Order Validation:**
- `OrderManager.can_control_unit()` checks if a faction can issue orders to a unit
- Allows both direct ownership AND vassal units

**Database Migration:**
```sql
ALTER TABLE savediplomacy ADD COLUMN vassal_of INT DEFAULT -1;
```
Run `migrations/add_vassal_of_column.sql` to add the column.

---

### New Feature: Troll Diplomacy

**Concept:** Neutral troll tribes can join the Amani Empire through:
1. **Alliance Attack** - Any ALLIANCE_FACTIONS unit on troll base/expansion
2. **Zul'jin Alone** - Zul'jin (unit ID 0) alone in troll base

**Neutral Troll Factions:** (defined in `NEUTRAL_TROLL_FACTIONS`)
- Firetree, Smolderthorn, Shadowpine, Shadowglen
- Revantusk, Mossflayer, Witherbark, Vilebranch

**Trigger Rules:**

| Trigger | Condition | Result |
|---------|-----------|--------|
| Alliance Attack | ALLIANCE unit in troll base/expansion hex | Tribe → Amani vassal (chieftain survives) |
| Zul'jin Alone | Zul'jin only non-troll unit in base | Chieftain killed, tribe → Amani vassal |
| Zul'jin Alone (dead chief) | Zul'jin in base, chieftain already dead | Tribe → Amani vassal |
| Zul'jin on Expansion | Zul'jin alone on troll expansion | Expansion NOT destroyed (protection) |
| Base Tier 0 | Troll base destroyed | Cannot join Amani |

**Chieftain Definition:** Tier 3 unit of the neutral troll faction (each has exactly one)

**Implementation Location:** `resolution_engine._resolve_troll_diplomacy()`

**Phase Order:**
1. Movement Resolution
2. Fast Travel Resolution
3. **Update Initiative Phase** ← Troll Diplomacy checks here
4. Ranged Fire Resolution
5. Combat Resolution

---

### New Phase: Update Initiative

**Purpose:** Handles diplomatic changes that affect initiative.

**Location:** Between movement and combat in resolution.

**Current Logic:** Troll Diplomacy checks only.

**Future:** General diplomacy (alliance changes, betrayals, surprise attacks).

**Key Design:** Initiative changes take effect BEFORE combat that turn. This enables:
- Treachery/ambush mechanics
- Moving as allies, then changing initiative, then fighting

---

## Known Issues / Future Work

1. **Hexside limit edge cases** - May still have bugs with complex multi-order scenarios
2. **Air unit movement** - Air units should ignore hexside limits (implemented) but may need more testing
3. **Caravan path validation** - Backend and frontend validation should be kept in sync
4. **Troll Diplomacy testing** - New feature, needs gameplay testing
5. **General Diplomacy** - Update Initiative phase ready for expansion

---

## Development Tips

1. **Hot Reload:** Frontend changes auto-reload via Vite. Backend changes auto-reload via uvicorn `--reload`.

2. **Testing Movement:** Zul'aman (hex 972) is a good test location with roads, rivers, and multiple units.

3. **Database:** Shared AWS MySQL - changes persist across all dev environments.

4. **Falsy Values:** Always use `??` instead of `||` for numeric defaults in JavaScript.
