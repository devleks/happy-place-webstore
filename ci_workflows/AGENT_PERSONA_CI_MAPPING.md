# Agent Persona → CI Agent Integration Guide

Complete mapping of Agent Personas to CI Agents for optimal workflow integration.

## 📚 Agent Persona Reference Files

Before using this guide, familiarize yourself with the Agent Personas:

| Persona | File | Purpose |
|---------|------|---------|
| **Developer Agent** | [agent-developer.md](agent-developer.md) | Coding, debugging, and implementation tasks |
| **Code Reviewer Agent** | [agent-code-reviewer.md](agent-code-reviewer.md) | Code quality assurance and reviews |
| **Rebaser Agent** | [agent-rebaser.md](agent-rebaser.md) | Git history management and rebasing |
| **Merger Agent** | [agent-merger.md](agent-merger.md) | Branch merging and integration |
| **Multiplan Manager** | [agent-multiplan-manager.md](agent-multiplan-manager.md) | Orchestrating parallel work and complex projects |
| **Initializer Agent** | [agent-initializer.md](agent-initializer.md) | Define goals and establish initial baseline |
| **Execution Agent** | [agent-execution.md](agent-execution.md) | Implement changes and produce change records |
| **Review/Validation Agent** | [agent-review-validation.md](agent-review-validation.md) | Execute checks and approve/iterate/rollback |

**Additional Resources:**
- [AGENT_PERSONAS_README.md](AGENT_PERSONAS_README.md) - Overview of all personas
- AGENT_HANDOFF_PROTOCOL.md - Standard collaboration loop (to be added to your project)

> **📁 File Organization Options:**
> 
> **Option 1: Review in current directory (immediate use)**
> ```
> downloaded-files/
> ├── agent-developer.md
> ├── agent-code-reviewer.md
> ├── agent-*.md (all persona files)
> ├── AGENT_PERSONA_CI_MAPPING.md (this file)
> └── ... (CI agent files)
> ```
> All links in this document work when files are in the same directory.
> 
> **Option 2: Integrate into project (recommended for teams)**
> ```
> your-project/
> ├── .promptx/
> │   └── personas/
> │       ├── agent-developer.md
> │       ├── agent-code-reviewer.md
> │       └── ... (copy all agent-*.md files here)
> └── ci_workflows/
>     ├── agent_lintguard.sh
>     ├── agent_schemasage.sh
>     └── ... (CI agent scripts)
> ```
> 
> **Setup script for Option 2:**
> ```bash
> # Create directory structure
> mkdir -p .promptx/personas
> 
> # Copy persona files
> cp agent-*.md .promptx/personas/
> cp AGENT_PERSONAS_README.md .promptx/personas/
> 
> # Copy this mapping guide
> cp AGENT_PERSONA_CI_MAPPING.md docs/
> ```

---

## 🤖 CI Agent Reference

The CI Agents used in this integration guide:

| CI Agent | Script | Purpose |
|----------|--------|---------|
| **LintGuard** | `agent_lintguard.sh` | Static code analysis (Python + JavaScript) |
| **SchemaSage** | `agent_schemasage.sh` | Database optimization & analysis |
| **PerfSmith** | `agent_perfsmith.sh` | Performance profiling & bundle analysis |
| **ShieldProbe** | `agent_shieldprobe.sh` | Security scanning & secret detection |
| **AtlasReporter** | `agent_atlasreporter.sh` | Consolidated reporting & digest |

---

## 📊 Comprehensive Mapping Table

