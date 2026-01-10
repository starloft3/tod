# Tides of Darkness - Setup Guide

This guide will help you get the game running on your machine.

## Prerequisites

### 1. Python 3.9 or higher

**Check if installed:**
```
python --version
```

**If not installed:**
- Download from: https://www.python.org/downloads/
- During installation, **CHECK "Add Python to PATH"**
- Recommended: Python 3.9, 3.10, or 3.11

### 2. Node.js 18 or higher (includes npm)

**Check if installed:**
```
node --version
npm --version
```

**If not installed:**
- Download from: https://nodejs.org/
- Choose the **LTS** (Long Term Support) version
- Run the installer with default options

### 3. Network Access

The game connects to a MySQL database hosted on AWS. Ensure you can reach:
- Host: `warcraft.c7a0os00g0wx.us-east-2.rds.amazonaws.com`
- Port: `3306`

Most home/office networks allow this. If you're on a corporate VPN or restricted network, you may need to disconnect or request access.

---

## First-Time Setup

### Step 1: Install Python Dependencies

Open a terminal/command prompt in the game folder and run:

```
pip install -r requirements.txt
```

This installs: FastAPI, uvicorn, PyMySQL, pydantic, pygame

### Step 2: Install Frontend Dependencies

Navigate to the frontend folder and install:

```
cd frontend
npm install
cd ..
```

This installs: Vue 3, vue-router, axios, vite

---

## Running the Game

### Option A: Use the Start Script (Recommended)

Double-click `START_GAME.bat` in the game folder.

This will:
1. Start the backend server (Python)
2. Start the frontend dev server (Node)
3. Open your browser to the game

### Option B: Manual Start

**Terminal 1 - Backend:**
```
python -m uvicorn tod.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```
cd frontend
npm run dev
```

Then open: http://localhost:5173

---

## Stopping the Game

### If using START_GAME.bat:
- Close both terminal windows that opened, OR
- Double-click `STOP_GAME.bat`

### If started manually:
- Press `Ctrl+C` in each terminal window

---

## Troubleshooting

### "Python was not found"
- Python isn't in your PATH
- Reinstall Python and check "Add Python to PATH"
- Or use full path: `C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe`

### "npm is not recognized"
- Node.js isn't installed or not in PATH
- Reinstall Node.js

### "Connection refused" or database errors
- Check your internet connection
- If on VPN, try disconnecting
- The database server may be temporarily down

### Frontend shows blank page
- Make sure backend is running first
- Check browser console (F12) for errors
- Try refreshing with Ctrl+F5

### Port already in use
- Another program is using port 8000 or 5173
- Close other instances of the game
- Or change the port in the start commands

---

## Quick Reference

| What | URL |
|------|-----|
| Game (Frontend) | http://localhost:5173 |
| API (Backend) | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
