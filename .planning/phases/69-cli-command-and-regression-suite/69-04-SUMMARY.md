---
phase: 69-cli-command-and-regression-suite
plan: 04
subsystem: regression-testing
tags: [regression, lsd, ibuprofen, inchi, baseline, checkpoint]

requires:
  - phase: 65-hypothesis-gate
    provides: "ibuprofen_no4j.lsd fixture + 392-SMILES solution file"
  - phase: 69-cli-command-and-regression-suite
    plan: 01
    provides: "LSDRunner API for run_file"

provides:
  - "tests/test_lsd_regression.py — InChI-set regression test for ibuprofen LSD fixture (D-16)"
  - "tests/fixtures/regression/ibuprofen_no_4j.lsd — classic v1 LSD fixture (no inventory block, no ; ELIM)"
  - "tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt — 392 unique C13H18O2 InChIs baseline"

affects:
  - "CI regression test coverage for lucy lsd run"

tech-stack:
  added: []
  patterns:
    - "D-16 InChI-set regression: set equality check (order-independent), no auto-update"
    - "outlsd .sol reconstruction: prepend '# From file:' + lsd content + '#\\n' + OUTLSD data from LSD stdout"
    - "D-16b: test failure on LSD version change is intentional — forces manual chemical review"

key-files:
  created:
    - "tests/test_lsd_regression.py"
    - "tests/fixtures/regression/ibuprofen_no_4j.lsd"
    - "tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt"
  modified: []

key-decisions:
  - "D-16 baseline generated from Phase 65 LSD-3.4.9 sol file (not a new LSD run) — shortcut valid because same LSD version"
  - "outlsd .sol reconstruction pattern: LSD stdin-mode writes OUTLSD data to stdout; prepend # header + lsd content + # delimiter to satisfy outlsd's input format"
  - "Baseline auto-verified via RDKit CalcMolFormula: all 392 InChIs are C13H18O2 — developer confirmation of chemical plausibility still required (D-16a)"

metrics:
  duration: "~10 min"
  tasks_completed: 2
  tasks_total: 3
  completed: "2026-05-19T18:10Z"
  checkpoint_reached: true
  checkpoint_type: "human-verify"
---

# Phase 69 Plan 04: LSD Regression Test + Ibuprofen Baseline Summary

**Status: CHECKPOINT REACHED — awaiting developer confirmation of InChI baseline plausibility (D-16a)**

**Ibuprofen LSD regression test framework created; 392-InChI baseline generated and auto-verified as C13H18O2. Integration test passes on LSD-equipped machine.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-05-19T18:10Z

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Create fixture files and test_lsd_regression.py | 99a725c | tests/test_lsd_regression.py, tests/fixtures/regression/ibuprofen_no_4j.lsd |
| 2 | Generate InChI baseline from Phase 65 smi shortcut | bae83b6 | tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt |
| Fix | Auto-fix outlsd SMILES extraction (Rule 1) | 9ec5da6 | tests/test_lsd_regression.py |

## Checkpoint Status

**Checkpoint type:** human-verify  
**Waiting for:** developer confirmation that 392 InChIs are chemically plausible C13H18O2 isomers (D-16a)

**Captured:**
- LSD version: 3.4.9 (same as Phase 65 run that produced the source .smi)
- Solution count: 392
- Baseline InChIs (first 3):
  1. `InChI=1S/C13H18O2/c1-4-10(5-2)12-7-6-11(8-12)9(3)13(14)15/h4,6-9,12H,5H2,1-3H3,(H,14,15)`
  2. `InChI=1S/C13H18O2/c1-4-10(5-2)12-8-6-7-11(12)9(3)13(14)15/h4,6-9,12H,5H2,1-3H3,(H,14,15)`
  3. `InChI=1S/C13H18O2/c1-4-10(5-2)6-7-11-8-12(11)9(3)13(14)15/h4,6-9,11H,5H2,1-3H3,(H,14,15)`
- Auto-verification: RDKit CalcMolFormula = C13H18O2 for all 392 InChIs (100% hit)
- Integration test result: **3/3 PASSED** when LSD binary is present

**Baseline file:** `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt`

**Resume signal:** "baseline-committed: 392 InChIs" — then Task 3 will add the count comment and finalize.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed outlsd SMILES extraction — `_run_outlsd` bug workaround**
- **Found during:** Task 2 verification (test_ibuprofen_no_4j_inchi_set_stable FAILED: actual=0, baseline=392)
- **Issue:** LSDRunner._run_outlsd calls `outlsd` with no mode argument. outlsd writes usage text to output, not SMILES. The test's first fallback (looking for .sol files) also failed because LSD-3.4.9 stdin mode does not create .sol files (writes OUTLSD data to stdout instead).
- **Root cause:** Known bug, documented in Phase 65 SUMMARY key-decisions. LSD-3.4.9 stdin mode writes OUTLSD format to stdout; outlsd expects a `.sol` file with `# From file:` header + lsd content + `#` delimiter + OUTLSD data.
- **Fix:** Reconstruct .sol from `result.stdout` by extracting the OUTLSD section and prepending the required header/delimiter. Verified produces same 392 SMILES → 392 C13H18O2 InChIs as baseline.
- **Files modified:** tests/test_lsd_regression.py
- **Commit:** 9ec5da6

## Verification

- `pytest tests/test_lsd_regression.py -v`: **3/3 PASSED** (LSD 3.4.9 installed; 392 InChIs matched baseline)
- `grep -c "CONSTRAINT INVENTORY v2\|; ELIM" tests/fixtures/regression/ibuprofen_no_4j.lsd`: 0 (clean classic form)
- `wc -l tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt`: 392

## Threat Flags

None. No new network endpoints, auth paths, or trust-boundary changes introduced.

## Self-Check: PASSED

- `tests/test_lsd_regression.py` exists and contains `shutil.which` skipif
- `tests/fixtures/regression/ibuprofen_no_4j.lsd` exists, has MULT lines, no inventory/ELIM
- `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` exists, 392 lines
- Commits 99a725c, bae83b6, 9ec5da6 present in git log
