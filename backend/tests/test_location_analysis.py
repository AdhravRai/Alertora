"""
Unit and integration tests for Location Analysis Service and API endpoints.
Tests coordinate geocoding, domain boundary checks, feature preprocessing,
and hazard matrix table payload generation.
"""

import pytest
from starlette.testclient import TestClient

from backend.location_service import location_analyzer, FEATURE_COLUMNS
from backend.main import app

client = TestClient(app)


def test_domain_boundary_checks():
    """Verifies that NCMRWF IMDAA domain boundaries are strictly respected."""
    # Gorakhpur (26.7663, 83.3689) -> inside domain (Lat 25.08 - 27.00, Lon 82.08 - 84.00)
    assert location_analyzer.is_in_imdaa_domain(26.7663, 83.3689) is True

    # Patna (25.5941, 85.1376) -> outside longitude
    assert location_analyzer.is_in_imdaa_domain(25.5941, 85.1376) is False

    # Chennai (13.0827, 80.2707) -> outside domain
    assert location_analyzer.is_in_imdaa_domain(13.0827, 80.2707) is False

    # Mumbai (19.0760, 72.8777) -> outside domain
    assert location_analyzer.is_in_imdaa_domain(19.0760, 72.8777) is False


def test_search_locations_coordinates():
    """Verifies coordinate regex parsing in search."""
    results = location_analyzer.search_locations("26.76, 83.37")
    assert len(results) == 1
    assert results[0]["latitude"] == 26.76
    assert results[0]["longitude"] == 83.37
    assert results[0]["in_model_domain"] is True


def test_feature_columns_schema():
    """Verifies that FEATURE_COLUMNS has exactly 29 features matching training configuration."""
    assert len(FEATURE_COLUMNS) == 29
    assert "precipitation" in FEATURE_COLUMNS
    assert "cloud_water" in FEATURE_COLUMNS
    assert "surface_pressure" in FEATURE_COLUMNS
    assert "relative_humidity" in FEATURE_COLUMNS
    assert "temperature" in FEATURE_COLUMNS
    assert "temperature_lag1" in FEATURE_COLUMNS
    assert "temperature_lag3" in FEATURE_COLUMNS
    assert "precipitation_change" in FEATURE_COLUMNS


def test_api_location_search_endpoint():
    """Tests GET /api/location/search."""
    response = client.get("/api/location/search?q=Gorakhpur")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # At least one result should be Gorakhpur
    names = [item["name"] for item in data]
    assert "Gorakhpur" in names


def test_api_location_analyze_in_domain():
    """Tests POST /api/location/analyze for in-domain point."""
    payload = {
        "latitude": 26.7663,
        "longitude": 83.3689,
        "name": "Gorakhpur",
        "district": "Gorakhpur",
        "state": "Uttar Pradesh",
        "country": "India"
    }
    response = client.post("/api/location/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"

    table_row = data["table_row"]
    assert table_row["district"] == "Gorakhpur"
    assert "risk" in table_row
    assert "hazard" in table_row
    assert "confidence" in table_row
    assert "populationAtRisk" in table_row

    evidence = data["evidence"]
    assert evidence["location"]["in_model_domain"] is True
    assert evidence["result_type"] == "MODEL_DERIVED"
    assert "model_name" in evidence["model_prediction"]
    assert evidence["model_prediction"]["operating_threshold"] == 0.25
    assert len(evidence["top_contributors"]) == 5


def test_api_location_analyze_out_of_domain():
    """Tests POST /api/location/analyze for out-of-domain point."""
    payload = {
        "latitude": 13.0827,
        "longitude": 80.2707,
        "name": "Chennai",
        "district": "Chennai",
        "state": "Tamil Nadu",
        "country": "India"
    }
    response = client.post("/api/location/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"

    evidence = data["evidence"]
    assert evidence["location"]["in_model_domain"] is False
    assert "PROVIDER_DERIVED" in evidence["result_type"]
    assert len(evidence["missing_inputs"]) > 0
    assert "outside the trained model's validated NCMRWF IMDAA domain" in evidence["data_limitations"]
