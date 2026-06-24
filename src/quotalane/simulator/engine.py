from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field

from quotalane.config.job_config import JobConfig
from quotalane.models.batch import Batch, BatchStatus
from quotalane.models.job import Job, JobStatus
from quotalane.models.lane import LaneState, QuotaLane
from quotalane.models.results import BatchExecutionResult, BatchExecutionStatus
from quotalane.models.work import WorkItem, WorkStatus
from quotalane.scheduler.missing_outputs import create_missing_output_retry_batch
from quotalane.scheduler.planner import plan_initial_batches
from quotalane.scheduler.rate_limits import can_accept_batch, refresh_lane_for_window
from quotalane.scheduler.retry import mark_for_retry, should_retry_batch
from quotalane.simulator.fake_executor import FakeBatchExecutor
from quotalane.simulator.scenarios import generate_fake_paragraph_work_items
from quotalane.storage.repositories import SQLiteRepository


class DispatchRecord(BaseModel):
    lane_id: str
    batch_id: str
    estimated_input_tokens: int
    status: str | None = None
    missing_outputs: int = 0


class DispatchWindow(BaseModel):
    window: int
    assignments: list[DispatchRecord] = Field(default_factory=list)


class SimulationResult(BaseModel):
    job_id: str
    work_items: int
    estimated_input_tokens: int
    lane_count: int
    batches_planned: int
    completed_batches: int
    failed_batches: int
    missing_outputs: int
    parallel_lanes_used: int
    estimated_dispatch_windows: int
    estimated_elapsed_minutes: int
    final_status: JobStatus
    windows: list[DispatchWindow]


@dataclass
class SimulationState:
    config: JobConfig
    repository: SQLiteRepository
    db_path: Path
    job: Job
    work_items: dict[str, WorkItem]
    lanes: dict[str, QuotaLane]
    queued_batches: list[Batch]
    terminal_batches: dict[str, Batch] = field(default_factory=dict)
    virtual_window: int = 0
    windows: list[DispatchWindow] = field(default_factory=list)
    retry_batch_counter: int = 1

    @property
    def estimated_tokens_by_id(self) -> dict[str, int]:
        return {item_id: item.estimated_input_tokens for item_id, item in self.work_items.items()}


def lanes_from_config(config: JobConfig) -> list[QuotaLane]:
    return [
        QuotaLane(
            lane_id=lane.lane_id,
            provider=lane.provider,
            model=lane.model,
            api_key_env_name=lane.api_key_env_name,
            requests_per_minute=lane.requests_per_minute,
            input_tokens_per_minute=lane.input_tokens_per_minute,
            safe_input_token_target=lane.safe_input_token_target,
            hard_input_token_cap=lane.hard_input_token_cap,
            daily_request_limit=lane.daily_request_limit,
            daily_token_limit=lane.daily_token_limit,
        )
        for lane in config.lanes
    ]


def _new_job(config: JobConfig, db_path: Path, work_items: list[WorkItem]) -> Job:
    return Job(
        job_id=config.job_id,
        job_type=config.job_type,
        status=JobStatus.running,
        total_work_items=len(work_items),
        completed_work_items=0,
        failed_work_items=0,
        missing_outputs=0,
        total_estimated_input_tokens=sum(item.estimated_input_tokens for item in work_items),
        checkpoint_path=str(db_path),
    )


def build_fresh_state(config: JobConfig, repository: SQLiteRepository, db_path: Path, *, reset: bool) -> SimulationState:
    if reset:
        repository.reset()
    work_items_list = generate_fake_paragraph_work_items(config.simulation)
    batches = plan_initial_batches(config, work_items_list)
    lanes = lanes_from_config(config)
    job = _new_job(config, db_path, work_items_list)
    repository.upsert_job(job)
    repository.upsert_work_items(config.job_id, work_items_list)
    repository.upsert_batches(batches)
    repository.upsert_lanes(lanes)
    repository.record_event(
        job_id=config.job_id,
        event_type="job_started",
        message="Simulation job initialized",
        details={"planned_batches": len(batches), "lanes": len(lanes)},
    )
    return SimulationState(
        config=config,
        repository=repository,
        db_path=db_path,
        job=job,
        work_items={item.work_item_id: item for item in work_items_list},
        lanes={lane.lane_id: lane for lane in lanes},
        queued_batches=list(batches),
    )


