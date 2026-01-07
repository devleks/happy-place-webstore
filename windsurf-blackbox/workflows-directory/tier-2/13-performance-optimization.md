# 13 - Performance Optimization Workflow

Systematic approach to identifying, measuring, and resolving performance bottlenecks across frontend, backend, and infrastructure layers.

---

## Overview

This workflow provides a structured methodology for performance optimization, from initial profiling through implementation and validation of improvements.

## When to Use

- Application feels slow or unresponsive
- Performance regression detected
- Scaling for increased load
- Pre-launch performance review
- Cost optimization (reduce resource usage)
- User experience improvement initiatives

---

## Quick Start

```bash
./blackbox.sh start "perf-[area]-[issue]"
```

---

## Cascade Prompt

```
Execute Performance Optimization workflow for: [DESCRIPTION]

Area: [frontend/backend/database/infrastructure/full-stack]
Current state: [metrics if known]
Target: [performance goals]

Steps:
1. Establish baseline metrics
2. Profile and identify bottlenecks
3. Prioritize by impact
4. Implement optimizations
5. Validate improvements
6. Document and monitor

Reference: workflows/tier-2/13-performance-optimization.md
Session: [CURRENT-SESSION-ID]
```

---

## Performance Targets

### Industry Benchmarks

| Metric | Target | Poor |
|--------|--------|------|
| **First Contentful Paint (FCP)** | < 1.8s | > 3s |
| **Largest Contentful Paint (LCP)** | < 2.5s | > 4s |
| **First Input Delay (FID)** | < 100ms | > 300ms |
| **Cumulative Layout Shift (CLS)** | < 0.1 | > 0.25 |
| **Time to Interactive (TTI)** | < 3.8s | > 7.3s |
| **API Response Time (p50)** | < 200ms | > 1s |
| **API Response Time (p99)** | < 1s | > 5s |
| **Database Query Time** | < 100ms | > 500ms |
| **Error Rate** | < 0.1% | > 1% |

---

## Phase 1: Baseline Measurement

### Frontend Profiling

```bash
# Lighthouse CLI
npm install -g lighthouse
lighthouse https://your-site.com --output=json --output-path=./baseline.json

# WebPageTest
# Use https://www.webpagetest.org/ for detailed waterfall

# Chrome DevTools
# Performance tab → Record → Analyze
```

### Lighthouse Automation Script

```javascript
// lighthouse-audit.js
const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');

async function runAudit(url) {
    const chrome = await chromeLauncher.launch({chromeFlags: ['--headless']});
    const options = {
        logLevel: 'info',
        output: 'json',
        port: chrome.port,
        onlyCategories: ['performance']
    };
    
    const result = await lighthouse(url, options);
    await chrome.kill();
    
    const report = {
        url,
        timestamp: new Date().toISOString(),
        scores: {
            performance: result.lhr.categories.performance.score * 100,
            fcp: result.lhr.audits['first-contentful-paint'].numericValue,
            lcp: result.lhr.audits['largest-contentful-paint'].numericValue,
            cls: result.lhr.audits['cumulative-layout-shift'].numericValue,
            tbt: result.lhr.audits['total-blocking-time'].numericValue
        }
    };
    
    fs.writeFileSync(
        `perf-baseline-${Date.now()}.json`, 
        JSON.stringify(report, null, 2)
    );
    
    return report;
}

runAudit('https://your-site.com').then(console.log);
```

### Backend Profiling

```bash
# Node.js profiling
node --prof app.js
node --prof-process isolate-*.log > profile.txt

# Python profiling
python -m cProfile -o profile.stats app.py
python -m pstats profile.stats

# Go profiling
go tool pprof http://localhost:6060/debug/pprof/profile
```

### Database Profiling

```sql
-- PostgreSQL: Enable slow query log
ALTER SYSTEM SET log_min_duration_statement = 100;  -- Log queries > 100ms
SELECT pg_reload_conf();

-- Find slow queries
SELECT query, calls, mean_time, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Check missing indexes
SELECT schemaname, relname, seq_scan, seq_tup_read,
       idx_scan, idx_tup_fetch,
       seq_tup_read / NULLIF(seq_scan, 0) as avg_seq_tup
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;
```

### Baseline Report Template

```markdown
## Performance Baseline Report

**Date:** [YYYY-MM-DD]
**Session:** [CONV-ID]
**Environment:** [Production/Staging]

### Frontend Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| FCP | [X]s | < 1.8s | 🟢/🟡/🔴 |
| LCP | [X]s | < 2.5s | 🟢/🟡/🔴 |
| CLS | [X] | < 0.1 | 🟢/🟡/🔴 |
| TTI | [X]s | < 3.8s | 🟢/🟡/🔴 |

### Backend Metrics
| Endpoint | p50 | p95 | p99 | RPS |
|----------|-----|-----|-----|-----|
| GET /api/users | [X]ms | [X]ms | [X]ms | [X] |

### Database Metrics
| Query | Avg Time | Calls/min | Total Time |
|-------|----------|-----------|------------|
| [query] | [X]ms | [X] | [X]s |

### Infrastructure
- CPU utilization: [X]%
- Memory usage: [X]%
- Network I/O: [X] MB/s
- Disk I/O: [X] IOPS
```

