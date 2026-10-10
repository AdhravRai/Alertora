"""
ALERTORA AI — Real-Time Event Bus & Broadcaster
Provides in-memory publish/subscribe event broadcasting for Server-Sent Events (SSE).
Features:
- Bounded client queues (prevents uncontrolled memory growth)
- Event ID sequencing & Last-Event-ID replay from an in-memory ring buffer
- Heartbeat generation to maintain active connection keep-alive
- Graceful client disconnect cleanup
"""

import asyncio
import json
import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional
from uuid import uuid4

from backend.config import (
    SSE_CLIENT_QUEUE_MAX_SIZE,
    SSE_HEARTBEAT_INTERVAL_SECONDS,
    SSE_RING_BUFFER_SIZE,
)

logger = logging.getLogger("alertora.event_bus")


class RealTimeEvent:
    """Represents a discrete real-time event to be streamed to clients."""

    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id or f"evt_{int(time.time() * 1000)}_{uuid4().hex[:6]}"
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def format_sse(self) -> str:
        """
        Format event per the standard SSE text/event-stream specifications:
        id: <event_id>
        event: <event_type>
        data: <json_string>

        """
        payload = {
            **self.data,
            "_metadata": {
                "eventId": self.event_id,
                "eventType": self.event_type,
                "timestamp": self.timestamp,
            },
        }
        json_data = json.dumps(payload, separators=(",", ":"))
        return f"id: {self.event_id}\nevent: {self.event_type}\ndata: {json_data}\n\n"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.event_id,
            "event": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class EventBroadcaster:
    """
    Central event distributor managing client subscription queues and event history.
    """

    def __init__(
        self,
        ring_buffer_size: int = SSE_RING_BUFFER_SIZE,
        queue_max_size: int = SSE_CLIENT_QUEUE_MAX_SIZE,
    ):
        self._clients: Dict[str, asyncio.Queue] = {}
        self._history: Deque[RealTimeEvent] = deque(maxlen=ring_buffer_size)
        self._queue_max_size = queue_max_size
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def register_client(
        self,
        client_id: str,
        last_event_id: Optional[str] = None,
    ) -> asyncio.Queue:
        """
        Register a new client listener and backfill missed events if last_event_id is given.
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=self._queue_max_size)

        async with self._lock:
            self._clients[client_id] = queue

            # If Last-Event-ID provided, replay events from ring buffer after that ID
            if last_event_id:
                replaying = False
                for event in list(self._history):
                    if replaying:
                        try:
                            queue.put_nowait(event)
                        except asyncio.QueueFull:
                            break
                    elif event.event_id == last_event_id:
                        replaying = True

        logger.info(
            f"[EventBus] Client connected: {client_id} (active: {len(self._clients)}, replayed: {queue.qsize()})"
        )
        return queue

    async def remove_client(self, client_id: str) -> None:
        """Remove a client from the active subscription set."""
        async with self._lock:
            if client_id in self._clients:
                del self._clients[client_id]
                logger.info(
                    f"[EventBus] Client disconnected: {client_id} (active: {len(self._clients)})"
                )

    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> RealTimeEvent:
        """
        Publish an event to all connected clients and store in ring buffer.
        Non-blocking drop-oldest behavior on individual slow queues.
        """
        event = RealTimeEvent(
            event_type=event_type,
            data=data,
            event_id=event_id,
        )

        self._history.append(event)

        # Distribute to all client queues
        disconnected_clients: List[str] = []
        for client_id, queue in list(self._clients.items()):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Queue full: drop oldest event to avoid memory leak and append new event
                try:
                    _ = queue.get_nowait()
                    queue.put_nowait(event)
                except Exception:
                    disconnected_clients.append(client_id)

        # Cleanup failed clients
        for cid in disconnected_clients:
            if cid in self._clients:
                del self._clients[cid]

        logger.debug(
            f"[EventBus] Published '{event_type}' ({event.event_id}) to {len(self._clients)} clients"
        )
        return event

    async def start_heartbeat(
        self,
        interval_seconds: int = SSE_HEARTBEAT_INTERVAL_SECONDS,
    ) -> None:
        """Start periodic heartbeat task to keep connections alive."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            return

        async def _heartbeat_loop():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    if self._clients:
                        self.publish(
                            event_type="heartbeat",
                            data={
                                "serverTime": datetime.now(timezone.utc).isoformat(),
                                "activeClients": len(self._clients),
                            },
                        )
                except asyncio.CancelledError:
                    break
                except Exception as ex:
                    logger.warning(f"[EventBus] Heartbeat error: {ex}")

        self._heartbeat_task = asyncio.create_task(_heartbeat_loop())

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat loop task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None


# Global Singleton Event Broadcaster Instance
broadcaster = EventBroadcaster()
