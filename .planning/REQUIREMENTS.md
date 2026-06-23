# Milestone v9.1 Requirements — CASE Final-Answer Correctness & Verification Gates

**Goal:** Ensure the final reported structure is correct AND independently verified —
close the three "clean-but-wrong" defect classes (low MAE, plausible, but wrong) that
slip through every existing safety net, proven by blind UATs.

**Source:** three pending defect todos surfaced by the v9.0/post-v9.0 blind UAT campaign
(`2026-06-{17,21,23}-*.md`); full audit in the gitignored `CASE-UAT-LOG.md`.

---

## v9.1 Requirements

### RANK — Ranker correctness (`lucy lsd rank` ↔ `lucy predict c13`)
- [x] **RANK-01**: `lucy lsd rank` and `lucy predict c13` produce the same per-shift 13C prediction for an identical molecule (single prediction path; no divergent code).
- [x] **RANK-02**: For a correct structure, the ranker no longer systematically under-scores the truth — its MAE / match-count agrees with `lucy predict c13` within a defined tolerance.
- [x] **RANK-03**: A regression test pins ranker↔predict agreement on the CASE1 and CASE3 molecules where divergence was measured (2.23 vs 0.27; ranker put the wrong isomer #1).

### IDENT — Final identity-verification gate
- [x] **IDENT-01**: The solution-analyst derives compound identity from the SMILES via a tool (InChIKey / structure lookup), and never asserts a recalled trivial name as fact.
- [x] **IDENT-02**: An independent final gate (devils-advocate and/or `verify_case_solution.py`) checks the analyst's name↔structure mapping before results are reported; a mismatch blocks/flags the report.
- [x] **IDENT-03**: When identity cannot be tool-confirmed, the report marks the name as tentative (with confidence) rather than asserting it.

### MULT — Aliphatic multiplicity robustness (hardens v9.0 FIX-10)
- [ ] **MULT-01**: When aliphatic multiplicity is not hard-determinable (non-multiplicity-edited HSQC and/or unreliable/phase-distorted APT/DEPT), the lsd-engineer searches ALL viable multiplicity families (e.g. iPr-path `3×CH₃+CH` AND ethyl-path `2×CH₃+CH₂+CH₂`) rather than hard-coding one.
- [ ] **MULT-02**: An MAE-independent clean-but-wrong guardrail: if ≥2 viable multiplicity families exist but only one was searched, the run does not accept — it reopens and searches the other(s).
- [ ] **MULT-03**: A devils-advocate "evidence FOR model X" multiplicity flag forces model X into the search space; it cannot be dismissed by the convergence narrative.
- [ ] **MULT-04**: The nmr-chemist emits an explicit "multiplicity-ambiguous → enumerate families" signal when HSQC is not multiplicity-edited, so the lsd-engineer acts on it deterministically.

### UAT — Blind-UAT validation gate (proves the fixes; surfaces a 4th defect if any)
- [ ] **UAT-01**: CASE4 re-run blind → chamazulene's di-methyl-ethyl constitution is present in the solution set (truth reachable), regardless of which regioisomer ranks #1. (Direct acceptance test for MULT.)
- [ ] **UAT-02**: CASE5 re-run blind on sanitised data passes — correct structure at rank 1 AND name correctly derived from structure (acceptance for IDENT).
- [ ] **UAT-03**: CASE6, CASE7, CASE8 first blind runs executed and bookkept; any new defect class surfaced is captured as a todo (does not have to be fixed in v9.1).

---

## Future Requirements (deferred)

- [ ] Solvent-aware 13C prediction (improves ranker accuracy on shifted systems; orthogonal to RANK code-path unification)
- [ ] HOSE-DB coverage for non-benzenoid aromatics (azulene gap seen in CASE4 — ranking can't resolve regiochemistry there even with the right class in the set)
- [ ] NOESY/ROESY spatial constraints to break regiochemical ties (would resolve CASE4 substituent positions)

## Out of Scope

- Resolving azulene regiochemistry by 13C alone — physically unresolvable (top isomers within 0.26 ppm MAE); v9.1 only requires the correct *constitution class* to be reachable, not unique regiochemistry.
- New solver backends / pyLSD revival — v9.0 settled on the single native-LSD path (D-02); v9.1 does not reopen it.
- Stereochemistry (E/Z, R/S) — unchanged from prior milestones.
- Re-running already-valid blind passes (CASE1/2/3/9) — they stand.

## Traceability

*(each REQ-ID mapped to exactly one phase — 13/13 mapped)*

| REQ-ID | Phase | Status |
|--------|-------|--------|
| RANK-01 | Phase 86 | Complete |
| RANK-02 | Phase 86 | Complete |
| RANK-03 | Phase 86 | Complete |
| IDENT-01 | Phase 87 | Complete |
| IDENT-02 | Phase 87 | Complete |
| IDENT-03 | Phase 87 | Complete |
| MULT-01 | Phase 88 | pending |
| MULT-02 | Phase 88 | pending |
| MULT-03 | Phase 88 | pending |
| MULT-04 | Phase 88 | pending |
| UAT-01 | Phase 89 | pending |
| UAT-02 | Phase 89 | pending |
| UAT-03 | Phase 89 | pending |
