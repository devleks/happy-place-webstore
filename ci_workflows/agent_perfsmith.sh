#!/bin/bash
# Agent PerfSmith: Code optimization insights for backend + frontend
# macOS-optimized version with enhanced analysis and caching
set -euo pipefail

# ============================================================================
# CONFIGURATION
# ============================================================================
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$ROOT_DIR/reports"
CACHE_DIR="$ROOT_DIR/.perfsmith_cache"
mkdir -p "$REPORTS_DIR" "$CACHE_DIR"

HOTSPOT_REPORT="$REPORTS_DIR/perfsmith_hotspots.md"
BUNDLE_REPORT="$REPORTS_DIR/perfsmith_bundle.json"
LIGHTHOUSE_REPORT="$REPORTS_DIR/perfsmith_lighthouse.json"
SUMMARY_REPORT="$REPORTS_DIR/perfsmith_summary.json"

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
    echo -e "${BLUE}[PerfSmith]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PerfSmith]${NC} ✓ $1"
}

log_warning() {
    echo -e "${YELLOW}[PerfSmith]${NC} ⚠ $1"
}

log_error() {
    echo -e "${RED}[PerfSmith]${NC} ✗ $1" >&2
}

timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

# Get file size in human-readable format
file_size() {
    local file=$1
    if [ ! -f "$file" ]; then
        echo "0B"
        return
    fi
    
    if is_macos; then
        stat -f %z "$file" | awk '{
            if ($1 < 1024) print $1 "B"
            else if ($1 < 1048576) printf "%.1fKB\n", $1/1024
            else if ($1 < 1073741824) printf "%.1fMB\n", $1/1048576
            else printf "%.1fGB\n", $1/1073741824
        }'
    else
        stat -c %s "$file" | awk '{
            if ($1 < 1024) print $1 "B"
            else if ($1 < 1048576) printf "%.1fKB\n", $1/1024
            else if ($1 < 1073741824) printf "%.1fMB\n", $1/1048576
            else printf "%.1fGB\n", $1/1073741824
        }'
    fi
}

# ============================================================================
# HOTSPOT ANALYSIS
# ============================================================================
generate_hotspots() {
    local helper_script="$ROOT_DIR/ci_workflows/helpers/perfsmith_hotspots.py"
    
    if [ ! -f "$helper_script" ]; then
        log_warning "Hotspot analyzer not found: $helper_script"
        log_info "Creating basic hotspot report..."
        create_basic_hotspot_report
        return 0
    fi
    
    log_info "Generating code hotspot analysis..."
    
    local backend_dir="$ROOT_DIR/backend"
    local frontend_dir="$ROOT_DIR/frontend/src"
    
    if ! python3 "$helper_script" \
        --backend-dir "$backend_dir" \
        --frontend-dir "$frontend_dir" \
        --output "$HOTSPOT_REPORT" 2>/dev/null; then
        
        log_warning "Hotspot analysis failed, creating basic report"
        create_basic_hotspot_report
        return 0
    fi
    
    log_success "Hotspot analysis complete"
}

create_basic_hotspot_report() {
    cat >"$HOTSPOT_REPORT" <<MARKDOWN
# PerfSmith Code Hotspot Analysis
**Generated:** $(timestamp)

## Backend Analysis
MARKDOWN

    if [ -d "$ROOT_DIR/backend" ]; then
        echo "### Large Python Files" >> "$HOTSPOT_REPORT"
        find "$ROOT_DIR/backend" -name "*.py" -type f -exec wc -l {} \; 2>/dev/null | \
            sort -rn | head -10 | \
            awk '{printf "- %s (%d lines)\n", $2, $1}' >> "$HOTSPOT_REPORT" || true
    fi
    
    cat >>"$HOTSPOT_REPORT" <<MARKDOWN

## Frontend Analysis
MARKDOWN

    if [ -d "$ROOT_DIR/frontend/src" ]; then
        echo "### Large Component Files" >> "$HOTSPOT_REPORT"
        find "$ROOT_DIR/frontend/src" -name "*.jsx" -o -name "*.tsx" -type f 2>/dev/null | \
            xargs wc -l 2>/dev/null | \
            sort -rn | head -10 | \
            awk '{if (NF > 1) printf "- %s (%d lines)\n", $2, $1}' >> "$HOTSPOT_REPORT" || true
    fi
    
    cat >>"$HOTSPOT_REPORT" <<MARKDOWN

## Recommendations
1. Break down files >500 lines into smaller modules
2. Consider code-splitting for large React components
3. Use React.lazy() for conditional components
4. Profile runtime performance with browser DevTools
MARKDOWN
}

