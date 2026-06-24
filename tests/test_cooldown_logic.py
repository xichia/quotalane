from quotalane.models.lane import LaneState, QuotaLane
from quotalane.scheduler.rate_limits import refresh_lane_for_window


def test_cooldown_logic():
    lane = QuotaLane(
        lane_id="lane",
        provider="gemini",
        model="m",
        requests_per_minute=1,
        input_tokens_per_minute=250_000,
        safe_input_token_target=225_000,
        hard_input_token_cap=240_000,
    ).mark_cooldown(2)
    assert refresh_lane_for_window(lane, 1).state == LaneState.cooldown
    assert refresh_lane_for_window(lane, 2).state == LaneState.ready
