import json
from pathlib import Path


HANDOFF_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "processed"
    / "alertora_forecast_july29_0200.json"
)


def load_handoff():
    if not HANDOFF_FILE.exists():
        raise FileNotFoundError(
            f"ML handoff file not found: {HANDOFF_FILE}"
        )

    with open(
        HANDOFF_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def build_api_data():
    data = load_handoff()

    horizons = data["horizons"]
    first_horizon = horizons[0]

    # ---------------------------------------------------------
    # Current / near-term risk
    # ---------------------------------------------------------
    first_grid = first_horizon["grid"]["cells"]

    max_nowcast = max(
        cell["nowcast_probability"]
        for cell in first_grid
    )

    high_rain_cells = sum(
        1
        for cell in first_grid
        if cell["predicted_high_rain"]
    )

    risk_level = (
        "HIGH"
        if high_rain_cells > 0
        else "MODERATE"
    )

    current_risk = {
        "timestamp": data["forecast"]["base_time"],
        "latitude": data["storm"]["current_position"]["latitude"],
        "longitude": data["storm"]["current_position"]["longitude"],
        "nowcast_probability": round(
            max_nowcast * 100,
            2
        ),
        "predicted_high_rain_cells": high_rain_cells,
        "risk_level": risk_level,
        "risk_basis": (
            "Derived from the first forecast horizon's "
            "predicted_high_rain grid cells."
        ),
        "method": data["method"],
        "method_note": data["method_note"],
        "is_fixture": False,
        "source_type": "ML_HANDOFF"
    }

    # ---------------------------------------------------------
    # Forecast horizons
    # ---------------------------------------------------------
    forecast_points = []

    for horizon in horizons:
        summary = horizon["summary"]

        forecast_points.append(
            {
                "time": (
                    f"+{int(horizon['lead_hours'])}h"
                ),

                "hour": (
                    f"+{int(horizon['lead_hours'])} HR"
                ),

                "lead_hours":
                    horizon["lead_hours"],

                "lead_minutes":
                    horizon["lead_minutes"],

                "nowcast_probability": round(
                    summary["maximum_probability"] * 100,
                    2
                ),

                "mean_probability": round(
                    summary["mean_probability"] * 100,
                    2
                ),

                "ml_probability": round(
                    max(
                        cell["ml_probability"]
                        for cell in horizon["grid"]["cells"]
                    ) * 100,
                    2
                ),

                "predicted_high_rain_cells":
                    summary["predicted_high_rain_cells"],

                "total_cells":
                    summary["total_cells"],

                "storm_position":
                    horizon["storm_position"],

                # Real ML spatial risk grid
                "grid": {
                    "rows":
                        horizon["grid"]["rows"],

                    "columns":
                        horizon["grid"]["columns"],

                    "cells":
                        horizon["grid"]["cells"]
                }
            }
        )

    forecast = {
        "forecast_time": data["forecast"]["base_time"],

        "time_grid": [
            point["time"]
            for point in forecast_points
        ],

        "points": forecast_points,

        "horizon_hours":
            data["forecast"]["horizon_hours"],

        "method":
            data["method"],

        "method_note":
            data["method_note"],

        "is_fixture": False,

        "source_type":
            "ML_HANDOFF"
    }

    # ---------------------------------------------------------
    # Storm trajectory
    # ---------------------------------------------------------
    storm = data["storm"]

    trajectory = []

    for horizon in horizons:
        position = horizon["storm_position"]

        trajectory.append(
            {
                "time": (
                    f"+{int(horizon['lead_hours'])}h"
                ),

                "latitude":
                    position["latitude"],

                "longitude":
                    position["longitude"]
            }
        )

    storms = {
        "storms": [
            {
                "id": storm["track_id"],

                "type":
                    "trajectory_based_nowcast",

                "intensity":
                    None,

                "current_position": {
                    "latitude":
                        storm["current_position"]["latitude"],

                    "longitude":
                        storm["current_position"]["longitude"]
                },

                "trajectory":
                    trajectory
            }
        ],

        "is_fixture": False,

        "source_type":
            "ML_HANDOFF"
    }

    # ---------------------------------------------------------
    # Explainability
    # ---------------------------------------------------------
    xai = data["explainability"]

    explainability = {
        "method":
            xai["method"],

        "global_top_features":
            xai["global_top_features"],

        "cell_explanations":
            xai["cell_explanations"],

        "is_fixture": False,

        "source_type":
            "ML_HANDOFF"
    }

    # ---------------------------------------------------------
    # Derived alert
    # ---------------------------------------------------------
    alerts = {
        "alerts": [
            {
                "id":
                    f"ML-{storm['track_id']}",

                "severity":
                    risk_level,

                "title":
                    "Heavy Rain Nowcast Risk",

                "location":
                    "ML forecast region",

                "timestamp":
                    data["forecast"]["base_time"],

                "eta":
                    "+1h to +6h forecast window",

                "confidence":
                    None,

                "hazardTypes":
                    ["Heavy Rain"],

                "summary": (
                    f"{high_rain_cells} of "
                    f"{first_horizon['summary']['total_cells']} "
                    "cells are predicted high-rain cells "
                    "in the +1h horizon."
                ),

                "action": (
                    "Development/demo forecast output. "
                    "Not an official public warning."
                )
            }
        ],

        "is_fixture": False,

        "source_type":
            "ML_HANDOFF"
    }

    # ---------------------------------------------------------
    # Historical verification
    # ---------------------------------------------------------
    historical = data["historical_verification"]

    return {
        "system_status": {
            "status":
                "ML_HANDOFF_DEMO",

            "environment":
                "local-development",

            "source_type":
                "ML_HANDOFF",

            "live":
                False,

            "dataset":
                data["forecast"]["source"]["dataset"],

            "model_component":
                data["method"]["ml_component"],

            "nowcast_component":
                data["method"]["spatial_component"]
        },

        "current_risk":
            current_risk,

        "forecast":
            forecast,

        "storms":
            storms,

        "alerts":
            alerts,

        "explainability":
            explainability,

        "historical_events": {
            "available":
                historical["available"],

            "note":
                historical["note"],

            "events":
                []
        }
    }


DEVELOPMENT_FIXTURE = build_api_data()