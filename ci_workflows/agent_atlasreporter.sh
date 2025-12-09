#!/bin/bash
# Agent AtlasReporter: consolidates individual agent outputs into a digest
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"

DIGEST_FILE="$REPORTS_DIR/weekly_agent_digest.md"

timestamp() {
  date -u +"%Y-%m-%d %H:%M:%S UTC"
}

json_timestamp() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "missing"
    return
  fi
  python3 - <<PY 2>/dev/null
import json, pathlib, sys
path = pathlib.Path("$file")
try:
    data = json.loads(path.read_text())
    print(data.get("generated_at", "unknown"))
except Exception:
    print("unreadable")
PY
}

write_digest() {
  local lint_ts db_status perf_status shield_ts
  lint_ts=$(json_timestamp "$REPORTS_DIR/lintguard.json")
  shield_ts=$(json_timestamp "$REPORTS_DIR/security_findings.json")

  if [ -f "$REPORTS_DIR/db_audit.md" ]; then
    db_status="available"
  else
    db_status="missing"
  fi

  if [ -f "$REPORTS_DIR/perfsmith_hotspots.md" ]; then
    perf_status="available"
  else
    perf_status="missing"
  fi

  cat >"$DIGEST_FILE" <<MARKDOWN
# Weekly Agent Digest
Generated: $(timestamp)

## Status Snapshot
- **LintGuard:** $lint_ts (details: \`reports/lintguard.json\`)
- **SchemaSage:** $db_status (details: \`reports/db_audit.md\`)
- **PerfSmith:** $perf_status (details: \`reports/perfsmith_hotspots.md\`)
- **ShieldProbe:** $shield_ts (details: \`reports/security_findings.json\`)

## Artifact Index
1. Static Analysis → \`reports/lintguard_*.json\`
2. Database Audit → \`reports/schemasage_*.txt\`
3. Performance Study → \`reports/perfsmith_hotspots.md\`, \`reports/perfsmith_bundle.json\`
4. Security & Privacy → \`reports/shieldprobe_*.json\`, \`reports/security_findings.json\`

## Recommended Actions
1. Patch packages flagged by LintGuard/ShieldProbe before merging feature work.
2. Apply indexes suggested in SchemaSage explain plans to cut sequential scans.
3. Break down functions called out in PerfSmith hotspot table and consider code-splitting React modules.
4. Attach the above artifacts to the next pull request or release note for reviewer context.

## Code Snippet TODOs
- Paste problematic function excerpts referenced in \`perfsmith_hotspots.md\`.
- Capture SQL plans showing Seq Scan + Filter for historical tracking.
- Record remediation diffs after vulnerabilities are addressed.
MARKDOWN
}

main() {
  echo "[AtlasReporter] Building consolidated digest"
  write_digest
  echo "[AtlasReporter] Digest ready → $DIGEST_FILE"
}

main "$@"
