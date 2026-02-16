---
phase: 38-two-tier-ranking-and-badlist
plan: 02
subsystem: documentation
tags: [lsd, ranking, badlist, case-agent, strained-rings]

# Dependency graph
requires:
  - phase: 38-01
    provides: Implementation of two-tier ranking algorithm in CLI
provides:
  - CASE agent knowledge with badlist filter patterns for LSD file generation
  - Documentation of two-tier ranking algorithm for users
  - Guidance on epoxide exception handling
affects: [39-statistical-constraints-integration, 40-ibuprofen-validation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Badlist filters (DEFF NOT) for excluding strained rings in natural products
    - Two-tier ranking interpretation (match count priority over MAE)

key-files:
  created: []
  modified:
    - ~/.claude/agents/lucy-case-agent.md
    - CLAUDE.md

key-decisions:
  - "8 DEFF NOT patterns cover all common strained ring motifs (3- and 4-membered)"
  - "Epoxide exception documented with specific shift range (45-55 ppm) and formula requirements"
  - "Two-tier ranking prioritizes signal match count over MAE to prevent wrong structures with coincidentally low errors"

patterns-established:
  - "Badlist section added to Manual File Construction Checklist (item 8)"
  - "Ranking interpretation explains BOTH metrics (match count and MAE) must be reported"

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 38 Plan 02: Badlist Documentation and Ranking Guidance Summary

**8 DEFF NOT patterns exclude strained rings, two-tier ranking documented for match count priority over MAE**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-11T14:43:33Z
- **Completed:** 2026-02-11T14:46:08Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added 8 DEFF NOT badlist patterns to CASE agent knowledge (cyclopropane, cyclobutane, aziridine, azetidine, thiirane, thietane, epoxide, oxetane)
- Documented epoxide exception case with specific criteria (45-55 ppm shift range + oxygen in formula)
- Added two-tier ranking algorithm explanation to agent knowledge and CLAUDE.md
- Updated Manual File Construction Checklist with item 8 for badlist filters

## Task Commits

Each task was committed atomically:

1. **Task 1 & 2: Documentation updates** - `b3aae81` (docs)

**Note:** ~/.claude/agents/lucy-case-agent.md is outside repository and was modified but not committed to this repo.

## Files Created/Modified

- `~/.claude/agents/lucy-case-agent.md` - Added Badlist Filters section with 8 DEFF NOT patterns, epoxide exception, ranking algorithm guidance, and updated checklist item 8
- `CLAUDE.md` - Added matched_count to CLI output reference, documented two-tier ranking algorithm

## Decisions Made

1. **Badlist covers 8 strained ring patterns**: All 3- and 4-membered rings with C, N, O, S (cyclopropane, cyclobutane, aziridine, azetidine, thiirane, thietane, epoxide, oxetane) are excluded as chemically implausible in natural products.

2. **Epoxide exception with specific criteria**: Remove `DEFF NOT C1OC1` only when BOTH conditions met: (a) 13C shifts in 45-55 ppm range, (b) molecular formula contains oxygen. Prevents false positives while allowing genuine epoxide structures.

3. **Two-tier ranking prioritizes match count**: Solutions ranked by signal match count (descending) THEN MAE (ascending). This prevents wrong structures with coincidentally low MAE but incomplete spectral coverage from outranking correct structures with more complete signal assignments.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward documentation additions.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

CASE agent now has:
- Badlist patterns ready to insert into every LSD file (Section 3, after MULT/HSQC/HMBC/BOND, before ELIM)
- Ranking interpretation guidance (Section 5, step 6)
- Updated Manual File Construction Checklist with 8 items

Phase 39 can now integrate statistical constraints (hybridisation, neighbours, HHB, signal grouping) into agent workflow, building on this badlist foundation.

No blockers. Ready for Phase 39 (Statistical Constraints Integration).

---
*Phase: 38-two-tier-ranking-and-badlist*
*Completed: 2026-02-11*
