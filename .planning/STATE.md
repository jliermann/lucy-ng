---
gsd_state_version: 1.0
milestone: v9.0
milestone_name: CASE Reliability & Skill Consolidation
status: executing
stopped_at: Phase 80 closed at FAILED gate (80-UAT-VERDICT.md written, CASE9 FAIL). Phase 80 mechanism (elim_budget, plausibility filter, skill surgery, SC-3 guard PASS) delivered + unit-green (pytest 1054) but the blind CASE9 UAT failed on an UPSTREAM peak-picking defect. Phase 81 (FIX-08) created with full scope in ROADMAP. v9.0 still does not ship.
last_updated: "2026-06-16T07:56:49.645Z"
last_activity: 2026-06-16 -- Phase 85 execution started
progress:
  total_phases: 11
  completed_phases: 11
  total_plans: 34
  completed_plans: 34
  percent: 100
---

# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-20)

**Core value:** AI agent autonomously determines compound structures from NMR, with a multi-agent team that uses the intended solver pipeline — not a manual bypass
**Current focus:** **FIX-12 (Phase 85) DONE + VERIFIED 2026-06-16** — HMBC picker now has an SNR floor (`lucy pick hmbc --snr-floor`, default SNR mode); on CASE1 it RECOVERS the ring-diagnostic 3J-meta correlations (H4→C2 SNR 22.4, H6→C3 SNR 9.8) that legacy fraction-of-max dropped → the data to close the benzene ring emergently is now in the picked set; suite 1079 passed. Both CASE1 (UAT-03) + CASE9 (UAT-04) already SOLVED on Opus 4.8 (AND-gate substantively met; mechanism caveat = documented ring-BOND escalation). **Remaining: FIX-11 (Phase 84, Kekulé canonicalize — small) + the live test: a blind CASE run on Opus 4.8 to confirm the benzene ring now emerges WITHOUT forced ring-BONDs (D-04).** Then the gate-criterion decision (emergent vs documented forcing) likely resolves in favour of emergent. See .planning/research/D04-emergent-ring/ + 85-VERIFICATION.md.

## Current Position

```
Phase 72: Design Re-Validation       [x] Complete
Phase 73: Solution Plumbing Fix      [x] Complete
Phase 74: Constraint Preservation    [x] Complete
Phase 75: Skill Consolidation        [x] Complete
Phase 76: Milestone UAT Gate         [x] Executed — GATE FAILED (CASE1 spirit-fail, CASE9 deferred)
Phase 77: Fix lucy lsd run + Tooling [x] Complete
Phase 78: Blind Re-UAT (CASE1+CASE9) [x] Executed — GATE FAILED (CASE1 UAT-03 PASS, CASE9 UAT-04 FAIL)
Phase 79: Peak-Picking + Symmetry    [x] Complete — carbonyl-masking ELIMINATED (verified live), but CASE9 exposed 4J-HMBC blocker
Phase 80: Long-Range 4J-HMBC Defect  [~] Mechanism delivered + unit-green; blind UAT GATE FAILED (upstream picker defect) → Phase 81
Phase 81: Peak-Picking Integrity     [x] Code complete + VERIFIED (FIX-08) — all 5 fixes a–e shipped, suite 1077 passed
Phase 82: Blind-UAT Skill Hygiene    [x] DONE (FIX-09) — runtime CASE skills decontaminated + migrated into repo/.claude (symlinked); 2026-06-10 CASE9 run invalidated
Phase 83: Constraint-Hardness Guard  [x] DONE + VERIFIED (FIX-10) — advisory rule + G-PROP-EVIDENCE gate + dominant_element tooling; CASE9 truth not excluded; suite 1071 passed. Blind CASE9 re-run = remaining v9.0 ship-gate
```

Progress: [█████████░] 89% (8/10 phases; v9.0 does NOT ship until CASE9 passes)

Phase: 85 (hmbc-peak-picking-integrity) — EXECUTING
Plan: 1 of 2
Status: Executing Phase 85
Last activity: 2026-06-16 -- Phase 85 execution started

