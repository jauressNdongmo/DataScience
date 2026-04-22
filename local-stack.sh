#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/.local-runtime"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$RUNTIME_DIR/logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3307}"

print_usage() {
  cat <<USAGE
Usage: ./local-stack.sh [start|stop|restart|status|logs]

Commands:
  start    Start all local services
  stop     Stop all local services started by this script
  restart  Stop then start all services
  status   Show service status and important URLs
  logs     Tail all service logs
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERROR] Missing required command: $1"
    exit 1
  fi
}

is_pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

wait_for_port() {
  local host="$1"
  local port="$2"
  local timeout_secs="${3:-60}"
  local start_ts
  start_ts="$(date +%s)"

  while true; do
    if (echo >"/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
      return 0
    fi
    if (( "$(date +%s)" - start_ts > timeout_secs )); then
      return 1
    fi
    sleep 1
  done
}

cleanup_port() {
  local port="$1"
  local label="$2"

  if ! command -v lsof >/dev/null 2>&1; then
    return
  fi

  local pids
  pids="$(lsof -tiTCP:${port} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return
  fi

  echo "[CLEAN] Port ${port} already in use (${label}). Stopping existing listener(s)."
  while IFS= read -r pid; do
    [[ -z "$pid" ]] && continue
    kill "$pid" >/dev/null 2>&1 || true
  done <<<"$pids"

  sleep 1

  local still_running
  still_running="$(lsof -tiTCP:${port} -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$still_running" ]]; then
    while IFS= read -r pid; do
      [[ -z "$pid" ]] && continue
      kill -9 "$pid" >/dev/null 2>&1 || true
    done <<<"$still_running"
  fi
}

cleanup_stack_ports() {
  cleanup_port 8090 "discovery-server"
  cleanup_port 8888 "config-server"
  cleanup_port 8000 "ml-python"
  cleanup_port 8093 "agri-data"
  cleanup_port 8095 "integration"
  cleanup_port 8094 "decision"
  cleanup_port 8081 "gateway"
  cleanup_port 5173 "frontend-react"
  cleanup_port 5174 "frontend-react (fallback)"
  cleanup_port 5175 "frontend-react (fallback)"
}

start_background() {
  local service="$1"
  local workdir="$2"
  local cmd="$3"
  local env_prefix="${4:-}"

  local pid_file="$PID_DIR/${service}.pid"
  local log_file="$LOG_DIR/${service}.log"

  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file")"
    if is_pid_alive "$existing_pid"; then
      echo "[SKIP] $service already running (PID $existing_pid)"
      return
    fi
    rm -f "$pid_file"
  fi

  echo "[START] $service"
  if [[ -n "$env_prefix" ]]; then
    nohup bash -lc "cd '$workdir' && $env_prefix $cmd" >"$log_file" 2>&1 &
  else
    nohup bash -lc "cd '$workdir' && $cmd" >"$log_file" 2>&1 &
  fi

  local pid=$!
  echo "$pid" >"$pid_file"
  echo "  -> PID: $pid"
  echo "  -> Log: $log_file"
}

stop_service() {
  local service="$1"
  local pid_file="$PID_DIR/${service}.pid"

  if [[ ! -f "$pid_file" ]]; then
    return
  fi

  local pid
  pid="$(cat "$pid_file")"

  if is_pid_alive "$pid"; then
    echo "[STOP] $service (PID $pid)"
    kill "$pid" >/dev/null 2>&1 || true

    for _ in {1..20}; do
      if ! is_pid_alive "$pid"; then
        break
      fi
      sleep 0.5
    done

    if is_pid_alive "$pid"; then
      echo "  -> force kill"
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  fi

  rm -f "$pid_file"
}

