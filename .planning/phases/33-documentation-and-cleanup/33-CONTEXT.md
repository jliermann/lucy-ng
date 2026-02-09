# Phase 33: Documentation and Cleanup - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove deprecated components and update documentation to reflect the v2.1 architecture that now actually exists and works. Bring the diagnostic agent up to the same hybrid inlining standard as the CASE agent. No new features — only documentation accuracy and agent consistency.

</domain>

<decisions>
## Implementation Decisions

### CLAUDE.md update scope
- Add sub-command reference section — Claude decides detail level (names + one-liners vs usage examples) and placement in document
- Update stale references that point to old workflow (e.g., "For CASE domain knowledge, see skill/SKILL.md" → should reflect sub-command entry points)
- Architecture section must name the actual agent files (lucy-case-agent.md, lucy-diagnostic.md) with their roles — no vague "supervisor + CASE agent" language
- Remove or correct references to supervisor agent (dissolved into case.md orchestrator)

### Diagnostic agent hybrid inlining
- Bring lucy-diagnostic.md up to the same hybrid inlining standard as lucy-case-agent.md (Phase 28)
- Inline critical LSD manual sections from skill/diagnostic/SKILL.md into the agent definition — Claude decides the right balance (~400-600 lines critical content vs full 1,876 lines)
- This is treated as cleanup (bringing agents to consistent standard), not a new requirement
- Goal: diagnostic agent is GUARANTEED to have LSD command syntax knowledge in context when spawned, not dependent on runtime file reads

### PROJECT.md full refresh
- Update 3 v2.1 decisions in decisions table from "— Pending" to appropriate outcome
- Fix Current State section: remove "paper-only, not wired up" language, reflect actual agent names and wired-up architecture
- Update Active requirements: Claude decides whether to move to Validated or keep as Active with checkmarks
- Update version number if appropriate
- Make the entire document reflect current reality

### Claude's Discretion
- Release notes: not selected for discussion — Claude decides format, location, and depth per roadmap success criterion 4
- CLAUDE.md sub-command section detail level and placement
- How much of skill/diagnostic/SKILL.md to inline (critical sections vs full manual)
- Whether Active requirements move to Validated or stay with checkmarks
- supervisor.md deletion verification (already done — just confirm in CLNP-01)

</decisions>

<specifics>
## Specific Ideas

- User raised the diagnostic agent gap proactively: "How did we make sure that the diagnostic agent is an expert w/r to the LSD manual?" — this motivated the hybrid inlining decision
- CASE agent (Phase 28) uses ~528 lines of inlined knowledge as the benchmark for hybrid inlining
- The diagnostic agent is only spawned for deep failures, so having complete LSD knowledge is critical for accurate root cause analysis

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 33-documentation-and-cleanup*
*Context gathered: 2026-02-08*
