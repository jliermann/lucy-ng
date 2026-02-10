# Project Milestones: lucy-ng

## v2.1 Working Multi-Agent CASE (Shipped: 2026-02-09)

**Delivered:** Working multi-agent orchestration replacing v2.0's paper-only architecture — sub-command skills, real agent spawning, progress monitoring, loop detection, advisory intervention, diagnostic specialist delegation, AI-driven sanitisation.

**Phases completed:** 27-33 (9 plans total)

**Key accomplishments:**
- Sub-command skills: /lucy-ng:case, /lucy-ng:sanitise, /lucy-ng:dereplicate, /lucy-ng:predict, /lucy-ng:status
- CASE orchestrator that spawns autonomous CASE agent via Task(), monitors CASE-PROGRESS.md, detects 4 loop patterns
- Autonomous CASE agent with 613 lines of inlined NMR/LSD knowledge
- Diagnostic specialist delegation after 2 failed basic interventions
- AI-driven dataset sanitisation (no CLI — requires AI semantic reasoning)
- First live CASE test: Ibuprofen identified (rank #1) but with wrong topology (cyclohexadiene, not aromatic)

**Stats:**
- 7 phases, 9 plans
- 1 day from start to shipped (2026-02-08 → 2026-02-09)

**What's next:** v3.0 Statistical Detection — data-driven constraints to replace agent guesswork

---

## v2.0 Robust Multi-Agent CASE (Shipped: 2026-02-08)

**Delivered:** AI-first skill architecture with thin tool wrappers, supervisor/diagnostic specialist agents (paper definitions), comprehensive CASE workflow knowledge (3,780 lines)

**Phases completed:** 20-26 (16 plans total)

**Key accomplishments:**
- System audit: all 16 MCP tools + 7 CLI groups classified
- CLAUDE.md split into project-level + SKILL.md (1,079 lines) + supervisor SKILL.md + diagnostic SKILL.md (1,874 lines)
- MCP server removed entirely — CLI-only architecture
- Incremental HMBC strategy, error tolerance, confidence scoring encoded in skills
- Supervisor and diagnostic specialist agent definitions (paper architecture)
- Thin CLI tools validated with Ibuprofen de novo CASE

**Stats:**
- 7 phases, 16 plans
- 3 weeks (2026-01-18 → 2026-02-08)

---

## v1.2 HOSE Database Prediction (Shipped: 2026-01-18)

**Delivered:** Database-backed 13C shift prediction using 7.9M HOSE statistics from 895K compounds, enabling accurate solution ranking with O(1) lookups

**Phases completed:** 16-19 (4 plans total)

**Key accomplishments:**
- hose_stats table with 7.9M pre-computed statistics (mean, std, count) per HOSE code at radii 1-6
- HOSELookupProtocol for interchangeable prediction backends
- DatabaseHOSELookup adapter for O(1) database queries
- C13Predictor with dual-backend support (database preferred, JSON table fallback)
- ResumableHOSEStatsGenerator with checkpoint/resume for large dataset processing
- CLI `--db` option with intelligent auto-detection
- MCP `get_hose_stats_info` tool for agent capability checking
- Single database now powers both dereplication AND 13C prediction

**Stats:**
- 17,552 lines of Python
- 642 tests
- 4 phases, 4 plans, 16 tasks
- 3 days from v1.1 to v1.2 (2026-01-15 → 2026-01-18)

**Git range:** `feat(16-01)` → `feat(19-01)`

**What's next:** Planning next milestone

---

## v1.1 Database-Backed Dereplication (Shipped: 2026-01-15)

**Delivered:** SQLite database backend enabling ~100x faster dereplication against 928K compounds (COCONUT + NMRShiftDB)

**Phases completed:** 11-15 (5 plans total)

**Key accomplishments:**
- SQLite database schema for storing 928K compounds with formula-indexed queries
- Database importer for batch loading from NMRShiftDB and COCONUT SDF files
- DatabaseQueryService API for formula-based compound lookup
- CLI auto-detection of database with `LUCY_DATABASE` env var support
- MCP tool integration with `database_type` field for agent transparency
- ~100x faster dereplication vs. SD file scanning

**Stats:**
- 42 files created/modified
- 11,196 lines of Python
- 5 phases, 5 plans
- 7 days from v1.0 to v1.1 (2026-01-08 → 2026-01-15)

**Git range:** `feat(11-01)` → `feat(15-01)`

**What's next:** Planning next milestone

---

## v1.0 Core CASE Pipeline (Shipped: 2026-01-12)

**Delivered:** Complete Computer-Assisted Structure Elucidation pipeline with 13 MCP tools, 7 CLI command groups, and LSD solver integration

**Phases completed:** 1-10 (12 plans total, including decimal phases 2.1, 4.1, 4.2, 5.1, 5.2)

**Key accomplishments:**
- Bruker 1D/2D NMR spectrum reading (1H, 13C, DEPT, HSQC, HMBC, COSY)
- DEPT-guided adaptive HSQC peak picking with multiplicity detection
- HMBC-guided peak picking to filter noise correlations
- Symmetry detection for molecular equivalence handling
- LSD solver integration with constraint generation and solution parsing
- HOSE-based 13C shift prediction for solution ranking
- NMRXiv dataset fetching for research evaluation
- 13 MCP tools for Claude agent integration
- 7 CLI command groups for scripting and testing

**Stats:**
- 100+ files created
- ~8,000 lines of Python (before v1.1)
- 12 phases (10 integer + 5 decimal insertions), 12 plans
- 5 days from start to v1.0 (2026-01-08 → 2026-01-12)

**Git range:** `feat(01-01)` → `feat(10-01)`

**What's next:** Database-backed dereplication for v1.1

---
