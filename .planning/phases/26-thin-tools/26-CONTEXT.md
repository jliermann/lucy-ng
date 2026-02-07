# Phase 26: Thin Tools - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 26 removes the MCP server entirely and makes all CLI commands thin data-access wrappers. The AI agent becomes the sole intelligence layer, using skill documents for reasoning and CLI commands via Bash for data access. This is a fundamental architecture simplification: no MCP, no embedded intelligence in tools, AI writes LSD files directly.

</domain>

<decisions>
## Implementation Decisions

### MCP Removal
- **Remove MCP server entirely** -- delete `src/lucy_ng/mcp/server.py` and all MCP infrastructure
- AI agent uses `lucy ...` CLI commands via Bash tool instead of MCP tool calls
- No dual-mode architecture needed -- single interface (CLI), single intelligence layer (AI)

### CLI Simplification
- **All CLI commands become thin** -- remove embedded intelligence from every command, not just Tier 3
- `lucy lsd generate` **removed entirely** -- AI writes LSD files directly using skill knowledge
- `lucy pick hsqc` becomes thin: returns raw HSQC peaks above threshold, no DEPT-guided filtering
- `lucy pick hmbc` becomes thin: returns raw HMBC peaks above threshold, no cross-validation filtering
- `lucy analyze symmetry` becomes thin: returns raw intensity data and carbon counts, no heuristic inference
- Tier 2 tools (pick_peaks_1d, dereplicate_c13, rank_lsd_solutions, predict_c13_shifts) to be reviewed and adjusted -- may also have intelligence to remove
- Tier 1 tools (read, fetch, check, run, visualize, hose stats) stay as-is

### Code Consolidation
- **Include in Phase 26**: consolidate the 3 duplicated code areas into shared utilities
  - Experiment auto-discovery: shared utility in lsd/ or processing/
  - Database auto-detection: move to database/finder.py
  - LSD file parsing: move to lsd/parser.py

### Test Strategy
- Claude's Discretion: decide whether to delete smart-behavior tests or keep as regression tests for the underlying algorithms

### CLAUDE.md Cleanup
- Remove all MCP-related sections (Tool Output Reference for MCP, MCP server references, MCP permissions in settings.json)
- Update to reflect CLI-only architecture

### Skill Migration
- AI reasons from **first principles**, not memorized heuristics -- SKILL.md teaches NMR fundamentals, not "if shift > 165 then carbonyl"
- The diagnostic agent needs deep LSD manual training to become a total expert -- Claude decides the best approach for this
- Existing skill content from Phases 22-23 (HMBC strategy, error tolerance, confidence scoring) stays as-is
- skill/diagnostic/SKILL.md Section 1 has the LSD command reference; Claude decides if SKILL.md needs additional LSD writing guidance

### Validation
- Validate on **Ibuprofen** (existing test data at data/Ibuprofen/)
- De novo CASE only -- dereplication does not count for quality validation
- Success bar: AI performs CASE using thin CLI + skill knowledge, and correct Ibuprofen structure appears as a **top-ranked** LSD solution (top 3)

</decisions>

<specifics>
## Specific Ideas

- "AI is the intelligence" -- the user's guiding principle for this phase. Tools are data pipes, nothing more.
- "CLI should be maximally thin" -- no smart defaults, no embedded heuristics, no domain inference in Python
- The diagnostic specialist agent needs to be trained as a "total expert" on the LSD manual

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 26-thin-tools*
*Context gathered: 2026-02-07*
