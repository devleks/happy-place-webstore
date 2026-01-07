# 15 - Technical Debt Management Workflow

Systematic approach to identifying, tracking, prioritizing, and reducing technical debt to maintain codebase health and development velocity.

---

## Overview

This workflow provides a structured methodology for managing technical debt as a first-class concern, balancing debt reduction with feature development.

## When to Use

- Codebase feeling "heavy" or slow to develop
- Increasing bug rates or regressions
- Onboarding new developers takes too long
- Performance degradation over time
- Security vulnerabilities accumulating
- Sprint planning / capacity allocation

---

## Quick Start

```bash
./blackbox.sh start "debt-[category]-[scope]"
```

---

## Cascade Prompt

```
Execute Technical Debt Management workflow for: [SCOPE]

Focus area: [code/architecture/testing/dependencies/documentation]
Time budget: [X hours/sprint]
Priority: [critical/high/medium/low]

Steps:
1. Identify and catalog debt
2. Assess impact and cost
3. Prioritize by value
4. Plan remediation
5. Execute incrementally
6. Track and report

Reference: workflows/tier-2/15-technical-debt-management.md
Session: [CURRENT-SESSION-ID]
```

---

## Technical Debt Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    TECHNICAL DEBT TAXONOMY                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CODE DEBT                                                      │
│  ├── Duplicated code                                            │
│  ├── Complex/unmaintainable functions                           │
│  ├── Missing error handling                                     │
│  ├── Poor naming/structure                                      │
│  ├── Dead code                                                  │
│  └── Outdated patterns                                          │
│                                                                 │
│  ARCHITECTURE DEBT                                              │
│  ├── Tight coupling                                             │
│  ├── Missing abstractions                                       │
│  ├── Scalability limitations                                    │
│  ├── Monolith needing decomposition                             │
│  └── Wrong technology choices                                   │
│                                                                 │
│  TESTING DEBT                                                   │
│  ├── Low test coverage                                          │
│  ├── Flaky tests                                                │
│  ├── Missing integration tests                                  │
│  ├── No E2E tests                                               │
│  └── Slow test suite                                            │
│                                                                 │
│  DEPENDENCY DEBT                                                │
│  ├── Outdated packages                                          │
│  ├── Security vulnerabilities                                   │
│  ├── Deprecated APIs                                            │
│  ├── Version conflicts                                          │
│  └── Abandoned dependencies                                     │
│                                                                 │
│  DOCUMENTATION DEBT                                             │
│  ├── Missing/outdated docs                                      │
│  ├── Undocumented APIs                                          │
│  ├── No architecture docs                                       │
│  ├── Missing runbooks                                           │
│  └── Stale comments                                             │
│                                                                 │
│  INFRASTRUCTURE DEBT                                            │
│  ├── Manual deployments                                         │
│  ├── Missing monitoring                                         │
│  ├── No disaster recovery                                       │
│  ├── Hardcoded configs                                          │
│  └── Insecure configurations                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Debt Identification

### Automated Detection

```bash
#!/bin/bash
# debt-scanner.sh

echo "🔍 Technical Debt Scanner"
echo "========================="

# Code complexity
echo ""
echo "📊 Code Complexity (Top 10 complex files):"
npx complexity-report src/**/*.ts 2>/dev/null | head -20

# Duplicated code
echo ""
echo "📋 Code Duplication:"
npx jscpd src/ --min-lines 10 --min-tokens 50 2>/dev/null | tail -10

# TODO/FIXME comments
echo ""
echo "📝 TODO/FIXME Comments:"
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ | wc -l
echo "   Total found. Top items:"
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ | head -10

# Outdated dependencies
echo ""
echo "📦 Outdated Dependencies:"
npm outdated 2>/dev/null | head -20

# Security vulnerabilities
echo ""
echo "🔒 Security Vulnerabilities:"
npm audit --json 2>/dev/null | jq '.metadata.vulnerabilities'

# Test coverage
echo ""
echo "🧪 Test Coverage:"
npm run test:coverage 2>/dev/null | grep -E "Statements|Branches|Functions|Lines"

# ESLint issues
echo ""
echo "⚠️ Linting Issues:"
npx eslint src/ --format compact 2>/dev/null | wc -l
echo "   Total issues found"
```

