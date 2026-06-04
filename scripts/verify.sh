#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Backend tests =="
cd "$ROOT_DIR/apps/api"
python3 -m pytest

echo "== Frontend typecheck =="
cd "$ROOT_DIR/apps/web"
npm run typecheck

echo "== Frontend build =="
npm run build

echo "Verification complete."
