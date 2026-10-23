#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

mkdir -p gen
python -m grpc_tools.protoc \
  -I ../../proto \
  --python_out=gen \
  --grpc_python_out=gen \
  ../../proto/notification/v1/notification.proto

find gen -type d -exec touch {}/__init__.py \;
echo "Generated stubs in apps/notification-service/gen"
