"""
ALERTORA AI — Real-Time Pipeline Watcher
Monitors ML nowcasting and spatial risk-zone output artifacts.
Detects file mtime changes and broadcasts real-time events to connected clients:
- forecast_updated: when alertora_forecast_july29_0200.json updates
- risk_zones_updated: when risk_zones_july29_0200.json updates
- storm_trajectory_updated: when nowcast_result.json updates
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from backend.config import DATA_PROCESSED_DIR, PERSON_B_OUTPUT_DIR
from backend.real_time.event_bus import broadcaster

logger = logging.getLogger("alertora.pipeline_watcher")


class PipelineWatcher:
    """
    Watches processed data directories and publishes events when pipeline outputs change.
    """

    def __init__(self, check_interval_seconds: float = 5.0):
        self.check_interval = check_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._mtimes: Dict[str, float] = {}

        # Target monitored files
        self.monitored_targets = {
            "forecast": DATA_PROCESSED_DIR / "alertora_forecast_july29_0200.json",
            "risk_zones": DATA_PROCESSED_DIR / "risk_zones_july29_0200.json",
            "trajectory": PERSON_B_OUTPUT_DIR / "nowcast_result.json",
        }

    def _initialize_mtimes(self) -> None:
        """Record initial modification times of target files."""
        for key, path in self.monitored_targets.items():
            if path.exists():
                try:
                    self._mtimes[key] = os.path.getmtime(path)
                except OSError:
                    self._mtimes[key] = 0.0
            else:
                self._mtimes[key] = 0.0

    def check_and_publish_updates(self) -> Dict[str, bool]:
        """
        Check file timestamps against recorded mtimes and publish events if changed.
        Returns a dict of which targets were updated.
        """
        updates: Dict[str, bool] = {}

        # 1. Forecast update
        forecast_path = self.monitored_targets["forecast"]
        if forecast_path.exists():
            try:
                mtime = os.path.getmtime(forecast_path)
                prev_mtime = self._mtimes.get("forecast", 0.0)
                if prev_mtime > 0 and mtime > prev_mtime:
                    with open(forecast_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    broadcaster.publish(
                        event_type="forecast_updated",
                        data={
                            "source": forecast_path.name,
                            "timestamp": data.get("metadata", {}).get("forecast_time", "2026-07-29T02:00:00Z"),
                            "gridPoints": len(data.get("grid_forecasts", [])),
                            "leadHorizons": [1, 2, 3, 4, 5, 6],
                        },
                    )
                    updates["forecast"] = True
                self._mtimes["forecast"] = mtime
            except Exception as ex:
                logger.warning(f"Error checking forecast file: {ex}")

        # 2. Risk zones update
        risk_path = self.monitored_targets["risk_zones"]
        if risk_path.exists():
            try:
                mtime = os.path.getmtime(risk_path)
                prev_mtime = self._mtimes.get("risk_zones", 0.0)
                if prev_mtime > 0 and mtime > prev_mtime:
                    with open(risk_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    broadcaster.publish(
                        event_type="risk_zones_updated",
                        data={
                            "source": risk_path.name,
                            "horizonCount": len(data),
                            "horizons": list(data.keys()),
                        },
                    )
                    updates["risk_zones"] = True
                self._mtimes["risk_zones"] = mtime
            except Exception as ex:
                logger.warning(f"Error checking risk zones file: {ex}")

        # 3. Storm trajectory update
        traj_path = self.monitored_targets["trajectory"]
        if traj_path.exists():
            try:
                mtime = os.path.getmtime(traj_path)
                prev_mtime = self._mtimes.get("trajectory", 0.0)
                if prev_mtime > 0 and mtime > prev_mtime:
                    with open(traj_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    broadcaster.publish(
                        event_type="storm_trajectory_updated",
                        data={
                            "source": traj_path.name,
                            "trackingAvailable": "trajectory" in data or "features" in data or "storm_track" in data,
                            "summary": "Updated convective storm trajectory vectors loaded",
                        },
                    )
                    updates["trajectory"] = True
                self._mtimes["trajectory"] = mtime
            except Exception as ex:
                logger.warning(f"Error checking trajectory file: {ex}")

        return updates

    async def start(self) -> None:
        """Start the background file inspection loop."""
        if self._task and not self._task.done():
            return

        self._initialize_mtimes()

        async def _watch_loop():
            logger.info("[PipelineWatcher] Started file change watcher.")
            while True:
                try:
                    await asyncio.sleep(self.check_interval)
                    self.check_and_publish_updates()
                except asyncio.CancelledError:
                    break
                except Exception as ex:
                    logger.warning(f"[PipelineWatcher] Loop error: {ex}")

        self._task = asyncio.create_task(_watch_loop())

    async def stop(self) -> None:
        """Stop the background watcher loop."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("[PipelineWatcher] Stopped file change watcher.")


# Global singleton pipeline watcher instance
pipeline_watcher = PipelineWatcher()
