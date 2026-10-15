"""
Integration test suite for FastAPI REST endpoints, real-time events,
device registration, alert dispatch, and caching headers.
"""

import pytest
from starlette.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify GET / endpoint returns correct branding, version, and features."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "ALERTORA AI"
    assert data["status"] == "ONLINE"
    assert "version" in data


def test_system_status_endpoint():
    """Verify GET /api/system-status returns status, sensors, and sse status."""
    response = client.get("/api/system-status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "AI SYSTEM ONLINE"
    assert "sensors" in data
    assert "sse" in data


def test_locations_endpoint_region_metadata():
    """Verify GET /api/locations returns canonical region metadata with valid risk and coordinates."""
    response = client.get("/api/locations")
    assert response.status_code == 200
    locations = response.json()
    assert isinstance(locations, list)
    assert len(locations) > 0

    loc = locations[0]
    # Verify canonical region metadata fields
    assert "id" in loc and loc["id"] is not None
    assert "name" in loc and loc["name"] is not None
    assert "region" in loc or "region_id" in loc
    assert "currentRisk" in loc and loc["currentRisk"] is not None
    assert loc["currentRisk"] != "undefined"
    assert "latitude" in loc or "lat" in loc
    assert "longitude" in loc or "lng" in loc
    assert isinstance(loc.get("lat") or loc.get("latitude"), (int, float))
    assert isinstance(loc.get("lng") or loc.get("longitude"), (int, float))


def test_prediction_endpoint():
    """Verify existing GET /api/prediction backward compatibility."""
    response = client.get("/api/prediction?location_id=chennai&lat=13.0827&lng=80.2707")
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "confidence" in data
    assert "overall_risk_level" in data["predictions"]


def test_trigger_warning_endpoint():
    """Verify POST /api/trigger-warning works and integrates alert dispatch."""
    response = client.post("/api/trigger-warning?district=Varanasi")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["district"] == "Varanasi"
    assert "broadcast_channels" in data
    assert "alert_id" in data


def test_device_registration_workflow():
    """Verify device register, list, and unregister endpoints."""
    # 1. Register device
    reg_payload = {
        "device_token": "fcm_test_token_999",
        "device_id": "phone_test_device",
        "lat": 26.04,
        "lng": 83.04,
        "platform": "android",
    }
    res_reg = client.post("/api/notifications/register", json=reg_payload)
    assert res_reg.status_code == 201
    reg_data = res_reg.json()
    assert reg_data["device_token"] == "fcm_test_token_999"
    assert len(reg_data["geohash"]) == 6

    # 2. Query devices
    res_list = client.get("/api/notifications/devices")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["registeredCount"] >= 1

    # 3. Unregister device
    res_unreg = client.post("/api/notifications/unregister", json={"device_token": "fcm_test_token_999"})
    assert res_unreg.status_code == 200
    assert res_unreg.json()["status"] == "SUCCESS"


def test_alert_evaluate_and_dispatch():
    """Verify POST /api/alerts/evaluate-and-dispatch endpoint."""
    payload = {
        "hazard_type": "THUNDERSTORM",
        "severity": "CRITICAL",
        "district": "Gorakhpur",
        "eta": "15 mins",
        "confidence": 95,
        "bbox": [26.0, 83.0, 27.0, 84.0],
    }
    response = client.post("/api/alerts/evaluate-and-dispatch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["district"] == "Gorakhpur"
    assert "alert_id" in data
    assert "elapsed_ms" in data


def test_events_status_and_publish():
    """Verify GET /api/events/status and POST /api/events/publish."""
    res_status = client.get("/api/events/status")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "ONLINE"

    pub_payload = {
        "event_type": "radar_scan_completed",
        "data": {"sweep": "0.5_deg", "reflectivityMax": 58},
    }
    res_pub = client.post("/api/events/publish", json=pub_payload)
    assert res_pub.status_code == 200
    data = res_pub.json()
    assert data["status"] == "PUBLISHED"
    assert data["eventType"] == "radar_scan_completed"


def test_etag_and_caching_headers():
    """Verify ETag header generation and 304 Not Modified validation."""
    response = client.get("/")
    assert response.status_code == 200
    etag = response.headers.get("ETag")
    assert etag is not None
    assert "Cache-Control" in response.headers

    # Send If-None-Match with matching ETag
    conditional_response = client.get("/", headers={"If-None-Match": etag})
    assert conditional_response.status_code == 304


def test_frontend_html_and_static_serving():
    """Verify frontend HTML dashboard and static assets are served properly for browsers."""
    # 1. Browser navigation to root /
    browser_res = client.get("/", headers={"Accept": "text/html,application/xhtml+xml"})
    assert browser_res.status_code == 200
    assert "<!DOCTYPE html>" in browser_res.text
    assert "ALERTORA AI" in browser_res.text

    # 2. Direct /index.html navigation
    index_res = client.get("/index.html")
    assert index_res.status_code == 200
    assert "<!DOCTYPE html>" in index_res.text

    # 3. Static asset serving
    js_res = client.get("/js/api.js")
    assert js_res.status_code == 200
    assert "AlertoraAPIService" in js_res.text


def test_service_worker_endpoint():
    """Verify /sw.js is served with application/javascript and Cache-Control headers."""
    sw_res = client.get("/sw.js")
    assert sw_res.status_code == 200
    assert "application/javascript" in sw_res.headers.get("content-type", "")
    assert "alertora-offline" in sw_res.text


def test_region_defensive_null_safety():
    """Verify locations endpoint maintains stability even when fixture structures are partial."""
    from backend.main import get_locations
    locs = get_locations()
    assert isinstance(locs, list)
    assert len(locs) == 1
    loc = locs[0]
    # Check that region label is never undefined
    assert loc["name"] != "undefined"
    assert loc["id"] != "undefined"
    assert loc["currentRisk"] != "undefined"
    assert loc["district"] != "undefined"
    assert loc["lat"] is not None
    assert loc["lng"] is not None


