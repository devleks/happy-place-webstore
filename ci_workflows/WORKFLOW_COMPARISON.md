# Workflow Comparison: Original vs macOS-Optimized

## Quick Reference

| Feature | Original | macOS-Optimized | Impact |
|---------|----------|-----------------|--------|
| Runner OS | Ubuntu | macOS | +10x cost, +macOS compatibility |
| Dependency Caching | ❌ None | ✅ Python, npm, builds | 30-60% faster |
| Git Clone | Full history | Shallow (depth=1) | 2-5s faster |
| Homebrew Optimization | N/A | Disabled auto-update | 1-2 min faster |
| Concurrency Control | ❌ None | ✅ Cancel in-progress | Saves runner minutes |
| Timeouts | ❌ None | ✅ Per-job limits | Prevents runaway jobs |
| Artifact Strategy | Single upload | Individual + consolidated | Better debugging |
| PR Integration | ❌ None | ✅ Auto-comment | Better visibility |
| Failure Handling | Basic | Notification job | Improved awareness |
| Estimated Runtime | ~12-15 min | ~6-8 min (cached) | ~50% improvement |

## Detailed Differences

### 1. Runner Configuration

**Original:**
```yaml
jobs:
  lintguard:
    runs-on: ubuntu-latest
```

**Optimized:**
```yaml
jobs:
  lintguard:
    runs-on: macos-latest
    timeout-minutes: 15
```

**Changes:**
- macOS runner for native compatibility
- Timeout protection against hanging jobs

### 2. Dependency Management

**Original:**
```yaml
- name: Install frontend dependencies
  run: npm ci
  working-directory: frontend
```

**Optimized:**
```yaml
- name: Setup Node with caching
  uses: actions/setup-node@v4
  with:
    node-version: ${{ env.NODE_VERSION }}
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json

- name: Install frontend dependencies
  run: npm ci --prefer-offline
  working-directory: frontend
```

**Changes:**
- Built-in caching via setup actions
- `--prefer-offline` flag uses cache first
- Centralized version management

### 3. Build Artifact Caching

**Original:**
```yaml
# No caching
```

**Optimized:**
```yaml
- name: Cache build artifacts
  uses: actions/cache@v4
  with:
    path: |
      frontend/dist
      frontend/build
      frontend/.next
    key: perfsmith-build-${{ runner.os }}-${{ hashFiles(...) }}
    restore-keys: |
      perfsmith-build-${{ runner.os }}-
```

**Changes:**
- Caches compiled outputs
- Smart cache key based on dependencies + source
- Fallback keys for partial matches

### 4. Environment Variables

**Original:**
```yaml
# No global env vars
```

**Optimized:**
```yaml
env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "18"
  HOMEBREW_NO_AUTO_UPDATE: 1
  HOMEBREW_NO_INSTALL_CLEANUP: 1
```

**Changes:**
- Centralized version management
- macOS-specific optimizations
- Faster Homebrew operations

### 5. Git Clone Strategy

**Original:**
```yaml
- uses: actions/checkout@v4
```

**Optimized:**
```yaml
- name: Checkout code
  uses: actions/checkout@v4
  with:
    fetch-depth: 1  # Shallow clone
```

**Changes:**
- Only fetches latest commit
- Dramatically faster for large repos

### 6. Concurrency Control

**Original:**
```yaml
# No concurrency control
```

**Optimized:**
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

**Changes:**
- Cancels outdated workflow runs
- Saves runner minutes on rapid pushes
- Prevents queue buildup

### 7. Artifact Management

**Original:**
```yaml
- name: Upload reports artifact
  uses: actions/upload-artifact@v4
  with:
    name: agent-reports
    path: reports
```

**Optimized:**
```yaml
# Per-agent uploads
- name: Upload LintGuard results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: lintguard-results
    path: reports/lintguard*
    retention-days: 7

# Consolidated upload
- name: Upload consolidated reports
  uses: actions/upload-artifact@v4
  with:
    name: agent-reports-${{ github.run_number }}
    path: reports
    retention-days: 30
```

**Changes:**
- Separate artifacts per agent (parallel downloads)
- Unique naming with run number
- Different retention for different artifact types
- `if: always()` ensures upload even on failure

### 8. Pull Request Integration

**Original:**
```yaml
# No PR integration
```

**Optimized:**
```yaml
- name: Post summary to PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      # Auto-post results as PR comment
```

**Changes:**
- Automatic PR comments with results
- Better visibility for reviewers
- No manual checking required

### 9. Trigger Events

**Original:**
```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "0 2 * * *"
```

**Optimized:**
```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "0 2 * * *"
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

**Changes:**
- Runs on push to main/develop
- Runs on pull requests
- Better CI/CD integration

### 10. Failure Handling

**Original:**
```yaml
# No failure handling
```

**Optimized:**
```yaml
notify-on-failure:
  needs: [lintguard, schemasage, perfsmith, shieldprobe, atlasreporter]
  runs-on: macos-latest
  if: failure()
  steps:
    - name: Notify team
      run: echo "Failures detected..."
```

**Changes:**
- Dedicated failure notification job
- Ready for integration with Slack/email
- Centralized alerting

## Migration Checklist

- [ ] Review agent bash scripts for Linux-specific commands
- [ ] Replace `apt-get` with `brew` if present
- [ ] Test locally using `run_agents_locally.sh`
- [ ] Update secrets if needed (DATABASE_URL, SLACK_WEBHOOK, etc.)
- [ ] Set up billing alerts for macOS runner usage
- [ ] Monitor first 3-5 runs closely
- [ ] Verify cache hit rates after 1 week
- [ ] Compare costs after 1 month

## Performance Expectations

### First Run (Cold Cache)
- **Original**: 12-15 minutes
- **Optimized**: 10-12 minutes
- **Improvement**: ~20%

### Subsequent Runs (Warm Cache)
- **Original**: 12-15 minutes (no caching)
- **Optimized**: 6-8 minutes
- **Improvement**: ~50%

### Cost Impact
- **Monthly cost increase**: ~$15-20 (Linux → macOS)
- **Monthly time savings**: ~120 minutes (with daily runs)
- **Break-even**: If developer time worth >$10/hour

## Recommendation

**Use macOS-optimized workflow if:**
- ✅ You need macOS-specific testing
- ✅ You have budget for premium runners
- ✅ Developer time is valuable
- ✅ You want faster feedback loops

**Stick with Linux if:**
- ✅ No macOS-specific requirements
- ✅ Budget-constrained project
- ✅ Willing to wait longer for results
- ✅ Running many workflows (costs add up)

**Consider hybrid approach:**
- Daily scheduled runs on Linux (cost-effective)
- PR runs on macOS (fast feedback when it matters)
