#!/bin/bash
# Agent LintGuard: Static code analysis for backend (Python) and frontend (React)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"

RUFF_REPORT="$REPORTS_DIR/lintguard_ruff.json"
BANDIT_REPORT="$REPORTS_DIR/lintguard_bandit.json"
ESLINT_REPORT="$REPORTS_DIR/lintguard_eslint.json"
SUMMARY_REPORT="$REPORTS_DIR/lintguard.json"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

bootstrap_python_tooling() {
  if [ "${SKIP_AGENT_BOOTSTRAP:-0}" -eq 1 ]; then
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "[LintGuard] python3 is required" >&2
    exit 1
  fi

  python3 -m pip install --user --upgrade ruff bandit >/dev/null 2>&1 || true
  hash -r
}

run_python_linters() {
  pushd "$ROOT_DIR/backend" >/dev/null
  echo "[LintGuard] Running Ruff on backend/"
  python3 -m ruff check . --output-format json >"$RUFF_REPORT" || true

  echo "[LintGuard] Running Bandit on backend/"
  python3 -m bandit -r . -f json -o "$BANDIT_REPORT" || true
  popd >/dev/null
}

run_frontend_eslint() {
  pushd "$ROOT_DIR/frontend" >/dev/null
  echo "[LintGuard] Running ESLint on frontend/src"
  npx eslint "src/**/*.{js,jsx}" -f json -o "$ESLINT_REPORT" || true
  popd >/dev/null
}

write_summary() {
  cat >"$SUMMARY_REPORT" <<JSON
{
  "agent": "LintGuard",
  "generated_at": "$(timestamp)",
  "artifacts": {
    "ruff": "reports/$(basename "$RUFF_REPORT")",
    "bandit": "reports/$(basename "$BANDIT_REPORT")",
    "eslint": "reports/$(basename "$ESLINT_REPORT")"
  },
  "notes": [
    "Review Ruff + Bandit JSON for rule-level detail",
    "ESLint report stores all frontend findings with rule metadata"
  ]
}
JSON
}

main() {
  echo "[LintGuard] Starting static analysis pipeline"
  bootstrap_python_tooling
  run_python_linters
  run_frontend_eslint
  write_summary
  echo "[LintGuard] Completed successfully → reports stored in $REPORTS_DIR"
}

main "$@"