**Phase 77 scope (fixes only — decisions in 77-CONTEXT.md):**

1. FIX-01: `lucy lsd run` `_invoke_outlsd` — real solutions.smi + fail-loud on outlsd error + regression test. See memory project-lucy-lsd-run-broken-v9.
2. FIX-02: deterministic cross-ring COSY equivalence emission in tooling → aromatic ring emerges (emergent primary; ring-BOND only as documented escalation per D-77-01/06).
3. FIX-03: retire deprecated lucy-case-agent.md + targeted skill-creator audit (no full rewrite).

**Phase 78 (separate):** blind re-UAT CASE1 + CASE9 via fixed mechanism; harness scripts/verify_case_solution.py already built. UAT-03/04.

Wave structure:

- Wave 0: Phase 72 (gate — must complete before all others; answers 4 open design questions)
- Wave 1: Phase 73 (outlsd/lucy-lsd-run plumbing fix; depends on 72)
- Wave 2: Phase 74 (constraint preservation + merge; depends on 73)
- Wave 3: Phase 75 (skill consolidation; depends on 72 design decisions AND 74 fixed tooling)
- Wave 4: Phase 76 (UAT gate; depends on 75)

## Completed Milestones

| Milestone | Phases | Shipped |
|-----------|--------|---------|
| v1.0 Core CASE Pipeline | 1-10 | 2026-01-12 |
| v1.1 Database-Backed Dereplication | 11-15 | 2026-01-15 |
| v1.2 HOSE Database Prediction | 16-19 | 2026-01-18 |
| v2.0 Robust Multi-Agent CASE | 20-26 | 2026-02-08 |
| v2.1 Working Multi-Agent CASE | 27-33 | 2026-02-09 |
| v3.0 Statistical Detection | 34-40 | 2026-02-16 |
| v4.0 Team-Based CASE | 41-48 | 2026-02-18 |
| v5.0 Fragment Library | 49-54 | 2026-02-21 |
| v6.0 Skill Quality Overhaul | 55-58 | 2026-03-10 |
| v7.0 Statistical 4J Detection | 59-64 | ABANDONED 2026-03-12 |
| v8.0 pyLSD Integration | 65-71 | Superseded by v9.0 (UAT failed as mechanism validation) |

## Performance Metrics

**Velocity:**

- Total plans completed: 118 across 10 milestones (9 shipped + 1 abandoned)
- v7.0: 5 phases executed, 9 plans, all reverted — 0 requirements met
- v8.0: 6 phases executed (65-70), 15 plans complete; Phase 71 UAT superseded
- Cumulative: 64 phases total (58 with code, v7 reverted, v8 phase 71 pending)

## Accumulated Context

### Roadmap Evolution

