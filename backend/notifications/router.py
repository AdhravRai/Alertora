"""
ALERTORA AI — Notification & Emergency Alert FastAPI Router
Exposes:
- POST /api/notifications/register: Device location registration with geohash indexing
- POST /api/notifications/unregister: Device unregistration
- GET /api/notifications/devices: Device registry status
- POST /api/alerts/evaluate-and-dispatch: Geohash targeted alert dispatch
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.notifications.service import (
    AlertDispatchPayload,
    AlertDispatchResponse,
    notification_service,
)
from backend.spatial.persistence import (
    DeviceRecord,
    DeviceRegistrationRequest,
    device_store,
)

logger = logging.getLogger("alertora.notifications.router")

router = APIRouter(prefix="/api", tags=["Notifications & Targeting"])


@router.post(
    "/notifications/register",
    summary="Register Device Location for Geohash Targeting",
    response_model=DeviceRecord,
    status_code=status.HTTP_201_CREATED,
)
async def register_device(payload: DeviceRegistrationRequest):
    """
    Registers a client device token and spatial coordinate.
    Calculates precision 6 geohash and adds to the inverted spatial lookup index.
    """
    try:
        record = device_store.register(payload)
        logger.info(f"[Registry] Device registered: token={payload.device_token[:10]}... geohash={record.geohash}")
        return record
    except Exception as ex:
        logger.error(f"[Registry] Device registration failed: {ex}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(ex)}")


class UnregisterRequest(BaseModel):
    device_token: str = Field(..., description="Device token to unregister")


@router.post(
    "/notifications/unregister",
    summary="Unregister Device",
    status_code=status.HTTP_200_OK,
)
async def unregister_device(payload: UnregisterRequest):
    """Removes a device token from the active registry."""
    success = device_store.unregister(payload.device_token)
    return {"status": "SUCCESS" if success else "NOT_FOUND", "device_token": payload.device_token}


@router.get(
    "/notifications/devices",
    summary="Device Registry Summary",
    status_code=status.HTTP_200_OK,
)
async def get_device_summary():
    """Returns active registered device count and sample listings."""
    devices = device_store.get_all()
    return {
        "status": "ONLINE",
        "registeredCount": len(devices),
        "devices": [d.model_dump() for d in devices[:50]],
    }


@router.post(
    "/alerts/evaluate-and-dispatch",
    summary="Evaluate Geohash Targeting & Dispatch Emergency Alert",
    response_model=AlertDispatchResponse,
    status_code=status.HTTP_200_OK,
)
async def dispatch_alert(payload: AlertDispatchPayload):
    """
    Evaluates geospatial candidate geohashes, verifies polygon/bbox inclusion,
    suppresses recent duplicate alerts, sends push notifications, and broadcasts
    the alert to all connected SSE clients.
    """
    try:
        response = await notification_service.evaluate_and_dispatch(payload)
        return response
    except Exception as ex:
        logger.error(f"[AlertDispatch] Dispatch failed: {ex}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Alert dispatch failed: {str(ex)}")
