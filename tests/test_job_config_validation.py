import pytest

from quotalane.config.job_config import BatchingConfig, JobConfig, LaneConfig


def _lane(*, lane_id: str = "lane", hard_cap: int = 240_000) -> LaneConfig:
    return LaneConfig(
        lane_id=lane_id,
        provider="gemini",
        model="gemini-3.1-flash-lite",
        api_key_env_name="KEY",
        requests_per_minute=1,
        input_tokens_per_minute=max(250_000, hard_cap),
        safe_input_token_target=min(225_000, hard_cap),
        hard_input_token_cap=hard_cap,
    )


def test_job_config_requires_at_least_one_lane():
    with pytest.raises(ValueError):
        JobConfig(
            job_id="job",
            job_type="paragraph_summary",
            provider="gemini",
            model="gemini-3.1-flash-lite",
            lanes=[],
        )


def test_batching_hard_cap_must_fit_at_least_one_lane():
    with pytest.raises(ValueError, match="must fit at least one lane"):
        JobConfig(
            job_id="job",
            job_type="paragraph_summary",
            provider="gemini",
            model="gemini-3.1-flash-lite",
            lanes=[_lane(hard_cap=120_000)],
            batching=BatchingConfig(
                safe_input_token_target=200_000,
                hard_input_token_cap=240_000,
            ),
        )


def test_batching_hard_cap_may_target_largest_lane():
    config = JobConfig(
        job_id="job",
        job_type="paragraph_summary",
        provider="gemini",
        model="gemini-3.1-flash-lite",
        lanes=[
            _lane(lane_id="small", hard_cap=120_000),
            _lane(lane_id="large", hard_cap=240_000),
        ],
        batching=BatchingConfig(
            safe_input_token_target=225_000,
            hard_input_token_cap=240_000,
        ),
    )

    assert config.batching.hard_input_token_cap == 240_000
