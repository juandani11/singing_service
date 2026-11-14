"""Genera fixtures de audio para el handoff de integracion (no se commitean).

Uso:
    python integration/generate_fixtures.py
    python integration/generate_fixtures.py --include-long

Requiere ffmpeg en PATH para m4a/mp3/aac/ogg. Los WAV se generan con numpy.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

DEFAULT_DIR = Path(__file__).resolve().parent / "fixtures"
RATE = 44100
AMPLITUDE = 0.3


def sine(freq: float, duration: float, rate: int = RATE) -> np.ndarray:
    t = np.arange(int(duration * rate), dtype=np.float64) / rate
    samples = AMPLITUDE * 32767.0 * np.sin(2.0 * np.pi * freq * t)
    return samples.astype(np.int16)


def silence(duration: float, rate: int = RATE) -> np.ndarray:
    return np.zeros(int(duration * rate), dtype=np.int16)


def write_wav(path: Path, samples: np.ndarray, rate: int) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.astype("<i2").tobytes())


def ffmpeg_binary() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise SystemExit("ERROR: ffmpeg no esta en PATH (necesario para m4a/mp3/aac/ogg)")
    return found


def transcode(src: Path, dst: Path, codec: list[str]) -> None:
    subprocess.run(
        [ffmpeg_binary(), "-hide_banner", "-loglevel", "error", "-y",
         "-i", str(src), *codec, str(dst)],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(DEFAULT_DIR))
    parser.add_argument(
        "--include-long",
        action="store_true",
        help="genera long_11min.wav (10.6 MB, 8 kHz) para probar AUDIO_TOO_LONG",
    )
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    wav_440 = out / "sine_440hz_5s.wav"
    write_wav(wav_440, sine(440.0, 5.0), RATE)
    write_wav(out / "sine_442hz_5s.wav", sine(442.0, 5.0), RATE)
    write_wav(out / "silence_3s.wav", silence(3.0), RATE)

    transcode(wav_440, out / "sine_440hz_5s.m4a", ["-c:a", "aac", "-b:a", "128k"])
    transcode(wav_440, out / "sine_440hz_5s.mp3", ["-c:a", "libmp3lame", "-q:a", "4"])
    transcode(wav_440, out / "sine_440hz_5s.aac", ["-c:a", "aac", "-b:a", "128k", "-f", "adts"])
    transcode(wav_440, out / "sine_440hz_5s.ogg", ["-c:a", "libvorbis", "-q:a", "5"])

    if args.include_long:
        # 8 kHz mono para que 660 s quepan bajo el limite de 50 MB.
        write_wav(out / "long_11min.wav", silence(660.0, rate=8000), 8000)

    print(f"fixtures generadas en: {out}")
    for path in sorted(out.iterdir()):
        print(f"  {path.name:<24} {path.stat().st_size / (1024 * 1024):.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
