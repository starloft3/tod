# Debug Tools Reference

The Admin panel provides powerful tools for testing and debugging. Access it via the sidebar.

---

## Admin Panel Sections

### 1. Turn Information

Shows current game state:
- **Round Number**: Which round of the game (1, 2, 3...)
- **Round Side**: Horde or Alliance
- **Initiative**: Which faction(s) are currently acting
- **Phase**: Planning or Resolution

### 2. Game Configuration

Live-adjustable game constants organized by category:

#### Combat
- `river_crossing_penalty`: Penalty for attacking over rivers
- `fortification_penalty`: Penalty for attacking fortifications
- `flanking_bonus_increment`: Bonus per controlled flanking hexside

#### Terrain
- Terrain penalties for Plains, Forest, Mountain, Swamp
- Initial defender bonuses by terrain type

#### Economic
- Commerce/Rest costs and gains
- Upgrade costs for base tiers

#### Caravan
- Max caravan length
- Caravan establishment costs by distance

#### Movement
- Road hexside bonus
- Hexside movement limits

#### Debug
- **Infinite Resources**: Bases have unlimited gold/lumber/oil
- **Verbose Combat Logs**: Show detailed dice rolls and modifiers
- **Instant Kill Mode**: Any hit kills the target (for quick testing)
- **No Damage Mode**: Attacks happen but deal no damage (for testing flow)

---

## Modify Unit Section

Edit individual unit stats in real-time:

1. Enter a **Unit ID** (visible when you click on a unit on the map)
2. Click **Load Unit**
3. Modify any stats:
   - **HP**: Current health (1 to Max HP)
   - **Max HP**: Maximum health (1-30)
   - **Combat**: Attack value (10-80)
   - **Movement**: Movement points (1-5)
   - **Light/Heavy/Natural Armor**: (0-5 each)
   - **Tier**: Veterancy level (0-4)
   - **Location**: Hex ID to teleport the unit
   - **Faction**: Change ownership

4. Click **Save Changes**

**Quick Actions:**
- **Kill Unit**: Instantly kills the selected unit
- **Full Heal**: Restores HP to max

---

## Spawn Unit Section

Create new units anywhere on the map:

1. Select **Unit Type** from dropdown
2. Enter **Faction ID** (0=Amani, 1=Bleeding Hollow, etc.)
3. Enter **Hex ID** for spawn location
4. Click **Spawn Unit**

Tip: Look at the hex ID in the bottom-left when hovering over the map.

---

## Save/Load Section

### Saving
1. Enter a save name (e.g., "before_big_battle")
2. Optionally add notes
3. Click **Save Game**

### Loading
1. Click a save from the list
2. Review the metadata (turn, date, notes)
3. Click **Load** to restore that state

⚠️ Loading will discard any unsaved changes!

---

## Common Testing Workflows

### Test a Combat Scenario
1. Spawn opposing units in adjacent hexes
2. Use Modify Unit to set specific stats
3. Move one unit into the other's hex
4. Click **Resolve Turn**
5. Check logs for detailed combat breakdown

### Test Economic Actions
1. Enable **Infinite Resources** in Debug config
2. Queue multiple Harvest/Commerce actions
3. Resolve and verify gold/lumber/oil changes

### Test Movement
1. Spawn a unit with specific movement points
2. Issue a long movement order
3. Resolve and check the movement log

### Test Edge Cases
1. Save the game state first!
2. Make your changes
3. If something breaks, reload the save

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| W/A/S/D | Pan the map |
| Mouse wheel | Zoom in/out |
| Escape | Cancel current order |
| Click unit | Select for orders |
| Click hex | View hex details |

---

## Finding Unit/Hex IDs

- **Unit ID**: Click on a unit → shown in the info panel as "Unit ID: X"
- **Hex ID**: Hover over any hex → shown in the bottom status bar
- **Base ID**: Click on a base → shown in the info panel
