# lucy-ng State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** AI agent autonomously determines compound structures from NMR, with data-driven statistical constraints replacing guesswork
**Current focus:** v3.0 Statistical Detection — Phase 40 (Validation)

## Current Position

**Milestone**: v3.0 Statistical Detection
**Phase**: 40 of 40 (Validation) — COMPLETE
**Plan**: 03 of 03 complete (Tier 2 database validation + validation report)
**Status**: v3.0 validation complete, ship recommendation: YES with 3 documented gaps
**Last activity**: 2026-02-12 — Completed Phase 40 (Validation)

Progress: [█████████████████████████████████████████] 100% (40/40 phases complete)

## Completed Milestones

| Milestone | Phases | Shipped |
|-----------|--------|---------|
| v1.0 Core CASE Pipeline | 1-10 | 2026-01-12 |
| v1.1 Database-Backed Dereplication | 11-15 | 2026-01-15 |
| v1.2 HOSE Database Prediction | 16-19 | 2026-01-18 |
| v2.0 Robust Multi-Agent CASE | 20-26 | 2026-02-08 |
| v2.1 Working Multi-Agent CASE | 27-33 | 2026-02-09 |
| v3.0 Statistical Detection | 34-40 | 2026-02-12 |

## Performance Metrics

**Velocity:**
- Total plans completed: 70 (v1.0-v2.1: 39, v3.0: 31)
- Average duration: ~3 hours per phase (v1.0-v1.2), < 15 min per phase (v2.0-v2.1 docs/skills), ~6 min per plan (v3.0 implementation)
- Total execution time: ~78.2 hours (69.5h + 8.7h Phase 40 database regen + validation)

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- v3.0: Major version bump — statistical detection is fundamental capability addition, not incremental
- v3.0: Motivated by Sherlock CASE system analysis (Wenk PhD thesis) — identified 5 critical gaps
- v3.0: Gap 1 (statistical detection) selected as first milestone — universal benefit, builds on existing HOSE DB
- v3.0: Gaps 4+5 (ranking + badlist) bundled into v3.0 — too small for standalone milestones
- v3.0: Signal grouping detection included — identifies close shifts but combinatorial exchange deferred to v3.1
- Phase 34-01: Use ALTER TABLE ADD COLUMN for v3→v4 migration (safe, fast, in-place)
- Phase 34-01: Composite index (radius, mean) for O(log N) BETWEEN queries in detection
- Phase 34-01: All query methods backward compatible with v3 databases (try/except fallback)
- Phase 34-02: extract_hybridisation() at module level for reusability across generator classes
- Phase 34-02: update_with_hybridisation() instead of modifying update() for backward compatibility
- Phase 34-02: generate_all() returns tuple (aggregates, hybridisations) - minimal breaking change
- Phase 34-02: Treat S and UNSPECIFIED hybridisations as sp3 (conservative default)
- Phase 34-03: StatisticalDetector is pure query+frequency layer (no HOSE/RDKit logic)
- Phase 35-01: Neighbour count columns store presence frequency (count of observations with ≥1 element)
- Phase 35-01: Halogen aggregation in single has_halogen_neighbor column (F/Cl/Br/I combined)
- Phase 35-01: parse_sphere_1() uses regex [A-Z][a-z]? to extract elements, ignoring bond prefixes
- Phase 35-01: Upsert accepts 5, 8, or 13-element tuples for v3/v4/v5 backward compatibility
- Phase 35-02: update_with_neighbors() calls update_with_hybridisation() internally for composition
- Phase 35-02: WelfordAccumulator.to_tuple() extended from 6 to 11 elements for v5 schema
- Phase 35-02: HOSEStatsGenerator.generate_all() returns 3-tuple (aggregates, hybridisations, neighbour_counts)
- Phase 35-03: mandatory_elements/forbidden_elements properties use hardcoded 0.95/0.01 thresholds for convenience
- Phase 35-03: Constraints use custom thresholds passed to detect_neighbours() for flexibility
- Phase 35-03: Warn on unpopulated neighbour columns (v4 databases) rather than fail
- Phase 35-04: --mode flag overrides --min-frequency/--max-frequency when both provided
- Phase 35-04: No multiplicity argument for neighbours detection (research recommends ignoring it)
- Phase 36-01: Bond pair statistics at formula level (not HOSE level) - correct granularity for HHB queries
- Phase 36-01: Ring columns store counts (not booleans) for frequency distributions
- Phase 36-01: Composite PRIMARY KEY (formula_normalized, element1, element2) for bond_pair_stats
- Phase 36-01: Backward compatibility - get_bond_pair_stats_by_formula returns [] for v5 databases
- Phase 36-02: update_with_rings() calls update_with_neighbors() internally for composition pattern
- Phase 36-02: WelfordAccumulator.to_tuple() extended from 11 to 14 elements for v6 schema
- Phase 36-02: extract_hetero_hetero_bonds() returns canonicalized pairs (alphabetically sorted)
- Phase 36-02: HOSEStatsGenerator.generate_all() returns 4-tuple adding ring_counts dict
- Phase 36-03: Heteroatom detection via simple regex pattern (no RDKit needed for formula parsing)
- Phase 36-03: Pure hydrocarbons get has_heteroatoms=False with clear user message
- Phase 36-03: CLI takes FORMULA argument (not shift_ppm) to distinguish from other detect subcommands
- Phase 36-03: Formula not in database returns has_data=False with warning (vs formula exists but no HHB)
- Phase 37-01: Complete linkage prevents chaining (all pairwise distances must be <= tolerance)
- Phase 37-01: Multiplicity incompatible pairs cause entire group to split into singletons
- Phase 37-01: Ambiguous multiplicities (CH/CH3) do NOT bridge incompatible pairs (CH vs CH3)
- Phase 37-01: Use statistics.mean() instead of numpy to avoid adding dependency for trivial math
- Phase 37-01: 1-based LSD atom IDs with parenthesized format for multi-atom groups
- Phase 37-02: Use actual LSD runs instead of syntax mocking for validation (stronger validation)
- Phase 37-02: Count solutions via .sol file detection (more reliable than stderr parsing)
- Phase 37-02: Document false positive risk and tolerance rationale as test docstrings
- Phase 37-03: Custom text formatting instead of GroupingResult.summary() for LSD atom list display
- Phase 37-03: Lazy import of group_signals() following detect.py pattern
- Phase 37-03: False positive warning mandatory in text output
- Phase 38-01: Sort key (-matched_count, mae) makes signal coverage primary ranking criterion
- Phase 38-01: ShiftAssignment carries radius_used/confidence from PredictedShift for transparency
- Phase 38-01: Hallucination test uses ghost carbons (predictions in gaps) for realistic scenario
- Phase 38-01: CLI text output shows Matched=N/M alongside MAE for user visibility
- Phase 38-02: 8 DEFF NOT patterns exclude all common strained ring motifs (3- and 4-membered)
- Phase 38-02: Epoxide exception documented with specific shift range (45-55 ppm) and formula requirements
- Phase 38-02: Two-tier ranking prioritizes signal match count over MAE to prevent wrong structures with coincidentally low errors
- Phase 39-01: Inline detection knowledge in agent file (240 lines) for immediate access during CASE workflow
- Phase 39-01: Selective detection by shift range (120-160, 160-220, 50-90 ppm) instead of querying every shift
- Phase 39-01: Detection runs once per compound (before first LSD) - results constant across iterations
- Phase 39-02: Chemistry-First Hierarchy with 5 explicit priority levels (DEPT 100% > HSQC 95% > HMBC 80% > shifts 70% > detection 60%)
- Phase 39-02: Conflict resolution decision tree for 5 patterns (DEPT, formula, HSQC, no data, ambiguous)
- Phase 39-02: 3 worked conflict examples (allylic CH2, formula mismatch, peroxide override)
- Phase 39-02: Threshold override guidelines with mandatory documentation for every override
- Phase 39-02: Detection failure handling with shift-based fallback heuristics when database has no entries
- Phase 39-02: Principle: statistics augment NMR evidence, never override
- Phase 40-02: Validation tests use synthetic data (no database regeneration required)
- Phase 40-02: Chemistry principles documented in test docstrings for clarity
- Phase 40-02: Badlist pattern existence validated via agent file inspection
- Phase 40-02: Agent USAGE of badlist deferred to Plan 40-03 UAT report
- Phase 40-03: Two-tier validation pattern (Tier 1 synthetic + Tier 2 real database)
- Phase 40-03: Ship with documented gaps (3 known limitations don't block release)
- Phase 40-03: Full CASE agent testing deferred to post-phase UAT (stochastic, non-deterministic)

### Pending Todos

- ~~Implement neighbourhood detection CLI commands (Phase 35)~~ → COMPLETE
- ~~Implement HHB and ring detection (Phase 36)~~ → COMPLETE
- ~~Signal grouping detection (Phase 37)~~ → COMPLETE
- ~~Implement two-tier ranking and badlist (Phase 38)~~ → COMPLETE
- ~~Add detection protocol and chemistry-first hierarchy to CASE agent (Phase 39)~~ → COMPLETE (30/30 must-haves verified)
- ~~Database regeneration with v6 schema (Phase 40-01)~~ → COMPLETE (7.89M HOSE stats, 8h 39m)
- ~~Tier 1 validation tests (Phase 40-02)~~ → COMPLETE (762 tests pass: 730 existing + 32 new)
- ~~Validation report and ship decision (Phase 40-03)~~ → COMPLETE (Ship: YES with 3 documented gaps)
- Post-phase UAT with ibuprofen/pulegone — validate agent CASE workflow with statistical detection
- v3.1 planning: COSY integration, fragment library, combinatorial exchange

### Blockers/Concerns

- ~~HOSE database schema extension requires migration or fresh generation~~ → RESOLVED: ALTER TABLE migration is instant
- ~~HOSE database hybridisation columns exist but are unpopulated (all 0) until database regeneration~~ → RESOLVED: Phase 40-01 regenerated database with v6 schema fully populated
- ~~Ibuprofen failure root cause (v2.1): 4-bond HMBC + rigid assignment + no statistical constraints → cyclohexadiene solutions~~ → ADDRESSED: v3.0 statistical detection constrains aromatic rings
- ~~Research flags threshold sensitivity~~ → RESOLVED: --mode relaxed and --min/max-frequency override flags implemented in Phase 35-04
- Known Gap 1 (COSY agent usage): Agent identifies COSY but doesn't use it for H-H connectivity — deferred to v3.1
- Known Gap 2 (database regeneration requirement): End users with v1.x-v2.x databases must regenerate (2-3h one-time cost)
- Known Gap 3 (full CASE testing): Agent USAGE of detection validated through unit tests, full CASE workflow deferred to post-phase UAT

## Session Continuity

Last session: 2026-02-12
Stopped at: Phase 40 (Validation) complete — v3.0 Statistical Detection validated and ready to ship
Resume file: None — Phase 40 complete, ready for post-phase UAT

---
*Last updated: 2026-02-12 after Phase 40 Plan 03 complete (Tier 2 Database Validation + v3.0 Ship Report — 3 tasks, ship recommendation: YES with 3 documented gaps)*
