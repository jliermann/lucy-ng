---
phase: 72-design-re-validation
plan: "02"
subsystem: planning
tags: [architecture-decisions, design, lsd, 4j-handling, aromatic-ring, constraint-translation]
status: awaiting-checkpoint
completed_date: "2026-05-20"

dependency_graph:
  requires:
    - 72-01 (experiment results.json)
  provides:
    - 72-DECISIONS.md (locked architecture decisions for Phases 73-76)
  affects:
    - Phase 73 (outlsd plumbing fix)
    - Phase 74 (generator native-only emission + constraint preservation)
    - Phase 75 (skill doc single-path rewrite)

tech_stack:
  added: []
  patterns:
    - evidence-driven architecture decision document
    - controlled experiment → verdict mapping

key_files:
  created:
    - .planning/phases/72-design-re-validation/72-DECISIONS.md
  modified: []

decisions:
  - "D-04 = EMERGENT: Arm A produced 2 aromatic solutions including ibuprofen without SKEL forcing"
  - "SYME → DUPL is INCORRECT; correct native mechanism is BOND/COSY structural constraints"
  - "Phase-65 0/90 postmortem figure corrected to 5/90 with constraint-loss confound explanation"
  - "D-01 primary = HMBC X Y 2 4; Arm C confirms it is viable but over-constrains when all 3 added simultaneously"
  - "D-02 = single primary path; agent-reversion hypothesis CONFIRMED"

metrics:
  duration_seconds: 129
  tasks_completed: 1
  tasks_total: 2
  files_created: 1
  files_modified: 0
  note: "Plan 02 is autonomous=false; stops at checkpoint:human-verify after Task 1"
---

# Phase 72 Plan 02: Architecture Decisions Document Summary

**One-liner:** D-04 EMERGENT verdict from Arm A (2/2 aromatic without SKEL); SYME→DUPL corrected to BOND/COSY native; per-phase implications written for Phases 73-75.

## What Was Built

`72-DECISIONS.md` — the locked architecture decision document answering Q1-Q4 from the v8.0 UAT postmortem, grounded in results.json from the Phase 72 Plan 01 controlled experiment.

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write 72-DECISIONS.md from experiment results | 1bd4607 | .planning/phases/72-design-re-validation/72-DECISIONS.md |
| 2 | checkpoint:human-verify | — | Awaiting sign-off |

## Decisions Made

### Q1: D-01 — Extended bond range primary (CONFIRMED)
Arm C produced 1 aromatic solution with `HMBC X Y 2 4` for 3 known 4J correlations. Extended bond range is viable. Over-constraining all 3 simultaneously excludes ibuprofen (ortho-isomer survives); the implementation should add them incrementally.

### Q2: D-02 — Single primary path (CONFIRMED)
Agent-reversion hypothesis confirmed: iter3 used direct lsd binary with K=0 (no permutations) after merge=0 failures. One prominently-documented path is the architectural fix.

### Q3: D-03 — SYME→DUPL is INCORRECT
DUPL is output deduplication (not structural equivalence). The correct native SYME translation is BOND/COSY structural constraints (verified in iter3/compound_native.lsd). Phase 74 must map each SYME use site to the appropriate BOND/COSY pattern.

### Q4: D-04 — EMERGENT
Arm A: 2 solutions, both aromatic (100%), ibuprofen (HEFNNWSXXWATRW) present. Phase 74 does not need SKEL benzene insertion in the normal path.

### Phase-65 Re-evaluation
The postmortem "0/90" figure is corrected to **5/90** (RDKit-verified iter2 solutions). The constraint-loss bug (SYME/DEFF NOT stripped) was suppressing aromatic solutions. Arm A (full constraints, no bug) → 2/2 aromatic.

## Automated Verification Results

All three plan verification checks passed:
- PASS: all 4 Q-sections present (Q1-Q4 Answer)
- PASS: all required content (DUPL, SYME, INCORRECT, EMERGENT, 5/90, Phase 73-75)
- PASS: D-01 through D-04 all referenced

## Deviations from Plan

None — plan executed exactly as written. The results.json data was directly consumable; no unexpected findings required deviation.

## Known Stubs

None. The decision document is complete and evidence-grounded. The only open item is the human-verify checkpoint sign-off.

## Threat Flags

None. 72-DECISIONS.md is a planning document. No new network endpoints, auth paths, or schema changes introduced.

## Self-Check: PASSED

- [x] `.planning/phases/72-design-re-validation/72-DECISIONS.md` exists
- [x] Commit 1bd4607 exists: `git log --oneline | grep 1bd4607` confirms
- [x] All 3 automated verification checks passed
- [x] No file deletions in commit

---

*Plan status: AWAITING CHECKPOINT — Task 2 (human-verify) pending user sign-off*
