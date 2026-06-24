from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL,
    total_work_items INTEGER NOT NULL,
    completed_work_items INTEGER NOT NULL,
    failed_work_items INTEGER NOT NULL,
    missing_outputs INTEGER NOT NULL,
    total_estimated_input_tokens INTEGER NOT NULL,
    checkpoint_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS work_items (
    work_item_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    external_id TEXT NOT NULL,
    input_text_hash TEXT NOT NULL,
    estimated_input_tokens INTEGER NOT NULL,
    metadata_json TEXT NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS batches (
    batch_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    lane_id TEXT,
    work_item_ids_json TEXT NOT NULL,
    estimated_input_tokens INTEGER NOT NULL,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL,
    parent_batch_id TEXT,
    error_code TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS lanes (
    lane_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    api_key_env_name TEXT,
    requests_per_minute INTEGER NOT NULL,
    input_tokens_per_minute INTEGER NOT NULL,
    safe_input_token_target INTEGER NOT NULL,
    hard_input_token_cap INTEGER NOT NULL,
    daily_request_limit INTEGER,
    daily_token_limit INTEGER,
    state TEXT NOT NULL,
    cooldown_until_window INTEGER,
    in_flight_batch_id TEXT,
    requests_used_current_window INTEGER NOT NULL,
    input_tokens_used_current_window INTEGER NOT NULL,
    current_window INTEGER NOT NULL,
    requests_used_today INTEGER NOT NULL,
    input_tokens_used_today INTEGER NOT NULL,
    last_request_window INTEGER,
    failure_count INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS batch_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT NOT NULL,
    lane_id TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    virtual_window INTEGER NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    input_tokens INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduler_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    lane_id TEXT,
    batch_id TEXT,
    virtual_window INTEGER,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    virtual_window INTEGER NOT NULL,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: str | Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()
