---
phase: 80-long-range-4j-hmbc-connectivity-defect
plan: "03"
subsystem: agent-skills
tags: [skill-surgery, elim-escalation, 4j-hmbc, regression-guard]
dependency_graph:
  requires: [80-01, 80-02]
  provides: [skill-surgery-complete, sc3-regression-guard]
  affects: [blind-case9-uat]
tech_stack:
  added: []
  patterns: [elim-iterative-escalation, cosy-explicit-range-protection, post-hoc-4j-explanation]
key_files:
  created:
    - .planning/phases/80-long-range-4j-hmbc-connectivity-defect/80-ELIM-REGRESSION.md
  modified:
    - ~/.claude/agents/lucy-lsd-engineer.md
    - ~/.claude/agents/lucy-devils-advocate.md
    - ~/.claude/agents/lucy-solution-analyst.md
    - ~/.claude/agents/lucy-diagnostic.md
    - ~/.claude/commands/lucy-ng/case.md
decisions:
  - "D-01/D-02: ELIM iterative escalation is now the primary 4J mechanism in all skill files"
  - "D-03: 4J Deferral Rule removed from lsd-engineer; no AI pre-classification of 4J suspects"
  - "D-04: Post-hoc 4J explanation via lucy lsd analyze only; no removal advisory"
  - "D-05: pyLSD routing block and fallback path removed from lsd-engineer"
  - "D-07: >10 solutions minimisation stopping condition removed; plausible solution stopping rule added"
  - "D-08: Stopping rule encodes smallest ELIM N yielding >= 1 plausible solution"
  - "COSY-protection: COSY X Y 3 3 explicit-range required for all aromatic equivalence pairs (ELIM-immune per LSD manual line 521)"
  - "SC-3 locked: Arm A + ELIM 1 0 ibuprofen run confirms aromatic ring in rank #1 (C13H18O2 para-disubstituted benzene)"
metrics:
  duration: "~90 minutes"
  completed: "2026-06-09"
  tasks: 3
  files: 6
---

# Phase 80 Plan 03: Agent Skill Surgery + SC-3 Regression Guard Summary

