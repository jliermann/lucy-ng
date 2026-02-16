---
phase: 38-two-tier-ranking-and-badlist
plan: 01
subsystem: ranking
tags: [ranking, hallucination-prevention, tdd, hose, transparency]

# Dependency graph
requires:
  - phase: 27-33
    provides: SolutionRanker with MAE-based ranking
  - phase: 16-19
    provides: HOSE-based C13 prediction with radius_used and confidence
provides:
  - Two-tier ranking (match count primary, MAE secondary)
  - HOSE radius transparency in ranking output via ShiftAssignment.radius_used
  - Hallucination prevention test suite
  - CLI match count display in text output
affects:
  - 39-statistical-constraints-integration
  - 40-ibuprofen-validation

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Two-tier ranking: sort by (-matched_count, mae) prevents hallucinations"
    - "TDD with mock predictors for controlled match/MAE scenarios"

key-files:
  created: []
  modified:
    - src/lucy_ng/ranking/ranker.py
    - src/lucy_ng/ranking/models.py
    - src/lucy_ng/cli/lsd.py
    - tests/test_ranking.py

key-decisions:
  - "Sort key (-matched_count, mae) makes signal coverage primary ranking criterion"
  - "ShiftAssignment carries radius_used/confidence from PredictedShift for transparency"
  - "Hallucination test uses ghost carbons (predictions in gaps) for realistic scenario"
  - "CLI text output shows Matched=N/M alongside MAE for user visibility"

patterns-established:
  - "TDD pattern: RED phase with hallucination scenario, GREEN with sort key fix"
  - "Match count prioritization: solutions with more matched signals rank higher regardless of MAE"
  - "Radius transparency: JSON output includes which HOSE radius predicted each carbon"

# Metrics
duration: 24min
completed: 2026-02-11
---

# Phase 38 Plan 01: Two-Tier Ranking Summary

**Match count primary ranking with MAE tiebreaker prevents ibuprofen-style hallucinations where wrong structures with lower MAE outranked correct solutions with better signal coverage**

## Performance

- **Duration:** 24 min
- **Started:** 2026-02-11T14:42:53Z
- **Completed:** 2026-02-11T15:06:53Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- Two-tier ranking implemented: solutions sorted by (-matched_count, mae)
- Hallucination prevention test passes: CORRECT (13/13, MAE=1.71) now ranks above WRONG (11/13, MAE=0.72)
- ShiftAssignment extended with radius_used and confidence fields for HOSE transparency
- CLI text output shows "Matched=N/M MAE=X.XX ppm" per solution
- All docstrings updated to describe two-tier ranking behavior

## Task Commits

Each task was committed atomically following TDD pattern:

1. **Task 1: Write failing tests (RED)** - `b0d54f0` (test)
   - TestTwoTierRanking class with 4 test cases
   - test_hallucination_prevention_ibuprofen_style simulates real failure (WRONG has lower MAE but fewer matches)
   - Current sort (mae, -matched_count) causes test to FAIL as expected

2. **Task 2: Fix sort order and update docstrings (GREEN)** - `5c511fc` (feat)
   - Changed sort key from `(r.mae, -r.matched_count)` to `(-r.matched_count, r.mae)`
   - Updated ranker.py, models.py docstrings to describe two-tier ranking
   - Updated CLI text output to show "Matched=N/M" per solution
   - All tests pass including hallucination prevention

3. **Task 3: Add radius_used and confidence to ShiftAssignment** - `adf1bf7` (feat)
   - Added radius_used: int | None field to ShiftAssignment
   - Added confidence: float | None field to ShiftAssignment
   - Propagated pred.radius_used and pred.confidence in ranker._match_shifts()
   - JSON output now includes HOSE radius per assignment (RANK-05)

## Files Created/Modified

- `src/lucy_ng/ranking/ranker.py` - Changed sort key to (-matched_count, mae), updated docstrings, propagate radius_used
- `src/lucy_ng/ranking/models.py` - Updated RankingResult docstring, added radius_used/confidence to ShiftAssignment
- `src/lucy_ng/cli/lsd.py` - Updated text output format to show "Matched=N/M"
- `tests/test_ranking.py` - Added TestTwoTierRanking with 4 comprehensive test cases

## Decisions Made

1. **Sort key order:** Used `(-matched_count, mae)` to make signal coverage the primary criterion
   - Rationale: Ibuprofen failure showed wrong structures can have lower MAE through ghost carbons
   - Match count is more reliable indicator of structural correctness

2. **Hallucination test design:** Used "ghost carbons" (predictions in gaps between experimental peaks) for realistic scenario
   - WRONG: 11 matched with very low errors (~0.2 ppm) + 2 ghost carbons with moderate errors (~5 ppm) → MAE=0.72
   - CORRECT: 13 matched with larger errors (2.0-2.5 ppm) → MAE=1.71
   - This mirrors real ibuprofen failure where cyclohexadiene solutions had better MAE but missing aromatic carbons

3. **Transparency via radius_used:** Propagated HOSE radius to ShiftAssignment for ranking output
   - Rationale: Enables diagnostic analysis of which predictions used fallback to higher radii
   - JSON output includes radius per assignment for CASE agent analysis

4. **CLI display format:** Added "Matched=N/M" before MAE in text output
   - Rationale: Users need to see signal coverage immediately, not just MAE
   - Format: "Solution 1: Matched=13/13 MAE=2.13 ppm (Good)"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - TDD pattern worked smoothly with RED phase confirming broken sort, GREEN phase fixing it.

## Next Phase Readiness

- Two-tier ranking complete (RANK-01, RANK-02)
- HOSE radius transparency complete (RANK-05)
- Ready for Phase 38-02 (badlist documentation)
- Ready for Phase 39 (statistical constraints integration with CASE agent)
- Ibuprofen validation (Phase 40) will verify hallucination prevention on real data

---
*Phase: 38-two-tier-ranking-and-badlist*
*Completed: 2026-02-11*
