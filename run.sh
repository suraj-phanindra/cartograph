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
    echo "==> serving the demo at http://127.0.0.1:${PORT}/index.html"
    echo "    (Ctrl-C to stop)"
    cd frontend && exec ../.venv/bin/python -m http.server "$PORT" --bind 127.0.0.1 ;;
  *) echo "usage: ./run.sh [serve|build|test]"; exit 1 ;;
esac
