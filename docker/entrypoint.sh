#!/usr/bin/env bash
set -euo pipefail

: "${APP_HOST:=0.0.0.0}"
: "${APP_PORT:=8000}"

echo "[entrypoint] Starting in mode: ${1:-api}"

wait_for_postgres() {
  echo "[entrypoint] Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
  for i in $(seq 1 60); do
    if pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; then
      echo "[entrypoint] Postgres is up."
      return 0
    fi
    sleep 1
  done
  echo "[entrypoint] Postgres is still not reachable. Exiting."
  return 1
}

run_migrations() {
  echo "[entrypoint] Running migrations..."
  alembic upgrade head
}

case "${1:-api}" in
  api)
    wait_for_postgres
    run_migrations
    echo "[entrypoint] Starting FastAPI (uvicorn)..."
    exec uvicorn src.main:app --host "${APP_HOST}" --port "${APP_PORT}"
    ;;
  worker)
    wait_for_postgres
    echo "[entrypoint] Starting Celery worker..."
    exec celery -A src.worker.celery_app:celery_app worker -l info
    ;;
  beat)
    wait_for_postgres
    echo "[entrypoint] Starting Celery beat..."
    exec celery -A src.worker.celery_app:celery_app beat -l info
    ;;
  *)
    exec "$@"
    ;;
esac
