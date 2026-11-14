# Datos de prueba vocales (§12.1 del documento de alcance)

Audios reales necesarios para los tests de Sprint 3–4 y el E2E de Sprint 5.
**No se versionan audios personales**; usar formatos cortos (< 30 s, < 2 MB) y
subirlos como release/adjunto del repo si son pesados.

| Archivo esperado | Descripción | Uso |
|---|---|---|
| `referencia.wav` | 1 frase vocal de referencia (20–30 s) | `reference_file` en tests de integración |
| `intento_afinado.wav` | Ejecución casi afinada → score alto | Validar score alto (§12.1) |
| `intento_desafinado.wav` | Desviaciones deliberadas de pitch | Validar segmentos `out_of_tune` |
| `intento_pausa.wav` | Con pausa/silencio claro | Validar `no_voice` ≠ desafinado (HU-43/46) |

Además se generan **sintéticos** (senoidales 440 Hz, silencio, ruido) en código
para tests unitarios de `pitch.py` (Sprint 3) — no requieren archivo.
