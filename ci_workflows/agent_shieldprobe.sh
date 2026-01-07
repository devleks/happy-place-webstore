#!/bin/bash
# Agent ShieldProbe: Privacy and security checks for backend + frontend
# macOS-optimized version with parallel scanning and enhanced reporting
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
CACHE_DIR="$ROOT_DIR/.shieldprobe_cache"
mkdir -p "$REPORTS_DIR" "$CACHE_DIR"

BACKEND_AUDIT="$REPORTS_DIR/shieldprobe_backend.json"
FRONTEND_AUDIT="$REPORTS_DIR/shieldprobe_frontend.json"
ENCRYPTION_LOG="$REPORTS_DIR/shieldprobe_encryption.log"
SHIPPING_LOG="$REPORTS_DIR/shieldprobe_shipping.log"
SECRETS_SCAN="$REPORTS_DIR/shieldprobe_secrets.txt"
SUMMARY_REPORT="$REPORTS_DIR/security_findings.json"

# Colors
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Severity levels (bash 3.2 compatible)
SEVERITY_CRITICAL=0
SEVERITY_HIGH=0
SEVERITY_MEDIUM=0
SEVERITY_LOW=0

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
log_info() {
    echo -e "${BLUE}[ShieldProbe]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[ShieldProbe]${NC} ✓ $1"
}

log_warning() {
    echo -e "${YELLOW}[ShieldProbe]${NC} ⚠ $1"
}

log_error() {
    echo -e "${RED}[ShieldProbe]${NC} ✗ $1" >&2
}

timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================
bootstrap_python_tooling() {
    if [ "${SKIP_AGENT_BOOTSTRAP:-0}" -eq 1 ]; then
        log_info "Skipping bootstrap (SKIP_AGENT_BOOTSTRAP=1)"
        return 0
    fi
    
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "python3 is required"
        if is_macos; then
            log_info "Install with: brew install python@3.11"
        fi
        return 1
    fi
    
    log_info "Installing security scanning tools..."

    # Use --break-system-packages on macOS for Homebrew Python
    local pip_flags="--user --upgrade --quiet"
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        pip_flags="--upgrade --quiet"
    elif is_macos && [[ "$(which python3)" == *"/opt/homebrew/"* ]]; then
        pip_flags="--break-system-packages --upgrade --quiet"
    fi
    
    python3 -m pip install $pip_flags pip-audit safety 2>&1 | grep -v "Requirement already satisfied" || true
    hash -r 2>/dev/null || true
    
    # Verify installation
    if ! python3 -m pip_audit --version >/dev/null 2>&1; then
        log_warning "pip-audit not available, security scanning will be limited"
    fi
    
    log_success "Security tools ready"
}

# ============================================================================
# BACKEND SECURITY SCANS
# ============================================================================
run_pip_audit() {
    local start_time=$(date +%s)
    
    if [ ! -d "$ROOT_DIR/backend" ]; then
        log_warning "Backend directory not found, skipping pip-audit"
        echo '{"vulnerabilities": [], "skipped": "no backend directory"}' > "$BACKEND_AUDIT"
        return 0
    fi
    
    if [ ! -f "$ROOT_DIR/backend/requirements.txt" ]; then
        log_warning "requirements.txt not found, skipping pip-audit"
        echo '{"vulnerabilities": [], "skipped": "no requirements.txt"}' > "$BACKEND_AUDIT"
        return 0
    fi
    
    pushd "$ROOT_DIR/backend" >/dev/null
    
    log_info "Running pip-audit on Python dependencies..."
    
    # Run pip-audit with caching
    if python3 -m pip_audit \
        -r requirements.txt \
        --format json \
        --cache-dir "$CACHE_DIR/pip-audit" \
        > "$BACKEND_AUDIT" 2>/dev/null; then
        log_success "pip-audit completed cleanly"
    else
        local exit_code=$?
        if [ $exit_code -eq 1 ]; then
            log_warning "pip-audit found vulnerabilities (see report)"
        else
            log_warning "pip-audit had issues (exit code: $exit_code)"
        fi
    fi
    
    popd >/dev/null
    
    # Count vulnerabilities
    if command -v jq >/dev/null 2>&1 && [ -f "$BACKEND_AUDIT" ]; then
        local vuln_count
        vuln_count=$(jq '.vulnerabilities | length' "$BACKEND_AUDIT" 2>/dev/null || echo 0)
        if [ "$vuln_count" -gt 0 ]; then
            log_warning "Found $vuln_count backend vulnerabilities"
        fi
    fi
    
    local duration=$(($(date +%s) - start_time))
    log_info "Backend audit completed in ${duration}s"
}

