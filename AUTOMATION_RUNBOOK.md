# Automation Runbook

This runbook documents the local-first agent framework introduced for Happy Place Boutique.

## New Artifacts & Layout
- `reports/` — canonical location for generated JSON, Markdown, and log outputs (tracked via `.gitkeep`).
- `ci_workflows/` — holds agent scripts, helper utilities, the orchestration runner, and a GitHub Actions template (`agents-ci.yml`) ready to copy into `.github/workflows/` when remote CI is desired.
- Helper assets:
  - `ci_workflows/helpers/perfsmith_hotspots.py`
  - `ci_workflows/helpers/schemasage_explain.sql`

## Local Execution
1. Ensure backend virtualenv and frontend dependencies (`npm install`) are available.
2. Export `DATABASE_URL` for SchemaSage (example: `export DATABASE_URL=postgresql://user:pass@localhost:5432/happy_place_db`).
3. Run individual agents as needed: `bash ci_workflows/agent_lintguard.sh`, `bash ci_workflows/agent_schemasage.sh`, etc. Optional env flags:
   - `SKIP_AGENT_BOOTSTRAP=1` to stop scripts from installing lint/security tools.
   - `RUN_PERF_BUILD=1` to force PerfSmith to build the React bundle and run `source-map-explorer`.
4. Execute the full suite via `bash ci_workflows/run_agents_locally.sh`. The scripts populate `reports/` with:
   - Static analysis JSON (`lintguard_*.json`)
   - Database snapshots/logs (`schemasage_*.txt`, `db_audit.md`)
   - Performance notes (`perfsmith_hotspots.md`, optional bundle JSON)
   - Security findings (`shieldprobe_*.json`, `security_findings.json`)
   - Consolidated digest (`weekly_agent_digest.md`)

## CI Workflow Template
- `ci_workflows/agents-ci.yml` defines five jobs (LintGuard, SchemaSage, PerfSmith, ShieldProbe, AtlasReporter) plus artifact upload.
- To enable GitHub Actions, copy the file to `.github/workflows/agents.yml`, add `DATABASE_URL` to repository secrets, and ensure runners can reach any required databases.
- While running locally, you can trigger the same logic with tools like `act` by pointing to this YAML (`act -W ci_workflows/agents-ci.yml`).

## Reporting Expectations
- Commit generated reports only when needed for collaboration; otherwise add them to PR descriptions or release notes.
- Before merges touching authentication, payments, or database schema, rerun ShieldProbe + SchemaSage and attach the latest artifacts to `reports/weekly_agent_digest.md`.
- Keep this runbook updated when new agents, scripts, or environment prerequisites are introduced.
