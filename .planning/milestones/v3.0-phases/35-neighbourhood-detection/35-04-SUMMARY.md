---
phase: 35-neighbourhood-detection
plan: 04
subsystem: cli
tags: [python, click, cli, statistical-detection, neighbourhood-analysis]

# Dependency graph
requires:
  - phase: 35-03
    provides: StatisticalDetector.detect_neighbours() method, NeighbourResult model
provides:
  - lucy detect neighbours CLI subcommand with threshold overrides
  - --mode strict (1%/95%) vs relaxed (0.1%/99%) thresholds
  - --min-frequency and --max-frequency for custom control
  - Text and JSON output formats
affects: [39-case-agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Click command pattern matching hybridisation command structure
    - Mode-based threshold presets with manual override capability

key-files:
  created:
    - (none - tests appended to existing file)
  modified:
    - src/lucy_ng/cli/detect.py
    - tests/test_detection_neighbours.py

key-decisions:
  - "--mode flag overrides --min-frequency/--max-frequency when both provided"
  - "No multiplicity argument per research recommendations (ignored for Phase 35)"
  - "Database auto-detection via DatabaseFinder (same pattern as hybridisation command)"

patterns-established:
  - "Detection CLI commands follow consistent pattern: shift → db auto-detect → detector → output"
  - "All detect subcommands support --db, --radius, --window, --format (text/json)"

# Metrics
duration: 6min
completed: 2026-02-11
---

# Phase 35 Plan 04: Neighbourhood CLI Summary

**lucy detect neighbours CLI subcommand exposes forbidden/mandatory element detection with strict/relaxed modes and custom threshold overrides**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-11T09:24:05Z
- **Completed:** 2026-02-11T09:30:35Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `lucy detect neighbours <shift>` CLI command with all threshold controls
- --mode strict (1%/95%) vs relaxed (0.1%/99%) preset thresholds
- --min-frequency and --max-frequency for custom override
- Text output shows forbidden/mandatory elements, JSON output machine-readable
- 5 comprehensive CLI integration tests covering help, text, JSON, relaxed mode
- Follows hybridisation command pattern exactly (consistent UX)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add neighbours CLI subcommand** - `afb2b80` (feat)
2. **Task 2: CLI integration tests** - `88db205` (test)

## Files Created/Modified
- `src/lucy_ng/cli/detect.py` - Added neighbours_command with threshold override flags
- `tests/test_detection_neighbours.py` - Added 5 CLI integration tests (now 16 total tests)

## Decisions Made
- **Mode overrides manual thresholds:** --mode relaxed sets 0.1%/99% regardless of --min-frequency/--max-frequency values. This ensures preset modes work predictably.
- **No multiplicity argument:** Research (35-RESEARCH.md) recommends ignoring multiplicity for neighbour detection (unlike hybridisation where it's valuable). This keeps the interface simpler.
- **Database auto-detection:** Follows DatabaseFinder.find_hose_database() pattern from hybridisation command for consistent UX.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

Ready for Phase 36 (HHB and Ring Detection).

CLI integration complete:
- `lucy detect hybridisation` exposes sp3/sp2/sp1 detection
- `lucy detect neighbours` exposes forbidden/mandatory element detection
- Both commands support text and JSON output
- Both commands have comprehensive test coverage

Phase 35 complete. All 4 plans executed:
- 35-01: Schema v5 with neighbour columns
- 35-02: Stats generator extension
- 35-03: Detection models and detector method
- 35-04: CLI subcommand (this plan)

Next milestone (v3.0) continues with Phase 36 (HHB/ring detection) and Phase 37 (signal grouping).

---
*Phase: 35-neighbourhood-detection*
*Completed: 2026-02-11*
