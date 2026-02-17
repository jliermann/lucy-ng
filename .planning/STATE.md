# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** AI agent autonomously determines compound structures from NMR, with a collaborative team architecture that self-corrects through peer review
**Current focus:** v4.0 Team-Based CASE — Phase 45 in progress

## Current Position

**Milestone**: v4.0 Team-Based CASE — Phases 41-47
**Phase**: 45 — Team Coordination Protocol (complete)
**Plan**: 45-02 complete (full protocol trace, 6/6 SC verified PASS)
**Status**: Phase 45 complete — both plans done, ready for Phase 46
**Last activity**: 2026-02-17 — 45-02 complete (28-step protocol trace, all 6 success criteria PASS, no dead-end states found)

Progress: [##############░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 4/7 phases

## Completed Milestones

| Milestone | Phases | Shipped |
|-----------|--------|---------|
| v1.0 Core CASE Pipeline | 1-10 | 2026-01-12 |
| v1.1 Database-Backed Dereplication | 11-15 | 2026-01-15 |
| v1.2 HOSE Database Prediction | 16-19 | 2026-01-18 |
| v2.0 Robust Multi-Agent CASE | 20-26 | 2026-02-08 |
| v2.1 Working Multi-Agent CASE | 27-33 | 2026-02-09 |
| v3.0 Statistical Detection | 34-40 | 2026-02-16 |

## Performance Metrics

**Velocity:**
- Total plans completed: 73 across 6 milestones (+ 9 in v4.0)
- v3.0: 7 phases, 21 plans, 51 commits, 2 days
- Total execution time: ~78.2 hours

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

### Pending Todos

- Post-phase UAT with additional compounds (pulegone, etc.)

### Blockers/Concerns

- Agent behavior gaps from v3.0 UAT: DEFF NOT persistence, signal grouping not applied, grouped notation lost (v4.0 target)
- COSY agent usage: deferred beyond v4.0
- Database regeneration: End users with pre-v3.0 databases must regenerate

## Accumulated Decisions (Phase 45)

- **45-01:** Orchestrator (not lsd-engineer) creates all iteration tasks — prevents workflow stopping after iteration 1
- **45-01:** Shift list embedded in ranking task description by orchestrator — solution-analyst no longer depends on nmr-chemist message for shifts
- **45-01:** Parallel hmbc-selection task created alongside lsd-iteration task when solution_count is 10-50 and iterations >= 2
- **45-01:** Elapsed time computed from CASE-PROGRESS.md Started timestamp; v3.0 iteration count (4) used as baseline surrogate (wall-clock not recorded in v3.0)
- **45-01:** lsd-engineer spawn prompt updated to "Claim iteration tasks from TaskList as they become available" (removed task-creation instruction)
- **45-02:** All 6 Phase 45 success criteria PASS against shipped code — coordination protocol is ready for Phase 47 UAT
- **45-02:** No dead-end states in protocol — orchestrator creates all tasks; every agent action triggers next action or termination
- **45-02:** 28-step protocol trace covers spawn → peak-picking → LSD with DA gate → parallel tasks → ranking → present_results → terminate

## Accumulated Decisions (Phase 44)

- **44-01:** Coordinator-as-sole-writer enforced at agent instruction level with explicit negation ("You do NOT write CASE-PROGRESS.md") — not just by omission
- **44-01:** All labeled fields in message templates match orchestrator detect_loops field names (Solution count, sp2 count, H budget, HMBC correlations used) — backward-compatible by design
- **44-01:** Terminal message rule: [ITERATION-COMPLETE], [VALIDATION-PASSED], [VALIDATION-BLOCKED] are terminal — one per agent per iteration; revised messages use "(revised)" suffix
- **44-01:** devils-advocate retains no Write tool (read-only); solution-analyst retains Write for final_results.md (not CASE-PROGRESS.md)
- **44-02:** write_progress is a REFERENCE step (not sequential) — coordinator writes throughout workflow as messages arrive
- **44-02:** 9 writing triggers defined covering all agent message types: file header, [SETUP-COMPLETE], iteration header, [ITERATION-COMPLETE], [VALIDATION-PASSED]/[VALIDATION-BLOCKED], coordinator solution count, [RANKING-COMPLETE], diagnostic intervention, intra-iteration revision
- **44-02:** devils-advocate prompt changed from monitoring CASE-PROGRESS.md to receiving validation requests via SendMessage — aligns with its read-only tool access
- **44-02:** All field names preserved identically to v3.0 (Solution count, Constraints added, sp2 count, H budget, HMBC correlations used) — LLM parsing handles deeper nesting transparently

## Accumulated Decisions (Phase 43)

- **43-01:** JSON format confirmed safe in LSD ; comments (parser smoke test passed); inventory block at TOP of LSD file before MULT definitions
- **43-01:** deff_not_patterns initialized at iteration 1 alongside DEFF NOT commands (atomic write rule prevents desync)
- **43-01:** NEVER rebuild inventory from scratch -- same read-previous-never-reconstruct rule applied to inventory itself
- **43-02:** Three-check inventory reconciliation (accuracy, regression, content) is the primary validation protocol for Devils-Advocate
- **43-02:** Legacy fallback for files without inventory block -- backwards compatible with pre-Phase-43 LSD files
- **43-02:** Detection coverage check at 3+ iterations triggers WARNING for pending_from_detection items

## Session Continuity

Last session: 2026-02-17
Stopped at: 45-02 complete (Phase 45 done — protocol verified, all 6 SC PASS)
Resume file: None

---
*Last updated: 2026-02-17 after 45-02 execution*
