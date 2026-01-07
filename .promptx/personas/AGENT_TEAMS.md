# Agent Teams & Collaboration Matrix

Complete team structure mapping AI agent personas to CI/CD agents for optimized development workflows.

## 📊 Team Overview

| AI Persona | Role | Primary CI Agents | Secondary CI Agents |
|------------|------|-------------------|---------------------|
| **Initializer** | Setup & Baseline | SchemaSage, AtlasReporter | PerfSmith |
| **Execution** | Implementation | LintGuard, PerfSmith | SchemaSage |
| **Review/Validation** | Quality Gate | ShieldProbe, LintGuard, AtlasReporter | All |
| **Developer** | Coding | LintGuard, PerfSmith | ShieldProbe |
| **Code Reviewer** | PR Review | All Agents | AtlasReporter |
| **Rebaser** | Git History | LintGuard | - |
| **Merger** | Integration | All Agents | AtlasReporter |
| **Multiplan Manager** | Orchestration | AtlasReporter | All |

---

## 🎯 Primary Teams

### Team 1: Initialization & Baseline

**Team Leader:** Initializer Agent  
**CI Co-Workers:**
- **SchemaSage** (Primary) - Database state baseline
- **AtlasReporter** (Primary) - Consolidated baseline report
- **PerfSmith** (Secondary) - Performance baseline metrics

**Workflow:**
```
1. Initializer defines goal/scope/constraints
2. SchemaSage captures DB schema snapshot
3. PerfSmith establishes performance baseline
4. AtlasReporter generates baseline digest
5. Initializer creates state.md with baselines
```

**Use Cases:**
- Starting new feature work
- Beginning sprint
- Establishing project baseline
- Post-release baseline capture

**Example:**
```bash
# Initializer workflow
./ci_workflows/agent_schemasage.sh        # Capture DB state
./ci_workflows/agent_perfsmith.sh         # Get performance baseline
./ci_workflows/agent_atlasreporter.sh     # Generate baseline report

# Initializer then creates:
# - work_packet.md (goal/scope/constraints)
# - state.md (current baseline from reports)
# - checks.md (acceptance criteria)
```

---

### Team 2: Development & Implementation

**Team Leader:** Execution Agent  
**CI Co-Workers:**
- **LintGuard** (Primary) - Real-time code quality
- **PerfSmith** (Primary) - Performance monitoring
- **SchemaSage** (Conditional) - If DB changes involved

**Workflow:**
```
1. Execution Agent implements changes
2. LintGuard runs continuously for code quality
3. PerfSmith monitors complexity/hotspots
4. SchemaSage validates DB changes (if applicable)
5. Execution Agent updates change_record.md
```

**Use Cases:**
- Feature implementation
- Bug fixes
- Refactoring
- Database migrations

**Example:**
```bash
# Development loop
while [ "$changes_pending" = true ]; do
    # Make changes
    git add .
    
    # Quick validation
    ./ci_workflows/agent_lintguard.sh
    
    # Check performance impact
    RUN_PERF_BUILD=1 ./ci_workflows/agent_perfsmith.sh
    
    # If DB changes
    export DATABASE_URL="..."
    ./ci_workflows/agent_schemasage.sh
done
```

---

### Team 3: Quality Assurance & Validation

**Team Leader:** Review/Validation Agent  
**CI Co-Workers:**
- **ShieldProbe** (Primary) - Security validation
- **LintGuard** (Primary) - Code quality check
- **SchemaSage** (Primary) - DB integrity check
- **PerfSmith** (Primary) - Performance validation
- **AtlasReporter** (Primary) - Final consolidated report

**Workflow:**
```
1. Review/Validation Agent triggers all checks
2. LintGuard: Code quality validation
3. ShieldProbe: Security & vulnerability scan
4. SchemaSage: DB schema validation
5. PerfSmith: Performance regression check
6. AtlasReporter: Generate validation digest
7. Review/Validation Agent: PASS/FAIL decision
```

