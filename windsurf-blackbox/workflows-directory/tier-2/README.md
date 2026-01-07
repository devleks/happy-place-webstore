# Tier 2 Workflows

Extended workflows for specialized development scenarios beyond the core Tier 1 collection.

## Tier 2 Workflow Collection

| # | Workflow | Status | Description |
|---|----------|--------|-------------|
| 12 | [Database Migration](12-database-migration.md) | ✅ Complete | Schema changes, data migrations, rollback procedures |
| 13 | [Performance Optimization](13-performance-optimization.md) | ✅ Complete | Profiling, bottleneck analysis, optimization strategies |
| 14 | [Documentation Generation](14-documentation-generation.md) | ✅ Complete | API docs, architecture docs, automation |
| 15 | [Technical Debt Management](15-technical-debt-management.md) | ✅ Complete | Debt identification, prioritization, remediation |
| 16 | [Feature Flag Management](16-feature-flag-management.md) | ✅ Complete | Progressive rollouts, A/B testing, cleanup |
| 17 | [A/B Testing](17-ab-testing.md) | ✅ Complete | Experiment design, statistical analysis, reporting |
| 18 | [Monitoring & Alerting](18-monitoring-alerting.md) | ✅ Complete | Metrics, logs, traces, SLIs/SLOs |
| 19 | [Disaster Recovery](19-disaster-recovery.md) | ✅ Complete | Backup, failover, DR testing |
| 20 | [Compliance & Auditing](20-compliance-auditing.md) | ✅ Complete | SOC2, GDPR, audit logging, evidence collection |

## Adding New Workflows

When creating a Tier 2 workflow:

1. Follow the Tier 1 template structure
2. Include Black Box integration
3. Add Cascade prompts
4. Update the main README
5. Add to cheat sheet

## Template

```markdown
# [Number] - [Workflow Name]

## Overview
[Brief description]

## When to Use
[Triggers and scenarios]

## Quick Start
\`\`\`bash
./blackbox.sh start "[workflow]-[topic]"
\`\`\`

## Cascade Prompt
\`\`\`
Execute [Workflow Name] workflow:
1. Step 1
2. Step 2
...
\`\`\`

## Detailed Steps
[Full workflow content]

## Black Box Integration
[How to log and track]

## Outputs
[Expected deliverables]
```

---

*Tier 2 Workflows - Coming Soon*
