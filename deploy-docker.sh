#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/deployment"
docker compose up --build
