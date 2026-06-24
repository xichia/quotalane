# QuotaLane

QuotaLane is a standalone, multi-key, token-aware LLM workload scheduler for large AI jobs that need to run safely under provider quota constraints.

It is designed as infrastructure for portfolio-scale AI systems work: asynchronous scheduling, multi-key parallel dispatch, token-aware batch packing, retry and requeue logic, missing-output recovery, SQLite checkpointing, Typer CLI design, structured logs, simulator mode, and offline test coverage.

> QuotaLane schedules work. It does not summarize documents, ingest content, or perform RAG.

## Why this exists

Large LLM jobs are usually limited less by CPU and more by provider quotas: tokens per minute, requests per minute, daily limits, and occasional incomplete outputs. QuotaLane turns many small work items into near-limit token batches, assigns them to independent API-key quota lanes, processes one batch per lane per dispatch window, and records enough scheduler state to recover safely.

The primary demonstration workload is paragraph summarization for DeepReader records.

## Relationship to the companion projects

```text
DeepReader:
  traceable document intelligence and retrieval

paragraph-summary-service:
  provider-backed paragraph-summary artifact generation

QuotaLane:
  reliable multi-key scheduling for large LLM workloads under provider constraints
```

### Boundaries

DeepReader owns document ingestion, source paragraph text, stable record IDs, retrieval, QA, citations, evidence inspection, and summary indexing.

`paragraph-summary-service` owns request validation, paragraph-record contracts, redaction, prompt rendering, provider calls, cache writes, usage/cost metadata, JSONL artifact writing, and direct small-request summarization.

QuotaLane owns token-aware batch packing for large jobs, multi-key lane assignment, parallel dispatch windows, per-lane RPM/TPM limits, cooldowns, retries, failed-batch requeue, missing-output recovery, checkpoints, and scheduler events.

## Architecture

```text
src/quotalane
├── cli                       Typer commands
├── config                    YAML/Pydantic config models
├── integrations              Generic contracts for future service integration
├── models                    Work items, batches, lanes, jobs, results
├── observability             Event and logging helpers
├── providers                 BatchExecutor protocol and mock provider
├── scheduler                 Packer, dispatch, rate limit, retry helpers
├── simulator                 Fake workload generation and async simulation engine
└── storage                   SQLite schema and repositories
```

The core abstraction for future integration is:

```python
class BatchExecutor(Protocol):
    async def execute_batch(self, batch: ScheduledBatch) -> BatchExecutionResult:
        ...
```

`paragraph-summary-service` can later implement this protocol while QuotaLane remains provider-agnostic.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
quotalane simulate examples/paragraph_summary_large_job.yaml --reset
```

The simulator requires no API keys.

## Simulator demo

The included example config creates four Gemini-style lanes, each with:

```text
RPM: 1
Input TPM: 250,000
Safe input token target: 225,000
Hard input token cap: 240,000
```

Run:

```bash
quotalane simulate examples/paragraph_summary_large_job.yaml --reset
```

Expected output shape:

```text
QuotaLane simulation
Job: paragraph_summary_large_demo
Work items: 9,800
Estimated input tokens: ~6.7M
Lanes: 4
Batches planned: ~31

Dispatch window 1:
  gemini_key_1 -> batch_001 -> ~225k tokens
  gemini_key_2 -> batch_002 -> ~225k tokens
  gemini_key_3 -> batch_003 -> ~225k tokens
  gemini_key_4 -> batch_004 -> ~225k tokens

Result:
  completed batches: 31
  failed batches: 0
  missing outputs: 0
  parallel lanes used: 4
  estimated dispatch windows: 8
  estimated elapsed time: ~8 minutes
  final status: completed
```

## Multi-key lane config

Each API key is represented as one independent quota lane:

```yaml
lanes:
  - lane_id: gemini_key_1
    provider: gemini
    model: gemini-3.1-flash-lite
    api_key_env_name: GEMINI_API_KEY_1
    requests_per_minute: 1
    input_tokens_per_minute: 250000
    safe_input_token_target: 225000
    hard_input_token_cap: 240000
