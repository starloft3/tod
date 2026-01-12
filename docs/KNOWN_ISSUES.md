# Known Issues & Limitations

Last Updated: January 2026

This document lists known bugs, quirks, and limitations in the current build.

---

## 🔴 Critical Issues

*None currently known that block testing.*

---

## 🟡 Gameplay Bugs

### Combat

1. **Mixed Land/Sea Combat**
   - Combat involving both land and sea units in the same hex is not fully implemented
   - Targeting rules may behave unexpectedly
   - Workaround: Avoid creating scenarios with mixed unit types in combat

2. **3+ Initiative Combat**
   - Combat hexes with units from 3+ different initiatives have undefined behavior
   - The game assumes 2-way combat (attackers vs defenders)
   - Workaround: Avoid three-way battles for now

### Movement

3. **Hexside Limits**
   - Very high traffic through a single hexside may not resolve perfectly
   - The conflict resolution picks winners somewhat arbitrarily

4. **Movement Through Combat (Frontend)**
   - Backend correctly stops movement when entering a hex with hostile units
   - Frontend does NOT yet prevent players from plotting moves through known hostiles
   - If you plot a path through an enemy-occupied hex, movement will stop there on resolution
   - Frontend validation will be added when faction-specific vision/fog of war is implemented

### Ranged Fire (NEW)

5. **Ranged Fire Targeting**
   - Just implemented - may have edge cases
   - Only INTERIOR_SIEGE units (Catapults, Ballistas, etc.) can use this
   - Can target any adjacent hex containing hostile units

---

## 🟢 UI/Visual Issues

### Map

5. **Caravan Lines**
   - Sometimes hard to see on certain terrain
   - Use the Show/Hide Caravans toggle if cluttered

6. **Unit Stacking Display**
   - Many units in one hex can make the display crowded
   - Click on the hex to see full unit list

### Logs

7. **Log Scrolling**
   - Very long log entries may display awkwardly
   - Expand individual entries for full details

---

## 🔧 Technical Limitations

### Database

8. **No Offline Mode**
   - Game requires connection to the MySQL database on AWS
   - Cannot play without internet

9. **Single Game Instance**
   - Only one game is stored in the database
   - Saving overwrites the shared game state

### Performance

10. **Large Saves**
    - Loading games with many queued orders may be slow
    - JSON save files can get large

---

## 📝 Not Yet Implemented

The following features are planned but not in this build:

- [ ] Victory Conditions
- [ ] Diplomacy System
- [ ] Advanced Veterancy (skill trees)
- [ ] Build Base action (leaders creating new bases)
- [ ] Naval Transport (boarding/unboarding ships)
- [ ] Air Combat special rules
- [ ] Fog of War (visual only - can use Admin mode)

---

## 🐛 Reporting New Issues

When you find a bug:

1. **Note what you were doing** - What actions led to the bug?
2. **Check the browser console** - Press F12 → Console tab for errors
3. **Save the game state** - So we can reproduce it
4. **Note the Unit IDs** - If specific units are involved

Document issues with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Any error messages

---

## 📋 Recently Fixed

- ✅ Movement logs showing wrong hex IDs
- ✅ Unable to spawn Faction 0 (Amani) units
- ✅ Clicking on bases during move order input
- ✅ Caravan destination showing "Unknown"
- ✅ Verbose combat log terrain details incorrect
- ✅ Base destruction not creating ruins
- ✅ Tier-up not working for mid-game kills
