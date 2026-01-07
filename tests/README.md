# Tests Folder (Current)

This `tests/` folder contains the **current** testing and evaluation artifacts for the Happy Place Webstore.

## Archive Policy

On **2025-12-19**, all files under `tests/` with a modified timestamp **before 2025-12-15** were **moved** (not deleted) into:

- `tests/test_bck/`

This was done to prevent stale scripts/logs/docs from being mistaken as current results.

### What was archived

- Older UAT docs and execution reports
- Older UAT scripts (`uat_*`)
- Historical `.log` outputs

### Where to find historical docs

- Previous docs and run logs are in `tests/test_bck/`

## Current Testing Baseline

- Authoritative documentation for the current test suite lives in:
  - `tests/UAT_TEST_DOCUMENTATION.md`

## Notes

- No test artifacts were deleted.
- If you need to restore any file to the active `tests/` directory, move it back from `tests/test_bck/`.
