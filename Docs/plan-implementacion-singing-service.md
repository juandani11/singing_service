# Plan de Implementación — `singing-service` (Microservicio de Voz)

**Proyecto:** SyncDance AI · Ingeniería de Software I · Grupo 7 · Septiembre 2026
**Área:** EP-08 Análisis vocal multimodal (RF-37 a RF-40, HU-43 a HU-47)
**Fuente:** *SyncDance AI — Requisitos y Alcance Propuesto* (v1.0) + guía operativa del equipo (herramientas fijas).
**Sprints:** 2 semanas c/u (supuesto §1.1). Sprints 0–5 + Post-MVP.

---

## 1. Alcance, rol y encaje en Scrum

Trabajo **exclusivamente en `/singing-service`** del monorepo, rama `feature/singing-microservice`, PR hacia `develop`/`main`. No toco el backend Django (conflictos casi nulos). El servicio:

- **No implementa JWT ni roles**: asume llamadas validadas en la red interna de Docker (decisión acordada del equipo).
- Endpoint interno: `http://singing-service:5000/api/v1/analyze` (URL fijada por el equipo).
- Swagger interactivo `http://localhost:5000/docs` = **contrato vivo** para el compañero de Django.
- Herramientas fijas: **FastAPI · Uvicorn · librosa (pyin) · NumPy/SciPy · FastDTW · Pydub/FFmpeg · Docker · Pytest · Postman/Swagger** (PyTorch/CREPE opcional).

### 1.1 Decisión de planificación (mejora sobre la guía) y transparencia Scrum

La guía del equipo concentra el algoritmo en Sprint 5; el documento de alcance dice que el análisis vocal es P2 y *"posterior al núcleo de baile, **si el tiempo lo permite**"* (§3.3) y §3.2 paso 8: combinar resultados *"cuando el alcance de baile ya sea estable"*. Por eso este plan:

1. **Adelanta el algoritmo a Sprints 3–4** con feature-flag `mock|real`, dejando S5 para integración Celery + E2E + demo. Razones: S5 ya concentra HU-42, hardening, pruebas E2E y demo final; HU-43 (8) + HU-44 (5) + HU-45 (8) = 21 SP no caben en 2 semanas junto con integración; y el §12.1 exige datos de prueba vocales que conviene tener temprano.
2. **Transparencia:** el backlog oficial asigna HU-43…47 al *Sprint 5*. Mi avance en S3–S4 se registra como **tasks/subtareas dentro de esas HUs** (o refino de historias), comunicado en planning/daily al PO y Scrum Master, para no falsear el estado del Sprint Backlog. Las HUs se declaran *terminadas* recién cuando se integran y validan en S5.
3. **Fallback estricto:** si el equipo prefiere la guía literal (algoritmo solo en S5), invierto S3–S4 en robustecer pipeline + tests + benchmark y comprimo el algoritmo en S5 con **solo pitch + score básico** (recortando HU-46 y DTW fino). Alternativa de mayor riesgo; se cambia solo por decisión del líder.

### 1.2 Relación con las historias del equipo

| HU del core (Sprint oficial) | Depende de mí | Qué entrego |
|---|---|---|
| HU-43 Extraer audio y pitch (8 SP, S5) | Sí — RF-37 | Curva F0 temporal; distingue sin-voz vs. desafinado |
| HU-44 Alinear referencia vocal (5 SP, S5) | Sí — RF-38 | Alineación DTW alumno↔referencia con tolerancia a desfase |
| HU-45 Calcular afinación y errores (8 SP, S5) | Sí — RF-38 | Diferencia tonal por segmento, timestamps, score vocal 0–100 documentado |
| HU-46 Mostrar feedback vocal (5 SP, S5) | Parcial — RF-39 | JSON de segmentos + mensajes que diferencian sin-voz de desafinación (UI en Flutter) |
| HU-47 Evaluación multimodal (5 SP, S5) | Parcial — RF-40 | `scores.vocal` como insumo; ponderación y persistencia en el Core |
| HU-15 / HU-18 (carga y encolado, S2) | Contract-only | El Core me envía audio/video del intento por HTTP interno |

---

## 2. Arquitectura objetivo y contrato de API

### 2.1 Estructura del servicio (monorepo `/singing-service`)

```
/singing-service
├── app/
│   ├── main.py                 # FastAPI app, routers, /health, /docs
│   ├── api/
│   │   ├── routes/analyze.py   # POST /api/v1/analyze, GET /api/v1/analyze/{id}
│   │   └── deps.py
│   ├── core/config.py          # settings por env: umbrales, hop_length, flags, TTL
│   ├── schemas/                # Pydantic request/response (contrato OpenAPI)
│   ├── services/
│   │   ├── preprocess.py       # FFmpeg/pydub: m4a/mp3/video → wav 16 kHz mono
│   │   ├── pitch.py            # librosa.pyin → serie F0 + voiced/unvoiced
│   │   ├── align.py            # FastDTW sobre features de pitch
│   │   ├── scoring.py          # cents, umbrales, segmentación, score vocal
│   │   └── feedback.py         # reglas mensaje → segmento (HU-46)
│   └── mock/data.py            # respuestas simuladas (Sprints 1–4)
├── tests/
│   ├── fixtures/audios/        # 1 referencia + 2 intentos (§12.1) + sintéticos
│   ├── test_contract.py        # snapshot OpenAPI + validación de schema
│   ├── test_preprocess.py
│   ├── test_pitch.py
│   ├── test_align.py
│   ├── test_scoring.py
│   └── test_api.py             # integración multipart extremo a extremo
├── Dockerfile                  # python-slim + ffmpeg (multi-stage), Uvicorn
├── requirements.txt            # versiones fijadas
├── postman_collection.json     # colección para pruebas del equipo
└── README.md                   # ejecución local y vía docker-compose + scoring.md
```

