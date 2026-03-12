---
phase: 63-full-generation-run
plan: "02"
subsystem: database
tags: [coupling-path-stats, calibration, 4j-detection, threshold-analysis]

# Dependency graph
requires:
  - phase: 63-full-generation-run
    plan: "01"
    provides: "coupling_path_stats table populated with 3,775,564 entries"
provides:
  - "calibration-results.md with full statistical analysis of coupling_path_stats data"
  - "Identified root cause: p_long_range metric is broken due to j5+ dominance"
  - "Documented architectural fix options for detection algorithm"
  - "Confirmed all 41 existing detection tests pass"
affects:
  - 64-uat
  - detection-engine
  - 4j-coupling-detection

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created:
    - .planning/phases/63-full-generation-run/calibration-results.md
  modified: []

key-decisions:
  - "Default thresholds (likely >= 0.50, possible >= 0.15) produce 100% false positive rate against real data — not changed because no threshold adjustment can fix the root cause"
  - "j5_plus dominates universally (67-90% of all pairs) making p_long_range = j4 + j5_plus useless as discriminator"
  - "Discrimination also fails for j4-only and conditional P(4J|2-4J) approaches due to broad HOSE code shift windows"
  - "Fix requires architectural change: either restrict shift window, use aromatic context indicator, or change metric to exclude j5_plus from denominator"

patterns-established: []

requirements-completed: [VAL-01]

# Metrics
duration: 45min
completed: 2026-03-12
---

# Phase 63 Plan 02: Threshold Calibration Summary

**Calibration reveals 100% false positive rate in 4J detection: p_long_range is not discriminating due to j5_plus dominance; architectural fix required before Phase 64 UAT**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-03-12T16:22:29Z
- **Completed:** 2026-03-12
- **Tasks:** 2/2 auto + Task 3 checkpoint
- **Files modified:** 1 (calibration-results.md created)

## Accomplishments

- Ran full statistical distribution analysis on 3,775,564 coupling_path_stats entries
- Validated ibuprofen 4J correlations (both return likely_4j — but only trivially due to global j5+ dominance)
- Discovered root cause: j5_plus (5+ bond paths) accounts for 67.5% of all observations and dominates ALL HOSE code pairs regardless of environment
- Confirmed 100% false positive rate: non-aromatic aliphatic pairs ALSO return likely_4j
- Tested 4 alternative metrics (p_long_range, j4-only, conditional P(4J|2-4J), normalized) — none discriminate
- All 41 existing detection tests pass (use synthetic controlled data, unaffected by production issue)
- Documented 4 architectural fix options with recommendation

## Task Commits

1. **Task 1: Analyze statistics distribution and validate ibuprofen 4J cases** - `03a2f5f` (chore)
2. **Task 2: Adjust thresholds if needed** - No code changes (defaults preserved; no threshold can fix root cause). Tests verified: 41/41 pass.

## Files Created/Modified

- `.planning/phases/63-full-generation-run/calibration-results.md` - Full calibration analysis (214 lines)

## Decisions Made

1. **Defaults not changed.** The default thresholds (likely >= 0.50, possible >= 0.15) technically satisfy the `must_haves` for the ibuprofen cases (both return likely_4j), but only trivially — ALL pairs return likely_4j. No threshold adjustment can fix this because the root cause is structural.

2. **Root cause identified:** `p_long_range = j4 + j5_plus` is broken because j5_plus is the "5 or more bonds" bucket and dominates universally in any medium-to-large molecule. The coupling_path_stats generator records ALL (carbon, proton-bearing-carbon) pairs including those 5+ bonds apart, so j5+ inflates to 67-90% for every HOSE code pair.

3. **Recommended fix (for Phase 64 prep):** Option C from calibration-results.md — use aromatic context as the discriminator. The 4J W-pathway problem in HMBC is fundamentally an aromatic ring problem. The most reliable indicator is the combination of: carbon_hose contains aromatic ring markers, h-carbon is in the benzylic shift range, and the pair is in the right topological relationship. This is a rule-based approach rather than a statistical threshold approach.

## Deviations from Plan

### Plan Expectation vs Reality

The plan assumed that threshold calibration against real data would yield either:
(a) confirmation that defaults work, or
(b) adjusted thresholds that work better.

The actual finding is (c): no threshold on the current metric works because the metric itself is fundamentally non-discriminating. This is a data-driven discovery, not a deviation — it's the correct result of the calibration task. The plan says "Threshold assessment: keep defaults or recommend changes" and we're recommending an architectural change.

**Action taken:** Documented the finding thoroughly in calibration-results.md. Defaults preserved (changing them would provide false confidence of a fix). Tests pass. Architecture change deferred to next phase.

None - plan executed exactly as written (calibration gave unexpected but valid result).

## Issues Encountered

**Fundamental metric design issue:** The `p_long_range = j4 + j5_plus` metric was designed before production data was available. It assumed j5_plus would be small for most HMBC correlations. In reality, because the generator records ALL atom pairs (not just HMBC-observable ones), j5_plus dominates universally. This was not apparent from synthetic test data.

The issue will need an architectural fix in the detection engine before Phase 64 UAT. See calibration-results.md Section 6 for options.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Calibration analysis complete and documented
- Database at data/reference/lucy-ng-derep.db is correct and ready for Figshare upload (data quality is good; the issue is in the detection algorithm, not the data)
- **Before Phase 64 UAT:** Detection algorithm needs architectural fix (see calibration-results.md Option C)
- Task 3 (Figshare upload) is a human checkpoint — see checkpoint details below

---

## Checkpoint: Task 3 — Figshare Upload

The database is ready for upload. To verify ibuprofen detection works (trivially at current thresholds):

```bash
lucy detect 4j 129.38 45.03 --db data/reference/lucy-ng-derep.db
lucy detect 4j 127.26 44.90 --db data/reference/lucy-ng-derep.db
```

Upload to Figshare as new version of DOI 10.6084/m9.figshare.31073554.

**Note:** Upload can be deferred until after the detection algorithm is fixed (Phase 64 prep), since users downloading now would get the broken default thresholds behavior.

## Self-Check: PASSED

- `.planning/phases/63-full-generation-run/calibration-results.md` - exists (created, 214 lines)
- Commit `03a2f5f` - exists in git log (chore: analyze coupling_path_stats)
- All 41 detection tests pass: confirmed `pytest tests/test_detection_4j.py -x -q`

---
*Phase: 63-full-generation-run*
*Completed: 2026-03-12*
