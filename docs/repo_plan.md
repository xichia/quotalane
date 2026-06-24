# Repository plan

## Goal

Build QuotaLane as a standalone Python package and CLI before integrating it with `paragraph-summary-service`.

## v0.1 vertical slice

The first version proves the core scheduling value:

```text
Read YAML config
Generate fake paragraph work items
Pack near-225k-token batches
Create one quota lane per API key config
Dispatch one batch per ready lane per virtual minute
Persist state to SQLite
Show clear terminal output
Run offline tests in CI
```

## Package responsibilities

- `config`: validates YAML job and lane settings.
- `models`: defines safe domain objects with no raw text persistence.
- `scheduler`: handles packing, rate-limit checks, lane selection, retry, and missing-output batch creation.
- `simulator`: owns fake workload generation and the async dispatch loop.
- `storage`: persists jobs, work items, batches, lanes, events, attempts, and checkpoints.
- `cli`: provides operator-facing commands.
- `integrations`: defines future service contracts without importing external services.

## Milestone sequence

1. **v0.1.0**: simulator and SQLite checkpoint vertical slice.
2. **v0.2.0**: hardened retry, missing-output, and resume workflows.
3. **v0.3.0**: paragraph-summary-service integration contract and fake integration tests.
4. **v0.4.0**: daily limits, lane disabling, richer failure scenarios, and observability.
5. **v0.5.0**: portfolio polish, case study, demo transcript, screenshots, and release tag.

## Integration boundary

`paragraph-summary-service` should import QuotaLane and provide an executor implementation. QuotaLane should remain provider-agnostic and should not import DeepReader or the service.
