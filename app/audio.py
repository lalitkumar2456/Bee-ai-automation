from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


def _bundled_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def _invalid(note: str) -> dict:
    return {
        'valid': False, 'duration_seconds': None, 'sample_rate_hz': None,
        'bitrate_kbps': None, 'loudness_db': None, 'analysis_note': note,
    }


def _ffmpeg_metadata(ffmpeg: str, path: Path) -> dict:
    try:
        probe = subprocess.run(
            [ffmpeg, '-hide_banner', '-i', str(path)], capture_output=True,
            text=True, check=False, timeout=30,
        )
        output = probe.stderr
        duration = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', output)
        sample_rate = re.search(r'Audio:.*?(\d+) Hz', output)
        bitrate = re.search(r'bitrate: (\d+(?:\.\d+)?) kb/s', output)
        if not duration or not sample_rate or not bitrate:
            return _invalid('FFmpeg could not read valid audio metadata.')

        hours, minutes, seconds = duration.groups()
        duration_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        loudness_run = subprocess.run(
            [ffmpeg, '-hide_banner', '-nostats', '-i', str(path),
             '-filter_complex', 'ebur128=peak=true', '-f', 'null', '-'],
            capture_output=True, text=True, check=False, timeout=60,
        )
        loudness_values = re.findall(r'\bI:\s*(-?\d+(?:\.\d+)?)\s+LUFS', loudness_run.stderr)
        if not loudness_values:
            return _invalid('FFmpeg could not calculate integrated loudness.')
        return {
            'valid': True,
            'duration_seconds': round(duration_seconds, 2),
            'sample_rate_hz': int(sample_rate.group(1)),
            'bitrate_kbps': float(bitrate.group(1)),
            'loudness_db': float(loudness_values[-1]),
            'analysis_note': 'Metadata and integrated loudness extracted by local FFmpeg (EBU R128).',
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return _invalid(f'Local FFmpeg analysis failed: {error}.')


def inspect_audio(path: Path) -> dict:
    """Return validated audio metadata using the local FFmpeg executable."""
    if not path.is_file() or path.stat().st_size == 0:
        return _invalid('The uploaded audio file is empty or unavailable.')
    ffmpeg = shutil.which('ffmpeg') or _bundled_ffmpeg()
    if not ffmpeg:
        return _invalid('No local FFmpeg executable is available for audio analysis.')
    return _ffmpeg_metadata(ffmpeg, path)
