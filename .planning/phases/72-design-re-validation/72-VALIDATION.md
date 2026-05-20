---
phase: 72
slug: design-re-validation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-20
---

# Phase 72 — Validation Strategy

> Design-decision phase. Validation = the controlled experiment produced real evidence + the decision document answers every question. No production code ships here.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | direct LSD binary + outlsd + RDKit (experiment); manual review (decision doc) |
| **Config file** | none (throwaway experiment artifacts) |
| **Quick verify command** | `python3 -c "from rdkit import Chem; ..."` aromatic check on experiment SMILES output |
| **Full suite command** | `pytest -q` (regression — confirm no Python broke; this phase should touch little/no shipped code) |
| **Estimated runtime** | experiment LSD runs ~1-5 min; RDKit check seconds |

---

## Sampling Rate

- **After the experiment task:** RDKit aromatic-ring check on the produced SMILES; record solution counts
- **After the decision-doc task:** manual read — all 4 questions answered YES/NO + rationale + per-phase implication
- **Before phase close:** `pytest -q` green (no regression if any code was touched)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | 1 | DESIGN-01 | Arm A (no forced fragment) experiment runs; aromatic ring presence determined by RDKit | integration | `python3 <aromatic_check.py> <armA_smiles>` (skipif LSD missing) | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | DESIGN-01/04 | Arm A vs Arm B (forced fragment) solution counts + aromatic counts recorded | integration | experiment script emits both arms' counts | ❌ W0 | ⬜ pending |
| TBD | TBD | 1 | DESIGN-01, DESIGN-02 | Decision document answers all 4 design questions with YES/NO + rationale + per-phase implication | doc | `grep -E "DESIGN-01\|DESIGN-02\|Q1\|Q2\|Q3\|Q4" <decision-doc>` | ❌ W0 | ⬜ pending |

*Final task IDs filled by planner. Status: ⬜ pending · ✅ green · ❌ red.*

---

## Wave 0 Requirements

- [ ] LSD filter files present: `/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3`, `ring4` (used by DEFF F/FEXP)
- [ ] Benzene fragment file for Arm B (from `iteration_03/filters/benzene.mol`)
- [ ] Experiment starting file: `CASE1/analysis/iteration_03/compound_native.lsd` (the working native file; Arm A = this minus SKEL/benzene lines)
- [ ] RDKit available (already a project dep)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Decision document is actionable for Phases 73-75 | DESIGN-01/02 | Judgment: each decision must name the file/phase it drives | Read decision doc; confirm D-01..D-04 each have a "→ Phase N implements X" line |
| Phase-65 hypothesis honestly re-evaluated | DESIGN-01 | Interpretation of experiment evidence | Confirm doc states whether the aromatic ring emerged from constraints alone, with the iter2 5/90 + constraint-loss confound noted |
| DUPL-vs-SYME finding incorporated | DESIGN-01 | Research found DUPL ≠ SYME; the equivalence mechanism (BOND/COSY structural) must be the decided approach | Confirm decision doc resolves how atom equivalence is natively expressed (not "SYME→DUPL") |

---

## Validation Sign-Off

- [ ] Experiment produced a real LSD run (Arm A) with RDKit-checked aromatic determination
- [ ] Both arms' counts recorded for the emergent-vs-forced decision
- [ ] Decision document answers all 4 questions + per-phase implications
- [ ] DUPL≠SYME correction reflected in the equivalence decision
- [ ] LSD-dependent tasks gated with skipif(LSD missing)
- [ ] `nyquist_compliant: true`

**Approval:** pending
