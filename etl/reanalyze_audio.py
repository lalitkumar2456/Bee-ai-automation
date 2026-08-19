"""Populate metadata for recordings uploaded before FFmpeg became available."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.audio import inspect_audio
from app.database import connection


def run() -> None:
    updated = 0
    with connection() as conn:
        rows = conn.execute('SELECT id, file_path FROM audio_submissions').fetchall()
        for row in rows:
            metadata = inspect_audio(ROOT / 'uploads' / row['file_path'])
            conn.execute(
                '''UPDATE audio_submissions
                   SET duration_seconds=?, sample_rate_hz=?, bitrate_kbps=?, loudness_db=?, analysis_note=?
                   WHERE id=?''',
                (metadata['duration_seconds'], metadata['sample_rate_hz'], metadata['bitrate_kbps'],
                 metadata['loudness_db'], metadata['analysis_note'], row['id']),
            )
            updated += 1
    print(f'Re-analyzed {updated} recording(s).')


if __name__ == '__main__':
    run()
