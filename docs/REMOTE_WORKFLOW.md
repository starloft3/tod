# Remote Development Workflow

Quick reference for working on ToD from multiple locations.

---

## Starting Development Session

### 1. Pull Latest Changes
```powershell
cd C:\Kidpik\self\tod
git pull origin modernization
```

### 2. Start the Game (PowerShell)
```powershell
# Terminal 1 - Backend
.\venv\Scripts\python.exe -m uvicorn tod.api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Or just double-click `START_GAME.bat` (note: uses system Python, not venv)

### 3. Open Game
- **Game**: http://localhost:5173/
- **API Docs**: http://localhost:8000/docs

---

## Ending Development Session

### 1. Stop Servers
Press `Ctrl+C` in both terminal windows, or run `STOP_GAME.bat`

### 2. Commit and Push Changes
```powershell
git add .
git commit -m "Description of what you changed"
git push origin modernization
```

---

## Important Notes

### Shared Database
Both locations connect to the same MySQL database on AWS. This means:
- Changes to game state (resolving turns, spawning units) are immediately shared
- **Don't run multiple instances simultaneously** unless testing read-only
- Use **JSON saves** (Admin panel → Save) for local experiments

### Virtual Environment
This location uses a local venv at `.\venv\`. When running Python manually:
```powershell
.\venv\Scripts\python.exe -m <module>
```

Or activate it first:
```powershell
.\venv\Scripts\Activate.ps1
python -m <module>
```

### If Dependencies Change
```powershell
# Python
.\venv\Scripts\pip.exe install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named uvicorn" | Use venv python: `.\venv\Scripts\python.exe` |
| Port 8000 in use | Kill process: `Stop-Process -Name python -Force` |
| Port 5173 in use | Kill process: `Stop-Process -Name node -Force` |
| Database connection failed | Check internet; AWS database may be down |
| Frontend shows blank | Check backend is running; check browser console (F12) |

---

## Quick Git Reference

```powershell
# Check status
git status

# See what branch you're on
git branch

# Pull updates
git pull origin modernization

# Stage all changes
git add .

# Commit
git commit -m "Your message"

# Push
git push origin modernization

# Discard local changes (careful!)
git checkout -- filename
```

---

*Last updated: January 2026*
