---
phase: 89-blind-uat-validation-gate
verified: 2026-06-28T00:00:00Z
status: passed
score: 3/3 UAT requirements satisfied
verifier: orchestrator (independent RDKit InChIKey verification of each blind run)
---

# Phase 89: Blind-UAT Validation Gate — Verification

**Goal:** Independent blind CASE runs prove the RANK (86) / IDENT (87) / MULT (88) fixes
hold end-to-end and surface any remaining "clean-but-wrong" defect class.

All blind runs were executed by fresh blind Claude instances (`feedback_blind_uat`); the
orchestrator only bookkept and independently RDKit-verified each result by InChIKey block1.
Full per-run detail: `89-UAT-TRACKING.md`.

## Requirement outcomes

- **UAT-01 (CASE4 → MULT):** v9.1-PASS (CONDITIONAL). The Phase-88 multiplicity machinery
  fired + verified live (`[MULTIPLICITY-AMBIGUOUS]`, 3 ethyl families each searched in own
  `iteration_NN_<family>/` dir, coverage_gate PASS, deduped union → 15 [5,7] di-methyl-ethyl
  azulenes). The wrong-class (iPr-only) exclusion that caused the 06-23 FAIL is fixed. The exact
  truth regiochemistry (chamazulene `FVZVDQVUOAAMCG`) is still absent — a NEW, separate
  azulene-regiochemistry-enumeration defect (todo `2026-06-25-case4-azulene-regiochemistry-enumeration-gap`),
  accepted as a documented v9.1 follow-up gap (UAT-03 spirit: new defect class need not be fixed in v9.1).

- **UAT-02 (CASE5 → IDENT):** PASS. Indigo at rank 1 (block1 `COHYTHOBJLSHDF`, RDKit-verified),
  name tool-derived and correctly held tentative (`lucy identify` ran at CASE runtime).

- **UAT-03 (CASE6/7/8 first blind runs):** 3/3 CLEAN PASS, all RDKit-verified:
  - CASE6 citronellol (`QMVPMAAFGQKVCJ`, rank 1, MAE 0.52).
  - CASE7 virgiline (`UGCQEPKCDSOOAO`, rank 1, MAE 0.78) — IDENT gate correctly flagged the
    recalled name "hydroxymatrine" ([G-IDENT-FLAGGED]); no hallucination asserted.
  - CASE8 eugenol (`RRAFCDWBNXTKKO`, rank 1, MAE 0.40) — first `confirmed` IDENT verdict;
    correctly distinguished from isoeugenol.
  No new defect class surfaced (one minor DB-synonym observation on eugenol; non-blocking).

## Cross-cutting live confirmations

- `lucy identify` reachable + run at CASE runtime in every case (closes Phase-87 GAP-87-A end-to-end).
- All three IDENT verdict branches exercised: `confirmed` (CASE8), structure-only/tentative
  (CASE6/7), name↔structure mismatch flagged.
- The post-solution G-IDENT advisory gate (case.md wiring, commit 87db328) fired in CASE6/7/8 —
  both [G-IDENT-PASSED] (CASE6/8) and [G-IDENT-FLAGGED] (CASE7) branches confirmed.
- Phase-88 MULT machinery: fires when ambiguous (CASE4), correctly dormant when firm (CASE6/7/8).

## Verdict

PASSED. v9.1 milestone gate closed. One documented non-blocking follow-up
(CASE4 azulene-regiochemistry enumeration) carried to a future milestone.
