---
phase: 36-hhb-and-ring-detection
plan: 03
subsystem: prediction
tags: [statistical-detection, hetero-hetero-bonds, cli, click]

# Dependency graph
requires:
  - phase: 36-02
    provides: BondPairStatsGenerator and bond_pair_stats table
provides:
  - detect_hhb() method on StatisticalDetector for formula-level HHB queries
  - HHBResult and BondPairInfo Pydantic models
  - lucy detect hhb CLI command for hetero-hetero bond detection
affects: [38-ranking-and-badlist, 39-case-agent-update]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Formula-level detection (not shift-window based like hybridisation/neighbours)"
    - "Heteroatom presence check via regex pattern matching"
    - "Bond pair classification: allowed (>=threshold) vs forbidden (<threshold)"

key-files:
  created: []
  modified:
    - src/lucy_ng/detection/models.py
    - src/lucy_ng/detection/detector.py
    - src/lucy_ng/detection/__init__.py
    - src/lucy_ng/cli/detect.py

key-decisions:
  - "Heteroatom detection via simple regex (N|O|S|F|Cl|Br|I|P|Si) - no RDKit needed for formula parsing"
  - "Pure hydrocarbons get has_heteroatoms=False with clear user message (HHB analysis not applicable)"
  - "Formula not in database returns has_data=False with warning message"
  - "CLI takes FORMULA argument (not shift_ppm like hybridisation/neighbours) - explicit help text to prevent confusion"

patterns-established:
  - "Formula-based detection pattern for molecular-level constraints (vs shift-based for atom-level)"
  - "Allowed/forbidden pair classification at custom threshold for CASE agent constraint generation"
  - "CLI argument type distinction: float (shift) vs string (formula)"

# Metrics
duration: 5min
completed: 2026-02-11
---

# Phase 36 Plan 03: HHB Detection CLI Summary

**Formula-level hetero-hetero bond detection with lucy detect hhb command and StatisticalDetector.detect_hhb() method**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-11T11:15:09Z
- **Completed:** 2026-02-11T11:20:05Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- StatisticalDetector.detect_hhb() queries bond_pair_stats table by molecular formula
- HHBResult model classifies bond pairs as allowed (>=1%) or forbidden (<1%) with customizable threshold
- Pure hydrocarbon formulas (no heteroatoms) return clear "not applicable" message
- lucy detect hhb CLI command with formula argument, --threshold flag, and JSON output support

## Task Commits

Each task was committed atomically:

1. **Task 1: Add HHBResult model and detect_hhb() method** - `2193c27` (feat)
2. **Task 2: Add hhb CLI subcommand** - `b914ee7` (feat)

## Files Created/Modified
- `src/lucy_ng/detection/models.py` - BondPairInfo model (element1, element2, frequency, compound_count) and HHBResult model with summary() method
- `src/lucy_ng/detection/detector.py` - detect_hhb() method with formula parsing, heteroatom detection, and bond pair classification
- `src/lucy_ng/detection/__init__.py` - Updated exports to include HHBResult
- `src/lucy_ng/cli/detect.py` - hhb subcommand with formula argument and threshold flag

## Decisions Made

**Heteroatom detection via regex:** Used simple pattern matching (N|O|S|F|Cl|Br|I|P|Si) instead of RDKit molecular parsing. Rationale: Formula strings are simple, regex is fast, no need for complex library for this check.

**Pure hydrocarbon handling:** Formula with no heteroatoms returns has_heteroatoms=False with clear message "HHB analysis not applicable". Rationale: Better UX than throwing error or empty result. User gets explicit feedback that their query makes sense but doesn't apply to this formula.

**Formula argument type:** CLI takes FORMULA as string argument (not shift_ppm as float like other detect subcommands). Help text explicitly states "molecular formula, NOT a shift value". Rationale: Prevents user confusion since detect hybridisation/neighbours take float shifts, but HHB operates at molecular formula level.

**Formula not found warning:** When formula doesn't exist in database, return has_data=False with warning message. Rationale: Distinguishes "formula exists but no HHB bonds" (valid - many compounds only have C-X bonds) from "formula not in database" (user may have typo or need different database).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward implementation following established patterns from hybridisation/neighbours detection.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Phase 37 (signal grouping detection). HHB detection complete and available for:
- CASE agent to query allowed hetero-hetero bonds by formula
- Badlist generation (Phase 38) to incorporate HHB frequency filtering
- CASE agent updates (Phase 39) to use lucy detect hhb for LSD constraint generation

No blockers. All 3 detection commands (hybridisation, neighbours, hhb) now operational.

---
*Phase: 36-hhb-and-ring-detection*
*Completed: 2026-02-11*
