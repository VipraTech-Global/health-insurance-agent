#!/usr/bin/env bash
set -euo pipefail

project_dir=/home/akhilesh/Projects/health-insurance-agent
project_name=coverguide-v2-closeout
deadline=$((SECONDS + 90))

while (( SECONDS < deadline )); do
  all_ready=true
  for service in postgres18 redis; do
    container_id="$(docker compose --project-directory "$project_dir" -p "$project_name" ps -q "$service")"
    if [[ -z "$container_id" ]] || [[ "$(docker inspect --format '{{.State.Health.Status}}' "$container_id")" != healthy ]]; then
      all_ready=false
    fi
  done
  nginx_id="$(docker compose --project-directory "$project_dir" -p "$project_name" ps -q nginx)"
  if [[ -z "$nginx_id" ]] || [[ "$(docker inspect --format '{{.State.Running}}' "$nginx_id")" != true ]]; then
    all_ready=false
  fi
  if [[ "$all_ready" == true ]]; then
    exit 0
  fi
  sleep 2
done

echo "CoverGuide infrastructure did not become healthy within 90 seconds." >&2
exit 1
