# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** AI agent autonomously determines compound structures from NMR, with data-driven statistical constraints replacing guesswork
**Current focus:** v3.0 Statistical Detection — hybridisation, neighbours, HHB, ranking, badlist filters

## Current Position

**Milestone**: v3.0 Statistical Detection
**Phase**: Not started (defining requirements)
**Plan**: —
**Status**: Defining requirements
**Last activity**: 2026-02-10 — Milestone v3.0 started

Progress: [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0%

## Completed Milestones

| Milestone | Phases | Shipped |
|-----------|--------|---------|
| v1.0 Core CASE Pipeline | 1-10 | 2026-01-12 |
| v1.1 Database-Backed Dereplication | 11-15 | 2026-01-15 |
| v1.2 HOSE Database Prediction | 16-19 | 2026-01-18 |
| v2.0 Robust Multi-Agent CASE | 20-26 | 2026-02-08 |
| v2.1 Working Multi-Agent CASE | 27-33 | 2026-02-09 |

## Performance Metrics

**Velocity:**
- Total plans completed: 39 (v1.0-v2.1)
- Average duration: ~3 hours per phase (v1.0-v1.2), < 15 min per phase (v2.0-v2.1 docs/skills), ~4 min per plan (v2.1 implementation)
- Total execution time: ~64.92 hours

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v3.0: Major version bump — statistical detection is a fundamental capability addition, not incremental
- v3.0: Motivated by Sherlock CASE system analysis (Wenk PhD thesis) — identified 5 critical gaps
- v3.0: Gap 1 (statistical detection) selected as first milestone — universal benefit, builds on existing HOSE DB
- v3.0: Gaps 4+5 (ranking + badlist) bundled into v3.0 — too small for standalone milestones
- v3.0: Signal grouping detection included — identifies close shifts but combinatorial exchange deferred to v3.1
- v3.1 planned: Signal grouping + combinatorial atom exchange (full implementation)
- v3.2 planned: Fragment library and search (24.5M SSCs)

### Pending Todos

- Implement statistical detection CLI commands
- Update CASE agent to use new CLI commands for constraint generation
- Validate on ibuprofen (CASE1) — must find correct aromatic structure

### Blockers/Concerns

- HOSE database schema may need extension for hybridisation/neighbourhood statistics
- Need to verify existing HOSE stats table contains sufficient data for detection queries
- Ibuprofen failure root cause: 4-bond HMBC + rigid assignment + no statistical constraints → cyclohexadiene solutions

## Session Continuity

Last session: 2026-02-10
Stopped at: Defining v3.0 requirements
Resume file: None (defining requirements)

---
*Last updated: 2026-02-10 after v3.0 milestone started*
