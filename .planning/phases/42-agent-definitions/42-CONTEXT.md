# Phase 42: Agent Definitions with Knowledge Distribution - Context

**Gathered:** 2026-02-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Decompose the monolithic 1280-line lucy-case-agent.md into 4 specialist agent definitions with distributed domain knowledge and clear inter-agent interfaces. Each specialist gets the knowledge it needs to operate autonomously within its role. The old lucy-case-agent.md is preserved as reference.

**Not in scope:** Constraint inventory system (Phase 43), CASE-PROGRESS.md format (Phase 44), team coordination protocol (Phase 45). This phase creates the agent files with knowledge; coordination logic comes later.

</domain>

<decisions>
## Implementation Decisions

### Coordinator role resolution
- Phase 41 decided: orchestrator skill (case.md) IS the coordinator/team lead
- No separate coordinator agent definition is created
- SC1 in roadmap says "5 roles including coordinator" but the coordinator is the orchestrator itself
- Phase 42 creates/updates 4 agent definitions: nmr-chemist, lsd-engineer, solution-analyst, devils-advocate
- The existing stub files from Phase 41 are replaced with full definitions

### Knowledge distribution boundaries
The 1280-line lucy-case-agent.md has 8 major sections. Distribution by responsibility:

**NMR-Chemist gets:**
- Section 1: NMR Background (experiment types, shift regions, common pitfalls) -- EXCLUSIVE
- Section 2: Spectral Quality Assessment (S/N, digital resolution, artifacts) -- EXCLUSIVE
- Section 3.5: Statistical Detection Protocol (all subsections) -- EXCLUSIVE
- Section 3.6: Chemistry-First Hierarchy (evidence priority, conflict resolution) -- EXCLUSIVE
- Section 6: Error Tolerance and Ambiguity Detection (close carbons, DEPT conflicts, quaternary sparsity) -- EXCLUSIVE
- Section 7: Confidence Scoring (per-atom, per-structure) -- SHARED with solution-analyst

**LSD-Engineer gets:**
- Section 3: LSD Command Reference (MULT, HSQC, HMBC, BOND, LIST, PROP, ELEM, SYME, DEFF, ELIM) -- EXCLUSIVE
- Section 3 subsections: correlation order, hybridization rules, ELIM, solution conversion, manual checklist, badlist -- EXCLUSIVE
- Section 4: Incremental HMBC Strategy (core principle, selection criteria, adaptive loop, stopping conditions, zero-solution recovery) -- EXCLUSIVE
- Section 5: CASE Workflow file organization rules -- EXCLUSIVE
- Section 8: CASE-PROGRESS.md Format -- SHARED with all (everyone reads/writes progress)

**Solution-Analyst gets:**
- Section 5 ranking algorithm (two-tier: match count then MAE) -- EXCLUSIVE
- Section 7: Confidence Scoring -- SHARED with nmr-chemist
- lucy lsd rank CLI usage and interpretation -- EXCLUSIVE
- lucy predict c13 CLI usage for shift prediction -- EXCLUSIVE

**Devils-Advocate gets:**
- Section 3 hybridization rules (sp2 even count) -- SHARED reference from lsd-engineer
- Section 3 badlist filters (DEFF NOT patterns) -- SHARED reference from lsd-engineer
- Section 6: Error Tolerance (close carbons, multiplicity conflicts) -- SHARED reference from nmr-chemist
- Diff protocol: what to check between iterations -- EXCLUSIVE (new content)
- Constraint persistence checklist -- EXCLUSIVE (new content, derived from v3.0 UAT findings)

### Inter-agent message schemas
- Messages use plain text with structured sections, NOT JSON payloads
- Each agent's definition specifies WHAT it posts to the team and WHAT it reads from others
- Structured sections use markdown headers within the message body for parseability
- Example: NMR-Chemist posts peak assignments as markdown table with columns: Atom#, Shift, Multiplicity, Confidence

**NMR-Chemist outputs:**
- Peak assignments (atom number, shift, multiplicity, confidence)
- Statistical detection results (hybridisation, neighbours, hhb, grouping)
- Spectral quality assessment (S/N, artifact flags)

