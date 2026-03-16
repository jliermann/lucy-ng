---
gsd_state_version: 1.0
milestone: v8.0
milestone_name: pyLSD Integration
status: planning
stopped_at: Completed 65-01-PLAN.md — GO decision for v8.0
last_updated: "2026-03-16T10:37:49.496Z"
last_activity: 2026-03-13 — v8.0 roadmap created
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 1
  completed_plans: 1
---

# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-13)

**Core value:** AI agent autonomously determines compound structures from NMR, with a collaborative team architecture that self-corrects through peer review
**Current focus:** v8.0 pyLSD Integration — Phase 65 COMPLETE (GO), Phases 66/68 ready to start in parallel

## Current Position

Phase: 66/68 — LSDInputGenerator Extensions / Constraint Inventory v2 (Wave 1, parallel)
Plan: — (not yet planned)
Status: Phase 65 complete — GO decision issued. Wave 1 unblocked.
Last activity: 2026-03-16 — Phase 65 hypothesis gate CONFIRMED, GO decision

## Phase Map (v8.0)

```
Phase 65: Hypothesis Validation Gate    [x] COMPLETE — GO decision 2026-03-16
Phase 66: LSDInputGenerator Extensions  [ ] Not started  (depends on 65 — UNBLOCKED)
Phase 67: PyLSDOrchestrator/Merger      [ ] Not started  (depends on 66)
Phase 68: Constraint Inventory v2       [ ] Not started  (depends on 65 — UNBLOCKED)
Phase 69: CLI and Regression Suite      [ ] Not started  (depends on 66, 67)
Phase 70: Agent Skill Updates           [ ] Not started  (depends on 68, 69)
Phase 71: Ibuprofen CASE UAT            [ ] Not started  (depends on 70)
```

Wave structure:
- Wave 0: Phase 65 (gate — must complete before all others)
- Wave 1: Phases 66, 68 (parallel — generator extensions and schema, both depend only on 65)
- Wave 2: Phase 67 (depends on 66), Phase 69 (depends on 66 + 67)
- Wave 3: Phase 70 (depends on 68 + 69)
- Wave 4: Phase 71 (depends on 70)

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

## Performance Metrics

**Velocity:**
- Total plans completed: 111 across 10 milestones (9 shipped + 1 abandoned)
- v7.0: 5 phases executed, 9 plans, all reverted — 0 requirements met
- Cumulative: 58 phases with code, 111 plans

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
- [v7.0 Post-Mortem]: Statistical 4J detection non-viable — 100% FP rate, j5_plus dominates universally
- [v7.0 Post-Mortem]: Next approach is pyLSD integration — solver explores 4J possibilities directly
- [v8.0 Research]: ELIM does NOT extend bond ranges — it drops correlations entirely. Use `HMBC X Y 2 4` for 4J handling.
- [v8.0 Research]: pyLSD should NOT be installed as an external tool — implement PyLSDOrchestrator directly in Python (~230 lines)
- [v8.0 Research]: Phase 65 is a manual validation gate (30 minutes, no code) — hypothesis must be confirmed before coding begins
- [Phase 65-hypothesis-gate]: GO: 4J HMBC removal hypothesis confirmed — ibuprofen (aromatic) found at rank 219/392 after removing 3 W-pathway correlations
- [Phase 65-hypothesis-gate]: LSD runner bug: _run_outlsd missing mode argument; direct outlsd 5 < file.sol is workaround — deferred fix for Phase 66/69

### Pending Todos

- Multi-compound UAT with non-aromatic compounds (v9.0)
- COSY correlation integration (deferred)
- NP-likeness scoring (deferred)

### Blockers/Concerns

None. Phase 65 hypothesis gate PASSED — GO decision issued. Wave 1 (Phases 66, 68) may proceed in parallel.

### Strategic Reference

See `background/sherlock-analysis.md` for full Sherlock vs lucy-ng comparison. Fragment library built (2.4M SSCs). 4J handling is the remaining major gap — v8.0 approach: pyLSD-style multi-run orchestration.

## Session Continuity

Last session: 2026-03-16T10:37:49.494Z
Stopped at: Completed 65-01-PLAN.md — GO decision for v8.0
Resume with: `/gsd:plan-phase 66` and `/gsd:plan-phase 68` (Wave 1 — parallel)

---
*Last updated: 2026-03-16 — Phase 65 complete, GO decision, Wave 1 unblocked*
