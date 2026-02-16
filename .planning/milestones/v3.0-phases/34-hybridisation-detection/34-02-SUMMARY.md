---
phase: 34
plan: 02
subsystem: prediction
status: COMPLETED
tags: [hose, statistics, hybridisation, rdkit]

requires:
  - 34-01  # Database schema v4 with hybridisation columns
  - 16  # HOSE code generator
  - 17  # Stats generator base implementation

provides:
  - Hybridisation extraction from RDKit atoms (sp3/sp2/sp1)
  - WelfordAccumulator with hybridisation count tracking
  - Extended stats generator pipeline with hybridisation data

affects:
  - 34-03  # Hybridisation detection module will query this data
  - 35  # Database regeneration will populate hybridisation counts

tech-stack:
  added: []
  patterns:
    - Online statistics with parallel metadata accumulation
    - Backward-compatible API extension (hybridisations parameter optional)

key-files:
  created:
    - tests/test_stats_generator_hybridisation.py  # Hybridisation extraction tests
  modified:
    - src/lucy_ng/prediction/stats_generator.py  # Added hybridisation tracking
    - tests/test_hose_stats_generator.py  # Updated for new tuple return format

decisions:
  - extract_hybridisation() at module level for reusability
  - update_with_hybridisation() instead of modifying update() for backward compatibility
  - generate_all() returns tuple (aggregates, hybridisations) - breaking change but minimal impact
  - compute_stats() accepts optional hybridisations parameter for graceful fallback
  - to_tuple() extended to 6 elements - breaking change requires test updates
  - Treat S and UNSPECIFIED hybridisations as sp3 (conservative default)

metrics:
  duration: "11 minutes"
  tests: "46 passed (8 new, 38 existing)"
  lines_added: 286
  lines_removed: 23
  completed: 2026-02-11
---

# Phase 34 Plan 02: Hybridisation Extraction in HOSE Stats Generator Summary

**One-liner:** Extended HOSE stats pipeline to extract and store hybridisation state (sp3/sp2/sp1) from RDKit atoms using Welford accumulators with parallel metadata tracking.

## What Was Done

### Core Implementation

1. **Module-level helper function:**
   - `extract_hybridisation(atom) -> str`: Maps RDKit hybridisation types to "sp3", "sp2", "sp1"
   - Works on implicit-H molecules (lucy-ng standard)
   - Treats S and UNSPECIFIED as sp3 (conservative default)

2. **WelfordAccumulator extension:**
   - Added `sp3_count`, `sp2_count`, `sp1_count` fields (default 0)
   - New method `update_with_hybridisation(value, hybridisation)`: Updates shift stats + increments hybridisation counter
   - Updated `merge()` to combine hybridisation counts (simple addition)
   - Extended `to_tuple()` to 6-element format: `(count, mean, m2, sp3_count, sp2_count, sp1_count)`

3. **ResumableHOSEStatsGenerator updates:**
   - `_process_chunk()`: Extracts hybridisation once per atom, calls `update_with_hybridisation()`
   - `_upsert_chunk_stats()`: Prepends hose_code/radius to 6-element tuple for 8-element upsert format

4. **SDFHOSEStatsGenerator updates:**
   - Same changes as ResumableHOSEStatsGenerator (extraction + update_with_hybridisation)
   - Ensures SDF-based generation tracks hybridisation identically

5. **HOSEStatsGenerator updates (backward compatibility focus):**
   - `generate_all()` now returns `tuple[dict, dict]` (aggregates, hybridisations)
   - Maintains parallel `hybridisations` dict: `{(hose_code, radius): {"sp3": N, "sp2": M, "sp1": K}}`
   - `compute_stats()` accepts optional `hybridisations` parameter (defaults to None for backward compat)
   - `populate_database()` passes both dicts through pipeline

### Test Coverage