**Use Cases:**
- Pre-commit validation
- PR merge checks
- Release validation
- Quality gate enforcement

**Example:**
```bash
# Full validation suite
./run_agents_locally.sh --parallel

# Review results
cat reports/weekly_agent_digest.md

# Review/Validation Agent decides:
# - PASS → git commit + push
# - FAIL (P0/P1) → request iteration
# - FAIL (P2/P3) → commit with warnings
```

---

### Team 4: Code Review & Assessment

**Team Leader:** Code Reviewer Agent  
**CI Co-Workers:**
- **LintGuard** (Primary) - Static analysis review
- **ShieldProbe** (Primary) - Security review
- **PerfSmith** (Primary) - Performance review
- **SchemaSage** (Conditional) - DB change review
- **AtlasReporter** (Primary) - Consolidated review report

**Workflow:**
```
1. Code Reviewer Agent analyzes PR diff
2. LintGuard: Check code quality issues
3. ShieldProbe: Identify security concerns
4. PerfSmith: Flag performance hotspots
5. SchemaSage: Review DB changes (if any)
6. AtlasReporter: Generate review digest
7. Code Reviewer: Provide structured feedback
```

**Use Cases:**
- Pull request reviews
- Code quality audits
- Security assessments
- Pre-merge validation

**Example:**
```bash
# PR review workflow
git checkout pr/123
./run_agents_locally.sh

# Code Reviewer analyzes:
# - reports/lintguard.json (code quality)
# - reports/security_findings.json (vulnerabilities)
# - reports/perfsmith_hotspots.md (performance)
# - reports/weekly_agent_digest.md (summary)

# Provides feedback:
# - P0: Critical security vulnerability (block merge)
# - P1: Performance regression (request changes)
# - P2: Code style issues (approve with comments)
# - P3: Suggestions (approve)
```

---

### Team 5: Git History Management

**Team Leader:** Rebaser Agent  
**CI Co-Workers:**
- **LintGuard** (Primary) - Ensure each commit is clean

**Workflow:**
```
1. Rebaser Agent reviews commit history
2. Plans rebase strategy
3. Performs interactive rebase
4. After each commit: LintGuard validates
5. Ensures atomic, logical commits
```

**Use Cases:**
- Cleaning commit history before PR
- Organizing work into logical commits
- Fixing broken commits
- Preparing for merge

**Example:**
```bash
# Rebase workflow
git rebase -i main

# For each commit during rebase:
git rebase --continue
./ci_workflows/agent_lintguard.sh  # Ensure commit is clean

# After rebase complete:
git log --oneline -10  # Verify clean history
```

---

### Team 6: Branch Integration

**Team Leader:** Merger Agent  
**CI Co-Workers:**
- **All CI Agents** (Primary) - Full validation
- **AtlasReporter** (Primary) - Integration report

**Workflow:**
```
1. Merger Agent analyzes branches
2. Plans merge strategy
3. Performs merge/rebase
4. Full validation suite runs:
   - LintGuard: Code quality
   - ShieldProbe: Security
   - SchemaSage: DB integrity
   - PerfSmith: Performance
5. AtlasReporter: Integration digest
6. Merger Agent: Validates success
```

**Use Cases:**
- Merging feature branches
- Release branch integration
- Hotfix merging
- Coordinating multi-team merges

**Example:**
```bash
# Merge workflow
git checkout main
git merge --no-ff feature/new-auth

# Full validation
./run_agents_locally.sh --parallel

# Review integration report
cat reports/weekly_agent_digest.md

# If issues found:
if [ critical_issues -gt 0 ]; then
    git merge --abort
    # Fix issues and retry
fi
```

---

### Team 7: Project Orchestration

**Team Leader:** Multiplan Manager Agent  
**CI Co-Workers:**
- **AtlasReporter** (Primary) - Progress tracking
- **All Agents** (Secondary) - Coordination

**Workflow:**
```
1. Multiplan Manager breaks down project
2. Creates workstreams and dependencies
3. Coordinates multiple teams/developers
4. AtlasReporter tracks progress
5. Adjusts plans based on feedback
6. All agents validate at checkpoints
```

