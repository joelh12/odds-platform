#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-local}"
API_URL="${API_URL:-http://localhost:4000}"
WEB_URL="${WEB_URL:-http://localhost:3000}"
EDGE_URL="${EDGE_URL:-http://localhost:8082}"
BETMGM_ENABLED="${BETMGM_ENABLED:-false}"
SMOKE_API_PID=""
SMOKE_WEB_PID=""

wait_for_url() {
  local url="$1"
  local name="$2"
  local retries="${3:-40}"
  local delay="${4:-1}"

  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[ok] $name is reachable at $url"
      return 0
    fi
    sleep "$delay"
  done

  echo "[fail] timed out waiting for $name at $url" >&2
  return 1
}

check_json_contains() {
  local url="$1"
  local pattern="$2"
  local label="$3"

  local body
  body="$(curl -fsS "$url")"
  if [[ "$body" == *"$pattern"* ]]; then
    echo "[ok] $label"
  else
    echo "[fail] expected pattern '$pattern' in $url" >&2
    echo "body: $body" >&2
    return 1
  fi
}

smoke_http_checks() {
  echo "[step] HTTP checks"
  check_json_contains "$API_URL/health" '"status":"ok"' "API health"
  check_json_contains "$API_URL/api/meta" '"sources"' "API meta"
  check_json_contains "$API_URL/api/snapshot" '"matches"' "API snapshot"

  local stream_sample
  # Avoid failing on curl SIGPIPE when we intentionally truncate stream output.
  stream_sample="$( (curl -Ns "$API_URL/api/stream" | sed -n '1,4p;4q') 2>/dev/null || true )"
  if [[ "$stream_sample" == *"event: snapshot"* ]]; then
    echo "[ok] SSE stream emits snapshot events"
  else
    echo "[fail] SSE stream did not emit expected event" >&2
    echo "$stream_sample" >&2
    return 1
  fi

  local web_html
  web_html="$(curl -fsS "$WEB_URL" | head -n 20)"
  if [[ "$web_html" == *"Live Value Radar"* ]]; then
    echo "[ok] Web UI responded with app content"
  else
    echo "[fail] Web UI response missing expected content" >&2
    return 1
  fi
}

run_local_mode() {
  echo "[mode] local"
  npm run build >/dev/null

  BETMGM_ENABLED="$BETMGM_ENABLED" node apps/api/dist/index.js >/tmp/portfolio-api-smoke.log 2>&1 &
  SMOKE_API_PID=$!

  npm run start -w @portfolio/web >/tmp/portfolio-web-smoke.log 2>&1 &
  SMOKE_WEB_PID=$!

  cleanup() {
    if [[ -n "${SMOKE_API_PID:-}" ]]; then
      kill "$SMOKE_API_PID" >/dev/null 2>&1 || true
    fi
    if [[ -n "${SMOKE_WEB_PID:-}" ]]; then
      kill "$SMOKE_WEB_PID" >/dev/null 2>&1 || true
    fi
  }
  trap cleanup EXIT

  wait_for_url "$API_URL/health" "API"
  wait_for_url "$WEB_URL" "Web"

  smoke_http_checks
  echo "[ok] local smoke test passed"
}

run_docker_mode() {
  echo "[mode] docker"
  docker compose up --build -d

  cleanup() {
    docker compose down >/dev/null 2>&1 || true
  }
  trap cleanup EXIT

  wait_for_url "$API_URL/health" "API"
  wait_for_url "$WEB_URL" "Web"
  wait_for_url "$EDGE_URL/health" "Edge-Go"

  smoke_http_checks
  check_json_contains "$EDGE_URL/health" '"status":"ok"' "Edge-Go health"

  echo "[ok] docker smoke test passed"
}

case "$MODE" in
  local)
    run_local_mode
    ;;
  docker)
    run_docker_mode
    ;;
  *)
    echo "Usage: $0 [local|docker]" >&2
    exit 1
    ;;
esac