- Phase 77 added (2026-06-01): fix `lucy lsd run` plumbing bug + resolve D-04 emergent-aromatic + retire deprecated lucy-case-agent.md, then re-UAT CASE1 + CASE9. Created because the Phase 76 v9.0 UAT gate FAILED (CASE1 spirit-fail, CASE9 deferred).
- Phase 80 added (2026-06-09): Long-Range (4J) HMBC connectivity defect (FIX-07). Created because the Phase-79 blind CASE9 UAT proved the peak-picking/symmetry fixes work but exposed a deeper 4J-HMBC blocker. The v9.0 ship-gate moves to Phase 80.
- Phase 81 added (2026-06-10): Peak-Picking Integrity (FIX-08). Created because the Phase-80 blind CASE9 UAT GATE FAILED — but root cause was UPSTREAM of the (correctly-built, unit-green) Phase-80 solver mechanism: default `snr_floor=3.0` floods the picker with ~50 baseline-ripple peaks (incl. 13 impossible >220 ppm), the agent dropped the genuine ester carbonyl (166.08 ppm, SNR 17), DBE was misallocated, and the para-benzoate was excluded before LSD ran. No overcount guard exists (symmetry analysis only models undercount). v9.0 ship-gate moves to Phase 81. See 80-UAT-VERDICT.md.

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- [Phase 79-EXECUTION]: All 4 plans complete; code-review found 2 critical + 4 warnings (CR-01 NaN/empty-clean_data threshold, CR-02 noise_sigma roundtrip loss), ALL fixed + regression-tested. Full suite 1037 passed. FIX-04/05/06 verified.
- [Phase 79-UAT (CASE9 blind, 2026-06-09)]: Fixes ALL engaged in the live run — carbonyl 166.1 picked @ SNR 17 (FIX-04), 3 intensity-symmetry 2C-pairs detected (FIX-05), benzene ring emerged via COSY with no SKEL/ring-BOND, DBE self-check 5/5 + quality reexamination advisory fired (FIX-06). The Phase-78 carbonyl-masking root cause is ELIMINATED.
- [Phase 79-UAT root cause for Phase 80]: CASE9 still unsolved — converged to a wrong benzylic carbonate (meta, MAE 9.09, PLAUSIBLE-but-wrong) instead of the true para-benzoate-with-benzylic-alcohol (`CC(C)OC(=O)c1ccc(C(C)O)cc1`). Cause: false-positive long-range (4J) HMBC (`HMBC 1 8`=166.1↔70.2; set 2 3/2 9/3 8) enforced as 2-3J bonds the carbonyl to the para benzylic C (geometrically impossible), excluding the correct structure. Agent self-diagnosed this (iter 6-7) but couldn't recover within budget. This is the long-standing 4J-HMBC trap (v4.0 ibuprofen; v7.0 abandoned). Forensics: CASE9/analysis/final_results.md + CASE-PROGRESS.md.