**Use Cases:**
- Large feature development
- Multi-team projects
- Release coordination
- Complex refactoring

**Example:**
```bash
# Project tracking
./ci_workflows/agent_atlasreporter.sh  # Daily

# Multiplan Manager reviews:
# - Completed work (from digest)
# - Blockers (from issue counts)
# - Progress trends (comparing reports)
# - Risk areas (from security/performance reports)

# Adjusts plan accordingly
```

---

### Team 8: General Development

**Team Leader:** Developer Agent  
**CI Co-Workers:**
- **LintGuard** (Primary) - Code quality feedback
- **PerfSmith** (Primary) - Performance awareness
- **ShieldProbe** (Secondary) - Security awareness

**Workflow:**
```
1. Developer Agent codes features
2. LintGuard provides real-time feedback
3. PerfSmith monitors complexity
4. ShieldProbe alerts on security issues
5. Developer iterates until clean
```

**Use Cases:**
- Daily development work
- Feature implementation
- Bug fixes
- Technical debt reduction

**Example:**
```bash
# Development loop
while coding; do
    # Write code
    
    # Quick check
    ./ci_workflows/agent_lintguard.sh
    
    # If introducing new functions
    ./ci_workflows/agent_perfsmith.sh
    
    # If handling sensitive data
    ./ci_workflows/agent_shieldprobe.sh
done
```

---

## 🔄 Complete Workflow Example

### Feature Development Lifecycle

```
Phase 1: INITIALIZATION
├─ Initializer Agent (Team 1)
│  ├─ Runs: SchemaSage (DB baseline)
│  ├─ Runs: PerfSmith (performance baseline)
│  ├─ Runs: AtlasReporter (baseline digest)
│  └─ Creates: work_packet.md, state.md, checks.md
│
Phase 2: PLANNING
├─ Multiplan Manager Agent (Team 7)
│  ├─ Reviews: baseline reports
│  ├─ Breaks down: work into tasks
│  └─ Creates: execution plan
│
Phase 3: DEVELOPMENT
├─ Developer/Execution Agent (Team 2/8)
│  ├─ Implements: features
│  ├─ Runs: LintGuard (continuous)
│  ├─ Runs: PerfSmith (periodic)
│  └─ Updates: change_record.md
│
Phase 4: VALIDATION
├─ Review/Validation Agent (Team 3)
│  ├─ Runs: All CI agents
│  │  ├─ LintGuard (code quality)
│  │  ├─ ShieldProbe (security)
│  │  ├─ SchemaSage (DB integrity)
│  │  └─ PerfSmith (performance)
│  ├─ Runs: AtlasReporter (digest)
│  └─ Decides: PASS/FAIL/ITERATE
│
Phase 5: CODE REVIEW
├─ Code Reviewer Agent (Team 4)
│  ├─ Reviews: All agent reports
│  ├─ Analyzes: Diff + change record
│  └─ Provides: Structured feedback (P0-P3)
│
Phase 6: HISTORY CLEANUP
├─ Rebaser Agent (Team 5)
│  ├─ Organizes: Commit history
│  ├─ Validates: Each commit (LintGuard)
│  └─ Prepares: For merge
│
Phase 7: INTEGRATION
└─ Merger Agent (Team 6)
   ├─ Merges: Branch to main
   ├─ Runs: Full validation suite
   ├─ Runs: AtlasReporter (integration report)
   └─ Confirms: Success or rollback
```

---

## 📋 Agent Handoff Protocol

### Standard Handoff Format

```markdown
## Handoff to [Next Agent]

**From:** [Current Agent]  
**To:** [Next Agent]  
**Status:** [Complete/Blocked/Needs Review]

**Completed:**
- Task 1
- Task 2

**Artifacts:**
- file1.md
- file2.json
- reports/agent_reports/

**CI Reports:**
- LintGuard: PASS (5 warnings)
- ShieldProbe: PASS (0 critical)
- PerfSmith: PASS (2 hotspots)

**Next Steps:**
1. Action item 1
2. Action item 2

**Blockers:** None / [List blockers]
```

