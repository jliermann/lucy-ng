---
phase: 73-solution-plumbing-fix
plan: "01"
subsystem: lsd-runner
tags: [tdd, bugfix, plumbing, outlsd, lsd-binary, runner, orchestrator]
dependency_graph:
  requires:
    - 69-cli-command-and-regression-suite  # regression baseline
    - 67-pylsdorchestrator-and-solutionmerger  # orchestrator.py
  provides:
    - lsd-plumbing-single-run-path  # D-01 primary path
  affects:
    - 74-constraint-preservation  # depends on clean single-run path
    - 76-ibuprofen-uat  # end-to-end CASE run
tech_stack:
  added:
    - _invoke_outlsd module-level helper in runner.py (shared with orchestrator)
  patterns:
    - file-argument LSD invocation (relative path + CWD management)
    - outlsd SMILES mode: [outlsd_path, "5"] with .sol as stdin
    - success flag requires .sol exists AND smiles_path is not None
key_files:
  created:
    - tests/fixtures/regression/ibuprofen_no_4j.lsd  # ported from Phase 69
    - tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt
    - src/lucy_ng/lsd/orchestrator.py  # ported from Phase 67
    - tests/test_lsd_regression.py  # ported from Phase 69
  modified:
    - src/lucy_ng/lsd/runner.py  # three bugs fixed
    - src/lucy_ng/lsd/orchestrator.py  # _run_outlsd delegates to shared helper
    - tests/test_lsd_runner.py  # TestLSDRunnerFixed class added
    - src/lucy_ng/cli/lsd.py  # _perform_ranking helper added
    - tests/test_lsd_regression.py  # Path A for fixed runner added
decisions:
  - "File-argument mode requires RELATIVE path: LSD-3.4.9 writes {stem}.sol only when given relative filename, not absolute path. Fix: copy input to output_dir, invoke as filename only."
  - "Regression test updated with Path A: fixed runner writes solutions.smi directly; test now checks for solutions.smi first before attempting stdout reconstruction."
  - "_invoke_outlsd placed at module level in runner.py; orchestrator imports and delegates — no duplicate logic."
metrics:
  duration_minutes: 11
  completed: "2026-05-21"
  tasks_completed: 3
  files_modified: 7
---

# Phase 73 Plan 01: LSD Runner Plumbing Fix Summary

Fixed three bugs in `src/lucy_ng/lsd/runner.py` so LSD solutions flow reliably from solver run to ranked SMILES — file-argument invocation, correct outlsd call with "5" argument, and proper success semantics.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| Prerequisites | Port files from master | d23f2e7 | orchestrator.py, test_lsd_regression.py, fixtures, cli/lsd.py |
| 1 (RED) | Write failing TestLSDRunnerFixed tests | 360b229 | tests/test_lsd_runner.py |
| 2 (GREEN) | Fix runner.py + orchestrator.py | a2b3a17 | runner.py, orchestrator.py, test_lsd_regression.py |
| 3 (Gate) | Full suite verification | a2b3a17 | (verification only) |

## Bugs Fixed

### Bug 1: _execute_lsd used stdin invocation (no .sol written)

**Before:** `subprocess.run([str(self.lsd_path)], input=input_file.read_text(), ...)`

**After:** Copy input file to output_dir; `subprocess.run([str(self.lsd_path), filename], cwd=output_dir, ...)`

LSD-3.4.9 writes `{stem}.sol` to CWD only when given a **relative** filename. With an absolute path, it runs but produces no .sol file. This was not in the original research and was discovered empirically during execution.

### Bug 2: _run_outlsd passed wrong input and missing "5" argument

**Before:** `subprocess.run([str(self.outlsd_path)], input=input_file.read_text(), ...)`

**After:** Delegated to `_invoke_outlsd(outlsd_path, sol_file, output_dir)` which calls `subprocess.run([str(outlsd_path), "5"], stdin=fh, ...)` where `fh` is the .sol file handle.

Without the "5" argument, outlsd prints a 10-line usage message. With the .lsd file as stdin instead of the .sol file, outlsd cannot parse the input. Both defects caused `outlsd.out` to contain usage text instead of SMILES.

### Bug 3: success was a false-positive

**Before:** `success = proc.returncode == 0 or solution_count > 0`

**After:** `success = sol_file.exists() and smiles_path is not None`

LSD always writes "N solutions found" to stderr regardless of invocation mode, so `solution_count > 0` was always True even when no .sol was written. The new semantics require both .sol presence AND successful SMILES conversion.

