from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LaneState(str, Enum):
    ready = "ready"
    processing = "processing"
    cooldown = "cooldown"
    quota_exhausted = "quota_exhausted"
    failed = "failed"
    disabled = "disabled"


class QuotaLane(BaseModel):
    lane_id: str
    provider: str
    model: str
    api_key_env_name: str | None = None
    requests_per_minute: int = Field(gt=0)
    input_tokens_per_minute: int = Field(gt=0)
    safe_input_token_target: int = Field(gt=0)
    hard_input_token_cap: int = Field(gt=0)
    daily_request_limit: int | None = None
    daily_token_limit: int | None = None
    state: LaneState = LaneState.ready
    cooldown_until_window: int | None = None
    in_flight_batch_id: str | None = None
    requests_used_current_window: int = 0
    input_tokens_used_current_window: int = 0
    current_window: int = 0
    requests_used_today: int = 0
    input_tokens_used_today: int = 0
    last_request_window: int | None = None
    failure_count: int = 0
    updated_at: datetime = Field(default_factory=utc_now)

    def reset_window_if_needed(self, virtual_window: int) -> QuotaLane:
        if self.current_window == virtual_window:
            return self
        return self.model_copy(
            update={
                "current_window": virtual_window,
                "requests_used_current_window": 0,
                "input_tokens_used_current_window": 0,
                "updated_at": utc_now(),
            }
        )

    def mark_processing(self, batch_id: str) -> QuotaLane:
        return self.model_copy(
            update={
                "state": LaneState.processing,
                "in_flight_batch_id": batch_id,
                "updated_at": utc_now(),
            }
        )

    def mark_ready(self, virtual_window: int) -> QuotaLane:
        lane = self.reset_window_if_needed(virtual_window)
        return lane.model_copy(
            update={
                "state": LaneState.ready,
                "in_flight_batch_id": None,
                "cooldown_until_window": None,
                "updated_at": utc_now(),
            }
        )

    def mark_cooldown(self, until_window: int) -> QuotaLane:
        return self.model_copy(
            update={
                "state": LaneState.cooldown,
                "cooldown_until_window": until_window,
                "in_flight_batch_id": None,
                "updated_at": utc_now(),
            }
        )

    def mark_failed(self) -> QuotaLane:
        return self.model_copy(
            update={
                "state": LaneState.failed,
                "failure_count": self.failure_count + 1,
                "in_flight_batch_id": None,
                "updated_at": utc_now(),
            }
        )

    def record_request(self, tokens: int, virtual_window: int) -> QuotaLane:
        lane = self.reset_window_if_needed(virtual_window)
        return lane.model_copy(
            update={
                "requests_used_current_window": lane.requests_used_current_window + 1,
                "input_tokens_used_current_window": lane.input_tokens_used_current_window + tokens,
                "requests_used_today": lane.requests_used_today + 1,
                "input_tokens_used_today": lane.input_tokens_used_today + tokens,
                "last_request_window": virtual_window,
                "updated_at": utc_now(),
            }
        )
