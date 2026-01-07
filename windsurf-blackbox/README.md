# 🛩️ Windsurf Black Box

> **Your Flight Data Recorder for AI-Assisted Development**

Just like an airplane's black box captures everything to reconstruct what happened, the Windsurf Black Box captures every decision, action, discussion, and outcome from your development sessions - ensuring perfect continuity no matter how long between sessions.

---

## 📋 Table of Contents

- [Why Black Box?](#-why-black-box)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Directory Structure](#-directory-structure)
- [Usage Guide](#-usage-guide)
- [Integration](#-integration)
- [Workflows](#-workflows)
- [Templates](#-templates)
- [FAQ](#-faq)

---

## 🎯 Why Black Box?

| Problem | Black Box Solution |
|---------|-------------------|
| "Why did we decide that?" | Decision log with rationale |
| "What did we try?" | Complete action history |
| "Where did we leave off?" | Continuation prompts |
| "What happened in that session?" | Full session records |
| "How do I continue this project?" | Searchable catalog |
| "New dev needs context" | Project timeline & history |

---

## 🚀 Quick Start

### Option A: Full Installation (Recommended)

```bash
# From the windsurf-blackbox directory
./install.sh
```

This installs:
- Black Box scripts and templates
- Windsurf/VS Code tasks
- Cascade rules
- Code snippets
- Keyboard shortcuts

### Option B: Manual Setup

```bash
# Copy blackbox.sh to your project
cp blackbox.sh /your/project/

# Initialize Black Box
./blackbox.sh init
```

### 2. Start a Session

```bash
./blackbox.sh start "feature-user-auth"
```

Copy the generated prompt to Cascade.

### 3. Log During Session

```bash
# Log actions
./blackbox.sh action "Implemented JWT login" "success"

# Log decisions
./blackbox.sh decision "Use bcrypt for hashing" "Industry standard, GPU-resistant"

# Log issues
./blackbox.sh issue "Token refresh failing" "investigating"

# Create checkpoints
./blackbox.sh checkpoint "Before refactoring auth"

# Mark milestones
./blackbox.sh milestone "Authentication complete"
```

### 4. End Session

```bash
./blackbox.sh end
```

Copy the closing prompt to Cascade for summary generation.

---

## ✨ Features

### Session Management
- **Unique Session IDs**: `CONV-YYYY-MM-DD-NNN-topic`
- **Start/End Protocols**: Structured prompts for Cascade
- **Real-time Logging**: Actions, decisions, issues, checkpoints
- **Continuation Prompts**: Resume exactly where you left off

### Searchable Catalog
- **Master Index**: All sessions at a glance
- **Timeline View**: Chronological narrative
- **Decision Registry**: All decisions across sessions
- **Issue Tracker**: All issues and resolutions
- **Tag-based Search**: Find by technology, activity, component

### Integration
- **Tier 1 Workflows**: Connects with all development workflows
- **Git Integration**: Session IDs in commits
- **SSOT Connection**: Links to Single Source of Truth
- **IDE Tasks**: VS Code/Windsurf task integration

---

## 📁 Directory Structure

```
.windsurf-blackbox/
├── sessions/                 # Individual session records
│   ├── CONV-2024-12-17-001-auth-setup.md
│   └── CONV-2024-12-17-002-api-design.md
├── catalog/                  # Searchable indexes
│   ├── index.md             # Master index
│   ├── decisions.md         # All decisions
│   ├── issues.md            # All issues
│   ├── timeline.md          # Chronological view
│   ├── by-date/             # Date-based indexes
│   ├── by-topic/            # Topic clusters
│   └── by-status/           # Status groupings
├── archive/                  # Completed project archives
├── templates/                # Document templates
│   ├── session.md
│   ├── continuation-prompt.md
│   └── decision.md
├── .temp/                    # Working files (gitignored)
├── .gitignore
└── README.md
```

---

## 📖 Usage Guide

### Command Reference

```
./blackbox.sh <command> [arguments]

SESSION MANAGEMENT:
  init                    Initialize Black Box
  start <topic>           Start new session
  end [notes]             End current session
  status                  Show current status

LOGGING:
  action <desc> [result]  Log an action
  decision <desc> <why>   Log a decision
  issue <desc> [status]   Log an issue
  checkpoint <desc>       Create checkpoint
  milestone <desc>        Mark milestone
  note <text>             Add note

CATALOG:
  catalog                 Rebuild catalog
  search <query>          Search sessions
  list [n]                List recent (default: 10)
```

### Cascade Prompts

**Start Session:**
```
═══════════════════════════════════════════════════════════════
🎬 SESSION START
Session ID: CONV-[ID]
Project: [Name]
Branch: [branch]
Today's Objectives: [list]
Please acknowledge and track under this session ID.
═══════════════════════════════════════════════════════════════
```

**During Session:**
```
[CONV-ID] Log action: Implemented user validation
[CONV-ID] Log decision: Use Zod for validation because type-safe
[CONV-ID] Log issue: Form not validating on blur
[CONV-ID] Create checkpoint: Before adding OAuth
```

**End Session:**
```
═══════════════════════════════════════════════════════════════
🎬 SESSION END: CONV-[ID]
Generate: Summary, State, Action Items, Continuation Prompt
═══════════════════════════════════════════════════════════════
```

---

## 🌊 Windsurf IDE Integration

### Tasks (Command Palette)

Press `Cmd/Ctrl+Shift+P` → "Tasks: Run Task" → Select:

| Task | Description |
|------|-------------|
| 🎬 BB: Start Session | Start new session with topic |
| 🏁 BB: End Session | End current session |
| ⚡ BB: Log Action | Log an action |
| 🎯 BB: Log Decision | Log a decision with rationale |
| 🐛 BB: Log Issue | Log an issue |
| 📍 BB: Create Checkpoint | Create state checkpoint |
| 🏆 BB: Mark Milestone | Mark achievement |
| 📊 BB: Show Status | Show current status |
| 🔍 BB: Search Sessions | Search past sessions |
| 📖 BB: Open Catalog | Open session catalog |

### Keyboard Shortcuts

Add these to your keybindings (Cmd/Ctrl+K Cmd/Ctrl+S):

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+B S` | Start Session |
| `Ctrl+Shift+B E` | End Session |
| `Ctrl+Shift+B A` | Log Action |
| `Ctrl+Shift+B D` | Log Decision |
| `Ctrl+Shift+B I` | Log Issue |
| `Ctrl+Shift+B C` | Create Checkpoint |
| `Ctrl+Shift+B M` | Mark Milestone |
| `Ctrl+Shift+B T` | Show Status |
| `Ctrl+Shift+B O` | Open Current Session |
| `Ctrl+Shift+B L` | Open Catalog |

### Code Snippets

Type these prefixes in any file:

| Prefix | Inserts |
|--------|---------|
| `bb-start` | Session start prompt |
| `bb-end` | Session end prompt |
| `bb-action` | Action log entry |
| `bb-decision` | Decision log entry |
| `bb-issue` | Issue log entry |
| `bb-checkpoint` | Checkpoint entry |
| `bb-milestone` | Milestone marker |
| `bb-continue` | Continuation prompt |
| `bb-log` | Quick inline log |
| `bb-todo` | TODO with session ref |

### Cascade Integration

The `.windsurfrules` file teaches Cascade to:

1. **Recognize session commands**: "start session", "end session", etc.
2. **Auto-suggest logging**: After decisions, issues, milestones
3. **Generate summaries**: Proper format at session end
4. **Track context**: Reference session ID in work

Natural language commands:
- "start session user-auth"
- "log decision: use JWT because stateless"
- "checkpoint before refactor"
- "end session"

---

### With Git

```bash
# Include session ID in commits
git commit -m "feat(auth): implement JWT [CONV-2024-12-17-001]"

# Tag releases with session reference
git tag -a v1.0.0 -m "Release [Sessions: CONV-001 through CONV-015]"
```

### With VS Code/Windsurf

```json
// .vscode/tasks.json
{
  "tasks": [
    {
      "label": "BB: Start Session",
      "type": "shell",
      "command": "./blackbox.sh start \"${input:topic}\""
    },
    {
      "label": "BB: End Session",
      "type": "shell", 
      "command": "./blackbox.sh end"
    }
  ]
}
```

### With Other Workflows

The Black Box integrates with all Tier 1 workflows:

| Workflow | Integration |
|----------|-------------|
| Project Discovery | Initial session, SSOT creation |
| Git SOP | Branch/merge decisions |
| Code Review | Review sessions, findings |
| Security Audit | Vulnerability tracking |
| Incident Response | Incident timeline |
| API Design | Design decisions |
| CI/CD Pipeline | Deployment tracking |
| UAT | Test sessions |

---

## 📄 Workflows

### Core Workflows Included

1. **Session Management** (`workflows/01-session-management.md`)
   - Complete session lifecycle
   - ID protocol
   - Logging formats
   - Continuation system

2. **Catalog System** (`workflows/02-catalog-system.md`)
   - Index generation
   - Search capabilities
   - Cross-referencing
   - Timeline views

3. **Tier 1 Integration** (`workflows/03-tier1-integration.md`)
   - Connection to all workflows
   - Automation hooks
   - Directory structure
   - Quick reference

---

## 📝 Templates

### Available Templates

| Template | Purpose |
|----------|---------|
| `session.md` | Full session record structure |
| `continuation-prompt.md` | Resume prompts for any gap |
| `decision.md` | Detailed decision documentation |

---

## ❓ FAQ

**Q: How do I find a past session?**
```bash
./blackbox.sh search "authentication"
# Or check: .windsurf-blackbox/catalog/index.md
```

**Q: How do I continue after a long break?**
1. Find your last session: `./blackbox.sh list`
2. Open its continuation prompt section
3. Paste to Cascade
4. Start new session referencing the old one

**Q: Can I use this without the CLI?**
Yes! The templates work standalone. Create session files manually following the template structure.

**Q: How do I share with my team?**
The `.windsurf-blackbox/` directory is git-friendly. Commit it (except `.temp/`) and team members can search the catalog.

**Q: What's the session ID format?**
```
CONV-YYYY-MM-DD-NNN-topic-name
│    │         │   └── Optional topic (kebab-case)
│    │         └────── Daily sequence (001, 002, etc.)
│    └──────────────── Date
└────────────────────── Fixed prefix
```

---

## 🛠️ Maintenance

### Rebuild Catalog
```bash
./blackbox.sh catalog
```

### Archive Old Sessions
```bash
# Move completed project sessions to archive
mv .windsurf-blackbox/sessions/CONV-2024-* .windsurf-blackbox/archive/project-v1/
```

### Backup
```bash
# The entire directory is plain markdown - back up with your project
git add .windsurf-blackbox/
git commit -m "chore: update black box sessions"
```

---

## 📊 Status

```
┌─────────────────────────────────────────────────────────────┐
│              WINDSURF BLACK BOX v1.0                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🟢 ALWAYS RECORDING:                                       │
│     ✓ Every decision + WHY                                  │
│     ✓ Every action + OUTCOME                                │
│     ✓ Every problem + SOLUTION                              │
│     ✓ Every discussion + CONCLUSION                         │
│     ✓ Project state at any moment                           │
│                                                             │
│  🎯 ENABLES:                                                │
│     • Perfect reconstruction after ANY gap                  │
│     • Onboard new devs with full context                    │
│     • Understand "why" not just "what"                      │
│     • Never lose tribal knowledge                           │
│     • Continue exactly where you left off                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📜 License

MIT - Use freely in your projects.

---

## 🙏 Acknowledgments

Inspired by the need to maintain perfect continuity in AI-assisted development workflows, ensuring that no context is ever lost between sessions.

---

*Windsurf Black Box v1.0*
*Your future self will thank you.*
