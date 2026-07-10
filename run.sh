#!/usr/bin/env bash
# Cartograph — one command to reproduce the whole pipeline and serve the demo.
# Usage:  ./run.sh          (build everything, then serve the demo)
#         ./run.sh build    (just rebuild the computed artifact)
#         ./run.sh test     (run the test suite)
set -euo pipefail
cd "$(dirname "$0")"

PORT="${CARTOGRAPH_PORT:-8791}"

setup() {
  if [ ! -d .venv ]; then
    echo "==> creating venv + installing deps"
    python3 -m venv .venv
    ./.venv/bin/python -m pip install -q --upgrade pip
    ./.venv/bin/python -m pip install -q -r requirements.txt
  fi
}

build() {
  echo "==> freezing the locked held-out split (idempotent; first commit's artifact)"
  ./.venv/bin/python -m backend.eval.freeze_split
  echo "==> STRING enrichment (uses cache if present; network needed only once)"
  ./.venv/bin/python -m backend.graph.enrich
  echo "==> computing the artifact (real graph, honest eval, dossiers)"
  ./.venv/bin/python -m backend.build_artifact
}

case "${1:-serve}" in
  build) setup; build ;;
  test)  setup; ./.venv/bin/python -m pytest backend/tests/ -q ;;
  serve)
    setup; build
    echo ""
    echo "==> serving the OFFLINE workbench at http://127.0.0.1:${PORT}/index.html"
    echo "    (no API; live-only controls disabled; Ctrl-C to stop)"
    exec ./.venv/bin/python -m backend.serve_static "$PORT" ;;
  api)
    setup; build
    echo ""
    echo "==> serving the demo + LIVE API at http://127.0.0.1:${PORT}/index.html"
    echo "    (adds /api/* incl. upload; Ctrl-C to stop)"
    exec ./.venv/bin/python -m uvicorn backend.api.server:app --host 127.0.0.1 --port "$PORT" ;;
  *) echo "usage: ./run.sh [serve|build|test|api]"; exit 1 ;;
esac
