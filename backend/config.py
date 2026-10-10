"""
ALERTORA AI — Backend Configuration
Environment configuration with safe defaults for local development.
"""

import os
from pathlib import Path
from typing import List, Optional

# Project Paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PERSON_B_OUTPUT_DIR = PROJECT_ROOT / "person-b" / "output"

# SSE & Real-Time Event Settings
SSE_HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv("SSE_HEARTBEAT_INTERVAL_SECONDS", "15"))
SSE_CLIENT_QUEUE_MAX_SIZE: int = int(os.getenv("SSE_CLIENT_QUEUE_MAX_SIZE", "50"))
SSE_RING_BUFFER_SIZE: int = int(os.getenv("SSE_RING_BUFFER_SIZE", "100"))

# Geohash & Spatial Targeting Settings
GEOHASH_DEFAULT_PRECISION: int = int(os.getenv("GEOHASH_DEFAULT_PRECISION", "6"))
ALERT_DEDUPLICATION_WINDOW_MINUTES: int = int(os.getenv("ALERT_DEDUPLICATION_WINDOW_MINUTES", "30"))
ALERT_DEFAULT_EXPIRY_MINUTES: int = int(os.getenv("ALERT_DEFAULT_EXPIRY_MINUTES", "120"))

# Firebase Cloud Messaging (FCM) Settings
FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH", None)
FIREBASE_PROJECT_ID: Optional[str] = os.getenv("FIREBASE_PROJECT_ID", None)
NOTIFICATION_PROVIDER: str = os.getenv("NOTIFICATION_PROVIDER", "fcm")

# HTTP & Caching Settings
ENABLE_CACHE_HEADERS: bool = os.getenv("ENABLE_CACHE_HEADERS", "true").lower() in ("1", "true", "yes")
CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")

# IMDAA Validation Bounds
IMDAA_MIN_LAT: float = 25.08
IMDAA_MAX_LAT: float = 27.00
IMDAA_MIN_LON: float = 82.08
IMDAA_MAX_LON: float = 84.00
