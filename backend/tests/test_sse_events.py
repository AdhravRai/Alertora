"""
Unit and integration tests for Real-Time Event Bus and SSE streaming.
Tests:
- SSE event formatting
- Bounded client queue drop behavior
- Last-Event-ID ring buffer replay
- Client disconnect cleanup
- Heartbeat dispatch
"""

import asyncio
import json
import pytest

from backend.real_time.event_bus import EventBroadcaster, RealTimeEvent


def test_real_time_event_sse_formatting():
    """Verify event complies with text/event-stream specification."""
    event = RealTimeEvent(
        event_type="forecast_updated",
        data={"leadHorizon": 3, "status": "CONVECTIVE_STORM_DETECTED"},
        event_id="evt_test_1001",
    )
    sse_text = event.format_sse()

    assert sse_text.startswith("id: evt_test_1001\n")
    assert "event: forecast_updated\n" in sse_text
    assert sse_text.endswith("\n\n")

    # Extract JSON line
    data_lines = [line for line in sse_text.splitlines() if line.startswith("data: ")]
    assert len(data_lines) == 1
    data_payload = json.loads(data_lines[0].replace("data: ", ""))
    assert data_payload["leadHorizon"] == 3
    assert data_payload["_metadata"]["eventId"] == "evt_test_1001"


def test_broadcaster_register_and_publish():
    """Verify broadcaster registers clients and distributes events."""
    async def _test():
        broadcaster = EventBroadcaster(ring_buffer_size=10, queue_max_size=5)

        client_id = "test_client_1"
        queue = await broadcaster.register_client(client_id)
        assert broadcaster.client_count == 1

        event = broadcaster.publish(event_type="system_status_updated", data={"status": "ONLINE"})

        assert not queue.empty()
        received = await queue.get()
        assert received.event_id == event.event_id
        assert received.event_type == "system_status_updated"

        await broadcaster.remove_client(client_id)
        assert broadcaster.client_count == 0

    asyncio.run(_test())


def test_bounded_queue_overflow_drop():
    """Verify queue does not grow unbounded when client is slow (drop oldest)."""
    async def _test():
        max_size = 3
        broadcaster = EventBroadcaster(ring_buffer_size=10, queue_max_size=max_size)
        client_id = "slow_client"
        queue = await broadcaster.register_client(client_id)

        # Publish 5 events (exceeds queue max size 3)
        for i in range(5):
            broadcaster.publish(event_type="event_step", data={"step": i})

        assert queue.qsize() == max_size

        # The oldest items (0 and 1) were dropped; remaining should be 2, 3, 4
        items = []
        while not queue.empty():
            items.append(await queue.get())

        steps = [item.data["step"] for item in items]
        assert steps == [2, 3, 4]

    asyncio.run(_test())


def test_last_event_id_replay():
    """Verify client reconnecting with Last-Event-ID receives missed events from ring buffer."""
    async def _test():
        broadcaster = EventBroadcaster(ring_buffer_size=20, queue_max_size=20)

        # Publish historical events
        broadcaster.publish("step1", {"v": 1}, event_id="id_1")
        broadcaster.publish("step2", {"v": 2}, event_id="id_2")
        broadcaster.publish("step3", {"v": 3}, event_id="id_3")

        # Client reconnects with last_event_id="id_1"
        queue = await broadcaster.register_client("reconnected_client", last_event_id="id_1")

        # Should replay id_2 and id_3
        replayed = []
        while not queue.empty():
            replayed.append(await queue.get())

        assert len(replayed) == 2
        assert replayed[0].event_id == "id_2"
        assert replayed[1].event_id == "id_3"

    asyncio.run(_test())


def test_heartbeat_dispatch():
    """Verify heartbeat generates periodic heartbeat events."""
    async def _test():
        broadcaster = EventBroadcaster(ring_buffer_size=10, queue_max_size=10)
        queue = await broadcaster.register_client("heartbeat_listener")

        await broadcaster.start_heartbeat(interval_seconds=0.05)
        await asyncio.sleep(0.15)
        await broadcaster.stop_heartbeat()

        received_events = []
        while not queue.empty():
            received_events.append(await queue.get())

        heartbeats = [e for e in received_events if e.event_type == "heartbeat"]
        assert len(heartbeats) >= 1
        assert "activeClients" in heartbeats[0].data

    asyncio.run(_test())
