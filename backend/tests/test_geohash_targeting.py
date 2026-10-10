"""
Unit and integration tests for Geohash encoding and Spatial Targeting Engine.
Tests:
- Base-32 Geohash encode/decode roundtrip
- Neighbors calculation
- Point-in-polygon & bounding-box verification
- Device registration and inverted geohash index
- Candidate geohash filtering
- Deduplication suppression
- Expiry handling
"""

import time
from datetime import datetime, timezone, timedelta
import pytest

from backend.spatial.geohash import (
    adjacent,
    decode,
    decode_bbox,
    encode,
    geohashes_for_bbox,
    neighbors,
)
from backend.spatial.persistence import (
    DeviceRegistrationRequest,
    InMemoryDeviceStore,
)
from backend.spatial.targeting import (
    AlertTargetZone,
    SpatialTargetingEngine,
    point_in_bbox,
    point_in_polygon,
)


def test_geohash_encode_decode():
    """Verify coordinate round-trip encoding within precision error tolerance."""
    lat, lon = 26.04, 83.04  # Center of IMDAA domain
    gh = encode(lat, lon, precision=6)
    assert len(gh) == 6
    assert isinstance(gh, str)

    dec_lat, dec_lon = decode(gh)
    assert pytest.approx(dec_lat, abs=0.01) == lat
    assert pytest.approx(dec_lon, abs=0.01) == lon


def test_geohash_neighbors():
    """Verify 8 cardinal and diagonal neighbors generation."""
    gh = encode(26.04, 83.04, precision=6)
    adj = neighbors(gh)
    assert len(adj) == 8
    for direction in ("n", "s", "e", "w", "ne", "nw", "se", "sw"):
        assert direction in adj
        assert len(adj[direction]) == 6
        assert adj[direction] != gh


def test_geohashes_for_bbox():
    """Verify geohashes generated for bounding box covers target corners."""
    min_lat, min_lon, max_lat, max_lon = 25.5, 82.5, 25.6, 82.6
    hashes = geohashes_for_bbox(min_lat, min_lon, max_lat, max_lon, precision=6)
    assert len(hashes) > 0

    # Corners must be included
    c1 = encode(min_lat, min_lon, precision=6)
    c2 = encode(max_lat, max_lon, precision=6)
    assert c1 in hashes
    assert c2 in hashes


def test_point_in_polygon():
    """Verify ray casting point-in-polygon logic."""
    triangle = [(0.0, 0.0), (0.0, 10.0), (10.0, 5.0)]

    # Point clearly inside
    assert point_in_polygon(3.0, 5.0, triangle) is True
    # Point clearly outside
    assert point_in_polygon(12.0, 5.0, triangle) is False
    assert point_in_polygon(-1.0, 5.0, triangle) is False


def test_device_store_registration_and_lookup():
    """Verify device registration, geohash indexing, and spatial retrieval."""
    store = InMemoryDeviceStore(default_precision=6)

    # Register Device A in Varanasi (lat 25.3176, lon 82.9739)
    store.register(DeviceRegistrationRequest(
        device_token="token_vns_1",
        lat=25.3176,
        lng=82.9739,
    ))

    # Register Device B in Gorakhpur (lat 26.7606, lon 83.3732)
    store.register(DeviceRegistrationRequest(
        device_token="token_gkp_1",
        lat=26.7606,
        lng=83.3732,
    ))

    assert store.count() == 2

    # Query for Varanasi geohash
    vns_gh = encode(25.3176, 82.9739, precision=6)
    matches = store.get_by_geohashes({vns_gh})
    assert len(matches) == 1
    assert matches[0].device_token == "token_vns_1"

    # Query for Gorakhpur geohash
    gkp_gh = encode(26.7606, 83.3732, precision=6)
    matches_gkp = store.get_by_geohashes({gkp_gh})
    assert len(matches_gkp) == 1
    assert matches_gkp[0].device_token == "token_gkp_1"


def test_spatial_targeting_pipeline():
    """Verify full targeting: candidates -> geometric verification -> targeted list."""
    store = InMemoryDeviceStore(default_precision=6)
    engine = SpatialTargetingEngine(dedup_window_minutes=30)

    # Register 3 devices: 1 inside bbox, 2 outside
    store.register(DeviceRegistrationRequest(device_token="inside_dev", lat=26.00, lng=83.00))
    store.register(DeviceRegistrationRequest(device_token="outside_dev_1", lat=25.00, lng=82.00))
    store.register(DeviceRegistrationRequest(device_token="outside_dev_2", lat=28.00, lng=84.00))

    zone = AlertTargetZone(
        hazard_type="LIGHTNING",
        severity="CRITICAL",
        district="Azamgarh",
        bbox=(25.90, 82.90, 26.10, 83.10),
    )

    targeted, suppressed = engine.target_devices(zone, store=store)
    targeted_tokens = [d.device_token for d in targeted]

    assert "inside_dev" in targeted_tokens
    assert "outside_dev_1" not in targeted_tokens
    assert "outside_dev_2" not in targeted_tokens
    assert len(suppressed) == 0


def test_deduplication_suppression():
    """Verify repeated alerts for the same hazard are suppressed within the dedup window."""
    store = InMemoryDeviceStore(default_precision=6)
    engine = SpatialTargetingEngine(dedup_window_minutes=15)

    store.register(DeviceRegistrationRequest(device_token="dev_duplicate", lat=26.00, lng=83.00))

    zone = AlertTargetZone(
        hazard_type="THUNDERSTORM",
        severity="HIGH",
        bbox=(25.90, 82.90, 26.10, 83.10),
    )

    # First dispatch: target device
    targeted, suppressed = engine.target_devices(zone, store=store)
    assert len(targeted) == 1
    assert len(suppressed) == 0

    # Record dispatch
    engine.record_dispatch("dev_duplicate", "THUNDERSTORM")

    # Second dispatch within 15 min: should be suppressed
    targeted_2, suppressed_2 = engine.target_devices(zone, store=store)
    assert len(targeted_2) == 0
    assert "dev_duplicate" in suppressed_2


def test_expired_alert_rejection():
    """Verify expired alerts are rejected and target zero devices."""
    store = InMemoryDeviceStore(default_precision=6)
    engine = SpatialTargetingEngine()

    store.register(DeviceRegistrationRequest(device_token="dev_test", lat=26.00, lng=83.00))

    past_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    expired_zone = AlertTargetZone(
        hazard_type="CLOUDBURST",
        severity="CRITICAL",
        bbox=(25.90, 82.90, 26.10, 83.10),
        valid_until=past_time,
    )

    targeted, suppressed = engine.target_devices(expired_zone, store=store)
    assert len(targeted) == 0
    assert len(suppressed) == 0
