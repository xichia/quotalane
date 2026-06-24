from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class LaneConfig(BaseModel):
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

    @model_validator(mode="after")
    def validate_caps(self) -> LaneConfig:
        if self.safe_input_token_target > self.hard_input_token_cap:
            raise ValueError("safe_input_token_target must be <= hard_input_token_cap")
        if self.hard_input_token_cap > self.input_tokens_per_minute:
            raise ValueError("hard_input_token_cap must be <= input_tokens_per_minute")
        return self


class BatchingConfig(BaseModel):
    preserve_input_order: bool = True
    max_items_per_batch: int = Field(default=500, gt=0)
    safe_input_token_target: int = Field(default=225_000, gt=0)
    hard_input_token_cap: int = Field(default=240_000, gt=0)
    allow_safe_target_overflow: bool = True

    @model_validator(mode="after")
    def validate_caps(self) -> BatchingConfig:
        if self.safe_input_token_target > self.hard_input_token_cap:
            raise ValueError("safe_input_token_target must be <= hard_input_token_cap")
        return self


class RetryConfig(BaseModel):
    max_attempts: int = Field(default=3, ge=1)
    backoff_seconds: int = Field(default=60, ge=0)
    requeue_missing_outputs: bool = True


class CheckpointingConfig(BaseModel):
    enabled: bool = True
    checkpoint_every_batches: int = Field(default=1, ge=1)


class SimulationConfig(BaseModel):
    work_items: int = Field(default=9800, gt=0)
    average_tokens_per_item: int = Field(default=690, gt=0)
    token_jitter_ratio: float = Field(default=0.25, ge=0.0, le=1.0)
    provider_latency_seconds: float = Field(default=2.0, ge=0.0)
    fail_batch_ids: list[str] = Field(default_factory=list)
    missing_output_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    random_seed: int = 42


class JobConfig(BaseModel):
    job_id: str
    job_type: str
    provider: str
    model: str
    lanes: list[LaneConfig] = Field(min_length=1)
    batching: BatchingConfig = Field(default_factory=BatchingConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    checkpointing: CheckpointingConfig = Field(default_factory=CheckpointingConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)

    @model_validator(mode="after")
    def validate_lane_ids(self) -> JobConfig:
        lane_ids = [lane.lane_id for lane in self.lanes]
        if len(set(lane_ids)) != len(lane_ids):
            raise ValueError("lane_id values must be unique")
        largest_lane_cap = max(lane.hard_input_token_cap for lane in self.lanes)
        if self.batching.hard_input_token_cap > largest_lane_cap:
            raise ValueError("batching.hard_input_token_cap must fit at least one lane")
        return self


def load_job_config(path: str | Path) -> JobConfig:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return JobConfig.model_validate(data)
