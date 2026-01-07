#!/bin/bash
# Local macOS Agent Runner
# Executes all Happy Place agents locally for development/testing
# Usage: ./run_agents_locally.sh [--agent AGENT_NAME] [--parallel] [--skip-deps]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.11"
NODE_VERSION="18"
REPORTS_DIR="reports"
LOG_DIR="logs"

# Parse arguments
AGENT=""
PARALLEL=false
SKIP_DEPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            AGENT="$2"
            shift 2
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --agent AGENT_NAME   Run specific agent (lintguard, schemasage, perfsmith, shieldprobe, atlasreporter)"
            echo "  --parallel           Run compatible agents in parallel"
            echo "  --skip-deps          Skip dependency installation"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    fi
    return 0
}

# Pre-flight checks
preflight_checks() {
    log_info "Running pre-flight checks..."
    
    # Check if running on macOS
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_warning "This script is optimized for macOS but will attempt to run anyway"
    fi
    
    # Check required commands
    local missing_tools=()
    
    if ! check_command python3; then
        missing_tools+=("python3")
    fi
    
    if ! check_command node; then
        missing_tools+=("node")
    fi
    
    if ! check_command npm; then
        missing_tools+=("npm")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Install with: brew install python@${PYTHON_VERSION} node@${NODE_VERSION}"
        exit 1
    fi
    
    # Check Python version
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$python_version" != "$PYTHON_VERSION" ]]; then
        log_warning "Python version $python_version detected (expected $PYTHON_VERSION)"
    fi
    
    # Check Node version
    local node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [[ "$node_version" != "$NODE_VERSION" ]]; then
        log_warning "Node version $node_version detected (expected $NODE_VERSION)"
    fi
    
    log_success "Pre-flight checks passed"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    # Create directories
    mkdir -p "$REPORTS_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set environment variables (macOS optimizations)
    export HOMEBREW_NO_AUTO_UPDATE=1
    export HOMEBREW_NO_INSTALL_CLEANUP=1
    export SKIP_AGENT_BOOTSTRAP=0
    export RUN_PERF_BUILD=1
    
    log_success "Environment setup complete"
}

# Install dependencies
install_dependencies() {
    if [ "$SKIP_DEPS" = true ]; then
        log_warning "Skipping dependency installation (--skip-deps flag)"
        return
    fi
    
    log_info "Installing dependencies..."
    
    # Backend dependencies
    if [ -f "backend/requirements.txt" ]; then
        log_info "Installing Python dependencies..."
        pip3 install --quiet --prefer-binary -r backend/requirements.txt
        log_success "Python dependencies installed"
    fi
    
    # Frontend dependencies
    if [ -f "frontend/package.json" ]; then
        log_info "Installing Node dependencies..."
        cd frontend
        npm ci --prefer-offline --no-audit --loglevel=error
        cd ..
        log_success "Node dependencies installed"
    fi
}

# Run individual agent
run_agent() {
    local agent_name=$1
    local script_path="ci_workflows/agent_${agent_name}.sh"
    
    if [ ! -f "$script_path" ]; then
        log_error "Agent script not found: $script_path"
        return 1
    fi
    
    log_info "Running ${agent_name}..."
    
    # Make executable
    chmod +x "$script_path"
    
    # Run with logging
    local log_file="$LOG_DIR/${agent_name}_$(date +%Y%m%d_%H%M%S).log"
    
    if $script_path > "$log_file" 2>&1; then
        log_success "${agent_name} completed successfully"
        return 0
    else
        log_error "${agent_name} failed (see $log_file)"
        tail -n 20 "$log_file"
        return 1
    fi
}

# Run agents sequentially
run_sequential() {
    local agents=("lintguard" "schemasage" "perfsmith" "shieldprobe" "atlasreporter")
    local failed_agents=()
    
    log_info "Running agents sequentially..."
    
    for agent in "${agents[@]}"; do
        if ! run_agent "$agent"; then
            failed_agents+=("$agent")
        fi
    done
    
    # Summary
    echo ""
    log_info "===== Execution Summary ====="
    if [ ${#failed_agents[@]} -eq 0 ]; then
        log_success "All agents completed successfully!"
    else
        log_error "Failed agents: ${failed_agents[*]}"
        exit 1
    fi
}

# Run agents in parallel (where safe)
run_parallel() {
    log_info "Running agents in parallel..."
    
    # Phase 1: LintGuard (must run first)
    run_agent "lintguard" || exit 1
    
    # Phase 2: SchemaSage and PerfSmith in parallel
    log_info "Phase 2: Running SchemaSage and PerfSmith in parallel..."
    run_agent "schemasage" &
    local schemasage_pid=$!
    run_agent "perfsmith" &
    local perfsmith_pid=$!
    
    wait $schemasage_pid
    local schemasage_status=$?
    wait $perfsmith_pid
    local perfsmith_status=$?
    
    if [ $schemasage_status -ne 0 ] || [ $perfsmith_status -ne 0 ]; then
        log_error "Phase 2 failed"
        exit 1
    fi
    
    # Phase 3: ShieldProbe (depends on Phase 2)
    run_agent "shieldprobe" || exit 1
    
    # Phase 4: AtlasReporter (final step)
    run_agent "atlasreporter" || exit 1
    
    log_success "All agents completed successfully!"
}

# Generate report summary
generate_summary() {
    log_info "Generating summary report..."
    
    local summary_file="$REPORTS_DIR/local_run_summary_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$summary_file" << EOF
# Agent Execution Summary
**Executed**: $(date)
**Platform**: macOS (local)

## Results

EOF
    
    # Add agent results (use canonical outputs; glob checks break on macOS)
    if [ -f "$REPORTS_DIR/lintguard.json" ]; then
        echo "- ✅ lintguard: Success" >> "$summary_file"
    else
        echo "- ❌ lintguard: Not run or failed" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/db_audit.md" ]; then
        echo "- ✅ schemasage: Success" >> "$summary_file"
    else
        echo "- ❌ schemasage: Not run or failed" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/perfsmith_summary.json" ]; then
        echo "- ✅ perfsmith: Success" >> "$summary_file"
    else
        echo "- ❌ perfsmith: Not run or failed" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/security_findings.json" ]; then
        echo "- ✅ shieldprobe: Success" >> "$summary_file"
    else
        echo "- ❌ shieldprobe: Not run or failed" >> "$summary_file"
    fi

    if [ -f "$REPORTS_DIR/weekly_agent_digest.md" ]; then
        echo "- ✅ atlasreporter: Success" >> "$summary_file"
    else
        echo "- ❌ atlasreporter: Not run or failed" >> "$summary_file"
    fi
    
    cat >> "$summary_file" << EOF

## Logs
Available in: \`$LOG_DIR/\`

## Reports
Available in: \`$REPORTS_DIR/\`
EOF
    
    log_success "Summary saved to: $summary_file"
    cat "$summary_file"
}

# Main execution
main() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Happy Place Agents - Local Runner   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    preflight_checks
    setup_environment
    install_dependencies
    
    echo ""
    
    # Run specific agent or all
    if [ -n "$AGENT" ]; then
        log_info "Running single agent: $AGENT"
        run_agent "$AGENT"
    elif [ "$PARALLEL" = true ]; then
        run_parallel
    else
        run_sequential
    fi
    
    echo ""
    generate_summary
    
    log_success "Agent execution complete!"
}

# Trap errors
trap 'log_error "Script failed at line $LINENO"' ERR

# Run main
main
