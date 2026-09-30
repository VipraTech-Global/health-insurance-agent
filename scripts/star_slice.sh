#!/usr/bin/env bash
# Explicit branch runtime; never load the existing app's .env implicitly.
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
set -a
source .env.star-slice
set +a
if [[ "$POSTGRES_DB" != coverguide_star_slice || "$POSTGRES_TEST_DB" != test_coverguide_star_slice || "$REDIS_URL" != redis://127.0.0.1:6401/0 ]]; then
  echo 'Star slice database/test database/broker isolation check failed.' >&2
  exit 1
fi
action="${1:-check}"
if [[ $# -gt 0 ]]; then shift; fi
case "$action" in
  manage) exec uv run --no-sync python backend/manage.py "$@" ;;
  check) exec uv run --no-sync python backend/manage.py check "$@" ;;
  test) exec uv run --no-sync pytest --reuse-db "$@" ;;
  web) exec uv run --no-sync python backend/manage.py runserver 127.0.0.1:8021 --noreload ;;
  worker) exec env PYTHONPATH=backend uv run --no-sync celery -A config worker --hostname=star-slice@%h --concurrency=1 --queues=conversation ;;
  beat) exec env PYTHONPATH=backend uv run --no-sync celery -A config beat --schedule="$DATA_ROOT/star-slice-beat" ;;
  frontend) exec frontend/node_modules/.bin/next start frontend --hostname 127.0.0.1 --port 3021 ;;
  *) echo "Unknown Star slice action: $action" >&2; exit 2 ;;
esac
