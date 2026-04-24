#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/deployment"

max_attempts="${DEPLOY_BUILD_RETRIES:-3}"
attempt=1

until docker compose build; do
  if [ "${attempt}" -ge "${max_attempts}" ]; then
    echo "Docker build failed after ${max_attempts} attempts."
    exit 1
  fi
  echo "Docker build failed (attempt ${attempt}/${max_attempts}), retrying in 15s..."
  attempt=$((attempt + 1))
  sleep 15
done

docker compose up --no-build
