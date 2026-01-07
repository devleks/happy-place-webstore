#!/bin/bash

# ============================================================================
# Claude Code Session Closure Script
# ============================================================================
# Run this before closing Claude Code to save session state
# Usage: ./claude/close-session.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Configuration
# ============================================================================

STATE_FILE=".claude/PROJECT_STATE.md"
SESSION_LOG=".claude/session.log"
BACKUP_DIR=".claude/backups"

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}=================================${NC}"
    echo -e "${BLUE}  Claude Code Session Closure${NC}"
    echo -e "${BLUE}=================================${NC}"
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

# ============================================================================
# Main Script
# ============================================================================

print_header

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Backup current state file
if [ -f "$STATE_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/PROJECT_STATE_$(date +%Y%m%d_%H%M%S).md"
    cp "$STATE_FILE" "$BACKUP_FILE"
    print_success "Backed up state to: $BACKUP_FILE"
fi

# Get current git information
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "not-a-git-repo")
LAST_COMMIT=$(git log -1 --oneline 2>/dev/null || echo "no commits yet")
GIT_STATUS=$(git status --short 2>/dev/null || echo "")

# Count modified files
if [ -n "$GIT_STATUS" ]; then
    MODIFIED_COUNT=$(echo "$GIT_STATUS" | wc -l | tr -d ' ')
else
    MODIFIED_COUNT=0
fi

# Update the state file header
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

print_info "Updating project state..."

# Append session closure information
{
    echo ""
    echo "---"
    echo ""
    echo "### Session Closed: $TIMESTAMP"
    echo ""
    echo "**Git State at Closure:**"
    echo "- Branch: \`$CURRENT_BRANCH\`"
    echo "- Last Commit: \`$LAST_COMMIT\`"
    echo "- Modified Files: $MODIFIED_COUNT"
    echo ""
    if [ $MODIFIED_COUNT -gt 0 ]; then
        echo "**Uncommitted Changes:**"
        echo '```'
        echo "$GIT_STATUS"
        echo '```'
        echo ""
    fi
} >> "$STATE_FILE"

print_success "Updated $STATE_FILE"

# Log session closure
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session closed | Branch: $CURRENT_BRANCH | Modified: $MODIFIED_COUNT files" >> "$SESSION_LOG"

# Display summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Session Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Branch:          $CURRENT_BRANCH"
echo "Last Commit:     $LAST_COMMIT"
echo "Modified Files:  $MODIFIED_COUNT"
echo "State File:      $STATE_FILE"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Prompt for git commit (optional)
if [ $MODIFIED_COUNT -gt 0 ]; then
    print_warning "You have uncommitted changes."
    echo -e "Do you want to commit the state file? (y/N): \c"
    read -r COMMIT_CHOICE
    
    if [ "$COMMIT_CHOICE" = "y" ] || [ "$COMMIT_CHOICE" = "Y" ]; then
        git add "$STATE_FILE"
        git commit -m "chore: update session state [skip ci]"
        print_success "Committed state file"
    fi
fi

# Prompt for manual state update
echo ""
print_info "IMPORTANT: Before closing, update these in $STATE_FILE:"
echo "   1. Current Objective (if changed)"
echo "   2. What Was Just Completed"
echo "   3. What's In Progress"
echo "   4. What's Next (prioritized)"
echo "   5. Any Critical Context or Decisions"
echo ""
echo -e "Have you updated the state file? (y/N): \c"
read -r UPDATE_CHOICE

if [ "$UPDATE_CHOICE" != "y" ] && [ "$UPDATE_CHOICE" != "Y" ]; then
    print_warning "Please update $STATE_FILE before closing!"
    echo "   Run: nano $STATE_FILE"
    echo "   Or open it in your editor"
    exit 1
fi

# Final confirmation
echo ""
print_success "Session state saved successfully!"
print_info "Next session start with: 'Read .claude/PROJECT_STATE.md and continue'"
echo ""
print_header

# Optional: Display quick stats
echo -e "${BLUE}Session Statistics:${NC}"
TOTAL_SESSIONS=$(grep -c "Session Closed:" "$STATE_FILE" 2>/dev/null || echo "1")
echo "Total sessions logged: $TOTAL_SESSIONS"

# Keep only last 10 backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l | tr -d ' ')
if [ "$BACKUP_COUNT" -gt 10 ]; then
    print_info "Cleaning old backups (keeping last 10)..."
    cd "$BACKUP_DIR"
    ls -t | tail -n +11 | xargs rm -f
    cd - > /dev/null
fi

echo ""
print_success "Safe to close Claude Code now! 👋"
echo ""
