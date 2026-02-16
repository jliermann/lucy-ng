---
phase: 36-hhb-and-ring-detection
plan: 02
subsystem: prediction
tags: [rdkit, ring-detection, hose-statistics, hetero-hetero-bonds, welford-algorithm]

# Dependency graph
requires:
  - phase: 36-01
    provides: Schema v6 with bond_pair_stats table and ring columns
provides:
  - WelfordAccumulator with ring membership tracking (in_3ring, in_4ring, in_aromatic)
  - update_with_rings() method for combined neighbor+ring tracking
  - All 3 HOSE stats generators pass mol+atom_idx for ring detection
  - BondPairStatsGenerator for populating bond_pair_stats table
  - extract_hetero_hetero_bonds() for detecting non-C/non-H bond pairs
affects: [36-03-hhb-detection, 38-ranking-and-badlist]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Welford accumulator extended with ring membership counts for frequency distributions"
    - "update_with_rings() delegates to update_with_neighbors() for composition pattern"
    - "RDKit GetRingInfo().IsAtomInRingOfSize() for 3-ring and 4-ring detection"
    - "RDKit atom.GetIsAromatic() for aromaticity detection"
    - "BondPairStatsGenerator iterates compounds, extracts HHB pairs, computes formula-level statistics"

key-files:
  created:
    - src/lucy_ng/prediction/bond_pair_generator.py
    - tests/test_stats_generator_rings.py
    - tests/test_bond_pair_generator.py
  modified:
    - src/lucy_ng/prediction/stats_generator.py

key-decisions:
  - "update_with_rings() calls update_with_neighbors() internally for composition - avoids duplication"
  - "WelfordAccumulator.to_tuple() extended from 11 to 14 elements for v6 schema (16-element with hose_code+radius)"
  - "extract_hetero_hetero_bonds() returns canonicalized pairs (alphabetically sorted) - ensures ('N', 'O') not ('O', 'N')"
  - "BondPairStatsGenerator uses iter_compounds_with_shifts() for consistency with other generators"
  - "Ring membership as counts (not booleans) enables frequency distributions for Phase 38 badlist"

patterns-established:
  - "Ring detection pattern: GetRingInfo().IsAtomInRingOfSize(atom_idx, size)"
  - "Aromaticity detection: atom.GetIsAromatic() on molecules with implicit hydrogens"
  - "HHB extraction: iterate bonds, filter non-C/non-H, canonicalize pairs"
  - "Formula-level statistics: compute molecular formula, normalize, aggregate by (formula, elem1, elem2)"

# Metrics
duration: 9min
completed: 2026-02-11
---

# Phase 36 Plan 02: Ring and HHB Generators Summary

**Ring membership tracking (3-ring, 4-ring, aromatic) in HOSE stats and hetero-hetero bond pair statistics generator for formula-level HHB detection**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-11T11:00:15Z
- **Completed:** 2026-02-11T11:10:15Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- WelfordAccumulator tracks ring membership counts for frequency-based badlist filtering (Phase 38)
- All 3 HOSE stats generators (HOSEStatsGenerator, ResumableHOSEStatsGenerator, SDFHOSEStatsGenerator) detect ring membership during processing
- BondPairStatsGenerator populates bond_pair_stats table from compound SMILES with RDKit bond iteration
- 20 comprehensive tests covering ring tracking, HHB extraction, and database integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Ring membership tracking in HOSE generators** - `634e5d7` (feat)
2. **Task 2: BondPairStatsGenerator for hetero-hetero bonds** - `d3666d8` (feat)

## Files Created/Modified
- `src/lucy_ng/prediction/stats_generator.py` - WelfordAccumulator with in_3ring/in_4ring/in_aromatic fields, update_with_rings() method, to_tuple() extended to 14 elements, all generators updated
- `src/lucy_ng/prediction/bond_pair_generator.py` - BondPairStatsGenerator class and extract_hetero_hetero_bonds() function
- `tests/test_stats_generator_rings.py` - 8 test cases for ring tracking, merge, to_tuple, integration
- `tests/test_bond_pair_generator.py` - 12 test cases for HHB extraction, canonicalization, database population, frequency calculation

## Decisions Made

**update_with_rings() composition:** Added update_with_rings() method that calls update_with_neighbors() internally before ring checks. Rationale: Avoids code duplication, maintains single responsibility, ensures hybridisation and neighbor tracking happen consistently with ring tracking.

**to_tuple() extended to 14 elements:** Changed WelfordAccumulator.to_tuple() to return 14 elements (was 11 in v5). With hose_code+radius prepended, this creates 16-element tuples for v6 schema upsert. Rationale: Matches schema extension from Phase 36-01, enables ring frequency queries.

**Canonicalized HHB pairs:** extract_hetero_hetero_bonds() returns alphabetically sorted pairs (("N", "O") not ("O", "N")). Rationale: Ensures uniqueness regardless of bond direction, simplifies database queries (no need to check both orderings).

**Formula-level bond pair statistics:** BondPairStatsGenerator aggregates at formula level, not HOSE level. Rationale: HHB queries operate at molecular formula level ("Do C10H14O2 compounds have O-N bonds?"), matching the granularity decision from Phase 36-01.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - ring detection and bond pair extraction followed RDKit API patterns from existing codebase.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Generators complete for Phase 36-03 (HHB detection CLI). Ready to:
- Run BondPairStatsGenerator.populate_database() to fill bond_pair_stats table
- Run ResumableHOSEStatsGenerator with update_with_rings() to populate ring columns
- Query bond_pair_stats by formula for HHB detection
- Query hose_stats ring columns for aromatic/3-ring/4-ring frequency filtering

No blockers. Ring columns exist (will be populated on next HOSE generation run). Bond pair stats table created (will be populated on first BondPairStatsGenerator run).

---
*Phase: 36-hhb-and-ring-detection*
*Completed: 2026-02-11*
