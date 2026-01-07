# 17 - A/B Testing Workflow

Rigorous approach to designing, executing, and analyzing controlled experiments to make data-driven product decisions.

---

## Overview

This workflow ensures statistically valid A/B tests with proper hypothesis formation, sample size calculation, and result interpretation.

## When to Use

- Testing new features or designs
- Optimizing conversion funnels
- Pricing experiments
- Copy and messaging tests
- Algorithm comparisons
- UX/UI improvements

---

## Quick Start

```bash
./blackbox.sh start "experiment-[name]-[hypothesis]"
```

---

## Cascade Prompt

```
Execute A/B Testing workflow for: [EXPERIMENT NAME]

Hypothesis: [What we believe will happen]
Primary metric: [Main success measure]
Expected lift: [X% improvement]
Duration: [Estimated time needed]

Steps:
1. Define hypothesis and metrics
2. Calculate sample size
3. Implement experiment
4. Monitor experiment health
5. Analyze results
6. Document learnings

Reference: workflows/tier-2/17-ab-testing.md
Session: [CURRENT-SESSION-ID]
```

---

## Experiment Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    A/B TEST LIFECYCLE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. HYPOTHESIS        2. DESIGN           3. IMPLEMENT          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Define what  │───▶│ Sample size  │───▶│ Build        │      │
│  │ we're testing│    │ Metrics      │    │ variants     │      │
│  │ and why      │    │ Duration     │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  4. EXECUTE          5. ANALYZE          6. DECIDE             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Run test     │───▶│ Statistical  │───▶│ Ship/Iterate │      │
│  │ Monitor      │    │ analysis     │    │ Document     │      │
│  │ health       │    │              │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Hypothesis Definition

### Hypothesis Template

```markdown
## Experiment: [EXP-XXX] [Name]

### Hypothesis Statement
We believe that [CHANGE] for [USERS]
will result in [OUTCOME]
because [RATIONALE].

### Example
We believe that **simplifying the checkout form from 5 steps to 3**
for **all users completing a purchase**
will result in **10% increase in checkout completion rate**
because **reduced friction leads to higher conversion**.

### Success Metrics

**Primary Metric (OEC - Overall Evaluation Criterion)**
- Metric: Checkout completion rate
- Current: 3.2%
- Target: 3.52% (+10%)
- Minimum detectable effect: 5%

**Secondary Metrics**
| Metric | Current | Watch For |
|--------|---------|-----------|
| Revenue per user | $45 | No decrease |
| Cart abandonment | 68% | Decrease |
| Time to checkout | 180s | Decrease |

**Guardrail Metrics (Must Not Regress)**
| Metric | Current | Threshold |
|--------|---------|-----------|
| Page load time | 1.2s | < 2s |
| Error rate | 0.5% | < 1% |
| Support tickets | 10/day | No increase |
```

---

## Phase 2: Experiment Design

### Sample Size Calculator

```python
# sample_size_calculator.py
import scipy.stats as stats
import math

def calculate_sample_size(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.80,
    two_tailed: bool = True
) -> int:
    """
    Calculate required sample size per variant.
    
    Args:
        baseline_rate: Current conversion rate (e.g., 0.032 for 3.2%)
        minimum_detectable_effect: Relative change to detect (e.g., 0.10 for 10%)
        alpha: Significance level (default 0.05)
        power: Statistical power (default 0.80)
        two_tailed: Whether to use two-tailed test
    
    Returns:
        Sample size needed per variant
    """
    p1 = baseline_rate
    p2 = baseline_rate * (1 + minimum_detectable_effect)
    
    # Pooled proportion
    p_pooled = (p1 + p2) / 2
    
    # Z-scores
    z_alpha = stats.norm.ppf(1 - alpha / (2 if two_tailed else 1))
    z_power = stats.norm.ppf(power)
    
    # Sample size formula
    numerator = (z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                 z_power * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    
    return math.ceil(numerator / denominator)

# Example usage
sample_size = calculate_sample_size(
    baseline_rate=0.032,      # 3.2% conversion
    minimum_detectable_effect=0.10,  # 10% relative lift
    alpha=0.05,               # 95% confidence
    power=0.80                # 80% power
)

print(f"Required sample size per variant: {sample_size:,}")
# Output: Required sample size per variant: 23,849

# Calculate duration
daily_traffic = 5000
variants = 2
days_needed = math.ceil((sample_size * variants) / daily_traffic)
print(f"Estimated duration: {days_needed} days")
```

