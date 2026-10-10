"""
ALERTORA AI — Spatial Targeting & Verification Engine
Performs multi-stage geospatial targeting:
1. Candidate Geohash Discovery (precision 6 index)
2. Fine-grained Point-in-Polygon (Ray Casting) & Bounding Box inclusion verification
3. Deduplication Window enforcement (avoids user alert fatigue)
4. Temporal expiry policy verification
"""

import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from backend.config import (
    ALERT_DEDUPLICATION_WINDOW_MINUTES,
    ALERT_DEFAULT_EXPIRY_MINUTES,
    GEOHASH_DEFAULT_PRECISION,
)
from backend.spatial.geohash import geohashes_for_bbox
from backend.spatial.persistence import DeviceRecord, device_store


class AlertTargetZone(BaseModel):
    hazard_type: str = Field(..., description="Hazard type, e.g. THUNDERSTORM, LIGHTNING, CLOUDBURST, HAIL")
    severity: str = Field(..., description="Severity level, e.g. CRITICAL, HIGH, MODERATE")
    district: Optional[str] = Field(None, description="Administrative district name")
    bbox: Optional[Tuple[float, float, float, float]] = Field(
        None, description="[min_lat, min_lon, max_lat, max_lon]"
    )
    polygon: Optional[List[Tuple[float, float]]] = Field(
        None, description="Polygon vertices as list of [lat, lon]"
    )
    issued_at: Optional[str] = Field(None, description="ISO timestamp of issuance")
    valid_until: Optional[str] = Field(None, description="ISO timestamp of expiry")
    eta_minutes: Optional[int] = Field(30, description="Estimated time of arrival in minutes")


def point_in_bbox(lat: float, lon: float, bbox: Tuple[float, float, float, float]) -> bool:
    """Check if (lat, lon) is strictly within bounding box (min_lat, min_lon, max_lat, max_lon)."""
    min_lat, min_lon, max_lat, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def point_in_polygon(lat: float, lon: float, polygon: List[Tuple[float, float]]) -> bool:
    """
    Standard Ray-casting algorithm to test point-in-polygon inclusion.
    Vertices expected as list of (lat, lon).
    """
    if len(polygon) < 3:
        return False

    inside = False
    n = len(polygon)
    p1_lat, p1_lon = polygon[0]

    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if (p1_lat > lat) != (p2_lat > lat):
            x_inters = (lat - p1_lat) * (p2_lon - p1_lon) / (p2_lat - p1_lat) + p1_lon
            if lon < x_inters:
                inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon

    return inside


class SpatialTargetingEngine:
    """
    Coordinates spatial geohash discovery, geometric verification,
    alert deduplication, and expiration filtering.
    """

    def __init__(
        self,
        dedup_window_minutes: int = ALERT_DEDUPLICATION_WINDOW_MINUTES,
        default_expiry_minutes: int = ALERT_DEFAULT_EXPIRY_MINUTES,
    ):
        self.dedup_window_seconds = dedup_window_minutes * 60
        self.default_expiry_seconds = default_expiry_minutes * 60
        # Dispatched history: (device_token, hazard_type) -> float(epoch_seconds)
        self._dispatch_history: Dict[Tuple[str, str], float] = {}

    def get_candidate_geohashes(self, zone: AlertTargetZone, precision: int = GEOHASH_DEFAULT_PRECISION) -> Set[str]:
        """
        Derive bounding box and generate candidate geohashes for the zone.
        """
        bbox = zone.bbox

        if not bbox and zone.polygon:
            lats = [pt[0] for pt in zone.polygon]
            lons = [pt[1] for pt in zone.polygon]
            bbox = (min(lats), min(lons), max(lats), max(lons))

        if not bbox:
            return set()

        return geohashes_for_bbox(bbox[0], bbox[1], bbox[2], bbox[3], precision=precision)

    def is_alert_expired(self, zone: AlertTargetZone) -> bool:
        """Verify whether the alert has exceeded its valid timeframe."""
        now = time.time()

        if zone.valid_until:
            try:
                dt = datetime.fromisoformat(zone.valid_until.replace("Z", "+00:00"))
                return now > dt.timestamp()
            except Exception:
                pass

        if zone.issued_at:
            try:
                dt = datetime.fromisoformat(zone.issued_at.replace("Z", "+00:00"))
                if now > (dt.timestamp() + self.default_expiry_seconds):
                    return True
            except Exception:
                pass

        return False

    def is_duplicate(self, device_token: str, hazard_type: str) -> bool:
        """
        Check if an alert for this hazard_type was already dispatched to device within window.
        """
        key = (device_token, hazard_type.upper())
        last_sent = self._dispatch_history.get(key)
        if last_sent is not None:
            if (time.time() - last_sent) < self.dedup_window_seconds:
                return True
        return False

    def record_dispatch(self, device_token: str, hazard_type: str) -> None:
        """Record dispatch timestamp for deduplication tracking."""
        key = (device_token, hazard_type.upper())
        self._dispatch_history[key] = time.time()

    def clear_history(self) -> None:
        """Reset deduplication history (useful for testing)."""
        self._dispatch_history.clear()

    def target_devices(
        self,
        zone: AlertTargetZone,
        store: Optional[any] = None,
    ) -> Tuple[List[DeviceRecord], List[str]]:
        """
        Executes end-to-end targeting pipeline:
        1. Expiry check
        2. Geohash candidate retrieval
        3. Geometric point verification (polygon / bbox)
        4. Deduplication suppression
        Returns:
            (targeted_devices, suppressed_duplicate_tokens)
        """
        if self.is_alert_expired(zone):
            return ([], [])

        active_store = store or device_store

        # 1. Candidate geohashes
        candidate_geohashes = self.get_candidate_geohashes(zone)
        candidate_devices = active_store.get_by_geohashes(candidate_geohashes)

        targeted: List[DeviceRecord] = []
        suppressed_tokens: List[str] = []

        # 2. Geometric spatial verification
        for device in candidate_devices:
            is_inside = False

            if zone.polygon:
                is_inside = point_in_polygon(device.lat, device.lng, zone.polygon)
            elif zone.bbox:
                is_inside = point_in_bbox(device.lat, device.lng, zone.bbox)
            else:
                # If neither bbox nor polygon provided, fallback to candidate match
                is_inside = True

            if is_inside:
                # 3. Deduplication check
                if self.is_duplicate(device.device_token, zone.hazard_type):
                    suppressed_tokens.append(device.device_token)
                else:
                    targeted.append(device)

        return (targeted, suppressed_tokens)


# Global singleton targeting engine instance
targeting_engine = SpatialTargetingEngine()
