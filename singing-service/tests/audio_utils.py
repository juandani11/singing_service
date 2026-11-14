"""Utilidades de audio para tests: tonos sintéticos y transcodificación FFmpeg."""

from __future__ import annotations

import io
import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from app.services.preprocess import PreprocessError, resolve_ffmpeg

RATE = 16000
CENTS_80_HZ = 460.8  # 440 * 2^(80/1200)


def tone_wav(
    duration: float = 3.0,
    freq: float = 440.0,
    silence: float = 0.5,
    rate: int = RATE,
) -> bytes:
    """WAV mono: `silence` s de silencio + tono puro hasta `duration`."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        silence_frames = int(silence * rate)
        for i in range(int(duration * rate)):
            if i < silence_frames:
                sample = 0
            else:
                sample = int(10000 * math.sin(2 * math.pi * freq * i / rate))
            frames += struct.pack("<h", sample)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def ffmpeg_available() -> bool:
    try:
        resolve_ffmpeg()
        return True
    except PreprocessError:
        return False


def transcode(data: bytes, src_name: str, dst_name: str) -> bytes:
    """Transcodifica bytes con FFmpeg (p. ej. WAV → M4A/AAC o MP3)."""
    with tempfile.TemporaryDirectory(prefix="syncdance-test-") as tmp:
        src = Path(tmp) / src_name
        dst = Path(tmp) / dst_name
        src.write_bytes(data)
        codec = _codec_args(dst.suffix.lower())
        subprocess.run(
            [resolve_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(src), *codec, str(dst)],
            check=True,
            capture_output=True,
        )
        return dst.read_bytes()


def _codec_args(suffix: str) -> list[str]:
    if suffix in {".m4a", ".aac"}:
        return ["-c:a", "aac", "-b:a", "128k"]
    if suffix == ".mp3":
        return ["-c:a", "libmp3lame", "-q:a", "4"]
    if suffix == ".ogg":
        return ["-c:a", "libvorbis"]
    return []
