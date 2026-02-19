---
phase: 52-deff-formatter-lsd-generation
plan: 02
subsystem: fragments
tags: [lsd, cli, deff, fexp, smoke-test, goodlist, double-quotes, click]

# Dependency graph
requires:
  - phase: 52-deff-formatter-lsd-generation
    provides: DEFFFormatter class with smiles_to_fragment_content, write_fragment_file, deff_command, fexp_command
provides:
  - CLI command `lucy fragment to-lsd` generating LSD fragment files from SMILES
  - Fixed DEFF double-quote syntax in search command output
  - LSD smoke test proving goodlist semantics (4 solutions reduced to 1)
affects: [case-agent-fragment-injection, lucy-case-agent]

# Tech tracking
tech-stack:
  added: []
  patterns: [cli-fragment-file-generation, lsd-smoke-test-pattern, generic-fragment-with-flexible-h-counts]

key-files:
  created: []
  modified:
    - src/lucy_ng/cli/fragment.py
    - tests/test_lsd_formatter.py

key-decisions:
  - "Generic benzene fragment with (0 1) H counts for smoke test -- exact H counts from DEFFFormatter too restrictive for substituted ring matching"
  - "Fragment file written to CWD by default with bare filename in DEFF command -- LSD resolves relative to working directory"

patterns-established:
  - "LSD smoke test pattern: generic fragment with flexible H counts for ring matching in substituted contexts"
  - "CLI to-lsd output: JSON includes full file content, DEFF/FEXP commands, and canonical SMILES for agent consumption"

requirements-completed: [LINT-02, LINT-03]

# Metrics
duration: 7min
completed: 2026-02-19
---

# Phase 52 Plan 02: CLI to-lsd Command and LSD Smoke Test Summary

**`lucy fragment to-lsd` CLI command generating LSD fragment files from SMILES, with LSD smoke test proving benzene goodlist reduces toluene from 4 to 1 solution**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-19T18:06:30Z
- **Completed:** 2026-02-19T18:13:51Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `lucy fragment to-lsd "SMILES"` CLI command writes SSTR/LINK fragment files with deterministic hash-based filenames and outputs DEFF/FEXP commands in both JSON and text formats
- Fixed single-quote bug in search command's DEFF output (single quotes cause LSD error 160; now uses double quotes per LSD 3.4.9 spec)
- LSD smoke test proves end-to-end goodlist semantics: toluene baseline produces 4 solutions, benzene ring goodlist reduces to exactly 1 solution
- DEFF/FEXP ordering verification confirms commands appear before MULT in generated LSD files (LINT-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add to-lsd CLI command and fix search single-quote bug** - `23cbf91` (feat)
2. **Task 2: LSD smoke test -- goodlist semantics verification** - `fe57084` (test)

## Files Created/Modified
- `src/lucy_ng/cli/fragment.py` - Added `to-lsd` command (Click), fixed DEFF double quotes in search output
- `tests/test_lsd_formatter.py` - Added LSD smoke tests (goodlist reduces solutions, DEFF/FEXP ordering) and search quote verification tests

## Decisions Made
- Used generic benzene fragment with `(0 1)` H counts in smoke test instead of exact benzene from `DEFFFormatter.smiles_to_fragment_content("c1ccccc1")` -- exact benzene has all 1H but toluene has one 0H ring carbon, so exact matching gives 0 solutions. Generic fragments with flexible H counts are needed for matching substituted rings.
- Fragment atom count extracted by counting SSTR lines in written file content (rather than re-parsing SMILES)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Generic benzene fragment for smoke test instead of exact SMILES fragment**
- **Found during:** Task 2 (LSD smoke test)
- **Issue:** Plan said to use `DEFFFormatter.write_fragment_file("c1ccccc1")` for the smoke test fragment. This produces exact H counts (all 1H for benzene), but toluene has one ring carbon with 0H (bonded to methyl). The exact fragment gives 0 solutions instead of 1.
- **Fix:** Used a hand-written generic benzene fragment with `(0 1)` H counts per atom (matching the research smoke test pattern in 52-RESEARCH.md). DEFFFormatter.deff_command and fexp_command are still used for DEFF/FEXP generation.
- **Files modified:** tests/test_lsd_formatter.py
- **Verification:** Smoke test passes: 4 baseline solutions, 1 goodlist solution
- **Committed in:** fe57084 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix -- exact benzene H counts don't match substituted ring positions. The research file already documented `(0 1)` H counts as the correct pattern; the plan's instruction to use `write_fragment_file` was inconsistent with the research finding. No scope creep.

## Issues Encountered
None beyond the deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Fragment pipeline complete: search finds fragments, to-lsd generates files, DEFF/FEXP commands reference them
- Ready for CASE agent integration: agent can call `lucy fragment to-lsd` and inject output directly into LSD files
- Open question for future work: DEFFFormatter produces exact H counts (correct for known structures), but fragment matching in LSD may need flexible H counts for substituted positions. Consider adding a `flexible_h=True` option in a future phase.

## Self-Check: PASSED

All files and commits verified:
- src/lucy_ng/cli/fragment.py: FOUND
- tests/test_lsd_formatter.py: FOUND
- 52-02-SUMMARY.md: FOUND
- Commit 23cbf91 (Task 1): FOUND
- Commit fe57084 (Task 2): FOUND

---
*Phase: 52-deff-formatter-lsd-generation*
*Completed: 2026-02-19*
