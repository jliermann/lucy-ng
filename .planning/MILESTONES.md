# Project Milestones: lucy-ng

## v3.0 Statistical Detection (Shipped: 2026-02-16)

**Delivered:** Data-driven statistical detection replacing agent guesswork in structure elucidation — hybridisation, neighbourhood, HHB detection from 7.9M HOSE statistics, two-tier ranking preventing MAE hallucinations, badlist strained ring exclusion, and full CASE agent integration with chemistry-first hierarchy.

**Phases completed:** 34-40 (21 plans total)

**Key accomplishments:**
- Hybridisation detection: sp1/sp2/sp3 state from HOSE database frequency distributions per 13C shift
- Neighbourhood detection: forbidden (<1%) and mandatory (>95%) bond partners from HOSE sphere 1
- Hetero-hetero bond detection: formula-level bond pair frequencies from bond_pair_stats table
- Signal grouping: complete linkage clustering identifies close 13C shifts for combinatorial LSD atom exchange
- Two-tier ranking: match count priority prevents MAE hallucination; badlist excludes 3/4-membered strained rings
- Agent integration: CASE agent uses statistical detection CLI with chemistry-first hierarchy (DEPT > HSQC > HMBC > shifts > detection)
- Database regenerated with v6 schema (7.89M HOSE stats, 8h39m), 762 tests passing, live UAT: ibuprofen rank #1 (MAE=2.23)

**Stats:**
- 7 phases, 21 plans, 51 commits
- 88 files changed, +19,700 / -214 lines
- 18,855 lines Python, 762 tests
- 2 days (2026-02-11 → 2026-02-12)

**Git range:** `feat(34-01)` → `docs(40-03)`

**Tech debt:** Agent behavior gaps (DEFF NOT dropped across iterations, signal grouping detected but not applied as SYME, grouped notation lost) — prompting issues, not code bugs. Deferred to next milestone.

**What's next:** Agent workflow refinement, COSY integration, fragment library

---

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

---

## v4.0 Team-Based CASE (Shipped: 2026-02-18)

**Delivered:** 5-agent collaborative CASE team replacing monolithic agent — coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate with real-time peer review, constraint inventory persistence, pre-run validation gates, aromatic ring awareness, and all v3.0 constraint-loss bugs fixed.

**Phases completed:** 41-48 + 46.1 (21 plans total)

**Key accomplishments:**
- 5-agent CASE team: orchestrator spawns coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate via TeamCreate with 3,460 lines of distributed agent/skill definitions
- Constraint inventory system: JSON-based tracking in LSD file headers prevents DEFF NOT, SYME, grouped notation, and detection result loss across iterations
- Devils-advocate pre-run validation: three-check inventory reconciliation (accuracy, regression, content) gates every LSD solver run
- Aromatic ring awareness: nmr-chemist flags aromatic expectation from sp2 clusters, solution-analyst verifies `has_aromatic_ring` on solutions, recommends 4J HMBC removal when mismatch detected
- Coordinator-as-sole-writer pattern: agents post via SendMessage, coordinator writes CASE-PROGRESS.md — prevents file corruption from concurrent writes
- All 5 v3.0 constraint-loss bugs verified fixed in UAT: DEFF NOT persistence, SYME applied, grouped notation preserved, PROP/BOND used, detection constraints translated

**Stats:**
- 9 phases (8 + 46.1), 21 plans, 48 commits
- 3,460 lines agent/skill definitions
- 18,963 lines Python, 768 tests
- 2 days (2026-02-17 → 2026-02-18)

**Git range:** `719f158` → `9055a62`

**Tech debt:** 3 WARNING-level integration gaps (write_progress aromatic field templates, lsd-engineer step 8 message source wording). Accepted as non-blocking — no behavioral impact, narrative documentation gaps only.

**What's next:** Statistical 4J coupling detection, multi-compound UAT, COSY integration

---


## v5.0 Fragment Library (Shipped: 2026-02-21)

**Delivered:** Substructure-subspectrum correlation (SSC) fragment library with 2.4M fragments from 928K compounds, two-phase search engine, DEFF/FEXP goodlist injection validated against LSD solver, and full CASE agent team integration — the last major feature gap for Sherlock parity.

**Phases completed:** 49-54 (12 plans total)

**Key accomplishments:**
- Fragment database: 2,385,146 SSCs extracted from 928K compounds via BFS sphere fragmentation with bond-preservation rules (605 MB, schema v7, checkpointed 3.5-hour pipeline)
- Fragment search engine: 256-bit fingerprint pre-screening + greedy fine matching (DEV 2 ppm, AVGDEV 1 ppm), ranked by atom count then deviation, sub-second search on 2.4M SSCs
- DEFF/FEXP goodlist: SMILES-to-SSTR/LINK fragment file conversion validated with LSD smoke test (toluene: 4 solutions → 1 with benzene ring goodlist)
- Agent integration: lsd-engineer searches fragments per iteration, devils-advocate verifies fragment files, orchestrator logs fragment status per iteration
- Self-search recall: 100% on 100-compound sample (fingerprint indexing validated)
- Full test suite: 867 tests (860 passing, 7 skipped), 20,974 lines Python

**Stats:**
- 6 phases, 12 plans, 47 commits
- 61 files changed, +13,861 / -2,338 lines
- 20,974 lines Python, 867 tests
- 3 days (2026-02-19 → 2026-02-21)

**Git range:** `feat(49-01)` → `docs(54)`

**Known gaps:** VALD-01 (multi-compound CASE comparison) deferred — all 6 local test compounds have 4J HMBC coupling risk, making controlled A/B fragment comparison unreliable. Self-search validation (VALD-02) PASSED.

**What's next:** Statistical 4J HMBC detection, non-aromatic test compounds for fragment UAT, COSY integration

---

