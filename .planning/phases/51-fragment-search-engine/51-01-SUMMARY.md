---
phase: 51-fragment-search-engine
plan: 01
subsystem: fragments
tags: [numpy, sqlite, fingerprint, search, bitset, nearest-neighbour]

# Dependency graph
requires:
  - phase: 50-ssc-extraction-pipeline
    provides: "FragmentDatabaseManager with iter_ssc_bitsets, get_ssc_by_id; shifts_to_fingerprint; SSCRecord/SSCMatch models"
provides:
  - "expand_query_fingerprint function for query-side +-N bin tolerance expansion"
  - "FragmentSearcher class with two-phase search pipeline (pre-screening + fine matching)"
  - "FragmentSearcher export from lucy_ng.fragments"
affects: [52-lsd-fragment-formatter, 53-agent-fragment-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: ["NumPy vectorised batch bitset screening", "greedy nearest-neighbour fine matching with DEV/AVGDEV thresholds", "context manager wrapping FragmentDatabaseManager"]

key-files:
  created:
    - src/lucy_ng/fragments/searcher.py
    - tests/test_fragment_searcher.py
  modified:
    - src/lucy_ng/fragments/fingerprint.py
    - src/lucy_ng/fragments/__init__.py

key-decisions:
  - "LSB-first bit encoding with bitorder='little' in unpackbits/packbits to match existing shifts_to_fingerprint byte encoding"
  - "np.asarray wrapper around np.all(..., axis=1) to resolve mypy union type ambiguity without type: ignore"
  - "Chunked get_ssc_by_id with 999-ID limit per SQLite query to respect placeholder limit"

patterns-established:
  - "FragmentSearcher as context manager: wraps FragmentDatabaseManager, lazy connection open"
  - "Vectorised batch pre-screening: np.all((fps & q) == fps, axis=1) on (N,32) uint8 arrays"
  - "Greedy nearest-neighbour fine matching: sorted fragment shifts, pop closest remaining query shift"

requirements-completed: [SRCH-01, SRCH-02, SRCH-03, SRCH-04]

# Metrics
duration: 16min
completed: 2026-02-19
---

# Phase 51 Plan 01: Fragment Search Algorithm Summary

**Two-phase SSC search engine with expand_query_fingerprint for +-1 bin tolerance, NumPy vectorised pre-screening, and greedy nearest-neighbour fine matching ranked by atom_count DESC then avg_deviation ASC**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-19T16:56:00Z
- **Completed:** 2026-02-19T17:12:15Z
- **Tasks:** 2 (TDD: RED + GREEN)
- **Files modified:** 4

## Accomplishments
- Implemented `expand_query_fingerprint` in fingerprint.py: query-side +-N bin expansion using np.unpackbits/packbits with LSB-first encoding, no wrap-around at boundaries
- Implemented `FragmentSearcher` class in new searcher.py: context manager wrapping FragmentDatabaseManager with `search()`, `_prescreening_pass()`, `_screen_batch()`, and `_fine_match_record()` methods
- Pre-screening uses NumPy vectorised AND on batched (N,32) uint8 arrays from `iter_ssc_bitsets(batch_size=100_000)` -- never loads full database into RAM
- Fine matching uses greedy nearest-neighbour: for each fragment shift, find closest unmatched query shift, reject if per-pair DEV > threshold or overall AVGDEV > threshold
- Ranking sorts by (-atom_count, avg_deviation) and assigns sequential rank 1..N
- 17 comprehensive tests covering fingerprint expansion, pre-screening, fine matching, ranking, min_atom_count, end-to-end search, context manager protocol, max_results, and package import
- All 832 tests in full suite pass, mypy --strict clean, ruff clean

## Task Commits

Each task was committed atomically:

1. **Task 1: RED - Failing tests** - `9d257c7` (test)
2. **Task 2: GREEN - Implementation + fix** - `449d963` (feat)

**Plan metadata:** (pending)

_Note: TDD plan with RED (failing tests) then GREEN (implementation making all tests pass)_

## Files Created/Modified
- `src/lucy_ng/fragments/fingerprint.py` - Added `expand_query_fingerprint(fp, expand_bins=1)` function
- `src/lucy_ng/fragments/searcher.py` - New file: `FragmentSearcher` class with two-phase search pipeline
- `src/lucy_ng/fragments/__init__.py` - Added `FragmentSearcher` export and `__all__` update
- `tests/test_fragment_searcher.py` - 17 tests across 6 test classes

## Decisions Made
- Used `bitorder='little'` with np.unpackbits/packbits to match existing shifts_to_fingerprint LSB-first byte encoding (byte[N] bit K = 1 << K). The default `bitorder='big'` would have produced incorrect bit indices.
- Used `np.asarray()` wrapper around `np.all(..., axis=1)` to resolve mypy strict typing -- `np.all` with axis returns a union type that mypy won't allow indexing on. This avoids `type: ignore` comments.
- Chunked `get_ssc_by_id` calls at 999 IDs per batch to respect SQLite's compiled-in parameter limit of 999 placeholders.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_prescreening_passes_subset min_atom_count mismatch**
- **Found during:** Task 2 (GREEN implementation)
- **Issue:** Test created SSC with 2 atoms but search() default min_atom_count=3 filtered it out, causing false test failure
- **Fix:** Added `min_atom_count=1` to the test's search() call since the test targets pre-screening behavior, not min_atom_count filtering
- **Files modified:** tests/test_fragment_searcher.py
- **Verification:** Test passes after fix
- **Committed in:** 449d963 (part of GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug in test)
**Impact on plan:** Minimal -- test logic error caught and fixed immediately. No scope creep.

## Issues Encountered
None -- implementation followed the plan and research closely.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- FragmentSearcher is ready for Plan 02 to wrap with `lucy fragment search` CLI command
- `expand_query_fingerprint` and `FragmentSearcher` are importable from `lucy_ng.fragments`
- Phase 52 (LSD Fragment Formatter) can begin -- it depends only on `SSCMatch` model which is stable
- Multiplicity matching deferred: `SSCRecord.shift_list` stores only floats, no per-shift H-count data (requires future schema extension)

## Self-Check: PASSED

All artifacts verified:
- 5/5 files exist on disk
- 2/2 commit hashes found in git log
- 17/17 tests passing
- 832/832 full suite tests passing
- mypy --strict: 0 errors in target files
- ruff check: 0 errors

---
*Phase: 51-fragment-search-engine*
*Completed: 2026-02-19*
