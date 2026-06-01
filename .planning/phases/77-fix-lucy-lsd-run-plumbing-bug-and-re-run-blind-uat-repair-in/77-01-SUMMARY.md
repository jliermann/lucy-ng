---
phase: 77
plan: 01
subsystem: lsd-runner
tags: [fix, regression-test, outlsd, filter-files, fail-loud, tdd]
dependency_graph:
  requires: []
  provides: [FIX-01]
  affects: [src/lucy_ng/lsd/runner.py, tests/test_lsd_runner.py]
tech_stack:
  added: []
  patterns: [RuntimeError-propagation, importlib.resources-bundled-files, monkeypatch-subprocess]
key_files:
  created:
    - tests/fixtures/regression/arm_a_ring_excl.lsd
  modified:
    - src/lucy_ng/lsd/runner.py
    - tests/test_lsd_runner.py
decisions:
  - "Unconditional filter-file copy in _execute_lsd (matches write_file() behavior, idempotent)"
  - "RuntimeError raised (not returned None) for all three known-bad outlsd output cases: empty, error string, outlsd:-prefixed"
  - "Pre-existing mypy error at runner.py line 151 (self.lsd_path assignment) is out of scope — confirmed pre-existing by git stash verification"
metrics:
  duration_seconds: 170
  completed_date: "2026-06-01"
  tasks_completed: 2
  files_modified: 3
---

# Phase 77 Plan 01: Fix _execute_lsd Filter-File Copy + Harden _invoke_outlsd Fail-Loud Summary

**One-liner:** `_execute_lsd` now copies bundled ring3/ring4 filter files to output_dir (FIX-01A) and `_invoke_outlsd` raises `RuntimeError` on empty/error/non-SMILES output instead of writing garbage to solutions.smi (FIX-01B).

## What Was Built

### FIX-01A: Filter-file copy in `_execute_lsd`

Added one call after the existing `shutil.copy2` block in `LSDRunner._execute_lsd()`:

```python
# Copy bundled ring3/ring4 filter files so DEFF F1 "ring3" / DEFF F2 "ring4" resolve.
# Unconditional — matches write_file() behavior; idempotent if already present.
LSDInputGenerator._write_filter_files(output_dir)
```

This mirrors the behavior of `LSDInputGenerator.write_file()` which already calls `_write_filter_files()`. The `run_file()` path (calling `_execute_lsd` directly) was the missing case.

### FIX-01B: Fail-loud validation in `_invoke_outlsd`

Replaced the false-positive `if proc.stdout.strip()` check with three explicit guards:

1. Empty output → `RuntimeError("outlsd produced no output — ...")`
2. `"This is not a file for OUTLSD"` in stdout → `RuntimeError("outlsd rejected .sol file: ...")`
3. stdout starting with `"outlsd:"` → `RuntimeError("outlsd error: ...")`

Added `except RuntimeError: raise` before `except Exception: pass` so fail-loud errors propagate to `_execute_lsd`'s outer `except Exception` handler, which converts them to `LSDResult(success=False, stderr=str(e))`.

### Regression Tests

- `tests/fixtures/regression/arm_a_ring_excl.lsd`: copy of `arm_a.lsd` with DEFF paths changed from absolute to relative (`"ring3"` / `"ring4"`). Produces exactly 2 aromatic solutions when filter files are correctly deployed.
- `TestInvokeOutlsd` class: two unit tests (no LSD/outlsd needed):
  - `test_fail_loud_on_error_string`: monkeypatches subprocess.run, asserts `RuntimeError` matching `"This is not a file for OUTLSD"`
  - `test_fail_loud_on_empty_output`: monkeypatches subprocess.run, asserts `RuntimeError` matching `"no output"`
- `test_ring_exclusion_lsd_produces_smiles`: integration test (skipif LSD absent) that runs `LSDRunner().run_file()` on the new fixture, asserts solutions.smi exists with exactly 2 lines of valid SMILES with >= 6 aromatic atoms each.

## Verification Gate Results

| Check | Result |
|-------|--------|
| `pytest tests/test_lsd_runner.py -q --tb=short` | 27 passed |
| `grep -n "LSDInputGenerator._write_filter_files" runner.py` | line 270 (inside _execute_lsd) |
| `grep -n "This is not a file for OUTLSD" runner.py` | line 49 (inside _invoke_outlsd) |
| `grep -n "except RuntimeError" runner.py` | line 61 (RuntimeError re-raised) |
| `grep -c 'DEFF F1 "ring3"' arm_a_ring_excl.lsd` | 1 |
| `grep -v "^;" arm_a_ring_excl.lsd \| grep -c "steinbeck"` | 0 (no absolute paths) |
| `ruff check src/lucy_ng/lsd/runner.py` | All checks passed |
| `mypy src/lucy_ng/lsd/runner.py` (runner.py errors only) | 1 pre-existing error (out of scope) |

## Deviations from Plan

### Pre-existing mypy error (out of scope — not fixed)

**Found during:** Task 2 verification
**Issue:** `mypy src/lucy_ng/lsd/runner.py` reports 1 error at line 151 (`self.lsd_path = self._find_lsd()` — `Path | None` vs `Path`). This was confirmed pre-existing via `git stash` verification (existed at commit 7ca55f6 before Task 2 edits, originally at line 133).
**Action:** Not fixed (out of scope per deviation rules — pre-existing, not caused by this plan's changes).
**Documented in:** deferred-items.md (not blocking).

All other checks pass cleanly.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED: failing tests written | 7ca55f6 | PASS — TestInvokeOutlsd FAILED before fix |
| GREEN: implementation makes tests pass | e23cc3a | PASS — all 27 tests pass |
| REFACTOR | n/a | No refactor needed |

## Known Stubs

None — all implemented behavior is wired end-to-end.

## Threat Flags

No new threat surfaces introduced beyond those documented in plan threat model. T-77-01-01 mitigated by FIX-01B fail-loud implementation.

## Self-Check: PASSED

- `tests/fixtures/regression/arm_a_ring_excl.lsd`: FOUND
- `src/lucy_ng/lsd/runner.py`: FOUND (modified)
- `tests/test_lsd_runner.py`: FOUND (modified)
- Commit `7ca55f6` (RED): FOUND
- Commit `e23cc3a` (GREEN): FOUND
