# lucy-ng State

## Current Position

**Milestone**: 1.0 — Core CASE Pipeline
**Phase**: 2 (1D NMR Reading) — Complete
**Status**: Ready for Phase 3

## Recent Progress

- Phase 2 1D NMR Reading complete (3 commits)
- BrukerReader class implemented with read_1d() method
- Parameter extraction with edge case handling
- 14 tests written using real Ibuprofen data
- Module exports configured

## Key Decisions

| Decision | Date | Context |
|----------|------|---------|
| Hybrid CLI + MCP interface | 2026-01-08 | MCP for agent iteration, CLI for testing |
| Bruker-only for v1 | 2026-01-08 | Focus on most common format |
| LSD/pyLSD as primary solvers | 2026-01-08 | Established CASE tools with CLI |
| nmrglue for NMR parsing | 2026-01-08 | Most mature, BSD licensed, native Bruker support |
| Pydantic v2 for models | 2026-01-08 | Type safety, validation, JSON serialization |
| hatch build system | 2026-01-08 | Modern Python packaging |
| Use processed data | 2026-01-08 | Read from pdata/1/ not raw FID |

## Open Questions

- LSD vs pyLSD - which to target first?

## Resolved Questions

- **NMR parsing library**: nmrglue (2026-01-08) — Most mature, BSD licensed, native Bruker support, academic citations

## Session Continuity

**Last session**: 2026-01-08
**Completed**: Phase 2 1D NMR Reading (01-02-PLAN.md executed)
**Next**: Phase 3 2D NMR Reading

---
*Last updated: 2026-01-08*
