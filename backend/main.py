"""
ALERTORA AI — FastAPI Server Engine
Provides RESTful API endpoints, real-time Server-Sent Events (SSE),
geohash-targeted emergency alert dispatch, and EOC command integration.
"""

import hashlib
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.ai_engine import ai_engine
from backend.models import AlertItem, EOCDistrictRow, LocationProfile
from backend.notifications.router import router as notification_router
from backend.notifications.service import AlertDispatchPayload, notification_service
from backend.real_time import broadcaster, pipeline_watcher
from backend.real_time.sse_router import router as sse_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("alertora.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for background tasks: SSE heartbeats and pipeline file watcher."""
    logger.info("[Lifecycle] Starting Alertora background services...")
    await broadcaster.start_heartbeat()
    await pipeline_watcher.start()
    yield
    logger.info("[Lifecycle] Shutting down Alertora background services...")
    await pipeline_watcher.stop()
    await broadcaster.stop_heartbeat()


app = FastAPI(
    title="ALERTORA AI — Severe Weather Nowcasting API",
    description="Backend API with Real-Time SSE and Geohash Alert Dispatch for Smart India Hackathon Problem SIH26084",
    version="2.5.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTP Caching & ETag Middleware for Edge CDN / Browser Optimization
class CacheAndETagMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Never touch real-time event streaming endpoints
        if path.startswith("/api/events/stream"):
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-cache, no-transform"
            return response

        response: Response = await call_next(request)

        # Apply Caching & ETag on successful GET requests
        if request.method == "GET" and response.status_code == 200:
            if not response.headers.get("Cache-Control"):
                response.headers["Cache-Control"] = "public, max-age=60, must-revalidate"

            # Buffer response chunks to calculate MD5 ETag
            body_chunks = [chunk async for chunk in response.body_iterator]
            body_bytes = b"".join(body_chunks)

            etag = f'"{hashlib.md5(body_bytes).hexdigest()}"'
            response.headers["ETag"] = etag

            if_none_match = request.headers.get("If-None-Match")
            if if_none_match and if_none_match == etag:
                return Response(status_code=304, headers=dict(response.headers))

            async def stream_body():
                yield body_bytes

            response.body_iterator = stream_body()

        return response


app.add_middleware(CacheAndETagMiddleware)

# Mount Routers
app.include_router(sse_router)
app.include_router(notification_router)


# Existing Base REST Endpoints (Preserved for full backward compatibility)
@app.get("/")
def read_root():
    return {
        "app": "ALERTORA AI",
        "tagline": "Predict Early. Prepare Smart. Save Lives.",
        "status": "ONLINE",
        "sih_problem": "SIH26084",
        "version": "2.5.0",
        "features": [
            "Server-Sent Events (SSE) Real-Time Streaming",
            "Precision-6 Geohash Spatial Emergency Targeting",
            "FCM Push Delivery with Fail-Safe Dry-Run Mode",
            "Edge CDN Caching & ETag Support",
        ],
    }


@app.get("/api/system-status")
def get_system_status():
    return {
        "status": "AI SYSTEM ONLINE",
        "confidence": 91,
        "active_models": ["ConvLSTM-Nowcast-v2", "U-Net-Reflectivity-v4", "LightningSurge-XGB"],
        "sensors": {
            "radar": "ONLINE",
            "satellite": "ONLINE",
            "lightning": "ONLINE",
            "aws": "ONLINE",
        },
        "sse": {
            "status": "STREAMING_ACTIVE",
            "connectedClients": broadcaster.client_count,
        },
    }


@app.get("/api/prediction")
def get_prediction(location_id: str = "chennai", lat: float = 13.0827, lng: float = 80.2707):
    return ai_engine.predict_nowcast(lat=lat, lng=lng, location_id=location_id)


@app.post("/api/trigger-warning")
async def trigger_warning(district: str):
    """
    Triggers emergency warning dispatch.
    Preserves existing contract while executing spatial evaluation and real-time SSE broadcast.
    """
    dispatch_res = await notification_service.evaluate_and_dispatch(
        AlertDispatchPayload(
            hazard_type="THUNDERSTORM",
            severity="CRITICAL",
            title=f"CRITICAL WARNING: Severe Thunderstorm & Lightning Approaching {district}",
            district=district,
            eta="15-20 mins",
            confidence=94,
            summary=f"Automated convective early-warning triggered for {district} sector. Severe lightning strike probability >80%.",
            action="Seek immediate enclosed shelter. Avoid open fields, metal structures, and trees.",
        )
    )

    return {
        "status": "SUCCESS",
        "district": district,
        "alert_id": dispatch_res.alert_id,
        "message": f"Automated Emergency Cell Broadcast Warning dispatched to {district} sector.",
        "broadcast_channels": dispatch_res.broadcast_channels,
        "targeted_devices": dispatch_res.targeted_devices,
        "dispatched_count": dispatch_res.dispatched_count,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
