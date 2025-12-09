#!/bin/bash
# Agent PerfSmith: Code optimization insights for backend + frontend
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"

HOTSPOT_REPORT="$REPORTS_DIR/perfsmith_hotspots.md"
BUNDLE_REPORT="$REPORTS_DIR/perfsmith_bundle.json"

generate_hotspots() {
  echo "[PerfSmith] Generating hotspot summary"
  python3 "$ROOT_DIR/ci_workflows/helpers/perfsmith_hotspots.py" \
    --backend-dir "$ROOT_DIR/backend" \
    --frontend-dir "$ROOT_DIR/frontend/src" \
    --output "$HOTSPOT_REPORT"
}

analyze_bundle() {
  if [ "${RUN_PERF_BUILD:-0}" -ne 1 ]; then
    echo "[PerfSmith] Skipping bundle build (set RUN_PERF_BUILD=1 to enable)"
    return
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "[PerfSmith] npm not found; cannot build frontend" >&2
    return
  fi

  pushd "$ROOT_DIR/frontend" >/dev/null
  echo "[PerfSmith] Building React bundle for stats"
  npm run build >/dev/null
  echo "[PerfSmith] Running source-map-explorer"
  npx source-map-explorer "build/static/js/*.js" --json >"$BUNDLE_REPORT"
  popd >/dev/null
}

append_bundle_note() {
  if [ ! -f "$BUNDLE_REPORT" ]; then
    {
      echo ""
      echo "> Bundle stats were skipped. Run with RUN_PERF_BUILD=1 for bundle size JSON."
    } >>"$HOTSPOT_REPORT"
  fi
}

main() {
  echo "[PerfSmith] Starting analysis"
  generate_hotspots
  analyze_bundle
  append_bundle_note
  echo "[PerfSmith] Completed → reports stored in $REPORTS_DIR"
}

main "$@"
