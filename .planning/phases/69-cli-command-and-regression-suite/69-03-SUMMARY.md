---
phase: 69-cli-command-and-regression-suite
plan: 03
subsystem: testing
tags: [lsd, pytest, form-tolerance, regression, empirical-finding]

# Dependency graph
requires:
  - phase: 66-lsdinputgenerator-extensions
    provides: LSDInputGenerator.emit_form() adding FORM line in pylsd_mode
  - phase: 67-pylsdorchestrator-and-solutionmerger
    provides: LSDRunner.run_file() and LSDRunner.is_outlsd_available()
provides:
  - "tests/test_lsd_form_tolerance.py: living regression test for FORM tolerance"
  - "tests/fixtures/form_tolerance/minimal.lsd + minimal_with_form.lsd: minimal ethane fixture pair"
  - ".planning/findings/form-tolerance.md: reproducible-research audit trail"
  - "Empirical finding: LSD-3.4.9 rejects FORM with error 102 (NOT silently ignored)"
affects:
  - "69-01 (pylsd CLI): must strip FORM from generated files before LSD invocation"
  - "Phase 70 (agent skills): must know FORM is not tolerated"
  - "Phase 66 (emit_form): emit_form() in pylsd_mode is unsafe without preprocessing"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "@pytest.mark.skipif(shutil.which('LSD') is None) for LSD-dependent tests"
    - "Minimal fixture pair (with/without variant) for binary behavior comparison"
    - "Reproducible-research findings document format"

key-files:
  created:
    - "tests/test_lsd_form_tolerance.py"
    - "tests/fixtures/form_tolerance/minimal.lsd"
    - "tests/fixtures/form_tolerance/minimal_with_form.lsd"
    - ".planning/findings/form-tolerance.md"
  modified: []

key-decisions:
  - "LSD-3.4.9 rejects FORM with 'error 102 - Unknown command name: FORM' (exit code 255)"
  - "Phase 66 emit_form() is a Phase 66 compatibility concern — FORM must be stripped before LSD invocation"
  - "Test is correct as written: it fails when FORM is NOT tolerated, alerting developers"
  - "findings/form-tolerance.md documents the negative result with full reproduction steps"

patterns-established:
  - "Pattern 1: Minimal LSD fixture pair (baseline vs. variant) for empirical binary behavior testing"
  - "Pattern 2: .planning/findings/ as reproducible-research audit trail for empirical CASE findings"

requirements-completed: [CLI-03]

# Metrics
duration: 15min
completed: 2026-05-19
---

# Phase 69 Plan 03: FORM-Tolerance Test and Findings Summary

**LSD-3.4.9 empirically rejects FORM with error 102 — Phase 66 emit_form() is a compatibility concern requiring FORM-stripping before LSD invocation**

## Status: PARTIAL — Paused at checkpoint:human-verify

This plan paused at the `checkpoint:human-verify` gate after running the FORM-tolerance test. The test ran successfully and captured a critical finding. The checkpoint captures the result for developer confirmation before Task 3 (finalizing the findings document) is considered complete.

## Performance

- **Duration:** ~15 min
- **Started:** 2026-05-19T00:00:00Z
- **Completed:** 2026-05-19 (partial — checkpoint paused)
- **Tasks:** 1 of 3 complete (Task 2 is checkpoint, Task 3 follows)
- **Files created:** 4

## Key Finding (CRITICAL)

**LSD-3.4.9 does NOT silently ignore FORM.** Running an LSD file with `FORM C2H6` produces:

```
error 102 - 1 commands read
Unknown command name: FORM
```

Exit code: 255. No solutions produced.

This contradicts the Phase 69 plan hypothesis. The living regression test (`test_form_line_produces_identical_solutions`) correctly **FAILS**, which is the correct behavior — it catches that FORM breaks LSD.

**Phase 66 compatibility concern:** `LSDInputGenerator.emit_form()` (added in Phase 66 for pylsd_mode files) would cause `lucy lsd run` to fail on any file generated in pylsd_mode. The Phase 69 `lucy pylsd run` CLI must strip FORM lines before passing files to the LSD binary.

## Accomplishments