def load_state_for_resume(config: JobConfig, repository: SQLiteRepository, db_path: Path) -> SimulationState:
    job = repository.get_job(config.job_id)
    if job is None:
        return build_fresh_state(config, repository, db_path, reset=False)
    work_items_list = repository.list_work_items(config.job_id)
    lanes_list = repository.list_lanes() or lanes_from_config(config)
    all_batches = repository.list_batches(config.job_id)
    queued = [
        batch
        for batch in all_batches
        if batch.status in {BatchStatus.queued, BatchStatus.pending, BatchStatus.retry_pending, BatchStatus.processing}
    ]
    terminal = {
        batch.batch_id: batch
        for batch in all_batches
        if batch.status in {BatchStatus.completed, BatchStatus.failed, BatchStatus.partially_completed}
    }
    checkpoint = repository.latest_checkpoint(config.job_id)
    virtual_window = checkpoint["virtual_window"] + 1 if checkpoint else 0
    return SimulationState(
        config=config,
        repository=repository,
        db_path=db_path,
        job=job.model_copy(update={"status": JobStatus.running}),
        work_items={item.work_item_id: item for item in work_items_list},
        lanes={lane.lane_id: lane for lane in lanes_list},
        queued_batches=queued,
        terminal_batches=terminal,
        virtual_window=virtual_window,
        retry_batch_counter=len([b for b in all_batches if b.batch_id.startswith("retry_")]) + 1,
    )


def _select_assignments(state: SimulationState) -> list[tuple[QuotaLane, Batch]]:
    assignments: list[tuple[QuotaLane, Batch]] = []
    remaining_batches: list[Batch] = []
    for lane_id in sorted(state.lanes):
        lane = refresh_lane_for_window(state.lanes[lane_id], state.virtual_window)
        state.lanes[lane_id] = lane
        if lane.state != LaneState.ready:
            continue
        selected_index: int | None = None
        for index, batch in enumerate(state.queued_batches):
            if can_accept_batch(lane, batch, state.virtual_window):
                selected_index = index
                break
        if selected_index is not None:
            batch = state.queued_batches.pop(selected_index)
            assignments.append((lane, batch))
    remaining_batches.extend(state.queued_batches)
    state.queued_batches = remaining_batches
    return assignments


async def _execute_window(state: SimulationState, executor: FakeBatchExecutor) -> None:
    assignments = _select_assignments(state)
    if not assignments:
        state.virtual_window += 1
        return

    dispatch_window = DispatchWindow(window=state.virtual_window + 1)
    prepared: list[tuple[QuotaLane, Batch]] = []
    for lane, batch in assignments:
        assigned_batch = batch.assign(lane.lane_id)
        processing_lane = lane.mark_processing(assigned_batch.batch_id).record_request(
            assigned_batch.estimated_input_tokens, state.virtual_window
        )
        state.lanes[lane.lane_id] = processing_lane
        state.repository.upsert_batches([assigned_batch])
        state.repository.upsert_lanes([processing_lane])
        state.repository.update_work_statuses(
            state.config.job_id,
            {item_id: WorkStatus.processing for item_id in assigned_batch.work_item_ids},
            increment_attempt=True,
        )
        state.repository.record_event(
            job_id=state.config.job_id,
            event_type="batch_dispatched",
            message="Batch dispatched to quota lane",
            lane_id=lane.lane_id,
            batch_id=assigned_batch.batch_id,
            virtual_window=state.virtual_window,
            details={"estimated_input_tokens": assigned_batch.estimated_input_tokens},
        )
        dispatch_window.assignments.append(
            DispatchRecord(
                lane_id=lane.lane_id,
                batch_id=assigned_batch.batch_id,
                estimated_input_tokens=assigned_batch.estimated_input_tokens,
            )
        )
        prepared.append((processing_lane, assigned_batch))

    results = await asyncio.gather(*(executor.execute_batch(batch) for _, batch in prepared))
    batch_by_id = {batch.batch_id: batch for _, batch in prepared}
    lane_by_batch_id = {batch.batch_id: lane for lane, batch in prepared}
    result_by_id = {result.batch_id: result for result in results}

    for record in dispatch_window.assignments:
        result = result_by_id[record.batch_id]
        record.status = result.status.value
        record.missing_outputs = len(result.missing_work_item_ids)

    for result in results:
        _apply_result(state, batch_by_id[result.batch_id], lane_by_batch_id[result.batch_id], result)

    state.windows.append(dispatch_window)
    if state.config.checkpointing.enabled:
        _save_checkpoint(state)
    state.virtual_window += 1


