#!/bin/bash

#═══════════════════════════════════════════════════════════════════════════════
# WINDSURF BLACK BOX - Installation Script
# 
# Installs and configures the Black Box system for Windsurf IDE integration.
#═══════════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${CYAN}→ $1${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLACKBOX_SOURCE="$SCRIPT_DIR"
CURRENT_DIR="$(pwd)"

print_header "🛩️ WINDSURF BLACK BOX INSTALLER"

# CRITICAL: Check if running from inside the package directory
if [ "$CURRENT_DIR" = "$SCRIPT_DIR" ] || [[ "$CURRENT_DIR" == *"/windsurf-blackbox"* ]]; then
    echo -e "${RED}❌ ERROR: You're running this from inside the windsurf-blackbox directory!${NC}"
    echo ""
    echo "This will cause recursive copying and bloated files."
    echo ""
    echo -e "${YELLOW}CORRECT USAGE:${NC}"
    echo "  cd /path/to/YourProject"
    echo "  ./windsurf-blackbox/install.sh"
    echo ""
    echo "Or from anywhere:"
    echo "  cd /path/to/YourProject"
    echo "  /path/to/windsurf-blackbox/install.sh"
    echo ""
    exit 1
fi

echo "This script will install the Black Box system in your project."
echo ""

# Check if we're in a project directory
if [ ! -d ".git" ] && [ ! -f "package.json" ] && [ ! -f "Cargo.toml" ] && [ ! -f "go.mod" ] && [ ! -f "requirements.txt" ]; then
    print_warning "This doesn't appear to be a project root directory."
    read -p "Continue anyway? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "Installation cancelled."
        exit 0
    fi
fi

TARGET_DIR="$CURRENT_DIR"
print_info "Installing to: $TARGET_DIR"
echo ""

# Create directory structure
print_step "Creating directory structure..."

mkdir -p "$TARGET_DIR/.windsurf-blackbox/sessions"
mkdir -p "$TARGET_DIR/.windsurf-blackbox/catalog"
mkdir -p "$TARGET_DIR/.windsurf-blackbox/archive"
mkdir -p "$TARGET_DIR/.windsurf-blackbox/templates"
mkdir -p "$TARGET_DIR/.windsurf-blackbox/scripts"
mkdir -p "$TARGET_DIR/.windsurf-blackbox/.temp"
mkdir -p "$TARGET_DIR/.windsurf/rules"
mkdir -p "$TARGET_DIR/.vscode"

print_success "Directory structure created"

# Copy core files
print_step "Copying Black Box files..."

# Copy script
cp "$BLACKBOX_SOURCE/scripts/blackbox.sh" "$TARGET_DIR/.windsurf-blackbox/scripts/"
chmod +x "$TARGET_DIR/.windsurf-blackbox/scripts/blackbox.sh"

# Copy templates
cp "$BLACKBOX_SOURCE/templates/"*.md "$TARGET_DIR/.windsurf-blackbox/templates/" 2>/dev/null || true

# Copy workflows
if [ -d "$BLACKBOX_SOURCE/workflows" ]; then
    mkdir -p "$TARGET_DIR/.windsurf-blackbox/workflows"
    cp "$BLACKBOX_SOURCE/workflows/"*.md "$TARGET_DIR/.windsurf-blackbox/workflows/" 2>/dev/null || true
fi

# Copy README
cp "$BLACKBOX_SOURCE/README.md" "$TARGET_DIR/.windsurf-blackbox/" 2>/dev/null || true

# Copy gitignore
cp "$BLACKBOX_SOURCE/.gitignore" "$TARGET_DIR/.windsurf-blackbox/" 2>/dev/null || true

print_success "Core files copied"

# Copy workflows directory
print_step "Setting up workflows directory..."

if [ -d "$BLACKBOX_SOURCE/workflows-directory" ]; then
    mkdir -p "$TARGET_DIR/workflows"
    cp -r "$BLACKBOX_SOURCE/workflows-directory/"* "$TARGET_DIR/workflows/" 2>/dev/null || true
    print_success "Workflows directory created"
fi

# Setup Windsurf integration
print_step "Setting up Windsurf integration..."

# Copy Windsurf rules
if [ -f "$BLACKBOX_SOURCE/.windsurfrules" ]; then
    if [ -f "$TARGET_DIR/.windsurfrules" ]; then
        # Check if file is suspiciously large (> 100KB is wrong)
        FILE_SIZE=$(stat -f%z "$TARGET_DIR/.windsurfrules" 2>/dev/null || stat -c%s "$TARGET_DIR/.windsurfrules" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -gt 100000 ]; then
            print_warning "Existing .windsurfrules is unusually large (${FILE_SIZE} bytes)"
            print_warning "This may indicate a previous installation error"
            rm "$TARGET_DIR/.windsurfrules"
            cp "$BLACKBOX_SOURCE/.windsurfrules" "$TARGET_DIR/"
            print_success "Replaced with fresh .windsurfrules"
        else
            print_warning "Existing .windsurfrules found"
            read -p "Overwrite? (y/N): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                cp "$BLACKBOX_SOURCE/.windsurfrules" "$TARGET_DIR/"
                print_success "Replaced .windsurfrules"
            else
                # Backup existing, then copy new
                cp "$TARGET_DIR/.windsurfrules" "$TARGET_DIR/.windsurfrules.backup"
                cp "$BLACKBOX_SOURCE/.windsurfrules" "$TARGET_DIR/"
                print_info "Backed up existing to .windsurfrules.backup"
                print_success "Created new .windsurfrules"
            fi
        fi
    else
        cp "$BLACKBOX_SOURCE/.windsurfrules" "$TARGET_DIR/"
        print_success "Created .windsurfrules"
    fi