### Handoff Examples

#### Initializer → Execution
```
From: Initializer Agent
To: Execution Agent

Completed:
- Baseline captured (SchemaSage, PerfSmith, AtlasReporter)
- work_packet.md created with goal/scope/constraints
- state.md established with baselines
- checks.md defined with acceptance criteria

Artifacts:
- work_packet.md
- state.md  
- checks.md
- reports/baseline/

Next Steps:
1. Implement user authentication (OAuth2)
2. Run LintGuard + PerfSmith during development
3. Update change_record.md with each change
4. Handoff to Review/Validation when complete
```

#### Execution → Review/Validation
```
From: Execution Agent
To: Review/Validation Agent

Completed:
- User authentication implemented
- Tests written and passing
- change_record.md updated

Artifacts:
- src/auth/ (new)
- tests/auth/ (new)
- change_record.md

CI Reports (during development):
- LintGuard: 3 warnings (addressed)
- PerfSmith: No hotspots
- SchemaSage: Schema changes documented

Next Steps:
1. Run full validation suite
2. Check all acceptance criteria from checks.md
3. Decide: PASS/FAIL/ITERATE
```

#### Review/Validation → Code Reviewer
```
From: Review/Validation Agent
To: Code Reviewer Agent

Status: PASS (with minor findings)

Validation Results:
- LintGuard: PASS (0 issues)
- ShieldProbe: PASS (2 P3 recommendations)
- SchemaSage: PASS (migration scripts valid)
- PerfSmith: PASS (no regression)
- AtlasReporter: Digest generated

Artifacts:
- reports/weekly_agent_digest.md
- reports/security_findings.json
- reports/perfsmith_hotspots.md

Next Steps:
1. Review PR for code quality
2. Assess security recommendations
3. Provide structured feedback
```

---

## 🎯 Quick Reference Matrix

### When to Engage Which Team

| Scenario | Primary Team | Secondary Teams |
|----------|--------------|-----------------|
| Starting new feature | Team 1 (Initializer) | Team 7 (Multiplan) |
| Daily coding | Team 8 (Developer) | Team 2 (Execution) |
| Before commit | Team 3 (Review/Validation) | - |
| PR review | Team 4 (Code Reviewer) | Team 3 (Validation) |
| Cleaning history | Team 5 (Rebaser) | - |
| Merging to main | Team 6 (Merger) | Team 3 (Validation) |
| Complex project | Team 7 (Multiplan) | All teams |
| Bug fix | Team 8 (Developer) → Team 3 (Validation) | - |
| Security audit | Team 3 (Validation) + ShieldProbe | Team 4 (Reviewer) |
| Performance issue | Team 8 (Developer) + PerfSmith | Team 3 (Validation) |
| DB migration | Team 2 (Execution) + SchemaSage | Team 3 (Validation) |

---

## 🚀 Team Coordination Examples

### Example 1: New Feature Development

```bash
# 1. INITIALIZATION (Team 1)
./ci_workflows/agent_schemasage.sh
./ci_workflows/agent_perfsmith.sh
./ci_workflows/agent_atlasreporter.sh
# Initializer creates work_packet.md, state.md, checks.md

# 2. DEVELOPMENT (Team 2/8)
while [ "$feature_incomplete" = true ]; do
    # Code
    ./ci_workflows/agent_lintguard.sh  # Quick check
done

# 3. VALIDATION (Team 3)
./run_agents_locally.sh --parallel
# Review/Validation decides: PASS

# 4. REVIEW (Team 4)
# Code Reviewer analyzes reports + diff
# Provides feedback

# 5. CLEANUP (Team 5)
git rebase -i main
# Rebaser organizes commits

# 6. MERGE (Team 6)
git checkout main
git merge --no-ff feature/auth
./run_agents_locally.sh --parallel
# Merger validates integration
```

### Example 2: Hotfix Workflow

