#!/usr/bin/env bash
# One local entry point; shared DB/relay are health-checked, never restarted.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
set -a
source .env.star-slice
set +a
if [[ "$POSTGRES_DB" != coverguide_star_slice || "$POSTGRES_TEST_DB" != test_coverguide_star_slice || "$REDIS_URL" != redis://127.0.0.1:6401/0 ]]; then
  echo 'Demo database/test database/Redis isolation check failed.' >&2
  exit 1
fi
export UV_PROJECT_ENVIRONMENT="$PWD/.venv-star"
export COVERGUIDE_RELAY_CONCURRENCY=6
state_root="${COVERGUIDE_REPORT_ROOT}/ten-insurer/stack"
mkdir -p "$state_root"
action="${1:-start}"
if [[ "$action" != start && "$action" != restart && "$action" != health ]]; then
  echo 'Usage: bash scripts/demo_stack.sh [start|restart|health]' >&2
  exit 2
fi
# Read-only checks happen before starting task-owned processes.
uv run --no-sync python backend/manage.py shell -c 'from django.db import connection; from django.conf import settings; import redis,httpx; connection.ensure_connection(); assert redis.Redis.from_url(settings.REDIS_URL).ping(); r=httpx.get("http://127.0.0.1:8317/v1/models",headers={"Authorization":"Bearer "+settings.AI_RELAY_API_KEY},timeout=15); r.raise_for_status(); assert {"gpt-5.6-luna","claude-sonnet-5"} <= {m["id"] for m in r.json()["data"]}; print("Database, Redis and authorized relay models: healthy")'
launch() {
  local service="$1"; shift
  if [[ -f "$state_root/$service.pid" ]] && kill -0 "$(cat "$state_root/$service.pid")" 2>/dev/null; then return; fi
  setsid nohup "$@" > "$state_root/$service.log" 2>&1 < /dev/null &
  echo "$!" > "$state_root/$service.pid"
}
if [[ "$action" == restart ]]; then
  # Stop only this checkout's API/frontend/worker/recovery process trees. The
  # resident embeddings worker and shared database, Redis and relay keep running.
  uv run --no-sync python - "$state_root" "$PWD" <<'PY'
import os
import signal
import sys
import time
from pathlib import Path
root, checkout = map(Path, sys.argv[1:])
for service in ('api', 'frontend', 'worker', 'recovery'):
    record = root / (service + '.pid')
    if not record.exists():
        continue
    pid = int(record.read_text())
    process = Path('/proc') / str(pid)
    if not process.exists():
        record.unlink()
        continue
    if (process / 'cwd').resolve() not in {checkout, checkout / 'frontend'}:
        raise SystemExit('Refusing to stop a process outside this checkout: ' + service)
    descendants = [pid]
    for parent in descendants:
        for task in (Path('/proc') / str(parent) / 'task').glob('*/children'):
            descendants.extend(int(child) for child in task.read_text().split() if int(child) not in descendants)
    for target in reversed(descendants):
        try:
            os.kill(target, signal.SIGTERM)
        except ProcessLookupError:
            pass
    for _ in range(50):
        if not process.exists():
            break
        time.sleep(.1)
    record.unlink()
PY
  action=start
fi
if [[ "$action" == start ]]; then
  if ! uv run --no-sync python -c 'import json; from pathlib import Path; p=Path("frontend/.next/routes-manifest.json"); assert p.exists(); data=json.loads(p.read_text()); assert "http://127.0.0.1:8021/api/" in json.dumps(data.get("rewrites",{}))' 2>/dev/null; then
    (cd frontend && COVERGUIDE_BACKEND_URL=http://127.0.0.1:8021 npm run build)
  fi
  if ! curl -fsS http://127.0.0.1:8021/api/v1/auth/session/ > /dev/null; then
    launch api bash scripts/star_slice.sh web
  fi
  if ! curl -fsS http://127.0.0.1:3021/demo > /dev/null; then
    launch frontend bash scripts/star_slice.sh frontend
  fi
  launch worker env PYTHONPATH=backend uv run --no-sync celery -A config worker --loglevel=INFO --hostname=ten-insurer-demo@%h --concurrency=2 --queues=demo_live
  launch recovery bash scripts/star_slice.sh manage recover_demo_questions --loop
fi
if [[ "$action" == start ]] && ! curl -fsS http://127.0.0.1:8022/health > /dev/null; then
  launch embeddings bash scripts/star_slice.sh manage serve_demo_embeddings
fi
for attempt in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8021/api/v1/auth/session/ > /dev/null && curl -fsS http://127.0.0.1:3021/demo > /dev/null; then break; fi
  sleep 1
done
curl -fsS http://127.0.0.1:8021/api/v2/demo/health/ > /dev/null
curl -fsS http://127.0.0.1:3021/demo > /dev/null
embedding_ready=false
for attempt in $(seq 1 90); do
  if curl -fsS http://127.0.0.1:8022/health > "$state_root/embedding-health.json" 2>/dev/null; then
    embedding_ready=true
    break
  fi
  sleep 1
done
if [[ "$embedding_ready" != true ]]; then
  echo 'Resident BGE-M3 worker did not become healthy; inspect the embeddings log.' >&2
  exit 1
fi
cat "$state_root/embedding-health.json"
worker_ready=false
for attempt in $(seq 1 6); do
  if PYTHONPATH=backend uv run --no-sync celery -A config inspect ping --destination="ten-insurer-demo@$(hostname)" --timeout=5 > "$state_root/worker-health.log" 2>&1; then
    worker_ready=true
    break
  fi
  sleep 1
done
if [[ "$worker_ready" != true ]]; then cat "$state_root/worker-health.log" >&2; exit 1; fi
echo 'Demo worker: healthy'
echo 'Local demo: http://127.0.0.1:3021/demo'
