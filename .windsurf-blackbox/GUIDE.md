# Windsurf Black Box - Complete User Guide

> **Session Documentation System for AI-Assisted Development**

---

## Table of Contents

1. [What is Black Box?](#what-is-black-box)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [CLI Reference](#cli-reference)
6. [IDE Integration](#ide-integration)
7. [Cascade AI Integration](#cascade-ai-integration)
8. [Workflow Integration](#workflow-integration)
9. [Session Management](#session-management)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## What is Black Box?

Black Box is a **session documentation system** designed specifically for AI-assisted development workflows. It solves a critical problem: **AI assistants have no memory between sessions**.

### The Problem

When working with AI coding assistants like Cascade, every new conversation starts fresh. The AI doesn't remember:
- What you were working on yesterday
- Decisions you made and why
- Issues you encountered and how you solved them
- The current state of your project

This leads to:
- Repeating context every session
- Lost institutional knowledge
- Inconsistent decisions
- Difficulty continuing complex tasks

### The Solution

Black Box creates a **flight recorder** for your development sessions:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BLACK BOX SYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SESSION RECORDS                                                │
│  ├── Actions taken                                              │
│  ├── Decisions made (with rationale)                            │
│  ├── Issues encountered (with resolutions)                      │
│  ├── Checkpoints and milestones                                 │
│  └── Continuation prompts for next session                      │
│                                                                 │
│  CATALOG SYSTEM                                                 │
│  ├── Searchable index of all sessions                           │
│  ├── Cross-referenced decisions                                 │
│  └── Project knowledge base                                     │
│                                                                 │
│  WORKFLOW INTEGRATION                                           │
│  ├── 10 Tier 1 core workflows                                   │
│  ├── 9 Tier 2 extended workflows                                │
│  └── AI persona integration                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Bash shell (macOS, Linux, or WSL on Windows)
- A project directory with version control (recommended)

### Step 1: Download and Extract

```bash
# Download windsurf-blackbox.zip to your project
cd ~/Projects/MyProject
unzip windsurf-blackbox.zip
```

### Step 2: Run the Installer

> ⚠️ **CRITICAL**: Run the installer FROM your project root, not from inside windsurf-blackbox!

```bash
# ✅ CORRECT - Run from project root
cd ~/Projects/MyProject
./windsurf-blackbox/install.sh

# ❌ WRONG - Do NOT run from inside the package
cd ~/Projects/MyProject/windsurf-blackbox
./install.sh   # This will fail with an error
```

### Step 3: Verify Installation

```bash
# Check that files were created
ls -la .windsurf-blackbox/
ls -la .windsurfrules
ls -la workflows/

# Test the CLI
./blackbox.sh status
```

### Post-Installation Structure

```
MyProject/
├── .windsurf-blackbox/          ← Black Box system (hidden)
│   ├── scripts/blackbox.sh      ← Main CLI script
│   ├── sessions/                ← Session records stored here
│   ├── catalog/                 ← Searchable index
│   ├── templates/               ← Document templates
│   └── archive/                 ← Completed sessions
├── workflows/                   ← Your workflow library
│   ├── tier-1/                  ← 10 core workflows
│   ├── tier-2/                  ← 9 extended workflows
│   └── quick-reference/         ← Cheat sheets
├── .windsurf/rules/             ← Cascade AI rules
├── .vscode/                     ← IDE integration
│   ├── tasks.json               ← 19 automated tasks
│   ├── keybindings.json         ← Keyboard shortcuts
│   └── blackbox.code-snippets   ← Code snippets
├── .windsurfrules               ← Cascade integration
└── blackbox.sh                  ← Convenience symlink
```

---

## Quick Start

### Your First Session

```bash
# 1. Start a new session
./blackbox.sh start "implement-user-authentication"

# 2. Work with Cascade AI on your task...

# 3. Log important events as you work
./blackbox.sh action "Created User model with email/password fields"
./blackbox.sh decision "Use bcrypt for password hashing" "Industry standard, battle-tested"
./blackbox.sh issue "TypeScript error on User.create()" "Fixed by adding type assertion"

# 4. Create checkpoints before risky operations
./blackbox.sh checkpoint "Before refactoring auth middleware"

# 5. Mark major accomplishments
./blackbox.sh milestone "User registration working end-to-end"

# 6. End the session with a summary
./blackbox.sh end "Completed user registration, login pending"
```

### Continuing Work Tomorrow

```bash
# 1. Check what sessions exist
./blackbox.sh list

# 2. View your last session
./blackbox.sh show CONV-2024-12-17-001

# 3. Get the continuation prompt
./blackbox.sh continue CONV-2024-12-17-001

# 4. Paste the prompt into Cascade to restore context!

# 5. Start a new session for today's work
./blackbox.sh start "implement-user-login"
```

---

## Core Concepts

### Sessions

A **session** represents one focused work period. Each session:
- Has a unique ID (e.g., `CONV-2024-12-17-001`)
- Documents what happened during that work period
- Generates a continuation prompt for future sessions

### Entries

Sessions contain **entries** of different types:

| Entry Type | Purpose | Example |
|------------|---------|---------|
| **Action** | What you did | "Created database migration" |
| **Decision** | Choices made + rationale | "Use PostgreSQL because we need ACID" |
| **Issue** | Problems + resolutions | "Fixed CORS error by adding headers" |
| **Checkpoint** | Save points | "Before major refactor" |
| **Milestone** | Achievements | "MVP feature complete" |
| **Note** | General observations | "Need to revisit error handling" |

### The Catalog

The **catalog** is a searchable index of all sessions:
- Find sessions by topic, date, or content
- Cross-reference decisions across sessions
- Build project knowledge base over time

### Continuation Prompts

When you end a session, Black Box generates a **continuation prompt** containing:
- Session summary
- Current state
- Pending items
- Context needed to continue

Paste this into Cascade to restore full context!

---

## CLI Reference

### Session Commands

```bash
# Start a new session
./blackbox.sh start "description"
./blackbox.sh start "implement-payment-flow"

# End the current session
./blackbox.sh end "summary"
./blackbox.sh end "Completed Stripe integration, needs testing"

# View session status
./blackbox.sh status

# List all sessions
./blackbox.sh list
./blackbox.sh list 10        # Show last 10 sessions

# Show session details
./blackbox.sh show SESSION_ID
./blackbox.sh show CONV-2024-12-17-001

# Open session in editor
./blackbox.sh open SESSION_ID

# Generate continuation prompt
./blackbox.sh continue SESSION_ID
```

### Logging Commands

```bash
# Log an action (what you did)
./blackbox.sh action "description"
./blackbox.sh action "Created User model" "success"
./blackbox.sh action "Attempted migration" "failed"

# Log a decision (with rationale)
./blackbox.sh decision "what you decided" "why"
./blackbox.sh decision "Use JWT for auth" "Stateless, scalable"

# Log an issue (with status)
./blackbox.sh issue "description" "status"
./blackbox.sh issue "Memory leak in worker" "investigating"
./blackbox.sh issue "CORS error" "resolved"

# Create a checkpoint (save point)
./blackbox.sh checkpoint "description"
./blackbox.sh checkpoint "Before database migration"

# Mark a milestone (achievement)
./blackbox.sh milestone "description"
./blackbox.sh milestone "User authentication complete"

# Add a general note
./blackbox.sh note "description"
./blackbox.sh note "Consider adding rate limiting later"
```

### Search Commands

```bash
# Search sessions
./blackbox.sh search "query"
./blackbox.sh search "authentication"
./blackbox.sh search "PostgreSQL decision"

# View catalog
./blackbox.sh catalog
```

### Utility Commands

```bash
# Get help
./blackbox.sh help
./blackbox.sh help start
./blackbox.sh help decision

# Archive old sessions
./blackbox.sh archive SESSION_ID

# Export session to markdown
./blackbox.sh export SESSION_ID
```

---

## IDE Integration

### VS Code / Windsurf Tasks

Access via **Terminal → Run Task** or `Ctrl+Shift+P` → "Tasks: Run Task"

| Task | Description |
|------|-------------|
| Black Box: Start Session | Start new session with prompt |
| Black Box: End Session | End current session |
| Black Box: Show Status | View current session status |
| Black Box: Log Action | Log an action |
| Black Box: Log Decision | Log a decision |
| Black Box: Log Issue | Log an issue |
| Black Box: Create Checkpoint | Create a checkpoint |
| Black Box: Mark Milestone | Mark a milestone |
| Black Box: Search Sessions | Search the catalog |
| Black Box: List Sessions | List recent sessions |
| Black Box: Open Catalog | Open catalog in editor |
| Black Box: Open Current Session | Open current session file |
| Black Box: Quick Start - Feature | Start feature session |
| Black Box: Quick Start - Debug | Start debug session |
| Black Box: Quick Start - Review | Start review session |

### Keyboard Shortcuts

All shortcuts use the `Ctrl+Shift+B` prefix:

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+B, S` | Start Session |
| `Ctrl+Shift+B, E` | End Session |
| `Ctrl+Shift+B, A` | Log Action |
| `Ctrl+Shift+B, D` | Log Decision |
| `Ctrl+Shift+B, I` | Log Issue |
| `Ctrl+Shift+B, C` | Create Checkpoint |
| `Ctrl+Shift+B, M` | Mark Milestone |
| `Ctrl+Shift+B, T` | Show Status |
| `Ctrl+Shift+B, O` | Open Current Session |
| `Ctrl+Shift+B, L` | Open Catalog |

### Code Snippets

Type these prefixes and press Tab:

| Prefix | Output |
|--------|--------|
| `bb-start` | Session start prompt |
| `bb-end` | Session end prompt |
| `bb-action` | Action log entry |
| `bb-decision` | Decision log entry |
| `bb-issue` | Issue log entry |
| `bb-checkpoint` | Checkpoint entry |
| `bb-milestone` | Milestone entry |
| `bb-continue` | Continuation prompt |
| `bb-dec-record` | Full decision record template |
| `bb-iss-record` | Full issue record template |
| `bb-log` | Quick inline log comment |
| `bb-todo` | TODO with session reference |
| `bb-fixme` | FIXME with session reference |

---

## Cascade AI Integration

### Automatic Session Awareness

With the included `.windsurfrules`, Cascade will:

1. **Check for active sessions** at conversation start
2. **Suggest starting a session** if none is active
3. **Proactively offer to log** decisions and issues
4. **Generate session summaries** when ending

### Natural Language Commands

Just tell Cascade what you want:

```
"Start a session for user authentication"
→ Cascade runs: ./blackbox.sh start "user-authentication"

"Log that we decided to use JWT because it's stateless"
→ Cascade runs: ./blackbox.sh decision "Use JWT" "Stateless architecture"

"Create a checkpoint before we refactor"
→ Cascade runs: ./blackbox.sh checkpoint "Before refactoring"

"End the session, we completed the login flow"
→ Cascade runs: ./blackbox.sh end "Completed login flow"
```

### Cascade Will Proactively Suggest

- **After implementing something:** "Should I log this action?"
- **After making a choice:** "Would you like me to log this decision?"
- **After fixing a bug:** "Should I log this issue and resolution?"
- **Before risky changes:** "Consider creating a checkpoint first?"
- **Long sessions:** "Session active 2+ hours. Create a checkpoint?"

### Using Continuation Prompts

When starting a new Cascade conversation:

1. Run `./blackbox.sh continue SESSION_ID`
2. Copy the generated prompt
3. Paste it as your first message to Cascade
4. Cascade now has full context of previous work!

---

## Workflow Integration

### Available Workflows

Black Box includes 19 comprehensive workflows:

#### Tier 1 - Core Development (10 workflows)

| # | Workflow | Use For |
|---|----------|---------|
| 01 | Project Discovery | Starting new projects, creating SSOT |
| 02 | Git Workflow | Branch management, commits, PRs |
| 03 | Code Review | P0-P3 severity reviews |
| 04 | Security Audit | OWASP-based security checks |
| 05 | Incident Response | Production issue handling |
| 06 | API Design | REST/GraphQL API creation |
| 07 | CI/CD Pipeline | Build and deploy automation |
| 08 | UAT Frontend | Frontend testing |
| 09 | UAT Full-Stack | Integration testing |
| 10 | React Debugging | React-specific debugging |

#### Tier 2 - Extended (9 workflows)

| # | Workflow | Use For |
|---|----------|---------|
| 12 | Database Migration | Schema changes, data migrations |
| 13 | Performance Optimization | Profiling, optimization |
| 14 | Documentation Generation | API docs, architecture docs |
| 15 | Technical Debt | Debt identification and remediation |
| 16 | Feature Flags | Progressive rollouts |
| 17 | A/B Testing | Experiment design and analysis |
| 18 | Monitoring & Alerting | Observability setup |
| 19 | Disaster Recovery | Backup and recovery |
| 20 | Compliance & Auditing | SOC2, GDPR compliance |

### Starting a Workflow

Each workflow has a Cascade prompt template:

```bash
# View the workflow
cat workflows/tier-1/03-code-review.md

# Tell Cascade to use it
"Execute Code Review workflow for the authentication module"
```

### Workflow + Black Box

Workflows integrate with Black Box automatically:

```bash
# Start a workflow session
./blackbox.sh start "review-auth-module"

# Cascade will reference the session in all actions
# All decisions and issues are logged to the session

# End with workflow-specific summary
./blackbox.sh end "Code review complete: 2 P1, 5 P2 findings"
```

---

## Session Management

### Session Lifecycle

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  START   │────▶│  ACTIVE  │────▶│   END    │────▶│ ARCHIVED │
│          │     │          │     │          │     │          │
│ Creates  │     │ Logging  │     │ Summary  │     │ Stored   │
│ session  │     │ entries  │     │ generated│     │ forever  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

### Viewing Session History

```bash
# List recent sessions
./blackbox.sh list

# Output:
# Recent Sessions:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONV-2024-12-17-003  implement-payment-flow    Active
# CONV-2024-12-17-002  fix-auth-bug              Completed
# CONV-2024-12-17-001  setup-database            Completed
```

### Session File Structure

Each session creates a markdown file:

```markdown
# Session: CONV-2024-12-17-001

## Metadata
- **Started:** 2024-12-17 09:00:00
- **Topic:** implement-user-authentication
- **Status:** Active

## Timeline

### 09:00 - Session Started
Topic: implement-user-authentication

### 09:15 - Action
Created User model with email and password fields
Status: success

### 09:30 - Decision
**Decision:** Use bcrypt for password hashing
**Rationale:** Industry standard, well-tested, includes salt

### 10:00 - Issue
**Issue:** TypeScript error on User.create()
**Status:** resolved
**Resolution:** Added type assertion for Prisma client

### 10:30 - Milestone
User registration working end-to-end

## Session Summary
[Generated when session ends]

## Continuation Prompt
[Generated for next session]
```

### Searching Sessions

```bash
# Search by keyword
./blackbox.sh search "authentication"

# Search by decision
./blackbox.sh search "PostgreSQL"

# Search by date (in session ID)
./blackbox.sh search "2024-12-17"
```

---

## Best Practices

### 1. Start Every Work Session

```bash
# Always start a session before working
./blackbox.sh start "descriptive-topic-name"
```

### 2. Log Decisions with Rationale

Bad:
```bash
./blackbox.sh decision "Use Redis"
```

Good:
```bash
./blackbox.sh decision "Use Redis for session storage" "Need sub-ms latency, data is ephemeral, team has Redis experience"
```

### 3. Create Checkpoints Before Risk

```bash
# Before migrations
./blackbox.sh checkpoint "Before database migration"

# Before major refactors
./blackbox.sh checkpoint "Before auth system refactor"

# Before deleting code
./blackbox.sh checkpoint "Before removing legacy endpoints"
```

### 4. Log Issues Even When Resolved

```bash
# This helps future sessions!
./blackbox.sh issue "CORS error on /api/users" "resolved"
./blackbox.sh note "Fixed by adding origin to allowed list in cors config"
```

### 5. Use Meaningful Session Names

Bad:
```bash
./blackbox.sh start "work"
./blackbox.sh start "bug fix"
```

Good:
```bash
./blackbox.sh start "implement-stripe-checkout"
./blackbox.sh start "fix-memory-leak-in-worker"
./blackbox.sh start "review-pr-123-auth-changes"
```

### 6. End Sessions with Summaries

```bash
# Include what was done and what's pending
./blackbox.sh end "Completed Stripe checkout integration. Pending: webhook handling, error states, and tests"
```

### 7. Use Continuation Prompts

```bash
# At the end of a session
./blackbox.sh continue CONV-2024-12-17-001 > /tmp/prompt.md

# Tomorrow, paste into Cascade to restore context
```

### 8. Review the Catalog Periodically

```bash
# See what decisions have been made
./blackbox.sh catalog

# Search for patterns
./blackbox.sh search "decided"
```

---

## Troubleshooting

### "Command not found: blackbox.sh"

```bash
# Use the full path
./.windsurf-blackbox/scripts/blackbox.sh status

# Or recreate the symlink
ln -sf .windsurf-blackbox/scripts/blackbox.sh ./blackbox.sh
```

### "No active session"

```bash
# Start a session first
./blackbox.sh start "my-task"

# Then log entries
./blackbox.sh action "Did something"
```

### Session File is Empty

```bash
# Check the session directory
ls -la .windsurf-blackbox/sessions/

# View the actual file
cat .windsurf-blackbox/sessions/CONV-*.md
```

### Large/Bloated Files

If any file is unexpectedly large (>100KB):

```bash
# Check file sizes
ls -lh .windsurfrules
ls -lh .windsurf-blackbox/

# If bloated, delete and reinstall
rm .windsurfrules
rm -rf .windsurf-blackbox
./windsurf-blackbox/install.sh
```

### Cascade Doesn't Recognize Commands

Ensure `.windsurfrules` exists and contains Black Box rules:

```bash
# Check the file
cat .windsurfrules | head -20

# Should see "Black Box" mentioned
```

### IDE Tasks Not Appearing

1. Reload VS Code/Windsurf window
2. Check `.vscode/tasks.json` exists
3. Run "Tasks: Run Task" from command palette

### Permission Denied

```bash
# Make script executable
chmod +x .windsurf-blackbox/scripts/blackbox.sh
chmod +x blackbox.sh
```

---

## Getting Help

```bash
# General help
./blackbox.sh help

# Command-specific help
./blackbox.sh help start
./blackbox.sh help decision
./blackbox.sh help search
```

---

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════╗
║              WINDSURF BLACK BOX - QUICK REFERENCE             ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  SESSION LIFECYCLE                                            ║
║  ./blackbox.sh start "topic"     Start new session            ║
║  ./blackbox.sh end "summary"     End current session          ║
║  ./blackbox.sh status            View current status          ║
║                                                               ║
║  LOGGING                                                      ║
║  ./blackbox.sh action "what"     Log an action                ║
║  ./blackbox.sh decision "x" "y"  Log decision + rationale     ║
║  ./blackbox.sh issue "x" "stat"  Log issue + status           ║
║  ./blackbox.sh checkpoint "x"    Create save point            ║
║  ./blackbox.sh milestone "x"     Mark achievement             ║
║  ./blackbox.sh note "x"          Add general note             ║
║                                                               ║
║  NAVIGATION                                                   ║
║  ./blackbox.sh list              List all sessions            ║
║  ./blackbox.sh show ID           View session details         ║
║  ./blackbox.sh search "query"    Search sessions              ║
║  ./blackbox.sh continue ID       Get continuation prompt      ║
║                                                               ║
║  KEYBOARD (Ctrl+Shift+B, then...)                             ║
║  S=Start  E=End  A=Action  D=Decision  I=Issue                ║
║  C=Checkpoint  M=Milestone  T=Status  O=Open  L=Catalog       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

*Windsurf Black Box v1.0*
*Session Documentation for AI-Assisted Development*
