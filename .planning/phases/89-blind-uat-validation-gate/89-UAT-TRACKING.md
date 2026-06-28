---
phase: 89-blind-uat-validation-gate
status: complete
created: 2026-06-25
completed: 2026-06-28
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
| CASE6 | (R)-Citronellol (3,7-dimethyloct-6-en-1-ol) | C10H20O | `QMVPMAAFGQKVCJ` | ✅ CLEAN PASS (06-27) | top `CC(C)=CCCC(C)CCO` → block1 `QMVPMAAFGQKVCJ` (RDKit-verified = truth), rank 1, MAE 0.52, 10/10. IDENT: name "citronellol" tool-downgraded to tentative (COCONUT CNP0152105, no stored name — DB-coverage gap, not a real mismatch). **G-IDENT advisory gate FIRED → [G-IDENT-PASSED]** (first live confirmation of the case.md identity_gate wiring, commit 87db328). MULT machinery correctly DORMANT (HSQC mult-edited + DEPT-90 clean → not ambiguous, no false-trigger). No new defect. |
| CASE7 | Virgiline (lupin alkaloid, lactam + sec-OH) | C15H24N2O2 | `UGCQEPKCDSOOAO` | ✅ CLEAN PASS (06-28) | top `O=C1C2CC(CN3CCC(O)CC23)C2CCCCN12` → block1 `UGCQEPKCDSOOAO` (RDKit-verified = truth virgiline), rank 1, MAE 0.78, 14/15, decisive 0.34 gap. COCONUT CNP0175444 (confirmed-structure). **IDENT gate did its job:** analyst recalled name "hydroxymatrine" → `lucy identify` returned tentative + warning, AND **G-IDENT FIRED → [G-IDENT-FLAGGED]** (independent reasoning: 0.78 MAE doesn't fix the specific OH-regio/stereo; concurs with the tool) → name held `(tentative, unverified)`, NO hallucination asserted, structure reported by InChIKey/SMILES. Best live demonstration of the parametric-naming defense (this is the [G-IDENT-FLAGGED] branch; CASE6 showed [G-IDENT-PASSED]). MULT correctly dormant ([MULTIPLICITY-FIRM]; N-oxide family excluded by firm ruling, not unsearched). Autonomous iter2→iter3 self-correction (wrong N-oxide MAE 3.22 → correct lactam+carbinol MAE 0.78). No new defect. |
| CASE8 | Eugenol | C10H12O2 | `RRAFCDWBNXTKKO` | ✅ CLEAN PASS (06-28) | top `C=CCc1ccc(O)c(OC)c1` → block1 `RRAFCDWBNXTKKO` (RDKit-verified = truth eugenol), rank 1, MAE 0.40, 10/10. Correctly distinguished from isoeugenol (`BJIOGJUNALELMI`) + O-regioisomer. **IDENT `confirmed` branch (first across UATs):** `lucy identify` returned verdict `confirmed` (NMRShiftDB hit with name "2-Methoxy-4-(2-propenyl)phenol") → name stated plainly (D-07). **G-IDENT FIRED → [G-IDENT-PASSED]** (independent reasoning explicitly ruling out isoeugenol's 1-propenyl). MULT correctly dormant (edited HSQC). Minor obs (not a defect): supplying the literal token "eugenol" gave tentative (DB synonym-list miss); a clean run gave confirmed via the canonical name — conservative/safe. No new defect. |

(CASE6 = blind-safe; CASE7 = blind-safe; CASE8 needs the sanitise check confirmed before the run — see [[project_case_datasets_not_sanitised]].)

---

## Phase 89 close-out criteria

- [x] UAT-01: CASE4 — di-methyl-ethyl azulene CLASS RDKit-verified present (15 [5,7] candidates); MULT fix validated. **Accepted as v9.1-PASS (CONDITIONAL)** 2026-06-25; exact-truth regiochemistry gap documented as a follow-up todo (not a v9.1 blocker).
- [x] UAT-02: CASE5 indigo at rank 1 + name tool-derived (PASS 2026-06-24).
- [x] UAT-03: CASE6 (citronellol), CASE7 (virgiline), CASE8 (eugenol) — all CLEAN PASS, RDKit-verified; no new defect class surfaced (one minor DB-synonym observation on eugenol, non-blocking).
- [x] Every reported structure independently RDKit-verified by InChIKey (never self-report).

**PHASE 89 COMPLETE 2026-06-28.** v9.1 milestone gate closed: UAT-01 v9.1-PASS (conditional —
documented azulene-regiochemistry follow-up todo), UAT-02 PASS, UAT-03 3/3 CLEAN PASS. The
RANK (86) / IDENT (87) / MULT (88) fixes hold end-to-end on independent blind runs. Live-confirmed
across the gate: `lucy identify` all three verdict branches (confirmed=CASE8, structure-only/tentative=CASE6/7,
name↔structure flag), and the new post-solution G-IDENT gate firing both [G-IDENT-PASSED] (CASE6/8)
and [G-IDENT-FLAGGED] (CASE7).

### Blind-safety per case (UAT-03)
- **CASE6** (citronellol) — blind-safe (original `Unknown_…`).
- **CASE7** (virgiline) — blind-safe (`unknown_compound` redaction).
- **CASE8** (eugenol) — sanitised 2026-06-21; **blind-validity re-confirmed read-only 2026-06-28: 0 residual "eugenol" tokens in Bruker metadata, no NAME2/3 leak, no stale analysis dir.** Run in progress.