### Code Quality Metrics

```javascript
// debt-metrics.js
const fs = require('fs');
const path = require('path');

function analyzeFile(filepath) {
    const content = fs.readFileSync(filepath, 'utf-8');
    const lines = content.split('\n');
    
    return {
        file: filepath,
        lines: lines.length,
        todos: (content.match(/TODO|FIXME|HACK|XXX/g) || []).length,
        longFunctions: countLongFunctions(content),
        complexity: estimateComplexity(content),
        duplicateBlocks: 0, // Would need jscpd integration
    };
}

function countLongFunctions(content) {
    // Simplified: count functions > 50 lines
    const functionMatches = content.match(/function.*\{[\s\S]*?\n\}/g) || [];
    return functionMatches.filter(f => f.split('\n').length > 50).length;
}

function estimateComplexity(content) {
    // Count decision points
    const decisions = (content.match(/if|else|switch|case|for|while|\?\./g) || []).length;
    return Math.min(decisions / 10, 10); // Normalize to 0-10
}

// Generate report
const files = getAllFiles('src/', '.ts');
const metrics = files.map(analyzeFile);
const summary = {
    totalFiles: metrics.length,
    totalLines: metrics.reduce((a, m) => a + m.lines, 0),
    totalTodos: metrics.reduce((a, m) => a + m.todos, 0),
    avgComplexity: metrics.reduce((a, m) => a + m.complexity, 0) / metrics.length,
    highComplexityFiles: metrics.filter(m => m.complexity > 7).length,
};

console.log('Technical Debt Summary:', summary);
```

### Manual Identification Template

```markdown
## Technical Debt Register

### TD-001: [Title]
| Field | Value |
|-------|-------|
| **Category** | Code/Architecture/Testing/Dependencies/Docs/Infra |
| **Location** | `src/services/user.ts` |
| **Severity** | Critical/High/Medium/Low |
| **Age** | [When introduced or discovered] |
| **Reporter** | [Who identified it] |

**Description:**
[Detailed description of the debt]

**Impact:**
- Development velocity: [High/Medium/Low]
- Bug risk: [High/Medium/Low]
- Security risk: [High/Medium/Low]
- Performance: [High/Medium/Low]

**Root Cause:**
[Why this debt exists - rushed timeline, legacy code, etc.]

**Proposed Solution:**
[How to fix it]

**Estimated Effort:**
[Story points or hours]

**Dependencies:**
[Other debt items or features this depends on]
```

---

## Phase 2: Impact Assessment

### Cost of Delay Matrix

| Debt Item | Dev Velocity Impact | Bug Risk | Security Risk | Customer Impact | Total Score |
|-----------|--------------------:|----------:|--------------:|----------------:|------------:|
| TD-001 | 3 | 2 | 1 | 2 | 8 |
| TD-002 | 1 | 3 | 3 | 3 | 10 |
| TD-003 | 2 | 1 | 0 | 1 | 4 |

*Score: 0 (none) to 3 (severe)*

### Interest Rate Calculation

```markdown
## Technical Debt Interest

"Interest" = ongoing cost of NOT fixing the debt

### High Interest Debt (Fix ASAP)
- Causes multiple bugs per sprint
- Blocks other work regularly
- Security vulnerabilities
- Growing exponentially

### Medium Interest Debt (Plan to Fix)
- Slows down related features
- Occasional bugs
- Makes onboarding harder
- Linear growth

### Low Interest Debt (Track but Defer)
- Cosmetic issues
- Rarely touched code
- Minimal impact
- Stable/not growing
```

---

## Phase 3: Prioritization

