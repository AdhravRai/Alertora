"""
ALERTORA AI — Firebase Cloud Messaging (FCM) Provider Adapter
Provides reliable push notification delivery with:
- Safe credentials verification (graceful dry-run fallback when unconfigured)
- Zero leak of credentials or sensitive data
- Bounded retries with exponential backoff
- Full delivery auditing
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID

logger = logging.getLogger("alertora.notifications.fcm")


class NotificationDispatchResult(BaseModel):
    success_count: int = 0
    failure_count: int = 0
    simulated: bool = False
    tokens_sent: List[str] = Field(default_factory=list)
    failed_tokens: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None


class FCMNotificationProvider:
    """
    FCM Provider with safe credentials validation and simulated delivery fallback.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = FIREBASE_CREDENTIALS_PATH,
        project_id: Optional[str] = FIREBASE_PROJECT_ID,
        max_retries: int = 3,
    ):
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.max_retries = max_retries
        self.is_configured = False
        self._fcm_app = None

        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Attempt safe initialization of Firebase Admin SDK."""
        if not self.credentials_path or not os.path.isfile(self.credentials_path):
            logger.info(
                "[FCM Provider] FCM credentials path unconfigured or not found. "
                "Operating in SAFE DRY-RUN / SIMULATED delivery mode. Zero credentials exposed."
            )
            self.is_configured = False
            return

        try:
            import firebase_admin
            from firebase_admin import credentials, messaging

            # Masked path log (never print full sensitive credentials content)
            masked_path = os.path.basename(self.credentials_path)
            logger.info(f"[FCM Provider] Initializing Firebase Admin with credentials: {masked_path}")

            cred = credentials.Certificate(self.credentials_path)
            self._fcm_app = firebase_admin.initialize_app(cred, name="alertora-fcm")
            self.is_configured = True
            logger.info("[FCM Provider] Firebase Admin initialized successfully.")
        except ImportError:
            logger.warning(
                "[FCM Provider] firebase-admin package not installed. Running in SAFE SIMULATED delivery mode."
            )
            self.is_configured = False
        except Exception as ex:
            logger.warning(
                f"[FCM Provider] Failed to initialize Firebase credentials ({type(ex).__name__}). Falling back to safe simulated delivery mode."
            )
            self.is_configured = False

    async def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
    ) -> NotificationDispatchResult:
        """
        Send notification to a list of device tokens.
        If credentials unconfigured or dry-run, safely simulates dispatch.
        """
        if not tokens:
            return NotificationDispatchResult(success_count=0, failure_count=0, simulated=not self.is_configured)

        data = data or {}

        # 1. Fallback: Safe Simulated Dispatch Mode
        if not self.is_configured or self._fcm_app is None:
            logger.info(
                f"[FCM Provider (Simulated)] Dispatched emergency notification to {len(tokens)} devices: '{title}'"
            )
            return NotificationDispatchResult(
                success_count=len(tokens),
                failure_count=0,
                simulated=True,
                tokens_sent=list(tokens),
            )

        # 2. Live FCM Multicast Dispatch
        from firebase_admin import messaging

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in data.items()},
            tokens=tokens,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    channel_id="alertora_severe_weather",
                    priority="max",
                    sound="default",
                ),
            ),
        )

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = messaging.send_each_for_multicast(message, app=self._fcm_app)
                success_tokens = []
                failed_tokens = []

                for idx, resp in enumerate(response.responses):
                    if resp.success:
                        success_tokens.append(tokens[idx])
                    else:
                        failed_tokens.append(tokens[idx])

                logger.info(
                    f"[FCM Provider] Live multicast complete: {response.success_count} success, {response.failure_count} failed."
                )

                return NotificationDispatchResult(
                    success_count=response.success_count,
                    failure_count=response.failure_count,
                    simulated=False,
                    tokens_sent=success_tokens,
                    failed_tokens=failed_tokens,
                )
            except Exception as ex:
                last_error = str(ex)
                logger.warning(
                    f"[FCM Provider] Multicast attempt {attempt}/{self.max_retries} failed: {ex}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

        return NotificationDispatchResult(
            success_count=0,
            failure_count=len(tokens),
            simulated=False,
            tokens_sent=[],
            failed_tokens=list(tokens),
            error_message=last_error,
        )


# Global singleton FCM provider
fcm_provider = FCMNotificationProvider()
