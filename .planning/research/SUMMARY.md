# Project Research Summary

**Project:** lucy-ng v2.0 Multi-Agent CASE Architecture
**Domain:** AI-powered Computer-Assisted Structure Elucidation (NMR spectroscopy)
**Researched:** 2026-02-06
**Confidence:** HIGH

## Executive Summary

The v2.0 milestone transforms lucy-ng from a tool-heavy architecture to a skill-first multi-agent system. Research reveals this requires **zero new dependencies**—all orchestration capabilities are native to Claude Code via the Task tool and subagent system. The critical finding: this is a skill engineering problem, not a library/framework problem.

The Virgiline (CASE7) failure revealed the fundamental limitation of tool-heavy systems: AI agents bypass "smart" tools when the embedded logic doesn't match their reasoning. The solution is inversion of control: push domain knowledge into skills where the AI can reason about it, reduce tools to thin data access wrappers, and add a supervisor agent to detect and break unproductive loops.

**Recommended approach:** Incremental refactoring, not rewrite. Layer multi-agent orchestration over the working v1.2 system, migrate intelligence from Python to skills progressively, validate supervisor pattern before simplifying tools. The existing 16 MCP tools, SQLite database, and LSD integration remain unchanged—the multi-agent layer sits above them.

**Key risks:** Supervisor intervention criteria must be specific (not generic "try again"), state tracking needs structured format (not freeform), and tool simplification must maintain backward compatibility. Research shows tool-heavy systems degrade beyond 50-100 tools due to semantic confusion; lucy-ng at 16 tools is below threshold but growing, making this transformation timely.

## Key Findings

### Recommended Stack

**Zero additions.** Claude Code's native Task tool provides all orchestration primitives: subagent spawning (foreground/background), context isolation, auto-compaction, and resume capability. Subagents are defined as markdown files with YAML frontmatter (stored in `.claude/agents/`), not code. The supervisor-worker pattern uses file-based state management (`analysis/progress.md`, `TASKS.md`) following established patterns from enterprise multi-agent systems.

**Core technologies (unchanged from v1.2):**
- **Python 3.10+** - Runtime, no version change needed
- **Pydantic v2** - Data models, working well
- **nmrglue/NumPy/SciPy/RDKit** - NMR processing and chemistry, validated
- **SQLite** - 928K compound database with 7.9M HOSE statistics, unchanged
- **Click** - CLI framework, maintains backward compatibility
- **FastMCP** - MCP server, unchanged
- **Claude Code Task tool** - Native subagent orchestration (no installation needed)

**What NOT to add:**
- Multi-agent frameworks (LangGraph, CrewAI) - Claude Code provides orchestration natively
- Message queue systems (RabbitMQ, Redis) - File-based state sufficient for CASE workflows
- Workflow engines (Airflow, Prefect) - CASE is dynamic, not static DAG
- Agent monitoring platforms - Progress files provide observability, transcripts provide history

### Expected Features

**Must have (table stakes for robust CASE):**

**TS-1: Supervisor Agent with Loop Detection**
- Dedicated supervisor monitors CASE agent and detects unproductive patterns
- Specific loop patterns: ELIM thrashing, sp2 count oscillation, constraint churning, repeated zero-solution attempts
- Intervention strategies: After 3 failed attempts with same pattern → redirect with specific diagnosis
- Implementation: Markdown-based progress monitoring, no Python orchestration framework

**TS-2: CASE Skill with Incremental HMBC Strategy**
- Skill instructions teaching incremental constraint addition (not "throw everything in")
- Phase 1: Core structure from high-confidence signals (HSQC + well-separated quaternary carbons)
- Phase 2: Resolve ambiguity with diagnostic correlations (HMBC to distinguish scaffolds)
- Phase 3: Refine with full constraint set (only after scaffold determined)
- Rationale: Structure Elucidator 2025 emphasizes this for crowded spectral regions

