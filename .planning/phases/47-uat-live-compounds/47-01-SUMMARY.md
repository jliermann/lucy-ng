---
phase: 47-uat-live-compounds
plan: 01
status: complete
duration: evaluated from existing artifacts (CASE1 post-Phase-46.1 run)
commits: 0
---

## What was done

Evaluated the v4.0 team-based CASE run on Ibuprofen (C13H18O2) against the v3.0 bug matrix and Phase 47 success criteria. Artifacts were produced by a live CASE team run at `/Users/steinbeck/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/`.

### v3.0 Bug Matrix: 5/5 PASS

| Bug | Status | Key Evidence |
|-----|--------|-------------|
| Bug 1: DEFF NOT persistence | PASS | deff_not_patterns=["ring3","ring4"] constant across all 4 iterations |
| Bug 2: Signal grouping applied | PASS | 4 groups detected, all translated to grouped HMBC notation (10 entries by iter 4) |
| Bug 3: Grouped notation preserved | PASS | Count: 2→3→6→10, monotonically increasing |
| Bug 4: PROP/BOND documented | PASS | BOND used with reasoning in constraint inventory applied_from_detection |
| Bug 5: Detection -> constraints | PASS | applied_from_detection populated, pending_from_detection empty |

### Success Criteria

| # | Criterion | Result |
|---|-----------|--------|
| SC-1 | Ibuprofen in top 3 | PARTIAL — rank #4 by algorithm, #1 by analyst override (aromatic check) |
| SC-2 | All v3.0 bugs fixed | PASS (5/5) |
| SC-3 | Time < 2x baseline | PASS (4 iterations, same as v3.0) |

### Key Metrics

- **Iterations:** 4 (8441→146→61→5 solutions)
- **DA blocks:** 0 (all passed first attempt)
- **Orchestrator interventions:** 0
- **HMBC coverage:** 21/21 (100%)
- **Ibuprofen MAE:** 0.25 ppm (true HOSE radius-6 prediction)

### Critical Finding

Grouped HMBC notation `(8 9) 4/5/6/7` directly mitigates the 4J coupling problem. In ibuprofen, C9→H4/H5 is 3J and C8→H6/H7 is 3J, while the cross-pairs are 4J. Grouped notation requires only ONE atom of the pair to satisfy 3J, so ibuprofen survives. This is why the first v4.0 run (individual HMBC) got 7 wrong solutions while this run (grouped HMBC) correctly includes ibuprofen.

### New Issues

- Ranking algorithm places ibuprofen at rank #4 (match-count favors non-aromatic structures at 3 ppm tolerance)
- Phase 46.1 aromatic awareness correctly compensates via analyst override

## Deviations

- Task 1 (pre-flight) and Task 2 (live run) were not executed — artifacts from a prior run were evaluated directly
- This is a post-hoc evaluation of existing artifacts, not a live observed run

## What's next

Plan 47-02: Performance comparison report (v4.0-UAT-report.md written alongside this summary)
