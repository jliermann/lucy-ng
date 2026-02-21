# lucy-ng

**AI-agent powered Computer-Assisted Structure Elucidation for organic natural products**

## What This Is

Lucy-ng is an AI-agent skill for Computer-Assisted Structure Elucidation (CASE) of organic natural products from NMR spectroscopy data. The AI agent is the intelligence layer -- it reasons about spectra, detects problems, and drives the elucidation process. The Python tools are thin wrappers around external libraries (nmrglue, LSD, RDKit) that give the agent access to NMR data and solvers. The skill (CLAUDE.md) encodes domain expertise and workflow strategy.

## Core Value

An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## Current State

**Version:** v5.0 shipped 2026-02-21
**Codebase:** ~20,974 lines Python, 867 tests, 11 CLI command groups
**Database:** SQLite v6 schema with 928K compounds, 7.89M HOSE statistics + fragment library (2.4M SSCs, 605 MB)
**Agent definitions:** ~3,600 lines across 5 agent files + orchestrator skill (updated with fragment search workflow)

**What shipped in v5.0:** Fragment library infrastructure — 2,385,146 SSCs from 928K compounds, two-phase search engine (fingerprint pre-screening + fine matching), DEFF/FEXP goodlist injection validated with LSD smoke test, full agent team integration. Self-search recall 100%.

**Known limitation:** 4J HMBC couplings through aromatic rings silently exclude correct structures. All 6 local test compounds have this risk, preventing controlled fragment A/B testing. Statistical 4J detection is the highest-priority next feature.

## Architecture

- **Skill** (CLAUDE.md/SKILL.md): Domain expertise, workflow strategy, error handling knowledge -- the intelligence layer
- **Thin Tools**: Minimal Python CLI wrappers around nmrglue, LSD, RDKit, SQLite
- **Multi-Agent**: CASE agent (autonomous elucidation) + CASE orchestrator (loop detection, advisory intervention) + diagnostic specialist (deep LSD failure analysis)
- **Database**: SQLite with 928K compounds and 7.9M HOSE statistics

## Requirements

### Validated

- Read 1D Bruker NMR files (1H, 13C) — v1.0
- Read 2D Bruker NMR files (HSQC, HMBC, COSY) — v1.0
- Automated peak picking for 1D spectra — v1.0
- Automated peak picking for 2D spectra (DEPT-guided, HMBC-guided) — v1.0
- Generate LSD/pyLSD input file format — v1.0
- Execute LSD/pyLSD and parse results — v1.0
- CLI interface for all operations (7 command groups) — v1.0
- MCP server exposing tools for Claude (13 tools) — v1.0
- HOSE-based 13C shift prediction for solution ranking — v1.0
- NMRXiv dataset fetching — v1.0
- SQLite database for 928K compounds (COCONUT + NMRShiftDB) — v1.1
- Database-backed dereplication (~100x faster) — v1.1
- Database-backed 13C prediction with 7.9M HOSE statistics — v1.2
- MCP tool for checking prediction capability (get_hose_stats_info) — v1.2
- Sub-command skills following GSD pattern (sanitise, dereplicate, case, predict, status) — v2.1
- CASE orchestrator with real agent spawning, progress monitoring, loop detection, diagnostic delegation — v2.1
- Autonomous CASE agent definition with full skill knowledge and CASE-PROGRESS.md writing — v2.1
- AI-driven dataset sanitisation (compound identity removal, no CLI) — v2.1
- Diagnostic specialist agent reworked for orchestrator integration — v2.1
- Statistical hybridisation detection from HOSE database (sp1/sp2/sp3) — v3.0
- Statistical neighbourhood detection (forbidden/mandatory bond partners) — v3.0
- Hetero-hetero bond allowance detection from bond pair statistics — v3.0
- Signal grouping detection (close shifts within 0.25 ppm tolerance) — v3.0
- Two-tier ranking (match count priority prevents MAE hallucination) — v3.0
- Badlist filters (3/4-membered strained ring exclusion via DEFF NOT) — v3.0
- CASE agent integration with statistical detection and chemistry-first hierarchy — v3.0

### Validated (v4.0)

