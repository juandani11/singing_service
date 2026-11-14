"""Preprocesamiento de audio (Sprint 2, plan §4): FFmpeg → WAV 16 kHz mono.

Pipeline: validación de formato/tamaño → conversión FFmpeg (`-map 0:a:0`,
loudnorm) → duración desde el WAV resultante. Archivos temporales borrados
garantizadamente (context manager del caller — RNF-06).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = frozenset(
    {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".mp4", ".mov", ".mkv", ".webm"}
)

_FFMPEG_TIMEOUT_SEC = 120
_FFMPEG_VERSION_TIMEOUT_SEC = 5
_READ_CHUNK = 1024 * 1024


class PreprocessError(Exception):
    """Error de validación/conversión con código tipado (plan §3 punto 3)."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ProcessedAudio:
    path: Path
    duration_sec: float


def resolve_ffmpeg() -> str:
    """Localiza el binario: FFMPEG_BINARY → PATH. Error 500 si falta."""
    env = os.environ.get("FFMPEG_BINARY") or settings.ffmpeg_binary
    if env:
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise PreprocessError(
        "FFMPEG_NOT_FOUND",
        "FFmpeg no está disponible en el entorno (instálalo o define FFMPEG_BINARY)",
        500,
    )


def ffmpeg_version() -> str | None:
    """Versión del binario FFmpeg (para /health); None si no está disponible."""
    try:
        binary = resolve_ffmpeg()
        proc = subprocess.run(
            [binary, "-version"],
            capture_output=True,
            text=True,
            timeout=_FFMPEG_VERSION_TIMEOUT_SEC,
        )
    except (PreprocessError, OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    first = (proc.stdout or "").splitlines()[0] if proc.stdout else ""
    # "ffmpeg version 6.1.1-..." → "6.1.1-..."
    parts = first.split(" version ")
    if len(parts) < 2:
        return None
    return parts[1].split()[0] if parts[1].split() else None


def ensure_supported_extension(filename: str | None) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise PreprocessError(
            "UNSUPPORTED_FORMAT",
            f"Formato no soportado: {ext or 'desconocido'}; permitidos: "
            + ", ".join(sorted(ALLOWED_EXTENSIONS)),
            400,
        )
    return ext


async def read_capped(upload: UploadFile, max_bytes: int) -> bytes:
    """Lee el upload por chunks cortando en el límite (evita agotar memoria)."""
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(_READ_CHUNK):
        total += len(chunk)
        if total > max_bytes:
            raise PreprocessError(
                "AUDIO_TOO_LARGE",
                f"Archivo mayor al límite de {max_bytes // (1024 * 1024)} MB",
                413,
            )
        chunks.append(chunk)
    return b"".join(chunks)


def convert_to_wav16k(src: Path, dst: Path) -> None:
    """Extrae la pista de audio y la normaliza a WAV 16 kHz mono (loudnorm)."""
    cmd = [
        resolve_ffmpeg(),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-map",
        "0:a:0",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-ac",
        "1",
        "-ar",
        str(settings.sample_rate),
        str(dst),
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_FFMPEG_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        raise PreprocessError(
            "CONVERT_TIMEOUT",
            "La conversión de audio superó el tiempo máximo",
            400,
        ) from exc
    except OSError as exc:  # FFMPEG_BINARY inválido o binario inexistente
        raise PreprocessError(
            "FFMPEG_NOT_FOUND",
            f"No se pudo ejecutar FFmpeg ({cmd[0]}); revisa FFMPEG_BINARY o el PATH",
            500,
        ) from exc

    if proc.returncode != 0:
        stderr = (proc.stderr or "").lower()
        if "matches no streams" in stderr or "does not contain any stream" in stderr:
            raise PreprocessError(
                "NO_AUDIO_TRACK",
                "El archivo no contiene una pista de audio",
                400,
            )
        # Codec/contenedor no soportado por el FFmpeg instalado → UNSUPPORTED_FORMAT;
        # datos corruptos → INVALID_AUDIO (ambos 400).
        if any(
            token in stderr
            for token in ("decoder", "codec", "unsupported", "not supported")
        ):
            raise PreprocessError(
                "UNSUPPORTED_FORMAT",
                "El formato/codec del audio no se puede decodificar",
                400,
            )
        raise PreprocessError("INVALID_AUDIO", "No se pudo decodificar el audio", 400)


def wav_duration_sec(path: Path) -> float:
    try:
        with wave.open(str(path), "rb") as w:
            rate = w.getframerate()
            frames = w.getnframes()
    except (OSError, EOFError, wave.Error) as exc:
        # FFmpeg no produjo un WAV legible (salida ausente o corrupta)
        raise PreprocessError(
            "INVALID_AUDIO",
            "El audio convertido no es un WAV válido",
            400,
        ) from exc
    if rate <= 0 or frames <= 0:
        raise PreprocessError("EMPTY_AUDIO", "El audio no contiene muestras", 400)
    return frames / rate


def preprocess_bytes(
    data: bytes, filename: str | None, *, tmp_dir: Path, name: str
) -> ProcessedAudio:
    """Valida y convierte bytes subidos → WAV 16 kHz mono dentro de `tmp_dir`."""
    ext = ensure_supported_extension(filename)
    if not data:
        raise PreprocessError("EMPTY_FILE", "Archivo vacío", 400)

    # sufijo `_in` para que src != dst cuando el original ya es .wav
    src = tmp_dir / f"{name}_in{ext}"
    dst = tmp_dir / f"{name}.wav"
    src.write_bytes(data)

    convert_to_wav16k(src, dst)
    duration = wav_duration_sec(dst)

    if duration > settings.max_duration_sec:
        raise PreprocessError(
            "AUDIO_TOO_LONG",
            f"Duración de {duration:.1f}s supera el máximo de {settings.max_duration_sec}s",
            413,
        )
    return ProcessedAudio(path=dst, duration_sec=duration)
