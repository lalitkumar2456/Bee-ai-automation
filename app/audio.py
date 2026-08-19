from __future__ import annotations
import json, re, shutil, subprocess, wave
from pathlib import Path

def _bundled_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None

def inspect_audio(path: Path) -> dict:
    """Use local ffprobe when available; WAV files also work without FFmpeg."""
    if shutil.which('ffprobe'):
        result = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,bit_rate:stream=sample_rate','-of','json',str(path)],capture_output=True,text=True,check=False)
        try:
            info=json.loads(result.stdout); stream=next((x for x in info.get('streams',[]) if x.get('sample_rate')), {})
            fmt=info.get('format',{}); return {'duration_seconds':round(float(fmt.get('duration',0)),2),'sample_rate_hz':int(stream['sample_rate']) if stream.get('sample_rate') else None,'bitrate_kbps':round(float(fmt['bit_rate'])/1000,1) if fmt.get('bit_rate') else None,'loudness_db':None,'analysis_note':'Duration/rate/bitrate from local ffprobe; loudness requires FFmpeg ebur128.'}
        except (ValueError, KeyError, json.JSONDecodeError): pass
    # The compact imageio-ffmpeg package provides a local FFmpeg binary even
    # when Windows PATH does not contain ffprobe.
    ffmpeg = shutil.which('ffmpeg') or _bundled_ffmpeg()
    if ffmpeg:
        result = subprocess.run([ffmpeg, '-hide_banner', '-i', str(path)], capture_output=True, text=True, check=False)
        output = result.stderr
        duration = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', output)
        sample_rate = re.search(r'Audio:.*?(\d+) Hz', output)
        bitrate = re.search(r'bitrate: (\d+(?:\.\d+)?) kb/s', output)
        if duration:
            hours, minutes, seconds = duration.groups()
            seconds_total = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            return {'duration_seconds':round(seconds_total,2), 'sample_rate_hz':int(sample_rate.group(1)) if sample_rate else None, 'bitrate_kbps':float(bitrate.group(1)) if bitrate else None, 'loudness_db':None, 'analysis_note':'Metadata extracted by bundled local FFmpeg.'}
    if path.suffix.lower()=='.wav':
        with wave.open(str(path),'rb') as a:
            duration=a.getnframes()/a.getframerate(); rate=a.getframerate(); bitrate=a.getframerate()*a.getsampwidth()*8*a.getnchannels()/1000
        return {'duration_seconds':round(duration,2),'sample_rate_hz':rate,'bitrate_kbps':round(bitrate,1),'loudness_db':None,'analysis_note':'WAV metadata calculated locally; install FFmpeg for MP3/M4A analysis.'}
    return {'duration_seconds':None,'sample_rate_hz':None,'bitrate_kbps':None,'loudness_db':None,'analysis_note':'Install FFmpeg or upload WAV to extract metadata locally.'}