| Agent Persona | Persona Reference | Primary CI Co-Workers | Secondary CI Co-Workers | Why This Combination |
|---------------|-------------------|----------------------|------------------------|----------------------|
| **Developer Agent** | [agent-developer.md](agent-developer.md) | LintGuard, PerfSmith | ShieldProbe | **Real-time feedback during development**<br>• LintGuard catches code quality issues early<br>• PerfSmith identifies hotspots for optimization<br>• ShieldProbe ensures security-aware development |
| **Code Reviewer Agent** | [agent-code-reviewer.md](agent-code-reviewer.md) | LintGuard, ShieldProbe, AtlasReporter | PerfSmith, SchemaSage | **Comprehensive quality assessment**<br>• LintGuard provides static analysis findings<br>• ShieldProbe reports security vulnerabilities<br>• AtlasReporter gives consolidated P0-P3 view<br>• PerfSmith highlights performance concerns<br>• SchemaSage validates DB changes |
| **Rebaser Agent** | [agent-rebaser.md](agent-rebaser.md) | LintGuard | AtlasReporter | **Ensure clean commits**<br>• LintGuard validates each commit is clean<br>• AtlasReporter confirms no regressions introduced<br>• Minimal CI needs (Git-focused role) |
| **Merger Agent** | [agent-merger.md](agent-merger.md) | LintGuard, ShieldProbe, AtlasReporter | SchemaSage, PerfSmith | **Integration validation**<br>• LintGuard ensures merge doesn't break quality<br>• ShieldProbe validates no security regressions<br>• SchemaSage validates DB migrations merge cleanly<br>• AtlasReporter provides integration status report |
| **Multiplan Manager** | [agent-multiplan-manager.md](agent-multiplan-manager.md) | AtlasReporter | All Agents | **Strategic planning and monitoring**<br>• AtlasReporter provides consolidated status<br>• All agents inform planning decisions<br>• Tracks progress across workstreams<br>• Identifies blockers early |
| **Initializer Agent** | [agent-initializer.md](agent-initializer.md) | SchemaSage, AtlasReporter | ShieldProbe | **Baseline establishment**<br>• SchemaSage captures initial DB state<br>• AtlasReporter aggregates baseline reports<br>• ShieldProbe defines security requirements<br>• Sets success criteria for validation |
| **Execution Agent** | [agent-execution.md](agent-execution.md) | LintGuard, PerfSmith | ShieldProbe | **Implementation quality**<br>• LintGuard provides immediate code feedback<br>• PerfSmith tracks performance impact<br>• ShieldProbe ensures secure implementation<br>• Tight feedback loop during execution |
| **Review/Validation Agent** | [agent-review-validation.md](agent-review-validation.md) | ShieldProbe, LintGuard, AtlasReporter | SchemaSage, PerfSmith | **Comprehensive validation**<br>• ShieldProbe runs security checks<br>• LintGuard validates quality standards<br>• AtlasReporter provides PASS/FAIL report<br>• SchemaSage validates DB changes<br>• Decides commit/iterate/rollback |

### 🔗 Quick Navigation

