---
phase: 89-blind-uat-validation-gate
status: in_progress
created: 2026-06-25
requirements: [UAT-01, UAT-02, UAT-03]
---

# Phase 89 — Blind-UAT Validation Gate — Tracking

> **Goal:** Independent blind CASE runs prove the RANK (86) / IDENT (87) / MULT (88) fixes
> hold end-to-end and surface any remaining "clean-but-wrong" defect class.
>
> **ORCHESTRATOR-ONLY FILE.** This document lives under `.planning/` and is NEVER loaded
> during a CASE run (CASE runs in external NMR data directories). The truth InChIKeys below
> are verification targets for the bookkeeper — they MUST NOT leak into any CASE data dir or
> the loaded CASE skill. Blind runs use fresh, blind Claude instances via the `case-blind`
> alias (`feedback_blind_uat`); this orchestrator session only bookkeeps + independently
> verifies — it must NEVER run the CASE itself.

## Bookkeeping protocol (every UAT)

For each blind run, when its result arrives:
1. **Independent RDKit verification — never trust agent self-report.** Take the reported top
   SMILES from the run's `final_results.md` / `merged.smi`, compute its InChIKey with RDKit,
   and compare the **block1 (first 14 chars = 2D constitution)** against the truth target below.
2. Record: structure verdict (constitution match? rank? MAE?), the IDENT behaviour where
   relevant (tool-derived identity, tentative marking), any coordinator interventions, and
   whether any NEW defect class surfaced (→ capture as a todo; need not be fixed in v9.1).
3. Append the one-line verdict to the running `.planning/CASE-UAT-LOG.md` and update this file.
4. A run is only PASS when the constitution is RDKit-verified present per the acceptance below.

---

## UAT-01 — CASE4 (blind) → acceptance test for MULT (Phase 88)

**Status:** 🟡 CONDITIONAL (2026-06-25, orchestrator RDKit-verified) — MULT fix VALIDATED (di-methyl-ethyl class reachable, machinery fired), but exact truth regiochemistry still absent (NEW azulene-regiochemistry defect → todo `2026-06-25-case4-azulene-regiochemistry-enumeration-gap`).

- **Truth:** Chamazulene = 7-ethyl-1,4-dimethylazulene, **C14H16**.
  Truth InChIKey `FVZVDQVUOAAMCG-UHFFFAOYSA-N` (block1 `FVZVDQVUOAAMCG`), SMILES `CCc1ccc2ccc(C)c-2c(C)c1`.
- **Acceptance (regioisomer-independent):** a **di-methyl-ethyl azulene** constitution
  (azulene core + 2×CH₃ + 1×ethyl, C14H16) must be **PRESENT in the solution set** — the truth
  need not rank #1, and the exact regioisomer (hence exact block1) need not match. The prior
  FAIL had ALL solutions as mono-methyl-mono-isopropyl (1×CH₃ + 1×iPr) — the di-methyl-ethyl
  substituent class was a-priori excluded. Pass = that class is reachable.
- **What this proves:** the multiplicity-ambiguous branch enumerated BOTH families (iPr-path
  `3×CH₃+CH` AND ethyl-path `2×CH₃+CH₂+CH₂`) and searched both (per-family runs + union), so the
  ethyl-bearing constitution is in the searched set. Bonus signals to record: did the nmr-chemist
  emit `[MULTIPLICITY-AMBIGUOUS]`? did the DA `[MULT-EVIDENCE-FOR] model=ethyl` flag fire on the
  HMBC-11→13 evidence and force the ethyl family? did the coverage gate hold?

