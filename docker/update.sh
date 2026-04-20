#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

git pull

docker compose -f docker/docker-compose.yml build --no-cache
docker compose -f docker/docker-compose.yml up -d