fi

# Copy detailed rules
if [ -f "$BLACKBOX_SOURCE/.windsurf/rules/blackbox-rules.md" ]; then
    cp "$BLACKBOX_SOURCE/.windsurf/rules/blackbox-rules.md" "$TARGET_DIR/.windsurf/rules/"
    print_success "Copied Cascade rules"
fi

# Setup VS Code / Windsurf tasks
print_step "Setting up IDE tasks..."

if [ -f "$BLACKBOX_SOURCE/.vscode/tasks.json" ]; then
    if [ -f "$TARGET_DIR/.vscode/tasks.json" ]; then
        print_warning "Existing tasks.json found"
        read -p "Overwrite? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            cp "$BLACKBOX_SOURCE/.vscode/tasks.json" "$TARGET_DIR/.vscode/"
            print_success "Tasks.json updated"
        else
            cp "$BLACKBOX_SOURCE/.vscode/tasks.json" "$TARGET_DIR/.vscode/tasks.blackbox.json"
            print_info "Saved as tasks.blackbox.json (merge manually)"
        fi
    else
        cp "$BLACKBOX_SOURCE/.vscode/tasks.json" "$TARGET_DIR/.vscode/"
        print_success "Tasks.json created"
    fi
fi

# Copy snippets
if [ -f "$BLACKBOX_SOURCE/.vscode/blackbox.code-snippets" ]; then
    cp "$BLACKBOX_SOURCE/.vscode/blackbox.code-snippets" "$TARGET_DIR/.vscode/"
    print_success "Code snippets installed"
fi

# Copy keybindings reference
if [ -f "$BLACKBOX_SOURCE/.vscode/keybindings.json" ]; then
    cp "$BLACKBOX_SOURCE/.vscode/keybindings.json" "$TARGET_DIR/.vscode/keybindings.blackbox.json"
    print_info "Keybindings saved as keybindings.blackbox.json (add to user keybindings)"
fi

# Create convenience symlink
print_step "Creating convenience symlink..."

if [ ! -f "$TARGET_DIR/blackbox.sh" ]; then
    ln -sf ".windsurf-blackbox/scripts/blackbox.sh" "$TARGET_DIR/blackbox.sh"
    print_success "Created ./blackbox.sh symlink"
else
    print_warning "blackbox.sh already exists in project root"
fi

# Initialize Black Box
print_step "Initializing Black Box..."

cd "$TARGET_DIR"
./.windsurf-blackbox/scripts/blackbox.sh init

# Create initial catalog
print_step "Creating initial catalog..."

cat > "$TARGET_DIR/.windsurf-blackbox/catalog/index.md" << 'EOF'
# 📚 Windsurf Black Box - Session Catalog

> Auto-generated catalog of all development sessions

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Sessions | 0 |
| Active Sessions | 0 |
| Last Updated | Installation |

---

## 📅 Sessions

*No sessions recorded yet. Start your first session with:*

```bash
./blackbox.sh start "my-first-session"
```

---

*Catalog generated at installation*
*Windsurf Black Box v1.0*
EOF

print_success "Initial catalog created"

# Summary
print_header "✅ INSTALLATION COMPLETE"

echo "Black Box has been installed in your project!"
echo ""
echo "📁 Installed locations:"
echo "   .windsurf-blackbox/    ← Session documentation system"
echo "   workflows/             ← Tier 1 workflow templates"
echo ""
echo "🚀 Quick Start:"
echo "   ./blackbox.sh start \"my-task\"    # Start session"
echo "   ./blackbox.sh status              # Check status"
echo "   ./blackbox.sh end                 # End session"
echo ""
echo "📋 Workflows: workflows/tier-1/"
echo "   01-project-discovery.md   06-api-design.md"
echo "   02-git-workflow.md        07-cicd-pipeline.md"
echo "   03-code-review.md         08-uat-frontend.md"
echo "   04-security-audit.md      09-uat-fullstack.md"
echo "   05-incident-response.md   10-react-debugging.md"
echo ""
echo "⌨️  Keyboard Shortcuts (add to your keybindings):"
echo "   Ctrl+Shift+B S  → Start session"
echo "   Ctrl+Shift+B E  → End session"
echo "   Ctrl+Shift+B A  → Log action"
echo "   Ctrl+Shift+B D  → Log decision"
echo ""
echo "💡 Snippets available (type in editor):"
echo "   bb-start     → Session start prompt"
echo "   bb-end       → Session end prompt"
echo "   bb-action    → Log action entry"
echo "   bb-decision  → Log decision entry"
echo ""
echo "📖 Documentation:"
echo "   .windsurf-blackbox/README.md"
echo "   workflows/README.md"
echo "   workflows/quick-reference/workflow-cheatsheet.md"
echo ""
echo "Happy documenting! 🛩️"
