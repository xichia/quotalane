from __future__ import annotations

from collections.abc import Iterable

from quotalane.models.batch import Batch
from quotalane.models.lane import QuotaLane
from quotalane.scheduler.rate_limits import can_accept_batch, refresh_lane_for_window


def ready_lanes(lanes: Iterable[QuotaLane], virtual_window: int) -> list[QuotaLane]:
    refreshed = [refresh_lane_for_window(lane, virtual_window) for lane in lanes]
    return [lane for lane in refreshed if lane.state == "ready"]


def pair_ready_lanes_with_batches(
    lanes: list[QuotaLane], batches: list[Batch], virtual_window: int
) -> list[tuple[QuotaLane, Batch]]:
    pairs: list[tuple[QuotaLane, Batch]] = []
    batch_index = 0
    for lane in lanes:
        while batch_index < len(batches):
            batch = batches[batch_index]
            batch_index += 1
            if can_accept_batch(lane, batch, virtual_window):
                pairs.append((lane, batch))
                break
    return pairs
