#!/bin/bash

# ============================================================================
# Claude Code Session Opening Script
# ============================================================================
# Run this when starting a new Claude Code session
# Usage: ./claude/open-session.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Configuration
# ============================================================================

STATE_FILE=".claude/PROJECT_STATE.md"
SESSION_LOG=".claude/session.log"

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${CYAN}=================================${NC}"
    echo -e "${CYAN}  Claude Code Session Start${NC}"
    echo -e "${CYAN}=================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_section() {
    echo -e "${MAGENTA}▶ $1${NC}"
}

# ============================================================================
# Main Script
# ============================================================================

print_header

# Check if state file exists
if [ ! -f "$STATE_FILE" ]; then
    print_error "Project state file not found: $STATE_FILE"
    echo "   Run this first: cp .claude/PROJECT_STATE.md.template $STATE_FILE"
    exit 1
fi

# Log session start
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session opened" >> "$SESSION_LOG"

print_success "Session started: $TIMESTAMP"
echo ""

# ============================================================================
# Git Status Check
# ============================================================================

print_section "Git Status"

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "not-a-git-repo")
LAST_COMMIT=$(git log -1 --oneline 2>/dev/null || echo "no commits yet")
GIT_STATUS=$(git status --short 2>/dev/null || echo "")

echo "Branch:      ${GREEN}$CURRENT_BRANCH${NC}"
echo "Last Commit: $LAST_COMMIT"

if [ -n "$GIT_STATUS" ]; then
    MODIFIED_COUNT=$(echo "$GIT_STATUS" | wc -l | tr -d ' ')
    print_warning "Uncommitted changes: $MODIFIED_COUNT files"
    echo ""
    echo "$GIT_STATUS" | head -10
    if [ $MODIFIED_COUNT -gt 10 ]; then
        echo "... and $(($MODIFIED_COUNT - 10)) more files"
    fi
else
    print_success "Working directory clean"
fi

echo ""

# ============================================================================
# Project State Summary
# ============================================================================

print_section "Project State Summary"
echo ""

# Extract key sections from state file
echo -e "${CYAN}Current Objective:${NC}"
sed -n '/## 🎯 Current Objective/,/^---$/p' "$STATE_FILE" | grep -v "^#" | grep -v "^---" | grep -v "^<!--" | sed 's/^/  /'
echo ""

echo -e "${CYAN}What's In Progress:${NC}"
sed -n '/### 🔄 What.*In Progress/,/^### /p' "$STATE_FILE" | grep -v "^#" | grep "^\- \[" | head -5
echo ""

echo -e "${CYAN}What's Next:${NC}"
sed -n '/### ⏭️ What.*Next/,/^---$/p' "$STATE_FILE" | grep -v "^#" | grep -v "^---" | grep "^[0-9]" | head -5
echo ""

echo -e "${CYAN}Known Issues/Blockers:${NC}"
BLOCKERS=$(sed -n '/### 🚧 Known Issues/,/^### /p' "$STATE_FILE" | grep "^\- \*\*Issue" | wc -l | tr -d ' ')
if [ "$BLOCKERS" -gt 0 ]; then
    sed -n '/### 🚧 Known Issues/,/^### /p' "$STATE_FILE" | grep "^\- \*\*Issue" | head -3
    if [ "$BLOCKERS" -gt 3 ]; then
        echo "  ... and $(($BLOCKERS - 3)) more blockers"
    fi
else
    echo "  None recorded"
fi
echo ""

# ============================================================================
# Recent Activity
# ============================================================================

print_section "Recent Activity"
echo ""

# Show last 5 commits
echo -e "${CYAN}Last 5 Commits:${NC}"
git log -5 --oneline --decorate --color=always 2>/dev/null || echo "  No git history"
echo ""

# Show last session info from state file
echo -e "${CYAN}Last Session:${NC}"
LAST_SESSION=$(grep -A 5 "Session Closed:" "$STATE_FILE" | tail -6 | head -6)
if [ -n "$LAST_SESSION" ]; then
    echo "$LAST_SESSION" | sed 's/^/  /'
else
    echo "  No previous session recorded"
fi
echo ""

# ============================================================================
# Quick Reference Commands
# ============================================================================

print_section "Quick Reference"
echo ""

echo -e "${CYAN}Common Commands:${NC}"
sed -n '/### Running the Project/,/^### /p' "$STATE_FILE" | grep -v "^#" | sed 's/^/  /'
echo ""

# ============================================================================
# Pre-Flight Checklist
# ============================================================================

print_section "Pre-Flight Checklist"
echo ""

# Check dependencies
if [ -f "package.json" ]; then
    if [ -d "node_modules" ]; then
        print_success "Node modules installed"
    else
        print_warning "Node modules not found - run: npm install"
    fi
fi

if [ -f "requirements.txt" ]; then
    print_info "Python project detected - verify venv is activated"
fi

if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    print_warning "Missing .env file - copy from .env.example"
fi

echo ""

# ============================================================================
# Claude Code Initialization Prompt
# ============================================================================

print_section "Claude Code Initialization"
echo ""

echo -e "${YELLOW}Copy this message to start Claude Code:${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
cat << 'EOF'
Session initialization:
1. Read .claude/PROJECT_STATE.md
2. Review current git status
3. Verify understanding of:
   - Current objective
   - What's in progress
   - Next immediate steps

Confirm you're ready to continue from where we left off.
Keep your response brief - just confirm context loaded.
EOF
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# ============================================================================
# Session Tips
# ============================================================================

print_section "Session Tips"
echo ""

echo "• Update state regularly during long sessions"
echo "• Run ./claude/close-session.sh before rate limits hit"
echo "• Keep objective and next steps current"
echo "• Document decisions and rationale as you go"
echo ""

# ============================================================================
# Final Status
# ============================================================================

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
print_success "Ready to start Claude Code session!"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Optional: Auto-open state file in editor
if command -v code &> /dev/null; then
    echo -e "Open state file in VS Code? (y/N): \c"
    read -r OPEN_CHOICE
    if [ "$OPEN_CHOICE" = "y" ] || [ "$OPEN_CHOICE" = "Y" ]; then
        code "$STATE_FILE"
    fi
fi
