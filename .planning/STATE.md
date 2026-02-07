# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-06)

**Core value:** AI agent autonomously determines compound structures from NMR, with multi-agent architecture preventing loops
**Current focus:** Phase 23 Plan 01 complete; error tolerance and ambiguity detection documented in SKILL.md

## Current Position

**Milestone**: v2.0 Robust Multi-Agent CASE
**Phase**: 23 of 26 (Error Tolerance and Confidence) -- IN PROGRESS
**Plan**: 1 of 2 complete
**Status**: Phase 23 Plan 01 complete (error tolerance and ambiguity detection in SKILL.md)
**Last activity**: 2026-02-07 -- Completed 23-01-PLAN.md (resolution-based ambiguity detection)

Progress: [========================|.....] 84% (23 plans complete, 4 remaining)

## Completed Milestones

| Milestone | Phases | Shipped |
|-----------|--------|---------|
| v1.0 Core CASE Pipeline | 1-10 | 2026-01-12 |
| v1.1 Database-Backed Dereplication | 11-15 | 2026-01-15 |
| v1.2 HOSE Database Prediction | 16-19 | 2026-01-18 |

## Performance Metrics

**Velocity:**
- Total plans completed: 27 (v1.0-v1.2 + Phase 20 + Phase 21 + Phase 22 Plan 01 + Phase 23 Plan 01)
- Average duration: ~3 hours per phase
- Total execution time: ~63 hours

**Recent Trend:**
- Phase 20 completed in 3 plans (~15 min total execution)
- Phase 21 completed in 3 plans (~11 min total: 3 min + 5 min + 3 min)
- Phase 22 Plan 01 completed in ~3 min
- Phase 23 Plan 01 completed in ~3 min
- Trend: Accelerating on documentation tasks (< 5 min per plan)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v2.0: AI as intelligence layer -- domain knowledge in skill, not Python code
- v2.0: Multi-agent CASE -- supervisor prevents loops, specialists handle subtasks
- v2.0: Error tolerance as skill knowledge -- teach AI to detect issues, not build Python machinery
- v2.0: Skip COSY -- notoriously difficult to analyze, defer
- 20-01: MCP tools: 7 Tier 1, 4 Tier 2, 4 Tier 3 (of 15 total)
- 20-01: CLI groups: 4 Tier 1, 3 Tier 2, 2 Tier 3 (of 9 groups, 22 commands)
- 20-01: generate_correlation_diagram = Tier 1 despite 1151 lines (pure visualization, no NMR inference)
- 20-03: SKILL.md proposed at ~500 lines with 9 sections (NMR background through quick reference)
- 20-03: SUPERVISOR.md proposed at ~40 lines for workflow selection and escalation
- 20-03: Phase 26 dual-mode architecture: MCP thin wrappers + CLI retains smart behavior
- 21-01: SKILL.md actual: 418 lines, 8 sections (NMR background through quick reference)
- 21-01: Deduplication achieved: sp2 even count (1x), ELIM usage (1x), correlation order (1x), score thresholds (1x), MAE thresholds (1x)
- 21-01: SKILL.md excludes project-level content (setup, dev reference, database stats stay in CLAUDE.md)
- 21-02: CLAUDE.md reduced from 1,080 to 305 lines (72% reduction), keeping only project-level content
- 21-02: skill/supervisor/SKILL.md created (78 lines) with workflow selection, loop detection, escalation criteria
- 21-02: Zero domain knowledge remains in CLAUDE.md -- all workflow/reasoning now in skill/SKILL.md
- 21-03: All subskills deduplicated with cross-references to skill/SKILL.md
- 21-03: Blind CASE Protocol properly homed in skill/sanitize/SKILL.md
- 21-03: SKIL-03 (zero cross-document duplication) verified across all 5 audit clusters
- 21-03: Final line counts: CLAUDE.md (305), SKILL.md (418), CASE (666), sanitize (407), dereplicate (182), supervisor (78)
- 22-01: HMBC strategy documented: adaptive iteration (3-5 batch), NOT fixed 3-phase recipe
- 22-01: Quality assessment documented: S/N evaluation, digital resolution, artifact recognition
- 22-01: SKILL.md grown to 610 lines, 10 sections (added quality + HMBC strategy)
- 22-01: Iteration cap ~10 for safety (prevents loops before Phase 24 supervisor)
- 23-01: Error tolerance documented: resolution-based close carbon detection (pts/ppm), context-dependent DEPT/HSQC conflict resolution
- 23-01: Ambiguity handling: LSD LIST/PROP in single file (NOT separate variants), standardized Ambiguities Detected table format
- 23-01: Quaternary carbon sparsity: shift-based constraints (modular for future atom environment database), 20% incremental threshold reduction
- 23-01: SKILL.md grown to 864 lines, 11 sections (added error tolerance + ambiguity detection, renumbered Quick Reference)

### Pending Todos

- Phase 23 Plan 01 complete: SKILL.md now 864 lines with 11 sections (error tolerance + ambiguity detection added)
- Phase 23 Plan 02 ready: Confidence scoring (CONF-01 through CONF-03) - per-atom and per-structure confidence annotation
- Phase 24 foundation ready: skill/supervisor/SKILL.md + convergence detection from 22-01 + ambiguity escalation from 23-01
- 8 intelligence hotspot modules (~2,139 lines) identified for progressive migration through Phases 23-26
- 3 code consolidation targets (experiment auto-discovery, database finder, LSD parser) queued for Phase 26

### Blockers/Concerns

- Virgiline (CASE7) failure is the motivating case for v2.0 -- supervisor and incremental HMBC should address root causes

## Session Continuity

Last session: 2026-02-07
Stopped at: Completed Phase 23 Plan 01 (error tolerance and ambiguity detection)
Resume file: None

---
*Last updated: 2026-02-07 after Phase 23 Plan 01 completion*