---

## Phase 2: Identify Bottlenecks

### Bottleneck Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERFORMANCE BOTTLENECK MAP                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FRONTEND                                                       │
│  ├── Render blocking resources (CSS, JS)                        │
│  ├── Large bundle sizes                                         │
│  ├── Unoptimized images                                         │
│  ├── Layout thrashing                                           │
│  ├── Memory leaks                                               │
│  └── Third-party scripts                                        │
│                                                                 │
│  BACKEND                                                        │
│  ├── Slow database queries                                      │
│  ├── N+1 query problems                                         │
│  ├── Missing caching                                            │
│  ├── Synchronous blocking operations                            │
│  ├── Inefficient algorithms                                     │
│  └── External API latency                                       │
│                                                                 │
│  DATABASE                                                       │
│  ├── Missing indexes                                            │
│  ├── Table locks                                                │
│  ├── Connection pool exhaustion                                 │
│  ├── Unoptimized queries                                        │
│  └── Data model issues                                          │
│                                                                 │
│  INFRASTRUCTURE                                                 │
│  ├── Insufficient resources                                     │
│  ├── Network latency                                            │
│  ├── Disk I/O bottlenecks                                       │
│  ├── Load balancer configuration                                │
│  └── CDN misses                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Analysis Queries

```sql
-- Find N+1 queries (look for similar queries with different IDs)
SELECT LEFT(query, 100) as query_pattern, 
       count(*) as count,
       avg(mean_time) as avg_time
FROM pg_stat_statements
GROUP BY LEFT(query, 100)
HAVING count(*) > 100
ORDER BY count DESC;

-- Find missing indexes
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
-- Look for "Seq Scan" on large tables

-- Find lock contention
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.query AS blocked_query
FROM pg_locks blocked_locks
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
```

---

## Phase 3: Optimization Strategies

### Frontend Optimizations

```javascript
// 1. Code splitting
const Dashboard = React.lazy(() => import('./Dashboard'));

// 2. Image optimization
<Image
  src="/hero.jpg"
  width={800}
  height={600}
  loading="lazy"
  placeholder="blur"
/>

// 3. Memoization
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* render */}</div>;
});

const memoizedValue = useMemo(() => computeExpensive(a, b), [a, b]);

// 4. Virtual scrolling for long lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={400}
  itemCount={10000}
  itemSize={35}
>
  {Row}
</FixedSizeList>

// 5. Debounce expensive operations
const debouncedSearch = useMemo(
  () => debounce((query) => search(query), 300),
  []
);
```

### Backend Optimizations

```python
# 1. Database query optimization - avoid N+1
# Bad
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # N+1 queries

# Good
users = User.objects.select_related('profile').all()

# 2. Caching
from functools import lru_cache
from django.core.cache import cache

@lru_cache(maxsize=1000)
def get_user_permissions(user_id):
    return calculate_permissions(user_id)

# Redis caching
def get_user(user_id):
    cache_key = f"user:{user_id}"
    user = cache.get(cache_key)
    if not user:
        user = User.objects.get(id=user_id)
        cache.set(cache_key, user, timeout=3600)
    return user

# 3. Async operations
import asyncio
import aiohttp

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# 4. Pagination
def get_users(page=1, per_page=20):
    return User.objects.all()[(page-1)*per_page:page*per_page]

# 5. Connection pooling
from sqlalchemy import create_engine
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### Database Optimizations

```sql
-- 1. Add missing indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_orders_user_created 
    ON orders(user_id, created_at DESC);

-- 2. Partial indexes for filtered queries
CREATE INDEX idx_active_users ON users(email) WHERE active = true;

-- 3. Covering indexes
CREATE INDEX idx_orders_summary 
    ON orders(user_id) INCLUDE (total, status);

-- 4. Query optimization
-- Bad: SELECT * 
SELECT id, name, email FROM users WHERE id = 1;

-- Bad: LIKE with leading wildcard
-- Good: Full-text search or trigram index
CREATE INDEX idx_users_name_trgm ON users USING gin(name gin_trgm_ops);
SELECT * FROM users WHERE name ILIKE '%john%';

-- 5. Batch operations
-- Bad: Individual inserts in loop
-- Good: Bulk insert
INSERT INTO logs (message, created_at)
VALUES 
    ('msg1', now()),
    ('msg2', now()),
    ('msg3', now());
```

### Infrastructure Optimizations

```yaml
# 1. CDN configuration (Cloudflare)
# Cache static assets aggressively
Cache-Control: public, max-age=31536000, immutable

# 2. Nginx optimization
worker_processes auto;
worker_connections 4096;

gzip on;
gzip_types text/plain application/json application/javascript text/css;
gzip_min_length 1000;

