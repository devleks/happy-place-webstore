# 📋 Workflow Quick Reference Cheat Sheet

One-page reference for all Tier 1 workflows.

---

## Workflow Selection Guide

| Situation | Use Workflow |
|-----------|--------------|
| Starting/resuming a project | 01 Project Discovery |
| Creating feature branch | 02 Git Workflow |
| Reviewing PR/MR | 03 Code Review |
| Checking for vulnerabilities | 04 Security Audit |
| Production issue | 05 Incident Response |
| Designing new API | 06 API Design |
| Setting up builds/deploys | 07 CI/CD Pipeline |
| Testing UI components | 08 UAT Frontend |
| Testing integrations | 09 UAT Full-Stack |
| Debugging React issues | 10 React Debugging |
| Documenting sessions | Black Box |

---

## Quick Start Commands

```bash
# Always start with Black Box session
./blackbox.sh start "[workflow]-[topic]"

# Check status
./blackbox.sh status

# End session
./blackbox.sh end
```

---

## Workflow Quick References

### 01 - Project Discovery

```
Cascade: "Execute Project Discovery workflow"

Steps:
1. Analyze structure     → @src/ @package.json
2. Identify tech stack   → Languages, frameworks, DBs
3. Extract business rules → Domain logic, constraints
4. Generate SSOT         → Single Source of Truth doc
5. Create checkpoint     → Ready for development

Output: SSOT.md
```

### 02 - Git Workflow

```
Cascade: "Follow Git Workflow SOP"

Branch naming:
  feature/[ticket]-[description]
  bugfix/[ticket]-[description]
  hotfix/[version]-[description]

Commit format:
  type(scope): description [SESSION-ID]
  
Types: feat, fix, docs, style, refactor, test, chore
```

### 03 - Code Review

```
Cascade: "Execute Code Review on [PR/files]"

Severity levels:
  P0 - Critical  → Must fix before merge
  P1 - High      → Should fix before merge
  P2 - Medium    → Fix soon after merge
  P3 - Low       → Nice to have

Checklist:
  □ Correctness    □ Security
  □ Performance    □ Maintainability
```

### 04 - Security Audit

```
Cascade: "Run Security Audit"

OWASP Top 10 Check:
  A01 - Broken Access Control
  A02 - Cryptographic Failures
  A03 - Injection
  A04 - Insecure Design
  A05 - Security Misconfiguration
  A06 - Vulnerable Components
  A07 - Authentication Failures
  A08 - Data Integrity Failures
  A09 - Logging Failures
  A10 - SSRF

Commands:
  npm audit / pip-audit / cargo audit
  grep -r "password\|secret\|key" --include="*.env*"
```

### 05 - Incident Response

```
Cascade: "Execute Incident Response for [issue]"

Severity:
  P0 - Complete outage     → All hands, immediate
  P1 - Major degradation   → On-call + backup
  P2 - Partial impact      → On-call
  P3 - Minor issue         → Next business day

Timeline template:
  [HH:MM] Detected: [what]
  [HH:MM] Investigated: [finding]
  [HH:MM] Mitigated: [action]
  [HH:MM] Resolved: [fix]
```

### 06 - API Design

```
Cascade: "Design API for [feature]"

REST conventions:
  GET    /resources        → List
  GET    /resources/:id    → Read
  POST   /resources        → Create
  PUT    /resources/:id    → Replace
  PATCH  /resources/:id    → Update
  DELETE /resources/:id    → Delete

Status codes:
  200 OK, 201 Created, 204 No Content
  400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found
  500 Internal Error, 503 Service Unavailable
```

### 07 - CI/CD Pipeline

```
Cascade: "Set up CI/CD for [project]"

Pipeline stages:
  1. Install    → Dependencies
  2. Lint       → Code quality
  3. Test       → Unit + integration
  4. Build      → Compile/bundle
  5. Deploy     → Staging → Production

Key files:
  .github/workflows/*.yml
  .gitlab-ci.yml
  Jenkinsfile
```

### 08 - UAT Frontend

```
Cascade: "Run Frontend UAT"

Test types:
  Unit       → Components in isolation
  Integration→ Component interactions
  E2E        → User flows
  Visual     → Screenshot comparison
  A11y       → Accessibility

Tools:
  Jest, React Testing Library, Cypress
  Playwright, Chromatic, axe-core
```

### 09 - UAT Full-Stack

```
Cascade: "Run Full-Stack UAT"

Test layers:
  API        → Contract + integration
  Database   → Migrations + integrity
  Services   → Business logic
  E2E        → Complete flows

Tools:
  Supertest, Postman/Newman, k6
  TestContainers, Database seeders
```

### 10 - React Debugging

```
Cascade: "Debug React issue: [description]"

Common issues:
  - Infinite re-renders → Check useEffect deps
  - Stale state        → Use functional updates
  - Memory leaks       → Cleanup in useEffect
  - Prop drilling      → Consider context/state mgmt

Tools:
  React DevTools, console.log, debugger
  React.Profiler, why-did-you-render
```

---

## Black Box Integration

Every workflow should:

```bash
# 1. Start session
./blackbox.sh start "[workflow]-[topic]"

# 2. Log during execution
./blackbox.sh action "description" "result"
./blackbox.sh decision "what" "why"
./blackbox.sh issue "problem" "status"

# 3. End session
./blackbox.sh end
```

---

## Cascade Quick Commands

```
"Start session [topic]"
"Execute workflow [number]"
"Log decision: [what] because [why]"
"Log issue: [problem]"
"Checkpoint: [description]"
"End session"
"Search sessions for [query]"
```

---

## File Locations

```
workflows/
├── tier-1/
│   ├── 01-project-discovery.md
│   ├── 02-git-workflow.md
│   ├── 03-code-review.md
│   ├── 04-security-audit.md
│   ├── 05-incident-response.md
│   ├── 06-api-design.md
│   ├── 07-cicd-pipeline.md
│   ├── 08-uat-frontend.md
│   ├── 09-uat-fullstack.md
│   └── 10-react-debugging.md
└── quick-reference/
    └── workflow-cheatsheet.md  ← You are here

.windsurf-blackbox/             ← Session Documentation
.promptx/personas/              ← AI Agent Personas
```

---

*Tier 1 Workflow Cheat Sheet v1.0*
