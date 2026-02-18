# lucy-ng

**AI-agent powered Computer-Assisted Structure Elucidation for organic natural products**

## What This Is

Lucy-ng is an AI-agent skill for Computer-Assisted Structure Elucidation (CASE) of organic natural products from NMR spectroscopy data. The AI agent is the intelligence layer -- it reasons about spectra, detects problems, and drives the elucidation process. The Python tools are thin wrappers around external libraries (nmrglue, LSD, RDKit) that give the agent access to NMR data and solvers. The skill (CLAUDE.md) encodes domain expertise and workflow strategy.

## Core Value

An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## Current State

**Version:** v4.0 shipped 2026-02-18
**Codebase:** ~18,963 lines Python, 768 tests, 10 CLI command groups
**Database:** SQLite v6 schema with 928K compounds and 7.89M HOSE statistics
**Agent definitions:** 3,460 lines across 5 agent files + orchestrator skill
**Live UAT:** Ibuprofen team-based CASE — all v3.0 constraint-loss bugs fixed, aromatic ring awareness added

**What v4.0 delivered:**
- 5-agent collaborative CASE team via TeamCreate (coordinator, nmr-chemist, lsd-engineer, solution-analyst, devils-advocate)
- Constraint inventory system preventing constraint loss across iterations
- Devils-advocate pre-run validation gate with three-check reconciliation
- Aromatic ring awareness (nmr-chemist flags expectation, solution-analyst verifies, remediation guidance)
- Coordinator-as-sole-writer pattern for CASE-PROGRESS.md
- Diagnostic specialist integration with team context and constraint inventory

**Known limitation:** 4J HMBC couplings through aromatic rings silently exclude correct structures. Ibuprofen correct structure not found due to 3 W-pathway 4J correlations enforced as 2-3 bond. Needs statistical 4J detection in next milestone.

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

### Deferred

- [ ] Support for COSY correlations in LSD constraints
- [ ] Fragment library for substructure suggestion
- [ ] Stereochemistry handling (E/Z, R/S)
- [ ] Interactive CASE mode with user feedback loop

### Out of Scope

- NMR spectrum prediction from structures - use HOSE codes instead
- GUI or web visualization - purely programmatic interface
- Non-Bruker vendor formats (Varian, JEOL, etc.) - Bruker only for v1
- SENECA integration - requires Java GUI rebuild, deferred
- Natural products likeness scoring - later feature

## Constraints

- Python 3.10+ required
- Open source only - no proprietary dependencies
- Open data formats - no vendor lock-in
- Must interface with existing LSD/pyLSD CLI tools

## Context

### Background

Lucy was the original CASE software created by the project author and sold to Bruker. Lucy-ng represents a complete reimagining for the AI-agent era, prioritizing programmatic interfaces over GUI interactions.

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

## Technical State

**Version:** v4.0 (shipped 2026-02-18)
**Codebase:** ~18,963 lines Python, 768 tests
**Tech stack:** Python 3.10+, Pydantic v2, nmrglue, RDKit, SQLite, Click
**Database:** v6 schema with 928K compounds, 7.89M HOSE statistics
**Agent definitions:** 3,460 lines across 6 files (5 agents + orchestrator skill)

**Capabilities:**
- 10 CLI command groups, 26+ commands (thin data-access wrappers)
- 4 statistical detection commands: hybridisation, neighbours, hhb, grouping
- Two-tier ranking with badlist strained ring exclusion + aromatic ring sanity check
- SQLite database with 928K compounds (COCONUT + NMRShiftDB)
- 7.89M HOSE statistics for 13C prediction and statistical detection
- Full CASE pipeline: peak picking → statistical detection → LSD generation → solving → ranking
- Sub-command skills: status, dereplicate, predict, sanitise, case (in ~/.claude/commands/lucy-ng/)
- 5-agent CASE team: lucy-nmr-chemist.md, lucy-lsd-engineer.md, lucy-solution-analyst.md, lucy-devils-advocate.md + case.md orchestrator
- Diagnostic specialist: lucy-diagnostic.md (constraint inventory-aware, team context)
- CASE orchestrator: spawns 5-agent team via TeamCreate, monitors CASE-PROGRESS.md, detects 4 loop patterns, intervenes with advisory constraints, delegates to diagnostic specialist
- Constraint inventory: JSON tracking in LSD file headers, DA reconciliation gate

**Known tech debt (from v4.0 UAT):**
- 4J HMBC couplings through aromatic rings not detected — silently excludes correct structures
- 3 WARNING-level write_progress template gaps (aromatic field propagation)
- Multi-compound UAT not yet performed (only ibuprofen tested)

---
*Last updated: 2026-02-18 after v4.0 milestone complete*