```

Four keys means four near-225k-token batches can be assigned in the same dispatch window. Ten keys means ten lanes can run in parallel, subject to configured limits.

## Batch packing logic

The packer is deterministic and order-preserving by default. It:

- estimates tokens per item from the supplied `estimated_input_tokens` field,
- adds items until the safe target would be exceeded,
- optionally allows slight safe-target overflow when still under the hard cap,
- never emits a batch above the hard cap,
- preserves work item IDs, and
- tracks estimated input tokens per batch.

For Gemini paragraph-summary workloads, the intended defaults are:

```text
Input TPM: 250,000
Safe target: 225,000
Hard cap: 240,000
RPM: 1 request/lane/minute
```

## Parallel dispatch model

The simulator runs in virtual dispatch windows. In each window:

1. ready lanes are selected,
2. one ready batch is paired with each ready lane,
3. those assignments are dispatched concurrently with `asyncio`,
4. batch, lane, work-item, and scheduler-event state is persisted,
5. failed batches and missing outputs are requeued when attempts remain.

No real provider calls are made in v0.1.

## Rate-limit handling

QuotaLane models per-lane request and token windows. A lane can accept a batch only when that lane has enough request and token capacity in the current virtual minute. Lanes transition through explicit states:

```text
ready -> processing -> cooldown -> ready
ready -> processing -> failed/quota_exhausted/disabled
```

A failure on one lane does not block healthy lanes unless a future fail-fast mode is enabled.

## Retries and missing-output recovery

Provider responses may fail or return incomplete item-level outputs. QuotaLane records per-item results and can requeue missing outputs into retry batches while preserving completed outputs.

The simulator supports:

```yaml
simulation:
  fail_batch_ids: [batch_006]
  missing_output_ratio: 0.05
retry:
  max_attempts: 3
  backoff_seconds: 60
  requeue_missing_outputs: true
```

## Checkpointing and resume

SQLite persists jobs, work items, lanes, batches, attempts, events, and checkpoints. This is enough for simulator resume without duplicating completed batches.

QuotaLane intentionally does **not** persist raw paragraph text, prompts, API keys, or credentials. It persists stable IDs, hashes, estimated token counts, statuses, and safe metadata.

### Safety and storage contract

QuotaLane treats work-item metadata and scheduler event details as untrusted. Before persistence, it recursively drops keys commonly used for raw text, prompts, API keys, secrets, credentials, passwords, and bearer/access tokens.

The scheduler stores API-key environment variable names for lane configuration, but never reads, logs, or stores the key values. Future provider-backed executors should resolve raw text and credentials outside QuotaLane, then return only item IDs, statuses, safe error codes, and token usage.

## CLI

```bash
quotalane simulate examples/paragraph_summary_large_job.yaml --reset
quotalane status
quotalane inspect paragraph_summary_large_demo
quotalane resume paragraph_summary_large_demo
```

`resume` reopens the saved checkpoint database and continues incomplete simulator work from persisted state.

## Testing

```bash
pytest
```

The test suite covers packing, dispatch windows, per-lane limits, lane state transitions, cooldowns, retry and missing-output requeue, checkpoint load/save, CLI behavior, SQLite repositories, and no-raw-text persistence.

Recent hardening also covers recursive redaction, event-detail redaction, resume without duplicate attempts, and config validation that prevents batches no lane can accept.

## Limitations

v0.1 is a simulator-first vertical slice. It does not make real provider calls, does not yet enforce daily quota limits, and does not include a FastAPI service. These are intentionally deferred to keep QuotaLane independent and integration-ready.

## Roadmap

See [`docs/v0.1_tasks.md`](docs/v0.1_tasks.md) and [`docs/architecture.md`](docs/architecture.md).

## Portfolio positioning

QuotaLane demonstrates infrastructure for reliable AI workloads under real API constraints: multi-key parallelism, token-aware batching, rate-limit handling, retry/recovery, checkpointing, and clean service boundaries.