# Connection keepalive
keepalive_timeout 65;
keepalive_requests 100;

# 3. Redis configuration
maxmemory 2gb
maxmemory-policy allkeys-lru

# 4. Database connection pooling (PgBouncer)
[databases]
mydb = host=localhost dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

---

## Phase 4: Implementation

### Optimization Priority Matrix

| Optimization | Impact | Effort | Priority |
|--------------|--------|--------|----------|
| Add missing DB index | High | Low | P0 |
| Enable CDN caching | High | Low | P0 |
| Fix N+1 queries | High | Medium | P1 |
| Code splitting | Medium | Medium | P2 |
| Image optimization | Medium | Low | P1 |
| Add Redis caching | High | High | P1 |

### Implementation Checklist

```markdown
## Optimization Implementation Checklist

### Pre-Implementation
- [ ] Baseline metrics recorded
- [ ] Optimization plan reviewed
- [ ] Rollback plan documented
- [ ] Feature flag created (if applicable)

### Implementation
- [ ] Code changes complete
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Performance tests run

### Validation
- [ ] Metrics improved as expected
- [ ] No regressions in other areas
- [ ] No new errors introduced
- [ ] Load testing completed

### Deployment
- [ ] Staged rollout plan
- [ ] Monitoring dashboards ready
- [ ] Alerting configured
- [ ] Documentation updated
```

---

## Phase 5: Validation

### A/B Performance Comparison

```javascript
// performance-comparison.js
const baseline = require('./perf-baseline.json');
const current = require('./perf-current.json');

const compare = (metric, baseVal, currVal, lowerIsBetter = true) => {
    const diff = currVal - baseVal;
    const pct = ((diff / baseVal) * 100).toFixed(1);
    const improved = lowerIsBetter ? diff < 0 : diff > 0;
    return {
        baseline: baseVal,
        current: currVal,
        diff,
        pctChange: `${pct}%`,
        status: improved ? '✅ Improved' : diff === 0 ? '➖ No change' : '❌ Regressed'
    };
};

console.log('Performance Comparison');
console.log('======================');
console.log('FCP:', compare('FCP', baseline.fcp, current.fcp));
console.log('LCP:', compare('LCP', baseline.lcp, current.lcp));
console.log('TTI:', compare('TTI', baseline.tti, current.tti));
```

### Load Testing

```yaml
# k6 load test script
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '2m', target: 100 },   // Ramp up
        { duration: '5m', target: 100 },   // Stay at 100
        { duration: '2m', target: 200 },   // Ramp to 200
        { duration: '5m', target: 200 },   // Stay at 200
        { duration: '2m', target: 0 },     // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],  // 95% under 500ms
        http_req_failed: ['rate<0.01'],    // Error rate < 1%
    },
};

export default function() {
    const res = http.get('https://api.example.com/users');
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
    });
    sleep(1);
}
```

---

## Phase 6: Documentation

### Performance Report Template

```markdown
## Performance Optimization Report

**Session:** [CONV-ID]
**Date:** [YYYY-MM-DD]
**Author:** [Name]

### Executive Summary
[Brief summary of optimizations and results]

### Metrics Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| LCP | 4.2s | 2.1s | 50% faster |
| API p95 | 800ms | 200ms | 75% faster |
| DB queries | 45/req | 12/req | 73% reduction |

### Optimizations Implemented

1. **[Optimization 1]**
   - Problem: [Description]
   - Solution: [What was done]
   - Impact: [Measured improvement]

2. **[Optimization 2]**
   - Problem: [Description]
   - Solution: [What was done]
   - Impact: [Measured improvement]

### Recommendations
- [Future optimization 1]
- [Future optimization 2]

### Monitoring
- Dashboard: [Link]
- Alerts configured: [List]
```

---

## Black Box Integration

```bash
# Start performance session
./blackbox.sh start "perf-api-optimization"

# Log baseline
./blackbox.sh action "Captured baseline metrics" "p95: 800ms"

# Log findings
./blackbox.sh issue "N+1 query in /users endpoint" "identified"

# Log optimization
./blackbox.sh decision "Add Redis caching for user lookups" "High traffic endpoint"
./blackbox.sh action "Implemented caching layer" "success"

# Log results
./blackbox.sh milestone "API p95 reduced from 800ms to 200ms"

# End session
./blackbox.sh end "75% improvement achieved"
```

---

## Quick Reference

| Task | Tool/Command |
|------|--------------|
| Frontend profiling | Lighthouse, Chrome DevTools |
| Backend profiling | `node --prof`, `py-spy`, `go pprof` |
| Database profiling | `pg_stat_statements`, `EXPLAIN ANALYZE` |
| Load testing | k6, Artillery, JMeter |
| APM | Datadog, New Relic, Sentry |
| Bundle analysis | `webpack-bundle-analyzer` |

---

*Performance Optimization Workflow v1.0*
*Integrates with Black Box for tracking improvements*
