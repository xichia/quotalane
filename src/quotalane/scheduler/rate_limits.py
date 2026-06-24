from __future__ import annotations

from quotalane.models.batch import Batch
from quotalane.models.lane import LaneState, QuotaLane


def refresh_lane_for_window(lane: QuotaLane, virtual_window: int) -> QuotaLane:
    lane = lane.reset_window_if_needed(virtual_window)
    if lane.state == LaneState.cooldown and lane.cooldown_until_window is not None:
        if lane.cooldown_until_window <= virtual_window:
            lane = lane.mark_ready(virtual_window)
    return lane


def can_accept_batch(lane: QuotaLane, batch: Batch, virtual_window: int) -> bool:
    lane = refresh_lane_for_window(lane, virtual_window)
    if lane.state != LaneState.ready:
        return False
    if batch.estimated_input_tokens > lane.hard_input_token_cap:
        return False
    if lane.requests_used_current_window + 1 > lane.requests_per_minute:
        return False
    if lane.input_tokens_used_current_window + batch.estimated_input_tokens > lane.input_tokens_per_minute:
        return False
    if lane.daily_request_limit is not None and lane.requests_used_today + 1 > lane.daily_request_limit:
        return False
    if lane.daily_token_limit is not None and lane.input_tokens_used_today + batch.estimated_input_tokens > lane.daily_token_limit:
        return False
    return True