8 new tests in `test_stats_generator_hybridisation.py`:
- `test_extract_hybridisation_sp3`: Ethane, cyclohexane detection
- `test_extract_hybridisation_sp2`: Benzene, acetic acid, ethylene detection
- `test_extract_hybridisation_sp1`: Acetylene, propargyl alcohol detection
- `test_extract_hybridisation_no_explicit_h`: Confirms implicit-H molecules work correctly
- `test_welford_accumulator_hybridisation_counts`: Verifies counter increments
- `test_welford_accumulator_merge_hybridisation`: Verifies counts merge correctly
- `test_welford_accumulator_to_tuple_extended`: Verifies 6-element tuple format
- `test_welford_accumulator_backward_compat`: Plain `update()` doesn't affect hybridisation counts

38 existing tests updated for new API:
- `test_generate_all`: Unpacks tuple, validates hybridisations dict structure
- `test_to_tuple`: Unpacks 6 elements, verifies hybridisation counts are 0 with plain update
- Edge case tests: Updated to unpack tuple return value from `generate_all()`

### Architecture Decisions

**Why extract_hybridisation() at module level?**
- Reusable across all generator classes
- Clear separation of concerns (RDKit analysis vs statistics)
- Easy to test in isolation

**Why update_with_hybridisation() instead of modifying update()?**
- Backward compatibility: Existing code using plain `update()` continues to work
- Explicit intent: Shows that hybridisation tracking is happening
- Test coverage: `test_welford_accumulator_backward_compat` proves plain `update()` still works

**Why return tuple from generate_all()?**
- Breaking change, but minimal impact (only 4 test call sites)
- Cleaner than adding optional parameter and checking if provided
- Parallel structure is natural fit for parallel dict comprehensions

**Why optional hybridisations parameter in compute_stats()?**
- Graceful degradation: Can still compute stats without hybridisations
- Allows testing aggregates-only path
- Future-proof: Other code can call compute_stats() without breaking

**Why treat S and UNSPECIFIED as sp3?**
- Conservative default (sp3 is most common in organic chemistry)
- Avoids crashes on edge cases (e.g., sulfur atoms, exotic bonds)
- Statistical queries can filter by total counts if needed

## Files Modified

**Created:**
- `tests/test_stats_generator_hybridisation.py` (160 lines): Comprehensive hybridisation extraction tests

**Modified:**
- `src/lucy_ng/prediction/stats_generator.py` (+240 lines, -15 lines):
  - Added `extract_hybridisation()` helper
  - Extended `WelfordAccumulator` with 3 fields + 1 method
  - Updated all 3 generator classes (_process_chunk + _upsert_chunk_stats or generate_all/compute_stats)
- `tests/test_hose_stats_generator.py` (+46 lines, -8 lines):
  - Updated `test_generate_all` to validate hybridisations dict
  - Updated `test_to_tuple` for 6-element format
  - Updated 3 edge case tests to unpack tuple

## Test Results

```
tests/test_stats_generator_hybridisation.py: 8 passed
tests/test_hose_stats_generator.py: 38 passed
Total: 46 passed, 0 failed
```

All tests pass. No regressions in full suite (614 passed, 3 unrelated failures in lsd_analyzer).

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Blocked on:**
- None

**Enables:**
- Phase 34-03: Hybridisation detection module can now query populated hybridisation counts
- Phase 35: Database regeneration will populate sp3/sp2/sp1 counts in existing HOSE stats

**Notes:**
- Database schema is ready (v4 from Plan 34-01) but data is unpopulated (all counts = 0)
- Phase 35 will run `lucy database generate-hose` to populate hybridisation data
- Detection module in 34-03 will use backward-compatible queries (try/except on column access)

## Performance Notes

- Hybridisation extraction adds negligible overhead (~single GetHybridization() call per atom per radius)
- WelfordAccumulator overhead: 3 integers = 24 bytes per (hose_code, radius) key
- Database overhead: 3 integers per row (already in schema from 34-01)
- No change to Welford merge algorithm complexity (still O(1) per key)

## Known Limitations

- S and UNSPECIFIED hybridisations treated as sp3 (may misclassify exotic bonding)
- No validation that hybridisation counts sum to total count (trusted to RDKit)
- Detection queries in 34-03 must handle zero counts gracefully (data unpopulated until Phase 35)
