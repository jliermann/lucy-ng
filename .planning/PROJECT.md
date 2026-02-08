# lucy-ng

**AI-agent powered Computer-Assisted Structure Elucidation for organic natural products**

## What This Is

Lucy-ng is an AI-agent skill for Computer-Assisted Structure Elucidation (CASE) of organic natural products from NMR spectroscopy data. The AI agent is the intelligence layer -- it reasons about spectra, detects problems, and drives the elucidation process. The Python tools are thin wrappers around external libraries (nmrglue, LSD, RDKit) that give the agent access to NMR data and solvers. The skill (CLAUDE.md) encodes domain expertise and workflow strategy.

## Core Value

An AI agent can autonomously determine the structure of an unknown organic compound from its NMR spectra, with a multi-agent architecture that prevents unproductive loops and keeps the elucidation on track.

## Current Milestone: v2.1 Working Multi-Agent CASE

**Goal:** Make the multi-agent architecture actually work — sub-command skills following the GSD pattern, real agent spawning and result collection, working AI-driven sanitisation.

**Target features:**
- Sub-command skills: `/lucy-ng:case`, `/lucy-ng:sanitise`, `/lucy-ng:dereplicate`, `/lucy-ng:predict`, `/lucy-ng:status`
- CASE orchestrator that spawns autonomous CASE agent, monitors progress, detects loops, spawns diagnostic specialist
- AI-driven dataset sanitisation (no CLI — AI reasoning required to identify compound identifiers)
- Old monolithic skill and paper-only agent definitions replaced by working GSD-pattern orchestration

## Architecture

- **Skill** (CLAUDE.md/SKILL.md): Domain expertise, workflow strategy, error handling knowledge -- the intelligence layer
- **Thin Tools**: Minimal Python CLI/MCP wrappers around nmrglue, LSD, RDKit, SQLite
- **Multi-Agent**: CASE agent (does the work) + Supervisor agent (keeps it on track) + optional specialist agents
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

### Active

- [ ] Sub-command skills following GSD pattern (sanitise, dereplicate, case, predict, status)
- [ ] CASE orchestrator with real agent spawning, progress monitoring, loop detection, diagnostic delegation
- [ ] Autonomous CASE agent definition with full skill knowledge and CASE-PROGRESS.md writing
- [ ] AI-driven dataset sanitisation (compound identity removal, no CLI)
- [ ] Diagnostic specialist agent reworked for orchestrator integration

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
| GSD-pattern sub-commands | v2.1: Skills as ~/.claude/commands/lucy-ng/*.md with Task() agent spawning | — Pending |
| /lucy-ng:case NEVER dereplicates | v2.1: Absolute separation — dereplication is a separate sub-command | — Pending |
| Sanitisation is AI-only | v2.1: No CLI for sanitise — requires AI reasoning to identify compound identifiers | — Pending |

## Current State

**Version:** v2.0 (shipped 2026-02-08)
**Codebase:** ~17,500 lines Python, 642 tests
**Tech stack:** Python 3.10+, Pydantic v2, nmrglue, RDKit, SQLite, Click

**Capabilities:**
- 9 CLI command groups, 22 commands (thin data-access wrappers)
- SQLite database with 928K compounds (COCONUT + NMRShiftDB)
- 7.9M HOSE statistics for database-backed 13C prediction
- Full CASE pipeline: peak picking → LSD generation → solving → ranking
- Skill documents: SKILL.md (1,079 lines), supervisor SKILL.md (827 lines), diagnostic SKILL.md (1,874 lines)
- Agent definitions: supervisor.md, diagnostic-specialist.md (paper-only, not wired up)

**What v2.0 delivered vs what's missing:**
- Delivered: Skill restructure, thin CLI, MCP removal, domain knowledge in skills
- Missing: Actual multi-agent orchestration — agents defined on paper but never invoked

---
*Last updated: 2026-02-08 after v2.1 milestone started*