**Estado interno: stateless.** El servicio no tiene base de datos (evita migraciones y duplicidad de verdad): los resultados se guardan en un almacén ligero con **TTL** (dict/LRU por proceso o archivo temporal JSON) y la **fuente de verdad es el Core**, que persiste el JSON en PostgreSQL. Si el proceso se reinicia, el Core reintenta el `GET` y, si no encuentra el `analysis_id`, relanza el `POST` (idempotencia por `attempt_id`).

### 2.2 Contrato OpenAPI (v1) — se congela en Sprint 1

**`POST /api/v1/analyze`** — `multipart/form-data`
- `file`: audio o video del intento (`.m4a`, `.mp3`, `.wav`, `.mp4`/`.mov`; del video se extrae la pista con FFmpeg)
- `reference_file`: audio de referencia de la rutina (origen: ver §3, punto 1)
- `attempt_id`, `routine_id`: correlación con el Core
- `mode`: `mock | real` (flag; default `mock` hasta Sprint 4)
- **Respuesta `202 Accepted`:** `{ "analysis_id", "status": "queued|completed|failed" }`

**`GET /api/v1/analyze/{analysis_id}`** → resultado completo:

```json
{
  "analysis_id": "...", "attempt_id": "...", "routine_id": "...",
  "status": "completed", "algorithm_version": "1.0.0",
  "duration_sec": 34.2,
  "pitch": {
    "student":  [{ "t": 0.04, "f0": 220.4, "voiced": true }],
    "reference":[ "..."],
    "hop_ms": 46
  },
  "segments": [
    { "start": 12.0, "end": 12.6, "type": "out_of_tune",
      "expected_note": "E4", "sung_note": "F#4", "delta_cents": 45, "severity": "high" },
    { "start": 27.1, "end": 28.0, "type": "no_voice", "delta_cents": null, "severity": "info" }
  ],
  "scores": { "vocal": 71, "afinacion": 71, "estabilidad": 66, "control_volumen": 80, "silence_pct": 4 },
  "feedback": [
    { "code": "SUSTAIN_2ND_BAR", "message": "Sostén la afinación en el segundo compás: hasta 72 cents de desviación." },
    { "code": "LOW_VOLUME_ENTRY", "message": "Detectamos 4% del tiempo sin voz; es distinto a una desafinación." }
  ],
  "timings": { "preprocess_ms": 180, "pitch_ms": 640, "dtw_ms": 210, "scoring_ms": 30 }
}
```

**`GET /health`** → `{ "status": "ok", "version": "1.0.0" }` (health check del compose).

Decisiones del contrato:
- **`202 + GET`** en vez de un POST gigante: el worker de Celery puede reintentar el GET sin re-procesar (idempotencia; afín a HU-17 y RNF-07).
- `type: out_of_tune | no_voice` → CAs de HU-43 y HU-46 (distinguir ausencia de voz de desafinación).
- `algorithm_version` + `timings` → trazabilidad exigida por HU-20/RF-25 y métrica §15.1 (tiempo medio de procesamiento).
- `severity` ordenado → soporta el ranking "errores más relevantes primero" de HU-31/RF-26 aplicado a lo vocal.
- Sin autenticación: solo red interna (documentado como decisión y como riesgo aceptado).

---

## 3. Puntos de coordinación con el equipo

1. **Origen del audio de referencia:** opción recomendada — el Core extrae la pista del video maestro durante el preprocesamiento (HU-19/RF-16) y me la envía en `reference_file`. Alternativa aceptada por el contrato: acepto también *video* de referencia (mismo `preprocess`). **Acordar en el refinement de Sprint 1.**
2. **HU-47 / ponderación:** mi servicio expone `scores.vocal`; la fórmula combinada (p. ej. 60/40) y su documentación viven en el Core. *Opcional:* exponer `POST /api/v1/combine` si el líder prefiere el cálculo de mi lado — decidir el día 1 de S5. Requisito inamovible: los scores individuales siguen visibles (CA de HU-47).
3. **Timeouts y reintentos:** Core llama con timeout de 60 s; 2 reintentos con backoff; luego marca `failed`. Yo nunca devuelvo 500 crudos: errores tipados (400/413/415/422) con `code` y mensaje.
4. **Persistencia:** el Core guarda el JSON de resultado en PostgreSQL (RF-25); mi TTL local es solo caché operativa.
5. **HU-48 (notificación):** el Core notifica; se apoya en mi `GET .../{id}` para saber cuándo el análisis está `completed`.
6. **Datos de prueba compartidos (§12.1):** 1 referencia vocal + 2 intentos con diferencias de pitch conocidas + 1 caso con pausa larga; los conservo en `tests/fixtures` y los comparto con el equipo para el E2E de S5.
7. **Evidencia para demo:** publicaré la URL de `/docs` y la colección Postman en cada Sprint Review.

