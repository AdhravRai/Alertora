"""
ALERTORA AI - FastAPI Server Engine

Provides RESTful API endpoints for:
- Severe weather nowcasting
- Current ML risk
- 0-6 hour forecast
- Storm trajectory
- Alerts
- Explainability
- Risk zones
- Historical verification metadata
- GIS/frontend integration
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import LocationProfile, AlertItem, EOCDistrictRow
from backend.ml_handoff import DEVELOPMENT_FIXTURE
from backend.ai_engine import ai_engine


app = FastAPI(
    title="ALERTORA AI - Severe Weather Nowcasting API",
    description=(
        "Backend API for Smart India Hackathon Problem SIH26084. "
        "Consumes the final Alertora ML handoff JSON."
    ),
    version="2.4.0",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "app": "ALERTORA AI",
        "tagline": "Predict Early. Prepare Smart. Save Lives.",
        "status": "ONLINE",
        "sih_problem": "SIH26084",
    }


# ---------------------------------------------------------------------------
# System Status
# ---------------------------------------------------------------------------

@app.get("/api/system-status")
def get_system_status():
    """
    Returns the status of the ML handoff and its data source.

    This endpoint intentionally does not claim live radar,
    satellite, or lightning connectivity.
    """
    return DEVELOPMENT_FIXTURE["system_status"]


# ---------------------------------------------------------------------------
# Legacy Prediction Endpoint
# ---------------------------------------------------------------------------

@app.get("/api/prediction")
def get_prediction(
    location_id: str = "chennai",
    lat: float = 13.0827,
    lng: float = 80.2707,
):
    """
    Existing compatibility endpoint.

    Kept intact so older frontend functionality continues to work.
    """
    return ai_engine.predict_nowcast(
        lat=lat,
        lng=lng,
        location_id=location_id,
    )


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

@app.get("/api/locations")
def get_locations():
    """
    Returns the forecast location represented by the ML handoff.

    The frontend expects a location selector, so we expose the
    storm/forecast position from the actual ML handoff.
    """
    current_position = (
        DEVELOPMENT_FIXTURE["storms"]["storms"][0]["current_position"]
    )

    return [
        {
            "id": "ml-forecast-region",
            "name": "ML Forecast Region",
            "latitude": current_position["latitude"],
            "longitude": current_position["longitude"],
        }
    ]


# ---------------------------------------------------------------------------
# Current Risk
# ---------------------------------------------------------------------------

@app.get("/api/current-risk")
def get_current_risk():
    """
    Returns current/near-term risk derived from the ML handoff.
    """
    return DEVELOPMENT_FIXTURE["current_risk"]


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

@app.get("/api/forecast")
def get_forecast():
    """
    Returns the 0-6 hour trajectory-based nowcast forecast.
    """
    return DEVELOPMENT_FIXTURE["forecast"]


# ---------------------------------------------------------------------------
# Storms / Trajectory
# ---------------------------------------------------------------------------

@app.get("/api/storms")
def get_storms():
    """
    Returns current storm position and +1h to +6h trajectory.
    """
    return DEVELOPMENT_FIXTURE["storms"]


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@app.get("/api/alerts")
def get_alerts():
    """
    Returns an Alertora alert derived from the ML handoff.
    """
    return DEVELOPMENT_FIXTURE["alerts"]


# ---------------------------------------------------------------------------
# Explainability
# ---------------------------------------------------------------------------

@app.get("/api/explainability")
def get_explainability():
    """
    Returns SHAP-based global and cell-level explainability.
    """
    return DEVELOPMENT_FIXTURE["explainability"]


# ---------------------------------------------------------------------------
# Risk Zones
# ---------------------------------------------------------------------------

RISK_ZONES_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "risk_zones_july29_0200.json"
)


@app.get("/api/risk-zones")
def get_risk_zones():
    """
    Returns geographic high-risk zones generated as a
    post-processing layer from the validated ML handoff.

    The underlying XGBoost/nowcast handoff is not modified.
    """
    if not RISK_ZONES_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Risk-zone artifact not found",
        )

    try:
        with open(
            RISK_ZONES_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid risk-zone JSON: {exc}",
        )


# ---------------------------------------------------------------------------
# Historical Events / Verification
# ---------------------------------------------------------------------------

@app.get("/api/historical-events")
def get_historical_events():
    """
    Returns historical verification metadata from the ML handoff.

    The current handoff provides verification metadata rather than
    a populated event catalogue.
    """
    return DEVELOPMENT_FIXTURE["historical_events"]


@app.get("/api/historical-events/{event_id}")
def get_historical_event(event_id: str):
    """
    Returns one historical event when available.
    """
    events = DEVELOPMENT_FIXTURE["historical_events"].get(
        "events",
        [],
    )

    for event in events:
        if event.get("id") == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Historical event not found",
    )


# ---------------------------------------------------------------------------
# Trigger Warning
# ---------------------------------------------------------------------------

@app.post("/api/trigger-warning")
def trigger_warning(district: str):
    """
    Demo-only warning trigger.

    This does not represent a real government/public alert dispatch.
    """
    return {
        "status": "SUCCESS",
        "district": district,
        "message": (
            f"Demo emergency warning action triggered for "
            f"{district} sector."
        ),
        "broadcast_channels": [
            "Cell Broadcast",
            "State Siren Grid",
            "Mobile Push",
        ],
    }


# ---------------------------------------------------------------------------
# Local Development Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