**Result (2026-06-25, orchestrator RDKit-verified):**
- Reported top SMILES (azulene-aware best): `CCc2ccc(C)cc1cc(C)cc12` (block1 `AGJIEFIKCFPZLY`, [5,7] azulene, C14H16) — a di-methyl-ethyl azulene, but NOT chamazulene.
- Final solution set: **15 [5,7] di-methyl-ethyl azulenes** (`iteration_07_anchor_recovery/solutions.smi`), all RDKit-confirmed [5,7] + C14H16 + ethyl+2×methyl.
- **Di-methyl-ethyl azulene CLASS present in solution set?** ✅ YES (all 15). → the MULT-targeted defect (only mono-methyl-iPr class searched) is FIXED.
- **Exact truth chamazulene (`FVZVDQVUOAAMCG`, 7-Et-1,4-diMe) present?** ❌ NO — not among the 15, nor in any searched family. Truth regiochemistry still unreachable.
- **MULT machinery fired:** ✅ `[MULTIPLICITY-AMBIGUOUS]` emitted (HSQC not mult-edited); 3 ethyl families (ethyl33/ethyl24/ethyl_low) enumerated + ALL searched in own dirs; `## Multiplicity Coverage` ledger + coverage_gate verdict PASS; deduped union ranked. iPr class correctly excluded by H-budget (11 aliphatic H → 3×CH₃+1×CH₂).
- **DA [MULT-EVIDENCE-FOR]:** not emitted — direct HMBC evidence (C33.86↔H1.38 mutual) resolved the CH₂ placement to ethyl33 without needing the binding flag.
- **IDENT bonus:** `lucy identify` ran on candidates → verdict novel; name NOT asserted (chamazulene explicitly held tentative). Minor: the analyst's prose cited a WRONG chamazulene reference key `UPRCJVNLNOWREJ` (≠ truth `FVZVDQVUOAAMCG`) — IDENT discipline still held.
- **Verdict:** 🟡 **CONDITIONAL.** Phase-88 MULT acceptance MET (di-methyl-ethyl class now searched/reachable; machinery verified). The strict "exact truth reachable" reading FAILS — chamazulene's specific regiochemistry is absent due to a NEW, separate defect (azulene regiochemistry enumeration / degraded 2D + azulene HOSE-unreliability), captured as a todo. Not a v9.1 blocker (UAT-03 spirit: new defect class need not be fixed in v9.1).

---

## UAT-02 — CASE5 (blind, sanitised) → acceptance test for IDENT (Phase 87)

**Status:** ✅ PASS (Run-2, 2026-06-24, orchestrator-verified — see project_phase87_identity_gate)

- **Truth:** Indigo, **C16H10N2O2**, truth InChIKey `COHYTHOBJLSHDF-BUHFOSPRSA-N` (block1 `COHYTHOBJLSHDF`).
- **Result:** rank-1 = indigo constitution (block1 `COHYTHOBJLSHDF` matched; reported
  `COHYTHOBJLSHDF-UHFFFAOYSA-N`, central-C=C stereo unspecified — constitution correct), MAE 1.64,
  C2-symmetry decisive, indirubin excluded, narrative clean (no mislabel). `lucy identify` RAN at
  CASE runtime and downgraded the recalled name "indigo" → tentative (COCONUT accession CNP0122392,
  no trivial name). IDENT-01/02/03 satisfied live.
- **Note:** the DA G-IDENT advisory layer was not wired at the time of that run; it has since been
  wired into case.md (commit 87db328) — a future blind run can confirm G-IDENT fires.

---

## UAT-03 — CASE6 / CASE7 / CASE8 first blind runs (coverage + defect-surfacing)

**Status:** ⬜ pending (first blind runs not yet executed)

Execute each as a fresh blind run, bookkeep, and capture any NEW defect class as a todo
(does not have to be fixed in v9.1). RDKit-verify each reported structure by block1.

| Case | Truth | Formula | Truth InChIKey (block1) | Status | Reported / verdict |
|------|-------|---------|--------------------------|--------|--------------------|
| CASE6 | (R)-Citronellol (3,7-dimethyloct-6-en-1-ol) | C10H20O | `QMVPMAAFGQKVCJ` | ⬜ pending | `______` |
| CASE7 | Virgiline (lupin alkaloid, lactam + sec-OH) | C15H24N2O2 | `UGCQEPKCDSOOAO` | ⬜ pending | `______` |
| CASE8 | Eugenol | C10H12O2 | `RRAFCDWBNXTKKO` | ⬜ pending | `______` |

(CASE6 = blind-safe; CASE7 = blind-safe; CASE8 needs the sanitise check confirmed before the run — see [[project_case_datasets_not_sanitised]].)

---

## Phase 89 close-out criteria

- [ ] UAT-01: CASE4 di-methyl-ethyl constitution RDKit-verified present in the solution set.
- [x] UAT-02: CASE5 indigo at rank 1 + name tool-derived (PASS 2026-06-24).
- [ ] UAT-03: CASE6/7/8 first blind runs executed + bookkept; new defects → todos.
- [ ] Every reported structure independently RDKit-verified by InChIKey (never self-report).

When UAT-01 + UAT-03 are recorded (UAT-02 already PASS): mark Phase 89 complete, close the
v9.1 milestone gate.
