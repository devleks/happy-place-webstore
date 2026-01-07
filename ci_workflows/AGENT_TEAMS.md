# CI Agent Teams & Workflow Assignments

This document defines the team structure, workflow assignments, and collaboration protocols for Happy Place Webstore's CI agent ecosystem.

---

## Leadership Structure

The agent ecosystem is led by **three Team Leaders** defined in `.promptx/personas/`:
 

| Team Leader | Persona File | Responsibility |
|-------------|--------------|----------------|
| **Initializer Agent** | `agent-initializer.md` | Defines goals, establishes artifacts/state, sets checks |
 **Execution Agent** | `agent-execution.md` | Implements changes, produces change records |
| **Review/Validation Agent** | `agent-review-validation.md` | Runs checks, approves/rejects, commits or rolls back |

**Handoff Protocol:** `.promptx/personas/AGENT_HANDOFF_PROTOCOL.md`

---

## Team Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              CI AGENT ECOSYSTEM                                          │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│                           ┌─────────────────────────────┐                                │
│                           │      TEAM LEADERS           │                                │
│                           │  (PromptX Personas)         │                                │
│                           └─────────────────────────────┘                                │
│                                        │                                                 │
│         ┌──────────────────────────────┼──────────────────────────────┐                  │
│         ▼                              ▼                              ▼                  │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐            │
│  │   INITIALIZER   │         │   EXECUTION     │         │ REVIEW/VALIDATE │            │
│  │     AGENT       │         │     AGENT       │         │     AGENT       │            │
│  │  (Goal/State)   │         │  (Implement)    │         │  (Check/Commit) │            │
│  └────────┬────────┘         └────────┬────────┘         └────────┬────────┘            │
│           │                           │                           │                      │
│           │ Coordinates               │ Coordinates               │ Coordinates          │
│           ▼                           ▼                           ▼                      │
│  ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐            │
│  │  SchemaSage     │         │   LintGuard     │         │   ShieldProbe   │            │
│  │  AtlasReporter  │         │   PerfSmith     │         │   LintGuard     │            │
│  └─────────────────┘         └─────────────────┘         └─────────────────┘            │
│                                                                                          │
│  ══════════════════════════════════════════════════════════════════════════════════════ │
│       AGENTS COLLABORATE VIA SHARED REPORTS + HANDOFF PROTOCOL                          │
│  ══════════════════════════════════════════════════════════════════════════════════════ │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Team Leader → Co-Worker Assignments

| Team Leader | CI Agent Co-Workers | Why |
|-------------|---------------------|-----|
| **Initializer Agent** | SchemaSage, AtlasReporter | Establishes DB state, aggregates baseline reports |
| **Execution Agent** | LintGuard, PerfSmith | Ensures code quality during implementation |
| **Review/Validation Agent** | ShieldProbe, LintGuard | Validates security, runs quality checks before commit |

---

## Agent Profiles & Assigned Workflows

### 1. LintGuard (Code Quality Specialist)

**Script:** `ci_workflows/agent_lintguard.sh`

**Purpose:** Static code analysis for backend (Python) and frontend (React)

**Tools:**
- Ruff (Python linting)
- Bandit (Python security linting)
- ESLint (JavaScript/React linting)

**Primary Workflows:**

| Workflow | File | Role |
|----------|------|------|
| Code Review | `workflows/tier-1/03-code-review.md` | Primary executor for automated quality checks |
| Technical Debt | `workflows/tier-2/15-technical-debt-management.md` | Identify code smells and debt indicators |

**Outputs:**

- `reports/lintguard_ruff.json`
- `reports/lintguard_bandit.json`
- `reports/lintguard_eslint.json`
- `reports/lintguard.json` (summary)

**Collaboration Rights:**
- Can request **ShieldProbe** for security-specific findings
- Can escalate to **AtlasReporter** for digest inclusion
- Should notify **PerfSmith** if complexity metrics suggest performance concerns

---

### 2. PerfSmith (Performance Analyst)

**Script:** `ci_workflows/agent_perfsmith.sh`

**Purpose:** Code optimization insights for backend + frontend

**Tools:**
- Custom hotspot analyzer (`helpers/perfsmith_hotspots.py`)
- source-map-explorer (bundle analysis)

**Primary Workflows:**

| Workflow | File | Role |
|----------|------|------|
| Performance Optimization | `workflows/tier-2/13-performance-optimization.md` | Primary executor |
| CI/CD Pipeline | `workflows/tier-1/07-cicd-pipeline.md` | Build optimization phase |

**Outputs:**

- `reports/perfsmith_hotspots.md`
- `reports/perfsmith_bundle.json`

**Collaboration Rights:**

- Can request **SchemaSage** for database query performance correlation
- Can request **LintGuard** findings to correlate complexity with hotspots
- Should escalate critical findings to **AtlasReporter**

---

### 3. SchemaSage (Database Specialist)

**Script:** `ci_workflows/agent_schemasage.sh`

