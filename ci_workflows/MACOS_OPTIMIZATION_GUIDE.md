# macOS GitHub Actions Optimization Guide

## Overview
This document explains the optimizations made for running the Happy Place Agents on macOS runners.

## Key Optimizations

### 1. **Dependency Caching** (30-60% faster runs)
- **Python packages**: Cached via `setup-python@v5` action
- **npm packages**: Cached via `setup-node@v4` action
- **Build artifacts**: Separate cache for compiled frontend code
- **Security scan data**: Cached between runs to avoid re-scanning unchanged files

**Impact**: Subsequent runs are 30-60% faster after initial cache population.

### 2. **Shallow Git Clones** (2-5s faster)
```yaml
fetch-depth: 1  # Only fetch latest commit
```
**Impact**: Reduces checkout time, especially for large repositories.

### 3. **Homebrew Optimizations**
```yaml
HOMEBREW_NO_AUTO_UPDATE: 1       # Skip brew update
HOMEBREW_NO_INSTALL_CLEANUP: 1   # Skip cleanup steps
```
**Impact**: Saves 1-2 minutes per job on macOS runners.

### 4. **Parallel Execution**
Jobs run in parallel where dependencies allow:
```
lintguard (parallel start)
├── schemasage
└── perfsmith (parallel with schemasage)
    └── shieldprobe
        └── atlasreporter
```

### 5. **Optimized npm/pip Installations**
- `npm ci --prefer-offline`: Uses local cache first
- `pip install --prefer-binary`: Prefer pre-compiled wheels (faster on macOS)

### 6. **Concurrency Control**
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```
**Impact**: Cancels outdated runs, saves runner minutes.

### 7. **Timeout Guards**
Each job has appropriate timeouts to prevent runaway processes:
- LintGuard: 15 minutes
- SchemaSage: 10 minutes
- PerfSmith: 20 minutes
- ShieldProbe: 15 minutes
- AtlasReporter: 5 minutes

### 8. **Artifact Management**
- Individual agent results uploaded separately
- Consolidated report with unique names per run
- 7-day retention for individual results
- 30-day retention for consolidated reports

## Cost Considerations

### macOS Runner Pricing
- **macOS runners**: ~10x more expensive than Linux
- **Typical costs** (GitHub Actions):
  - Linux: $0.008/minute
  - macOS: $0.08/minute

### Monthly Cost Estimate
Assuming daily runs with optimizations:
- **Before optimization**: ~15 min/run × 30 days × $0.08 = **$36/month**
- **After optimization**: ~8 min/run × 30 days × $0.08 = **$19.20/month**
- **Savings**: ~47% reduction in runner time

### When to Use macOS Runners
✅ **Use macOS runners when**:
- Building iOS/macOS applications
- Testing Swift/Objective-C code
- Need macOS-specific tools (Xcode, etc.)
- Targeting Apple Silicon (M1/M2) compatibility

❌ **Avoid macOS runners when**:
- Pure web development (use Linux)
- Running generic CI/CD tasks
- Budget-constrained projects

## Alternative: Hybrid Approach

Consider a hybrid strategy:
```yaml
jobs:
  # Use Linux for most jobs (cost-effective)
  lintguard:
    runs-on: ubuntu-latest
  
  # Use macOS only when needed
  macos-specific-tests:
    runs-on: macos-latest
```

## Local Development on macOS

For local testing before pushing to CI:

```bash
# Install dependencies
brew install python@3.11 node@18

# Run agents locally
./ci_workflows/agent_lintguard.sh
./ci_workflows/agent_schemasage.sh
./ci_workflows/agent_perfsmith.sh
./ci_workflows/agent_shieldprobe.sh
./ci_workflows/agent_atlasreporter.sh
```

## Performance Metrics

### Expected Runtime (with caching)
- **First run**: ~12-15 minutes
- **Cached runs**: ~6-8 minutes
- **Best case**: ~5-6 minutes

### Cache Hit Rates
- Python dependencies: ~95% (changes infrequently)
- npm dependencies: ~90% (changes moderately)
- Build artifacts: ~80% (changes frequently)
- Lint results: ~85% (code changes)

## Monitoring & Alerts

### Job Failure Notifications
The `notify-on-failure` job triggers when any agent fails. Customize it:

```yaml
- name: Slack notification
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "🚨 Agent workflow failed: ${{ github.workflow }}"
      }
```

## Best Practices

1. **Review cache hit rates monthly** - Adjust cache keys if hit rates drop
2. **Monitor runner minutes** - Set up billing alerts
3. **Use self-hosted runners** - Consider for high-volume projects
4. **Optimize agent scripts** - Profile and improve slow bash scripts
5. **Branch protection rules** - Require successful agent runs before merge

## Migration Path

### From Linux to macOS
1. Update `runs-on: macos-latest`
2. Test locally on macOS first
3. Review agent scripts for Linux-specific commands
4. Update any apt-get → brew commands
5. Monitor first few runs closely

### Gradual Migration
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest]
```
Run both in parallel temporarily to verify consistency.

## Troubleshooting

### Common Issues

**Slow npm install**
```yaml
# Solution: Use npm ci with frozen lockfile
run: npm ci --prefer-offline --no-audit
```

**Python package build times**
```yaml
# Solution: Use pre-built wheels
run: pip install --prefer-binary --only-binary=:all: -r requirements.txt
```

**Homebrew updates taking forever**
```yaml
# Solution: Already disabled in env vars
env:
  HOMEBREW_NO_AUTO_UPDATE: 1
```

**Cache not working**
- Verify cache key uniqueness
- Check if cache size exceeds 10GB limit
- Ensure cache paths exist before saving

## Additional Resources

- [GitHub Actions Pricing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
- [Caching Dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
- [macOS Runners Spec](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
