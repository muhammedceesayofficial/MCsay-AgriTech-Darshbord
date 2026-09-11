"""
DATABASE LAYER (SQLite)
=======================
This file is the "memory" of the app. The backend (main.py) never talks to
the .db file directly — it calls the functions below.

DATA FLOW:
  Frontend (app.js)  --HTTP-->  Backend (main.py)  --Python function-->  This file  --SQL-->  farm_yields.db

We use parameterized queries (?, ?) so user input is never pasted into SQL
as raw text. That prevents SQL injection (a common security bug).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "farm_yields.db"

# Values that match the Location (Gambia) dropdown in index.html.
GAMBIAN_REGIONS = (
    "West Coast Region (WCR)",
    "North Bank Region (NBR)",
    "Lower River Region (LRR)",
    "Central River Region (CRR)",
    "Upper River Region (URR)",
)


def get_connection():
    """Open a connection. row_factory lets us read rows like dictionaries."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _column_names(connection):
    rows = connection.execute("PRAGMA table_info(harvests)").fetchall()
    return {row["name"] for row in rows}


def init_db():
    """
    Create the harvests table if needed, then add the location column to older
    databases without deleting existing harvests (ALTER TABLE, not a wipe).
    main.py calls this once when the server starts.
    """
    connection = get_connection()
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS harvests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            yield_kg REAL NOT NULL,
            harvest_date TEXT NOT NULL,
            location TEXT NOT NULL DEFAULT 'West Coast Region (WCR)'
        )
        """
    )
    columns = _column_names(connection)
    if "location" not in columns:
        # Older farm_yields.db files had no location column. Add it in place.
        connection.execute(
            """
            ALTER TABLE harvests
            ADD COLUMN location TEXT NOT NULL DEFAULT 'West Coast Region (WCR)'
            """
        )
    connection.commit()
    connection.close()


def add_harvest(field_name, crop_type, yield_kg, harvest_date, location):
    """
    INSERT one new harvest, including the Gambian region.
    Called by POST /api/harvests in main.py after FastAPI validates the JSON.
    """
    connection = get_connection()
    cursor = connection.execute(
        """
        INSERT INTO harvests (field_name, crop_type, yield_kg, harvest_date, location)
        VALUES (?, ?, ?, ?, ?)
        """,
        (field_name, crop_type, yield_kg, harvest_date, location),
    )
    harvest_id = cursor.lastrowid
    connection.commit()
    connection.close()
    return {
        "id": harvest_id,
        "field_name": field_name,
        "crop_type": crop_type,
        "yield_kg": yield_kg,
        "harvest_date": harvest_date,
        "location": location,
    }


def get_all_harvests():
    """
    SELECT every harvest, newest first.
    Used by GET /api/harvests (the table) and POST /api/ai-advice (the agronomist).
    """
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT id, field_name, crop_type, yield_kg, harvest_date, location
        FROM harvests
        ORDER BY harvest_date DESC, id DESC
        """
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]