**One-liner:** Surgical removal of pyLSD/4J-Deferral machinery from 5 skill files and live LSD regression confirmation that ELIM N=1 preserves ibuprofen aromatic ring (rank #1, C13H18O2, 6 aromatic atoms verified by RDKit).

## What Was Built

### Task 1: lsd-engineer.md Surgery

- **Removed** the "4J Deferral Rule" section (~38 lines) — the aromatic↔aliphatic heuristic that deferred correlations to `deferred_4j`, the ">10 solutions" batch trigger, and the deferred_4j population logic
- **Removed** the pyLSD fallback routing block — `lucy pylsd run`, `pylsd_mode` checks, `HMBC X Y 2 4 ; ELIM` convention
- **Removed** pyLSD inventory fields (`pylsd_mode`, `elim_annotated`, `deferred_4j`) from schema table and example block
- **Rewrote** "ELIM Command (LAST RESORT)" → "ELIM Escalation (Phase 80 D-01/D-02)": iterative N=0→1→2→3 protocol with stopping rule (D-08)
- **Rewrote** Adaptive Loop stopping conditions: `solution_count <= 10` → `>= 1 plausible solution (aromatic/DBE-consistent)`
- **Rewrote** Zero-Solution Recovery step 7: old ELIM heuristic → ELIM escalation per protocol
- **Added** COSY explicit-range protection: `COSY X Y 3 3` required for all aromatic equivalence pairs (LSD manual line 521 guarantee)
- **Added** `elim_budget: int` field to inventory schema (replaces retired pyLSD fields)
- **Fixed** HMBC example: removed `HMBC 3 8 2 4` (immune to ELIM), replaced with plain `HMBC 1 2` with comment
- **Updated** [ITERATION-COMPLETE] template: removed per-permutation pylsd blocks; added `ELIM budget: N`

### Task 2: Four Skill File Surgeries

**devils-advocate.md:**
- **Removed** Check 4 pyLSD Mode Consistency (G1 FORM, G2 bare ELIM, G3 annotation, G4 permutation cap) — all enforce the retired pyLSD path
- **Removed** G5 (permutation constraint completeness) and G6 (empty merge) — pyLSD-specific post-run checks
- **Removed** G8 (agent reversion detection, pylsd_mode=true trigger) — dead code
- **Added** Check 4: ELIM Budget Sanity with 4 new gates: G-ELIM-1 (excessive N without escalation history), G-ELIM-2 (HMBC with explicit range immune to ELIM), G-ELIM-3 (ELIM in iteration 1 before all HMBC added), G-ELIM-4 (plain COSY X Y droppable by ELIM)
- **Updated** ELIM Usage section: reframed from "last resort" to primary 4J mechanism
- **Updated** [VALIDATION-PASSED] template: replaced `pyLSD mode:` with `ELIM budget:` field

**solution-analyst.md:**
- **Removed** hardcoded 4J removal advisory ("Identify HMBC correlations... Remove the most suspect ones and re-run LSD")
- **Replaced** with D-04 post-hoc framing: use `lucy lsd analyze` to identify path_length >= 4 correlations; report as plausibility annotation only; do NOT advise removal; escalate ELIM N instead

**diagnostic.md:**
- **Rewrote** "ELIM - Correlation Elimination" section: removed "LAST RESORT ONLY" and "NEVER use ELIM on first LSD run" framing; replaced with "4J tolerance mechanism" description including combinatorial semantics, `lucy lsd analyze` diagnostic use, and N=3 ceiling
- **Rewrote** Check 1 ELIM Presence: removed "FOUND → FAIL" logic; replaced with "ELIM expected when zero-solution recovery reached escalation" — WARNING checks for N>3, iteration 1, explicit bond range, missing COSY 3 3

**case.md:**
- **Removed** "Potential 4J correlations" from [SETUP-COMPLETE] required fields (nmr-chemist no longer classifies 4J suspects per D-03)
- **Renamed** Pattern 1 "ELIM Thrashing" → "ELIM Escalation (runaway-N detection)"; detection criterion changed from "ELIM present in 2+ iterations" to "elim_budget > 3 without plausible solution"
- **Updated** diagnose step for Pattern 1 to check N escalation history and recommend diagnostic specialist at N=3
- **Updated** intervene step for Pattern 1 advisory template: "runaway ELIM escalation detected, escalate to diagnostic specialist, do NOT continue"
- **Updated** Solution Explosion advisory: removed "Remove ELIM if present" reflex; added ELIM as final zero-solution mechanism

### Task 3: Arm A + ELIM 1 0 Regression Experiment

Live LSD run on `.planning/phases/72-design-re-validation/experiment/arm_a.lsd` with `ELIM 1 0` appended:
- **LSD binary:** `/Users/steinbeck/Dropbox/develop/LSD/lsd` (confirmed available)
- **Solutions found:** 7
- **Top-1:** `CC(C)Cc1ccc(C(C)C(=O)O)cc1` (canonical) — para-disubstituted ibuprofen, 6 aromatic atoms, C13H18O2, MAE 2.371 ppm, matched 8/13
- **Aromatic ring in top-3:** YES (top-2 both aromatic, confirmed by RDKit)
- **Verdict:** PASS
- **Result file:** `.planning/phases/80-long-range-4j-hmbc-connectivity-defect/80-ELIM-REGRESSION.md`

## Deviations from Plan

None — plan executed exactly as written. All 8 acceptance criteria for Task 1, all 8 for Task 2, and all 5 for Task 3 satisfied.

## Known Stubs

None. All skill edits encode live logic, not placeholders.

## Threat Flags

No new security-relevant surface introduced. This plan edits agent skill markdown files and runs the local LSD binary against a committed fixture file. No auth, network, or untrusted input involved.

## Self-Check: PASSED

- 80-ELIM-REGRESSION.md exists at `.planning/phases/80-long-range-4j-hmbc-connectivity-defect/80-ELIM-REGRESSION.md`
- Commit `34ebd2f` exists: `feat(80-03): add SC-3 regression guard — Arm A + ELIM 1 0 ibuprofen result`
- pytest 1047 passed, 0 failed
- All 16 grep acceptance criteria (Tasks 1+2) return correct counts
