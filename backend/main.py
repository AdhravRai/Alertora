"""
ALERTORA AI — FastAPI Server Engine
Provides RESTful API endpoints for severe weather nowcasting, GIS map data, EOC matrix, and alerts.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from backend.models import LocationProfile, AlertItem, EOCDistrictRow
from backend.fixtures import DEVELOPMENT_FIXTURE
from backend.ai_engine import ai_engine

app = FastAPI(
    title="ALERTORA AI — Severe Weather Nowcasting API",
    description="Backend API for Smart India Hackathon Problem SIH26084",
    version="2.4.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "app": "ALERTORA AI",
        "tagline": "Predict Early. Prepare Smart. Save Lives.",
        "status": "ONLINE",
        "sih_problem": "SIH26084"
    }

@app.get("/api/system-status")
def get_system_status():
    return DEVELOPMENT_FIXTURE["system_status"]

@app.get("/api/prediction")
def get_prediction(location_id: str = "chennai", lat: float = 13.0827, lng: float = 80.2707):
    return ai_engine.predict_nowcast(lat=lat, lng=lng, location_id=location_id)


@app.get("/api/locations")
def get_locations():
    return [
        {
            "id": "chennai",
            "name": "Chennai Metropolis",
            "latitude": 13.0827,
            "longitude": 80.2707
        }
    ]
    
@app.get("/api/current-risk")
def get_current_risk():
    return DEVELOPMENT_FIXTURE["current_risk"]


@app.get("/api/forecast")
def get_forecast():
    return DEVELOPMENT_FIXTURE["forecast"]


@app.get("/api/storms")
def get_storms():
    return DEVELOPMENT_FIXTURE["storms"]


@app.get("/api/alerts")
def get_alerts():
    return DEVELOPMENT_FIXTURE["alerts"]


@app.get("/api/explainability")
def get_explainability():
    return DEVELOPMENT_FIXTURE["explainability"]


@app.get("/api/historical-events")
def get_historical_events():
    return DEVELOPMENT_FIXTURE["historical_events"]


@app.get("/api/historical-events/{event_id}")
def get_historical_event(event_id: str):

    for event in DEVELOPMENT_FIXTURE["historical_events"]["events"]:
        if event.get("id") == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Historical event not found"
    )







@app.post("/api/trigger-warning")
def trigger_warning(district: str):
    return {
        "status": "SUCCESS",
        "district": district,
        "message": f"Automated Emergency Cell Broadcast Warning dispatched to {district} sector.",
        "broadcast_channels": ["Cell Broadcast", "State Siren Grid", "Mobile Push"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
