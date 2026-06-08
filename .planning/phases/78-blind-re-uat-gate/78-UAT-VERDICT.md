---
phase: 78-blind-re-uat-gate
date: 2026-06-08
overall_verdict: DOES_NOT_SHIP
uat_03: PASS
uat_04: FAIL
---

# 78 — v9.0 Milestone Gate Verdict (AND-gate roll-up)

This is the authoritative record of whether v9.0 ships. The AND-gate (D-78-05) requires **both**
UAT-03 and UAT-04 to PASS. It does not soften a FAIL to PASS (T-78-13).

## Verdict table

| Compound | Formula | UAT req | Verdict | Note |
|----------|---------|---------|---------|------|
| CASE1 | C13H18O2 | UAT-03 | **PASS** | Ibuprofen found as solution #2; ring fully EMERGENT (no ring-BOND/SKEL); clean pass (78-UAT-CASE1.md) |
| CASE9 | C12H16O3 | UAT-04 | **FAIL** | Correct structure never reached; ring forced via 6 ring-BONDs (D-04); upstream peak-picker dropped the ester carbonyl (78-UAT-CASE9.md) |
| **AND-GATE** | — | UAT-03 AND UAT-04 | **FAIL** | One compound fails → gate fails |

## Phase 78 success-criteria check

- **SC-1 (blind run + `verify_case_solution.py` exit 0 on each):** PARTIAL. Both runs were blind
  and both `solutions.smi` exit 0 — **but** the CASE9 harness pass is formula+aromatic only; the
  correct CASE9 structure is absent from every iteration. CASE1 ✓, CASE9 ✗ (structurally).
- **SC-2 (SYME=0, DEFF NOT=0, SKEL=0, native present, ring emergent or documented escalation):**
  CASE1 = native + EMERGENT (clean). CASE9 = native (SYME/DEFF NOT/SKEL=0) but ring via
  **documented D-04 ring-BOND escalation** (conditional), because emergent COSY had no input.
- **SC-3 (0 path-changing interventions; `lucy lsd run` primary):** CASE1 ✓. CASE9 ✗ —
  governance-deadlock user re-route + outlsd `#`-comment parse bug in iter 1.
- **SC-4 (AND-gate: both PASS → ships; failure documented for follow-up):** AND-gate = FAIL;
  failure documented here and in 78-UAT-CASE9.md; follow-up seeded as Phase 79.

## Milestone outcome

**v9.0 DOES NOT SHIP** — the AND-gate fails on UAT-04 (CASE9).

Next: Phase 79 addresses the upstream peak-picking / symmetry-detection defect that caused the
CASE9 failure (criteria C1/C2/C3), then CASE9 is re-run blind.

## Forensics (CASE9 — UAT-04 FAIL)

**Failed criteria:** C1 (correct structure never reached), C2 (ring forced, not emergent — only
conditional), C3 (governance-deadlock re-route + outlsd parse bug).

**On-disk evidence:**
- `…/CASE9/analysis/iteration_04/solutions.smi` — all 12 finals are phenyl-ether/acetal scaffolds;
  no ester, no para-disubstitution; true structure `CC(O)c1ccc(C(=O)OC(C)C)cc1` absent.
- `…/CASE9/analysis/iteration_05/compound.lsd` — `BOND 1 2/1 3/2 4/3 5/4 6/5 6` (forced ring).
- `…/CASE9/12` (raw 13C) — carbonyl at **166.08 ppm, SNR≈17**, **not** in `lucy pick 1d` default
  output (CDCl₃ triplet at 77 ppm @ 4.6e7 dominates the max-relative threshold); intensity
  doubling at 129.94/125.31/22.10 (the para-symmetry) not used by symmetry detection.

**Root cause (1-2 sentences):** A single upstream peak-picking/symmetry defect: the weak
quaternary ester carbonyl is masked by the CDCl₃-dominated relative threshold (so DBE is computed
without it, forcing an extra ring), and 13C intensity doubling that encodes para-symmetry is
ignored (so the ring reads as monosubstituted, leaving `lucy detect aromatic-cosy` with no
equivalence pairs and disabling the emergent-ring mechanism). The Phase-77 LSD mechanism is not
refuted — it never received correct input.

**Recommended D-76-07 follow-up (Phase 79):**
1. Peak-picker: SNR-based threshold and/or CDCl₃-multiplet exclusion before threshold computation.
2. Symmetry detection: use 13C peak intensity as a 2C-equivalence indicator feeding
   `lucy detect aromatic-cosy`.
3. Re-run CASE9 blind via the fixed stack; re-apply this AND-gate.

## What this phase delivered

- `78-SANITISATION-CHECK.md` — pre-run blindness audit (CASE1 + CASE9 identity-clean, gate READY)
- `78-UAT-CASE1.md` — CASE1 evidence + UAT-03 **PASS** (emergent, clean)
- `78-UAT-CASE9.md` — CASE9 evidence + UAT-04 **FAIL** + root-cause forensics
- `78-UAT-VERDICT.md` — this file; AND-gate roll-up; **v9.0 DOES NOT SHIP**