## Shared Helper

`_invoke_outlsd(outlsd_path, sol_file, output_dir)` is defined at module level in `runner.py`. Both `LSDRunner._run_outlsd` and `PyLSDOrchestrator._run_outlsd` import and call it. This eliminates the duplicate implementation that existed since Phase 67 (where orchestrator.py explicitly bypassed the buggy runner).

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED: test(73-01): failing tests | 360b229 | PASS — all 6 TestLSDRunnerFixed tests FAILED |
| GREEN: feat(73-01): fix runner | a2b3a17 | PASS — all 6 tests PASS |
| REFACTOR | n/a | No refactoring needed |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LSD absolute path does not produce .sol file**

- **Found during:** Task 2, first GREEN attempt
- **Issue:** The research documented that `lsd /absolute/path/compound.lsd` with `cwd=output_dir` writes `compound.sol` to `output_dir`. Empirically on this LSD-3.4.9 installation, the absolute path form does NOT write a .sol file — only the relative filename form does.
- **Fix:** Added logic to copy the input file to output_dir when it's not already there, then invoke LSD with just the filename (relative path in CWD=output_dir).
- **Files modified:** `src/lucy_ng/lsd/runner.py` (_execute_lsd)
- **Commit:** a2b3a17

**2. [Rule 1 - Bug] Regression test failed after fix due to Path A not handled**

- **Found during:** Task 3 verification
- **Issue:** `test_lsd_regression.py` was written for the stdin-mode behavior. After the fix, `result.stdout` still contains the 9-line header summary (but no OUTLSD data). The test's `if result.stdout.strip()` branch ran, found no OUTLSD marker, and tried to pipe the header to `outlsd 5` — which failed with exit code 1.
- **Fix:** Added Path A check: if `solutions.smi` exists in tmp_path (written by the fixed runner), use it directly and skip the reconstruction workarounds.
- **Files modified:** `tests/test_lsd_regression.py`
- **Commit:** a2b3a17

**3. [Rule 3 - Blocker] Worktree missing Phase 67/69 files**

- **Found during:** Initial setup
- **Issue:** Worktree was branched from a pre-Phase 67 commit. `orchestrator.py`, `test_lsd_regression.py`, and regression fixtures were missing. The plan's imports and tests required these files.
- **Fix:** Ported the files from the main repo (master). Added `_perform_ranking` helper to `cli/lsd.py` (needed for `test_lsd_rank_end_to_end`).
- **Files modified:** orchestrator.py, test_lsd_regression.py, fixtures, cli/lsd.py
- **Commit:** d23f2e7

## Verification Results

```
pytest tests/test_lsd_runner.py::TestLSDRunnerFixed -v
→ 6 passed

pytest tests/test_lsd_regression.py -v
→ 3 passed (test_ibuprofen_no_4j_inchi_set_stable: 392-InChI set stable)

pytest -q
→ 862 passed, 14 skipped, 0 failed, 31 warnings
```

## Phase Gate Checks (all TRUE)

1. `grep "str(self.lsd_path).*lsd_input_name" runner.py` — matches line 251
2. `grep "input=input_file.read_text()" runner.py` — 0 matches (removed)
3. `grep '"5"' runner.py` — matches line 35 in _invoke_outlsd
4. `grep "_invoke_outlsd" orchestrator.py` — import at line 31, delegation at line 274
5. `grep "sol_file.exists()" runner.py` — in success computation at line 283
6. Phase 69 regression: 3/3 passed
7. Full suite: 862 passed, 0 failed

## Known Stubs

None. All outputs are wired to real data.

## Threat Flags

None. No new network endpoints, auth paths, or schema changes introduced.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| src/lucy_ng/lsd/runner.py | FOUND |
| src/lucy_ng/lsd/orchestrator.py | FOUND |
| tests/test_lsd_runner.py | FOUND |
| tests/test_lsd_regression.py | FOUND |
| tests/fixtures/regression/ibuprofen_no_4j.lsd | FOUND |
| tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt | FOUND |
| .planning/phases/73-solution-plumbing-fix/73-01-SUMMARY.md | FOUND |
| Commit d23f2e7 (prerequisites) | FOUND |
| Commit 360b229 (RED tests) | FOUND |
| Commit a2b3a17 (GREEN fix) | FOUND |
| 9/9 TestLSDRunnerFixed + regression tests pass | PASS |
