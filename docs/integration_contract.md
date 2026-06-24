# paragraph-summary-service integration contract

QuotaLane exposes provider-agnostic scheduling objects. A future `paragraph-summary-service` integration should provide a concrete executor that receives a scheduled batch and returns item-level results.

## Direction of dependency

Use:

```text
paragraph-summary-service -> imports/uses QuotaLane
```

Avoid:

```text
QuotaLane -> imports paragraph-summary-service
```

## Executor protocol

```python
class BatchExecutor(Protocol):
    async def execute_batch(self, batch: ScheduledBatch) -> BatchExecutionResult:
        ...
```

The service executor should:

1. resolve paragraph texts from the original request or service-owned storage,
2. apply redaction,
3. check cache hits,
4. render prompts,
5. call mock/Gemini provider only when explicitly enabled,
6. parse item-level outputs,
7. write cache entries,
8. append JSONL artifact lines,
9. return completed, failed, and missing work item IDs.

The executor should not pass raw paragraph text, prompts, provider credentials, or sensitive request metadata back into QuotaLane result metadata or scheduler events. Use stable IDs, hashes, safe error codes, and usage counts.

## Resume contract

QuotaLane can persist scheduler state without raw paragraph text. If a service restarts and raw paragraph text was not persisted, the caller must resubmit the original records. The service verifies stable record IDs and `input_text_hash` values before resuming incomplete items.
