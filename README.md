# GreenLedger — Farm Crop & Yield Tracker

A first AgriTech prototype that shows how a **browser (HTML/CSS/JS)**, a **Python API (FastAPI)**, and a **SQLite database** talk to each other.

## How the pieces connect

```
Farmer fills the form in index.html
        │
        ▼
app.js sends JSON with fetch()  ──POST /api/harvests──►  main.py (FastAPI)
                                                            │
                                                            ▼
                                                      database.py
                                                            │
                                                            ▼
                                                      farm_yields.db (SQLite)

On page load / refresh:
app.js GET /api/harvests  ◄── JSON list ──  main.py  ◄──  database.py  ◄──  SQLite

Advice button:
app.js POST /api/ai-advice  ──►  main.py  ──►  agronomist.py (same SQLite ledger)
```

| File | Role |
| --- | --- |
| `index.html` | The dashboard the farmer sees |
| `style.css` | Colors, layout, typography |
| `app.js` | Collects the form and calls the API |
| `main.py` | Receives HTTP, validates data, calls the database |
| `database.py` | Creates the table and runs SQL `INSERT` / `SELECT` |
| `agronomist.py` | Rule-based Gambian farm advice from the ledger |

Data is stored in `farm_yields.db` next to these files. Refreshing the page does **not** wipe harvests.

## Run locally (Windows)

1. Use **Python 3.11–3.14** (FastAPI’s packages do not install cleanly on the Python 3.15 beta). On this PC:

   ```powershell
   py -3.14 --version
   ```

2. Open **PowerShell** in this folder:

   ```powershell
   cd "C:\Users\User\OneDrive\Documents\MCsaySchool\Tech Work Space\AgriTech-Dashbord"
   ```

3. Create and activate a virtual environment (an isolated Python toolbox for this project):

   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If Windows blocks the activate script, run this once, then try again:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
   ```

4. Install FastAPI and the web server:

   ```powershell
   pip install -r requirements.txt
   ```

5. Start the app:

   ```powershell
   uvicorn main:app --reload
   ```

6. In your browser open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Leave the PowerShell window open while you use the dashboard. Press `Ctrl+C` to stop the server.

Optional: browse the auto-generated API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Try the data flow

1. Log a harvest and watch the table and totals update.
2. Refresh the page — the same rows should still be there (SQLite).
3. Open `farm_yields.db` later with any SQLite viewer if you want to see the raw table.
