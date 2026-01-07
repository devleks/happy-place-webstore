#!/bin/bash

# ============================================================================
# Claude Code Session Continuity System - Installation Script
# ============================================================================
# This script sets up the session continuity system in your project
# Usage: ./install.sh [target-directory]
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# Configuration
# ============================================================================

TARGET_DIR="${1:-.}"  # Use first argument or current directory
CLAUDE_DIR="$TARGET_DIR/.claude"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                       ║${NC}"
    echo -e "${CYAN}║  Claude Code Session Continuity System - Installer   ║${NC}"
    echo -e "${CYAN}║                                                       ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
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

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

# ============================================================================
# Main Installation
# ============================================================================

print_header

# Verify target directory
if [ ! -d "$TARGET_DIR" ]; then
    print_error "Target directory does not exist: $TARGET_DIR"
    exit 1
fi

print_info "Installing to: $TARGET_DIR"
echo ""

# ============================================================================
# Step 1: Create directory structure
# ============================================================================

print_step "Step 1: Creating .claude directory"

if [ -d "$CLAUDE_DIR" ]; then
    print_warning ".claude directory already exists"
    echo -e "Do you want to proceed? Existing files may be overwritten. (y/N): \c"
    read -r PROCEED
    if [ "$PROCEED" != "y" ] && [ "$PROCEED" != "Y" ]; then
        print_info "Installation cancelled"
        exit 0
    fi
else
    mkdir -p "$CLAUDE_DIR"
    print_success "Created .claude directory"
fi

# Create subdirectories
mkdir -p "$CLAUDE_DIR/backups"
mkdir -p "$CLAUDE_DIR/temp"
mkdir -p "$CLAUDE_DIR/archive"

print_success "Created subdirectories"
echo ""

# ============================================================================
# Step 2: Copy template files
# ============================================================================

print_step "Step 2: Installing template files"

# Copy all files from source .claude to target .claude
FILES_COPIED=0

# Core files
for file in PROJECT_STATE.md SESSION_PROMPT.md START_HERE.md README.md gitignore-additions.txt; do
    if [ -f "$SOURCE_DIR/$file" ]; then
        cp "$SOURCE_DIR/$file" "$CLAUDE_DIR/"
        print_success "Installed $file"
        FILES_COPIED=$((FILES_COPIED + 1))
    fi
done

# Scripts
for script in close-session.sh open-session.sh; do
    if [ -f "$SOURCE_DIR/$script" ]; then
        cp "$SOURCE_DIR/$script" "$CLAUDE_DIR/"
        chmod +x "$CLAUDE_DIR/$script"
        print_success "Installed $script (made executable)"
        FILES_COPIED=$((FILES_COPIED + 1))
    fi
done

echo ""
print_success "Installed $FILES_COPIED files"
echo ""

# ============================================================================
# Step 3: Configure .gitignore
# ============================================================================

print_step "Step 3: Configuring .gitignore"

GITIGNORE_FILE="$TARGET_DIR/.gitignore"

if [ ! -f "$GITIGNORE_FILE" ]; then
    touch "$GITIGNORE_FILE"
    print_info "Created .gitignore file"
fi

# Check if already configured
if grep -q ".claude/session.log" "$GITIGNORE_FILE" 2>/dev/null; then
    print_info ".gitignore already configured for .claude"
else
    echo "" >> "$GITIGNORE_FILE"
    echo "# Claude Code Session Continuity System" >> "$GITIGNORE_FILE"
    echo ".claude/session.log" >> "$GITIGNORE_FILE"
    echo ".claude/temp/" >> "$GITIGNORE_FILE"
    echo ".claude/*.tmp" >> "$GITIGNORE_FILE"
    echo ".claude/backups/*.md" >> "$GITIGNORE_FILE"
    echo ".claude/.DS_Store" >> "$GITIGNORE_FILE"
    print_success "Updated .gitignore"
fi

echo ""

# ============================================================================
# Step 4: Initialize state file
# ============================================================================

print_step "Step 4: Initialize project state"

