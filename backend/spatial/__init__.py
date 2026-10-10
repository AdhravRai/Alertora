"""
ALERTORA AI — Spatial Services & Geohash Engine
"""

from backend.spatial.geohash import (
    adjacent,
    decode,
    decode_bbox,
    encode,
    geohashes_for_bbox,
    neighbors,
)
from backend.spatial.persistence import (
    DeviceRecord,
    DeviceRegistrationRequest,
    InMemoryDeviceStore,
    POSTGIS_SCHEMA_DDL,
    device_store,
)
from backend.spatial.targeting import (
    AlertTargetZone,
    SpatialTargetingEngine,
    point_in_bbox,
    point_in_polygon,
    targeting_engine,
)

__all__ = [
    "encode",
    "decode",
    "decode_bbox",
    "adjacent",
    "neighbors",
    "geohashes_for_bbox",
    "DeviceRecord",
    "DeviceRegistrationRequest",
    "InMemoryDeviceStore",
    "POSTGIS_SCHEMA_DDL",
    "device_store",
    "AlertTargetZone",
    "SpatialTargetingEngine",
    "point_in_bbox",
    "point_in_polygon",
    "targeting_engine",
]