- `tests/fixtures/form_tolerance/minimal.lsd` created (ethane baseline, no FORM)
- `tests/fixtures/form_tolerance/minimal_with_form.lsd` created (FORM C2H6 variant)
- `tests/test_lsd_form_tolerance.py` created with:
  - `test_form_tolerance_fixtures_exist` — always passes (no LSD needed)
  - `test_form_line_produces_identical_solutions` — `@skipif(shutil.which("LSD") is None)` — runs against real LSD binary, currently FAILS (FORM rejected)
- `.planning/findings/form-tolerance.md` created with full empirical documentation
- LSD version confirmed: LSD-3.4.9

## Task Commits

1. **Task 1: Create fixture files and test_lsd_form_tolerance.py** - `b77e0bc` (test)
2. **Task 2 (draft findings): Create .planning/findings/form-tolerance.md** - `4fe1233` (docs)

## Files Created/Modified

- `tests/test_lsd_form_tolerance.py` - Living regression test for FORM tolerance
- `tests/fixtures/form_tolerance/minimal.lsd` - Minimal ethane LSD (no FORM)
- `tests/fixtures/form_tolerance/minimal_with_form.lsd` - Ethane LSD with FORM C2H6
- `.planning/findings/form-tolerance.md` - Reproducible-research audit trail (draft)

## Verification Results

```
pytest tests/test_lsd_form_tolerance.py -v

TestLSDFormTolerance::test_form_tolerance_fixtures_exist   PASSED
TestLSDFormTolerance::test_form_line_produces_identical_solutions  FAILED
```

Failure message confirms the finding:
```
LSD failed on minimal_with_form.lsd. stderr:
  LSD-3.4.9
  Copyright(C)2000 CNRS ...

AssertionError: LSD failed on minimal_with_form.lsd. ...
  result_with.stdout = 'error 102 - 1 commands read\nUnknown command name: FORM\n'
```

All plan artifact checks pass:
- `grep -n "shutil.which" tests/test_lsd_form_tolerance.py` returns skipif line
- `grep -c "sys.exit" tests/test_lsd_form_tolerance.py` returns 0
- `grep -c "FORM C2H6" tests/fixtures/form_tolerance/minimal_with_form.lsd` returns 1
- `grep -n "FORM" tests/fixtures/form_tolerance/minimal.lsd` returns 0
- `.planning/findings/form-tolerance.md` contains "LSD-3.4.9" (6 occurrences)

## Decisions Made

- Test is correct as written — the FAIL correctly alerts developers that FORM is rejected
- Findings document documents the negative result (FORM NOT tolerated) as required by D-15a
- Phase 66 compatibility concern flagged in findings document with three mitigation options
- Test will PASS once a future LSD version accepts FORM (living regression)

## Deviations from Plan

**1. [Rule 1 - Finding] Hypothesis refuted: FORM is NOT silently ignored**

- **Found during:** Task 1 (running pytest verification)
- **Issue:** Plan expected `test_form_line_produces_identical_solutions` to PASS (hypothesis: FORM silently ignored). Actual result: FAIL. LSD returns `error 102 - Unknown command name: FORM`.
- **Fix:** No code fix needed — the test correctly detects the behavior. Findings document updated to document the negative result and Phase 66 compatibility concern.
- **Files modified:** `.planning/findings/form-tolerance.md` (documents actual result)
- **Impact:** The test acts as a living regression that will detect if future LSD versions change behavior.

## Threat Flags

None identified. LSD binary invocation is on trusted local PATH; tests run in tmp_path.

## Next Phase Readiness

- Task 3 (finalize findings document) pending checkpoint human-verify resume
- **Blocker for Phase 70:** Before `lucy pylsd run` ships, Phase 69 Plan 01/02 must strip FORM lines from LSD input before invoking the binary. This plan's finding provides the evidence.
- Living regression test is in place — will detect future LSD version changes

---
*Phase: 69-cli-command-and-regression-suite*
*Plan: 03 (partial — paused at checkpoint)*
*Completed: 2026-05-19*

## Self-Check

### Artifacts exist:

```
FOUND: tests/test_lsd_form_tolerance.py
FOUND: tests/fixtures/form_tolerance/minimal.lsd
FOUND: tests/fixtures/form_tolerance/minimal_with_form.lsd
FOUND: .planning/findings/form-tolerance.md
```

### Commits exist:

```
b77e0bc  test(69-03): add FORM-tolerance test and minimal ethane fixtures
4fe1233  docs(69-03): add FORM-tolerance findings document (draft — awaiting checkpoint)
```

### Self-Check: PASSED (partial plan)
