#!/bin/bash
# Agent AtlasReporter: Consolidated digest from all agent outputs
# macOS-optimized version with enhanced formatting and analysis
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
mkdir -p "$REPORTS_DIR"

DIGEST_FILE="$REPORTS_DIR/weekly_agent_digest.md"
DIGEST_JSON="$REPORTS_DIR/weekly_agent_digest.json"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
log_info() {
    echo -e "${BLUE}[AtlasReporter]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[AtlasReporter]${NC} ✓ $1"
}

log_warning() {
    echo -e "${YELLOW}[AtlasReporter]${NC} ⚠ $1"
}

log_error() {
    echo -e "${RED}[AtlasReporter]${NC} ✗ $1" >&2
}

timestamp() {
    date -u +"%Y-%m-%d %H:%M:%S UTC"
}

is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

# ============================================================================
# DATA EXTRACTION
# ============================================================================
json_timestamp() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo "missing"
        return
    fi
    
    python3 - "$file" 2>/dev/null <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
        print(data.get("generated_at", data.get("timestamp", "unknown")))
except Exception as e:
    print(f"unreadable: {e}")
PY
}

json_field() {
    local file="$1"
    local field="$2"
    local default="${3:-0}"
    
    if [ ! -f "$file" ]; then
        echo "$default"
        return
    fi
    
    python3 - "$file" "$field" "$default" 2>/dev/null <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
        # Navigate nested fields (e.g., "vulnerabilities.total")
        keys = sys.argv[2].split('.')
        value = data
        for key in keys:
            value = value.get(key, sys.argv[3])
            if value == sys.argv[3]:
                break
        print(value)
except Exception:
    print(sys.argv[3])
PY
}

file_exists_status() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "✓ available"
    else
        echo "✗ missing"
    fi
}

# ============================================================================
# STATUS COLLECTION
# ============================================================================
collect_lintguard_status() {
    local report="$REPORTS_DIR/lintguard.json"
    local timestamp
    timestamp=$(json_timestamp "$report")
    
    local total_issues
    total_issues=$(json_field "$report" "summary.total_issues" "unknown")
    
    echo "lintguard|$timestamp|$total_issues issues"
}

collect_schemasage_status() {
    local report="$REPORTS_DIR/db_audit.md"
    local status
    status=$(file_exists_status "$report")
    
    local timestamp="N/A"
    if [ -f "$report" ]; then
        timestamp=$(grep "Generated:" "$report" 2>/dev/null | cut -d: -f2- | xargs || echo "unknown")
    fi
    
    echo "schemasage|$timestamp|$status"
}

collect_perfsmith_status() {
    local report="$REPORTS_DIR/perfsmith_summary.json"
    local timestamp
    timestamp=$(json_timestamp "$report")
    
    local recommendations
    recommendations=$(json_field "$report" "recommendations" "[]" | python3 -c "import sys,json; print(len(json.loads(sys.stdin.read())))")
    
    echo "perfsmith|$timestamp|$recommendations recommendations"
}

collect_shieldprobe_status() {
    local report="$REPORTS_DIR/security_findings.json"
    local timestamp
    timestamp=$(json_timestamp "$report")
    
    local total_vulns
    total_vulns=$(json_field "$report" "vulnerabilities.total" "unknown")
    
    local risk_level
    risk_level=$(json_field "$report" "risk_level" "unknown")
    
    echo "shieldprobe|$timestamp|$total_vulns vulnerabilities|$risk_level"
}

# ============================================================================
# ISSUE AGGREGATION
# ============================================================================
aggregate_critical_issues() {
    local issues=()
    
    # Check LintGuard issues
    local lint_issues
    lint_issues=$(json_field "$REPORTS_DIR/lintguard.json" "summary.total_issues" 0)
    if [ "$lint_issues" -gt 50 ]; then
        issues+=("🔴 **CRITICAL**: $lint_issues static analysis issues detected")
    elif [ "$lint_issues" -gt 0 ]; then
        issues+=("🟡 **Warning**: $lint_issues static analysis issues found")
    fi
    
    # Check ShieldProbe vulnerabilities
    local critical_vulns high_vulns
    critical_vulns=$(json_field "$REPORTS_DIR/security_findings.json" "vulnerabilities.critical" 0)
    high_vulns=$(json_field "$REPORTS_DIR/security_findings.json" "vulnerabilities.high" 0)
    
    if [ "$critical_vulns" -gt 0 ]; then
        issues+=("🔴 **CRITICAL**: $critical_vulns critical security vulnerabilities")
    fi
    if [ "$high_vulns" -gt 0 ]; then
        issues+=("🟠 **High**: $high_vulns high severity vulnerabilities")
    fi
    
    # Check database issues (look for Seq Scan in explain)
    if [ -f "$REPORTS_DIR/schemasage_explain.txt" ]; then
        local seq_scans
        seq_scans=$(grep -c "Seq Scan" "$REPORTS_DIR/schemasage_explain.txt" 2>/dev/null || echo 0)
        if [ "$seq_scans" -gt 5 ]; then
            issues+=("🟡 **Warning**: $seq_scans sequential scans detected (consider indexing)")
        fi
    fi
    
    printf '%s\n' "${issues[@]}"
}