### Prioritization Framework

```
Priority Score = (Impact × Frequency) / Effort

Where:
- Impact: 1-5 (how much it hurts when encountered)
- Frequency: 1-5 (how often it's encountered)
- Effort: 1-5 (story points or days to fix)
```

### Priority Matrix

```
                    EFFORT
                Low    Medium    High
           ┌─────────┬─────────┬─────────┐
     High  │  DO NOW │  PLAN   │ CONSIDER│
           ├─────────┼─────────┼─────────┤
I  Medium  │  PLAN   │CONSIDER │  DEFER  │
M          ├─────────┼─────────┼─────────┤
P    Low   │CONSIDER │  DEFER  │  IGNORE │
A          └─────────┴─────────┴─────────┘
C
T
```

### Sprint Allocation

```markdown
## Recommended Debt Budget

### Sustainable Pace
- **20% of sprint capacity** for tech debt
- 1 sprint per quarter dedicated to debt reduction
- Every PR should leave code better than found

### Debt Emergency Mode
- **40% of capacity** until crisis resolved
- Pause non-critical features
- Focus on highest-interest debt

### Debt Paydown Strategies

1. **Boy Scout Rule**
   - Every change improves something
   - Small, continuous improvements

2. **Dedicated Stories**
   - Explicit debt reduction tickets
   - Sized and prioritized like features

3. **Refactoring Sprints**
   - Periodic dedicated effort
   - Major architectural changes

4. **Strangler Pattern**
   - Replace incrementally
   - New code follows new patterns
```

---

## Phase 4: Remediation

### Remediation Strategies by Type

#### Code Debt

```typescript
// Before: Complex, nested function
function processOrder(order: Order) {
    if (order.items.length > 0) {
        for (const item of order.items) {
            if (item.inStock) {
                if (item.quantity > 0) {
                    // ... 50 more lines
                }
            }
        }
    }
}

// After: Extracted, readable functions
function processOrder(order: Order) {
    if (!hasItems(order)) return;
    
    const availableItems = order.items.filter(isAvailable);
    return availableItems.map(processItem);
}

function isAvailable(item: Item): boolean {
    return item.inStock && item.quantity > 0;
}

function processItem(item: Item): ProcessedItem {
    // focused logic
}
```

#### Architecture Debt

```markdown
## Strangler Fig Pattern

1. **Identify boundary**
   - Find seams in the existing code
   - Define interface for new implementation

2. **Build alongside**
   - Create new implementation
   - Route traffic gradually

3. **Migrate incrementally**
   - Move endpoints/features one at a time
   - Verify each migration

4. **Remove old code**
   - Once fully migrated, delete legacy
   - Clean up routing
```

#### Testing Debt

```bash
# Identify untested code
npx jest --coverage --coverageReporters=text | grep -E "^[^|]*\|.*\s[0-7][0-9]\s"

# Prioritize testing:
# 1. Critical paths (auth, payments)
# 2. High-change areas
# 3. Bug-prone modules
# 4. Complex logic
```

#### Dependency Debt

```bash
# Update strategy
npm outdated

# Check for breaking changes
npx npm-check-updates -u

# Update one major version at a time
npm install package@next-major

# Run tests after each update
npm test

# Document breaking changes in CHANGELOG
```

---

## Phase 5: Tracking

### Debt Dashboard

```markdown
## Technical Debt Dashboard

### Summary (Last Updated: YYYY-MM-DD)

| Metric | Current | Target | Trend |
|--------|---------|--------|-------|
| Total Items | 45 | < 30 | ↘️ |
| Critical | 3 | 0 | ↘️ |
| High | 12 | < 5 | ↘️ |
| Debt Ratio | 18% | < 10% | ↘️ |
| Test Coverage | 72% | > 80% | ↗️ |
| Vuln Count | 5 | 0 | ↘️ |

### By Category
| Category | Count | Trend |
|----------|-------|-------|
| Code | 20 | ↘️ |
| Testing | 10 | ↘️ |
| Dependencies | 8 | → |
| Documentation | 5 | ↘️ |
| Architecture | 2 | → |

### Sprint Progress
- Started with: 48 items
- Closed: 5 items  
- Added: 2 items
- Net reduction: 3 items

### Top 5 to Address
1. [TD-015] Auth service refactor - Critical
2. [TD-023] Update React to v18 - High
3. [TD-007] Add payment tests - High
4. [TD-031] Fix N+1 queries - High
5. [TD-012] Update API docs - Medium
```