**LSD-Engineer outputs:**
- Iteration summary (constraints added/removed, solution count)
- LSD file path for current iteration
- Request for additional HMBC correlations or detection results

**Solution-Analyst outputs:**
- Ranked solutions table (rank, SMILES, MAE, matched count, quality)
- Chemical plausibility assessment
- Final results summary

**Devils-Advocate outputs:**
- Constraint diff report (what changed between iterations)
- Validation checklist (sp2 count, H budget, DEFF NOT persistence, SYME applied)
- Issue flags with severity (CRITICAL/WARNING/INFO)

### Shared knowledge policy
- **Minimal duplication:** Each knowledge section lives in ONE agent's definition as the authoritative source
- **Cross-references allowed:** Agents can reference concepts by name (e.g., "See LSD-Engineer's hybridization rules") without duplicating the full content
- **Shared essentials inlined:** Brief context that every agent needs (e.g., what NMR experiments are, what the CASE workflow does) is a 5-10 line summary in each agent, NOT the full section
- **CASE-PROGRESS.md format:** All agents need to read/write this, so the format specification is shared across all definitions (brief version in each, full version in lsd-engineer)
- **lucy CLI commands:** Each agent gets ONLY the CLI commands relevant to its role (nmr-chemist gets peak picking, lsd-engineer gets lsd run, solution-analyst gets lsd rank and predict c13)

### Agent file sizing targets
- Each agent definition should be 150-300 lines (vs. 1280 combined in monolith)
- Total across 4 agents: ~600-1200 lines (some shared content adds overhead but still more focused)
- If an agent exceeds 400 lines, knowledge is probably leaking across boundaries

### Tools per agent
- **NMR-Chemist:** Read, Write, Bash, Glob, Grep (needs Bash for lucy CLI peak picking and detection)
- **LSD-Engineer:** Read, Write, Bash, Glob, Grep (needs Bash for lucy lsd run, outlsd, file operations)
- **Solution-Analyst:** Read, Write, Bash, Glob, Grep (needs Bash for lucy lsd rank, lucy predict c13)
- **Devils-Advocate:** Read, Bash, Glob, Grep (reads LSD files, runs diff checks -- Write for logging only)

### Claude's Discretion
- Exact prose and formatting of each agent definition
- Whether to use XML tags (like the current agent) or markdown headers for sections
- How to handle the 5-10 line shared context summary (template vs. unique per agent)
- Order of sections within each agent definition

</decisions>

<specifics>
## Specific Ideas

- The existing lucy-case-agent.md (1280 lines) is the definitive source for all knowledge to distribute. No new domain knowledge is invented -- it is decomposed and redistributed.
- v3.0 UAT findings (MEMORY.md) revealed 5 specific agent behavior bugs. The devils-advocate agent definition should include explicit checks for all 5:
  1. DEFF NOT patterns dropped after iteration 1
  2. Signal grouping detected but never applied as SYME
  3. Grouped atom notation dropped after iteration 1
  4. PROP not used despite being documented
  5. No ELIM/LIST constraints from neighbourhood detection
- Agent definitions follow the same YAML frontmatter pattern as lucy-case-agent.md and lucy-diagnostic.md (name, description, tools, model fields)
- All agents use model: claude-opus-4-6 (matches Phase 41 spawn with model="opus")
- Each agent must include team communication instructions: how to use SendMessage, TaskList, TaskUpdate

</specifics>

<deferred>
## Deferred Ideas

- Constraint inventory JSON schema (Phase 43) -- will be referenced by lsd-engineer and devils-advocate but designed in Phase 43
- CASE-PROGRESS.md multi-agent format (Phase 44) -- agents need to write progress but the format is defined in Phase 44
- Iteration workflow and task assignment protocol (Phase 45) -- agents know their roles but the coordination sequence is Phase 45
- COSY integration -- deferred beyond v4.0 per MEMORY.md

</deferred>

---

*Phase: 42-agent-definitions*
*Context gathered: 2026-02-17*
