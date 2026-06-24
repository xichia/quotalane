from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SchedulerEvent(BaseModel):
    job_id: str
    event_type: str
    message: str
    lane_id: str | None = None
    batch_id: str | None = None
    virtual_window: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