```bash
# 1. QUICK INIT (Lightweight)
git checkout -b hotfix/security-patch
# Skip full initialization for urgency

# 2. FIX (Team 8)
# Make fix
./ci_workflows/agent_lintguard.sh
./ci_workflows/agent_shieldprobe.sh  # Critical!

# 3. VALIDATION (Team 3)
./run_agents_locally.sh
# Ensure fix doesn't break anything

# 4. FAST-TRACK MERGE (Team 6)
git checkout main
git merge hotfix/security-patch
./run_agents_locally.sh
# Validate and push
```

### Example 3: Large Refactoring

```bash
# 1. PLANNING (Team 7)
# Multiplan Manager breaks down work
# Creates multiple workstreams

# 2. BASELINE (Team 1)
./run_agents_locally.sh --parallel
# Capture "before" state

# 3. ITERATIVE EXECUTION (Team 2)
for module in $modules; do
    # Refactor module
    ./ci_workflows/agent_lintguard.sh
    ./ci_workflows/agent_perfsmith.sh  # Check complexity reduction
    git commit -m "Refactor: $module"
done

# 4. FULL VALIDATION (Team 3)
./run_agents_locally.sh --parallel
# Compare to baseline
# Ensure improvement

# 5. REVIEW (Team 4)
# Code Reviewer validates:
# - Maintained functionality
# - Improved metrics
# - No regressions

# 6. CLEANUP & MERGE (Teams 5 & 6)
git rebase -i main  # Organize commits
git checkout main
git merge feature/refactor
./run_agents_locally.sh  # Final check
```

---

## 📊 Success Metrics by Team

### Team 1 (Initialization)
- ✅ Clear work packet created
- ✅ Baseline metrics captured
- ✅ Acceptance criteria defined
- ✅ State documented

### Team 2 (Execution)
- ✅ Changes match work packet
- ✅ LintGuard passes
- ✅ Change record updated
- ✅ Tests passing

### Team 3 (Review/Validation)
- ✅ All checks pass
- ✅ No P0/P1 issues
- ✅ Acceptance criteria met
- ✅ Safe to commit

### Team 4 (Code Review)
- ✅ Comprehensive feedback provided
- ✅ Issues categorized (P0-P3)
- ✅ Clear action items
- ✅ Constructive tone

### Team 5 (Rebaser)
- ✅ Clean commit history
- ✅ Logical atomic commits
- ✅ Each commit passes LintGuard
- ✅ Clear commit messages

### Team 6 (Merger)
- ✅ Successful integration
- ✅ All tests pass
- ✅ No conflicts remain
- ✅ Integration validated

### Team 7 (Multiplan)
- ✅ Work decomposed effectively
- ✅ Dependencies identified
- ✅ Progress tracked
- ✅ Risks mitigated

### Team 8 (Developer)
- ✅ Clean code written
- ✅ Tests included
- ✅ Documentation updated
- ✅ Quality standards met

---

## 🔧 Customization

Adapt these teams to your needs:

**For Solo Developers:**
- Combine roles (you play all agents)
- Use CI agents as checkpoints
- Follow the workflow sequence

**For Small Teams:**
- Assign agent personas to individuals
- Use CI agents for automation
- Regular handoffs in standups

**For Large Teams:**
- Dedicated roles per persona
- Automated CI agent runs
- Formal handoff documentation

**For AI-Assisted Development:**
- Prompt AI with specific persona
- Reference CI agent reports
- Follow handoff protocols

---

## 📚 Related Documentation

- **Personas:** See individual `agent-*.md` files
- **Handoff Protocol:** See `AGENT_HANDOFF_PROTOCOL.md`
- **CI Agents:** See `AGENT_OPTIMIZATION_GUIDE.md`
- **Workflows:** See `WORKFLOW_COMPARISON.md`

---

**Version:** 1.0  
**Last Updated:** December 2024  
**Purpose:** Integrate AI agent personas with CI/CD agents for optimal development workflow

🚀 Ready to build better software with coordinated agent teams!