def _next_retry_batch_id(state: SimulationState) -> str:
    batch_id = f"retry_{state.retry_batch_counter:03d}"
    state.retry_batch_counter += 1
    return batch_id


def _apply_result(state: SimulationState, batch: Batch, lane: QuotaLane, result: BatchExecutionResult) -> None:
    repo = state.repository
    lane_after = state.lanes[lane.lane_id]
    if result.status == BatchExecutionStatus.failed:
        failed_batch = batch.fail(result.error_code or "BATCH_FAILED")
        repo.record_attempt(
            batch_id=batch.batch_id,
            lane_id=lane.lane_id,
            attempt_number=failed_batch.attempt_count,
            virtual_window=state.virtual_window,
            status=result.status.value,
            error_code=result.error_code,
            input_tokens=batch.estimated_input_tokens,
        )
        if should_retry_batch(failed_batch, state.config.retry.max_attempts):
            retry_batch = mark_for_retry(failed_batch).model_copy(update={"status": BatchStatus.queued})
            state.queued_batches.append(retry_batch)
            repo.upsert_batches([retry_batch])
            repo.update_work_statuses(
                state.config.job_id,
                {item_id: WorkStatus.pending for item_id in batch.work_item_ids},
            )
            repo.record_event(
                job_id=state.config.job_id,
                event_type="batch_requeued",
                message="Failed batch requeued",
                lane_id=lane.lane_id,
                batch_id=batch.batch_id,
                virtual_window=state.virtual_window,
                details={"error_code": result.error_code, "attempt_count": failed_batch.attempt_count},
            )
        else:
            state.terminal_batches[failed_batch.batch_id] = failed_batch
            repo.upsert_batches([failed_batch])
            repo.update_work_statuses(
                state.config.job_id,
                {item_id: WorkStatus.failed for item_id in batch.work_item_ids},
            )
        state.lanes[lane.lane_id] = lane_after.mark_failed()
        repo.upsert_lanes([state.lanes[lane.lane_id]])
        return

    completed_statuses = {item_id: WorkStatus.completed for item_id in result.completed_work_item_ids}
    if completed_statuses:
        repo.update_work_statuses(state.config.job_id, completed_statuses)

    if result.missing_work_item_ids:
        repo.update_work_statuses(
            state.config.job_id,
            {item_id: WorkStatus.missing for item_id in result.missing_work_item_ids},
        )
        parent = batch.model_copy(update={"status": BatchStatus.partially_completed})
        state.terminal_batches[parent.batch_id] = parent
        repo.upsert_batches([parent])
        repo.record_attempt(
            batch_id=batch.batch_id,
            lane_id=lane.lane_id,
            attempt_number=batch.attempt_count,
            virtual_window=state.virtual_window,
            status=result.status.value,
            error_code=result.error_code,
            input_tokens=batch.estimated_input_tokens,
        )
        if state.config.retry.requeue_missing_outputs and batch.attempt_count < state.config.retry.max_attempts:
            retry_batch = create_missing_output_retry_batch(
                parent_batch=batch,
                missing_work_item_ids=result.missing_work_item_ids,
                estimated_tokens_by_id=state.estimated_tokens_by_id,
                retry_batch_id=_next_retry_batch_id(state),
            )
            state.queued_batches.append(retry_batch)
            repo.upsert_batches([retry_batch])
            repo.update_work_statuses(
                state.config.job_id,
                {item_id: WorkStatus.pending for item_id in result.missing_work_item_ids},
            )
            repo.record_event(
                job_id=state.config.job_id,
                event_type="missing_outputs_requeued",
                message="Missing outputs requeued as retry batch",
                lane_id=lane.lane_id,
                batch_id=batch.batch_id,
                virtual_window=state.virtual_window,
                details={"missing_outputs": len(result.missing_work_item_ids)},
            )
        else:
            repo.update_work_statuses(
                state.config.job_id,
                {item_id: WorkStatus.failed for item_id in result.missing_work_item_ids},
            )
    else:
        completed_batch = batch.complete()
        state.terminal_batches[completed_batch.batch_id] = completed_batch
        repo.upsert_batches([completed_batch])
        repo.record_attempt(
            batch_id=batch.batch_id,
            lane_id=lane.lane_id,
            attempt_number=batch.attempt_count,
            virtual_window=state.virtual_window,
            status=result.status.value,
            error_code=result.error_code,
            input_tokens=batch.estimated_input_tokens,
        )

    state.lanes[lane.lane_id] = lane_after.mark_cooldown(state.virtual_window + 1)
    repo.upsert_lanes([state.lanes[lane.lane_id]])