# ============================================================================
# FRONTEND SECURITY SCANS
# ============================================================================
run_npm_audit() {
    local start_time=$(date +%s)
    
    if [ ! -d "$ROOT_DIR/frontend" ]; then
        log_warning "Frontend directory not found, skipping npm audit"
        echo '{"vulnerabilities": {}, "skipped": "no frontend directory"}' > "$FRONTEND_AUDIT"
        return 0
    fi
    
    pushd "$ROOT_DIR/frontend" >/dev/null
    
    if [ ! -f "package.json" ]; then
        log_warning "package.json not found, skipping npm audit"
        echo '{"vulnerabilities": {}, "skipped": "no package.json"}' > "$FRONTEND_AUDIT"
        popd >/dev/null
        return 0
    fi
    
    log_info "Running npm audit on frontend dependencies..."
    
    # Run npm audit (non-zero exit is expected when vulns found)
    npm audit --json > "$FRONTEND_AUDIT" 2>/dev/null || {
        local npm_exit=$?
        if [ $npm_exit -eq 1 ]; then
            log_warning "npm audit found vulnerabilities (see report)"
        else
            log_warning "npm audit had issues (exit code: $npm_exit)"
        fi
    }
    
    popd >/dev/null
    
    # Count vulnerabilities by severity
    if command -v jq >/dev/null 2>&1 && [ -f "$FRONTEND_AUDIT" ]; then
        local critical high moderate low
        critical=$(jq -r '.metadata.vulnerabilities.critical // 0' "$FRONTEND_AUDIT" 2>/dev/null || echo 0)
        high=$(jq -r '.metadata.vulnerabilities.high // 0' "$FRONTEND_AUDIT" 2>/dev/null || echo 0)
        moderate=$(jq -r '.metadata.vulnerabilities.moderate // 0' "$FRONTEND_AUDIT" 2>/dev/null || echo 0)
        low=$(jq -r '.metadata.vulnerabilities.low // 0' "$FRONTEND_AUDIT" 2>/dev/null || echo 0)
        
        SEVERITY_CRITICAL=$critical
        SEVERITY_HIGH=$high
        SEVERITY_MEDIUM=$moderate
        SEVERITY_LOW=$low
        
        local total=$((critical + high + moderate + low))
        if [ "$total" -gt 0 ]; then
            log_warning "Found $total frontend vulnerabilities (critical: $critical, high: $high)"
        fi
    fi
    
    local duration=$(($(date +%s) - start_time))
    log_info "Frontend audit completed in ${duration}s"
}

# ============================================================================
# SECRET SCANNING
# ============================================================================
scan_for_secrets() {
    log_info "Scanning for exposed secrets..."
    
    local patterns=(
        "password.*=.*['\"]"
        "api[_-]?key.*=.*['\"]"
        "secret.*=.*['\"]"
        "token.*=.*['\"]"
        "aws[_-]?access"
        "private[_-]?key"
        "BEGIN RSA PRIVATE KEY"
        "BEGIN PRIVATE KEY"
    )
    
    {
        echo "# Secret Scan Results"
        echo "Generated: $(timestamp)"
        echo ""
        echo "## Potential Secrets Found"
        echo ""
    } > "$SECRETS_SCAN"
    
    local found=false
    for pattern in "${patterns[@]}"; do
        local matches
        matches=$(grep -r -i -n -E "$pattern" "$ROOT_DIR" \
            --exclude-dir=node_modules \
            --exclude-dir=.git \
            --exclude-dir=venv \
            --exclude-dir=build \
            --exclude-dir=dist \
            --exclude="*.min.js" \
            --exclude="*.log" \
            2>/dev/null || true)
        
        if [ -n "$matches" ]; then
            echo "### Pattern: $pattern" >> "$SECRETS_SCAN"
            echo '```' >> "$SECRETS_SCAN"
            line_count=0
            while IFS= read -r match_line; do
                echo "$match_line" >> "$SECRETS_SCAN"
                line_count=$((line_count + 1))
                if [ "$line_count" -ge 20 ]; then
                    break
                fi
            done <<< "$matches"
            echo '```' >> "$SECRETS_SCAN"
            echo "" >> "$SECRETS_SCAN"
            found=true
        fi
    done
    
    if [ "$found" = false ]; then
        echo "✓ No obvious secrets found" >> "$SECRETS_SCAN"
        log_success "No exposed secrets detected"
    else
        log_warning "Potential secrets found - review $SECRETS_SCAN"
    fi
}

