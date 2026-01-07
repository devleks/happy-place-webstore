# Agent Handoff Protocol (Initializer → Execution → Review)

This protocol standardizes how agents collaborate on changes in this repo.

## 1) Shared Definitions

- **Artifact:** the primary file(s) or area being changed (code, tests, docs)
- **State:** the baseline assumptions that must remain consistent during iterations
- **Change Record:** a human-readable record describing the diff and how to validate it
- **Checks:** commands or procedures that must pass for approval

## 2) Handoff Sequence

### A) Initializer Agent

Produces:

- Goal statement
- Scope boundaries
- Constraints
- Success criteria
- Checks (commands)
- Rollback strategy

Outputs are stored/updated as:

- `plan.md` (optional)
- `state.md` (recommended)

### B) Execution Agent

Produces:

- Code/test/doc changes
- Updates `change_record.md` (per iteration)

### C) Review/Validation Agent

Produces:

- Validation report
- If PASS: commits the change
- If FAIL: actionable feedback or rollback instruction

## 3) Required Files (when applicable)

- `state.md` — environment + baseline assumptions
- `change_record.md` — iteration notes + verification steps

## 4) Minimum Change Record Format

- Goal reference
- Files changed
- Summary of changes
- How to validate (exact commands)
- Risks

## 5) Notes

- Avoid destructive operations unless explicitly approved.
- Prefer isolated, reversible steps.
- If SSOT conflicts exist, reconcile or record under Known Inconsistencies.