# ============================================================================
# BUNDLE ANALYSIS
# ============================================================================
analyze_bundle() {
    if [ "${RUN_PERF_BUILD:-0}" -ne 1 ]; then
        log_info "Skipping bundle build (set RUN_PERF_BUILD=1 to enable)"
        return 0
    fi
    
    if ! command -v npm >/dev/null 2>&1; then
        log_warning "npm not found, skipping bundle analysis"
        return 0
    fi
    
    if [ ! -d "$ROOT_DIR/frontend" ]; then
        log_warning "Frontend directory not found, skipping bundle analysis"
        return 0
    fi
    
    pushd "$ROOT_DIR/frontend" >/dev/null
    
    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        log_warning "package.json not found"
        popd >/dev/null
        return 0
    fi
    
    local start_time=$(date +%s)
    log_info "Building production bundle..."
    
    # Build with progress indicator
    if npm run build 2>&1 | grep -v "^$" | tail -n 5; then
        log_success "Build completed"
    else
        log_warning "Build had warnings"
    fi
    
    # Analyze bundle
    log_info "Analyzing bundle composition..."
    
    # Find build output directory
    local build_dir
    if [ -d "build" ]; then
        build_dir="build"
    elif [ -d "dist" ]; then
        build_dir="dist"
    elif [ -d ".next" ]; then
        build_dir=".next"
    else
        log_warning "Could not find build directory"
        popd >/dev/null
        return 0
    fi
    
    # Find JS files
    local js_files
    js_files=$(find "$build_dir" -name "*.js" -type f 2>/dev/null | head -5)
    
    if [ -z "$js_files" ]; then
        log_warning "No JS files found in build output"
        popd >/dev/null
        return 0
    fi
    
    # Try source-map-explorer if available
    if npx source-map-explorer --help >/dev/null 2>&1; then
        log_info "Running source-map-explorer..."
        # Use first few JS files to avoid timeout
        echo "$js_files" | head -3 | xargs npx source-map-explorer --json > "$BUNDLE_REPORT" 2>/dev/null || {
            log_warning "source-map-explorer failed, creating basic report"
            create_basic_bundle_report "$build_dir"
        }
    else
        log_info "source-map-explorer not available, creating basic report"
        create_basic_bundle_report "$build_dir"
    fi
    
    popd >/dev/null
    
    local duration=$(($(date +%s) - start_time))
    log_success "Bundle analysis completed in ${duration}s"
}

