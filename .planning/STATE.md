# lucy-ng State

## Current Position

**Milestone**: 1.0 — Core CASE Pipeline
**Phase**: 5 (LSD Integration) — Complete, enhanced with guided peak picking
**Status**: Phase 6 ready for planning

## Roadmap Evolution

- Phase 2.1 inserted after Phase 2: 1D Carbon Dereplication with nmrshiftdb (INSERTED)
  - Rationale: Validate pipeline works with 1D data before adding 2D complexity
- Phase 4.1 inserted after Phase 4: 2D Peak Picking Validation (INSERTED)
  - Rationale: Ensure 2D peak picking produces scientifically reasonable results
- Phase 4.2 inserted after Phase 4.1: DEPT-Guided Adaptive HSQC Peak Picking (INSERTED)
  - Rationale: DEPT provides ground truth for protonated carbons; HSQC must find all of them
- Phase 5.1 added: HMBC-Guided Peak Picking (COMPLETE)
  - Rationale: Filter HMBC noise by requiring correlation to known C and H positions

## Recent Progress

- Phase 5 LSD Integration complete and enhanced
- Added HMBCGuidedPicker for validated HMBC peak picking
- Fixed LSD runner (stderr parsing, success detection)
- Simplified HMBC format to 2 params (LSD defaults to 2-3 bonds)
- Added molecular formula parsing and heteroatom handling
- Comprehensive documentation of guided peak picking rationale
- 229 total tests passing (4 skipped when LSD not installed)

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
| inv4* long-range detection | 2026-01-10 | Distinguish HMBC from HSQC in inv4 pulse programs |
| nmrglue connected-region algorithm | 2026-01-10 | For 2D peak picking, handles overlapping peaks |
| Corner-based 2D noise estimation | 2026-01-10 | Corners rarely contain real peaks |
| Tolerance-based peak validation | 2026-01-10 | 0.5-1.0 ppm tolerance for 2D vs 1D matching |
| DEPT-guided adaptive thresholding | 2026-01-10 | Lower HSQC threshold until all DEPT carbons matched |
| Multiplicative threshold reduction | 2026-01-10 | ×0.5 factor gives logarithmic steps |
| HMBC-guided peak picking | 2026-01-10 | Filter HMBC by requiring C match in 13C/DEPT and H match in HSQC |
| LSD 2-param HMBC format | 2026-01-10 | LSD defaults to 2-3 bond distance; simpler than 4-param format |
| Real data over manual correlations | 2026-01-10 | Manual test correlations produced 900+ solutions; real data provides stronger constraints |

## Open Questions

- **Symmetry detection**: How to detect equivalent atoms from signal count vs molecular formula?
  - Affects LSD input (SYME command for equivalent atoms)
  - Quaternary carbons can also be in symmetry tuples, not just DEPT-visible carbons

## Resolved Questions

- **NMR parsing library**: nmrglue (2026-01-08) — Most mature, BSD licensed, native Bruker support, academic citations
- **Dereplication matching strategy**: Multi-mode with fuzzy tolerances (2026-01-09)
- **LSD vs pyLSD**: LSD first (2026-01-10) — Simpler (no Java), pyLSD builds on it, add ranking later

## Session Continuity

**Last session**: 2026-01-10
**Completed**:
- Phase 5 LSD Integration complete and enhanced
- HMBCGuidedPicker for validated HMBC peak picking
- LSD runner fixes (stderr parsing, success detection)
- HMBC format simplified to 2 params
- Molecular formula parsing and heteroatom handling in generator
- Comprehensive documentation in CLAUDE.md
- 229 total tests passing

**Key technical insights documented**:
- Guided peak picking rationale (noise reduction, constraint quality)
- Molecular symmetry effects on signal count
- LSD input quality directly affects solution count
- Real experimental data essential (manual correlations insufficient)

**Next**: Plan and execute Phase 6 (CLI Interface)

---
*Last updated: 2026-01-10*