---

## 4. Plan por sprints

### Sprint 0 — Fundación técnica (§9.1 del doc + mi esqueleto)
**Meta del equipo:** repo, ramas, Docker, Django/Angular/Flutter, PostgreSQL, Redis/Celery, health checks, CI básica, convenciones.

1. Rama `feature/singing-microservice` + scaffold FastAPI (`/health` + `/docs`).
2. `Dockerfile` (python-slim + **ffmpeg**, multi-stage) y servicio `singing-service` **añadido al `docker-compose.yml` raíz** (red interna, puerto 5000).
3. `requirements.txt` fijado; linters (ruff/black); `pytest` smoke; CI verde.
4. README con pasos reproducibles; convenciones de commit/PR alineadas con el equipo.

**Incremento:** `docker-compose up` levanta Core + `singing-service` y el health check responde.
**DoD:** PR revisado, CI verde, sin secretos versionados.

### Sprint 1 — Contrato OpenAPI + mock (entrega a Django)
**Meta del equipo:** HU-01 a HU-12 (usuarios, rutinas, asignaciones).

1. Modelar todo el contrato con Pydantic (§2.2) → OpenAPI autogenerado en `/docs`.
2. `mode=mock`: respuestas estáticas coherentes con el prototipo Figma (score 71, segmentos 00:12/00:27/00:41, feedback HU-46).
3. Estructura modular `services/` con firmas tipadas (stubs mock).
4. `test_contract.py`: snapshot del esquema OpenAPI (detecta cambios incompatibles en PR) + validación de la respuesta mock contra el schema.
5. **Colección Postman** de los 3 endpoints + publicar `/docs` al equipo; **refinement con Django** (campos necesarios para HU-46/HU-47; origen del audio de referencia, punto 1 de §3).
6. Capturar/almacenar los audios de prueba de §12.1.

**Incremento:** contrato congelado v1 → Django escribe su worker/cliente contra el mock.
**Riesgo controlado:** cambios de contrato sólo hasta el cierre de este sprint.

### Sprint 2 — Pipeline de preprocesamiento de audio
**Meta del equipo:** HU-13 a HU-20 (captura, carga, colas, preprocesamiento maestro).

1. `preprocess.py`: FFmpeg/pydub → **wav 16 kHz mono, normalizado**; extracción de pista desde video (`-vn`), porque el intento llega como video (HU-13/RF-11).
2. Validaciones: formato, tamaño, duración → errores tipados (400/413/415); audio sin pista → `code: NO_AUDIO_TRACK`.
3. Archivos temporales con limpieza garantizada (context manager, `finally`) — RNF-06; límite de concurrencia (semáforo o workers Uvicorn).
4. `mode=real` parcial: recibe y preprocesa, devuelve metadata real (`duration_sec`, sample rate) + resto mock.
5. Tests: mp3→wav, m4a→wav, video→wav, corrupto, duración excesiva. Logs estructurados con `attempt_id` (RNF-03).
6. Benchmark preliminar de conversión (métrica a monitorear).

**Incremento:** el Core me envía un archivo real de un intento y recibe metadata válida.

### Sprint 3 — Extracción de pitch (HU-43 / RF-37)
**Meta del equipo:** HU-21 a HU-30 (núcleo IA de baile).

1. `pitch.py` con **`librosa.pyin`** → serie F0 + prob. voiced; `fmin≈65`, `fmax≈1047`, `hop_length` configurable (≈46 ms por frame).
2. Detección de **segmentos sin voz** (voiced=false sostenido > N frames) ≠ notas desafinadas → CA de HU-43.
3. Serialización a `pitch.student/reference`; downsampling defensivo del payload si crece demasiado.
4. Feature-flag: `mode=real` completa `pitch`, el resto sigue en mock.
5. Tests: senoidales sintéticas (440 Hz → ±5 cents), silencio → `no_voice`, ruido sin crash; **benchmark: objetivo < 2 s para audio de 40 s en CPU** (registrado en `timings`).
6. PoC CREPE opcional solo si sobra tiempo: documentar comparación, no bloquear.

**Incremento:** curva F0 real de los audios de §12.1.
**🎯 Punto de decisión intermedio (go/no-go):** revisar con PO/líder si el núcleo de baile (S3 del equipo) va estable y si mi velocidad lo permite → confirma el camino a S4/S5. Si no, aplicar §1.1 punto 3 (plan estricto) u Opción B del §8.

