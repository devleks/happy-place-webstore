# 18 - Monitoring & Alerting Workflow

Comprehensive approach to implementing observability through metrics, logs, and traces with intelligent alerting to detect and respond to issues proactively.

---

## Overview

This workflow establishes a robust monitoring foundation following the three pillars of observability: metrics, logs, and traces.

## When to Use

- Setting up new application monitoring
- Improving existing observability
- Defining SLIs/SLOs/SLAs
- Configuring alerting rules
- Debugging production issues
- Capacity planning

---

## Quick Start

```bash
./blackbox.sh start "monitoring-[scope]-[objective]"
```

---

## Cascade Prompt

```
Execute Monitoring & Alerting workflow for: [SERVICE/APPLICATION]

Scope: [infrastructure/application/business/all]
Current state: [none/basic/advanced]
Key objectives: [uptime/performance/cost/user-experience]

Steps:
1. Define SLIs and SLOs
2. Implement metrics collection
3. Configure log aggregation
4. Set up distributed tracing
5. Create dashboards
6. Configure intelligent alerts

Reference: workflows/tier-2/18-monitoring-alerting.md
Session: [CURRENT-SESSION-ID]
```

---

## Observability Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                 THREE PILLARS OF OBSERVABILITY                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  METRICS                 LOGS                   TRACES          │
│  ┌──────────────┐       ┌──────────────┐       ┌──────────────┐│
│  │ What's       │       │ What         │       │ How requests ││
│  │ happening?   │       │ happened?    │       │ flow?        ││
│  │              │       │              │       │              ││
│  │ • Counters   │       │ • Events     │       │ • Spans      ││
│  │ • Gauges     │       │ • Errors     │       │ • Context    ││
│  │ • Histograms │       │ • Audit      │       │ • Latency    ││
│  │ • Summaries  │       │ • Debug      │       │ • Errors     ││
│  └──────────────┘       └──────────────┘       └──────────────┘│
│         │                      │                      │        │
│         └──────────────────────┴──────────────────────┘        │
│                               │                                 │
│                    ┌──────────▼──────────┐                     │
│                    │     DASHBOARDS      │                     │
│                    │     & ALERTS        │                     │
│                    └─────────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Define SLIs/SLOs

### SLI (Service Level Indicator) Examples

```yaml
# sli-definitions.yaml
slis:
  availability:
    name: "Service Availability"
    description: "Proportion of successful requests"
    formula: "successful_requests / total_requests"
    good_threshold: "status_code < 500"
    
  latency:
    name: "Request Latency"
    description: "Proportion of requests faster than threshold"
    formula: "requests_under_threshold / total_requests"
    good_threshold: "response_time < 200ms"
    
  error_rate:
    name: "Error Rate"
    description: "Proportion of requests resulting in errors"
    formula: "error_requests / total_requests"
    good_threshold: "status_code < 400"
    
  throughput:
    name: "Throughput"
    description: "Requests processed per second"
    formula: "requests / time_window"
    good_threshold: "> 1000 rps"
```

### SLO (Service Level Objective) Template

```markdown
## SLO: API Availability

### Definition
99.9% of API requests should succeed within 200ms over a 30-day window.

### Components
| SLI | Target | Window |
|-----|--------|--------|
| Availability | 99.9% | 30 days |
| Latency (p99) | < 200ms | 30 days |

### Error Budget
- Monthly budget: 43.2 minutes downtime
- Current consumption: 12.5 minutes (29%)
- Remaining: 30.7 minutes

### Alerting Thresholds
| Alert | Condition | Severity |
|-------|-----------|----------|
| Fast burn | >5% budget in 1 hour | Critical |
| Slow burn | >10% budget in 6 hours | Warning |
| Budget exhausted | >100% consumed | Critical |
```

---

## Phase 2: Metrics Implementation

### Application Metrics (Prometheus)

