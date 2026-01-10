# lucy-ng State

## Current Position

**Milestone**: 1.0 — Core CASE Pipeline
**Phase**: 3 (2D NMR Reading) — Complete
**Status**: Ready for Phase 4 (Peak Picking)

## Roadmap Evolution

- Phase 2.1 inserted after Phase 2: 1D Carbon Dereplication with nmrshiftdb (INSERTED)
  - Rationale: Validate pipeline works with 1D data before adding 2D complexity

## Recent Progress

- Phase 3 2D NMR Reading complete (2 commits)
- BrukerReader.read_2d() for HSQC, HMBC, COSY, TOCSY, NOESY, ROESY
- Experiment type detection from pulse program patterns
- 12 new tests, all 69 tests passing

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
| Multi-mode dereplication matching | 2026-01-09 | shifts_only, dept_enhanced modes for different data quality |
| Overlap-adjusted scoring | 2026-01-09 | Account for fewer peaks than expected carbons |
| Variable tolerance by region | 2026-01-09 | Tighter for aliphatic (0.8), looser for carbonyl (1.5) |
| RDKit for SD parsing | 2026-01-09 | Industry standard, handles MOL blocks and properties |
| inv4* long-range detection | 2026-01-10 | Distinguish HMBC from HSQC in inv4 pulse programs via lr/lplr/lrnd patterns |

## Open Questions

- LSD vs pyLSD - which to target first?

## Resolved Questions

- **NMR parsing library**: nmrglue (2026-01-08) — Most mature, BSD licensed, native Bruker support, academic citations
- **Dereplication matching strategy**: Multi-mode with fuzzy tolerances (2026-01-09)

## Session Continuity

**Last session**: 2026-01-10
**Completed**:
- Phase 3 2D NMR Reading (01-03-PLAN.md executed)
- BrukerReader.read_2d() with experiment type detection
- 12 comprehensive 2D tests
**Next**: Plan and execute Phase 4 (Peak Picking)

---
*Last updated: 2026-01-10*
