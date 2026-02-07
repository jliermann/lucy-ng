# Phase 24: Supervisor Agent - Context

**Gathered:** 2026-02-07
**Status:** Ready for planning

<domain>
## Phase Boundary

A supervisor agent that wraps the CASE workflow, detects when the CASE agent is stuck in an unproductive loop, and intervenes with diagnosis-first redirects. The supervisor is the single entry point for all lucy-ng invocations (routing to dereplication, CASE, sanitize, etc.). Covers SUPV-01 through SUPV-07.

Phase 25 (Diagnostic Specialist) adds a dedicated LSD expert agent that the supervisor can later delegate to. Phase 24's supervisor handles its own basic diagnosis.

</domain>

<decisions>
## Implementation Decisions

### Agent Architecture
- Supervisor wraps CASE: user talks to supervisor, supervisor spawns CASE agent as subagent via Claude Code's Task tool
- Supervisor is ALWAYS the entry point for every lucy-ng invocation (not just CASE). It routes to dereplication, CASE, sanitize, etc.
- True multi-agent: supervisor spawns CASE agent via Task tool, gets results back, evaluates, decides next step
- CASE agent runs full workflow with checkpoints: supervisor doesn't micro-manage individual steps, but CASE agent writes checkpoint files that the supervisor reads between iterations
- Supervisor agent defined as markdown file with YAML frontmatter in `.claude/agents/`

### State Tracking
- CASE agent writes a human-readable markdown progress report (CASE-PROGRESS.md) in the compound's working directory
- Markdown format chosen over JSON because the supervisor is an AI agent that reads natural language; also human-readable for user inspection
- Progress report is accumulating (append-style log): each iteration appends to the report, building full history of what was tried
- Rich reporting: each iteration entry includes solution count, constraints added/removed, WHY changes were made, confidence assessment, HMBC correlations used
- File persists across sessions (working directory, next to LSD files and spectra)

### Intervention Behavior
- Supervisor diagnoses first (Phase 24), before Phase 25 adds a dedicated diagnostic specialist
- Advisory with constraints: supervisor tells CASE agent what the problem is and what to fix (e.g., "sp2 count issue detected, fix before retrying"), but does NOT dictate exactly which atom to change -- CASE agent figures out the specific fix
- Escalate to user after 10 failed intervention cycles with same pattern (not 3 -- give the supervisor substantial room to try different angles)
- Each intervention cycle: detect loop → diagnose from progress log → advise CASE agent with constraints → CASE retries

### Convergence Criteria
- Three convergence signals: solution count trend (should decrease), constraint effectiveness (each added constraint should change solution set), and confidence score improvement over iterations
- Flexible success target:
  - Ideal: 1-5 solutions with top-ranked high confidence
  - Acceptable: <10 solutions with top-ranked well-differentiated by ranking score
  - Not a failure if count slightly higher, as long as ranking clearly separates best candidates
- Hard safety cap: ~20 total LSD iterations maximum, then report best result and escalate
- Plateau handling: conditional -- plateau at <=10 solutions with good analysis = convergence. Plateau at >10 = try additional strategy

### Claude's Discretion
- Exact checkpoint file format and structure (within markdown, human-readable constraint)
- How to map loop detection patterns to specific diagnostic checks
- How to structure the supervisor's system prompt / agent definition
- Routing logic details (how supervisor decides between dereplication, CASE, sanitize)
- Exact wording of advisory messages to CASE agent

</decisions>

<specifics>
## Specific Ideas

- User envisions the AI agent performing a likelihood analysis of chemical substructures (fragments), hybridization, and heteroatom attachments (via LSD lists) at the very beginning of CASE -- not only after HMBC iterations. This is a workflow enhancement that the supervisor should expect from the CASE agent and verify was done.
- The existing `skill/supervisor/SKILL.md` (78 lines) is the foundation -- it has basic loop detection patterns and escalation criteria that Phase 24 will expand significantly.
- Convergence detection from Phase 22 (iteration cap ~10) and ambiguity escalation from Phase 23 feed into supervisor logic.

</specifics>

<deferred>
## Deferred Ideas

- Upfront substructure/hybridization/heteroatom likelihood analysis as part of the CASE workflow -- this is a SKILL.md enhancement (CASE strategy) rather than supervisor logic. Should be captured as a future SKILL.md update or a CASE workflow improvement phase.
- Full diagnostic specialist delegation (Phase 25) -- supervisor does basic diagnosis in Phase 24, delegates to specialist in Phase 25.

</deferred>

---

*Phase: 24-supervisor-agent*
*Context gathered: 2026-02-07*
