# change_record.md — Current Instance UAT Suite

## Iteration 1 — Establish new post-archive UAT runner

### Summary

Created a new, post-archive UAT runner under `tests/` to replace older scripts stored in `tests/test_bck/`.

### Files

- `tests/plan.md`
- `tests/state.md`
- `tests/change_record.md`
- `tests/uat_current_helpers.sh`
- `tests/uat_current_tests.sh`

### Validation

- Run: `bash tests/uat_current_tests.sh`

### Notes / Risks

- If authenticated endpoints fail with `401` after successful login, treat as auth regression.
- Fulfillment role endpoints (packer/shipper) are not validated unless role credentials exist.