### Experiment Specification

```yaml
# experiments/exp-001-checkout-simplification.yaml
id: EXP-001
name: Checkout Simplification
status: planning  # planning, running, analyzing, concluded

hypothesis:
  change: "Reduce checkout steps from 5 to 3"
  target_users: "All users completing purchase"
  expected_outcome: "10% increase in completion rate"
  rationale: "Reduced friction improves conversion"

design:
  type: A/B  # A/B, A/B/n, multivariate
  allocation: 50/50
  variants:
    control:
      name: "5-step checkout"
      description: "Current checkout flow"
    treatment:
      name: "3-step checkout"
      description: "Simplified checkout flow"

metrics:
  primary:
    name: checkout_completion_rate
    type: proportion
    baseline: 0.032
    mde: 0.10  # minimum detectable effect
    direction: increase
    
  secondary:
    - name: revenue_per_user
      type: continuous
      direction: no_decrease
    - name: checkout_time_seconds
      type: continuous
      direction: decrease
      
  guardrails:
    - name: error_rate
      threshold: 0.01
    - name: page_load_time
      threshold: 2000

statistics:
  alpha: 0.05
  power: 0.80
  sample_size_per_variant: 23849
  
schedule:
  start_date: 2024-12-20
  estimated_duration_days: 10
  
owner: "@product-team"
session: CONV-2024-12-17-001
```

---

## Phase 3: Implementation

### Experiment Assignment

```typescript
// experiment-assignment.ts
import { createHash } from 'crypto';

interface ExperimentConfig {
  id: string;
  variants: string[];
  allocation: number[];  // Must sum to 100
  salt: string;
}

function assignVariant(
  userId: string,
  experiment: ExperimentConfig
): string {
  // Deterministic assignment using hash
  const hash = createHash('sha256')
    .update(`${experiment.salt}:${userId}`)
    .digest('hex');
  
  // Convert first 8 chars to number (0-4294967295)
  const hashNum = parseInt(hash.slice(0, 8), 16);
  
  // Normalize to 0-100
  const bucket = (hashNum / 0xffffffff) * 100;
  
  // Assign based on allocation
  let cumulative = 0;
  for (let i = 0; i < experiment.variants.length; i++) {
    cumulative += experiment.allocation[i];
    if (bucket < cumulative) {
      return experiment.variants[i];
    }
  }
  
  return experiment.variants[experiment.variants.length - 1];
}

// Usage
const experiment: ExperimentConfig = {
  id: 'exp-001-checkout',
  variants: ['control', 'treatment'],
  allocation: [50, 50],
  salt: 'exp-001-v1',
};

const variant = assignVariant(user.id, experiment);
// Always returns same variant for same user
```

### Event Tracking

```typescript
// experiment-tracking.ts
interface ExperimentEvent {
  experimentId: string;
  variant: string;
  userId: string;
  eventType: 'exposure' | 'conversion' | 'custom';
  eventName?: string;
  value?: number;
  timestamp: Date;
  properties?: Record<string, unknown>;
}

class ExperimentTracker {
  // Track when user sees experiment
  trackExposure(experimentId: string, variant: string, userId: string) {
    this.track({
      experimentId,
      variant,
      userId,
      eventType: 'exposure',
      timestamp: new Date(),
    });
  }

  // Track conversion
  trackConversion(
    experimentId: string,
    variant: string,
    userId: string,
    value?: number
  ) {
    this.track({
      experimentId,
      variant,
      userId,
      eventType: 'conversion',
      value,
      timestamp: new Date(),
    });
  }

  // Track custom metric
  trackMetric(
    experimentId: string,
    variant: string,
    userId: string,
    metricName: string,
    value: number
  ) {
    this.track({
      experimentId,
      variant,
      userId,
      eventType: 'custom',
      eventName: metricName,
      value,
      timestamp: new Date(),
    });
  }

  private async track(event: ExperimentEvent) {
    // Send to analytics pipeline
    await analytics.track('experiment_event', event);
  }
}

// Usage in checkout
const tracker = new ExperimentTracker();

// On page load
tracker.trackExposure('exp-001', variant, user.id);

// On checkout complete
tracker.trackConversion('exp-001', variant, user.id, order.total);
```

