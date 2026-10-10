"""
ALERTORA AI — Emergency Notification Dispatch Service
Orchestrates geospatial targeting, deduplication, push notification dispatch,
and real-time SSE alert event publication.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field

from backend.notifications.fcm_provider import FCMNotificationProvider, NotificationDispatchResult, fcm_provider
from backend.real_time.event_bus import broadcaster
from backend.spatial.persistence import InMemoryDeviceStore, device_store
from backend.spatial.targeting import AlertTargetZone, SpatialTargetingEngine, targeting_engine

logger = logging.getLogger("alertora.notifications.service")


class AlertDispatchPayload(BaseModel):
    hazard_type: str = Field("THUNDERSTORM", description="Severe hazard type (THUNDERSTORM, LIGHTNING, CLOUDBURST, HAIL)")
    severity: str = Field("HIGH", description="Severity category (CRITICAL, HIGH, MODERATE, LOW)")
    title: Optional[str] = Field(None, description="Alert banner title")
    district: str = Field("Chennai Metropolis", description="Target district or sector")
    eta: str = Field("25 mins", description="Estimated arrival time string")
    confidence: int = Field(88, ge=0, le=100, description="Model confidence score (0-100)")
    summary: Optional[str] = Field(None, description="Detailed hazard warning summary")
    action: Optional[str] = Field(None, description="Mandated safety precaution")
    bbox: Optional[Tuple[float, float, float, float]] = Field(None, description="Spatial bounding box [min_lat, min_lon, max_lat, max_lon]")
    polygon: Optional[List[Tuple[float, float]]] = Field(None, description="Polygon vertices list")
    valid_until: Optional[str] = Field(None, description="ISO timestamp for alert validity")


class AlertDispatchResponse(BaseModel):
    alert_id: str
    status: str
    district: str
    hazard_type: str
    severity: str
    targeted_devices: int
    dispatched_count: int
    suppressed_duplicates: int
    simulated: bool
    broadcast_channels: List[str]
    elapsed_ms: float
    timestamp: str


class NotificationService:
    """
    Coordinates emergency warning distribution across geohash targeting and push providers.
    """

    def __init__(
        self,
        provider: Optional[FCMNotificationProvider] = None,
        engine: Optional[SpatialTargetingEngine] = None,
        store: Optional[InMemoryDeviceStore] = None,
    ):
        self.provider = provider or fcm_provider
        self.engine = engine or targeting_engine
        self.store = store or device_store

    async def evaluate_and_dispatch(self, payload: AlertDispatchPayload) -> AlertDispatchResponse:
        start_time = time.time()
        alert_id = f"ALT-{int(start_time * 1000)}-{uuid4().hex[:4].upper()}"

        title = payload.title or f"{payload.severity} ALERT: {payload.hazard_type} Approaching {payload.district}"
        body = payload.summary or f"High-confidence {payload.hazard_type.lower()} nowcast. ETA: {payload.eta}. Seek shelter."

        # 1. Build Spatial Target Zone
        zone = AlertTargetZone(
            hazard_type=payload.hazard_type,
            severity=payload.severity,
            district=payload.district,
            bbox=payload.bbox,
            polygon=payload.polygon,
            valid_until=payload.valid_until,
            issued_at=datetime.now(timezone.utc).isoformat(),
        )

        # 2. Identify Targeted Devices & Suppress Duplicates
        targeted_devices, suppressed_tokens = self.engine.target_devices(zone, store=self.store)
        tokens_to_send = [d.device_token for d in targeted_devices]

        # 3. Dispatch Push Notifications via Provider
        dispatch_result: NotificationDispatchResult
        if tokens_to_send:
            dispatch_result = await self.provider.send_multicast(
                tokens=tokens_to_send,
                title=title,
                body=body,
                data={
                    "alert_id": alert_id,
                    "hazard_type": payload.hazard_type,
                    "severity": payload.severity,
                    "district": payload.district,
                    "eta": payload.eta,
                    "action": payload.action or "Seek indoor shelter immediately",
                },
            )
            # Record dispatches for deduplication
            for token in dispatch_result.tokens_sent:
                self.engine.record_dispatch(token, payload.hazard_type)
        else:
            dispatch_result = NotificationDispatchResult(
                success_count=0,
                failure_count=0,
                simulated=not self.provider.is_configured,
            )

        # 4. Broadcast real-time alert_created event to SSE stream
        alert_event_data = {
            "id": alert_id,
            "severity": payload.severity,
            "title": title,
            "location": payload.district,
            "hazardTypes": [payload.hazard_type],
            "eta": payload.eta,
            "confidence": payload.confidence,
            "summary": body,
            "action": payload.action or "Seek immediate indoor shelter; disconnect sensitive electronics.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channels": ["Cell Broadcast", "State Siren Grid", "Mobile Push"],
        }
        broadcaster.publish(event_type="alert_created", data=alert_event_data)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return AlertDispatchResponse(
            alert_id=alert_id,
            status="SUCCESS",
            district=payload.district,
            hazard_type=payload.hazard_type,
            severity=payload.severity,
            targeted_devices=len(targeted_devices),
            dispatched_count=dispatch_result.success_count,
            suppressed_duplicates=len(suppressed_tokens),
            simulated=dispatch_result.simulated,
            broadcast_channels=["Cell Broadcast", "State Siren Grid", "Mobile Push"],
            elapsed_ms=elapsed_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# Global singleton notification service
notification_service = NotificationService()