# ============================================================================
# DIGEST GENERATION
# ============================================================================
write_markdown_digest() {
    # Collect statuses
    local lint_status schema_status perf_status shield_status
    lint_status=$(collect_lintguard_status)
    schema_status=$(collect_schemasage_status)
    perf_status=$(collect_perfsmith_status)
    shield_status=$(collect_shieldprobe_status)
    
    # Get critical issues
    local issues
    mapfile -t issues < <(aggregate_critical_issues)
    
    cat >"$DIGEST_FILE" <<MARKDOWN
# 🤖 Weekly Agent Digest
**Generated:** $(timestamp)  
**Platform:** $(uname -s) $(uname -m)  
**Workflow:** Happy Place Agents v2.0

---

## 📊 Executive Summary
MARKDOWN

    if [ ${#issues[@]} -eq 0 ]; then
        echo "✅ **All Clear** - No critical issues detected across all agents" >> "$DIGEST_FILE"
    else
        echo "⚠️  **Attention Required** - The following issues need review:" >> "$DIGEST_FILE"
        echo "" >> "$DIGEST_FILE"
        printf '%s\n' "${issues[@]}" >> "$DIGEST_FILE"
    fi
    
    cat >>"$DIGEST_FILE" <<MARKDOWN

---

## 📋 Agent Status

### 🔍 LintGuard - Static Analysis
- **Status:** ${lint_status#*|}
- **Artifacts:** 
  - \`reports/lintguard.json\` - Consolidated report
  - \`reports/lintguard_ruff.json\` - Python (Ruff)
  - \`reports/lintguard_bandit.json\` - Security (Bandit)
  - \`reports/lintguard_eslint.json\` - Frontend (ESLint)

### 🗄️  SchemaSage - Database Analysis
- **Status:** ${schema_status#*|}
- **Artifacts:**
  - \`reports/db_audit.md\` - Audit summary
  - \`reports/schemasage_schema.txt\` - Schema snapshot
  - \`reports/schemasage_indexes.txt\` - Index analysis
  - \`reports/schemasage_explain.txt\` - Query plans

### ⚡ PerfSmith - Performance Analysis
- **Status:** ${perf_status#*|}
- **Artifacts:**
  - \`reports/perfsmith_summary.json\` - Performance summary
  - \`reports/perfsmith_hotspots.md\` - Code hotspots
  - \`reports/perfsmith_bundle.json\` - Bundle analysis

### 🛡️  ShieldProbe - Security & Privacy
- **Status:** ${shield_status#*|}
- **Artifacts:**
  - \`reports/security_findings.json\` - Consolidated findings
  - \`reports/shieldprobe_backend.json\` - Backend vulnerabilities
  - \`reports/shieldprobe_frontend.json\` - Frontend vulnerabilities
  - \`reports/shieldprobe_secrets.txt\` - Secret scan

---

## 🎯 Recommended Actions

### Immediate (P0)
MARKDOWN

    # Add P0 actions based on critical issues
    if [ "$critical_vulns" -gt 0 ] 2>/dev/null; then
        echo "1. **URGENT**: Patch $critical_vulns critical security vulnerabilities" >> "$DIGEST_FILE"
    fi
    if [ "$lint_issues" -gt 100 ] 2>/dev/null; then
        echo "2. Address high-priority static analysis findings before merge" >> "$DIGEST_FILE"
    fi
    
    cat >>"$DIGEST_FILE" <<MARKDOWN

### Short-term (P1)
1. Review and apply database index recommendations from SchemaSage
2. Refactor large files identified in PerfSmith hotspot analysis
3. Update dependencies with known vulnerabilities
4. Review and remove any exposed secrets from codebase

### Long-term (P2)
1. Establish baseline metrics for static analysis violations
2. Implement automated dependency scanning in pre-commit hooks
3. Set up performance budgets for bundle sizes
4. Regular database maintenance schedule (VACUUM, ANALYZE)

---

## 📈 Trends & Metrics

MARKDOWN

    # Add metrics table
    echo "| Metric | Current | Status |" >> "$DIGEST_FILE"
    echo "|--------|---------|--------|" >> "$DIGEST_FILE"
    echo "| Static Analysis Issues | $lint_issues | $([ "$lint_issues" -lt 20 ] && echo "✅ Good" || echo "⚠️  Needs Work") |" >> "$DIGEST_FILE"
    echo "| Security Vulnerabilities | $((critical_vulns + high_vulns)) | $([ "$((critical_vulns + high_vulns))" -eq 0 ] && echo "✅ Good" || echo "🔴 Action Required") |" >> "$DIGEST_FILE"
    echo "| Database Sequential Scans | $seq_scans | $([ "$seq_scans" -lt 5 ] && echo "✅ Good" || echo "⚠️  Review Needed") |" >> "$DIGEST_FILE"
    
    cat >>"$DIGEST_FILE" <<MARKDOWN

---

## 💡 Quick Wins

### Code Quality
\`\`\`bash
# Fix auto-fixable linting issues
cd frontend && npx eslint --fix "src/**/*.{js,jsx}"
cd backend && python3 -m ruff check --fix .
\`\`\`

### Security
\`\`\`bash
# Update vulnerable packages
npm audit fix
pip-audit --fix
\`\`\`

### Performance
\`\`\`bash
# Analyze bundle size
cd frontend && npx source-map-explorer build/static/js/*.js
\`\`\`

### Database
\`\`\`sql
-- Find and fix missing indexes
SELECT schemaname, tablename, seq_scan, idx_scan 
FROM pg_stat_user_tables 
WHERE seq_scan > idx_scan * 10
ORDER BY seq_scan DESC;
\`\`\`

---

## 📎 Attachments

For detailed findings, review individual agent reports in the \`reports/\` directory or download the complete artifact bundle from GitHub Actions.

**Next Digest:** $(date -u -v+7d +"%Y-%m-%d" 2>/dev/null || date -u -d "+7 days" +"%Y-%m-%d")

---

*Generated by AtlasReporter v2.0 • [View Workflow](../../actions)*
MARKDOWN
}

write_json_digest() {
    cat >"$DIGEST_JSON" <<JSON
{
  "generated_at": "$(timestamp)",
  "platform": "$(uname -s)",
  "agents": {
    "lintguard": $(cat "$REPORTS_DIR/lintguard.json" 2>/dev/null || echo '{"status": "missing"}'),
    "schemasage": {
      "status": "$(file_exists_status "$REPORTS_DIR/db_audit.md")"
    },
    "perfsmith": $(cat "$REPORTS_DIR/perfsmith_summary.json" 2>/dev/null || echo '{"status": "missing"}'),
    "shieldprobe": $(cat "$REPORTS_DIR/security_findings.json" 2>/dev/null || echo '{"status": "missing"}')
  },
  "summary": {
    "total_lint_issues": $(json_field "$REPORTS_DIR/lintguard.json" "summary.total_issues" 0),
    "total_vulnerabilities": $(json_field "$REPORTS_DIR/security_findings.json" "vulnerabilities.total" 0),
    "critical_vulnerabilities": $(json_field "$REPORTS_DIR/security_findings.json" "vulnerabilities.critical" 0),
    "high_vulnerabilities": $(json_field "$REPORTS_DIR/security_findings.json" "vulnerabilities.high" 0),
    "risk_level": "$(json_field "$REPORTS_DIR/security_findings.json" "risk_level" "unknown")"
  }
}
JSON
}

# ============================================================================
# ARTIFACT VALIDATION
# ============================================================================
validate_artifacts() {
    log_info "Validating agent outputs..."
    
    local expected_files=(
        "lintguard.json"
        "db_audit.md"
        "perfsmith_hotspots.md"
        "security_findings.json"
    )
    
    local missing=()
    for file in "${expected_files[@]}"; do
        if [ ! -f "$REPORTS_DIR/$file" ]; then
            missing+=("$file")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        log_warning "Missing artifacts: ${missing[*]}"
        log_info "Digest will reflect incomplete data"
    else
        log_success "All expected artifacts present"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
main() {
    local start_time=$(date +%s)
    
    log_info "Building consolidated agent digest"
    log_info "Platform: $(uname -s) $(uname -m)"
    
    # Validate inputs
    validate_artifacts
    
    # Generate digests
    log_info "Generating markdown digest..."
    write_markdown_digest
    
    log_info "Generating JSON digest..."
    write_json_digest
    
    # Summary
    local digest_size
    if is_macos; then
        digest_size=$(stat -f %z "$DIGEST_FILE" | awk '{printf "%.1fKB", $1/1024}')
    else
        digest_size=$(stat -c %s "$DIGEST_FILE" | awk '{printf "%.1fKB", $1/1024}')
    fi
    
    local duration=$(($(date +%s) - start_time))
    
    log_success "Digest ready ($digest_size) → $DIGEST_FILE"
    log_success "JSON digest → $DIGEST_JSON"
    log_info "Completed in ${duration}s"
    
    # Show critical issues on console
    local critical_count
    critical_count=$(grep -c "🔴 \*\*CRITICAL\*\*" "$DIGEST_FILE" 2>/dev/null || echo 0)
    
    if [ "$critical_count" -gt 0 ]; then
        log_warning "═══════════════════════════════════════════"
        log_warning "$critical_count CRITICAL ISSUES DETECTED"
        log_warning "Review $DIGEST_FILE immediately"
        log_warning "═══════════════════════════════════════════"
    fi
    
    return 0
}

# Cleanup
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "AtlasReporter failed with exit code $exit_code"
    fi
    return $exit_code
}

trap cleanup EXIT

main "$@"