### Sprint 4 — Alineación, desviaciones y score vocal (HU-44, HU-45, base HU-46 / RF-38, RF-39)
**Meta del equipo:** HU-31 a HU-41 (feedback y visualización).

1. `align.py`: **FastDTW** sobre features de pitch (F0 en cents/log-Hz + bin voiced) → mapeo timestamps alumno↔referencia **tolerando desfase de inicio** (CA de HU-44); mapeo incluido en la respuesta (asociado al intento).
2. `scoring.py`: diferencia en **cents** por frame alineado → agrupación en segmentos (sin eventos redundantes del mismo error continuo, patrón HU-27), **umbrales configurables por env** (p. ej. 50 cents), ranking por `severity`.
3. **Score vocal 0–100 con fórmula documentada** en `README/docs/scoring.md` (CA de HU-45: score *documentado*): p. ej. `100 − media(cents_error ponderados) − penalización_silencio`, acotado [0,100]; test de reproducibilidad (misma entrada → mismo score).
4. `feedback.py`: reglas → mensajes (RF-39) diferenciando `no_voice` de `out_of_tune`, priorizando lo más relevante.
5. `mode=real` completo; tests de integración API con los audios de §12.1 (desfase conocido, diferencias conocidas, pausa/sin voz).
6. Cierre de **HU-46** si hay capacidad (su parte backend); si no, queda `feedback` con mensajes básicos y se termina en S5.

**Incremento:** un archivo real produce `segments`, `scores` y `feedback` completos sin mock.

### Sprint 5 — Integración multimodal + cierre (HU-47 / RF-40, HU-46 pendiente, E2E, demo)
**Meta del equipo:** HU-42 a HU-48, hardening, pruebas E2E y demo final.

1. **Integración Core ↔ servicio:** worker Celery llama `POST /api/v1/analyze` y consolida el JSON en la DB; timeouts/reintentos según §3 punto 3.
2. **HU-47:** entregar `scores.vocal` en el formato acordado; ponderación documentada en el Core; verificar scores individuales por separado (CA). Endpoint `/combine` solo si se decidió en §3 punto 2.
3. Completar HU-46 pendiente (mensajes/segmentos) si se postergó.
4. **Contract test E2E** con §11: *una ejecución con audio produce pitch, comparación, score vocal y feedback sin romper el flujo de baile*.
5. Hardening: timeouts, payload grande, audio sin pista, reinicio del servicio (TTL) → reintentos OK; cierre de workers; colección Postman final; README/scoring finales.
6. **Métricas para la demo (§15.1):** tiempo medio de procesamiento por intento vocal (`timings`) y % de éxito de la tanda de prueba.
7. Demo integrada: cuenta nueva → intento con audio → resultado vocal consultado en la app.

**Incremento:** entrega final del área de canto.

---

## 5. Resumen del plan y carga

| Sprint | Enfoque del `singing-service` | HU soportadas | Modo | Carga propia (est.) |
|---|---|---|---|---|
| 0 | Scaffold + Docker + compose + health | — (infra) | — | 3 SP |
| 1 | Contrato OpenAPI v1 + mock + `/docs` + Postman | contract-only | mock | 5 SP |
| 2 | Preprocesamiento FFmpeg/pydub | soporta HU-15/HU-18 | mock + metadata real | 8 SP |
| 3 | Pitch `librosa.pyin` + sin-voz + benchmark | HU-43 (RF-37) | real en `pitch` | 8 SP |
| 4 | FastDTW + cents + score + reglas feedback | HU-44, HU-45, base HU-46 (RF-38/39) | real completo | 13 SP (+5 si entra HU-46) |
| 5 | Integración Celery + HU-47 + hardening + E2E + demo | HU-47 (RF-40), cierre HU-46 | real + E2E | 10–13 SP |

**Nota sobre SP:** las estimaciones por HU (21 SP de vocal) son del backlog del equipo; la carga por sprint de arriba es mi esfuerzo individual orientativo. Recalibrar tras Sprint 1 con la velocidad real (§8 del doc).

**Secuencia de valor:** S1 deja el contrato entregable desde la semana 1 → S2 ya recibe archivos reales → S3–S4 construyen el algoritmo con tests → S5 sólo conecta. Si algo se retrasa, el contrato mock de S1 mantiene al Core desbloqueado.

---

## 6. Trazabilidad HU/RF → endpoint/función → test → sprint (patrón §10)

| HU | RF | Endpoint / función | Test principal | Sprint (plan) |
|---|---|---|---|---|
| HU-43 | RF-37 | `POST /analyze` + `services/pitch.py` | `test_pitch.py` (sintéticas, silencio, ruido) | S3 |
| HU-44 | RF-38 | `services/align.py` (FastDTW) | `test_align.py` (desfase conocido) | S4 |
| HU-45 | RF-38 | `segments` + `scores.vocal` (`scoring.py`) | `test_scoring.py` (cents, umbrales, score reproducible) | S4 |
| HU-46 | RF-39 | `segments.type` + `feedback` (`feedback.py`) | `test_contract.py` + `test_api.py` (no_voice ≠ out_of_tune) | S4–S5 |
| HU-47 | RF-40 | `scores.vocal` (input Core) / `POST /combine` opcional | `test_api.py` E2E + contrato con Django | S5 |
| HU-20/RF-25 (soporte) | RF-25 | `algorithm_version`, `timings` | snapshot contract | S1+ |

