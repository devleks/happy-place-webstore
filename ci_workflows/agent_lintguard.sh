#!/bin/bash
# Agent LintGuard: Static code analysis for backend (Python) and frontend (React)
# macOS-optimized version with parallel execution and enhanced error handling
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
CACHE_DIR="$ROOT_DIR/.lintguard_cache"
mkdir -p "$REPORTS_DIR" "$CACHE_DIR"

RUFF_REPORT="$REPORTS_DIR/lintguard_ruff.json"
BANDIT_REPORT="$REPORTS_DIR/lintguard_bandit.json"
ESLINT_REPORT="$REPORTS_DIR/lintguard_eslint.json"
SUMMARY_REPORT="$REPORTS_DIR/lintguard.json"

# Colors for better UX
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
log_info() {
    echo -e "${BLUE}[LintGuard]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[LintGuard]${NC} ✓ $1"
}

log_warning() {
    echo -e "${YELLOW}[LintGuard]${NC} ⚠ $1"
}

log_error() {
    echo -e "${RED}[LintGuard]${NC} ✗ $1" >&2
}

timestamp() {
    # BSD date (macOS) compatible
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# Check if running on macOS
is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

# Validate command exists
require_command() {
    local cmd=$1
    local install_hint=${2:-""}
    
    if ! command -v "$cmd" >/dev/null 2>&1; then
        log_error "$cmd is not installed"
        if [ -n "$install_hint" ]; then
            log_info "Install with: $install_hint"
        fi
        return 1
    fi
    return 0
}

# Calculate file hash for cache validation
file_hash() {
    local file=$1
    if is_macos; then
        md5 -q "$file" 2>/dev/null || echo "none"
    else
        md5sum "$file" 2>/dev/null | cut -d' ' -f1 || echo "none"
    fi
}

# Check if cache is valid
cache_valid() {
    local cache_file=$1
    local source_pattern=$2
    local max_age_minutes=${3:-60}
    
    # Check if cache exists and is recent
    if [ ! -f "$cache_file" ]; then
        return 1
    fi
    
    # Check age (macOS stat format)
    local cache_age
    if is_macos; then
        cache_age=$(( ($(date +%s) - $(stat -f %m "$cache_file")) / 60 ))
    else
        cache_age=$(( ($(date +%s) - $(stat -c %Y "$cache_file")) / 60 ))
    fi
    
    if [ "$cache_age" -gt "$max_age_minutes" ]; then
        return 1
    fi
    
    # Check if source files changed
    local current_hash
    current_hash=$(find "$ROOT_DIR" -name "$source_pattern" -type f -exec cat {} \; 2>/dev/null | file_hash -)
    local cached_hash
    cached_hash=$(cat "$cache_file.hash" 2>/dev/null || echo "none")
    
    [ "$current_hash" = "$cached_hash" ]
}

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================
bootstrap_python_tooling() {
    if [ "${SKIP_AGENT_BOOTSTRAP:-0}" -eq 1 ]; then
        log_info "Skipping bootstrap (SKIP_AGENT_BOOTSTRAP=1)"
        return 0
    fi
    
    require_command python3 "brew install python@3.11" || exit 1
    
    log_info "Installing Python linting tools..."
    
    # Use --break-system-packages on macOS for Homebrew Python
    local pip_flags="--user --upgrade --quiet"
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        pip_flags="--upgrade --quiet"
    elif is_macos && [[ "$(which python3)" == *"/opt/homebrew/"* ]]; then
        pip_flags="--break-system-packages --upgrade --quiet"
    fi
    
    # Install with progress indicator
    {
        python3 -m pip install $pip_flags ruff bandit 2>&1 | grep -v "Requirement already satisfied" || true
    } &
    local pip_pid=$!
    
    # Show progress
    while kill -0 $pip_pid 2>/dev/null; do
        echo -n "."
        sleep 0.5
    done
    echo ""
    
    wait $pip_pid
    
    # Refresh command hash
    hash -r 2>/dev/null || true
    
    # Verify installation
    if ! python3 -m ruff --version >/dev/null 2>&1; then
        log_error "Ruff installation failed"
        return 1
    fi
    
    if ! python3 -m bandit --version >/dev/null 2>&1; then
        log_error "Bandit installation failed"
        return 1
    fi
    
    log_success "Python tools installed"
}

# ============================================================================
# LINTING FUNCTIONS
# ============================================================================
run_python_linters() {
    local start_time=$(date +%s)
    
    if [ ! -d "$ROOT_DIR/backend" ]; then
        log_warning "Backend directory not found, skipping Python linters"
        return 0
    fi
    
    pushd "$ROOT_DIR/backend" >/dev/null
    
    # Run Ruff and Bandit in parallel for speed
    log_info "Running Python linters in parallel..."
    
    # Ruff in background
    {
        log_info "Running Ruff..."
        python3 -m ruff check . \
            --output-format json \
            --cache-dir "$CACHE_DIR/ruff" \
            > "$RUFF_REPORT" 2>/dev/null || true
        log_success "Ruff completed"
    } &
    local ruff_pid=$!
    
    # Bandit in background
    {
        log_info "Running Bandit..."
        python3 -m bandit -r . \
            -x "./venv,./.venv,./venv_*,./venv_broken_*,venv,.venv,venv_*,venv_broken_*,./scripts,./tests,./migrations,./reset_admin_password.py,./test_admin_login_direct.py,./test_passwords.py" \
            -f json \
            -o "$BANDIT_REPORT" \
            --silent 2>/dev/null || true
        log_success "Bandit completed"
    } &
    local bandit_pid=$!
    
    # Wait for both to complete
    wait $ruff_pid $bandit_pid
    
    popd >/dev/null
    
    local duration=$(($(date +%s) - start_time))
    log_success "Python linters completed in ${duration}s"
}

run_frontend_eslint() {
    local start_time=$(date +%s)
    
    if [ ! -d "$ROOT_DIR/frontend" ]; then
        log_warning "Frontend directory not found, skipping ESLint"
        return 0
    fi
    
    pushd "$ROOT_DIR/frontend" >/dev/null
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_warning "node_modules not found, running npm install..."
        npm ci --prefer-offline --no-audit >/dev/null 2>&1 || {
            log_error "npm install failed"
            popd >/dev/null
            return 1
        }
    fi
    
    log_info "Running ESLint..."
    
    # Use ESLint cache for faster runs
    npx eslint "src/**/*.{js,jsx,ts,tsx}" \
        --format json \
        --output-file "$ESLINT_REPORT" \
        --cache \
        --cache-location "$CACHE_DIR/eslint" \
        2>/dev/null || true
    
    popd >/dev/null
    
    local duration=$(($(date +%s) - start_time))
    log_success "ESLint completed in ${duration}s"
}

# ============================================================================
# REPORTING
# ============================================================================
count_issues() {
    local report=$1
    local tool=$2
    
    if [ ! -f "$report" ]; then
        echo 0
        return
    fi
    
    case $tool in
        ruff)
            python3 -c "import json; print(len(json.load(open('$report'))))" 2>/dev/null || echo 0
            ;;
        bandit)
            python3 -c "import json; d=json.load(open('$report')); print(len(d.get('results', [])))" 2>/dev/null || echo 0
            ;;
        eslint)
            python3 -c "import json; d=json.load(open('$report')); print(sum(len(f.get('messages', [])) for f in d))" 2>/dev/null || echo 0
            ;;
        *)
            echo 0
            ;;
    esac
}

