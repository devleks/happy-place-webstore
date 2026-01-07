# 16 - Feature Flag Management Workflow

Systematic approach to implementing, managing, and retiring feature flags for controlled rollouts, A/B testing, and operational toggles.

---

## Overview

This workflow provides best practices for using feature flags to reduce deployment risk, enable progressive rollouts, and separate deployment from release.

## When to Use

- Releasing new features incrementally
- A/B testing and experimentation
- Kill switches for risky features
- User segmentation (beta users, enterprise)
- Operational toggles (maintenance mode)
- Trunk-based development enablement

---

## Quick Start

```bash
./blackbox.sh start "flag-[feature]-[purpose]"
```

---

## Cascade Prompt

```
Execute Feature Flag Management workflow for: [FEATURE]

Flag type: [release/experiment/ops/permission]
Rollout strategy: [percentage/user-segment/all]
Duration: [temporary/permanent]

Steps:
1. Define flag requirements
2. Implement flag
3. Configure rollout
4. Monitor and iterate
5. Clean up when complete

Reference: workflows/tier-2/16-feature-flag-management.md
Session: [CURRENT-SESSION-ID]
```

---

## Feature Flag Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE FLAG TAXONOMY                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RELEASE FLAGS (Temporary)                                      │
│  ├── Purpose: Hide incomplete features                          │
│  ├── Lifespan: Days to weeks                                    │
│  ├── Default: OFF                                               │
│  └── Remove: After full rollout                                 │
│                                                                 │
│  EXPERIMENT FLAGS (Temporary)                                   │
│  ├── Purpose: A/B testing                                       │
│  ├── Lifespan: Weeks to months                                  │
│  ├── Default: Control variant                                   │
│  └── Remove: After experiment concludes                         │
│                                                                 │
│  OPS FLAGS (Semi-permanent)                                     │
│  ├── Purpose: Operational control                               │
│  ├── Lifespan: Long-term                                        │
│  ├── Default: Varies                                            │
│  └── Examples: Maintenance mode, rate limits                    │
│                                                                 │
│  PERMISSION FLAGS (Permanent)                                   │
│  ├── Purpose: User/tenant segmentation                          │
│  ├── Lifespan: Permanent                                        │
│  ├── Default: OFF                                               │
│  └── Examples: Premium features, beta access                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Flag Design

### Naming Convention

```
[scope]_[feature]_[purpose]

Examples:
- release_new_checkout_flow
- experiment_pricing_page_v2
- ops_maintenance_mode
- permission_advanced_analytics
- kill_external_api_calls
```

### Flag Specification Template

```yaml
# flags/release_new_checkout_flow.yaml
name: release_new_checkout_flow
description: "New streamlined checkout experience"
type: release
owner: "@checkout-team"

created: 2024-12-17
expected_removal: 2025-01-15
session: CONV-2024-12-17-001

default_value: false

targeting:
  rules:
    - name: "Internal testing"
      conditions:
        - attribute: email
          operator: ends_with
          value: "@company.com"
      value: true
      
    - name: "Beta users"
      conditions:
        - attribute: user.beta
          operator: equals
          value: true
      value: true
      
    - name: "Percentage rollout"
      conditions:
        - attribute: user.id
          operator: percentage
          value: 10  # 10% of users
      value: true

fallback: false

metrics:
  - checkout_completion_rate
  - checkout_time_seconds
  - checkout_errors

alerts:
  - condition: "error_rate > 5%"
    action: "auto_disable"
  - condition: "latency_p99 > 2000ms"
    action: "notify"
```

---

## Phase 2: Implementation

### SDK Integration

```typescript
// feature-flags.ts
import { LaunchDarkly } from 'launchdarkly-node-server-sdk';

// Initialize client
const ldClient = LaunchDarkly.init(process.env.LAUNCHDARKLY_SDK_KEY);

// Type-safe flag definitions
interface FeatureFlags {
  release_new_checkout_flow: boolean;
  experiment_pricing_page_v2: 'control' | 'variant_a' | 'variant_b';
  ops_maintenance_mode: boolean;
  permission_advanced_analytics: boolean;
}

// Flag evaluation helper
async function getFlag<K extends keyof FeatureFlags>(
  flagKey: K,
  user: LDUser,
  defaultValue: FeatureFlags[K]
): Promise<FeatureFlags[K]> {
  await ldClient.waitForInitialization();
  return ldClient.variation(flagKey, user, defaultValue);
}

// Usage in application
async function checkoutHandler(req: Request, res: Response) {
  const user = {
    key: req.user.id,
    email: req.user.email,
    custom: {
      plan: req.user.plan,
      beta: req.user.isBeta,
    },
  };

  const useNewCheckout = await getFlag(
    'release_new_checkout_flow',
    user,
    false
  );

  if (useNewCheckout) {
    return newCheckoutFlow(req, res);
  } else {
    return legacyCheckoutFlow(req, res);
  }
}
```

