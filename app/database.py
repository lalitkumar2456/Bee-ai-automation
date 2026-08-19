from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", ROOT / "consultbae.db"))

@contextmanager
def connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize_database() -> None:
    with connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS people (
          id INTEGER PRIMARY KEY, canonical_name TEXT NOT NULL, email TEXT UNIQUE, phone TEXT UNIQUE,
          city TEXT, experience_years REAL, current_ctc_inr REAL, applied_date TEXT,
          classification TEXT, classification_status TEXT NOT NULL DEFAULT 'pending',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS person_sources (
          id INTEGER PRIMARY KEY, person_id INTEGER NOT NULL REFERENCES people(id), source_name TEXT NOT NULL,
          source_record_id INTEGER NOT NULL, raw_name TEXT, raw_email TEXT, raw_phone TEXT, match_method TEXT NOT NULL,
          UNIQUE(source_name, source_record_id));
        CREATE TABLE IF NOT EXISTS person_skills (
          id INTEGER PRIMARY KEY, person_id INTEGER NOT NULL REFERENCES people(id), skill TEXT NOT NULL,
          source_name TEXT NOT NULL, UNIQUE(person_id, skill, source_name));
        CREATE TABLE IF NOT EXISTS review_queue (
          id INTEGER PRIMARY KEY, source_name TEXT NOT NULL, source_record_id INTEGER NOT NULL,
          candidate_person_id INTEGER REFERENCES people(id), reason TEXT NOT NULL, payload TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS audio_submissions (
          id INTEGER PRIMARY KEY, person_id INTEGER NOT NULL REFERENCES people(id), file_path TEXT NOT NULL,
          file_name TEXT NOT NULL, duration_seconds REAL, sample_rate_hz INTEGER, bitrate_kbps REAL,
          loudness_db REAL, analysis_note TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
