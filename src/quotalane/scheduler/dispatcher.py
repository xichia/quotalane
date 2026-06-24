from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from quotalane.models.batch import Batch
from quotalane.models.results import BatchExecutionResult

DispatchCallable = Callable[[Batch], Awaitable[BatchExecutionResult]]


async def dispatch_concurrently(
    assignments: list[tuple[str, Batch]], executor: DispatchCallable
) -> list[BatchExecutionResult]:
    tasks = [asyncio.create_task(executor(batch)) for _, batch in assignments]
    if not tasks:
        return []
    return list(await asyncio.gather(*tasks))
