# Windsurf Black Box - Tier 1 Workflow Integration

Official integration of the Session Documentation System (Black Box) into the development workflow collection.

---

## Workflow Collection Status

| # | Workflow | Status | Integration |
|---|----------|--------|-------------|
| 1 | Universal Project Discovery + SSOT | ✅ | ↔️ Black Box |
| 2 | Git Workflow SOP | ✅ | ↔️ Black Box |
| 3 | React Debugging | ✅ | ↔️ Black Box |
| 4 | Automated UAT (Frontend) | ✅ | ↔️ Black Box |
| 5 | Full-Stack UAT | ✅ | ↔️ Black Box |
| 6 | Code Review | ✅ | ↔️ Black Box |
| 7 | Security Audit | ✅ | ↔️ Black Box |
| 8 | Incident Response | ✅ | ↔️ Black Box |
| 9 | API Design | ✅ | ↔️ Black Box |
| 10 | CI/CD Pipeline | ✅ | ↔️ Black Box |
| 11 | **Session Documentation (Black Box)** | ✅ | **CORE** |

---

## Integration Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                     COMPLETE WORKFLOW ECOSYSTEM                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                    ┌─────────────────────────┐                             │
│                    │   PROJECT DISCOVERY     │                             │
│                    │   + SSOT GENERATION     │                             │
│                    └───────────┬─────────────┘                             │
│                                │                                           │
│                    ┌───────────▼─────────────┐                             │
│                    │      BLACK BOX          │◀══════════════════════╗     │
│                    │   Session Management    │                       ║     │
│                    │  • Start/End Sessions   │                       ║     │
│                    │  • Track Decisions      │                       ║     │
│                    │  • Log Actions/Issues   │                       ║     │
│                    │  • Generate Catalog     │                       ║     │
│                    └───────────┬─────────────┘                       ║     │
│                                │                                     ║     │
│         ┌──────────────────────┼──────────────────────┐              ║     │
│         │                      │                      │              ║     │
│         ▼                      ▼                      ▼              ║     │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐        ║     │
│  │   DEVELOP   │       │   REVIEW    │       │   DEPLOY    │        ║     │
│  ├─────────────┤       ├─────────────┤       ├─────────────┤        ║     │
│  │ API Design  │       │ Code Review │       │ CI/CD       │        ║     │
│  │ Git SOP     │       │ Security    │       │ UAT         │        ║     │
│  │ Debugging   │       │ Audit       │       │             │        ║     │
│  └──────┬──────┘       └──────┬──────┘       └──────┬──────┘        ║     │
│         │                     │                     │               ║     │
│         └─────────────────────┴─────────────────────┘               ║     │
│                               │                                     ║     │
│                    ┌──────────▼──────────┐                          ║     │
│                    │  INCIDENT RESPONSE  │══════════════════════════╝     │
│                    └─────────────────────┘                                │
│                                                                            │
│  ════════════════════════════════════════════════════════════════════     │
│       ALL WORKFLOWS FEED INTO BLACK BOX FOR CONTINUITY                    │
│  ════════════════════════════════════════════════════════════════════     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Integration Points by Workflow

### 1. Project Discovery + SSOT

**How Black Box Integrates:**
- Discovery sessions create initial Black Box entries
- SSOT document references session IDs for change history
- Architecture decisions logged with rationale

**Integration Commands:**
```bash
# Start discovery session
./blackbox.sh start "project-discovery"

# Log SSOT creation
./blackbox.sh decision "SSOT structure defined" "Standard template for [tech stack]"

# Reference in SSOT
# In SSOT.md, add: "Created in session CONV-YYYY-MM-DD-NNN"
```

### 2. Git Workflow SOP

**How Black Box Integrates:**
- Each significant git operation logged
- Branch decisions recorded with rationale
- Merge/rebase outcomes documented

**Git Integration:**
```bash
# In commit messages, reference session:
git commit -m "feat(auth): implement JWT login [CONV-2024-12-17-001]"

# Log major git operations
./blackbox.sh action "Created feature branch" "feature/auth from main"
./blackbox.sh decision "Rebase strategy" "Keep linear history for this feature"
```

### 3. React Debugging Workflow

**How Black Box Integrates:**
- Debugging sessions capture issue investigation
- Root cause analysis documented
- Solutions and anti-patterns recorded

**Debug Session Pattern:**
```bash
./blackbox.sh start "debug-rendering-issue"
./blackbox.sh issue "Component not re-rendering" "investigating"
./blackbox.sh action "Added React DevTools profiling" "found unnecessary re-renders"
./blackbox.sh decision "Use useMemo for expensive computation" "Reduced re-renders by 80%"
./blackbox.sh end "Resolved - was missing dependency in useEffect"
```