### React Hook Implementation

```typescript
// useFeatureFlag.ts
import { useFlags, useLDClient } from 'launchdarkly-react-client-sdk';

export function useFeatureFlag<T>(
  flagKey: string,
  defaultValue: T
): { value: T; loading: boolean } {
  const flags = useFlags();
  const client = useLDClient();
  
  const loading = !client?.initialized;
  const value = flags[flagKey] ?? defaultValue;
  
  return { value, loading };
}

// Usage in component
function CheckoutPage() {
  const { value: useNewCheckout, loading } = useFeatureFlag(
    'release_new_checkout_flow',
    false
  );

  if (loading) return <LoadingSpinner />;

  return useNewCheckout ? <NewCheckout /> : <LegacyCheckout />;
}
```

### Server-Side Rendering

```typescript
// pages/checkout.tsx (Next.js)
import { getServerSideProps } from 'next';

export const getServerSideProps: GetServerSideProps = async (context) => {
  const user = await getUser(context.req);
  
  const flags = await evaluateFlags(user, [
    'release_new_checkout_flow',
    'experiment_pricing_page_v2',
  ]);

  return {
    props: {
      flags,
      user,
    },
  };
};

export default function CheckoutPage({ flags }) {
  // Use pre-evaluated flags - no loading state needed
  return flags.release_new_checkout_flow 
    ? <NewCheckout /> 
    : <LegacyCheckout />;
}
```

---

## Phase 3: Rollout Strategy

### Progressive Rollout Plan

```markdown
## Rollout Plan: New Checkout Flow

### Phase 1: Internal (Day 1-3)
- Target: Internal employees only
- Goal: Catch obvious bugs
- Success: No P0/P1 issues

### Phase 2: Beta (Day 4-7)
- Target: Opt-in beta users (500 users)
- Goal: Gather feedback, measure metrics
- Success: NPS > 40, completion rate stable

### Phase 3: Canary (Day 8-14)
- Target: 5% of all users
- Goal: Validate at scale
- Success: No degradation in key metrics

### Phase 4: Gradual Rollout (Day 15-28)
- 5% → 10% → 25% → 50% → 75% → 100%
- Each increase after 48h stability
- Rollback trigger: Error rate > 2%

### Phase 5: Cleanup (Day 29-35)
- Remove flag from code
- Delete flag from system
- Update documentation
```

### Rollout Automation

```typescript
// rollout-automation.ts
interface RolloutStage {
  percentage: number;
  durationHours: number;
  successCriteria: {
    errorRateMax: number;
    latencyP99Max: number;
    conversionDropMax: number;
  };
}

const rolloutPlan: RolloutStage[] = [
  { percentage: 5, durationHours: 48, successCriteria: { errorRateMax: 0.02, latencyP99Max: 2000, conversionDropMax: 0.05 } },
  { percentage: 10, durationHours: 48, successCriteria: { errorRateMax: 0.02, latencyP99Max: 2000, conversionDropMax: 0.05 } },
  { percentage: 25, durationHours: 48, successCriteria: { errorRateMax: 0.02, latencyP99Max: 2000, conversionDropMax: 0.05 } },
  { percentage: 50, durationHours: 48, successCriteria: { errorRateMax: 0.02, latencyP99Max: 2000, conversionDropMax: 0.05 } },
  { percentage: 100, durationHours: 0, successCriteria: { errorRateMax: 0.02, latencyP99Max: 2000, conversionDropMax: 0.05 } },
];

async function checkRolloutHealth(flagKey: string): Promise<boolean> {
  const metrics = await getMetrics(flagKey, '1h');
  const currentStage = await getCurrentStage(flagKey);
  
  return (
    metrics.errorRate <= currentStage.successCriteria.errorRateMax &&
    metrics.latencyP99 <= currentStage.successCriteria.latencyP99Max &&
    metrics.conversionDrop <= currentStage.successCriteria.conversionDropMax
  );
}

async function advanceRollout(flagKey: string) {
  if (await checkRolloutHealth(flagKey)) {
    await incrementRolloutPercentage(flagKey);
    console.log(`✅ Advanced ${flagKey} to next stage`);
  } else {
    await rollback(flagKey);
    console.log(`❌ Rolled back ${flagKey} due to health check failure`);
  }
}
```

---

## Phase 4: Monitoring

### Flag Dashboard

