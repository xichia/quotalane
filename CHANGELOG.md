# Changelog

## Unreleased

- Improved CLI ergonomics by adding clear help text for all commands.
- Added explicit file existence checks and YAML validation to give clear error messages for invalid configs.
- Added tests for CLI failure paths (invalid config, missing config, unknown job id in resume and inspect).
- Documented explicit architecture decisions (raw text storage, virtual simulated time, service separation).
- Hardened recursive redaction for work-item metadata and scheduler event details.
- Added job-config validation so planned batch hard caps must fit at least one quota lane.
- Expanded regression coverage for hard-cap packing, dispatch-window lane assignment, failed-batch retry attempts, resume deduplication, and no-raw-text storage.
- Updated README and integration docs with the safe persistence and executor boundary contracts.

## 0.1.0 - Initial simulator slice

- Added Typer CLI with `simulate`, `status`, `inspect`, and `resume` commands.
- Added Pydantic YAML job config models.
- Added fake paragraph workload generation.
- Added deterministic token-aware batch packing.
- Added async multi-lane simulator dispatch.
- Added per-lane RPM/TPM checks using virtual dispatch windows.
- Added basic retry/requeue behavior.
- Added missing-output detection and retry batches.
- Added SQLite persistence for jobs, work items, batches, lanes, events, and checkpoints.
- Added offline pytest coverage and GitHub Actions CI.