write_summary() {
    local ruff_count bandit_count eslint_count
    ruff_count=$(count_issues "$RUFF_REPORT" ruff)
    bandit_count=$(count_issues "$BANDIT_REPORT" bandit)
    eslint_count=$(count_issues "$ESLINT_REPORT" eslint)
    
    cat >"$SUMMARY_REPORT" <<JSON
{
  "agent": "LintGuard",
  "version": "2.0-macos",
  "generated_at": "$(timestamp)",
  "execution_time_seconds": $SECONDS,
  "artifacts": {
    "ruff": "reports/$(basename "$RUFF_REPORT")",
    "bandit": "reports/$(basename "$BANDIT_REPORT")",
    "eslint": "reports/$(basename "$ESLINT_REPORT")"
  },
  "summary": {
    "ruff_issues": $ruff_count,
    "bandit_issues": $bandit_count,
    "eslint_issues": $eslint_count,
    "total_issues": $((ruff_count + bandit_count + eslint_count))
  },
  "notes": [
    "Review Ruff + Bandit JSON for rule-level detail",
    "ESLint report stores all frontend findings with rule metadata",
    "Cache enabled for faster subsequent runs"
  ]
}
JSON
    
    # Print summary to console
    log_info "════════════════════════════════════════"
    log_info "Issue Summary:"
    log_info "  Ruff:    $ruff_count"
    log_info "  Bandit:  $bandit_count"
    log_info "  ESLint:  $eslint_count"
    log_info "  Total:   $((ruff_count + bandit_count + eslint_count))"
    log_info "════════════════════════════════════════"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
main() {
    local overall_start=$(date +%s)
    
    log_info "Starting static analysis pipeline"
    log_info "Platform: $(uname -s) $(uname -m)"
    
    # Validate environment
    bootstrap_python_tooling || exit 1
    require_command npm "brew install node@18" || exit 1
    
    # Run linters (parallel where safe)
    run_python_linters &
    local python_pid=$!
    
    run_frontend_eslint &
    local frontend_pid=$!
    
    # Wait for all linters
    wait $python_pid $frontend_pid
    
    # Generate summary
    write_summary
    
    local total_duration=$(($(date +%s) - overall_start))
    log_success "Completed in ${total_duration}s → reports stored in $REPORTS_DIR"
    
    # Return exit code based on issues found
    local total_issues
    total_issues=$(python3 -c "import json; print(json.load(open('$SUMMARY_REPORT')).get('summary', {}).get('total_issues', 0))" 2>/dev/null || echo 0)
    
    if [ "$total_issues" -gt 0 ]; then
        log_warning "Found $total_issues issues"
        return 0  # Don't fail CI, just warn
    fi
    
    return 0
}

# Cleanup on exit
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "LintGuard failed with exit code $exit_code"
    fi
    return $exit_code
}

trap cleanup EXIT

# Run main
main "$@"
