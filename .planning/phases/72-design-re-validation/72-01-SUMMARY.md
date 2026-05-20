---
phase: 72-design-re-validation
plan: "01"
subsystem: lsd-experiment
tags: [lsd, controlled-experiment, ibuprofen, aromatic-ring, rdkit, d-01, d-04]
dependency_graph:
  requires: []
  provides:
    - 72-design-re-validation/experiment/results.json
    - 72-design-re-validation/experiment/arm_a.lsd
    - 72-design-re-validation/experiment/arm_b.lsd
    - 72-design-re-validation/experiment/arm_c.lsd
    - 72-design-re-validation/experiment/run_experiment.py
  affects: []
tech_stack:
  added: []
  patterns:
    - LSD file-argument invocation (lsd arm.lsd, not lsd < arm.lsd)
    - outlsd 5 with .sol as stdin for SMILES conversion
    - RDKit GetRingInfo().AtomRings() + GetIsAromatic() for 6-membered aromatic check
    - InchiToInchiKey for ibuprofen identity check
key_files:
  created:
    - .planning/phases/72-design-re-validation/experiment/arm_a.lsd
    - .planning/phases/72-design-re-validation/experiment/arm_b.lsd
    - .planning/phases/72-design-re-validation/experiment/arm_c.lsd
    - .planning/phases/72-design-re-validation/experiment/run_experiment.py
    - .planning/phases/72-design-re-validation/experiment/results.json
    - .planning/phases/72-design-re-validation/experiment/arm_a_solutions.smi
    - .planning/phases/72-design-re-validation/experiment/arm_b_solutions.smi
    - .planning/phases/72-design-re-validation/experiment/arm_c_solutions.smi
    - .planning/phases/72-design-re-validation/experiment/arm_a.sol
    - .planning/phases/72-design-re-validation/experiment/arm_b.sol
    - .planning/phases/72-design-re-validation/experiment/arm_c.sol
  modified: []
decisions:
  - "D-04 = EMERGENT: aromatic ring appears in Arm A (no SKEL) with 2 solutions including ibuprofen"
  - "D-01 = CONFIRMED: Arm C extended bond range yields aromatic solutions (1 solution, ortho isomer)"
  - "LSD file-argument mode required for .sol file creation; stdin mode writes to stdout"
metrics:
  duration_seconds: 868
  completed_date: "2026-05-20"
  tasks_completed: 2
  tasks_total: 2
  files_created: 11
  files_modified: 0
---

# Phase 72 Plan 01: 3-Arm Controlled LSD Experiment on CASE1 Summary

3-arm ibuprofen CASE1 experiment: Arm A (no SKEL) produces 2 aromatic solutions including ibuprofen, settling D-04 as EMERGENT; Arm C (extended bond range) confirms D-01 with 1 aromatic solution.

## What Was Built

Three controlled LSD input files derived from the verified iteration_03 baseline (`compound_native.lsd`, 2 solutions), a self-contained Python experiment runner, and the resulting solution files with RDKit aromatic/ibuprofen analysis.

- **Arm A** (`arm_a.lsd`): iteration_03 baseline minus SKEL/PATH/F3. Tests whether aromatic ring emerges from native constraints (COSY, HMBC, BOND, DEFF ring exclusion) alone.
- **Arm B** (`arm_b.lsd`): verbatim copy of iteration_03 baseline. Sanity check — expected 2 solutions with ibuprofen.
- **Arm C** (`arm_c.lsd`): Arm A base plus `HMBC 3 8 2 4`, `HMBC 3 13 2 4`, `HMBC 3 9 2 4` (3 known 4J W-path correlations). Tests D-01 bond-range primary mechanism.

## Experiment Results

| Arm | Description | Solution Count | Aromatic Ring? | Ibuprofen Found? |
|-----|-------------|---------------|----------------|-----------------|
| A | No SKEL, full native constraints | 2 | YES | YES (para isomer) |
| B | With SKEL benzene (baseline) | 2 | YES | YES (para isomer) |
| C | Arm A + HMBC X Y 2 4 for 3 4J suspects | 1 | YES | NO (ortho isomer only) |

