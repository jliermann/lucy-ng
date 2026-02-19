---
phase: 50-ssc-extraction-pipeline
plan: 01
subsystem: database
tags: [numpy, bitset, fingerprint, sqlite, checkpoint, fragments, ssc]

# Dependency graph
requires:
  - phase: 49-fragment-schema-infrastructure
    provides: FragmentDatabaseManager with schema_meta table, SSCRecord model

provides:
  - shifts_to_fingerprint() utility: 256-bit (32-byte) bitset encoding of 13C shifts with 2 ppm bins
  - FragmentDatabaseManager.set_checkpoint() / get_checkpoint() / clear_checkpoints()
  - FragmentDatabaseManager.clear_ssc_data() for --fresh flag in extraction pipeline

affects:
  - 50-02 SSC extraction pipeline (uses shifts_to_fingerprint + checkpoint methods)
  - 51-fragment-search (uses fingerprints for Boolean-AND pre-screening)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD red-green cycle for pure utility functions and DB methods
    - 256-bit bitset via np.zeros(32, dtype=np.uint8) with bit manipulation
    - Checkpoint prefix convention: all checkpoint keys use checkpoint_ prefix in schema_meta
    - INSERT OR REPLACE upsert for checkpoint persistence across pipeline restarts

key-files:
  created:
    - src/lucy_ng/fragments/fingerprint.py
    - tests/test_fingerprint.py
  modified:
    - src/lucy_ng/fragments/db.py
    - src/lucy_ng/fragments/__init__.py
    - tests/test_fragment_db.py

key-decisions:
  - "Fingerprint valid range is [0, 512) ppm (256 bins x 2 ppm) — out-of-range shifts silently ignored rather than raising"
  - "clear_checkpoints uses LIKE 'checkpoint_%' pattern so schema_version and bin_size rows are always preserved"
  - "clear_ssc_data deletes ssc_bitset before ssc (explicit ordering, not relying on CASCADE) for clarity"

patterns-established:
  - "Bitset encoding: np.zeros(32, dtype=np.uint8), bin_idx = int(shift/bin_ppm), byte = bin_idx//8, bit = 1 << (bin_idx%8)"
  - "Checkpoint prefix: all checkpoint keys prefixed with checkpoint_ to distinguish from schema metadata"
  - "TDD cycle: write all failing tests first, then implement minimal code to pass, then lint/type-check"

requirements-completed: [FRAG-03]

# Metrics
duration: 12min
completed: 2026-02-19
---

# Phase 50 Plan 01: Fingerprint Utility and Checkpoint Methods Summary

**256-bit bitset fingerprint encoder (shifts_to_fingerprint) and checkpoint get/set/clear methods on FragmentDatabaseManager — the two building blocks for resumable SSC extraction in Plan 02**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-19T14:39:19Z
- **Completed:** 2026-02-19T14:51:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created `fingerprint.py` with `shifts_to_fingerprint()`: encodes 13C shifts into 32-byte bitsets using 2 ppm bins, handles negatives and out-of-range silently, idempotent OR within same bin
- Added four checkpoint methods to `FragmentDatabaseManager`: `set_checkpoint`, `get_checkpoint`, `clear_checkpoints`, `clear_ssc_data` — enabling resumable multi-hour extraction runs
- Full TDD: 10 fingerprint tests + 7 checkpoint tests, all passing alongside 20 pre-existing Phase 49 tests (37 total new/modified, 798 suite-wide)
- Exported `shifts_to_fingerprint` from the `lucy_ng.fragments` package public API

## Task Commits

Each task was committed atomically:

1. **Task 1: Create fingerprint utility module** - `7a4dbc7` (feat)
2. **Task 2: Add checkpoint methods to FragmentDatabaseManager** - `c0bfff5` (feat)

**Plan metadata:** _(to be added in final commit)_

_Note: TDD tasks had single feat commits (RED and GREEN in one commit per task, as GREEN completed cleanly in first attempt)_

## Files Created/Modified
- `src/lucy_ng/fragments/fingerprint.py` - shifts_to_fingerprint() with BIN_SIZE_PPM=2.0, FINGERPRINT_BYTES=32 constants
- `src/lucy_ng/fragments/__init__.py` - Added shifts_to_fingerprint to imports and __all__
- `src/lucy_ng/fragments/db.py` - Added Checkpoint Methods section: set_checkpoint, get_checkpoint, clear_checkpoints, clear_ssc_data
- `tests/test_fingerprint.py` - 10 tests: empty, single-bit, same-bin idempotency, two-bin, length, zero-shift, max-shift, negative, 512-boundary, roundtrip
- `tests/test_fragment_db.py` - 7 new tests in TestCheckpointMethods class appended to existing file

## Decisions Made
- Fingerprint valid range `[0, 512)` ppm (256 bins x 2 ppm): out-of-range shifts silently ignored rather than raising, consistent with set-semantics
- `clear_checkpoints` uses `LIKE 'checkpoint_%'` SQL pattern so `schema_version` and `bin_size` rows are always preserved
- `clear_ssc_data` explicitly deletes `ssc_bitset` before `ssc` for clarity (not relying on CASCADE)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `shifts_to_fingerprint` ready for use in Plan 02 SSC extraction pipeline to encode each SSC's shifts on insert
- Checkpoint methods ready for Plan 02 to store `checkpoint_last_compound_id` for resumption
- `clear_ssc_data` ready for Plan 02 `--fresh` flag implementation
- Full test suite (798 tests) passes with no regressions

---
*Phase: 50-ssc-extraction-pipeline*
*Completed: 2026-02-19*