**TS-3: Error Tolerance as AI Knowledge (Not Python Detection)**
- Skill teaches AI to detect and reason about spectroscopic ambiguities
- Close carbon shifts (0.3-0.5 ppm in aliphatic regions) - AI identifies proactively, documents ambiguity
- DEPT phase conflicts (HSQC shows CH, DEPT suggests CH2) - AI compares and chooses ground truth
- Ambiguous HMBC assignment (cross-peak to either of two close carbons) - AI generates variants, tests both
- Quaternary carbon HMBC sparsity - AI uses chemical shift to constrain heteroatom attachment

**TS-4: Diagnostic Specialist Agent**
- Specialist systematically diagnoses WHY LSD failed (0 or 1000+ solutions)
- For 0 solutions: Check sp2 count (even?), hydrogen budget (matches?), HMBC conflicts, correlation order
- For 1000+ solutions: Check constraint count, quaternary carbon connectivity, heteroatom constraints, symmetry encoding
- Output: Structured diagnostic report with root cause and recommended fixes

**TS-5: Thin Peak Picker Tools (Remove Intelligence)**
- Reduce MCP tools to data access wrappers, remove embedded logic
- Keep: Read spectrum, extract peaks above threshold, return raw data
- Remove: DEPT-guided adaptive thresholding, HMBC filtering, automatic conflict resolution
- Rationale: AI can reason about data context-dependently; Python can't

**Should have (competitive differentiators):**

**DIFF-1: AI-Readable Spectral Quality Assessment**
- Skill teaches S/N indicators (>100:1 clean, 20-100:1 check weak correlations, <20:1 aggressive filtering)
- Digital resolution impact (low resolution → close carbons alias, document HMBC distinction limits)
- Artifact recognition (1J correlations, t1 noise, baseline roll)

**DIFF-2: Confidence-Annotated Output**
- All analysis steps include confidence levels (High >90%, Medium 60-90%, Low <60%)
- Documents which assignments were certain vs guessed
- Flags areas where additional NMR might help

