#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT_DIR"

node --check src/app_auto_test/web/app.js
node --test tests/web_contract.test.mjs
python3 -m pytest
