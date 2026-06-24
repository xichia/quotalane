from __future__ import annotations

import hashlib
import random

from quotalane.config.job_config import SimulationConfig
from quotalane.models.work import WorkItem


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def generate_fake_paragraph_work_items(config: SimulationConfig) -> list[WorkItem]:
    rng = random.Random(config.random_seed)
    jitter = config.token_jitter_ratio
    items: list[WorkItem] = []
    low = max(1, int(config.average_tokens_per_item * (1 - jitter)))
    high = max(low, int(config.average_tokens_per_item * (1 + jitter)))
    for index in range(1, config.work_items + 1):
        tokens = rng.randint(low, high)
        external_id = f"deepreader_paragraph_{index:06d}"
        items.append(
            WorkItem(
                work_item_id=f"work_{index:06d}",
                external_id=external_id,
                input_text_hash=_stable_hash(external_id),
                estimated_input_tokens=tokens,
                metadata={"source": "simulator", "ordinal": index},
            )
        )
    return items