**Jump to detailed integration patterns:**
- [Developer Agent Integration](#developer-agent--ci-agents)
- [Code Reviewer Agent Integration](#code-reviewer-agent--ci-agents)
- [Review/Validation Agent Integration](#reviewvalidation-agent--ci-agents)
- [Multiplan Manager Integration](#multiplan-manager-agent--ci-agents)

**Jump to workflow examples:**
- [Feature Development Lifecycle](#example-1-feature-development-lifecycle)
- [Integration Checklists](#-integration-checklists)
- [Configuration Examples](#-configuration-examples)

---

## 🔄 Workflow Integration Examples

### Example 1: Feature Development Lifecycle

```
1. INITIALIZER AGENT
   └─> Runs: SchemaSage (baseline DB state)
   └─> Runs: AtlasReporter (initial report)
   └─> Defines: Success criteria, rollback strategy

2. MULTIPLAN MANAGER
   └─> Reviews: AtlasReporter (current state)
   └─> Plans: Break down into tasks
   └─> Assigns: Tasks to execution streams

3. EXECUTION AGENT (per task)
   └─> Implements: Feature code
   └─> Runs: LintGuard (continuous feedback)
   └─> Runs: PerfSmith (performance check)
   └─> Updates: change_record.md

4. REVIEW/VALIDATION AGENT
   └─> Runs: LintGuard (full scan)
   └─> Runs: ShieldProbe (security scan)
   └─> Runs: SchemaSage (DB validation)
   └─> Generates: AtlasReporter (comprehensive report)
   └─> Decision: PASS → commit | FAIL → iterate

5. REBASER AGENT
   └─> Cleans: Commit history
   └─> Runs: LintGuard (verify each commit)
   └─> Validates: AtlasReporter (no regressions)

6. MERGER AGENT
   └─> Merges: To main branch
   └─> Runs: All CI Agents (integration validation)
   └─> Generates: AtlasReporter (merge report)
```

---

## 🎯 Detailed Integration Patterns

### Developer Agent + CI Agents

**When to Run:**
- After every significant code change
- Before committing
- During local development

**CI Agent Sequence:**
```bash
# Quick local validation
./ci_workflows/agent_lintguard.sh         # 8s - Immediate feedback
./ci_workflows/agent_perfsmith.sh         # 15s - Performance impact

# If touching security-sensitive code
./ci_workflows/agent_shieldprobe.sh       # 25s - Security check
```

**Integration Points:**
```python
# Developer Agent workflow
def implement_feature():
    write_code()
    run_tests()
    
    # CI Integration Point 1
    lint_results = run_ci_agent("lintguard")
    if lint_results.total_issues > 10:
        fix_issues(lint_results)
    
    # CI Integration Point 2
    perf_results = run_ci_agent("perfsmith")
    if perf_results.has_hotspots():
        optimize_code(perf_results.hotspots)
    
    commit_changes()
```

---

### Code Reviewer Agent + CI Agents

**When to Run:**
- On every pull request
- Before code review meetings
- After addressing review comments

**CI Agent Sequence:**
```bash
# Comprehensive review suite
./ci_workflows/agent_lintguard.sh         # Static analysis
./ci_workflows/agent_shieldprobe.sh       # Security scan
./ci_workflows/agent_perfsmith.sh         # Performance analysis
./ci_workflows/agent_schemasage.sh        # DB changes (if applicable)
./ci_workflows/agent_atlasreporter.sh     # Consolidated report
```

**Integration Points:**
```markdown
# Code Review Template Enhanced with CI Reports

## PR Review Checklist

### Automated Checks (from CI Agents)
- [ ] LintGuard: {{lintguard.total_issues}} issues found
  - P0 Critical: {{lintguard.critical}}
  - P1 High: {{lintguard.high}}
- [ ] ShieldProbe: {{shieldprobe.risk_level}} risk level
  - Critical Vulns: {{shieldprobe.critical_count}}
- [ ] PerfSmith: {{perfsmith.recommendations_count}} recommendations
- [ ] AtlasReporter: Overall status: {{atlas.status}}

### Manual Review
- [ ] Code logic is sound
- [ ] Tests are comprehensive
- [ ] Documentation updated
```

---

### Review/Validation Agent + CI Agents

**When to Run:**
- Before every commit
- After addressing feedback
- As final validation gate

**CI Agent Sequence:**
```bash
# Full validation suite
./run_agents_locally.sh --parallel        # Run all agents

# Or sequentially for debugging
./ci_workflows/agent_lintguard.sh
./ci_workflows/agent_shieldprobe.sh
./ci_workflows/agent_schemasage.sh
./ci_workflows/agent_perfsmith.sh
./ci_workflows/agent_atlasreporter.sh
```

**Decision Framework:**
```python
# Review/Validation Agent decision logic
def validate_and_decide():
    # Run all CI agents
    results = {
        'lint': run_ci_agent('lintguard'),
        'security': run_ci_agent('shieldprobe'),
        'perf': run_ci_agent('perfsmith'),
        'db': run_ci_agent('schemasage'),
        'summary': run_ci_agent('atlasreporter')
    }
    
    # Aggregate findings
    critical_issues = (
        results['lint'].critical_count +
        results['security'].critical_count
    )
    
    # Decision logic
    if critical_issues > 0:
        return Decision.ROLLBACK, "Critical issues found"
    
    if results['summary'].total_issues > 50:
        return Decision.ITERATE, "Too many issues, needs cleanup"
    
    if results['security'].risk_level == "high":
        return Decision.ITERATE, "Security concerns"
    
    return Decision.COMMIT, "All checks passed"
```

---

### Multiplan Manager Agent + CI Agents

**When to Run:**
- During project planning
- Weekly progress reviews
- Before milestone releases

**CI Agent Usage:**
```bash
# Historical trend analysis
./ci_workflows/agent_atlasreporter.sh     # Current state
cat reports/weekly_agent_digest.md        # Review trends

# Planning inputs
cat reports/perfsmith_hotspots.md         # Performance concerns
cat reports/security_findings.json        # Security backlog
cat reports/db_audit.md                   # DB optimization needs
```

**Planning Template:**
```markdown
# Project Plan: {{project_name}}

## Baseline Assessment (from CI Agents)

### Code Quality (LintGuard)
- Current issues: {{lint_total}}
- Target: <10 issues
- Estimated cleanup: {{lint_cleanup_hours}}h

### Security (ShieldProbe)
- Current vulnerabilities: {{security_total}}
- Critical: {{security_critical}} (MUST fix before launch)
- Target: 0 critical, <5 total

### Performance (PerfSmith)
- Hotspots identified: {{perf_hotspots}}
- Large files: {{perf_large_files}}
- Target: Refactor top 5 hotspots

### Database (SchemaSage)
- Slow queries: {{db_slow_queries}}
- Missing indexes: {{db_missing_indexes}}
- Target: <2s query time

## Work Breakdown
Based on CI findings, prioritized tasks:

### P0 (Critical) - Sprint 1
1. Fix {{security_critical}} critical vulnerabilities
2. Address {{lint_p0}} P0 lint issues
3. Add {{db_critical_indexes}} critical indexes

### P1 (High) - Sprint 2
1. Refactor {{perf_top_hotspots}} performance hotspots
2. Clean up {{lint_p1}} high-priority issues
3. VACUUM {{db_bloated_tables}} bloated tables

### P2 (Medium) - Sprint 3+
1. Code cleanup and tech debt
2. Performance optimizations
3. Documentation updates
```

---

## 🔧 Configuration Examples

### Developer Agent Configuration
```bash
# .env.developer
AGENT_ROLE="developer"
CI_AGENTS="lintguard,perfsmith"
CI_THRESHOLD_CRITICAL=0
CI_THRESHOLD_HIGH=5
RUN_CI_ON_SAVE=true
```

### Review/Validation Agent Configuration
```bash
# .env.review
AGENT_ROLE="review-validation"
CI_AGENTS="lintguard,shieldprobe,schemasage,perfsmith,atlasreporter"
CI_THRESHOLD_CRITICAL=0
CI_THRESHOLD_HIGH=0
REQUIRE_ALL_PASS=true
```

---

## 📋 Integration Checklists

### Pre-Development Checklist (Initializer Agent)
- [ ] Run SchemaSage to capture baseline DB state
- [ ] Run AtlasReporter to document starting point
- [ ] Define success criteria based on CI metrics
- [ ] Document rollback strategy

### Development Checklist (Developer/Execution Agent)
- [ ] Run LintGuard after significant changes
- [ ] Run PerfSmith if modifying hot paths
- [ ] Run ShieldProbe if touching auth/security
- [ ] Update change_record.md with CI findings

### Pre-Commit Checklist (Review/Validation Agent)
- [ ] Run full CI suite (all agents)
- [ ] Review AtlasReporter digest
- [ ] Verify 0 critical issues
- [ ] Confirm <10 total issues
- [ ] Check security risk level = "low"
- [ ] Validate DB changes (if applicable)

### Pre-Merge Checklist (Merger Agent)
- [ ] Run full CI suite on merge target
- [ ] Run full CI suite on feature branch
- [ ] Run full CI suite on merged result
- [ ] Review AtlasReporter for regressions
- [ ] Verify all checks pass

---

## 🎓 Best Practices

### 1. **Continuous Feedback Loop**
```
Developer writes code
    ↓
Run LintGuard (8s feedback)
    ↓
Fix issues immediately
    ↓
Run PerfSmith before commit (15s)
    ↓
Optimize if needed
    ↓
Full validation before push (45s)
```

### 2. **Layered Validation**
- **Local (Developer)**: LintGuard + PerfSmith (quick feedback)
- **Pre-commit (Review)**: + ShieldProbe (comprehensive)
- **Pre-merge (Merger)**: + SchemaSage + AtlasReporter (complete)

### 3. **Threshold Management**
```python
# Progressive thresholds
THRESHOLDS = {
    'developer': {
        'critical': 0,
        'high': 10,    # Lenient during development
        'total': 50
    },
    'review': {
        'critical': 0,
        'high': 5,     # Stricter before commit
        'total': 20
    },
    'merge': {
        'critical': 0,
        'high': 0,     # Strictest before merge
        'total': 10
    }
}
```

---

## 🚨 Common Pitfalls

### ❌ Don't: Run all CI agents on every file save
**Why:** Slow feedback loop, disrupts flow
**Do:** Run LintGuard only, full suite on commit

### ❌ Don't: Ignore CI warnings during development
**Why:** Issues compound, harder to fix later
**Do:** Fix issues immediately while context is fresh

### ❌ Don't: Run CI agents without clear decision criteria
**Why:** Unclear what to do with results
**Do:** Define thresholds and actions upfront

### ❌ Don't: Skip CI validation because "it's a small change"
**Why:** Small changes can have big impacts
**Do:** Run at least LintGuard + ShieldProbe on all changes

---

## 📊 Success Metrics

Track these metrics to measure integration effectiveness:

| Metric | Target | How CI Agents Help |
|--------|--------|-------------------|
| Bugs found in production | <5/month | ShieldProbe + LintGuard catch issues early |
| Code review time | <2 hours | AtlasReporter provides pre-review summary |
| Deployment failures | <2% | Review/Validation Agent enforces quality gates |
| Security incidents | 0 | ShieldProbe scans all commits |
| Performance regressions | <1/quarter | PerfSmith tracks hotspots and complexity |
| Database incidents | <1/quarter | SchemaSage validates migrations and indexes |

---

## 🔗 Quick Reference Commands

### Developer Agent Daily Workflow
```bash
# Morning: Check current state
./ci_workflows/agent_atlasreporter.sh

# During development: Quick checks
./ci_workflows/agent_lintguard.sh

# Before commit: Full validation
./run_agents_locally.sh --parallel
```

### Code Reviewer Agent PR Review
```bash
# Generate comprehensive review report
./run_agents_locally.sh --parallel
cat reports/weekly_agent_digest.md
```

### Review/Validation Agent Gate Check
```bash
# Full validation with decision
./run_agents_locally.sh --parallel
python3 scripts/validate_and_decide.py reports/
```

---

**Version:** 1.0  
**Last Updated:** December 2024  
**Purpose:** Maximize value from CI Agents through proper Agent Persona integration

---

## 📖 Related Documentation

### Agent Personas
- [AGENT_PERSONAS_README.md](.promptx/personas/AGENT_PERSONAS_README.md) - Complete overview of all 8 personas
- [AGENT_HANDOFF_PROTOCOL.md](.promptx/personas/AGENT_HANDOFF_PROTOCOL.md) - Standard collaboration workflow

### CI Agents
- [AGENTS_README.md](AGENTS_README.md) - CI Agents quick start guide
- [AGENT_OPTIMIZATION_GUIDE.md](AGENT_OPTIMIZATION_GUIDE.md) - Detailed optimization documentation
- [AGENT_COMPARISON.md](AGENT_COMPARISON.md) - Before/after comparison
- [WHERE_AGENTS_RUN.md](WHERE_AGENTS_RUN.md) - Execution context guide

### Helper Files
- [HELPER_OPTIMIZATION_GUIDE.md](HELPER_OPTIMIZATION_GUIDE.md) - PerfSmith & SchemaSage helpers
- [optimized_perfsmith_hotspots.py](ci_workflows/helpers/perfsmith_hotspots.py)
- [optimized_schemasage_explain.sql](ci_workflows/helpers/schemasage_explain.sql)

### Workflow
- [WORKFLOW_COMPARISON.md](WORKFLOW_COMPARISON.md) - GitHub Actions workflow comparison
- [MACOS_OPTIMIZATION_GUIDE.md](MACOS_OPTIMIZATION_GUIDE.md) - macOS-specific optimizations
- [run_agents_locally.sh](run_agents_locally.sh) - Local execution script

### Complete Package
- [COMPLETE_PACKAGE_SUMMARY.md](COMPLETE_PACKAGE_SUMMARY.md) - Overview of all deliverables

---

## 💡 Quick Tips

1. **Start with one persona** - Master Developer + LintGuard integration first
2. **Read the persona file** - Understand the role before integrating CI agents
3. **Use the templates** - Copy/paste the code examples and checklists
4. **Iterate gradually** - Add CI integrations one at a time
5. **Measure results** - Track the success metrics to validate improvements

---

**Have questions?** Review the relevant persona documentation and CI agent guides listed above.