```markdown
## Feature Flag Dashboard

### Active Flags (12)

| Flag | Type | Rollout | Health | Owner | Age |
|------|------|---------|--------|-------|-----|
| release_new_checkout | Release | 25% | 🟢 | @team | 5d |
| experiment_pricing_v2 | Experiment | 50% | 🟢 | @growth | 14d |
| ops_rate_limit_strict | Ops | 100% | 🟢 | @platform | 30d |
| release_old_feature | Release | 100% | ⚠️ Stale | @team | 90d |

### Flag Health Metrics

#### release_new_checkout_flow
| Metric | Control | Treatment | Diff |
|--------|---------|-----------|------|
| Error Rate | 0.5% | 0.4% | -20% ✅ |
| Latency p99 | 1200ms | 1100ms | -8% ✅ |
| Conversion | 3.2% | 3.5% | +9% ✅ |

### Stale Flags (Action Required)
| Flag | Age | Status | Action |
|------|-----|--------|--------|
| release_old_feature | 90d | 100% | Remove from code |
| experiment_completed | 45d | Concluded | Clean up |
```

### Alerting Rules

```yaml
# flag-alerts.yaml
alerts:
  - name: flag_error_spike
    condition: |
      flag.variant.error_rate > 
      flag.control.error_rate * 1.5
    action: notify_and_consider_rollback
    channels: [slack, pagerduty]

  - name: flag_stale
    condition: |
      flag.type == 'release' AND
      flag.rollout == 100% AND
      flag.age > 30 days
    action: create_cleanup_ticket
    channels: [jira]

  - name: too_many_flags
    condition: |
      count(flags.active) > 50
    action: notify
    message: "Consider cleaning up old flags"
```

---

## Phase 5: Cleanup

### Flag Removal Checklist

```markdown
## Flag Removal Checklist: [FLAG_NAME]

### Pre-Removal
- [ ] Flag at 100% rollout for 2+ weeks
- [ ] No rollbacks in past 2 weeks
- [ ] Metrics confirmed positive/neutral
- [ ] Stakeholder sign-off

### Code Removal
- [ ] Remove flag evaluation calls
- [ ] Remove conditional branches
- [ ] Remove flag-specific tests
- [ ] Remove flag configuration
- [ ] Update documentation

### Post-Removal
- [ ] Deploy changes
- [ ] Delete flag from flag service
- [ ] Remove from monitoring
- [ ] Close related tickets
- [ ] Update flag registry
```

### Automated Cleanup Detection

```typescript
// stale-flag-detector.ts
async function detectStaleFlags(): Promise<StaleFlag[]> {
  const allFlags = await getAllFlags();
  const staleFlags: StaleFlag[] = [];

  for (const flag of allFlags) {
    const isStale = 
      flag.type === 'release' &&
      flag.rolloutPercentage === 100 &&
      daysSince(flag.lastModified) > 30;

    if (isStale) {
      staleFlags.push({
        ...flag,
        recommendation: 'Remove from codebase',
        codeReferences: await findCodeReferences(flag.key),
      });
    }
  }

  return staleFlags;
}

// Run weekly and create tickets
async function weeklyCleanupReport() {
  const staleFlags = await detectStaleFlags();
  
  for (const flag of staleFlags) {
    await createJiraTicket({
      title: `Clean up stale flag: ${flag.key}`,
      description: `Flag has been at 100% for ${flag.age} days`,
      labels: ['tech-debt', 'feature-flags'],
      assignee: flag.owner,
    });
  }
}
```

---

## Best Practices

### Do's ✅

```markdown
- Use consistent naming conventions
- Set expected removal dates for temporary flags
- Monitor flag performance separately from control
- Document flag purpose and success criteria
- Remove flags promptly after rollout
- Use kill switches for risky features
- Test both flag states in CI/CD
```

### Don'ts ❌

```markdown
- Don't nest flags (flag inside flag)
- Don't use flags for permanent configuration
- Don't leave stale flags in codebase
- Don't skip flag cleanup
- Don't have more than 50 active flags
- Don't deploy flag changes during incidents
```

---

## Black Box Integration

```bash
# Start flag session
./blackbox.sh start "flag-new-checkout-rollout"

# Log creation
./blackbox.sh action "Created feature flag" "release_new_checkout_flow"
./blackbox.sh decision "Phased rollout strategy" "Minimize risk"

# Log rollout progress
./blackbox.sh action "Increased rollout to 10%" "Metrics healthy"
./blackbox.sh checkpoint "Before 50% rollout"
./blackbox.sh action "Increased rollout to 50%" "Metrics healthy"

# Log completion
./blackbox.sh milestone "100% rollout achieved"
./blackbox.sh action "Removed flag from codebase" "Cleanup complete"

# End session
./blackbox.sh end "Flag lifecycle complete"
```

---

## Quick Reference

| Task | Action |
|------|--------|
| Create flag | Define in flag service + code wrapper |
| Start rollout | Set targeting rules, begin at 5% |
| Monitor | Check error rates, latency, conversions |
| Increase rollout | After 48h stability, increase % |
| Rollback | Set to 0% or disable flag |
| Clean up | Remove code, delete flag |

---

*Feature Flag Management Workflow v1.0*
*Integrates with Black Box for tracking*
