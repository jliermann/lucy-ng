---
phase: 65-hypothesis-gate
plan: 01
subsystem: validation
tags: [lsd, ibuprofen, 4j-coupling, hypothesis-gate, rdkit, smiles]

requires:
  - phase: v7.0-post-mortem
    provides: "Knowledge that 4J W-pathway HMBC correlations cause LSD to fail on ibuprofen"

provides:
  - "Confirmed: removing 3 4J HMBC correlations from ibuprofen LSD input produces aromatic ring solutions"
  - "Confirmed: correct ibuprofen structure (rank 219/392) is present in solution set"
  - "GO decision for v8.0 pyLSD Integration — Phases 66, 67, 68 unblocked"
  - "ibuprofen_no4j.lsd — reference LSD file with 4J correlations removed (9 HMBC lines)"
  - "ibuprofen_no4j.smi — 392 SMILES solutions for further analysis"

affects:
  - "66-lsd-generator-extensions"
  - "67-pylsd-orchestrator"
  - "68-constraint-inventory-v2"

tech-stack:
  added: []
  patterns:
    - "4J W-pathway removal: exclude HMBC lines where ArCH↔ArCH (cross-ring) or AliphaticCH↔ArCH (benzylic) for para-disubstituted benzenes"
    - "LSD must be invoked with filename argument (not stdin) to create .sol file with # From file: header required by outlsd"
    - "outlsd syntax: outlsd 5 < file.sol (format=5 for SMILES, no count argument)"

key-files:
  created:
    - ".planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd"
    - ".planning/phases/65-hypothesis-gate/ibuprofen_no4j.sol"
    - ".planning/phases/65-hypothesis-gate/ibuprofen_no4j.smi"
    - ".planning/phases/65-hypothesis-gate/validation_result.md"
  modified: []

key-decisions:
  - "GO: v8.0 hypothesis confirmed — 4J HMBC removal causes LSD to produce aromatic ring solutions containing ibuprofen"
  - "Ibuprofen appears at rank 219/392, not rank 1: HOSE-based ranking without aromaticity filter allows non-aromatic isomers to outrank correct structure — Phase 68 (substructure filters) is needed"
  - "LSD runner bug noted but deferred: _run_outlsd calls outlsd without mode argument (needs 5 for SMILES) — outlsd.out contains usage text, not SMILES. Direct outlsd call via Bash is the workaround."

patterns-established:
  - "Hypothesis Gate Pattern: 30-minute manual test before any code is written — v7.0 lesson applied"
  - "4J identification by chemical meaning, not atom numbers — W-pathway requires ArCH↔ArCH cross-ring or AliphaticCH↔ArCH benzylic topology"

requirements-completed: [GATE-01]

duration: 35min
completed: 2026-03-16
---

# Phase 65 Plan 01: Hypothesis Validation Gate Summary

**4J HMBC removal hypothesis CONFIRMED — removing 3 W-pathway correlations causes LSD to produce ibuprofen (aromatic) among 392 solutions; v8.0 GO decision issued**

## Performance

- **Duration:** ~35 min
- **Started:** 2026-03-16T11:20Z
- **Completed:** 2026-03-16T11:55Z
- **Tasks:** 2
- **Files created:** 4

## Accomplishments

- Created `ibuprofen_no4j.lsd` with 3 known 4J HMBC correlations removed (12 → 9 HMBC lines)
- LSD found 392 solutions (vs 7 in the original v4.0 run with 4J included)
- RDKit check: 3 of 392 solutions have 6 aromatic atoms — all 3 canonicalize to ibuprofen
- Ibuprofen confirmed at rank 219/392 via InChI comparison
- Decision: **GO** — Phases 66, 67, 68 unblocked

## Task Commits

1. **Task 1: Create modified LSD file with 4J correlations removed and run LSD** - `7503a44` (feat)
2. **Task 2: Convert solutions to SMILES and check for aromatic rings with RDKit** - `2fe6462` (feat)

## Files Created

- `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.lsd` — Modified LSD input (9 HMBC lines, 4J removed)
- `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.sol` — LSD solution file (392 solutions, 6377 lines)
- `.planning/phases/65-hypothesis-gate/ibuprofen_no4j.smi` — SMILES for all 392 solutions
- `.planning/phases/65-hypothesis-gate/validation_result.md` — Full GO/NO-GO decision document with evidence

## Decisions Made

- **GO: v8.0 confirmed** — The core hypothesis holds. Removing 4J W-pathway HMBC correlations allows LSD to find the aromatic (correct) structure.
- **Ibuprofen at rank 219, not rank 1** — This is expected and acceptable. HOSE-based ranking without aromaticity filter allows non-aromatic isomers to outrank the correct structure. Phase 68 (Constraint Inventory v2) will add substructure filters. The important result is that ibuprofen IS in the solution set.
- **LSD runner bug deferred** — `lucy lsd run` auto-calls `outlsd` without mode argument; `outlsd.out` contains usage text. Direct bash call `outlsd 5 < file.sol` is the workaround. Will track as deferred issue — fix in Phase 66 or 69.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] LSD must be invoked with filename argument, not stdin**
- **Found during:** Task 1 (LSD run)
- **Issue:** `lucy lsd run` uses stdin piping; LSD writes `.sol` file only when given filename argument. Direct `LSD < file.lsd` produced stdout but no `.sol` file; `outlsd` rejected the stdin-captured output as "not a file for OUTLSD."
- **Fix:** Ran `LSD ibuprofen_no4j.lsd` directly (filename argument) which created `ibuprofen_no4j.sol` with the `# From file:` header required by outlsd.
- **Files modified:** None (runtime fix, not code)
- **Verification:** `outlsd 5 < ibuprofen_no4j.sol` produced 392 SMILES successfully
- **Committed in:** 7503a44 (Task 1 commit)

**2. [Rule 3 - Blocking] outlsd does not accept a count argument**
- **Found during:** Task 2 (outlsd conversion)
- **Issue:** Plan specified `outlsd 20 < file.sol` (20 as solution count limit). outlsd only takes format mode (1-9), not a count. Running with 20 produces usage error.
- **Fix:** Used `outlsd 5 < file.sol` (format 5 = SMILES, no count). All 392 solutions converted.
- **Verification:** 392 SMILES generated, RDKit parsed all successfully
- **Committed in:** 2fe6462 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 - blocking tool syntax issues)
**Impact on plan:** Both were CLI invocation corrections. No scope change. Results are complete and valid.

## Issues Encountered

- `outlsd.out` from `lucy lsd run` contains usage text (bug in LSDRunner._run_outlsd: missing mode argument). Not blocking for this plan — used direct `outlsd` call. Noted as deferred fix.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

**GO — all three parallel phases unblocked:**
- **Phase 66** (LSDInputGenerator Extensions): Add `generate_with_extended_range()` method supporting HMBC 2-4J range syntax and 4J correlation flagging
- **Phase 67** (PyLSDOrchestrator/Merger): Implement multi-run orchestration (~230 lines Python), merge solution sets from restricted and permissive runs
- **Phase 68** (Constraint Inventory v2): Add ConstraintInventory class with substructure filters, badlist management, aromaticity check

**Reference values for Phase 66/67:**
- 9 retained HMBC lines (genuine 2-3J correlations) in `ibuprofen_no4j.lsd` are the "restricted pass" input
- 3 removed lines (`HMBC 6 8`, `HMBC 10 6`, `HMBC 10 8`) are the 4J candidates for "extended range pass"

---
*Phase: 65-hypothesis-gate*
*Completed: 2026-03-16*
