---
phase: 50-ssc-extraction-pipeline
plan: 02
subsystem: fragments
tags: [rdkit, bfs, fragmentation, ssc, sqlite, checkpoint, tqdm, cli, pipeline]

# Dependency graph
requires:
  - phase: 50-01
    provides: shifts_to_fingerprint, FragmentDatabaseManager checkpoint methods
  - phase: 49-fragment-schema-infrastructure
    provides: FragmentDatabaseManager, SSCRecord, SSCMatch models

provides:
  - extract_fragments_for_compound(): BFS atom-centred radius 1-3 + ring-centred fragmentation
  - SSCExtractor: resumable extraction pipeline with 5-key checkpoint protocol
  - SSCExtractor.validate_self_search(): bin-size validation via Boolean-AND pre-screening
  - lucy fragment build CLI command with --sample, --resume/--fresh, --chunk-size options

affects:
  - 51-fragment-search (consumes SSC records and bitsets from fragment DB)
  - 52-lsd-integration (uses SSCMatch model from Phase 49)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - BFS fragmentation with RDKit FindAtomEnvironmentOfRadiusN + PathToSubmol
    - AROMATICITY_MDL standardisation mandatory before all fragmentation
    - Per-compound deduplication with in-memory set (not global)
    - Resumable pipeline: insert SSC batch FIRST, save checkpoint AFTER
    - Sequence[tuple[int | None, float]] covariant annotation for public API
    - tqdm import annotated with type: ignore[import-untyped] (pre-existing pattern)

key-files:
  created:
    - src/lucy_ng/fragments/extractor.py
    - tests/test_ssc_extractor.py
  modified:
    - src/lucy_ng/cli/fragment.py

key-decisions:
  - "Ring-centred environments: expand ring bonds + all bonds to immediate non-ring neighbours (radius 1 expansion)"
  - "Sample mode stops after N compounds_processed (not compound iterations) — skipped compounds do not count against sample"
  - "validate_self_search uses bytes comparison (query_fp[i] & ssc_bitset[i] == ssc_bitset[i]) rather than numpy for simplicity"
  - "Sequence[tuple[int | None, float]] covariant type for extract_fragments_for_compound atom_shifts param — avoids mypy list invariance error"

# Metrics
duration: 29min
completed: 2026-02-19
---

# Phase 50 Plan 02: SSC Extraction Pipeline Summary

**BFS sphere fragmentation algorithm (radius 1-3 + ring-centred) with resumable SSCExtractor pipeline and `lucy fragment build` CLI — the core Phase 50 deliverable extracting substructure-subspectrum correlations from the 928K compound database**

## Performance

- **Duration:** 29 min
- **Started:** 2026-02-19T14:54:59Z
- **Completed:** 2026-02-19T15:23:23Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Created `src/lucy_ng/fragments/extractor.py` with BFS fragmentation algorithm:
  - `extract_fragments_for_compound`: atom-centred radius 1-3 environments via `FindAtomEnvironmentOfRadiusN` + `PathToSubmol`, plus ring-centred environments (ring bonds + immediate neighbours) for rings <= 6 atoms
  - `AROMATICITY_MDL` standardisation mandatory before any fragmentation — ensures aromatic and Kekulé SMILES inputs produce identical canonical fragment SMILES
  - Per-compound SMILES deduplication via in-memory set
  - `_build_ssc_record` helper computes avg/min/max shift and bitset fingerprint
- Created `SSCExtractor` resumable pipeline class:
  - 5-key checkpoint protocol: last_id, processed, skipped, extracted, duplicate
  - Critical ordering: SSC batch inserted FIRST, checkpoint saved AFTER (INSERT OR IGNORE replay-safe)
  - `--fresh` truncates all SSC data and checkpoints via `clear_ssc_data()`
  - `--resume` restores all 5 counters from checkpoint for accurate progress reporting
  - Skipped compounds logged to stderr: `SKIPPED: compound_id=N (no atom-indexed shifts)`
  - `validate_self_search(sample_size)` method for Boolean-AND bin-size validation
- Added `lucy fragment build` CLI command to `src/lucy_ng/cli/fragment.py`:
  - Arguments: COMPOUND_DB (required), FRAGMENT_DB (optional, defaults to standard path)
  - Options: `--chunk-size`, `--sample`, `--resume/--fresh`
  - Sample mode with >= 100 compounds auto-runs self-search recall validation
  - Reports recall percentage; warns if < 99% (bin size validation before full run)
