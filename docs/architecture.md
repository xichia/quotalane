# QuotaLane architecture

QuotaLane is a scheduler, not a summarization service.

## Core objects

- `WorkItem`: one unit of LLM work. For paragraph summaries, one item maps to one DeepReader paragraph record. QuotaLane stores only IDs, hashes, estimated tokens, safe metadata, and status.
- `Batch`: a set of work item IDs packed near a safe token target.
- `QuotaLane`: one independent provider API key with its own RPM/TPM limits and state.
- `Job`: a collection of work items and batches.
- `BatchExecutionResult`: item-level result accounting returned by an executor.

## Scheduling loop

```text
load or create job state
pack pending work items into batches
select lanes with ready capacity
assign one batch to each ready lane
execute assignments concurrently
record results
requeue failed or missing work when attempts remain
checkpoint state
repeat until terminal
```

## Dispatch windows

The simulator uses virtual dispatch windows. A lane with `requests_per_minute: 1` can receive one batch in a given virtual minute. The simulator does not sleep for real minutes; it advances a minute counter after each dispatch window.

## Persistence

SQLite tables:

- `jobs`
- `work_items`
- `batches`
- `lanes`
- `batch_attempts`
- `scheduler_events`
- `checkpoints`

Checkpoint records contain JSON summaries sufficient to resume simulator jobs without duplicating completed batches.

## Safety rules

QuotaLane must not persist or log:

- raw paragraph text,
- full prompts,
- API keys,
- credentials,
- sensitive metadata.

The `WorkItem` model strips metadata keys that commonly contain raw text or prompts. The same recursive sanitizer is applied to scheduler event details before SQLite persistence, so operational events can record safe counts, IDs, statuses, and error codes without carrying prompts or source text.

Lane records may store API-key environment variable names, such as `GEMINI_API_KEY_1`, but not key values.

## Future integration

`paragraph-summary-service` should import QuotaLane and implement a batch executor. QuotaLane should not import the service.

```text
paragraph-summary-service -> QuotaLane
QuotaLane -/-> paragraph-summary-service
```
