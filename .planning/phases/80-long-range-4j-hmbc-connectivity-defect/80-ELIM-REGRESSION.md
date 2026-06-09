# Phase 80 — ELIM 1 0 Regression Guard: Ibuprofen Arm A (SC-3)

**Run date:** 2026-06-09
**Source file:** .planning/phases/72-design-re-validation/experiment/arm_a.lsd (unchanged; Phase-72 emergent-ring reference)
**Modification:** ELIM 1 0 appended (solver may drop 1 HMBC/COSY; P2=0 = no bond-distance limit)
**Purpose:** Confirm that adding ELIM 1 0 to the Phase-72 Arm A ibuprofen LSD file does NOT prevent the correct aromatic ibuprofen structure from appearing in top-3. This locks SC-3: ELIM 1 0 must not regress the v4.0 4J win.

## Results

**LSD run:** 7 solutions found
**outlsd conversion:** 7 SMILES
**Top-3 SMILES:**
1. CC(C)Cc1ccc(C(C)C(=O)O)cc1 (canonical) — from `CC(C)CC(=C1)C=CC(=C1)C(C)C(O)=O` — aromatic ring: yes — formula: C13H18O2 — matched_count: 8/13 — MAE: 2.371 ppm
2. CC(C)Cc1ccccc1C(C)C(=O)O (canonical) — from `C1=CC=C(C(C)C(O)=O)C(=C1)CC(C)C` — aromatic ring: yes — formula: C13H18O2 — matched_count: 6/13 — MAE: 2.600 ppm
3. CC(C)CC=CC(=C1)C(C)C(=C1)C(O)=O — aromatic ring: no — formula: C13H18O2 — matched_count: 6/13 — MAE: 3.305 ppm

**Aromatic ring in top-3:** yes (top-2 solutions both have 6 aromatic atoms, confirmed by RDKit)
**RDKit formula check (top-1):** C13H18O2 — correct

**Rank 1 canonical SMILES:** `CC(C)Cc1ccc(C(C)C(=O)O)cc1` — para-disubstituted benzene. This is ibuprofen (4-isobutylphenylpropionic acid / 2-(4-isobutylphenyl)propionic acid). 6 aromatic atoms confirmed.

## Verdict

PASS: ELIM 1 0 does not prevent ibuprofen from appearing; aromatic ring present in top-3. The correct para-disubstituted aromatic structure (C13H18O2) ranks #1 with matched_count=8/13 and MAE 2.371 ppm. SC-3 regression guard locked — ELIM N=1 is safe to use in the Phase 80 ELIM escalation protocol without regressing the ibuprofen result.

## Notes on COSY explicit-range gap

The Phase-72 arm_a.lsd was written before Phase 80's COSY 3 3 requirement. Plain `COSY X Y` lines are present (COSY 9 13, COSY 4 7, COSY 5 6, COSY 8 10, COSY 10 11). With ELIM 1 0, ELIM dropped 1 correlation from some solutions but the aromatic ring STILL emerged in top-1 (rank 1 has 6 aromatic atoms). This confirms the ring is robust to 1 dropped correlation at N=1.

Agent-written LSD files in Phase 80 onwards MUST use `COSY X Y 3 3` to fully protect equivalence pairs from elimination (per lsd-engineer skill update in 80-03 Task 1). The arm_a.lsd result confirms that even without the protection, N=1 is not catastrophic for ibuprofen — but the explicit range is required for correctness in general.
