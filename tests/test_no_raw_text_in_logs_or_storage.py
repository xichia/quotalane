from quotalane.models.work import WorkItem
from quotalane.simulator.engine import run_simulation
from quotalane.storage.repositories import SQLiteRepository


def _sqlite_bytes(db_path):
    paths = [
        db_path,
        db_path.with_name(f"{db_path.name}-wal"),
        db_path.with_name(f"{db_path.name}-shm"),
    ]
    return b"".join(path.read_bytes() for path in paths if path.exists())


def test_work_item_sanitizes_raw_text_metadata():
    item = WorkItem(
        work_item_id="w1",
        external_id="e1",
        input_text_hash="h1",
        estimated_input_tokens=100,
        metadata={
            "raw_text": "SECRET RAW TEXT",
            "prompt": "SECRET PROMPT",
            "safe": "ok",
            "nested": {
                "paragraph_text": "SECRET NESTED RAW TEXT",
                "label": "kept",
            },
            "items": [
                {
                    "full_prompt": "SECRET NESTED PROMPT",
                    "ordinal": 1,
                }
            ],
        },
    )
    assert "raw_text" not in item.metadata
    assert "prompt" not in item.metadata
    assert item.metadata["safe"] == "ok"
    assert "paragraph_text" not in item.metadata["nested"]
    assert item.metadata["nested"]["label"] == "kept"
    assert "full_prompt" not in item.metadata["items"][0]
    assert item.metadata["items"][0]["ordinal"] == 1


def test_no_raw_text_in_storage(small_config, db_path):
    run_simulation(small_config, db_path=db_path, reset=True, max_windows=1)
    raw = _sqlite_bytes(db_path)
    assert b"SECRET RAW TEXT" not in raw
    assert b"paragraph text" not in raw.lower()
    assert b"SECRET_API_KEY_VALUE" not in raw


def test_scheduler_event_details_are_sanitized_before_storage(db_path):
    repo = SQLiteRepository(db_path)
    repo.record_event(
        job_id="job",
        event_type="test",
        message="safe message",
        details={
            "prompt": "SECRET PROMPT",
            "safe_count": 3,
            "nested": {
                "api_key": "SECRET_API_KEY_VALUE",
                "label": "kept",
            },
        },
    )

    event = repo.list_events("job", limit=1)[0]
    assert "SECRET" not in event["details_json"]
    assert "safe_count" in event["details_json"]
    assert "label" in event["details_json"]
    assert b"SECRET" not in _sqlite_bytes(db_path)
