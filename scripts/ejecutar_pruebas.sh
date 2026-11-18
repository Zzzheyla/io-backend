#!/usr/bin/env bash
# Ejecuta las pruebas de carga de las tres APIs y guarda los datos crudos.
# Uso (desde Git Bash o Linux/macOS, en la carpeta del proyecto):
#     bash scripts/ejecutar_pruebas.sh
# Variables opcionales: REPS=10 DURATION=60s WARMUP=15s VUS=50
#     REPS=2 DURATION=15s bash scripts/ejecutar_pruebas.sh   (prueba rapida)

set -euo pipefail
export MSYS_NO_PATHCONV=1   # evita que Git Bash cambie las rutas de Docker

REPS=${REPS:-10}
DURATION=${DURATION:-60s}
WARMUP=${WARMUP:-15s}
VUS=${VUS:-50}
K6_IMAGE=${K6_IMAGE:-grafana/k6:0.54.0}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Ruta que entiende Docker (en Git Bash sale como C:/Users/...)
ROOT_DOCKER="$( (pwd -W) 2>/dev/null || pwd )"
RAW="$ROOT/resultados/raw"
mkdir -p "$RAW"

PY=""
for candidato in python python3 py; do
  if "$candidato" --version > /dev/null 2>&1; then PY=$candidato; break; fi
done
if [ -z "$PY" ]; then echo "No se encontro Python instalado" >&2; exit 1; fi

# alias : servicio : puerto interno : puerto en la PC
APIS=("python:api-python:8000:8001" "node:api-node:3000:8002" "csharp:api-csharp:8080:8003")
# SOLO=python2 ejecuta solo la comprobacion de Python con 2 procesos
if [ -n "${SOLO:-}" ]; then
  APIS=()
  [ "$SOLO" = "python2" ] && APIS=("python2:api-python2:8000:8004")
fi
SUFIJO=${SOLO:+_$SOLO}
RED=io-backend_default

esperar_api() {
  local puerto=$1
  for _ in $(seq 1 60); do
    if curl -sf "http://localhost:$puerto/health" > /dev/null; then return 0; fi
    sleep 1
  done
  echo "La API del puerto $puerto no respondio" >&2
  exit 1
}

k6_run() {
  local servicio=$1 puerto=$2 duracion=$3 salida=$4
  local export_arg=()
  if [ -n "$salida" ]; then export_arg=(--summary-export "/carga/salidas/$salida"); fi
  docker run --rm --network "$RED" \
    -v "$ROOT_DOCKER/carga:/carga" \
    -e BASE_URL="http://$servicio:$puerto" -e VUS="$VUS" -e DURATION="$duracion" \
    "$K6_IMAGE" run --quiet "${export_arg[@]}" /carga/carga.js > /dev/null
}

echo "== Construyendo y levantando los contenedores"
docker compose up -d --build
mkdir -p carga/salidas

echo "== Registrando versiones y equipo"
{
  echo "fecha: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "repeticiones: $REPS | duracion: $DURATION | calentamiento: $WARMUP | usuarios: $VUS"
  echo "k6: $K6_IMAGE"
  docker version --format 'docker: {{.Server.Version}}'
  docker info --format 'cpus del equipo: {{.NCPU}} | memoria: {{.MemTotal}} bytes | so: {{.OperatingSystem}}'
  docker compose images
} > "resultados/entorno${SUFIJO}.txt"

for rep in $(seq 1 "$REPS"); do
  for entrada in "${APIS[@]}"; do
    IFS=: read -r alias servicio puerto puerto_pc <<< "$entrada"
    echo "== Repeticion $rep/$REPS - $alias"

    # 1) Mismos datos para todos
    docker compose exec -T db psql -q -U io -d io -f /sql/reset.sql > /dev/null

    # 2) API recien reiniciada (memoria limpia)
    docker compose restart "$servicio" > /dev/null
    esperar_api "$puerto_pc"

    # 3) Calentamiento (no se guarda)
    k6_run "$servicio" "$puerto" "$WARMUP" ""

    # 4) Medicion de CPU y RAM en segundo plano mientras corre la prueba
    stats="$RAW/${alias}_rep${rep}_stats.csv"
    : > "$stats"
    ( while true; do
        docker stats --no-stream --format '{{.CPUPerc}},{{.MemUsage}}' "io-$servicio" >> "$stats" 2>/dev/null || true
      done ) &
    muestreo=$!

    # 5) Prueba de carga medida
    k6_run "$servicio" "$puerto" "$DURATION" "${alias}_rep${rep}.json"

    kill "$muestreo" 2>/dev/null || true
    wait "$muestreo" 2>/dev/null || true
    mv "carga/salidas/${alias}_rep${rep}.json" "$RAW/"
  done
done

if [ -n "${SOLO:-}" ]; then
  echo "Listo. Datos crudos en resultados/raw/${SOLO}_rep*.json"
  exit 0
fi
echo "== Resumiendo resultados"
"$PY" scripts/resumir_resultados.py

echo "Listo. Revisa la carpeta resultados/ y modelo/datos/datos_modelo.csv"
