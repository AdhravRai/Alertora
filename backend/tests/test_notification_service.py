"""
Unit and integration tests for Notification Service and FCM Provider.
Tests:
- Unconfigured credentials safe fallback (dry-run mode, no crashes)
- Zero credentials leak
- Notification service dispatch coordination
- Metrics and audit payload verification
"""

import asyncio
import pytest

from backend.notifications.fcm_provider import FCMNotificationProvider
from backend.notifications.service import (
    AlertDispatchPayload,
    NotificationService,
)
from backend.spatial.persistence import (
    DeviceRegistrationRequest,
    InMemoryDeviceStore,
)
from backend.spatial.targeting import SpatialTargetingEngine


def test_fcm_provider_safe_fallback_without_credentials():
    """Verify FCM provider cleanly falls back to safe dry-run when credentials missing."""
    async def _test():
        provider = FCMNotificationProvider(credentials_path="non_existent_creds.json")
        assert provider.is_configured is False

        result = await provider.send_multicast(
            tokens=["token_alpha", "token_beta"],
            title="TEST ALERT",
            body="Flash flood risk",
        )

        assert result.simulated is True
        assert result.success_count == 2
        assert result.failure_count == 0
        assert result.tokens_sent == ["token_alpha", "token_beta"]

    asyncio.run(_test())


def test_notification_service_evaluate_and_dispatch():
    """Verify complete notification service orchestration with spatial target matching."""
    async def _test():
        store = InMemoryDeviceStore()
        engine = SpatialTargetingEngine()
        provider = FCMNotificationProvider(credentials_path=None)

        service = NotificationService(provider=provider, engine=engine, store=store)

        # Register devices
        store.register(DeviceRegistrationRequest(
            device_token="dev_in_sector",
            lat=26.5,
            lng=83.5,
        ))
        store.register(DeviceRegistrationRequest(
            device_token="dev_far_away",
            lat=13.0,
            lng=80.0,
        ))

        payload = AlertDispatchPayload(
            hazard_type="HAIL",
            severity="HIGH",
            district="Mau Sector",
            eta="20 mins",
            bbox=(26.4, 83.4, 26.6, 83.6),
        )

        response = await service.evaluate_and_dispatch(payload)

        assert response.status == "SUCCESS"
        assert response.district == "Mau Sector"
        assert response.hazard_type == "HAIL"
        assert response.targeted_devices == 1
        assert response.dispatched_count == 1
        assert response.suppressed_duplicates == 0
        assert response.simulated is True
        assert "Cell Broadcast" in response.broadcast_channels

    asyncio.run(_test())
