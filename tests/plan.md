# plan.md — Current Instance UAT + Evaluations

## Goal

Create a **fresh, post-archive** UAT/evaluation suite that:

- Targets the **current backend API routes** (no stale endpoints).
- Covers the critical journeys:
  - Customer (cart → order)
  - Admin (dashboard metrics + order tracking)
  - Employee/POS (shift + transaction + receipts)
- Produces timestamped outputs suitable for Review/Validation gating.

## Scope

- **In scope:** API-level UAT via bash + curl.
- **Out of scope (for this first runner):** UI/E2E browser automation; deep fulfillment role testing (packer/shipper) unless dedicated credentials are available.

## Deliverables

- `tests/state.md`
- `tests/change_record.md`
- `tests/uat_current_helpers.sh`
- `tests/uat_current_tests.sh`

## Acceptance Criteria

- Running `bash tests/uat_current_tests.sh` returns exit code:
  - `0` when all mandatory tests pass.
  - non-zero when any mandatory test fails.
- Script uses only:
  - `bash`, `curl`, `python3`
  - (no `jq` dependency)

## Checks (Review/Validation Gate)

### Mandatory

- `bash tests/uat_current_tests.sh`

### Optional (CI co-workers)

- `bash ci_workflows/agent_lintguard.sh`
- `RUN_PERF_BUILD=0 bash ci_workflows/agent_perfsmith.sh`
- `bash ci_workflows/agent_shieldprobe.sh`
- `bash ci_workflows/agent_atlasreporter.sh`

## Preconditions

- Backend running at `http://127.0.0.1:5001` (default)
- Seed/test credentials exist:
  - `admin@happyplace.co.ke / admin123`
  - `manager@happyplace.co.ke / manager123`

## Notes

- If any authenticated endpoint fails with 401 after successful login, treat as a **P0** authentication regression.