### 4-5. UAT Workflows (Frontend & Full-Stack)

**How Black Box Integrates:**
- Test sessions documented
- Test failures logged with context
- UAT decisions and sign-offs recorded

**UAT Session Pattern:**
```bash
./blackbox.sh start "uat-sprint-23"
./blackbox.sh action "Ran E2E test suite" "42 passed, 3 failed"
./blackbox.sh issue "Checkout flow failing on mobile" "viewport issue"
./blackbox.sh milestone "UAT sign-off received"
./blackbox.sh end "Sprint 23 UAT complete"
```

### 6. Code Review Workflow

**How Black Box Integrates:**
- Review sessions tracked
- Review decisions documented
- P0-P3 issues logged

**Review Session Pattern:**
```bash
./blackbox.sh start "review-pr-145"
./blackbox.sh issue "P1: SQL injection vulnerability" "found in user input handler"
./blackbox.sh decision "Block merge until security fix" "P0 security issue"
./blackbox.sh action "Requested changes" "3 P1, 5 P2 issues"
./blackbox.sh end "Review complete - changes requested"
```

### 7. Security Audit Workflow

**How Black Box Integrates:**
- Audit sessions create comprehensive security records
- Vulnerability findings documented
- Remediation tracked

**Security Audit Pattern:**
```bash
./blackbox.sh start "security-audit-q4"
./blackbox.sh issue "OWASP A01: Broken Access Control" "admin endpoints exposed"
./blackbox.sh decision "Implement RBAC" "Use Casbin for policy management"
./blackbox.sh milestone "Critical vulnerabilities patched"
./blackbox.sh end "Audit complete - 3 critical, 7 high remediated"
```

### 8. Incident Response Workflow

**How Black Box Integrates:**
- Incidents automatically create session entries
- Timeline reconstruction from Black Box history
- Post-mortem references session decisions

**Incident Pattern:**
```bash
./blackbox.sh start "incident-2024-12-17-prod-outage"
./blackbox.sh issue "Production database connection exhausted" "critical"
./blackbox.sh action "Increased connection pool to 100" "temporary mitigation"
./blackbox.sh decision "Implement connection pooling library" "PgBouncer"
./blackbox.sh checkpoint "Service restored"
./blackbox.sh end "Incident resolved - RCA scheduled"
```

### 9. API Design Workflow

**How Black Box Integrates:**
- API design decisions documented
- Breaking changes logged
- Version decisions recorded

**API Design Pattern:**
```bash
./blackbox.sh start "api-v2-design"
./blackbox.sh decision "Use REST over GraphQL" "Simpler caching, team expertise"
./blackbox.sh decision "Pagination: cursor-based" "Better for large datasets"
./blackbox.sh action "Generated OpenAPI spec" "45 endpoints documented"
./blackbox.sh end "API v2 spec complete"
```

### 10. CI/CD Pipeline Workflow

**How Black Box Integrates:**
- Pipeline changes documented
- Deployment decisions logged
- Rollback events captured

**CI/CD Pattern:**
```bash
./blackbox.sh start "cicd-optimization"
./blackbox.sh decision "Parallel test execution" "Reduce pipeline from 15m to 5m"
./blackbox.sh action "Added build caching" "50% faster builds"
./blackbox.sh milestone "Sub-5-minute pipeline achieved"
./blackbox.sh end "Pipeline optimization complete"
```

---

## Cross-Workflow Session Templates

### Feature Development Session

```
./blackbox.sh start "feature-[name]"

Session covers:
1. Design discussion (API Design workflow)
2. Implementation (Git workflow)
3. Testing (UAT workflow)
4. Review (Code Review workflow)
5. Deployment (CI/CD workflow)

All in one continuous documented session.
```

### Bug Fix Session

```
./blackbox.sh start "bugfix-[issue-id]"

Session covers:
1. Investigation (Debugging workflow)
2. Root cause analysis
3. Fix implementation (Git workflow)
4. Verification (UAT workflow)
5. Deployment (CI/CD workflow)
```

### Maintenance Session

```
./blackbox.sh start "maintenance-[type]"

Session covers:
1. Security updates (Security Audit workflow)
2. Dependency updates
3. Performance optimization
4. Technical debt reduction
```

---

## Workflow Trigger Integration

### Auto-Start Patterns

Configure triggers in your IDE/terminal:

```bash
# .bashrc / .zshrc additions

# Auto-start session on branch creation
git_checkout_hook() {
    if [[ "$1" == "-b" ]]; then
        ./blackbox.sh start "branch-$2"
    fi
}
alias gco='git_checkout_hook'

# Start session for debugging
alias debug='./blackbox.sh start "debug-$(date +%H%M)" && '

# Start session for code review
review() {
    ./blackbox.sh start "review-$1"
    gh pr view "$1"
}
```