# Try to detect project information
PROJECT_NAME=$(basename "$TARGET_DIR")
CURRENT_BRANCH=$(cd "$TARGET_DIR" && git branch --show-current 2>/dev/null || echo "main")
LAST_COMMIT=$(cd "$TARGET_DIR" && git log -1 --oneline 2>/dev/null || echo "No commits yet")

# Update PROJECT_STATE.md with detected info
STATE_FILE="$CLAUDE_DIR/PROJECT_STATE.md"
TEMP_STATE=$(mktemp)

sed "s/\[Your project name\]/$PROJECT_NAME/g" "$STATE_FILE" > "$TEMP_STATE"
sed -i.bak "s/\[current-branch-name\]/$CURRENT_BRANCH/g" "$TEMP_STATE"
sed -i.bak "s/\[hash\] - \[message\]/$LAST_COMMIT/g" "$TEMP_STATE"
sed -i.bak "s/\[Auto-updated by close-session.sh\]/$(date '+%Y-%m-%d %H:%M:%S')/g" "$TEMP_STATE"

mv "$TEMP_STATE" "$STATE_FILE"
rm -f "$TEMP_STATE.bak"

print_success "Initialized PROJECT_STATE.md with project info"
echo ""

# ============================================================================
# Step 5: Create initial session log
# ============================================================================

print_step "Step 5: Creating session log"

SESSION_LOG="$CLAUDE_DIR/session.log"
if [ ! -f "$SESSION_LOG" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Session continuity system installed" > "$SESSION_LOG"
    print_success "Created session.log"
else
    print_info "session.log already exists"
fi

echo ""

# ============================================================================
# Installation Complete
# ============================================================================

print_header

echo -e "${GREEN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                       ║${NC}"
echo -e "${GREEN}║             Installation Complete! 🎉                 ║${NC}"
echo -e "${GREEN}║                                                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Next Steps
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Next Steps:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "1. ${YELLOW}Read the documentation:${NC}"
echo "   cat $CLAUDE_DIR/START_HERE.md"
echo ""

echo "2. ${YELLOW}Customize your project state:${NC}"
echo "   Edit: $CLAUDE_DIR/PROJECT_STATE.md"
echo "   Fill in:"
echo "   - Current objective"
echo "   - What you've completed"
echo "   - What's in progress"
echo "   - What's next"
echo ""

echo "3. ${YELLOW}Start your first session:${NC}"
echo "   cd $TARGET_DIR"
echo "   ./.claude/open-session.sh"
echo ""

echo "4. ${YELLOW}Test the workflow:${NC}"
echo "   In Claude Code, paste:"
echo "   ${GREEN}Session init: read .claude/PROJECT_STATE.md and continue${NC}"
echo ""

# ============================================================================
# Quick Start Commands
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Quick Start Commands:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$TARGET_DIR" != "." ]; then
    echo "cd $TARGET_DIR"
fi

echo ""
echo "# Open session (start working)"
echo "./.claude/open-session.sh"
echo ""
echo "# Edit state (customize for your project)"
echo "nano .claude/PROJECT_STATE.md"
echo ""
echo "# Close session (save progress)"
echo "./.claude/close-session.sh"
echo ""

# ============================================================================
# File Locations
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Installed Files:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

tree "$CLAUDE_DIR" 2>/dev/null || find "$CLAUDE_DIR" -type f -o -type d | sed 's|[^/]*/| |g'

echo ""

# ============================================================================
# Additional Tips
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Tips:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "• ${GREEN}Commit PROJECT_STATE.md${NC} to share context across machines"
echo "• ${GREEN}Update state regularly${NC} during long sessions (every 30-45 min)"
echo "• ${GREEN}Run close-session.sh${NC} before hitting rate limits"
echo "• ${GREEN}Document decisions${NC} to prevent repeating failed approaches"
echo ""

# ============================================================================
# Success Message
# ============================================================================

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Installation successful! Ready to eliminate context loss.${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

print_info "For full documentation, see: $CLAUDE_DIR/README.md"
echo ""