```typescript
// metrics.ts
import { Counter, Histogram, Gauge, Registry } from 'prom-client';

// Create registry
export const registry = new Registry();

// HTTP request metrics
export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [registry],
});

export const httpRequestTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [registry],
});

// Business metrics
export const ordersProcessed = new Counter({
  name: 'orders_processed_total',
  help: 'Total number of orders processed',
  labelNames: ['status', 'payment_method'],
  registers: [registry],
});

export const orderValue = new Histogram({
  name: 'order_value_dollars',
  help: 'Order value in dollars',
  buckets: [10, 25, 50, 100, 250, 500, 1000],
  registers: [registry],
});

// System metrics
export const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  labelNames: ['type'],
  registers: [registry],
});

export const queueSize = new Gauge({
  name: 'queue_size',
  help: 'Current queue size',
  labelNames: ['queue_name'],
  registers: [registry],
});

// Express middleware
export function metricsMiddleware(req, res, next) {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;
    const labels = {
      method: req.method,
      route,
      status_code: res.statusCode,
    };
    
    httpRequestDuration.observe(labels, duration);
    httpRequestTotal.inc(labels);
  });
  
  next();
}
```

### Infrastructure Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api-servers'
    static_configs:
      - targets: ['api-1:9090', 'api-2:9090']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'kubernetes'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

---

## Phase 3: Logging

### Structured Logging

```typescript
// logger.ts
import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  base: {
    service: 'api-service',
    version: process.env.APP_VERSION,
    environment: process.env.NODE_ENV,
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

// Request logger middleware
export function requestLogger(req, res, next) {
  const requestId = req.headers['x-request-id'] || generateId();
  const startTime = Date.now();
  
  // Add to request context
  req.log = logger.child({
    requestId,
    method: req.method,
    path: req.path,
    userAgent: req.headers['user-agent'],
  });
  
  req.log.info({ query: req.query }, 'Request started');
  
  res.on('finish', () => {
    req.log.info({
      statusCode: res.statusCode,
      duration: Date.now() - startTime,
    }, 'Request completed');
  });
  
  next();
}

// Usage in code
logger.info({ orderId, userId }, 'Processing order');
logger.error({ err, orderId }, 'Order processing failed');
```

### Log Aggregation (Loki/ELK)

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/log/containers/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            message: msg
            requestId: requestId
            service: service
      - labels:
          level:
          service:
      - timestamp:
          source: time
          format: RFC3339
```

---

## Phase 4: Distributed Tracing

### OpenTelemetry Setup

```typescript
// tracing.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'api-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: process.env.APP_VERSION,
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV,
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

// Manual span creation
import { trace, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('api-service');

async function processOrder(orderId: string) {
  return tracer.startActiveSpan('processOrder', async (span) => {
    try {
      span.setAttribute('order.id', orderId);
      
      // Nested span for payment
      await tracer.startActiveSpan('processPayment', async (paymentSpan) => {
        const result = await paymentService.charge(orderId);
        paymentSpan.setAttribute('payment.status', result.status);
        paymentSpan.end();
      });
      
      span.setStatus({ code: SpanStatusCode.OK });
    } catch (error) {
      span.recordException(error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      span.end();
    }
  });
}
```

---

## Phase 5: Dashboards

### Grafana Dashboard Template

```json
{
  "dashboard": {
    "title": "API Service Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (status_code)",
            "legendFormat": "{{status_code}}"
          }
        ]
      },
      {
        "title": "Latency (p50, p95, p99)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status_code=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
          }
        ],
        "thresholds": {
          "mode": "absolute",
          "steps": [
            {"value": 0, "color": "green"},
            {"value": 1, "color": "yellow"},
            {"value": 5, "color": "red"}
          ]
        }
      },
      {
        "title": "Active Connections",
        "type": "gauge",
        "targets": [
          {
            "expr": "sum(active_connections)"
          }
        ]
      }
    ]
  }
}
```

### Dashboard Hierarchy

```markdown
## Dashboard Organization

