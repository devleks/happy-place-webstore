# 📋 Development Workflows

This directory contains all Tier 1 development workflows optimized for Windsurf IDE and Cascade AI.

## Directory Structure

```
workflows/
├── README.md                          ← You are here
├── tier-1/                            ← Core development workflows
│   ├── 01-project-discovery.md        ← Universal Project Discovery + SSOT
│   ├── 02-git-workflow.md             ← Git Workflow SOP
│   ├── 03-code-review.md              ← Code Review (P0-P3 framework)
│   ├── 04-security-audit.md           ← Security Audit (OWASP)
│   ├── 05-incident-response.md        ← Incident Response
│   ├── 06-api-design.md               ← API Design (REST/GraphQL)
│   ├── 07-cicd-pipeline.md            ← CI/CD Pipeline
│   ├── 08-uat-frontend.md             ← Automated UAT (Frontend)
│   ├── 09-uat-fullstack.md            ← Full-Stack UAT
│   └── 10-react-debugging.md          ← React Debugging
├── tier-2/                            ← Extended workflows (future)
│   └── [additional workflows]
└── quick-reference/                   ← Cheat sheets
    └── workflow-cheatsheet.md
```

## Workflow Status

### Tier 1 - Core Development Workflows

| # | Workflow | File | Status |
|---|----------|------|--------|
| 1 | Universal Project Discovery + SSOT | `tier-1/01-project-discovery.md` | ✅ |
| 2 | Git Workflow SOP | `tier-1/02-git-workflow.md` | ✅ |
| 3 | Code Review | `tier-1/03-code-review.md` | ✅ |
| 4 | Security Audit | `tier-1/04-security-audit.md` | ✅ |
| 5 | Incident Response | `tier-1/05-incident-response.md` | ✅ |
| 6 | API Design | `tier-1/06-api-design.md` | ✅ |
| 7 | CI/CD Pipeline | `tier-1/07-cicd-pipeline.md` | ✅ |
| 8 | Automated UAT (Frontend) | `tier-1/08-uat-frontend.md` | ✅ |
| 9 | Full-Stack UAT | `tier-1/09-uat-fullstack.md` | ✅ |
| 10 | React Debugging | `tier-1/10-react-debugging.md` | ✅ |
| 11 | Session Documentation (Black Box) | `.windsurf-blackbox/` | ✅ |

### Tier 2 - Extended Workflows

| # | Workflow | File | Status |
|---|----------|------|--------|
| 12 | Database Migration | `tier-2/12-database-migration.md` | ✅ |
| 13 | Performance Optimization | `tier-2/13-performance-optimization.md` | ✅ |
| 14 | Documentation Generation | `tier-2/14-documentation-generation.md` | ✅ |
| 15 | Technical Debt Management | `tier-2/15-technical-debt-management.md` | ✅ |
| 16 | Feature Flag Management | `tier-2/16-feature-flag-management.md` | ✅ |
| 17 | A/B Testing | `tier-2/17-ab-testing.md` | ✅ |
| 18 | Monitoring & Alerting | `tier-2/18-monitoring-alerting.md` | ✅ |
| 19 | Disaster Recovery | `tier-2/19-disaster-recovery.md` | ✅ |
| 20 | Compliance & Auditing | `tier-2/20-compliance-auditing.md` | ✅ |

## Integration Map

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW ECOSYSTEM                                  │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│                    ┌─────────────────────────┐                             │
│                    │   01 PROJECT DISCOVERY  │                             │
│                    │        + SSOT           │◀─── Start here              │
│                    └───────────┬─────────────┘                             │
│                                │                                           │
│         ┌──────────────────────┼──────────────────────┐                    │
│         ▼                      ▼                      ▼                    │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐              │
│  │   DEVELOP   │       │   REVIEW    │       │   DEPLOY    │              │
│  ├─────────────┤       ├─────────────┤       ├─────────────┤              │
│  │ 06 API      │       │ 03 Code     │       │ 07 CI/CD    │              │
│  │ 02 Git      │       │ 04 Security │       │ 08-09 UAT   │              │
│  │ 10 Debug    │       │             │       │             │              │
│  └──────┬──────┘       └──────┬──────┘       └──────┬──────┘              │
│         │                     │                     │                      │
│         └─────────────────────┴─────────────────────┘                      │
│                               │                                            │
│                    ┌──────────▼──────────┐                                 │
│                    │  05 INCIDENT        │◀─── Production issues           │
│                    │     RESPONSE        │                                 │
│                    └─────────────────────┘                                 │
│                                                                            │
│  ══════════════════════════════════════════════════════════════════════   │
│       ALL WORKFLOWS INTEGRATE WITH BLACK BOX FOR CONTINUITY               │
│  ══════════════════════════════════════════════════════════════════════   │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## How to Use

### With Cascade AI

```
"Execute the Code Review workflow on the current PR"
"Start a Security Audit using workflow 04"
"Follow the Git Workflow for this feature branch"
```

### With Black Box Integration

```bash
# Start a session for the workflow
./blackbox.sh start "code-review-pr-123"

# Reference workflow in session
# [Cascade will follow workflow steps and log to Black Box]

# End session
./blackbox.sh end
```

## Complete Project Structure

```
your-project/
├── .promptx/                    ← AI Agent Personas
│   └── personas/
│       ├── developer.md
│       ├── reviewer.md
│       ├── rebaser.md
│       ├── merger.md
│       └── multiplan-manager.md
├── workflows/                   ← Development Workflows (THIS FOLDER)
│   ├── tier-1/
│   └── quick-reference/
├── .windsurf-blackbox/          ← Session Documentation
│   ├── sessions/
│   ├── catalog/
│   └── scripts/blackbox.sh
├── .windsurfrules               ← Cascade Rules
├── SSOT.md                      ← Single Source of Truth
└── blackbox.sh                  ← Convenience symlink
```

## Quick Reference

| Need To... | Use Workflow |
|------------|--------------|
| Start a new project | 01 Project Discovery |
| Manage branches/commits | 02 Git Workflow |
| Review code changes | 03 Code Review |
| Check for vulnerabilities | 04 Security Audit |
| Handle production issues | 05 Incident Response |
| Design APIs | 06 API Design |
| Set up pipelines | 07 CI/CD Pipeline |
| Test frontend | 08 UAT Frontend |
| Test full stack | 09 UAT Full-Stack |
| Debug React apps | 10 React Debugging |
| Document sessions | 11 Black Box |
| Migrate database | 12 Database Migration |
| Optimize performance | 13 Performance Optimization |
| Generate documentation | 14 Documentation Generation |
| Manage tech debt | 15 Technical Debt Management |
| Manage feature flags | 16 Feature Flag Management |
| Run A/B tests | 17 A/B Testing |
| Set up monitoring | 18 Monitoring & Alerting |
| Plan disaster recovery | 19 Disaster Recovery |
| Handle compliance | 20 Compliance & Auditing |

---

*Tier 1 Workflow Collection v1.0*
*Optimized for Windsurf IDE + Cascade AI*
