#!/usr/bin/env bash
# Build the API deployment package: backend/dist/lambda.zip
# Dependencies are installed as Linux arm64 wheels to match the Lambda runtime
# (python3.13, arm64), so this works from macOS or x86 Linux too.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
BUILD="$BACKEND/dist/build"
ZIP="$BACKEND/dist/lambda.zip"

rm -rf "$BUILD" "$ZIP"
mkdir -p "$BUILD"

cd "$BACKEND"
pipenv requirements > "$BACKEND/dist/requirements.txt"

python3 -m pip install \
  --quiet \
  --requirement "$BACKEND/dist/requirements.txt" \
  --target "$BUILD" \
  --platform manylinux2014_aarch64 \
  --implementation cp \
  --python-version 3.13 \
  --only-binary=:all:

cp -R flashpoll lambda_handler.py "$BUILD/"
find "$BUILD" -name '__pycache__' -type d -prune -exec rm -rf {} +

cd "$BUILD"
zip -q -r -X "$ZIP" .
echo "Built $ZIP ($(du -h "$ZIP" | cut -f1))"
