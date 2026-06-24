from __future__ import annotations

from pathlib import Path

import pytest

from quotalane.config.job_config import (
    BatchingConfig,
    CheckpointingConfig,
    JobConfig,
    LaneConfig,
    RetryConfig,
    SimulationConfig,
)


@pytest.fixture
def small_config() -> JobConfig:
    return JobConfig(
        job_id="test_job",
        job_type="paragraph_summary",
        provider="gemini",
        model="gemini-3.1-flash-lite",
        lanes=[
            LaneConfig(
                lane_id="lane_1",
                provider="gemini",
                model="gemini-3.1-flash-lite",
                api_key_env_name="KEY_1",
                requests_per_minute=1,
                input_tokens_per_minute=250_000,
                safe_input_token_target=225_000,
                hard_input_token_cap=240_000,
            ),
            LaneConfig(
                lane_id="lane_2",
                provider="gemini",
                model="gemini-3.1-flash-lite",
                api_key_env_name="KEY_2",
                requests_per_minute=1,
                input_tokens_per_minute=250_000,
                safe_input_token_target=225_000,
                hard_input_token_cap=240_000,
            ),
        ],
        batching=BatchingConfig(
            preserve_input_order=True,
            max_items_per_batch=500,
            safe_input_token_target=225_000,
            hard_input_token_cap=240_000,
        ),
        retry=RetryConfig(max_attempts=3, backoff_seconds=60, requeue_missing_outputs=True),
        checkpointing=CheckpointingConfig(enabled=True, checkpoint_every_batches=1),
        simulation=SimulationConfig(
            work_items=700,
            average_tokens_per_item=690,
            token_jitter_ratio=0.1,
            provider_latency_seconds=0,
            random_seed=123,
        ),
    )


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "quotalane.sqlite"
