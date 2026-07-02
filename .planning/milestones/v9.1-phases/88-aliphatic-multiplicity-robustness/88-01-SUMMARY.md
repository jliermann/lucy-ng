---
phase: 88-aliphatic-multiplicity-robustness
plan: 01
subsystem: cli
tags: [nmr, hsqc, multiplicity-editing, peak-picking, click, numpy]

# Dependency graph
requires:
  - phase: 81-fix08-peakpicking
    provides: the pick_1d negative_detected detector (np.min < -0.05*max_abs) ported here
provides:
  - "lucy pick hsqc --format json reports a deterministic multiplicity_edited boolean (+ negative_crosspeak_count)"
  - "pure _detect_multiplicity_edited(data) -> (bool, int) helper in cli/pick.py for direct reuse"
affects: [88-02, 88-03, 89-blind-uat]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deterministic HSQC multiplicity-editing detection via negative-intensity reduction (no LLM judgment)"
    - "Empty/zero-data degrade-to-safe-default guard mirroring _compute_2d_noise_sigma"

key-files:
  created: []
  modified:
    - src/lucy_ng/cli/pick.py
    - tests/test_cli_pick.py

key-decisions:
  - "Factored the 3-line detector into a pure helper _detect_multiplicity_edited(data) so the True case and empty-data degrade case are unit-testable without a Bruker fixture (plan approach (b))"
  - "Did NOT add the optional sample_spectrum_2d_edited conftest fixture — approach (b) tests the helper with an inline ndarray, making the conftest change unnecessary"

patterns-established:
  - "MULT-04 detection basis: a multiplicity-edited HSQC has phased CH2 cross-peaks of opposite sign => genuine negative intensity below -0.05*max_abs; no negatives => NOT edited => sign-ambiguous"

requirements-completed: [MULT-04]

# Metrics
duration: 6min
completed: 2026-06-25
---

# Phase 88 Plan 01: Aliphatic Multiplicity Robustness (HSQC editing detector) Summary

**`lucy pick hsqc --format json` now reports a deterministic `multiplicity_edited` boolean (+ `negative_crosspeak_count`), ported verbatim from the proven 1D `negative_detected` detector, with an empty-data safe-default guard.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-25T09:46Z
- **Completed:** 2026-06-25T09:52Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added a pure helper `_detect_multiplicity_edited(data) -> (bool, int)` to `cli/pick.py`, mirroring the pick_1d detector `np.min(data) < -0.05 * max_abs` and counting negative cross-peaks via `np.count_nonzero`.
- Wired `multiplicity_edited` and `negative_crosspeak_count` into the `pick hsqc --format json` output (and an edited/not-edited note in the text branch); `pick_2d`/`pick_hmbc` untouched.
- Empty/all-zero `spectrum.data` degrades to the safe default `(False, 0)` without calling `np.min` (T-88-01), mirroring the `_compute_2d_noise_sigma` `data.size == 0` guard.
- Verified the in-repo non-edited HSQC `data/Ibuprofen/6` reports `multiplicity_edited: false`, `negative_crosspeak_count: 0`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add multiplicity_edited detector to pick hsqc JSON output** - `e747531` (feat)
2. **Task 2: Unit tests — true (synthesized) / false (in-repo) / zeros (safe default)** - `c0dfe3b` (test)

_TDD note: RED was established before implementation by confirming `multiplicity_edited` was absent from the pre-change JSON; GREEN reached after the Task 1 edit; tests added in Task 2 pin the behavior._

## Files Created/Modified
- `src/lucy_ng/cli/pick.py` - New pure helper `_detect_multiplicity_edited`; `multiplicity_edited` + `negative_crosspeak_count` surfaced in `pick_hsqc` JSON and noted in its text branch.
- `tests/test_cli_pick.py` - Added `test_pick_hsqc_not_multiplicity_edited` (CLI False/0 on `data/Ibuprofen/6`) and a `TestDetectMultiplicityEdited` class (`_true`, `_false_on_zeros`, `_empty`).

## Decisions Made
- **Pure-helper approach (b):** Factored the detector into `_detect_multiplicity_edited` so the True case (synthesized negative cross-peak ndarray) and the empty/zero degrade case are deterministically unit-testable without needing a Bruker-readable edited-HSQC fixture (none exists in-repo).
- **conftest fixture skipped:** The plan listed `tests/conftest.py` in `files_modified` and offered an optional `sample_spectrum_2d_edited` fixture, but approach (b) tests the helper directly with an inline ndarray, so no conftest change was required. This is the plan's preferred path ("Choose approach (b)").
- **Added a 4th test** (`test_detect_multiplicity_edited_empty`) beyond the plan's required 3, explicitly pinning the `np.empty((0,0))` `data.size == 0` branch of T-88-01.

## Deviations from Plan

None affecting code behavior — plan executed as written. Two scope notes (both anticipated by the plan):
- `tests/conftest.py` was NOT modified (approach (b) made the optional fixture unnecessary; the plan sanctioned this choice).
- One extra empty-array test was added for full T-88-01 coverage.

## Issues Encountered
- mypy flagged `np.ndarray` (bare generic) on the new helper signature. Resolved by adopting the codebase convention `"np.ndarray[Any, Any]"` (matching `_compute_2d_noise_sigma`) and importing `Any`. mypy now reports no errors on `pick.py`.
- ruff reported 2 `E501` long-line warnings in `pick.py` — confirmed pre-existing (identical count before/after via `git stash`), so this is clean-delta on the touched file.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- MULT-04 detection basis is delivered and unit-tested (true/false/zeros/empty). Plans 88-02/88-03 (skill-level wiring of the multiplicity-family enumeration + clean-but-wrong guardrail) can consume the `multiplicity_edited` JSON field.
- The functional validation of the full MULT fix is the Phase 89 blind CASE4 UAT (UAT-01), per the roadmap.

## Self-Check: PASSED
- src/lucy_ng/cli/pick.py: FOUND
- tests/test_cli_pick.py: FOUND
- Commit e747531: FOUND
- Commit c0dfe3b: FOUND

---
*Phase: 88-aliphatic-multiplicity-robustness*
*Completed: 2026-06-25*
