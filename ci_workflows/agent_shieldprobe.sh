#!/bin/bash
# Agent ShieldProbe: Privacy and security checks for backend + frontend
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"

BACKEND_AUDIT="$REPORTS_DIR/shieldprobe_backend.json"
FRONTEND_AUDIT="$REPORTS_DIR/shieldprobe_frontend.json"
ENCRYPTION_LOG="$REPORTS_DIR/shieldprobe_encryption.log"
SHIPPING_LOG="$REPORTS_DIR/shieldprobe_shipping.log"
SUMMARY_REPORT="$REPORTS_DIR/security_findings.json"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

bootstrap_python_tooling() {
  if [ "${SKIP_AGENT_BOOTSTRAP:-0}" -eq 1 ]; then
    return
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "[ShieldProbe] python3 is required" >&2
    exit 1
  fi

  python3 -m pip install --user --upgrade pip-audit >/dev/null 2>&1 || true
  hash -r
}

run_pip_audit() {
  echo "[ShieldProbe] Running pip-audit"
  pushd "$ROOT_DIR/backend" >/dev/null
  python3 -m pip_audit -r requirements.txt -f json >"$BACKEND_AUDIT" || true
  popd >/dev/null
}

run_npm_audit() {
  echo "[ShieldProbe] Running npm audit"
  pushd "$ROOT_DIR/frontend" >/dev/null
  npm audit --json >"$FRONTEND_AUDIT" || true
  popd >/dev/null
}

run_privacy_tests() {
  echo "[ShieldProbe] Running encryption regression script"
  pushd "$ROOT_DIR/backend" >/dev/null
  python3 scripts/test_encryption.py >"$ENCRYPTION_LOG" 2>&1 || true
  echo "[ShieldProbe] Running shipping/auth smoke tests"
  bash test_shipping.sh >"$SHIPPING_LOG" 2>&1 || true
  popd >/dev/null
}

write_summary() {
  cat >"$SUMMARY_REPORT" <<JSON
{
  "agent": "ShieldProbe",
  "generated_at": "$(timestamp)",
  "artifacts": {
    "pip_audit": "reports/$(basename "$BACKEND_AUDIT")",
    "npm_audit": "reports/$(basename "$FRONTEND_AUDIT")",
    "encryption": "reports/$(basename "$ENCRYPTION_LOG")",
    "shipping_smoke": "reports/$(basename "$SHIPPING_LOG")"
  },
  "next_steps": [
    "Patch vulnerable packages listed in pip/npm audits",
    "Review encryption logs for assertion failures",
    "Verify shipping/auth endpoints reject unauthorized requests"
  ]
}
JSON
}

main() {
  echo "[ShieldProbe] Starting privacy/security checks"
  bootstrap_python_tooling
  run_pip_audit
  run_npm_audit
  run_privacy_tests
  write_summary
  echo "[ShieldProbe] Completed"
}

main "$@"