---

## 7. Estrategia de pruebas (§12) y RNF aplicados (§13)

| Nivel | Qué pruebo | Ejemplos |
|---|---|---|
| Unitaria (Pytest) | Algoritmos aislados | `pyin` con senoidales 440 Hz; cálculo de cents; umbrales; fórmula del score; reglas de feedback |
| Integración | Pipeline interno completo | mp3/m4a/video → preprocess → pitch → DTW → scoring → JSON |
| Contrato | OpenAPI estable | snapshot del esquema; mock y real validados contra Pydantic |
| API | Endpoints multipart | Postman/Swagger: válido, formato inválido, archivo grande, sin pista de audio |
| IA/Algoritmo | Consistencia | audios con desfase y diferencias de pitch **conocidos** (§12.1) |
| Rendimiento | CPU/latencia | < 2 s por audio de 40 s; `timings` en cada respuesta |

**Datos de prueba (§12.1):** 1 referencia vocal corta; 1 intento casi afinado (score alto); 1 intento con desviaciones deliberadas; 1 caso con pausa larga para `no_voice`; (1 video con pérdida de landmarks aplica al equipo, no a mí).

**RNF relevantes a mi servicio:**
- **RNF-01:** sin HTTPS interno (red Docker aislada) — aceptado y documentado; nada de secretos en Git.
- **RNF-03:** logs estructurados por `attempt_id`; errores rastreables en `timings` y `status`.
- **RNF-05:** entorno reproducible con Docker multi-stage.
- **RNF-06 (privacidad):** audio/video solo en storage temporal, **borrado al terminar el análisis**; no se persiste audio; logs sin PII.
- **RNF-07 (resiliencia):** un fallo no corrompe el intento → `status: failed` con `code`, diagnosticable y reintentable desde el Core.
- **RNF-02/RNF-04:** análisis fuera del request vía worker del Core; servicios de dominio separables (`services/`).

---

## 8. Riesgos, mitigación y plan contingente

| Riesgo | Impacto | Mitigación |
|---|---|---|
| S4 concentra HU-44+45 (13 SP) + HU-46 | Atraso en S5 | `pitch.py` listo a fin de S3; **Plan A:** HU-46 completa en S4 · **Plan B (ejecutar si go/no-go de S3 falla):** S4 sólo HU-44+45 y HU-46 (mensajes básicos) va a S5 |
| El núcleo de baile (S3 del equipo) no queda estable | El §3.2 condiciona el vocal a eso | Gate go/no-go al cierre de S3; **Opción B:** mantener contrato + mock + preprocess y demo vocal con datos sintéticos, sin integración E2E |
| Latencia de `librosa.pyin` | Timeout desde Celery | Benchmark por PR; ajuste de `hop/frame`; límite de duración; contrato `202+GET` |
| Imagen Docker con FFmpeg pesada | CI lento | Multi-stage + capas cacheadas |
| Cambios tardíos de contrato | Re-trabajo en ambos lados | Congelar OpenAPI en S1 + contract tests en CI |
| Servicio expuesto sin auth | RNF-01 | Solo red interna; puerto 5000 no publicado fuera del compose |
| Fallo del servicio tras `202` | Análisis perdido | TTL + reintento del Core con `attempt_id` idempotente (RNF-07) |
| Velocidad real < estimada | Desvíos | Recalibrar SP en S1; recortar primero PoC CREPE y luego HU-46 (nunca HU-43/44/45) |
| Post-MVP (HU-49) | — | Fuera de alcance; el contrato v1 no debe impedir añadir export después |

---

## 9. Ceremonias y control del avance (§15)

- **Daily:** estado de mi tarea en la rama, bloqueos de contrato con Django, avance de HUs de S5 (transparencia §1.1).
- **Sprint Planning:** mis HUs oficiales son de S5; mis tasks de S0–S4 salen de ellas.
- **Backlog Refinement (S1):** congelar contrato con Django + origen del audio de referencia.
- **Sprint Review:** S1 → demo de `/docs` + mock; S3 → primera curva F0 real; S4 → score real sobre audios de prueba; S5 → E2E completo.
- **Retrospective:** métricas — *tiempo medio de procesamiento vocal* y *% de éxito en la tanda de prueba* (§15.1).

---

## 10. Definition of Done adaptada al microservicio

- [ ] PR a `develop` con revisión de ≥1 integrante.
- [ ] `pytest` verde en CI (unit + integración + contract snapshot).
- [ ] `/docs` actualizado y refleja el contrato real.
- [ ] Respuesta con `attempt_id`, `algorithm_version` y `timings`.
- [ ] Errores tipados (sin 500 crudos); `failed` diagnosticable y reintentable.
- [ ] Archivos temporales de audio borrados tras el análisis (RNF-06).
- [ ] Sin secretos versionados; configuración por variables de entorno.
- [ ] README reproducible (`docker-compose up`) + `docs/scoring.md` con la fórmula del score.
- [ ] Trazabilidad actualizada (§6) y colección Postman vigente.