def _save_checkpoint(state: SimulationState) -> None:
    completed = sum(1 for item in state.work_items.values() if item.status == WorkStatus.completed)
    db_items = state.repository.list_work_items(state.config.job_id)
    completed = sum(1 for item in db_items if item.status == WorkStatus.completed)
    failed = sum(1 for item in db_items if item.status == WorkStatus.failed)
    missing = sum(1 for item in db_items if item.status == WorkStatus.missing)
    state.repository.save_checkpoint(
        state.config.job_id,
        state.virtual_window,
        {
            "queued_batches": [batch.batch_id for batch in state.queued_batches],
            "terminal_batches": list(state.terminal_batches),
            "completed_work_items": completed,
            "failed_work_items": failed,
            "missing_outputs": missing,
        },
    )


def _finalize(state: SimulationState) -> SimulationResult:
    db_items = state.repository.list_work_items(state.config.job_id)
    completed_items = sum(1 for item in db_items if item.status == WorkStatus.completed)
    failed_items = sum(1 for item in db_items if item.status == WorkStatus.failed)
    missing_items = sum(1 for item in db_items if item.status == WorkStatus.missing)
    all_batches = state.repository.list_batches(state.config.job_id)
    completed_batches = sum(1 for batch in all_batches if batch.status == BatchStatus.completed)
    failed_batches = sum(1 for batch in all_batches if batch.status == BatchStatus.failed)
    final_status = JobStatus.completed if failed_items == 0 and not state.queued_batches else JobStatus.partially_completed
    if failed_items and completed_items == 0:
        final_status = JobStatus.failed

    state.job = state.job.model_copy(
        update={
            "status": final_status,
            "completed_work_items": completed_items,
            "failed_work_items": failed_items,
            "missing_outputs": missing_items,
        }
    )
    state.repository.upsert_job(state.job)
    state.repository.record_event(
        job_id=state.config.job_id,
        event_type="job_finished",
        message="Simulation job finished",
        virtual_window=max(0, state.virtual_window - 1),
        details={"status": final_status.value},
    )
    return SimulationResult(
        job_id=state.config.job_id,
        work_items=state.job.total_work_items,
        estimated_input_tokens=state.job.total_estimated_input_tokens,
        lane_count=len(state.lanes),
        batches_planned=len(all_batches),
        completed_batches=completed_batches,
        failed_batches=failed_batches,
        missing_outputs=missing_items,
        parallel_lanes_used=max((len(window.assignments) for window in state.windows), default=0),
        estimated_dispatch_windows=len(state.windows),
        estimated_elapsed_minutes=len(state.windows),
        final_status=final_status,
        windows=state.windows,
    )


async def run_simulation_async(
    config: JobConfig,
    *,
    db_path: str | Path,
    reset: bool = False,
    resume: bool = False,
    max_windows: int | None = None,
) -> SimulationResult:
    db_path = Path(db_path)
    repository = SQLiteRepository(db_path)
    if resume:
        state = load_state_for_resume(config, repository, db_path)
    else:
        state = build_fresh_state(config, repository, db_path, reset=reset)
    executor = FakeBatchExecutor(config.simulation)

    windows_run = 0
    while state.queued_batches:
        if max_windows is not None and windows_run >= max_windows:
            break
        await _execute_window(state, executor)
        windows_run += 1
        # If all lanes are permanently failed, stop rather than spinning forever.
        if all(lane.state in {LaneState.failed, LaneState.disabled, LaneState.quota_exhausted} for lane in state.lanes.values()):
            break

    return _finalize(state)


def run_simulation(
    config: JobConfig,
    *,
    db_path: str | Path,
    reset: bool = False,
    resume: bool = False,
    max_windows: int | None = None,
) -> SimulationResult:
    return asyncio.run(
        run_simulation_async(config, db_path=db_path, reset=reset, resume=resume, max_windows=max_windows)
    )