- 17 tests in `tests/test_ssc_extractor.py`: 8 unit tests (fragmentation + SSCExtractor), 5 integration tests (full pipeline, recall, resume, fresh, CLI), 4 additional edge case tests
- Full test suite: 815 passed, 7 skipped, 0 failed (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: BFS fragmentation and SSCExtractor class** - `48283f2` (feat)
2. **Task 2: lucy fragment build CLI command** - `e0dbc41` (feat)

Note: Task 3 integration tests were included in the Task 1 commit (test file written holistically covering unit + integration).

## Files Created/Modified

- `src/lucy_ng/fragments/extractor.py` (CREATED) — BFS fragmentation functions + SSCExtractor class + validate_self_search
- `tests/test_ssc_extractor.py` (CREATED) — 17 tests: TestExtractFragmentsForCompound (8), TestSSCExtractorRun (4), TestFullPipeline (5)
- `src/lucy_ng/cli/fragment.py` (MODIFIED) — Added build command with --sample recall validation

## Decisions Made

- Ring-centred environments expand ring bonds plus all bonds to immediate non-ring neighbours (radius 1 expansion from all ring atoms), not a fixed BFS from ring centroid
- Sample mode counts processed compounds only (not skipped) against the limit — correct semantics for "validate on N compounds with shifts"
- `validate_self_search` uses Python bytes arithmetic for Boolean-AND pre-screening (no numpy dependency in the validation path)
- Function signature uses `Sequence[tuple[int | None, float]]` (covariant) instead of `list[tuple[int | None, float]]` (invariant) to allow passing `list[tuple[int, float]]` without mypy error

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Lint] Removed unused imports and variables**
- **Found during:** Task 1 ruff check
- **Issue:** `dataclasses.field` imported but unused; `ring_atom_set` variable assigned but unused
- **Fix:** Removed unused import and variable
- **Files modified:** `src/lucy_ng/fragments/extractor.py`

**2. [Rule 3 - Type] Changed list to Sequence for covariant type**
- **Found during:** Task 1 mypy check
- **Issue:** `list[tuple[int | None, float]]` is invariant — calling `extract_fragments_for_compound(smiles, indexed)` where `indexed: list[tuple[int, float]]` caused a mypy error
- **Fix:** Changed `atom_shifts` parameter type from `list[...]` to `Sequence[...]` (covariant)
- **Files modified:** `src/lucy_ng/fragments/extractor.py`

**3. [Rule 3 - Lint] Renamed unused loop variables in validate_self_search**
- **Found during:** Task 1 ruff check
- **Issue:** `compound_id` and `smiles` loop variables in validate_self_search not used (only `shifts` needed)
- **Fix:** Renamed to `_compound_id` and `_smiles`
- **Files modified:** `src/lucy_ng/fragments/extractor.py`

**4. [Rule 3 - Lint] Removed complex sample limit logic for skipped compounds**
- **Found during:** Task 1 ruff check (E501 line too long)
- **Issue:** Original logic tried to count skipped compounds against sample limit using checkpoint reload — line was 178 chars, and semantically sample should count processed compounds not all iterations
- **Fix:** Simplified — sample only counts processed (non-skipped) compounds; skipped compounds don't consume the sample budget
- **Files modified:** `src/lucy_ng/fragments/extractor.py`

## Issues Encountered

None beyond the lint/type issues fixed above.

## User Setup Required

None. All tests use in-memory SQLite fixture databases.

## Next Phase Readiness

- `extract_fragments_for_compound` ready to extract SSCs from the 928K compound database
- `SSCExtractor.run(sample=1000)` ready for bin-size validation (run before full 24M extraction)
- `lucy fragment build --sample 1000 data/reference/lucy-ng-derep.db` is the user-facing validation command
- Checkpoint system ensures the multi-hour full extraction can be safely interrupted and resumed
- Phase 51 (FragmentSearcher) can now consume the bitsets via `FragmentDatabaseManager.iter_ssc_bitsets()`

---
*Phase: 50-ssc-extraction-pipeline*
*Completed: 2026-02-19*
