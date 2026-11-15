"""Configuración del servicio por variables de entorno (pydantic-settings)."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes operativos del microservicio.

    Vía env sin prefijo: HOP_LENGTH, CENT_THRESHOLD, MAX_FILE_MB, etc.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "singing-service"
    version: str = "0.3.0"

    # Almacén stateless con TTL para analysis_id (plan §2.1)
    analysis_ttl_seconds: int = 3600

    # Binario FFmpeg (opcional): env FFMPEG_BINARY o `.env`
    ffmpeg_binary: str | None = None

    # Algoritmo (Sprints 3-4)
    sample_rate: int = 16000  # WAV de trabajo: preprocess (-ar) + pitch (sr) + hop_ms
    hop_length: int = 512
    cent_threshold: int = 50

    # Límites de subida (Sprint 0 — gap O2: 50 MB / 10 min)
    max_duration_sec: int = 600
    max_file_mb: int = 50

    # Concurrencia (Sprint 5, hardening): FFmpeg + pyin son costosos; cola
    # limitada por semáforo → 429 SERVICE_BUSY si se llena.
    # Límites con Field: un env inválido falla al arrancar, no por request (500).
    max_concurrent_analyses: int = Field(default=2, ge=1)
    busy_timeout_sec: float = Field(default=30.0, ge=0)


settings = Settings()
