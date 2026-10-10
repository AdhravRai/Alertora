"""
ALERTORA AI — Spatial Device Persistence Layer
Thread-safe device registration store with geohash indexing.
Includes PostGIS DDL schema definitions for cloud-scale deployment.
"""

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from backend.config import GEOHASH_DEFAULT_PRECISION
from backend.spatial.geohash import encode


# ==============================================================================
# PostGIS DDL Migration Schema (for Cloud / Production Database Deployments)
# ==============================================================================
POSTGIS_SCHEMA_DDL = """
-- PostGIS Extension & Spatial Device Registration Table
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS alertora_devices (
    device_token VARCHAR(255) PRIMARY KEY,
    device_id VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)) STORED,
    geohash_prefix VARCHAR(12) NOT NULL,
    platform VARCHAR(20) DEFAULT 'web',
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial GIST & Geohash B-tree Indexes for Sub-Millisecond Spatial Filtering
CREATE INDEX IF NOT EXISTS idx_alertora_devices_geom ON alertora_devices USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_alertora_devices_geohash ON alertora_devices (geohash_prefix);

-- Emergency Notification Audit Log
CREATE TABLE IF NOT EXISTS alertora_dispatches (
    dispatch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id VARCHAR(100) NOT NULL,
    hazard_type VARCHAR(50) NOT NULL,
    district VARCHAR(100),
    device_token VARCHAR(255) REFERENCES alertora_devices(device_token) ON DELETE CASCADE,
    delivery_status VARCHAR(30) NOT NULL,
    provider VARCHAR(20) DEFAULT 'fcm',
    dispatched_at TIMESTAMPTZ DEFAULT NOW(),
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_dispatches_alert_device ON alertora_dispatches (alert_id, device_token);
"""


class DeviceRegistrationRequest(BaseModel):
    device_token: str = Field(..., description="Unique FCM token or WebPush subscription identifier")
    device_id: Optional[str] = Field(None, description="Client hardware or browser session identifier")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    platform: Optional[str] = Field("web", description="Device platform (web, android, ios)")
    geohash: Optional[str] = Field(None, description="Optional pre-computed geohash")


class DeviceRecord(BaseModel):
    device_token: str
    device_id: Optional[str] = None
    lat: float
    lng: float
    geohash: str
    platform: str = "web"
    registered_at: str
    updated_at: str


class InMemoryDeviceStore:
    """
    Thread-safe in-memory device registry with geohash-indexed inverted bucket lookup.
    """

    def __init__(self, default_precision: int = GEOHASH_DEFAULT_PRECISION):
        self.default_precision = default_precision
        self._devices: Dict[str, DeviceRecord] = {}
        # Inverted index: geohash prefix -> Set of device_token
        self._geohash_index: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

    def register(self, req: DeviceRegistrationRequest) -> DeviceRecord:
        """Register or update a device's location and geohash index."""
        now = datetime.now(timezone.utc).isoformat()
        gh = req.geohash or encode(req.lat, req.lng, self.default_precision)

        with self._lock:
            # If device already registered, clean old geohash index
            old_record = self._devices.get(req.device_token)
            if old_record and old_record.geohash in self._geohash_index:
                self._geohash_index[old_record.geohash].discard(req.device_token)

            record = DeviceRecord(
                device_token=req.device_token,
                device_id=req.device_id,
                lat=req.lat,
                lng=req.lng,
                geohash=gh,
                platform=req.platform or "web",
                registered_at=old_record.registered_at if old_record else now,
                updated_at=now,
            )

            self._devices[req.device_token] = record

            # Add to inverted geohash index
            if gh not in self._geohash_index:
                self._geohash_index[gh] = set()
            self._geohash_index[gh].add(req.device_token)

            return record

    def unregister(self, device_token: str) -> bool:
        """Unregister a device."""
        with self._lock:
            record = self._devices.pop(device_token, None)
            if record:
                if record.geohash in self._geohash_index:
                    self._geohash_index[record.geohash].discard(device_token)
                return True
            return False

    def get_by_geohashes(self, geohashes: Set[str]) -> List[DeviceRecord]:
        """
        Retrieve all device records matching candidate geohashes or prefixes.
        """
        matching_tokens: Set[str] = set()

        with self._lock:
            for target_gh in geohashes:
                # Direct match
                if target_gh in self._geohash_index:
                    matching_tokens.update(self._geohash_index[target_gh])
                # Prefix matching for variable resolutions
                for indexed_gh, tokens in self._geohash_index.items():
                    if indexed_gh.startswith(target_gh) or target_gh.startswith(indexed_gh):
                        matching_tokens.update(tokens)

            return [self._devices[t] for t in matching_tokens if t in self._devices]

    def get_all(self) -> List[DeviceRecord]:
        with self._lock:
            return list(self._devices.values())

    def count(self) -> int:
        with self._lock:
            return len(self._devices)

    def clear(self) -> None:
        with self._lock:
            self._devices.clear()
            self._geohash_index.clear()


# Global Singleton Device Registry Store
device_store = InMemoryDeviceStore()
