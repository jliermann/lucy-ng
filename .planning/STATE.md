# lucy-ng State

## Current Position

**Milestone**: 1.0 — Core CASE Pipeline
**Phase**: 7 (MCP Server) — COMPLETE
**Status**: Milestone 1.0 Complete - All phases finished

## Roadmap Evolution

- Phase 2.1 inserted after Phase 2: 1D Carbon Dereplication with nmrshiftdb (INSERTED)
  - Rationale: Validate pipeline works with 1D data before adding 2D complexity
- Phase 4.1 inserted after Phase 4: 2D Peak Picking Validation (INSERTED)
  - Rationale: Ensure 2D peak picking produces scientifically reasonable results
- Phase 4.2 inserted after Phase 4.1: DEPT-Guided Adaptive HSQC Peak Picking (INSERTED)
  - Rationale: DEPT provides ground truth for protonated carbons; HSQC must find all of them
- Phase 5.1 added: HMBC-Guided Peak Picking (COMPLETE)
  - Rationale: Filter HMBC noise by requiring correlation to known C and H positions
- Phase 5.2 inserted after Phase 5.1: Symmetry Detection from Spectroscopic Data (INSERTED)
  - Rationale: Molecular symmetry causes fewer NMR signals than atoms; must detect and handle for valid LSD input

## Recent Progress

- **Phase 6 CLI Interface complete**:
  - Click-based CLI with 5 command groups (read, pick, analyze, dereplicate, lsd)
  - All commands support `--format text|json` output
  - Auto-detection of experiment types from Bruker data
  - Full pipeline integration from reading to LSD generation
  - 44 CLI tests (43 passing, 1 skipped)
- **Phase 5.2 Symmetry Detection complete**:
  - New `lucy_ng.analysis` module with AI-oriented convenience tools
  - `HydrogenBudgetAnalyzer`: Compare MF H count with observed carbon-assigned H
  - `IntensityReporter`: Report relative HSQC intensities, flag potential equivalents
  - `SymmetryAnalyzer`: Combined summary for AI-driven symmetry reasoning
  - Tools expose data with suggestions; AI makes final reasoning decisions
- Phase 5 LSD Integration complete and enhanced
- 309 total tests passing (5 skipped)

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
| Spectroscopic constraint inference | 2026-01-10 | Carbonyl C identified from shift; missing H assigned to O; derives BOND constraints automatically |
| Click CLI framework | 2026-01-10 | Simpler than Typer, no extra dependencies, widely used |
| JSON output option | 2026-01-10 | Enables MCP server reuse of CLI functionality |

## Open Questions

- None at this time

## Resolved Questions

- **NMR parsing library**: nmrglue (2026-01-08) — Most mature, BSD licensed, native Bruker support, academic citations
- **Dereplication matching strategy**: Multi-mode with fuzzy tolerances (2026-01-09)
- **LSD vs pyLSD**: LSD first (2026-01-10) — Simpler (no Java), pyLSD builds on it, add ranking later
- **Symmetry detection**: (2026-01-10) — AI-driven approach with convenience tools exposing H budget + intensity data

## Session Continuity

**Last session**: 2026-01-11
**Completed**:
- **Phase 7 MCP Server complete**
- FastMCP-based server with 10 tools:
  - `read_spectrum_1d`, `read_spectrum_2d` - Spectrum reading
  - `pick_peaks_1d`, `pick_hsqc_peaks`, `pick_hmbc_peaks` - Peak picking
  - `analyze_symmetry` - Symmetry detection
  - `dereplicate_c13` - Database matching
  - `check_lsd_availability`, `generate_lsd_input`, `run_lsd` - LSD integration
- Entry point: `lucy-mcp` command
- 18 MCP server tests
- Refactored SimplePeakPicker → AdaptivePeakPicker with static methods
- 325+ total tests passing

**Documentation complete**:
- Comprehensive README.md
- docs/INSTALLATION.md
- docs/USER_GUIDE.md
- docs/ARCHITECTURE.md
- docs/MCP_INTEGRATION.md

**Key technical insights**:
- FastMCP uses `name` and `instructions`, not `version`/`description`
- MCP tools return `{"success": bool, ...}` pattern
- Experiment detection: try 2D first, fall back to 1D
- COCONUT streaming mode handles 4.8GB database efficiently

**Milestone 1.0 Complete** - All 7 phases finished

---
*Last updated: 2026-01-11*