---

## Phase 4: Monitoring

### Experiment Health Dashboard

```markdown
## Experiment Dashboard: EXP-001

### Status: 🟢 Running (Day 5 of 10)

### Sample Size Progress
| Variant | Target | Current | % Complete |
|---------|--------|---------|------------|
| Control | 23,849 | 14,230 | 60% |
| Treatment | 23,849 | 14,102 | 59% |

### Primary Metric: Checkout Completion Rate
| Variant | Conversions | Sample | Rate | vs Control |
|---------|-------------|--------|------|------------|
| Control | 455 | 14,230 | 3.20% | - |
| Treatment | 512 | 14,102 | 3.63% | **+13.4%** |

**Statistical Significance:** 78% (need 95%)
**Estimated days to significance:** 3-4 more days

### Guardrail Metrics
| Metric | Control | Treatment | Status |
|--------|---------|-----------|--------|
| Error Rate | 0.45% | 0.52% | 🟢 OK |
| Load Time | 1.1s | 1.2s | 🟢 OK |
| Support Tickets | 8/day | 9/day | 🟢 OK |

### Health Checks
- ✅ Sample ratio mismatch: None (0.9% diff)
- ✅ No novelty effects detected
- ✅ Consistent across segments
- ✅ No data quality issues
```

### Sample Ratio Mismatch Check

```python
# srm_check.py
from scipy import stats

def check_sample_ratio_mismatch(
    control_size: int,
    treatment_size: int,
    expected_ratio: float = 0.5
) -> dict:
    """
    Check for Sample Ratio Mismatch using chi-square test.
    
    SRM indicates potential issues with randomization or tracking.
    """
    total = control_size + treatment_size
    expected_control = total * expected_ratio
    expected_treatment = total * (1 - expected_ratio)
    
    chi2, p_value = stats.chisquare(
        [control_size, treatment_size],
        [expected_control, expected_treatment]
    )
    
    actual_ratio = control_size / total
    ratio_diff = abs(actual_ratio - expected_ratio)
    
    return {
        'control_size': control_size,
        'treatment_size': treatment_size,
        'expected_ratio': expected_ratio,
        'actual_ratio': round(actual_ratio, 4),
        'ratio_difference': round(ratio_diff, 4),
        'chi_square': round(chi2, 4),
        'p_value': round(p_value, 4),
        'srm_detected': p_value < 0.01,
        'status': '❌ SRM Detected' if p_value < 0.01 else '✅ No SRM'
    }

# Example
result = check_sample_ratio_mismatch(14230, 14102, 0.5)
print(result)
# {'status': '✅ No SRM', 'p_value': 0.456, ...}
```

---

## Phase 5: Analysis

### Statistical Analysis

```python
# experiment_analysis.py
import numpy as np
from scipy import stats
import pandas as pd

def analyze_proportion_metric(
    control_conversions: int,
    control_total: int,
    treatment_conversions: int,
    treatment_total: int,
    alpha: float = 0.05
) -> dict:
    """
    Analyze A/B test results for proportion metrics (e.g., conversion rate).
    """
    # Calculate rates
    p_control = control_conversions / control_total
    p_treatment = treatment_conversions / treatment_total
    
    # Relative lift
    relative_lift = (p_treatment - p_control) / p_control
    
    # Standard error
    se = np.sqrt(
        p_control * (1 - p_control) / control_total +
        p_treatment * (1 - p_treatment) / treatment_total
    )
    
    # Z-test
    z_score = (p_treatment - p_control) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    # Confidence interval
    z_critical = stats.norm.ppf(1 - alpha / 2)
    ci_lower = (p_treatment - p_control) - z_critical * se
    ci_upper = (p_treatment - p_control) + z_critical * se
    
    # Convert to relative CI
    ci_lower_rel = ci_lower / p_control
    ci_upper_rel = ci_upper / p_control
    
    return {
        'control_rate': round(p_control, 4),
        'treatment_rate': round(p_treatment, 4),
        'absolute_lift': round(p_treatment - p_control, 4),
        'relative_lift': round(relative_lift, 4),
        'relative_lift_pct': f"{relative_lift * 100:.1f}%",
        'z_score': round(z_score, 3),
        'p_value': round(p_value, 4),
        'significant': p_value < alpha,
        'confidence_interval': f"[{ci_lower_rel*100:.1f}%, {ci_upper_rel*100:.1f}%]",
        'conclusion': 'Winner' if p_value < alpha and relative_lift > 0 else 
                     'Loser' if p_value < alpha and relative_lift < 0 else
                     'Inconclusive'
    }

# Example analysis
results = analyze_proportion_metric(
    control_conversions=455,
    control_total=14230,
    treatment_conversions=512,
    treatment_total=14102
)

print("=" * 50)
print("EXPERIMENT RESULTS")
print("=" * 50)
print(f"Control Rate: {results['control_rate']:.2%}")
print(f"Treatment Rate: {results['treatment_rate']:.2%}")
print(f"Relative Lift: {results['relative_lift_pct']}")
print(f"P-value: {results['p_value']}")
print(f"Significant: {results['significant']}")
print(f"95% CI: {results['confidence_interval']}")
print(f"Conclusion: {results['conclusion']}")
```

