---
phase: 60-statistics-generator
plan: "01"
subsystem: prediction
tags: [coupling-path, statistics, 4j-detection, tdd, checkpoint]
dependency_graph:
  requires:
    - 59-01: coupling_path_stats table schema
    - 59-02: DatabaseManager.insert_coupling_path_stats_batch, set_checkpoint, get_checkpoint, clear_checkpoint
  provides:
    - CouplingPathStatsGenerator class for populating coupling_path_stats
  affects:
    - Phase 61 Detection Engine (consumes coupling_path_stats)
tech_stack:
  added: []
  patterns:
    - TDD red/green cycle
    - COCONUT 1-based atom index conversion
    - RDKit GetDistanceMatrix for all-pairs O(1) bond distance lookup
    - HOSE codes at radius 2 for carbon pair identification
    - Checkpoint/resume pattern from ResumableHOSEStatsGenerator
key_files:
  created:
    - src/lucy_ng/prediction/coupling_path_generator.py
    - tests/test_coupling_path_generator.py
  modified: []
decisions:
  - "Accumulate all counts in memory for entire run; checkpoint only saves position, not partial DB writes. Avoids INSERT OR REPLACE conflict with partial count rows."
  - "Skip compound entirely if ANY shift has NULL atom_index (not just that shift). Ensures map is complete and distances are meaningful."
  - "Bond distance capped at 5 (not 6+) to match architecture v7.0 spec for coupling_path_stats bond_distance column."
metrics:
  duration_minutes: 8
  tasks_completed: 2
  files_created: 2
  files_modified: 0
  completed_date: "2026-03-10"
---

# Phase 60 Plan 01: CouplingPathStatsGenerator Summary

**One-liner:** Checkpointed statistics generator for (carbon_hose, h_carbon_hose, bond_distance) -> count pairs using RDKit distance matrix and HOSE codes at radius 2.

## What Was Built

`CouplingPathStatsGenerator` in `src/lucy_ng/prediction/coupling_path_generator.py`:

- **Core algorithm**: For each compound, parses SMILES (implicit H, no AddHs), converts COCONUT 1-based atom indices to 0-based, validates carbon atoms, computes all-pairs shortest bond distances via `Chem.GetDistanceMatrix(mol)`, generates HOSE R2 codes for each (carbon, proton-bearing-carbon) pair, accumulates counts.

- **Three public methods**:
  - `generate_all(progress, limit, start_id)` — returns `dict[(c_hose, h_hose, dist), count]`
  - `populate_database(progress)` — calls generate_all and inserts batch
  - `run(resume, fresh, chunk_size, limit, progress)` — production entry point with checkpoint/resume

- **Checkpoint/resume**: saves `last_compound_id`, `compounds_processed`, `compounds_failed` to `operation_checkpoint` table every `chunk_size` compounds. `fresh=True` clears table and checkpoint before starting. Strategy: accumulate in memory, write once at end (avoids INSERT OR REPLACE partial-count issue).

- **18 unit tests** covering: COCONUT index conversion, NULL skipping, non-carbon validation, distance capping, proton-bearing detection, 4J pair generation, VAL-04 checkpoint recovery identity, performance (1K compounds < 30s).

## Test Results

All 18 new tests pass. No regression on existing 73 tests (91 total pass).

## Key Architecture Decisions

### Memory accumulation vs chunked DB writes

The plan discussed both approaches. Implemented the simpler "accumulate all in memory, write once" strategy. This avoids the INSERT OR REPLACE overwrite problem (partial counts would be silently replaced rather than accumulated). The architecture doc estimates 2-4GB for 928K compounds with 40-char HOSE strings — acceptable for a batch generation run.

### Skip-entire-compound on any NULL atom_index

If we only skip the NULL-indexed shifts and continue, we'd compute distances using an incomplete set of atoms. The result would be noisy (wrong HOSE codes relative to the molecule's actual atom positions). Full compound skip produces cleaner statistics.

### Distance cap at 5

Distances >= 5 bonds are grouped as "5" in the database (bond_distance column stores 2, 3, 4, or 5). This matches the Phase 59 schema design. Very long-range pairs (5+) are rare in HMBC and are statistically grouped.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `src/lucy_ng/prediction/coupling_path_generator.py` exists
- `tests/test_coupling_path_generator.py` exists (18 tests, 606 lines)
- Commits: cbb9d6b (RED tests), 5189d05 (GREEN implementation)