### Debt Backlog Template

```yaml
# debt-backlog.yaml
items:
  - id: TD-001
    title: Refactor authentication service
    category: architecture
    severity: critical
    effort: 13  # story points
    interest: high  # growing cost
    location: src/services/auth/
    description: |
      Auth service has grown to 2000 lines with multiple responsibilities.
      Needs decomposition into separate services.
    impact:
      velocity: high
      bugs: medium
      security: high
    created: 2024-01-15
    updated: 2024-12-17
    status: in_progress
    assignee: "@developer"
    
  - id: TD-002
    title: Increase test coverage for payments
    category: testing
    severity: high
    effort: 8
    interest: medium
    location: src/services/payments/
    description: |
      Payment processing has only 45% test coverage.
      Critical path needs 90%+.
    impact:
      velocity: low
      bugs: high
      security: medium
    created: 2024-03-01
    status: backlog
```

---

## Phase 6: Reporting

### Sprint Report Template

```markdown
## Tech Debt Sprint Report

**Sprint:** [Number]
**Date:** [Range]
**Session:** [CONV-ID]

### Capacity Allocation
- Total capacity: 100 points
- Feature work: 80 points (80%)
- Debt work: 20 points (20%)

### Debt Work Completed
| ID | Title | Points | Category |
|----|-------|--------|----------|
| TD-015 | Auth refactor phase 1 | 8 | Architecture |
| TD-023 | React 18 upgrade | 5 | Dependencies |
| TD-032 | Remove dead code | 3 | Code |
| TD-041 | Fix flaky tests | 4 | Testing |

### Debt Added
| ID | Title | Source |
|----|-------|--------|
| TD-045 | New API needs tests | Feature work |
| TD-046 | Config refactoring | Discovery |

### Net Change
- Closed: 4 items (20 points)
- Added: 2 items (8 points)
- Net: -2 items (-12 points) ✅

### Quality Metrics
| Metric | Start | End | Change |
|--------|-------|-----|--------|
| Test Coverage | 72% | 75% | +3% ✅ |
| Vulnerabilities | 5 | 3 | -2 ✅ |
| Lint Errors | 234 | 201 | -33 ✅ |

### Next Sprint Focus
1. Complete auth refactor (TD-015 phase 2)
2. Address remaining vulnerabilities
3. Documentation updates
```

---

## Black Box Integration

```bash
# Start debt session
./blackbox.sh start "debt-code-auth-refactor"

# Log identification
./blackbox.sh action "Scanned for code debt" "Found 45 items"
./blackbox.sh decision "Prioritize auth refactor" "Highest interest debt"

# Log remediation
./blackbox.sh action "Refactored auth service" "Split into 3 modules"
./blackbox.sh milestone "Auth refactor phase 1 complete"

# Log results
./blackbox.sh action "Verified tests passing" "Coverage increased 3%"

# End session
./blackbox.sh end "Reduced debt by 12 points"
```

---

## Quick Reference

| Task | Command/Tool |
|------|--------------|
| Scan complexity | `npx complexity-report src/` |
| Find duplicates | `npx jscpd src/` |
| Check dependencies | `npm outdated` |
| Security audit | `npm audit` |
| Coverage report | `npm run test:coverage` |
| Lint issues | `npx eslint src/ --format compact` |

---

*Technical Debt Management Workflow v1.0*
*Integrates with Black Box for tracking*
