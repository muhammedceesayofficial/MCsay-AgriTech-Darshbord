"""
BACKEND (FastAPI)
=================
This file is the "translator" between the browser and the database.

DATA FLOW:
  1. Browser loads http://127.0.0.1:8000  ->  FastAPI sends index.html
  2. index.html loads style.css and app.js (same origin, same server)
  3. app.js GET  /api/harvests  ->  we read SQLite  ->  JSON back to the table
  4. Farmer clicks Submit
  5. app.js POST /api/harvests with JSON (now includes location)
  6. FastAPI validates HarvestIn, then database.add_harvest(...)
  7. Farmer clicks "Generate Localized Advice"
  8. app.js POST /api/ai-advice (no body needed)
  9. We read SQLite, run agronomist.generate_localized_advice(), return JSON
"""

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import agronomist
import database

app = FastAPI(title="Farm Crop & Yield Tracker")

database.init_db()

STATIC_DIR = Path(__file__).parent

GambianLocation = Literal[
    "West Coast Region (WCR)",
    "North Bank Region (NBR)",
    "Lower River Region (LRR)",
    "Central River Region (CRR)",
    "Upper River Region (URR)",
]


class HarvestIn(BaseModel):
    """JSON shape expected from app.js on Submit."""

    field_name: str = Field(min_length=1, max_length=80)
    crop_type: str = Field(min_length=1, max_length=80)
    yield_kg: float = Field(gt=0, le=1_000_000)
    harvest_date: str = Field(min_length=10, max_length=10)
    location: GambianLocation


@app.get("/api/harvests")
def list_harvests():
    """Frontend calls this on page load: GET /api/harvests"""
    return database.get_all_harvests()


@app.post("/api/harvests")
def create_harvest(payload: HarvestIn):
    """Frontend calls this on Submit: POST /api/harvests with a JSON body."""
    try:
        return database.add_harvest(
            field_name=payload.field_name.strip(),
            crop_type=payload.crop_type.strip(),
            yield_kg=payload.yield_kg,
            harvest_date=payload.harvest_date,
            location=payload.location,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/api/ai-advice")
def ai_advice():
    """
    Frontend advisory button: POST /api/ai-advice
    We do not need a request body — the agronomist reads the same SQLite
    ledger the dashboard table uses.
    """
    harvests = database.get_all_harvests()
    return agronomist.generate_localized_advice(harvests)


@app.get("/")
def serve_dashboard():
    """Visiting the site in a browser hits this route and receives index.html."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/style.css")
def serve_css():
    return FileResponse(STATIC_DIR / "style.css")


@app.get("/app.js")
def serve_js():
    return FileResponse(STATIC_DIR / "app.js")