- [v7.0 Post-Mortem]: Statistical 4J detection non-viable — 100% FP rate, j5_plus dominates universally
- [v7.0 Post-Mortem]: Next approach is pyLSD integration — solver explores 4J possibilities directly
- [v8.0 Research]: ELIM does NOT extend bond ranges — it drops correlations entirely. Use `HMBC X Y 2 4` for 4J handling.
- [v8.0 Research]: pyLSD should NOT be installed as an external tool — implement PyLSDOrchestrator directly in Python (~230 lines)
- [v8.0 Research]: Phase 65 is a manual validation gate (30 minutes, no code) — hypothesis must be confirmed before coding begins
- [Phase 65-hypothesis-gate]: GO: 4J HMBC removal hypothesis confirmed — ibuprofen (aromatic) found at rank 219/392 after removing 3 W-pathway correlations
- [Phase 65-hypothesis-gate]: LSD runner bug: _run_outlsd missing mode argument; direct outlsd 5 < file.sol is workaround — deferred fix for Phase 66/69
- [Phase 66-lsdinputgenerator-extensions]: OR condition for HMBC extended syntax: emit 'HMBC X Y min max' if min_bonds != 2 OR max_bonds != 3 — catches any single-field deviation from default 2-3 range
- [Phase 66-lsdinputgenerator-extensions]: SHIH placed after SHIX in same Chemical shifts section; generate() unchanged for pylsd_mode=False; validate_pylsd_input checks carbon count only
- [Phase 67-pylsdorchestrator-and-solutionmerger]: K-cap guard (K>3 raises ValueError) placed as FIRST statement in run(), before any I/O
- [Phase 67-pylsdorchestrator-and-solutionmerger]: Suspect correlations identified by (atom1_index, atom2_index, correlation_type) tuple — not id() — because deepcopy invalidates identity
- [Phase 67-pylsdorchestrator-and-solutionmerger]: outlsd invoked directly via subprocess bypassing LSDRunner._run_outlsd (known bug: missing mode argument)
- [Phase 67-02]: Plan 67-01 had already implemented SolutionMerger fully — Plan 67-02 adds only the 2 missing edge-case tests (invalid SMILES skipped, None smiles_file graceful)
- [v8.0-UAT-POSTMORTEM]: pyLSD merge bug confirmed — SolutionMerger collects 0 despite thousands of per-permutation raw solutions. Root cause: outlsd header-only conversion (R1).
- [v8.0-UAT-POSTMORTEM]: Permutation files drop BOND/SYME/DEFF NOT/grouped constraints — perm_00/compound.lsd = 542 B, HMBC-only (R2).
- [v8.0-UAT-POSTMORTEM]: SYME and DEFF NOT are NOT native LSD-3.4.9 commands (errors 102/150) — skills teach them but binary rejects them; lucy-ng translation layer not applied in permutation path (R3).
- [v8.0-UAT-POSTMORTEM]: Phase-65 hypothesis partially contradicted — iteration-2 (4J handled, but SYME/DEFF NOT dropped) produced 0/90 aromatic solutions; ring appeared only when forced via SKEL fragment in iteration-3 (confounded by constraint loss). Re-evaluation required in Phase 72.
- [v8.0-UAT-POSTMORTEM]: Solution found via direct lsd binary (K=0, no permutations) after ~7 manual coordinator interventions — the intended pyLSD mechanism contributed nothing to the result (R4).
- [v9.0-roadmap]: 4 open design questions (Q1-Q4 from postmortem) must be answered in Phase 72 before any fix phase begins. Q1: is pyLSD multi-run the right 4J approach? Q2: single vs dual solver path? Q3: where does constraint translation live? Q4: how is the aromatic ring established?
- [Phase 75-skill-consolidation]: DEFF F-number namespace split — ring exclusion reserves F1/F2 (ring3/ring4 filters); fragment goodlist uses F3+ (`lucy fragment to-lsd --filter-index` default changed 1→3). The two must never collide; the zero-solution fallback removes only the fragment's Fn, never ring-exclusion F1/F2.
- [Phase 75-skill-consolidation]: Native equivalence encoding (replaces non-native SYME): BOND for gem-dimethyl/isopropyl; COSY tagged `; equiv-pair` for aromatic symmetry pairs. DEFF F1/F2/FEXP replaces DEFF NOT for ring exclusion. devils-advocate G5-G8 gates added for the v8.0 failure modes (perm constraint completeness, empty-merge-vs-solncounter, post-validation edit, reversion).
- [Phase 75-skill-consolidation]: lucy-case-agent.md left untouched — DEPRECATED v4.0, not spawned by any active workflow, preserved as historical reference; excluded from native-command sign-off scope.
- [Phase 77-02-FIX-02]: detect_aromatic_cosy_pairs() algorithm: zip(sorted(groupA.atom_ids), reversed(sorted(groupB.atom_ids))) — cross-ring pairing, never within-group, verified against Arm A (COSY 4 7 + COSY 5 6 → 2/2 aromatic solutions)
- [Phase 77-02-FIX-02]: lucy detect aromatic-cosy CLI is now the authoritative source for cross-ring COSY pairs; agent must use this command instead of hand-deriving atom indices
- [Phase 78-GATE]: v9.0 milestone gate FAILED (does not ship). CASE1 UAT-03 = PASS (ibuprofen #2, ring fully emergent, clean). CASE9 UAT-04 = FAIL (correct structure 4-(1-hydroxyethyl)benzoic acid isopropyl ester never reached; ring forced via 6 ring-BONDs; governance-deadlock intervention). See 78-UAT-VERDICT.md.
- [Phase 78-FORENSICS]: CASE9 root cause is UPSTREAM of the Phase-77 LSD fix, proven from raw 13C (…/CASE9/12): (1) ester carbonyl at 166.08 ppm SNR≈17 dropped by `lucy pick 1d` because the CDCl₃ triplet (4.6e7 @ 77 ppm) dominates the max-relative threshold → DBE computed without carbonyl → forced extra ring; (2) 13C intensity doubling (129.94/125.31/22.10 = 2C signals) not used as a symmetry indicator → ring read monosubstituted → `lucy detect aromatic-cosy` gets no equivalence pairs → emergent ring disabled. The emergent-COSY mechanism is NOT refuted — it never got correct input. CASE1 lacks a weak quaternary carbonyl in the CDCl₃ shadow, so it was unaffected.

### Pending Todos

- **Phase 79 (next): fix CASE9 defect at TWO layers** (seed: `.planning/phases/79-peak-picking-symmetry-fix/79-SCOPE-SEED.md`). **Layer 1 — tooling:** (a) peak-picker SNR-based / CDCl₃-solvent-aware threshold so weak quaternary carbonyls (166.08 ppm, SNR≈17) aren't masked; (b) 13C intensity as 2C-equivalence indicator → feeds `lucy detect aromatic-cosy`. **Layer 2 — skill feedback loop** (the skill audit found peak-picking is fire-and-forget with NO sensor for clean-but-wrong convergence; the 4 loop-patterns key on solution_count not quality, so CASE9's clean 211→4→18→12 fired nothing): (c) DBE-insaturation self-check in nmr-chemist (DBE deficit + empty 160–220 ppm region → targeted re-pick); (d) new quality loop-pattern (best MAE > threshold OR all solutions IMPLAUSIBLE → reactivate nmr-chemist re-pick, bounded budget) wired into case.md/loop-patterns.md/advisory-templates.md; (e) make intensity-symmetry check procedural in nmr-chemist. Then re-run CASE9 blind (fresh instance, per feedback_blind_uat) and re-apply the AND-gate.
- Phase 78 blind UAT DONE: CASE1 UAT-03 PASS, CASE9 UAT-04 FAIL. See 78-UAT-VERDICT.md.

