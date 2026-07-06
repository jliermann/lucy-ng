---
gsd_state_version: 1.0
milestone: v9.2
milestone_name: CASE Web-View
status: executing
stopped_at: Completed 91-01 test scaffold
last_updated: "2026-07-06T13:17:54.588Z"
last_activity: 2026-07-06
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 10
  completed_plans: 8
  percent: 67
---

# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-29)

**Core value:** AI agent autonomously determines compound structures from NMR, with a multi-agent team that uses the intended solver pipeline — not a manual bypass
**Current focus:** Phase 92 — Orchestrator Integration

## Current Position

```
[Phase 90] [Phase 91] [Phase 92]
[  TODO  ] [  TODO  ] [  TODO  ]
```

Phase: 92 (Orchestrator Integration) — EXECUTING
Plan: 2 of 3
Status: Ready to execute
Last activity: 2026-07-06

## Milestone v9.2 Phases

| Phase | Goal | Requirements | Depends on |
|-------|------|--------------|------------|
| 90. Server, CLI, and Packaging | `lucy webview` commands + server lifecycle via `.webview.json` + `lucy-ng[webview]` optional extra | WV-01, WV-02, WV-08 | — |
| 91. API Endpoints, Depictions, and Static Frontend | Three JSON endpoints with graceful degradation + RDKit SVG + vanilla-JS dashboard | WV-03, WV-04, WV-05, WV-06 | 90 |
| 92. Orchestrator Integration | `case.md` launches server at run start, reports URL, server outlives team | WV-07 | 91 |

**Sequencing:** 90 (server + CLI) is the foundation — nothing else can be tested without it. 91 (API + frontend) builds on 90 and delivers the complete user-visible dashboard. 92 (orchestrator integration) is a skill-level edit to `case.md` that requires 91 to be working so the URL it reports leads to a real dashboard.

## Deferred Items

Items acknowledged and deferred at **v9.1 milestone close on 2026-06-29**:

| Category | Item | Status | Note |
|----------|------|--------|------|
| todo | 2026-06-25-case4-azulene-regiochemistry-enumeration-gap | deferred | NEW 4th defect class from v9.1 UAT-01; di-methyl-ethyl class now searched, exact chamazulene regiochemistry still unreachable. Carried-seed. |

Items acknowledged and deferred at v9.0 milestone close on 2026-06-17 (resolved in v9.1):

| Category | Item | Status | Note |
|----------|------|--------|------|
| todo | 2026-06-17-lucy-lsd-rank-scoring-defect | RESOLVED in v9.1 (Phase 86) | shipped as RANK |
| uat | 78-UAT-CASE1.md / 78-UAT-CASE9.md / 78-UAT-VERDICT.md | superseded | failed gate later overcome |
| verification | 75-VERIFICATION.md | human_needed | satisfied by v9.0 blind UATs |

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
| v9.0 CASE Reliability & Skill Consolidation | 72-85 | 2026-06-17 |
| v9.1 CASE Final-Answer Correctness & Verification Gates | 86-89 | 2026-06-29 |

## Performance Metrics

**Velocity:**

- Total plans completed: 170 across 11 milestones (10 shipped + 1 abandoned) at v9.1 close
- v9.1: 4 phases (86-89), shipped 2026-06-29; tests: 1131 passing at close
- v9.2: 3 phases planned (90-92); 0 plans complete

## Accumulated Context

### Roadmap Evolution

- v9.2 roadmap created (2026-07-02): phases 90-92. Derived from 8 requirements (WV-01..WV-08) from the approved design spec `docs/superpowers/specs/2026-07-02-case-webview-design.md`. Phase 90 delivers the server infrastructure and CLI lifecycle management; Phase 91 delivers all user-visible dashboard content (API layer + RDKit SVG depictions + static vanilla-JS frontend, including graceful degradation on partial files); Phase 92 wires the orchestrator to auto-start the server.

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

- [v9.2-roadmap]: FastAPI + uvicorn shipped as `lucy-ng[webview]` optional extra; core `lucy` CLI stays dependency-free. The frontend is static HTML + vanilla JS — no build toolchain. Server is "dumb" (reads files only, no agent-team coupling) so the same command serves both live and finished runs.
- [v9.2-roadmap]: Stage-2 items (rendered spectra tabs, data tables, SSE/WebSocket push) are explicitly deferred — not in scope for this milestone.
- [v9.2-roadmap]: Graceful degradation (WV-06) assigned to Phase 91 alongside the API endpoints because it is an API-layer concern: every endpoint must handle missing/partial/malformed source files without raising a 500.
- [v9.2-roadmap]: WV-07 (orchestrator integration) sequenced last because it requires a working dashboard URL (Phase 91) to be meaningful. It is a skill edit to `case.md` — no Python code changes expected.
- [Phase ?]: Raise click.ClickException from exc in _require_webview(): ruff B904 requires exception chaining in except clause
- [Phase 91]: Epoch values in timing.jsonl test fixtures are JSON strings (not ints) matching case.md shell printf %s output
- [Phase 91]: All fastapi/webview imports in test_webview_api.py are inside test function bodies (WV-08 collect-safety)

### Pending Todos

- **[2026-06-25] CASE4 azulene-regiochemistry-enumeration gap** — carried seed; not in v9.2 scope. See `.planning/todos/pending/2026-06-25-case4-azulene-regiochemistry-enumeration-gap.md`.

### Blockers/Concerns

None. Phase 90 may begin immediately (`/gsd-plan-phase 90`).

### Strategic Reference

See `background/sherlock-analysis.md` for full Sherlock vs lucy-ng comparison. v9.0 closed the end-to-end mechanism gap; v9.1 closed the three "clean-but-wrong" defect classes. v9.2 adds observability (dashboard) without touching solver logic.

Key v9.0 constraint (still in force): SYME and DEFF NOT are lucy-ng abstractions. Native LSD-3.4.9 commands are: MULT, LIST, PROP, BOND, COSY, HMBC, ELIM, DEFF, FEXP, HSQC, ELEM.

## Session Continuity

Last session: 2026-07-06T13:17:54.583Z
Stopped at: Completed 91-01 test scaffold
Resume with: `/gsd-plan-phase 90` (Server, CLI, and Packaging)

---
*Last updated: 2026-07-02 — v9.2 roadmap created (3 phases, 8 requirements mapped)*
