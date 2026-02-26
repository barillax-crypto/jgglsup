from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import random


@dataclass
class SyncResult:
    source: str
    status: str
    retries: int
    synced_at: datetime


class SyncService:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._latest_sync: dict[tuple[str, str], datetime] = {}

    def sync(self, org_id: str, source: str) -> SyncResult:
        retries = 0
        while retries <= self.max_retries:
            if random.random() > 0.2:
                synced_at = datetime.utcnow()
                self._latest_sync[(org_id, source)] = synced_at
                return SyncResult(source=source, status="ok", retries=retries, synced_at=synced_at)
            retries += 1
        synced_at = datetime.utcnow()
        return SyncResult(source=source, status="failed", retries=retries, synced_at=synced_at)

    def get_sync_alerts(self, org_id: str, sources: list[str], alert_hours: int) -> list[str]:
        alerts = []
        now = datetime.utcnow()
        for source in sources:
            latest = self._latest_sync.get((org_id, source))
            if latest is None or (now - latest) > timedelta(hours=alert_hours):
                alerts.append(f"{source}: no successful sync in >{alert_hours}h")
        return alerts