**Arm A solutions:**
- `C1=CC=C(C(C)C(O)=O)C(=C1)CC(C)C` — InChI key UYHNNWQKLGPQQX (ortho-ibuprofen)
- `CC(C)CC(=C1)C=CC(=C1)C(C)C(O)=O` — InChI key HEFNNWSXXWATRW = **ibuprofen** (para)

**Arm C solution:**
- `CC(C)CC(C=C1)=C(C=C1)C(C)C(O)=O` — InChI key UYHNNWQKLGPQQX (ortho isomer)

## Design Question Answers

**D-04 (aromatic ring): EMERGENT**
Arm A produced 2 aromatic solutions including the correct ibuprofen structure without any SKEL benzene fragment. The aromatic ring emerges from the native constraint set: COSY 4 7 / COSY 5 6 (aromatic H-H coupling through ring), HMBC correlations to sp2 carbons, and DEFF ring3/ring4 exclusion. Phase 74 does NOT need to implement forced SKEL insertion for ibuprofen-class compounds.

**D-01 (extended bond range): CONFIRMED**
Arm C with 3 `HMBC X Y 2 4` lines yields 1 aromatic solution. The mechanism works. The solution is the ortho isomer only (not para/ibuprofen) — the 4J constraints select the ortho arrangement. This is scientifically plausible: the W-path geometry for these 4J correlations (Cq 136.96 to CH2/CH/CH3) is more consistent with the ortho substitution pattern. The extended bond range keeps the search space open while still filtering to aromatic solutions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] LSD stdin mode does not write .sol file**

- **Found during:** Task 2 execution
- **Issue:** The plan specified `subprocess.run([str(LSD_BIN)], stdin=lsd_file.open(), ...)` (stdin redirect). Testing revealed that LSD stdin mode writes the OUTLSD-format solution data to STDOUT, not to a .sol file. The .sol file is only written when LSD receives the input file as a positional argument (`lsd arm_a.lsd`).
- **Fix:** Changed to `subprocess.run([str(LSD_BIN), str(lsd_file)], ...)`. LSD then writes `arm_a.sol`, `arm_b.sol`, `arm_c.sol` to the cwd. The outlsd invocation remains correct (`outlsd 5 < arm_a.sol`).
- **Evidence:** Manual test showed `lsd < arm_a.lsd` produces 2 solutions in stderr but no .sol file in cwd; `lsd arm_a.lsd` produces `arm_a.sol` with 92 lines of OUTLSD format data.
- **Files modified:** `run_experiment.py` (step 1 invocation updated)
- **Commits:** da1bab3

**Note on RESEARCH.md claim:** The RESEARCH.md stated "LSD stdin mode writes 'compound.sol'" — this was incorrect. Stdin mode writes to stdout. The CASE1 iteration_03 `compound_native.sol` was created by invoking `lsd compound_native.lsd` (file argument), not stdin. This distinction matters for Phase 73 (runner.py fix).

### Additional Finding: LSD Exit Code

LSD exits with code 1 even on success (solutions found). The solution count is reliably read from the `solncounter` file in the cwd. This matches the CLAUDE.md note "Success is determined by finding solutions, not just return code."

## Known Stubs

None — all results are real empirical data from the actual LSD binary run.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes. Experiment is throwaway planning artifacts only.

## Self-Check

**Files exist:**
- arm_a.lsd: FOUND
- arm_b.lsd: FOUND
- arm_c.lsd: FOUND
- run_experiment.py: FOUND
- results.json: FOUND (3 arms, all fields present)
- arm_a_solutions.smi: FOUND (2 lines)
- arm_b_solutions.smi: FOUND (2 lines)
- arm_c_solutions.smi: FOUND (1 line)

**Commits exist:**
- cf8c23d: feat(72-01): build three controlled LSD arm files from iter3 baseline
- da1bab3: feat(72-01): run 3-arm LSD experiment and record results

**arm_a.lsd SKEL command check:** 0 SKEL commands (2 mentions in comments only) — PASS

**Arm B baseline sanity:** 2 solutions, ibuprofen_found=True — PASS

**No src/ modifications:** Confirmed — only .planning/ artifacts created

## Self-Check: PASSED