**Defer (v2.1+):**
- Constraint Satisfaction Explorer specialist (generates LSD variants for ambiguous cases)
- Solution Explainer specialist (explains WHY a structure ranks #1)
- Parallel hypothesis exploration (background subagents for multiple interpretations)
- Agent Teams (experimental, may be overkill for sequential CASE workflow)

### Architecture Approach

**Three-layer model:** Skill Layer (intelligence) → Multi-Agent Layer (orchestration) → Tool Layer (data access)

**Agent roles:**
1. **Supervisor** - Monitors CASE progress via `analysis/progress.md`, detects loops (3+ same error, ELIM thrashing, constraint oscillation), intervenes with specific redirects
2. **CASE Agent** - Executes full elucidation workflow (dereplication → symmetry → peak picking → LSD → ranking), writes progress checkpoints, spawns specialists if needed
3. **Specialists (optional)** - Peak picker (HMBC validation), LSD debugger (constraint diagnosis)

**Communication protocol:**
- Task list: `analysis/TASKS.md` (shared high-level goals)
- Messaging: `analysis/messages/` (progress reports, redirect strategies)
- State tracking: `analysis/STATE.md` (current step, iteration count, issues, flags)

**Major components:**

1. **Supervisor Infrastructure** - Loop detection rules in `skill/SUPERVISOR.md`, state tracking templates, checkpoint monitoring patterns
2. **Skill Restructure** - Split CLAUDE.md (project-level) from SKILL.md (workflow), remove duplication, add checkpoint markers
3. **Multi-Agent Integration** - Supervisor spawns CASE subagent, monitors progress, intervenes on loops
4. **Tool Simplification** - Migrate intelligence from Python to skill, keep tools as thin data access wrappers

**Key architectural decision:** Supervisor + single CASE agent (not swarm). CASE is sequential workflow, not parallel tasks. Supervisor prevents loops; swarm would add coordination overhead without benefit.

### Critical Pitfalls

**1. Tool-Heavy Architecture Doesn't Scale**
- **Problem:** Embedding intelligence in Python tools creates brittle system that degrades as tool count grows
- **Evidence:** AI bypassed `generate_lsd_input` in Virgiline case, constructing LSD file directly when tool logic didn't match reasoning
- **Impact:** System degrades beyond ~50-100 tools (semantic confusion, cognitive overload); lucy-ng at 16 tools is below threshold but growing
- **Prevention:** Categorize tools by intelligence level (Tier 1: pure data access—keep; Tier 2: moderate intelligence—migrate to skill; Tier 3: complex logic—refactor later), encode domain knowledge in skill not code

**2. Supervisor Without Clear Intervention Criteria**
- **Problem:** Supervisor monitors but doesn't intervene (passive), or intervenes too broadly (generic "try again")
- **Impact:** CASE agent continues unproductive patterns for dozens of iterations, or supervisor terminates legitimate multi-step reasoning
- **Prevention:** Define specific loop patterns (same error 3+ times, ELIM adjusted 3+ times, sp2 corrected 2+ times for same atom), require multiple signals before intervention, interventions must be specific with root cause diagnosis

**3. State Tracking Fragility**
- **Problem:** Progress files become inconsistent or unparseable, supervisor can't monitor
- **Impact:** Loop detection fails, resume fails, debugging impossible (no audit trail)
- **Prevention:** Enforce structured format in skill (## heading, Status field, Issue if Failed), provide progress template, validate structure after writing

**4. Premature Specialist Agent Proliferation**
- **Problem:** Creating specialist for every subtask before validating supervisor pattern
- **Impact:** Over-engineered system, coordination overhead exceeds benefit
- **Prevention:** Start with supervisor + single CASE agent, only add specialists when CASE agent demonstrably struggles, each specialist must justify existence

**5. CASE-Specific: ELIM as First Resort**
- **Problem:** AI immediately adds ELIM when LSD returns 0 solutions, masking real constraint errors
- **Impact:** Root cause unfixed, multiple iterations with ELIM 1, 2, 3... without progress
- **Prevention:** Skill teaches decision tree: 0 solutions → check sp2 count (even?), H count (matches?), constraints (valid?); only if all correct → try ELIM 1 0 as last resort

## Implications for Roadmap

Based on research, suggested phase structure follows build order with dependency awareness:

### Phase 1: Supervisor Infrastructure (Foundation)
**Rationale:** Creates multi-agent framework without changing working tools; low risk, can start immediately
**Delivers:** Supervisor skill document (`skill/SUPERVISOR.md`), state tracking templates (`analysis/STATE.md`, `TASKS.md`, `messages/`), loop detection rule documentation
**Addresses:** TS-1 (supervisor with loop detection)
**Avoids:** Pitfall 2 (unclear intervention criteria) by documenting specific patterns upfront

### Phase 2: Skill Restructure (Parallel with Phase 1)
**Rationale:** Reorganizes content without behavior changes; low risk, independent of multi-agent work
**Delivers:** Split CLAUDE.md (project-level: setup, database, references) from SKILL.md (workflow: dereplication → LSD → ranking), remove duplication, add checkpoint markers
**Uses:** Content analysis and reorganization, no code changes
**Implements:** Clearer separation of concerns for multi-agent context loading

### Phase 3: Incremental HMBC Strategy (Parallel with Phase 1-2)
**Rationale:** Highest-impact change with lowest implementation risk; pure skill content, no code
**Delivers:** SKILL.md with 3-phase constraint addition strategy (core structure → resolve ambiguity → refine)
**Addresses:** TS-2 (incremental HMBC strategy), Pitfall 5 (ELIM as first resort)
**Implements:** Domain knowledge from Structure Elucidator 2025 research

### Phase 4: Error Tolerance Skill Content (After Phase 2)
**Rationale:** Builds on restructured skill; medium effort, high value for difficult cases
**Delivers:** Skill sections on close shifts, DEPT conflicts, HMBC ambiguity, quaternary carbon handling
**Addresses:** TS-3 (error tolerance as AI knowledge)
**Avoids:** Pitfall 11-14 (symmetry, ELIM, quaternary ghosts, close shifts)

### Phase 5: Supervisor Integration (Depends on Phase 1)
**Rationale:** Validates multi-agent approach before tool changes; medium risk, needs testing
**Delivers:** Working supervisor spawn pattern, checkpoint monitoring, loop detection implementation, intervention strategies
**Uses:** Claude Code Task tool, progress file monitoring
**Addresses:** TS-1 (supervisor agent), Pitfall 2 (intervention criteria)
**Critical validation:** Test on Virgiline (known failure case) and other difficult compounds

### Phase 6: Diagnostic Specialist (Depends on Phase 5)
**Rationale:** Adds value after supervisor validated; optional but high impact for stuck cases
**Delivers:** LSD diagnostic specialist agent with systematic failure analysis
**Addresses:** TS-4 (diagnostic specialist)
**Uses:** Specialist subagent pattern from Phase 5

### Phase 7: Tool Simplification (Depends on Phase 2, 3, 4, 5 validated)
**Rationale:** Only after skill proves it can handle complexity; medium risk, needs careful testing
**Delivers:** Simplified MCP tools (read_2d_peaks, read_1d_peaks), domain knowledge migrated to skill
**Addresses:** TS-5 (thin tools), Pitfall 1 (tool-heavy architecture)
**Avoids:** Breaking backward compatibility (dual mode: CLI keeps smart tools, MCP gets thin)

### Phase Ordering Rationale

- **Phases 1, 2, 3 can run in parallel** - Independent content work, no code conflicts
- **Phase 4 depends on Phase 2** - Needs restructured skill to add error tolerance sections
- **Phase 5 depends on Phase 1** - Needs supervisor infrastructure to implement monitoring
- **Phase 6 depends on Phase 5** - Needs supervisor pattern validated before adding specialists
- **Phase 7 depends on Phases 2, 3, 4, 5** - Needs skill content complete and multi-agent validated before removing tool intelligence

**Critical path:** Phase 1 → Phase 5 (supervisor working) → Phase 7 (tool simplification)

**Parallel work:** Phases 2, 3, 4 (skill content) can happen anytime

**Deferred to v2.1:** Constraint Explorer specialist, Solution Explainer specialist, Agent Teams (experimental, complexity not justified)

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 5 (Supervisor Integration):** May need iteration on loop detection thresholds; test with real failure cases to tune intervention criteria
- **Phase 7 (Tool Simplification):** Tool changes need careful validation; consider regression testing suite for backward compatibility

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Supervisor Infrastructure):** Well-documented pattern from enterprise multi-agent systems
- **Phase 2 (Skill Restructure):** Documentation reorganization, no novel concepts
- **Phase 3 (Incremental HMBC):** Direct application of Structure Elucidator 2025 methodology
- **Phase 4 (Error Tolerance):** Domain knowledge extraction from existing CLAUDE.md

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Claude Code Task tool verified in official docs (Jan 2026 release), subagent configuration well-documented with examples, zero new dependencies needed |
| Features | HIGH | Supervisor pattern validated in enterprise systems (Databricks, Azure), incremental constraint strategy from established CASE literature, tool simplification proven approach (HyperAI research) |
| Architecture | MEDIUM-HIGH | Supervisor + worker pattern well-documented, file-based state follows TeammateTool pattern, CASE-specific application needs validation on difficult test cases |
| Pitfalls | HIGH | Tool-heavy degradation documented (50-100 tool threshold), loop detection patterns from 2026 research, state tracking fragility known issue in multi-agent systems |

**Overall confidence:** HIGH

Research is based on official Claude Code documentation (subagents, Task tool), recent multi-agent architecture research (2026 patterns from enterprise systems), and domain-specific CASE methodology (Structure Elucidator 2025, LSD manual). The primitives exist and are well-validated; the CASE-specific application is straightforward.

### Gaps to Address

**1. Loop detection threshold tuning**
- **Gap:** What counts as "stuck" vs. legitimate multi-step reasoning in CASE context?
- **Resolution:** Test supervisor on known failure cases (Virgiline, other difficult compounds) during Phase 5 implementation; tune thresholds based on false positive/negative rates
- **Action:** Include validation test suite in Phase 5 requirements

**2. Tool simplification backward compatibility**
- **Gap:** How to maintain CLI usability while migrating intelligence to skills?
- **Resolution:** Dual mode—CLI tools retain smart behavior (existing users), MCP tools become thin (multi-agent mode)
- **Action:** Define compatibility matrix in Phase 7 planning; consider deprecation timeline for smart CLI mode

**3. Specialist agent justification**
- **Gap:** Which specialists are actually needed vs. premature optimization?
- **Resolution:** Start with supervisor + CASE agent only; add specialists incrementally when CASE agent demonstrably struggles
- **Action:** Defer specialists to optional phases; make data-driven decision based on Phase 5 results

**4. Skill size management**
- **Gap:** CLAUDE.md is already 1080 lines; will multi-agent sections make it unwieldy?
- **Resolution:** Restructuring in Phase 2 should reduce duplication; use skills inheritance for subagents
- **Action:** Set size budget (main skill <1500 lines, subagent skills <500 lines); monitor during implementation

## Sources

### Primary (HIGH confidence)

**Multi-Agent Orchestration:**
- [Create custom subagents - Claude Code Docs](https://code.claude.com/docs/en/sub-agents) - Official documentation
- [Multi-Agent Supervisor Architecture | Databricks](https://www.databricks.com/blog/multi-agent-supervisor-architecture-orchestrating-enterprise-ai-scale) - Enterprise patterns
- [AI Agent Orchestration Patterns | Microsoft Azure](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) - Validated patterns
- [The Task Tool: Claude Code's Agent Orchestration System](https://dev.to/bhaidar/the-task-tool-claude-codes-agent-orchestration-system-4bf2) - Task tool mechanics

**Skill Architecture:**
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills) - Official skill system documentation
- [AI Agent Architectures: Scaling Limits in 2026 | HyperAI](https://beta.hyper.ai/en/stories/53d4fafdd3b77c15bc7008b4122bc84c) - Tool-heavy degradation research (50-100 tool threshold)

**CASE Methodology:**
- [Structure Elucidator Suite 2025 Features | ACD/Labs](https://www.acdlabs.com/technical-support/current-software-versions/structure-elucidator-suite/) - Incremental constraint addition
- [LSD Manual](https://nuzillard.github.io/LSD/MANUAL_ENG.html) - Constraint satisfaction solver documentation
- Existing lucy-ng CLAUDE.md (1080 lines) - Domain knowledge reference

### Secondary (MEDIUM confidence)

**Loop Detection:**
- [Our Agent Had A 4 Minute Loop. Here's How We Fixed It. | Medium](https://medium.com/data-science-collective/our-agent-had-a-4-minute-loop-heres-how-we-fixed-it-40a8142ef1a9) - Practical loop detection patterns
- [Ralph Wiggum AI Agents: The Coding Loop of 2026 | Leanware](https://www.leanware.co/insights/ralph-wiggum-ai-coding) - Loop prevention strategies

**Multi-Agent Patterns:**
- [Claude Code's Hidden Multi-Agent System | Paddo.dev](https://paddo.dev/blog/claude-code-hidden-swarm/) - TeammateTool reverse engineering
- [Choosing the right orchestration pattern | Kore.ai](https://www.kore.ai/blog/choosing-the-right-orchestration-pattern-for-multi-agent-systems) - Supervisor vs swarm comparison

### Tertiary (LOW confidence)

**Agent Teams (experimental):**
- [Claude Code Swarm Orchestration Skill](https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea) - Community experimentation
- Agent Teams feature (Feb 2026, experimental) - Deferred to future milestone

---

**Research completed:** 2026-02-06
**Ready for roadmap:** Yes

**Key recommendation for roadmap creation:** Prioritize skill content (Phases 2-4) in parallel with supervisor infrastructure (Phase 1). Validate supervisor pattern (Phase 5) before any tool changes (Phase 7). This allows early wins (incremental HMBC strategy) while building toward full multi-agent architecture safely.
