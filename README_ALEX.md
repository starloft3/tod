# 🎮 Tides of Darkness - Tester Build

Welcome! This document will get you up and running quickly.

---

## Quick Start (3 Steps)

### Step 1: Install Prerequisites (One-Time)

You need **Python 3.9+** and **Node.js 18+** installed.

**Don't have them?** Run:
```
INSTALL_DEPENDENCIES.bat
```
This will check what's missing and guide you through installation.

**Already have them?** The script will install the required packages.

### Step 2: Start the Game

Double-click:
```
START_GAME.bat
```

This starts both servers and opens your browser to the game.

### Step 3: Play!

The game opens at: **http://localhost:5173**

---

## Getting Updates

When notified of updates, open a terminal in the game folder and run:
```
git pull origin modernization
```

Then restart the game.

---

## How to Stop

Either:
- Close the two terminal windows that opened, OR
- Double-click `STOP_GAME.bat`

---

## Documentation

| File | Description |
|------|-------------|
| `docs/SETUP_GUIDE.md` | Detailed installation instructions |
| `docs/DEBUG_TOOLS.md` | How to use the Admin panel |
| `docs/KNOWN_ISSUES.md` | Current bugs and limitations |

---

## Quick Gameplay Reference

### Submitting Orders

1. Click on a **unit** to select it
2. Click **Move** to start a movement order
3. Click hexes to build a path
4. Click **Submit Order** when done

### Resolving Turns

1. Go to the **Admin** panel (sidebar)
2. Click **Resolve Turn**
3. Check the **Logs** to see what happened

### Using Debug Tools

The Admin panel lets you:
- Spawn units anywhere
- Modify unit stats (HP, combat, location, etc.)
- Toggle infinite resources
- Enable verbose combat logging
- Save/Load game states

---

## Troubleshooting

### Game won't start
- Check that both Python and Node are installed
- Run `INSTALL_DEPENDENCIES.bat` again

### Blank screen / errors
- Make sure the backend started (check for errors in the "ToD Backend" window)
- Try refreshing with Ctrl+F5

### Database connection failed
- Check your internet connection
- The database server may be down - contact the dev team

---

## Reporting Issues

When you find a bug, please note:

1. **What were you trying to do?**
2. **What happened instead?**
3. **Any error messages?** (check browser console with F12)
4. **Unit IDs involved?** (visible when clicking on units)

Save the game state before doing something risky - you can always reload!

---

**Happy Testing! 🎯**