- 5-agent CASE team architecture (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate) — v4.0
- Team-based orchestrator skill replacing single-agent Task() spawning — v4.0
- Constraint inventory managed by lsd-engineer (read previous file, never reconstruct from memory) — v4.0
- Pre-run LSD validation by devils-advocate (diff vs previous, sp2, H budget, DEFF NOT, SYME) — v4.0
- Post-run solution quality review by solution-analyst (chemical plausibility, aromatic ring verification) — v4.0
- Real-time peer feedback protocol (any agent can flag issues in any other agent's work) — v4.0
- CASE-PROGRESS.md updated for team workflow (multi-agent contributions per iteration) — v4.0
- Aromatic ring awareness: nmr-chemist flags expectation, solution-analyst verifies, remediation guidance for 4J — v4.0
- Diagnostic specialist integration with team context (constraint inventory, analysis/ paths) — v4.0

### Validated (v5.0)

- Fragment library: 2.4M SSCs from 928K compounds with two-phase search engine — v5.0
- DEFF/FEXP goodlist injection validated with LSD smoke test — v5.0
- Agent team integration: lsd-engineer fragment search, devils-advocate file verification — v5.0
- Self-search recall 100% (fingerprint indexing validated) — v5.0

### Deferred

- [ ] Statistical 4J HMBC coupling detection (Priority 1 — v4.0/v5.0 UAT root cause)
- [ ] Multi-compound CASE comparison UAT (blocked on 4J detection or non-aromatic test compounds)
- [ ] Support for COSY correlations in LSD constraints (Priority 3)
- [ ] NP-likeness scoring for solution filtering (Priority 4 — RDKit built-in)
- [ ] Multi-fragment sequential injection (FRAG-05)
- [ ] Solvent-aware 13C prediction
- [ ] Stereochemistry handling (E/Z, R/S)
- [ ] Interactive CASE mode with user feedback loop

### Out of Scope

- NMR spectrum prediction from structures - use HOSE codes instead
- GUI or web visualization - purely programmatic interface
- Non-Bruker vendor formats (Varian, JEOL, etc.) - Bruker only for v1
- SENECA integration - requires Java GUI rebuild, deferred

## Constraints

- Python 3.10+ required
- Open source only - no proprietary dependencies
- Open data formats - no vendor lock-in
- Must interface with existing LSD/pyLSD CLI tools

## Context

### Background

Lucy was the original CASE software created by the project author and sold to Bruker. Lucy-ng represents a complete reimagining for the AI-agent era, prioritizing programmatic interfaces over GUI interactions.

### Strategic Reference

See `background/sherlock-analysis.md` — deep comparison of Sherlock CASE (Wenk PhD thesis) vs lucy-ng capabilities. Updated post-v4.0 with gap closure status and prioritized next milestones. Key finding: 4 of 5 critical gaps closed (v3.0/v4.0); fragment library (24.5M SSCs) is the remaining major gap for Sherlock parity.

### Problem

Existing NMR processing tools like nmrium are GUI-focused, making it difficult for AI agents to interact with them programmatically. An unattended system that can iterate through structure elucidation without human intervention requires a different architecture.

### Target Users

- Cheminformatics researchers
- Natural products chemists
- AI/ML researchers working on structure elucidation

### NMR Data Requirements

Minimum viable spectral data for v1:
- 1D: 1H and 13C spectra
- 2D: HSQC (direct C-H correlations) and HMBC (long-range correlations)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid CLI + MCP interface | MCP provides structured tools for agent iteration; CLI enables testing and scripting | Good |
| Bruker-only for v1 | Focus on most common format, expand vendor support later | Good |
| LSD/pyLSD as primary solvers | Established CASE tools with CLI interface | Good |
| nmrglue for NMR parsing | Most mature, BSD licensed, native Bruker support | Good |
| Pydantic v2 for models | Type safety, validation, JSON serialization | Good |
| DEPT-guided adaptive thresholding | Lower HSQC threshold until all DEPT carbons matched | Good |
| HMBC-guided peak picking | Filter by requiring C match in 13C/DEPT and H match in HSQC | Good |
| N:1 shift matching for ranking | Handles molecular symmetry correctly | Good |
| SQLite for dereplication DB | Portable, no server, formula-indexed for fast lookup | Good |
| HOSE codes for prediction | Pure Python, no external services, reasonable accuracy | Good |
| AI as intelligence layer | v2.0: Domain knowledge belongs in skill, not Python code | Good |
| Multi-agent CASE | v2.0: Supervisor prevents loops, specialists handle subtasks | Revisit — v2.0 defined on paper only, v2.1 delivers working orchestration |
| Error tolerance as skill knowledge | v2.0: Teach AI to detect close shifts, ambiguity -- not Python machinery | Good |
| MCP removed, CLI-only | v2.0: Single interface, AI uses thin CLI via Bash | Good |
| GSD-pattern sub-commands | v2.1: Skills as ~/.claude/commands/lucy-ng/*.md with Task() agent spawning | Good |
| /lucy-ng:case NEVER dereplicates | v2.1: Absolute separation — dereplication is a separate sub-command | Good |
| Sanitisation is AI-only | v2.1: No CLI for sanitise — requires AI reasoning to identify compound identifiers | Good |
| Orchestration via Task() | v2.1: Orchestrator spawns agents using Task() with model: inherit | Good |
| Hybrid context inlining | v2.1: ~500-700 lines critical knowledge inlined in agents, detailed references via file paths | Good |
| Per-pattern intervention counters | v2.1: Track failures separately per loop pattern, 10-cycle escalation | Good |
| Diagnostic delegation threshold | v2.1: Specialist spawned after 2 failed basic interventions with same pattern | Good |
| Data-driven statistical detection | v3.0: Replace agent guesswork with HOSE database statistics (inspired by Sherlock CASE) | Good |
| Chemistry-first hierarchy | v3.0: NMR evidence (DEPT/HSQC/HMBC) always overrides statistical detection | Good |
| Two-tier ranking | v3.0: Match count primary, MAE secondary — prevents hallucination from wrong structures with coincidentally low MAE | Good |
| Badlist via DEFF NOT | v3.0: Hardcoded strained ring exclusion in agent knowledge rather than automated filtering | Good — but agent drops across iterations |
| Schema migration chain | v3.0: ALTER TABLE v3→v4→v5→v6 with backward-compatible queries | Good |
| Team-based CASE | v4.0: 5-agent team (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate) replacing single autonomous agent. Peer feedback eliminates constraint loss. | Good — all v3.0 bugs fixed |
| Constraint inventory in LSD headers | v4.0: JSON block tracking all constraint types, read-previous-never-reconstruct rule, DA reconciliation | Good |
| Coordinator-as-sole-writer | v4.0: Agents post via SendMessage, coordinator writes CASE-PROGRESS.md — prevents corruption | Good |
| Aromatic ring awareness | v4.0: Post-ranking sanity check when NMR evidence shows aromatic pattern but solutions lack rings | Good — caught in UAT |
| Separate fragment DB | v5.0: lucy-ng-fragments.db (605 MB) independent from main DB (2.8 GB) — prevents Dropbox sync contention | Good |
| 2 ppm fingerprint bins | v5.0: 256-bit fingerprint with 2 ppm bins validated by 100% self-search recall on 1K sample | Good |
| DEFF goodlist over badlist | v5.0: DEFF/FEXP constrains structures TO contain fragment (positive constraint, more powerful than exclusion) | Good — LSD smoke test confirms |
| Fragment persistence rule | v5.0: Copy DEFF F1/FEXP from previous LSD file, never reconstruct — same as DEFF NOT rule | Good |
| UAT deferral for 4J risk | v5.0: All 6 compounds have 4J HMBC risk, deferred CASE comparison to avoid confounding variables | Pending — need non-aromatic compounds |

## Technical State

**Version:** v5.0 (shipped 2026-02-21)
**Codebase:** ~20,974 lines Python, 867 tests
**Tech stack:** Python 3.10+, Pydantic v2, nmrglue, RDKit, NumPy, SQLite, Click
**Database:** v6 schema with 928K compounds, 7.89M HOSE statistics + fragment library (2.4M SSCs, 605 MB)
**Agent definitions:** ~3,600 lines across 6 files (5 agents + orchestrator skill)

**Capabilities:**
- 11 CLI command groups, 30+ commands (thin data-access wrappers)
- 4 statistical detection commands: hybridisation, neighbours, hhb, grouping
- Fragment library: build, search, to-lsd, info commands
- Two-tier ranking with badlist strained ring exclusion + aromatic ring sanity check
- SQLite databases: compound DB (928K compounds, COCONUT + NMRShiftDB) + fragment DB (2.4M SSCs)
- 7.89M HOSE statistics for 13C prediction and statistical detection
- Full CASE pipeline: peak picking → statistical detection → fragment search → LSD generation → solving → ranking
- Sub-command skills: status, dereplicate, predict, sanitise, case (in ~/.claude/commands/lucy-ng/)
- 5-agent CASE team with fragment integration: lsd-engineer searches+injects fragments, devils-advocate verifies files
- Diagnostic specialist: lucy-diagnostic.md (constraint inventory-aware, team context)
- CASE orchestrator: spawns 5-agent team via TeamCreate, monitors CASE-PROGRESS.md, detects 4 loop patterns
- Constraint inventory: JSON tracking in LSD file headers, DA reconciliation gate, DEFF/FEXP tracking

**Known tech debt:**
- 4J HMBC couplings through aromatic rings not detected — silently excludes correct structures (highest priority)
- Multi-compound CASE UAT deferred — all test compounds have 4J risk
- 3 WARNING-level write_progress template gaps (aromatic field propagation)

---
*Last updated: 2026-02-21 after v5.0 milestone complete*