**Purpose:** Database analysis, migration validation, and optimization

**Tools:**

- PostgreSQL (`psql`)
- Custom EXPLAIN ANALYZE probes
- Migration dry-run scripts

**Primary Workflows:**

| Workflow | File | Role |
|----------|------|------|
| Database Migration | `workflows/tier-2/12-database-migration.md` | Primary executor |
| Performance Optimization | `workflows/tier-2/13-performance-optimization.md` | Query optimization support |

**Outputs:**

- `reports/schemasage_schema.txt`
- `reports/schemasage_explain.txt`
- `reports/schemasage_migration.log`
- `reports/schemasage_procedure.log`
- `reports/db_audit.md` (summary)

**Collaboration Rights:**

- Can request **ShieldProbe** for data privacy verification
- Can notify **PerfSmith** about query performance issues
- Should escalate schema drift to **AtlasReporter**

**Required Environment:**
- `DATABASE_URL` must be set

---

### 4. ShieldProbe (Security & Privacy Guardian)

**Script:** `ci_workflows/agent_shieldprobe.sh`

**Purpose:** Privacy and security checks for backend + frontend

**Tools:**

- pip-audit (Python dependency vulnerabilities)
- npm audit (JavaScript dependency vulnerabilities)
- Custom encryption regression tests
- Auth/shipping smoke tests

**Primary Workflows:**

| Workflow | File | Role |
|----------|------|------|
| Security Audit | `workflows/tier-1/04-security-audit.md` | Primary executor |
| Compliance & Auditing | `workflows/tier-2/20-compliance-auditing.md` | GDPR/privacy compliance |
| Incident Response | `workflows/tier-1/05-incident-response.md` | Post-incident validation |

**Outputs:**

- `reports/shieldprobe_backend.json`
- `reports/shieldprobe_frontend.json`
- `reports/shieldprobe_encryption.log`
- `reports/shieldprobe_shipping.log`
- `reports/security_findings.json` (summary)

**Collaboration Rights:**

- Can request **LintGuard** Bandit findings for code-level security
- Can request **SchemaSage** for data-at-rest verification
- Should escalate critical vulnerabilities to **AtlasReporter** immediately
- Has authority to **block** deployments for P0 security issues

---

### 5. AtlasReporter (Team Coordinator & Digest Builder)

**Script:** `ci_workflows/agent_atlasreporter.sh`

**Purpose:** Consolidates all agent outputs into a unified digest

**Primary Workflows:**

| Workflow | File | Role |
|----------|------|------|
| Documentation Generation | `workflows/tier-2/14-documentation-generation.md` | Report aggregation |
| CI/CD Pipeline | `workflows/tier-1/07-cicd-pipeline.md` | Final artifact assembly |

**Outputs:**

- `reports/weekly_agent_digest.md`

**Collaboration Rights:**

- Has **read access** to all agent outputs
- Can request re-runs from any agent if reports are missing or stale
- Responsible for **knowledge sharing** across agents
- Creates the **handoff summary** for human reviewers

---

## Execution Order (Pipeline)

```
┌──────────────────────────────────────────────────────────────────┐
│                     CI AGENT PIPELINE                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stage 1: LintGuard                                              │
│     ↓                                                            │
│  Stage 2: SchemaSage ────────────┐                               │
│           PerfSmith ─────────────┤ (parallel)                    │
│     ↓                            ↓                               │
│  Stage 3: ShieldProbe (waits for LintGuard + PerfSmith)          │
│     ↓                                                            │
│  Stage 4: AtlasReporter (waits for SchemaSage + ShieldProbe)     │
│     ↓                                                            │
│  Output: reports/ artifact                                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Defined in:** `ci_workflows/agents-ci.yml`

---

## Inter-Agent Collaboration Protocol

### 1. Assistance Requests

Agents can request assistance from other agents using the shared `reports/` directory:

```
reports/
├── .agent_requests/           ← Inter-agent requests (create if needed)
│   ├── lintguard_to_shieldprobe.json
│   └── perfsmith_to_schemasage.json
└── [agent outputs]
```

**Request Format:**
```json
{
  "from_agent": "PerfSmith",
  "to_agent": "SchemaSage",
  "request_type": "query_correlation",
  "context": "Hotspot detected in order_service.py line 145",
  "question": "Is the orders query at this line causing sequential scans?",
  "timestamp": "2025-12-19T03:30:00Z"
}
```

### 2. Knowledge Sharing

Agents share knowledge via:

- **Artifact cross-references** in their summary reports
- **AtlasReporter digest** which consolidates learnings
- **Recommended Actions** sections in each agent's output

### 3. Brainstorming / Judgment Improvement

When an agent encounters ambiguity:

1. **Log the ambiguity** in its output with a `[NEEDS_REVIEW]` tag
2. **Request input** from the most relevant peer agent
3. **AtlasReporter** collects all `[NEEDS_REVIEW]` items for human decision

### 4. Escalation Path

```
Individual Agent Finding
        ↓
   P0-P1 Issue?
        ↓
  ┌─────┴─────┐
  │    YES    │ → Immediate escalation to AtlasReporter + human review
  │    NO     │ → Include in regular digest
  └───────────┘