start_stack() {
  require_cmd bash
  require_cmd mvn
  require_cmd npm
  require_cmd python3

  if ! wait_for_port "$MYSQL_HOST" "$MYSQL_PORT" 2; then
    echo "[WARN] MySQL not reachable on ${MYSQL_HOST}:${MYSQL_PORT}."
    echo "       Start MySQL first (credentials expected: springboot/springboot)."
  fi

  cleanup_stack_ports

  local common_java_cmd="mvn spring-boot:run -Dspring-boot.run.profiles=dev"
  local pip_cmd="$ROOT_DIR/backend/ml-python/.venv/bin/pip"

  start_background "discovery-server" "$ROOT_DIR/backend/discoveryServer" "$common_java_cmd"
  if wait_for_port localhost 8090 90; then
    echo "[OK] discovery-server ready on :8090"
  else
    echo "[WARN] discovery-server not ready yet (port 8090)"
  fi

  local config_env="CONFIG_REPO_LOCATION=file:${ROOT_DIR}/config-repo"
  start_background "config-server" "$ROOT_DIR/backend/configServer" "$common_java_cmd" "$config_env"
  if wait_for_port localhost 8888 90; then
    echo "[OK] config-server ready on :8888"
  else
    echo "[WARN] config-server not ready yet (port 8888)"
  fi

  if [[ ! -d "$ROOT_DIR/backend/ml-python/.venv" ]]; then
    echo "[INIT] Creating Python venv for ml-python"
    python3 -m venv "$ROOT_DIR/backend/ml-python/.venv"
  fi

  if ! "$ROOT_DIR/backend/ml-python/.venv/bin/python" -c "import fastapi" >/dev/null 2>&1; then
    echo "[INIT] Installing ml-python dependencies"
    "$pip_cmd" install -r "$ROOT_DIR/backend/ml-python/requirements.txt"
  fi

  start_background "ml-python" "$ROOT_DIR/backend/ml-python" \
    "AUTO_TRAIN_ON_STARTUP=true DATASET_PATH='$ROOT_DIR/backend/ml-python/data/yield_df.csv' ./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"

  if [[ ! -d "$ROOT_DIR/frontend/react/node_modules" ]]; then
    echo "[INIT] Installing frontend dependencies"
    (cd "$ROOT_DIR/frontend/react" && npm install)
  fi

  start_background "agri-data" "$ROOT_DIR/backend/agriData" "$common_java_cmd"
  start_background "integration" "$ROOT_DIR/backend/integration" "$common_java_cmd"
  start_background "decision" "$ROOT_DIR/backend/decision" "$common_java_cmd"
  start_background "gateway" "$ROOT_DIR/backend/gateway" "$common_java_cmd"
  start_background "frontend-react" "$ROOT_DIR/frontend/react" "npm run dev -- --host 0.0.0.0 --port 5173 --strictPort"

  echo
  echo "Local stack start requested. Use './local-stack.sh status' to check health."
  print_urls
}

print_urls() {
  cat <<URLS

URLs:
- Frontend React:      http://localhost:5173
- API Gateway:         http://localhost:8081
- Discovery Server:    http://localhost:8090
- Config Server:       http://localhost:8888
- Agri Data Service:   http://localhost:8093/agri-data
- Integration Service: http://localhost:8095/integration
- Decision Service:    http://localhost:8094/decision
- ML Python Service:   http://localhost:8000
URLS
}

status_stack() {
  local services=(
    discovery-server
    config-server
    ml-python
    agri-data
    integration
    decision
    gateway
    frontend-react
  )

  echo "Service status:"
  for service in "${services[@]}"; do
    local pid_file="$PID_DIR/${service}.pid"
    if [[ -f "$pid_file" ]]; then
      local pid
      pid="$(cat "$pid_file")"
      if is_pid_alive "$pid"; then
        echo "- $service: RUNNING (PID $pid)"
      else
        echo "- $service: STOPPED (stale PID file)"
      fi
    else
      echo "- $service: STOPPED"
    fi
  done
  print_urls
}

stop_stack() {
  local services=(
    frontend-react
    gateway
    decision
    integration
    agri-data
    ml-python
    config-server
    discovery-server
  )

  for service in "${services[@]}"; do
    stop_service "$service"
  done

  echo "All tracked local services have been stopped."
}

logs_stack() {
  if ! compgen -G "$LOG_DIR/*.log" >/dev/null; then
    echo "No log files found in $LOG_DIR"
    exit 0
  fi

  echo "Tailing logs from $LOG_DIR"
  tail -n 80 -F "$LOG_DIR"/*.log
}

cmd="${1:-start}"
case "$cmd" in
  start)
    start_stack
    ;;
  stop)
    stop_stack
    ;;
  restart)
    stop_stack
    start_stack
    ;;
  status)
    status_stack
    ;;
  logs)
    logs_stack
    ;;
  *)
    print_usage
    exit 1
    ;;
esac
