---
gsd_state_version: 1.0
milestone: v9.0
milestone_name: CASE Reliability & Skill Consolidation
status: ready_to_plan
stopped_at: Phase 77 complete (3/3) — ready to discuss Phase 78
last_updated: 2026-06-01T16:27:37.019Z
last_activity: 2026-06-01
progress:
  total_phases: 7
  completed_phases: 6
  total_plans: 15
  completed_plans: 125
  percent: 86
---

# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-20)

**Core value:** AI agent autonomously determines compound structures from NMR, with a multi-agent team that uses the intended solver pipeline — not a manual bypass
**Current focus:** Phase 78 — blind re uat gate

## Current Position

```
Phase 72: Design Re-Validation       [x] Complete
Phase 73: Solution Plumbing Fix      [x] Complete
Phase 74: Constraint Preservation    [x] Complete
Phase 75: Skill Consolidation        [x] Complete
Phase 76: Milestone UAT Gate         [x] Executed — GATE FAILED (CASE1 spirit-fail, CASE9 deferred)
Phase 77: Fix lucy lsd run + Tooling [ ] Context gathered — ready to plan (fixes only)
Phase 78: Blind Re-UAT (CASE1+CASE9) [ ] Not started (depends on 77)
```

Progress: [██████████] 100%

Phase: 78
Plan: Not started
Status: Ready to plan
Last activity: 2026-06-01

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

- Total plans completed: 114 across 10 milestones (9 shipped + 1 abandoned)
- v7.0: 5 phases executed, 9 plans, all reverted — 0 requirements met
- v8.0: 6 phases executed (65-70), 15 plans complete; Phase 71 UAT superseded
- Cumulative: 64 phases total (58 with code, v7 reverted, v8 phase 71 pending)

## Accumulated Context

### Roadmap Evolution

- Phase 77 added (2026-06-01): fix `lucy lsd run` plumbing bug + resolve D-04 emergent-aromatic + retire deprecated lucy-case-agent.md, then re-UAT CASE1 + CASE9. Created because the Phase 76 v9.0 UAT gate FAILED (CASE1 spirit-fail, CASE9 deferred).

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

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

### Pending Todos

- Phase 76: Blind UAT on CASE1 + CASE9 — MUST be run by a fresh blind Claude instance (no compound-identity context); verify merged.smi top-3 independently via RDKit (aromatic-ring + formula match), not agent self-report. This is the milestone gate proving the consolidated skills make the agent solve via the intended native mechanism.

*(Phases 72-75 complete — design re-validated, plumbing fixed, constraints preserved, skills consolidated to native commands.)*

### Blockers/Concerns

None. Roadmap created. Phase 72 may begin immediately.

Note: Phase 72 is a design/analysis phase — it answers questions, it does not build code. Duration is expected to be short (half-day to 1 day). The postmortem evidence is already on disk; the work is synthesis and decision recording.

### Strategic Reference

See `background/sherlock-analysis.md` for full Sherlock vs lucy-ng comparison. Fragment library built (2.4M SSCs). 4J handling is the remaining major gap — v8.0 approach: pyLSD-style multi-run orchestration (implemented but buggy; v9.0 repairs).

Key v9.0 constraint: SYME and DEFF NOT are lucy-ng abstractions. Native LSD-3.4.9 commands are: MULT, LIST, PROP, BOND, COSY, HMBC, ELIM, DEFF, FEXP, HSQC, ELEM. Any solver path that bypasses lucy-ng's translation layer loses SYME/DEFF NOT silently.

## Session Continuity

Last session: 2026-06-01T16:04:22.227Z
Stopped at: Phase 77 context gathered
Resume with: `/gsd-plan-phase 76` — but note Phase 76 is the blind UAT gate and MUST be run by a fresh blind Claude instance (CASE1 + CASE9), with merged.smi verified independently via RDKit. See feedback_blind_uat memory.

---
*Last updated: 2026-05-24 — Phase 75 complete (5/5 plans, SKILL-01/02/03 verified); Phase 76 UAT next*
