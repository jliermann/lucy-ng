# lucy-ng

**AI-agent powered Computer-Assisted Structure Elucidation for organic natural products**

## Vision

Lucy-ng is the next-generation successor to Lucy, designed for AI-agent (Claude) driven structure elucidation from NMR spectroscopic data. Unlike GUI-focused tools like nmrium, lucy-ng is built for programmatic, unattended operation where an AI agent can iterate through the elucidation process until a structure is determined.

The system reads Bruker NMR data, performs peak picking, generates constraints, and interfaces with structure elucidation solvers (LSD/pyLSD) in a hybrid loop that combines constraint-based generation with prediction-based validation.

## Architecture

- **Core**: Python 3.10+ library for NMR processing and CASE workflow
- **CLI**: Command-line interface for testing, debugging, and scripting
- **MCP Server**: Model Context Protocol tools for Claude agent integration
- **Solver Interface**: Wrapper for LSD/pyLSD command-line tools

## Requirements

### Validated

(None yet - ship to validate)

### Active

- [ ] Read 1D Bruker NMR files (1H, 13C)
- [ ] Read 2D Bruker NMR files (HSQC, HMBC)
- [ ] Automated peak picking for 1D spectra
- [ ] Automated peak picking for 2D spectra
- [ ] Generate LSD/pyLSD input file format
- [ ] Execute LSD/pyLSD and parse results
- [ ] CLI interface for all operations
- [ ] MCP server exposing tools for Claude

### Out of Scope

- NMR spectrum prediction from structures - use external tools
- Natural products database searching - later feature
- GUI or web visualization - purely programmatic interface
- Non-Bruker vendor formats (Varian, JEOL, etc.) - Bruker only for v1
- SENECA integration - requires Java GUI rebuild, deferred
- Natural products likeness scoring - later feature

## Constraints

- Python 3.10+ required
- Open source only - no proprietary dependencies
- Open data formats - no vendor lock-in
- Must interface with existing LSD/pyLSD CLI tools

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hybrid CLI + MCP interface | MCP provides structured tools for agent iteration; CLI enables testing and scripting | Pending |
| Bruker-only for v1 | Focus on most common format, expand vendor support later | Pending |
| LSD/pyLSD as primary solvers | Established CASE tools with CLI interface | Pending |
| Research-first for NMR parsing | Evaluate nmrglue vs nmrium components vs custom | Pending |
| Hybrid elucidation loop | Combine constraint-based generation AND prediction-based validation | Pending |

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

---
*Last updated: 2026-01-08 after initialization*
