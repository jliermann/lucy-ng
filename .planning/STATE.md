# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-19)

**Core value:** AI agent autonomously determines compound structures from NMR, with a collaborative team architecture that self-corrects through peer review
**Current focus:** v5.0 Fragment Library — COMPLETE (all 6 phases done, 12 plans executed)

## Current Position

**Milestone**: v5.0 Fragment Library
**Phase**: 54 of 54 (Multi-Compound UAT)
**Status**: Complete (all plans executed)
**Last activity**: 2026-02-21 — Phase 54 Plan 02 complete (UAT: self-search PASSED, CASE comparison DEFERRED)

Progress: [██████████] 100% (12 plans complete)

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

## Performance Metrics

**Velocity:**
- Total plans completed: 88 across 7 milestones (+ 12 in v5.0)
- v4.0: 9 phases, 21 plans, 48 commits, 2 days
- v5.0: 6 phases, 12 plans, 16 commits, 3 days
- Total execution time: ~78.2 hours + ~2 hours (v5.0)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.

Recent decisions affecting v5.0 (latest first):
- Phase 54 Plan 02: Multi-compound CASE comparison (VALD-01) deferred — all 6 compounds have 4J HMBC risk
- Phase 54 Plan 02: Fragment library accepted as infrastructure-complete based on self-search + integration tests
- Phase 54 Plan 01: Self-search recall 100% validates 2 ppm bin size and BFS extraction pipeline end-to-end
- Phase 54 Plan 01: Full extraction completed: 2,385,146 SSCs from 928K compounds (605 MB)
- Phase 53 Plan 01: Agent files outside lucy-ng git repo (~/.claude/) -- changes tracked in summary, no per-task commits
- Phase 53 Plan 01: DEFF F1/FEXP ordering: after inventory comment block, before first MULT (different from DEFF NOT after correlations)
- Phase 53 Plan 01: Fragment persistence follows same rule as DEFF NOT: copy from previous LSD file, never reconstruct
- Phase 52 Plan 02: Generic benzene fragment with (0 1) H counts for smoke test -- exact H counts too restrictive for substituted ring matching
- Phase 52 Plan 02: Fragment file written to CWD by default with bare filename in DEFF command (LSD resolves relative to working directory)
- Phase 52 Plan 01: HybridizationType from rdkit.Chem.rdchem (not rdkit.Chem.Hybridization which does not exist)
- Phase 52 Plan 01: type: ignore[no-untyped-call] for RDKit GetAtoms/GetBonds (untyped C++ stubs in strict mypy)
- Phase 51 Plan 02: DEFF/FEXP are path templates -- actual .lsd files written by Phase 52
- Phase 51 Plan 02: prescreening_count/fine_match_count as public attributes on FragmentSearcher (not changing return type)
- Phase 51 Plan 01: LSB-first bitorder='little' in unpackbits/packbits to match shifts_to_fingerprint encoding
Previous decisions:
- Separate `lucy-ng-fragments.db` file (not merged into 2.8 GB main DB) — Dropbox sync and index contention
- Validate 2 ppm bin size on 1K sample BEFORE full 24M extraction — bin size is unrecoverable once baked in
- DEFF goodlist LSD syntax requires LSD smoke test validation BEFORE agent integration — goodlist vs DEFF NOT semantic confusion is silent failure

### Pending Todos

- Statistical 4J HMBC coupling detection (deferred to v5.1)
- Multi-compound UAT with non-aromatic compounds (deferred — need compounds without 4J risk)
- COSY correlation integration (deferred to v5.2)
- NP-likeness scoring (deferred to v5.2)

### Blockers/Concerns

- 4J HMBC couplings silently exclude correct structures — highest priority for next milestone
- All 6 local test compounds are aromatic with 4J risk — need non-aromatic compounds for clean fragment UAT

### Strategic Reference

See `background/sherlock-analysis.md` for full Sherlock vs lucy-ng comparison. Fragment library is now built (2.4M SSCs). Remaining gap: statistical 4J coupling detection.

## Session Continuity

Last session: 2026-02-21
Stopped at: v5.0 milestone complete — ready for `/gsd:complete-milestone v5.0`
Resume with: `/gsd:complete-milestone v5.0`

---
*Last updated: 2026-02-21 — v5.0 Fragment Library all phases complete*
