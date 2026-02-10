# lucy-ng

**AI-agent powered Computer-Assisted Structure Elucidation for organic natural products**

## What This Is

Lucy-ng is an AI-agent skill for Computer-Assisted Structure Elucidation (CASE) of organic natural products from NMR spectroscopy data. The AI agent is the intelligence layer -- it reasons about spectra, detects problems, and drives the elucidation process. The Python tools are thin wrappers around external libraries (nmrglue, LSD, RDKit) that give the agent access to NMR data and solvers. The skill (CLAUDE.md) encodes domain expertise and workflow strategy.

## Core Value

An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## Current Milestone: v3.0 Statistical Detection (Active)

**Goal:** Add data-driven statistical detection to replace agent guesswork — hybridisation detection, neighbourhood constraints, hetero-hetero bond allowance, improved ranking, and badlist filters. Inspired by Sherlock CASE system analysis (Wenk PhD thesis).

**Target features:**
- CLI commands for statistical hybridisation detection from HOSE database (sp1/sp2/sp3 frequencies per shift)
- CLI commands for forbidden/mandatory neighbour detection from bond partner distributions
- CLI command for hetero-hetero bond allowance detection from bond pair statistics
- Two-tier ranking: signal match count first, then average deviation
- Badlist filters for 3/4-membered ring exclusion in LSD
- Agent integration: CASE agent uses statistical detection CLI to write better-constrained LSD files
- Signal grouping detection (identify close shifts within 0.25 ppm tolerance)

**Motivation:** Live testing revealed that lucy-ng's ibuprofen CASE produced 8 wrong cyclohexadiene solutions (not ibuprofen). Sherlock solves the same problem trivially because statistical constraints reduce search space by 5 orders of magnitude (Caripyrin: 8.5M -> 10 structures from hybridisation + neighbours alone). Without data-driven constraints, the AI agent is guessing.

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

### Active

- [ ] Statistical hybridisation detection from HOSE database
- [ ] Statistical neighbourhood detection (forbidden/mandatory)
- [ ] Hetero-hetero bond allowance detection
- [ ] Signal grouping detection (close shifts within tolerance)
- [ ] Two-tier ranking (match count + deviation)
- [ ] Badlist filters (3/4-membered ring exclusion)
- [ ] CASE agent integration with statistical detection CLI

### Deferred

- [ ] Support for COSY correlations in LSD constraints -- notoriously difficult to analyze
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

## Current State

**Version:** v3.0-dev (milestone started 2026-02-10, building on v2.1 shipped 2026-02-09)
**Codebase:** ~17,500 lines Python, 642 tests
**Tech stack:** Python 3.10+, Pydantic v2, nmrglue, RDKit, SQLite, Click

**Capabilities:**
- 9 CLI command groups, 22 commands (thin data-access wrappers)
- SQLite database with 928K compounds (COCONUT + NMRShiftDB)
- 7.9M HOSE statistics for database-backed 13C prediction
- Full CASE pipeline: peak picking → LSD generation → solving → ranking
- Skill documents: SKILL.md (1,079 lines), diagnostic SKILL.md (1,874 lines)
- Sub-command skills: status, dereplicate, predict, sanitise, case (in ~/.claude/commands/lucy-ng/)
- Agent definitions: lucy-case-agent.md (613 lines, hybrid inlined), lucy-diagnostic.md (hybrid inlined)
- CASE orchestrator: spawns autonomous agent, monitors CASE-PROGRESS.md, detects 4 loop patterns, intervenes with advisory constraints, delegates to diagnostic specialist

**What v2.1 delivered:**
- Working multi-agent orchestration: CASE agent spawned via Task(), progress monitored, loops detected and intervened
- Sub-command skills replacing monolithic /lucy-ng skill
- AI-driven sanitisation without CLI dependency
- Diagnostic specialist integration with delegation threshold
- v2.0's paper-only agent architecture replaced with working GSD-pattern orchestration

---
*Last updated: 2026-02-10 after v3.0 milestone started*