### Level 1: Executive
- Business KPIs
- SLO status
- Cost overview

### Level 2: Service Overview
- Request rates
- Error rates
- Latency percentiles
- Availability

### Level 3: Deep Dive
- Per-endpoint metrics
- Database performance
- Cache hit rates
- Queue depths

### Level 4: Debug
- Individual traces
- Log correlation
- Resource utilization
```

---

## Phase 6: Alerting

### Alert Rules (Prometheus)

```yaml
# alert-rules.yaml
groups:
  - name: slo-alerts
    rules:
      # Fast burn - 5% budget in 1 hour
      - alert: SLOFastBurn
        expr: |
          (
            sum(rate(http_requests_total{status_code=~"5.."}[1h]))
            / sum(rate(http_requests_total[1h]))
          ) > 14.4 * 0.001
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate burning SLO budget quickly"
          description: "Error rate is {{ $value | humanizePercentage }}"
          runbook: "https://wiki/runbooks/slo-fast-burn"

      # Slow burn - 10% budget in 6 hours
      - alert: SLOSlowBurn
        expr: |
          (
            sum(rate(http_requests_total{status_code=~"5.."}[6h]))
            / sum(rate(http_requests_total[6h]))
          ) > 2 * 0.001
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Elevated error rate consuming SLO budget"

  - name: infrastructure-alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical

  - name: application-alerts
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "p99 latency above 2 seconds"

      - alert: DatabaseConnectionPoolExhausted
        expr: pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 2m
        labels:
          severity: critical
```

### Alert Routing (Alertmanager)

```yaml
# alertmanager.yml
global:
  slack_api_url: $SLACK_WEBHOOK_URL
  pagerduty_url: https://events.pagerduty.com/v2/enqueue

route:
  receiver: 'default'
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
      
    - match:
        severity: critical
      receiver: 'slack-critical'
      
    - match:
        severity: warning
      receiver: 'slack-warning'

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts-default'
        
  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts-critical'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ end }}'
        
  - name: 'slack-warning'
    slack_configs:
      - channel: '#alerts-warning'
        
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: $PAGERDUTY_SERVICE_KEY
        severity: critical
```

---

## Monitoring Checklist

```markdown
## Monitoring Implementation Checklist

### Metrics
- [ ] Application metrics defined
- [ ] Business metrics defined
- [ ] Infrastructure metrics collected
- [ ] Prometheus configured
- [ ] Exporters installed

### Logging
- [ ] Structured logging implemented
- [ ] Log levels configured
- [ ] Request IDs propagated
- [ ] Log aggregation set up
- [ ] Retention policies defined

### Tracing
- [ ] OpenTelemetry SDK installed
- [ ] Auto-instrumentation enabled
- [ ] Context propagation working
- [ ] Trace sampling configured

### Dashboards
- [ ] Overview dashboard created
- [ ] Per-service dashboards
- [ ] Business metrics dashboard
- [ ] On-call dashboard

### Alerting
- [ ] SLOs defined
- [ ] Alert rules created
- [ ] Routing configured
- [ ] Runbooks written
- [ ] On-call schedule set
```

---

## Black Box Integration

```bash
# Start monitoring session
./blackbox.sh start "monitoring-api-observability"

# Log implementation
./blackbox.sh action "Defined SLIs and SLOs" "99.9% availability target"
./blackbox.sh action "Implemented Prometheus metrics" "15 custom metrics"
./blackbox.sh decision "Use Loki over ELK" "Better Prometheus integration"
./blackbox.sh action "Configured alerting rules" "12 rules created"
./blackbox.sh milestone "Full observability stack deployed"

# End session
./blackbox.sh end "Monitoring coverage: 95%"
```

---

*Monitoring & Alerting Workflow v1.0*
*Integrates with Black Box for tracking*
