from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

SENSITIVE_METADATA_KEYS = {
    "text",
    "raw_text",
    "paragraph_text",
    "prompt",
    "full_prompt",
    "api_key",
    "credential",
    "credentials",
    "secret",
    "password",
    "authorization",
    "access_token",
    "refresh_token",
    "bearer_token",
}


class WorkStatus(str, Enum):
    pending = "pending"
    batched = "batched"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    missing = "missing"


def utc_now() -> datetime:
    return datetime.now(UTC)


def _is_sensitive_metadata_key(key: str) -> bool:
    normalized = key.lower().strip()
    if normalized in SENSITIVE_METADATA_KEYS:
        return True
    return any(token in normalized for token in ("api_key", "secret", "credential"))


def _sanitize_metadata_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return sanitize_metadata(value)
    if isinstance(value, list):
        return [_sanitize_metadata_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_metadata_value(item) for item in value)
    return value


def sanitize_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    """Drop metadata keys likely to contain raw text, prompts, or secrets."""
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        if _is_sensitive_metadata_key(str(key)):
            continue
        safe[key] = _sanitize_metadata_value(value)
    return safe


class WorkItem(BaseModel):
    work_item_id: str
    external_id: str
    input_text_hash: str
    estimated_input_tokens: int = Field(gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: WorkStatus = WorkStatus.pending
    attempt_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("metadata")
    @classmethod
    def sanitize(cls, value: dict[str, Any]) -> dict[str, Any]:
        return sanitize_metadata(value)

    def mark(self, status: WorkStatus) -> WorkItem:
        return self.model_copy(update={"status": status, "updated_at": utc_now()})

    def increment_attempt(self) -> WorkItem:
        return self.model_copy(
            update={"attempt_count": self.attempt_count + 1, "updated_at": utc_now()}
        )
