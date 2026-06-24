from quotalane.models.lane import LaneState, QuotaLane


def test_lane_state_transitions():
    lane = QuotaLane(
        lane_id="lane",
        provider="gemini",
        model="m",
        requests_per_minute=1,
        input_tokens_per_minute=250_000,
        safe_input_token_target=225_000,
        hard_input_token_cap=240_000,
    )
    assert lane.state == LaneState.ready
    lane = lane.mark_processing("batch_001")
    assert lane.state == LaneState.processing
    lane = lane.mark_cooldown(1)
    assert lane.state == LaneState.cooldown
    lane = lane.mark_ready(1)
    assert lane.state == LaneState.ready