create_basic_bundle_report() {
    local build_dir=$1
    
    cat >"$BUNDLE_REPORT" <<JSON
{
  "timestamp": "$(timestamp)",
  "build_directory": "$build_dir",
  "files": [
JSON
    
    local first=true
    find "$build_dir" -name "*.js" -type f 2>/dev/null | while read -r file; do
        local size
        size=$(file_size "$file")
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$BUNDLE_REPORT"
        fi
        cat >>"$BUNDLE_REPORT" <<JSON
    {
      "path": "${file#$ROOT_DIR/}",
      "size": "$size"
    }
JSON
    done
    
    echo "  ]" >> "$BUNDLE_REPORT"
    echo "}" >> "$BUNDLE_REPORT"
}

# ============================================================================
# PERFORMANCE RECOMMENDATIONS
# ============================================================================
generate_recommendations() {
    local recommendations=()
    
    # Check hotspot report
    if [ -f "$HOTSPOT_REPORT" ]; then
        local large_files
        large_files=$(grep -c "lines)" "$HOTSPOT_REPORT" 2>/dev/null || echo 0)
        if [ "$large_files" -gt 5 ]; then
            recommendations+=("Consider refactoring $large_files large files")
        fi
    fi
    
    # Check bundle size
    if [ -f "$BUNDLE_REPORT" ]; then
        local total_size
        total_size=$(find "$ROOT_DIR/frontend/build" -name "*.js" -type f -exec cat {} \; 2>/dev/null | wc -c | tr -d ' ')
        if [ "$total_size" -gt 1048576 ]; then  # >1MB
            recommendations+=("Bundle size is large - consider code splitting")
        fi
    fi
    
    printf '%s\n' "${recommendations[@]}"
}

# ============================================================================
# REPORTING
# ============================================================================
append_bundle_note() {
    if [ ! -f "$BUNDLE_REPORT" ]; then
        cat >>"$HOTSPOT_REPORT" <<MARKDOWN

---

## Bundle Analysis
> Bundle analysis was skipped. Run with \`RUN_PERF_BUILD=1\` to generate bundle size report.

To enable:
\`\`\`bash
RUN_PERF_BUILD=1 ./ci_workflows/agent_perfsmith.sh
\`\`\`
MARKDOWN
    else
        local bundle_size
        bundle_size=$(file_size "$BUNDLE_REPORT")
        cat >>"$HOTSPOT_REPORT" <<MARKDOWN

---

## Bundle Analysis
✓ Bundle analysis complete - see \`perfsmith_bundle.json\` ($bundle_size)

### Quick Stats
MARKDOWN
        
        # Add basic stats if available
        if command -v jq >/dev/null 2>&1; then
            jq -r '.files[] | "- \(.path): \(.size)"' "$BUNDLE_REPORT" 2>/dev/null >> "$HOTSPOT_REPORT" || true
        fi
    fi
}

write_summary() {
    local recommendations=()
    while IFS= read -r line; do
        [ -n "$line" ] && recommendations+=("$line")
    done < <(generate_recommendations)
    
    cat >"$SUMMARY_REPORT" <<JSON
{
  "agent": "PerfSmith",
  "version": "2.0-macos",
  "generated_at": "$(timestamp)",
  "execution_time_seconds": $SECONDS,
  "artifacts": {
    "hotspots": "reports/$(basename "$HOTSPOT_REPORT")",
    "bundle": "reports/$(basename "$BUNDLE_REPORT")"
  },
  "recommendations": [
$(printf '    "%s"' "${recommendations[@]}" | paste -sd, -)
  ]
}
JSON
    
    # Console summary
    log_info "════════════════════════════════════════"
    log_info "Performance Analysis Summary:"
    if [ ${#recommendations[@]} -eq 0 ]; then
        log_success "No major performance concerns"
    else
        for rec in "${recommendations[@]}"; do
            log_info "  • $rec"
        done
    fi
    log_info "════════════════════════════════════════"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================
main() {
    local start_time=$(date +%s)
    
    log_info "Starting performance analysis"
    log_info "Platform: $(uname -s) $(uname -m)"
    
    # Run analyses in parallel where safe
    generate_hotspots &
    local hotspot_pid=$!
    
    analyze_bundle &
    local bundle_pid=$!
    
    # Wait for both
    wait $hotspot_pid $bundle_pid
    
    # Add bundle note to hotspot report
    append_bundle_note
    
    # Generate summary
    write_summary
    
    local duration=$(($(date +%s) - start_time))
    log_success "Completed in ${duration}s → reports in $REPORTS_DIR"
    
    return 0
}

# Cleanup
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "PerfSmith failed with exit code $exit_code"
    fi
    return $exit_code
}

trap cleanup EXIT

main "$@"