### VS Code / Windsurf Tasks

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Start Dev Session",
      "type": "shell",
      "command": "./blackbox.sh start \"${input:sessionTopic}\"",
      "problemMatcher": []
    },
    {
      "label": "End Dev Session", 
      "type": "shell",
      "command": "./blackbox.sh end",
      "problemMatcher": []
    },
    {
      "label": "Log Decision",
      "type": "shell",
      "command": "./blackbox.sh decision \"${input:decision}\" \"${input:rationale}\"",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "sessionTopic",
      "type": "promptString",
      "description": "Session topic (kebab-case)"
    },
    {
      "id": "decision",
      "type": "promptString", 
      "description": "What was decided?"
    },
    {
      "id": "rationale",
      "type": "promptString",
      "description": "Why?"
    }
  ]
}
```

---

## Cascade Integration Commands

Add to your workflow prompts:

```markdown
## Session Context (Add to any workflow)

Current session: [CONV-ID]
Track all decisions, actions, and issues under this session ID.
At significant points, use format:

ACTION @CONV-ID: [description]
DECISION @CONV-ID: [what] because [why]
ISSUE @CONV-ID: [problem] - [status]
MILESTONE @CONV-ID: [achievement]
```

---

## Complete Directory Structure

```
project/
├── .windsurf-blackbox/           ← Black Box root
│   ├── sessions/                  ← Session records
│   │   ├── CONV-2024-12-17-001-auth-refactor.md
│   │   └── CONV-2024-12-17-002-api-design.md
│   ├── catalog/                   ← Searchable indexes
│   │   ├── index.md
│   │   ├── decisions.md
│   │   ├── issues.md
│   │   └── timeline.md
│   ├── archive/                   ← Completed project archives
│   ├── templates/                 ← Document templates
│   │   ├── session.md
│   │   ├── decision.md
│   │   └── incident.md
│   ├── .temp/                     ← Working files (gitignored)
│   ├── .gitignore
│   └── README.md
├── .promptx/                      ← AI Agent Personas
│   └── personas/
│       ├── developer.md
│       ├── reviewer.md
│       ├── rebaser.md
│       ├── merger.md
│       └── multiplan-manager.md
├── workflows/                     ← Workflow definitions
│   ├── 01-project-discovery.md
│   ├── 02-git-sop.md
│   ├── 03-code-review.md
│   ├── 04-security-audit.md
│   ├── 05-incident-response.md
│   ├── 06-api-design.md
│   ├── 07-cicd-pipeline.md
│   ├── 08-uat-frontend.md
│   ├── 09-uat-fullstack.md
│   ├── 10-react-debugging.md
│   └── 11-session-documentation.md
├── scripts/
│   └── blackbox.sh               ← Black Box CLI
└── SSOT.md                        ← Single Source of Truth
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TIER 1 WORKFLOW + BLACK BOX                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  EVERY SESSION PATTERN:                                                 │
│  ──────────────────────                                                 │
│  1. ./blackbox.sh start "[workflow]-[topic]"                            │
│  2. Execute workflow                                                    │
│  3. Log decisions/actions/issues                                        │
│  4. ./blackbox.sh end                                                   │
│                                                                         │
│  WORKFLOW PREFIXES:                                                     │
│  ─────────────────                                                      │
│  discovery-    → Project Discovery                                      │
│  feature-      → Feature Development                                    │
│  debug-        → Debugging                                              │
│  review-       → Code Review                                            │
│  security-     → Security Audit                                         │
│  incident-     → Incident Response                                      │
│  api-          → API Design                                             │
│  cicd-         → CI/CD Pipeline                                         │
│  uat-          → User Acceptance Testing                                │
│  maintenance-  → Maintenance/Updates                                    │
│                                                                         │
│  LOGGING DURING WORKFLOW:                                               │
│  ────────────────────────                                               │
│  ./blackbox.sh action "Did X" "result"                                  │
│  ./blackbox.sh decision "Chose Y" "because Z"                           │
│  ./blackbox.sh issue "Problem W" "status"                               │
│  ./blackbox.sh milestone "Achieved V"                                   │
│  ./blackbox.sh checkpoint "Before risky change"                         │
│                                                                         │
│  CONTINUITY:                                                            │
│  ──────────                                                             │
│  • All workflows feed into Black Box                                    │
│  • Session IDs in commit messages                                       │
│  • SSOT references session history                                      │
│  • Catalog enables full project reconstruction                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Windsurf Black Box - Tier 1 Integration v1.0*
