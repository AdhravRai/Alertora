"""
ALERTORA AI — Server-Sent Events (SSE) FastAPI Router
Exposes:
- GET /api/events/stream: Real-time SSE event stream for frontend dashboard.
- POST /api/events/publish: Broadcast an event to connected clients.
- GET /api/events/status: Monitor active SSE clients and event metrics.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.real_time.event_bus import broadcaster

logger = logging.getLogger("alertora.sse")

router = APIRouter(prefix="/api/events", tags=["Real-Time Events"])


class PublishEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of event, e.g. forecast_updated, risk_zones_updated")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload dictionary")
    event_id: Optional[str] = Field(None, description="Optional custom event ID")


@router.get(
    "/stream",
    summary="Server-Sent Events Stream",
    description="Stream real-time convective nowcast updates, risk zones, alerts, and heartbeats to clients.",
    response_class=StreamingResponse,
)
async def sse_event_stream(
    request: Request,
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
):
    """
    Long-lived HTTP connection streaming SSE events.
    Handles disconnection cleanly and prevents unconstrained memory retention.
    """
    client_id = f"client_{uuid4().hex[:8]}"
    queue = await broadcaster.register_client(client_id, last_event_id=last_event_id)

    async def event_generator():
        try:
            # Yield initial connection confirmation event
            initial_event = broadcaster.publish(
                event_type="system_status_updated",
                data={
                    "status": "CONNECTED",
                    "clientId": client_id,
                    "message": "Connected to Alertora Real-Time Convective Early-Warning Stream",
                },
            )
            # Send initial event directly to this client
            yield initial_event.format_sse()

            while True:
                # Check if client has disconnected
                if await request.is_disconnected():
                    logger.info(f"[SSE] Client {client_id} disconnected detected via request.")
                    break

                try:
                    # Wait for next event with a 15-second timeout
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield event.format_sse()
                except asyncio.TimeoutError:
                    # Send a comment keep-alive ping if no event arrived in timeout window
                    yield ": keep-alive ping\n\n"
                except asyncio.CancelledError:
                    logger.info(f"[SSE] Stream cancelled for client {client_id}")
                    break

        except Exception as ex:
            logger.warning(f"[SSE] Exception in stream for {client_id}: {ex}")
        finally:
            await broadcaster.remove_client(client_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.post(
    "/publish",
    summary="Publish Event to SSE Stream",
    status_code=status.HTTP_200_OK,
)
async def publish_event(body: PublishEventRequest):
    """
    Publish an event into the real-time stream.
    Used by pipeline jobs, spatial analysis updates, and alert triggers.
    """
    event = broadcaster.publish(
        event_type=body.event_type,
        data=body.data,
        event_id=body.event_id,
    )
    return {
        "status": "PUBLISHED",
        "eventId": event.event_id,
        "eventType": event.event_type,
        "activeClients": broadcaster.client_count,
        "timestamp": event.timestamp,
    }


@router.get(
    "/status",
    summary="Real-Time Event Stream Status",
    status_code=status.HTTP_200_OK,
)
async def stream_status():
    """Returns active connection count and broadcaster health status."""
    return {
        "status": "ONLINE",
        "activeClients": broadcaster.client_count,
        "broadcaster": "FastAPI SSE Streaming Broadcaster",
    }