*(Phases 72-78 complete — design re-validated, plumbing fixed, constraints preserved, skills consolidated, Phase-77 fixes verified, re-UAT executed. CASE1 passes clean; CASE9 fails on an upstream peak-picking defect → Phase 79.)*

### Blockers/Concerns

None. Roadmap created. Phase 72 may begin immediately.

Note: Phase 72 is a design/analysis phase — it answers questions, it does not build code. Duration is expected to be short (half-day to 1 day). The postmortem evidence is already on disk; the work is synthesis and decision recording.

### Strategic Reference

See `background/sherlock-analysis.md` for full Sherlock vs lucy-ng comparison. Fragment library built (2.4M SSCs). 4J handling is the remaining major gap — v8.0 approach: pyLSD-style multi-run orchestration (implemented but buggy; v9.0 repairs).

Key v9.0 constraint: SYME and DEFF NOT are lucy-ng abstractions. Native LSD-3.4.9 commands are: MULT, LIST, PROP, BOND, COSY, HMBC, ELIM, DEFF, FEXP, HSQC, ELEM. Any solver path that bypasses lucy-ng's translation layer loses SYME/DEFF NOT silently.

## Session Continuity

Last session: 2026-06-09T09:40:40.755Z
Stopped at: Phase 80 closed at FAILED gate (80-UAT-VERDICT.md written, CASE9 FAIL). Phase 80 mechanism (elim_budget, plausibility filter, skill surgery, SC-3 guard PASS) delivered + unit-green (pytest 1054) but the blind CASE9 UAT failed on an UPSTREAM peak-picking defect. Phase 81 (FIX-08) created with full scope in ROADMAP. v9.0 still does not ship.
Resume with: `/gsd-plan-phase 81` (or `/gsd-discuss-phase 81` first) — 5 fixes: (a) snr_floor default 3→5 in peak_picker.py, (b) expose `--snr-floor` in `lucy pick 1d`, (c) overcount guard + `missing_carbons<0` alarm in analyze.py + symmetry_analysis.py, (d) nmr-chemist SNR≥5/carbonyl rules, (e) CASE9/12 regression test. Then re-run blind UAT CASE9+CASE1 (fresh instances per feedback_blind_uat) and re-apply the AND-gate.

---
*Last updated: 2026-06-09 — Phase 79 complete (4/4 plans, FIX-04/05/06 verified, code-review bugs fixed); CASE9 blind UAT exposed 4J-HMBC trap → Phase 80 (FIX-07) added; v9.0 ship-gate moves to Phase 80*