### Results Report Template

```markdown
## Experiment Results: EXP-001 Checkout Simplification

### Executive Summary
**Result: ✅ Winner - Ship Treatment**

The simplified 3-step checkout significantly outperformed the control,
increasing checkout completion rate by 13.4% (p=0.02).

### Key Metrics

| Metric | Control | Treatment | Lift | P-value | Result |
|--------|---------|-----------|------|---------|--------|
| **Completion Rate** | 3.20% | 3.63% | **+13.4%** | 0.02 | ✅ Winner |
| Revenue/User | $45.20 | $46.10 | +2.0% | 0.34 | Neutral |
| Checkout Time | 180s | 145s | -19.4% | <0.01 | ✅ Improved |

### Guardrails
| Metric | Control | Treatment | Status |
|--------|---------|-----------|--------|
| Error Rate | 0.45% | 0.52% | ✅ Pass |
| Load Time | 1.1s | 1.2s | ✅ Pass |

### Statistical Details
- Sample Size: 28,332 (14,230 control, 14,102 treatment)
- Duration: 10 days
- Statistical Power: 83%
- Confidence Level: 95%
- 95% CI for lift: [+2.1%, +24.7%]

### Segment Analysis
| Segment | Control | Treatment | Lift | Significant |
|---------|---------|-----------|------|-------------|
| Mobile | 2.8% | 3.4% | +21% | Yes |
| Desktop | 3.6% | 3.9% | +8% | No |
| New Users | 2.4% | 3.0% | +25% | Yes |
| Returning | 4.1% | 4.2% | +2% | No |

### Recommendation
1. **Ship to 100%** - Results are statistically significant and positive
2. **Monitor for 2 weeks** post-launch
3. **Consider mobile-first optimization** - Largest gains on mobile

### Next Steps
- [ ] Remove feature flag
- [ ] Update documentation
- [ ] Plan follow-up experiment for payment step

---
*Experiment concluded: 2024-12-30*
*Session: CONV-2024-12-17-001*
```

---

## Best Practices

### Do's ✅

```markdown
- Define hypothesis BEFORE looking at data
- Calculate sample size BEFORE starting
- Run to full sample size (no peeking!)
- Use guard rails for safety
- Check for SRM regularly
- Document everything
- Segment analysis as secondary
```

### Don'ts ❌

```markdown
- Don't stop early just because significant
- Don't run multiple tests on same users
- Don't ignore guardrail failures
- Don't make decisions on secondary metrics
- Don't forget novelty effects
- Don't test without sufficient traffic
```

---

## Black Box Integration

```bash
# Start experiment session
./blackbox.sh start "experiment-checkout-simplification"

# Log design
./blackbox.sh decision "3-step vs 5-step checkout" "Reduce friction"
./blackbox.sh action "Calculated sample size" "23,849 per variant"

# Log execution
./blackbox.sh action "Started experiment" "50/50 allocation"
./blackbox.sh checkpoint "Day 5 - 60% complete"

# Log results
./blackbox.sh action "Analyzed results" "13.4% lift, p=0.02"
./blackbox.sh milestone "Experiment concluded - Winner"
./blackbox.sh decision "Ship treatment" "Significant positive result"

# End session
./blackbox.sh end "Checkout completion +13.4%"
```

---

*A/B Testing Workflow v1.0*
*Integrates with Black Box for tracking*
