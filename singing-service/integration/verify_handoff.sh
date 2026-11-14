#!/usr/bin/env bash
# Verificacion end-to-end del handoff Core <-> singing-service.
#
# Uso (desde la raiz del monorepo):
#   bash singing-service/integration/verify_handoff.sh
#
# Requisitos: docker (o servicio ya corriendo), curl, ffmpeg, Python con
# integration/requirements.txt instalado. Linux/macOS: bash. Windows: Git Bash
# o WSL (el script usa rutas POSIX y detecta el venv de Windows).

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
HEALTH_URL="${HEALTH_URL:-http://localhost:5000/health}"
export SINGING_SERVICE_URL="${SINGING_SERVICE_URL:-http://localhost:5000/api/v1/analyze}"

if [ -x "${SERVICE_DIR}/.venv/bin/python" ]; then
  PYTHON="${SERVICE_DIR}/.venv/bin/python"
elif [ -x "${SERVICE_DIR}/.venv/Scripts/python.exe" ]; then
  PYTHON="${SERVICE_DIR}/.venv/Scripts/python.exe"
else
  PYTHON="${PYTHON:-python3}"
fi

FIXTURES_DIR="${SCRIPT_DIR}/fixtures"
LOG_DIR="$(mktemp -d)"
trap 'rm -rf "${LOG_DIR}"' EXIT

TOTAL=0
PASSED=0
fail() { echo "[FAIL] $1"; }
ok()   { PASSED=$((PASSED + 1)); echo "[PASS] $1"; }
step() { TOTAL=$((TOTAL + 1)); }

echo "=== singing-service :: verify_handoff ==="
echo "service_dir : ${SERVICE_DIR}"
echo "python      : ${PYTHON}"
echo "analyze_url : ${SINGING_SERVICE_URL}"
echo

echo "-- 1/4 docker compose up + health --"
step
if command -v docker >/dev/null 2>&1; then
  if ( cd "${SERVICE_DIR}" && docker compose up -d singing-service ) >"${LOG_DIR}/docker.log" 2>&1; then
    echo "docker compose up: OK"
  else
    echo "AVISO: docker compose up fallo (se asume servicio ya corriendo):"
    tail -n 5 "${LOG_DIR}/docker.log"
  fi
else
  echo "AVISO: docker no disponible; se asume servicio ya corriendo"
fi

HEALTH_OK=0
for _ in $(seq 1 60); do
  if curl -fsS "${HEALTH_URL}" >"${LOG_DIR}/health.json" 2>/dev/null; then
    HEALTH_OK=1
    break
  fi
  sleep 1
done
if [ "${HEALTH_OK}" -eq 1 ]; then
  ok "health 200 (${HEALTH_URL})"
else
  fail "health no respondio 200 en 60 s (${HEALTH_URL})"
fi

echo
echo "-- 2/4 fixtures --"
if "${PYTHON}" "${SCRIPT_DIR}/generate_fixtures.py" >"${LOG_DIR}/fixtures.log" 2>&1; then
  echo "fixtures: OK ($(grep -c 'MB' "${LOG_DIR}/fixtures.log" || true) archivos)"
else
  fail "generate_fixtures.py"
  cat "${LOG_DIR}/fixtures.log"
fi

echo
echo "-- 3/4 simulacion de worker (absolute + comparative) --"
step
if "${PYTHON}" "${SCRIPT_DIR}/simulate_celery_worker.py" \
  --audio "${FIXTURES_DIR}/sine_440hz_5s.wav" --mode absolute \
  >"${LOG_DIR}/sim_absolute.log" 2>&1; then
  ok "simulate absolute"
else
  fail "simulate absolute"
  cat "${LOG_DIR}/sim_absolute.log"
fi

step
if "${PYTHON}" "${SCRIPT_DIR}/simulate_celery_worker.py" \
  --audio "${FIXTURES_DIR}/sine_442hz_5s.wav" --mode comparative \
  --reference "${FIXTURES_DIR}/sine_440hz_5s.wav" \
  >"${LOG_DIR}/sim_comparative.log" 2>&1; then
  ok "simulate comparative"
else
  fail "simulate comparative"
  cat "${LOG_DIR}/sim_comparative.log"
fi

echo
echo "-- 4/4 matriz de errores --"
step
if "${PYTHON}" "${SCRIPT_DIR}/test_error_scenarios.py" >"${LOG_DIR}/errors.log" 2>&1; then
  ok "test_error_scenarios"
else
  fail "test_error_scenarios"
  cat "${LOG_DIR}/errors.log"
fi

echo
echo "=== RESUMEN: ${PASSED}/${TOTAL} checks OK ==="
if [ "${PASSED}" -eq "${TOTAL}" ]; then
  echo "RESULTADO: HANDOFF OK"
  exit 0
fi
echo "RESULTADO: HANDOFF CON FALLOS"
exit 1
