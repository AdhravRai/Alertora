"""
Temporary development fixtures for Alertora.

IMPORTANT:
These are NOT real ML predictions.
They are only used to test frontend/API integration.
"""

DEVELOPMENT_FIXTURE = {

    "system_status": {
        "status": "DEVELOPMENT_FIXTURE",
        "environment": "local-development",
        "sources": {
            "ml_model": {
                "status": "fixture",
                "live": False
            },
            "nowcast_engine": {
                "status": "fixture",
                "live": False
            },
            "radar": {
                "status": "not_connected",
                "live": False
            },
            "satellite": {
                "status": "not_connected",
                "live": False
            },
            "lightning": {
                "status": "not_connected",
                "live": False
            }
        }
    },

    "current_risk": {
        "timestamp": "2026-09-25T12:30:00Z",
        "latitude": 13.0827,
        "longitude": 80.2707,

        "thunderstorm_probability": 72,
        "heavy_rain_probability": 68,

        "confidence": None,

        "risk_level": "HIGH",

        "top_features": [
            {
                "name": "radar_reflectivity",
                "contribution": None
            },
            {
                "name": "cloud_top_temperature",
                "contribution": None
            },
            {
                "name": "lightning_rate",
                "contribution": None
            }
        ],

        "is_fixture": True
    },

    "forecast": {
        "forecast_time": "2026-09-25T12:30:00Z",

        "time_grid": [
            "+0h",
            "+30m",
            "+1h",
            "+2h",
            "+3h",
            "+4h",
            "+5h",
            "+6h"
        ],

        "points": [
            {
                "time": "+0h",
                "thunderstorm_probability": 72,
                "heavy_rain_probability": 68
            },
            {
                "time": "+30m",
                "thunderstorm_probability": 78,
                "heavy_rain_probability": 73
            },
            {
                "time": "+1h",
                "thunderstorm_probability": 84,
                "heavy_rain_probability": 80
            },
            {
                "time": "+2h",
                "thunderstorm_probability": 88,
                "heavy_rain_probability": 85
            },
            {
                "time": "+3h",
                "thunderstorm_probability": 82,
                "heavy_rain_probability": 78
            },
            {
                "time": "+4h",
                "thunderstorm_probability": 70,
                "heavy_rain_probability": 65
            },
            {
                "time": "+5h",
                "thunderstorm_probability": 55,
                "heavy_rain_probability": 50
            },
            {
                "time": "+6h",
                "thunderstorm_probability": 40,
                "heavy_rain_probability": 36
            }
        ],

        "is_fixture": True
    },

    "storms": {
        "storms": [
            {
                "id": "fixture-storm-01",

                "type": "convective_cell",

                "intensity": None,

                "current_position": {
                    "latitude": 13.14,
                    "longitude": 79.90
                },

                "trajectory": [
                    {
                        "time": "+30m",
                        "latitude": 13.16,
                        "longitude": 79.96
                    },
                    {
                        "time": "+1h",
                        "latitude": 13.18,
                        "longitude": 80.02
                    },
                    {
                        "time": "+2h",
                        "latitude": 13.20,
                        "longitude": 80.08
                    },
                    {
                        "time": "+3h",
                        "latitude": 13.22,
                        "longitude": 80.14
                    },
                    {
                        "time": "+4h",
                        "latitude": 13.24,
                        "longitude": 80.20
                    },
                    {
                        "time": "+5h",
                        "latitude": 13.26,
                        "longitude": 80.26
                    },
                    {
                        "time": "+6h",
                        "latitude": 13.28,
                        "longitude": 80.32
                    }
                ]
            }
        ],

        "is_fixture": True
    },

    "alerts": {
        "alerts": [
            {
                "id": "FIXTURE-001",
                "severity": "HIGH",
                "title": "Development Convective Risk",
                "location": "Test Region",
                "timestamp": "2026-09-25T12:30:00Z",
                "eta": "Estimated",
                "confidence": None,
                "hazardTypes": [
                    "Thunderstorm",
                    "Heavy Rain"
                ],
                "summary": "Development fixture for frontend integration.",
                "action": "No operational action. Development data only."
            }
        ],

        "is_fixture": True
    },

    "explainability": {
        "available": False,
        "message": "Actual model feature contributions will be supplied by Person A.",
        "features": [],
        "is_fixture": True
    },

    "historical_events": {
        "events": [],
        "message": "Historical event data will be connected during integration.",
        "is_fixture": True
    }
}