---

## Registro de avance

| Fecha | Sprint | Evidencia / resultado |
|---|---|---|
| 06/10/2026 | **S0 — completado** | Scaffold `singing-service/` (FastAPI + `/health` + `/docs`, config por env, paquetes `services/`, `schemas/`, `mock/`). Verificación: `pytest` 3/3 OK · `ruff check` OK · imagen Docker multi-stage (python:3.14-slim + FFmpeg, no root, HEALTHCHECK) construida · `docker compose up` → `/health` = `{"status":"ok","service":"singing-service","version":"1.0.0","mode":"mock"}` y `/docs` = 200. **Pendiente de contexto de equipo:** mover al monorepo, integrar al compose raíz (red interna) e iniciar rama `feature/singing-microservice`. |
| 06/10/2026 | **S1 — completado + revisado** | Contrato OpenAPI v1 modelado con Pydantic (`app/schemas/analyze.py`): `AcceptedResponse`, `PitchPoint/PitchCurves`, `Segment` con validación cruzada `out_of_tune` ↔ `no_voice`, `Scores` 0–100, `FeedbackItem`, `Timings`, `AnalysisResult`. Endpoints `POST /api/v1/analyze` (202, multipart, idempotencia por `attempt_id`) y `GET /api/v1/analyze/{id}` (404 tipado). Mock coherente con Figma: score 71, segmentos 12.0/27.1/41.0 s, 978 frames de pitch. Almacén TTL stateless (`core/store.py`). Snapshot del contrato en `tests/snapshots/openapi_v1.json`. Colección Postman. Datos §12.1 documentados. **Revisión S1 (6 hallazgos, corregidos):** (1) `get_by_index` devolvía ids ya expirados → bug de reintento 202→404; (2) fuga del índice de idempotencia al purgar; (3) tipado `TtlStore[object]` → `TtlStore[AnalysisResult]`; (4) status `completed` hardcodeado en respuestas idempotentes; (5) `attempt_id`/`routine_id` vacíos aceptados → `min_length=1`; (6) descripción de `mode` desactualizada. Tests de regresión añadidos (`test_store.py`, ids vacíos) → `pytest` **15/15** · `ruff` OK · E2E Docker POST→GET: `vocal: 71`, segmentos `out_of_tune,no_voice,out_of_tune`. **Pendiente (coordinación):** publicar `/docs` al equipo y cerrar el origen del audio de referencia en refinement. |
| 06/10/2026 | **S2 — completado** | Pipeline de preprocesamiento (`app/services/preprocess.py`): `resolve_ffmpeg` (env `FFMPEG_BINARY` → PATH → error 500 `FFMPEG_NOT_FOUND`), validaciones `UNSUPPORTED_FORMAT` 415 / `FILE_TOO_LARGE` 413 (lectura por chunks, corte en `MAX_FILE_MB`) / `EMPTY_FILE` 400 / `DURATION_TOO_LONG` 413 / `NO_AUDIO_TRACK` 415 / `INVALID_AUDIO` 400 / `CONVERT_TIMEOUT` 400; conversión FFmpeg (`-map 0:a:0` + loudnorm I=-16 → WAV 16 kHz mono, timeout 120 s) y duración real vía módulo `wave`. Ruta `POST /analyze` con `mode=real`: idempotencia → validación → `run_in_threadpool` → `TemporaryDirectory` limpio (RNF-06) → respuestas con `algorithm_version=0.2.0-preprocess-real`, `duration_sec` real, `timings.preprocess_ms` medido y recorte coherente de curvas/segmentos/feedback a la duración real; el test 501 se reemplazó por `tests/test_preprocess.py` (10 tests). Snapshot OpenAPI regenerado (cambio de descripción de `mode`). Verificación: `pytest` **24/24** · `ruff` OK · E2E Docker: POST `mode=real` con wav 44.1 kHz → 202, `duration_sec: 2.0`, 44 frames, `preprocess_ms: 663`, 0 segmentos; extensión `.txt` → 415 `UNSUPPORTED_FORMAT`; reintento → mismo `analysis_id`. |
| 06/10/2026 | **Revisión de S1+S2 (código)** | Revisión estática de rutas, store, schemas, mock, preprocess y tests. **Corregido:** (R2-1) `convert_to_wav16k` no capturaba `OSError` con `FFMPEG_BINARY` inválido → 500 sin código tipado, ahora `FFMPEG_NOT_FOUND`; (R2-2) variable `_reference` asignada sin usarse con `# noqa: F841` → se invoca la conversión sin asignar el resultado (se consumirá desde S3); (R2-3) sin test de `reference_file` corrupta → añadido (`400 INVALID_AUDIO`); (R2-4) sin test de binario FFmpeg inválido → añadido (`500 FFMPEG_NOT_FOUND`). **Notas sin cambio (transitorias a S3):** en `mode=real` las curvas mock sólo cubren ≤45 s y `scores` siguen siendo los del prototipo (`algorithm_version` los delata); `mode` es por request y `env MODE` sólo se refleja en `/health`; aún no hay límite de concurrencia para FFmpeg/pyin (riesgo documentado; se añadirá semáforo en S3 junto al pitch). Verificación: `pytest` **26/26** · `ruff` OK. |
| 06/10/2026 | **S3 — completado** | Pitch real con `librosa.pyin` (HU-43) en `app/services/pitch.py`: `fmin=65` (E2) / `fmax=1047` (C6), `hop_length` configurable (512 @ 16 kHz → `hop_ms: 32`), frames sin voz → `f0: null` + `silence_pct` real calculado desde los frames no voceados; fallos de extracción → `400 PITCH_EXTRACT_FAILED`. La ruta `mode=real` ejecuta preprocess de alumno y referencia → pyin de ambos en `run_in_threadpool` → `build_result(..., pitch=<curvas reales>, silence_pct=<real>, dtw_ms=0, scoring_ms=0)` con `algorithm_version=0.3.0-pitch-real`; el builder mock ahora acepta inyección de pitch/métricas (S1 intacto por defaults; mensaje `LOW_VOLUME_ENTRY` dinámico con el `silence_pct`). Dependencia: `librosa>=1.0` (encaja en Python 3.14 con numba 0.68). Tests: `tests/test_pitch.py` (3: tono+silo, ruta real, silencio total) → `pytest` **29/29** · `ruff` OK · snapshot regenerado (descripción de `mode`). E2E Docker: wav 3 s (0.5 s silencio + 440 Hz) → `0.3.0-pitch-real`, mediana f0 alumno **439.8 Hz**, referencia **219.9 Hz**, `silence_pct: 15`, `hop_ms: 32`, `pitch_ms: 6136` (incluye JIT numba de arranque; en caliente <0.5 s), `segments: 0`. **Pendiente para S4:** derivar `segments`/`scores`/`dtw_ms` reales y añadir semáforo de concurrencia (pyin + DTW). |
| 06/10/2026 | **Revisión final de S1+S2+S3** | Re-auditoría completa (rutas, store, schemas, mock, preprocess, pitch, tests). **Corregido:** (A) `wav_duration_sec` no capturaba `wave.Error`/`OSError`/`EOFError` → una salida ilegible de FFmpeg producía un `500` sin código tipado; ahora `400 INVALID_AUDIO` (+ test de regresión). (B) La tasa de muestreo `16000` estaba hardcodeada en tres sitios (`preprocess -ar`, `pitch _SR`, cálculo de `hop_ms` en la ruta) → riesgo de desincronización silenciosa entre `hop_ms` publicado y los frames reales; ahora `settings.sample_rate` como única fuente de verdad. **Sin errores en:** store (locks/TTL/índice), contrato (validadores cruzados), idempotencia (orden mode → índice → cómputo), manejo de temporales (RNF-06 incluso en rutas de error), límites de subida, y circuito `run_in_threadpool`/`PreprocessError`. Verificación: `pytest` **30/30** · `ruff` OK. |
| 06/10/2026 | **S4 — completado** | FastDTW + cents + scores + feedback (HU-44/45/46, RF-38/39). Servicios nuevos: `align.py` (`align_frames` con FastDTW y distancia en cents que penaliza voz↔sin-voz con `nan` — hallazgo: `fastdtw` convierte `None` a `nan` y una distancia que esperaba `None` rompía la matriz DTW —, `build_segments` con duraciones mínimas 0.4 s/0.6 s y gravedad vía `CENT_THRESHOLD`, `hz_to_note` A4=440), `scoring.py` (`afinacion` = % frames dentro del umbral, `estabilidad` = 100−2σ, `control_volumen` = 100−100·CV del RMS voceado, `vocal` = 0.5/0.25/0.25), `feedback.py` (códigos `OUT_OF_TUNE` y `NO_VOICE` que distinguen HU-46). La ruta `mode=real` ejecuta la cadena completa y responde `algorithm_version=0.4.0-align-scoring` con `dtw_ms`/`scoring_ms` reales; `build_result` acepta inyección de scores/segmentos/feedback (mock intacto). **Scoring documentado** en `Docs/scoring.md` (fórmulas, umbrales, códigos, env, trazabilidad). Dockerfile: `build-essential` en el builder (fastdtw es sdist sin wheels). Tests: `tests/test_align.py` (15: alineación, segmentos, notas, scoring, feedback y ruta desafinada) → `pytest` **45/45** · `ruff` OK · snapshot regenerado. E2E Docker: 440 vs 440 → `afinacion 100`, `vocal 98`, `segments []`; 460 vs 440 → segmento `out_of_tune` **80 cents `high`**, feedback `OUT_OF_TUNE`, `afinacion 0`, `vocal 47`, `dtw_ms 4`. **Pendiente:** S5 (Celery + HU-47 + E2E + demo) y semáforo de concurrencia. |
| 06/10/2026 | **Revisión de S1–S4** | Auditoría con ojos frescos antes de S5 sobre los archivos más editados: `routes/analyze.py`, `services/align.py`, `scoring.py`, `feedback.py`, `preprocess.py` (`ensure_supported_extension`), `mock/data.py` (`build_result`), tabla de errores del README y `postman_collection.json` (JSON válido). **1 bug corregido:** `feedback.py` calculaba el `% de tiempo sin voz` con `round()`, que puede informar **"0%" con segmentos `no_voice` presentes** (audio largo + segmento mínimo de 0.6 s) → ahora `max(1, pct)`. Verificados sin errores: `filename=None` → 415 tipado (no 500), orden idempotencia→validación→cómputo, `zip(strict=True)` entre `points` y `aligned`, notas de `out_of_tune` siempre no-`None` (implícito en `cents`), `hop_ms` derivado de `settings`, clamps `end ≤ duration` coherentes entre `build_segments` y el filtro de `build_result`. Verificación: `pytest` **45/45** · `ruff` OK. |
| 06/10/2026 | **S5 — completado (entregables del servicio)** | (1) **Concurrencia/hardening:** semáforo `MAX_CONCURRENT_ANALYSES=2` + espera `BUSY_TIMEOUT_SEC=30` → **429 `SERVICE_BUSY`** (`threading.Semaphore` vía `asyncio.to_thread`: no bloquea el loop, seguro entre loops, liberado en `finally` incluso en error; `mode=mock` no lo usa) + tests (`tests/test_busy.py`). (2) **RNF-03:** `app/core/log.py` — eventos JSON una-línea (`analysis_accepted` con timings/vocal, `analysis_failed` con `code`, `analysis_not_found`), `basicConfig` en `main.py`, sin PII (RNF-06). (3) **E2E contrato §11:** `tests/test_e2e.py` — desviación conocida 80 cents (460.8 vs 440) exige `out_of_tune` 75–85 `high` + feedback + score + reintento idempotente; pausa larga → `NO_VOICE` sin informar "0%" (regresión del bug de revisión); mp3 → pipeline completo → `pytest` **51/51** · `ruff` OK. (4) **`Docs/integracion-core.md`:** flujo Celery, esqueleto de task con reintentos/backoff/429, tabla de errores→acción del worker, timeouts, **HU-47** (el Core pondera `scores.vocal` con el de baile; `/combine` pendiente de decisión §3.2; sub-scores verificables por separado), estado `failed`/`queued` reservados en el contrato (RNF-07 lo resuelve el Core con `detail.code`), observabilidad y env vars. (5) **Métricas §15.1** con `scripts/demo_e2e.py` (audios §12.1 autogenerados): **3/3 = 100 % de éxito**, wall medio **654 ms**, `timings` medio 647 ms, sonda de audio 40 s = **1703 ms < 2 s (RNF cumplido)**. (6) Postman final (6 requests: +real, +404) y README (checklist S5, estructura, comando demo). **E2E Docker (rebuild):** demo `3/3 = 100 %` (wall medio 2808 ms con JIT de numba frío en el primer request; sonda 40 s = 1827 ms < 2 s) y eventos JSON de RNF-03 visibles en `docker compose logs`. **Pendiente equipo/monorepo:** decisión `/combine`, demo de app (Core), mover `singing-service` al monorepo + compose raíz + rama `feature/singing-microservice`. |
| 06/10/2026 | **Revisión de S5** | Auditoría de todo lo añadido en S5 (ruta con semáforo+logs, `core/log.py`, `config.py`, `test_busy/test_e2e`, `scripts/demo_e2e.py`, guía Core, Postman). **No-flaky verificado:** el delta del E2E 80 cents se midió **6/6 idéntico (80, afinación 0)** — pyin determinista con audio generado; rango 75–85 con holgura. **2 correcciones:** (1) `BUSY_TIMEOUT_SEC` negativo o `MAX_CONCURRENT_ANALYSES=0` provocaba `ValueError` de `threading` → **500 sin código tipado por request**; ahora `Field(ge=…)` → configuración inválida **falla al arrancar** (fail-fast). (2) Los reintentos idempotentes del Core eran invisibles en logs → nuevo evento `analysis_idempotent_hit` (RNF-03). Sin errores en: emparejamiento acquire/finally (release también en rutas de error), `except HTTPException` sin doble log con `PreprocessError`, mock fuera del semáforo (diseño), orden idempotencia→semáforo, `json.dumps(default=str)`, huella de OpenAPI intacta (sin cambio de esquema). Tests nuevos `tests/test_log.py` (idempotencia logueada, 404 logueado, bounds de env) → `pytest` **54/54** · `ruff` OK. **Prototipo Figma (`Docs/prototipo.png`):** estados 02.1/02.2 correctos; faltan secciones 6-9 (Segmentos con 3 filas, Feedback con 2 cards, **Evaluación combinada HU-47**, CTA) + nota bajo la curva y hay 2 nodos huérfanos fuera del wrapper → **BLOQUE 4 de fix** añadido a `Docs/prompt-agente-figma-canto.md` (MCP Figma sigue bloqueado por plan). |