```

---

## Team Leader Responsibilities

### Initializer Agent (Team Leader)

**Reports to:** Human stakeholder  
**Coordinates:** SchemaSage, AtlasReporter

**Responsibilities:**

- Define the goal and scope before work begins
- Establish baseline state (DB schema, existing reports)
- Define acceptance checks that must pass
- Create work packets for Execution Agent

**Independence:**

- Can request SchemaSage to validate DB assumptions
- Can request AtlasReporter to generate baseline digest
- Can reach out to Review/Validation Agent for check definitions

---

### Execution Agent (Team Leader)

**Reports to:** Initializer Agent (receives work packets)  
**Coordinates:** LintGuard, PerfSmith

**Responsibilities:**

- Implement changes against artifacts
- Produce change records (diffs + notes)
- Ensure code quality during implementation
- Hand off to Review/Validation Agent

**Independence:**

- Can request LintGuard for real-time quality feedback
- Can request PerfSmith for performance impact analysis
- Can reach out to Initializer Agent for scope clarification
- Can reach out to Review/Validation Agent for early validation

---

### Review/Validation Agent (Team Leader)

**Reports to:** Execution Agent (receives change records)  
**Coordinates:** ShieldProbe, LintGuard

**Responsibilities:**

- Execute all defined checks
- Produce PASS/FAIL validation reports
- Approve and commit, or reject with feedback
- Initiate rollback if critical issues found

**Independence:**

- Can request ShieldProbe for security validation
- Can request LintGuard for code quality verification
- Can reach out to Execution Agent for clarification
- Can escalate to Initializer Agent if scope changed
- Has authority to **block** commits for P0 issues

---

## Cross-Team Collaboration

### Agent Independence

Each CI agent co-worker has **independence** to:

1. **Reach out to other agents** for assistance
2. **Brainstorm** with peer agents on complex findings
3. **Share knowledge** via artifact cross-references
4. **Improve judgment** by correlating findings across domains

### Collaboration Matrix

| Agent Requesting | Can Request From | For |
|------------------|------------------|-----|
| LintGuard | ShieldProbe | Security-specific code patterns |
| LintGuard | PerfSmith | Performance impact of complexity |
| PerfSmith | SchemaSage | Database query correlation |
| PerfSmith | LintGuard | Code complexity metrics |
| SchemaSage | ShieldProbe | Data privacy verification |
| SchemaSage | PerfSmith | Query performance impact |
| ShieldProbe | LintGuard | Bandit findings correlation |
| ShieldProbe | SchemaSage | Data-at-rest encryption check |
| AtlasReporter | All agents | Report consolidation |

### Knowledge Sharing Protocol

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE SHARING LOOP                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Agent discovers finding                                             │
│     ↓                                                                   │
│  2. Agent determines if cross-domain expertise needed                   │
│     ↓                                                                   │
│  3. Agent creates request in reports/.agent_requests/                   │
│     ↓                                                                   │
│  4. Peer agent responds with analysis                                   │
│     ↓                                                                   │
│  5. Originating agent incorporates learning                             │
│     ↓                                                                   │
│  6. AtlasReporter captures shared knowledge in digest                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Handoff Protocol Reference:** `.promptx/personas/AGENT_HANDOFF_PROTOCOL.md`

---

## Quick Reference: Who Does What

| Need to... | Primary Agent | Supporting Agent(s) |
|------------|---------------|---------------------|
| Check code quality | LintGuard | — |
| Find performance issues | PerfSmith | SchemaSage |
| Validate DB schema | SchemaSage | ShieldProbe |
| Audit security | ShieldProbe | LintGuard (Bandit) |
| Scan for vulnerabilities | ShieldProbe | — |
| Get consolidated report | AtlasReporter | All agents |
| Validate migrations | SchemaSage | — |
| Analyze bundle size | PerfSmith | — |
| Check GDPR compliance | ShieldProbe | SchemaSage |

---

## Running Locally

```bash
# Run all agents locally
./ci_workflows/run_agents_locally.sh

# Run individual agent
./ci_workflows/agent_lintguard.sh
./ci_workflows/agent_perfsmith.sh
./ci_workflows/agent_schemasage.sh   # Requires DATABASE_URL
./ci_workflows/agent_shieldprobe.sh
./ci_workflows/agent_atlasreporter.sh
```

---

## Adding a New Agent

1. Create `ci_workflows/agent_<name>.sh`
2. Define its workflow assignments in this document
3. Add it to `agents-ci.yml` with appropriate dependencies
4. Update AtlasReporter to include its outputs in the digest
5. Document collaboration rights and escalation rules

---

**Version:** 1.0  
**Created:** December 19, 2025  
**Maintained by:** Happy Place Development Team