# ============================================================================
# PRIVACY & COMPLIANCE TESTS
# ============================================================================
run_privacy_tests() {
    local encryption_script="$ROOT_DIR/backend/scripts/test_encryption.py"
    local shipping_script="$ROOT_DIR/backend/test_shipping.sh"
    
    # Encryption tests
    if [ -f "$encryption_script" ]; then
        log_info "Running encryption regression tests..."
        pushd "$ROOT_DIR/backend" >/dev/null
        
        if python3 scripts/test_encryption.py > "$ENCRYPTION_LOG" 2>&1; then
            log_success "Encryption tests passed"
        else
            log_warning "Encryption tests had failures (see $ENCRYPTION_LOG)"
        fi
        
        popd >/dev/null
    else
        log_info "Encryption test script not found, skipping"
        echo "Test script not found at $encryption_script" > "$ENCRYPTION_LOG"
    fi
    
    # Shipping/auth smoke tests
    if [ -f "$shipping_script" ]; then
        log_info "Running shipping/auth smoke tests..."
        pushd "$ROOT_DIR/backend" >/dev/null
        
        if bash test_shipping.sh > "$SHIPPING_LOG" 2>&1; then
            log_success "Shipping tests passed"
        else
            log_warning "Shipping tests had failures (see $SHIPPING_LOG)"
        fi
        
        popd >/dev/null
    else
        log_info "Shipping test script not found, skipping"
        echo "Test script not found at $shipping_script" > "$SHIPPING_LOG"
    fi
}

# ============================================================================
# REPORTING
# ============================================================================
write_summary() {
    # Calculate total vulnerabilities
    local total_vulns
    total_vulns=$((SEVERITY_CRITICAL + SEVERITY_HIGH + SEVERITY_MEDIUM + SEVERITY_LOW))
    
    # Determine risk level
    local risk_level="low"
    if [ "$SEVERITY_CRITICAL" -gt 0 ]; then
        risk_level="critical"
    elif [ "$SEVERITY_HIGH" -gt 0 ]; then
        risk_level="high"
    elif [ "$SEVERITY_MEDIUM" -gt 5 ]; then
        risk_level="medium"
    fi
    
    cat >"$SUMMARY_REPORT" <<JSON
{
  "agent": "ShieldProbe",
  "version": "2.0-macos",
  "generated_at": "$(timestamp)",
  "execution_time_seconds": $SECONDS,
  "risk_level": "$risk_level",
  "artifacts": {
    "pip_audit": "reports/$(basename "$BACKEND_AUDIT")",
    "npm_audit": "reports/$(basename "$FRONTEND_AUDIT")",
    "secrets_scan": "reports/$(basename "$SECRETS_SCAN")",
    "encryption": "reports/$(basename "$ENCRYPTION_LOG")",
    "shipping_smoke": "reports/$(basename "$SHIPPING_LOG")"
  },
  "vulnerabilities": {
    "total": $total_vulns,
    "critical": $SEVERITY_CRITICAL,
    "high": $SEVERITY_HIGH,
    "medium": $SEVERITY_MEDIUM,
    "low": $SEVERITY_LOW
  },
  "next_steps": [
    "Patch vulnerable packages listed in pip/npm audits",
    "Review potential secrets in secrets scan report",
    "Verify encryption logs for assertion failures",
    "Confirm shipping/auth endpoints reject unauthorized requests"
  ]
}
JSON
    
    # Console summary
    log_info "════════════════════════════════════════"
    log_info "Security Scan Summary:"
    log_info "  Risk Level: $risk_level"
    log_info "  Total Vulnerabilities: $total_vulns"
    log_info "  Critical: $SEVERITY_CRITICAL"
    log_info "  High: $SEVERITY_HIGH"
    log_info "  Medium: $SEVERITY_MEDIUM"
    log_info "  Low: $SEVERITY_LOW"
    log_info "════════════════════════════════════════"
    
    # Warning if critical/high vulns
    if [ "$SEVERITY_CRITICAL" -gt 0 ] || [ "$SEVERITY_HIGH" -gt 0 ]; then
        log_error "CRITICAL OR HIGH SEVERITY VULNERABILITIES FOUND!"
        log_error "Review reports immediately and patch before deployment"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
main() {
    local start_time=$(date +%s)
    
    log_info "Starting privacy/security checks"
    log_info "Platform: $(uname -s) $(uname -m)"
    
    # Validate environment
    bootstrap_python_tooling || exit 1
    
    # Run security scans in parallel
    run_pip_audit &
    local pip_pid=$!
    
    run_npm_audit &
    local npm_pid=$!
    
    scan_for_secrets &
    local secrets_pid=$!
    
    # Wait for parallel scans
    wait $pip_pid $npm_pid $secrets_pid
    
    # Run privacy tests (sequential)
    run_privacy_tests
    
    # Generate summary
    write_summary
    
    local duration=$(($(date +%s) - start_time))
    log_success "Completed in ${duration}s → reports in $REPORTS_DIR"
    
    # Exit with warning if high-severity issues found
    if [ "$SEVERITY_CRITICAL" -gt 0 ]; then
        log_warning "Exiting with warning due to critical vulnerabilities"
        return 1
    fi
    
    return 0
}

# Cleanup
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "ShieldProbe completed with issues (exit code $exit_code)"
    fi
    return $exit_code
}

trap cleanup EXIT

main "$@"
